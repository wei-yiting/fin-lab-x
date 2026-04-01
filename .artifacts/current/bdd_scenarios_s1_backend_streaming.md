# BDD Scenarios — S1 Backend Streaming

## Meta
- Design Reference: `.artifacts/current/design_S1_backend_streaming.md`, `.artifacts/archive/design.md`
- Generated: 2026-03-31
- Discovery Method: Three Amigos (Agent Teams — PO, Dev, QA)

### Design Decisions Made During Discovery

| # | Decision | Rationale |
|---|----------|-----------|
| DD-01 | `id` is mandatory (changed from optional) | Eliminates auto-generation complexity, prevents empty-string data leakage (C08), ensures client always knows session ID |
| DD-02 | `start` event includes `sessionId` as confirmation echo | Lets client assert the session ID the server is using matches what was sent |
| DD-03 | Same-session concurrent requests → immediate HTTP 409 | Explicit rejection is safer than indefinite wait; avoids lock timeout ambiguity |
| DD-04 | Regenerate `messageId` is strictly validated | Must match last assistant message; 422 on mismatch; prevents silent server/client desync |
| DD-05 | Fatal error does NOT emit synthetic ToolError for pending tools | Stream error and tool error are semantically different; client cleans up pending tools on finish(error) |
| DD-06 | Post-restart silent amnesia is accepted V1 behavior | InMemorySaver is volatile by design; documented limitation |

---

## Feature: SSE Streaming Pipeline

### Context
Backend streams AI agent responses via SSE following AI SDK UIMessage Stream Protocol v1. Every successful request produces a well-framed stream bounded by `start` and `finish` events, with paired lifecycle events for text blocks and tool calls.

### Rule: Every successful request produces a well-framed SSE stream

#### S-stream-01: Text-only response is correctly framed
> Verifies that a response without tool calls has paired text block events and terminal finish

- **Given** session "sess-001" exists
- **When** the API consumer sends `{ "message": "你好，請自我介紹", "id": "sess-001" }`
- **Then** the stream contains exactly one `start` event with a unique `messageId` and `sessionId: "sess-001"`
- **And** one `text-start` / `text-end` pair with matching `id`
- **And** one or more `text-delta` events between them
- **And** a terminal `finish` event with `finishReason: "stop"`

Category: Illustrative
Origin: PO

#### S-stream-02: Tool call response has correct lifecycle and text block closure
> Verifies that text blocks are closed before tool events, and tool lifecycle is complete

- **Given** session "sess-002" exists
- **When** the API consumer sends `{ "message": "TSMC 最近表現如何？", "id": "sess-002" }` and the agent decides to call a tool
- **Then** any open text block receives `text-end` before the first `tool-call-start`
- **And** each tool call has a complete lifecycle: `tool-call-start` → `tool-call-end` → `tool-result` (same `toolCallId`)
- **And** text after tool results gets a new `text-start` with a different `id`
- **And** the stream ends with `finish(stop)`

Category: Illustrative
Origin: Multiple (PO seeded, Dev challenged text block closure C01)

#### S-stream-03: Parallel tool calls each produce complete lifecycle events
> Verifies that multiple simultaneous tool calls each get their own paired events

- **Given** session "sess-003" exists
- **When** the API consumer sends `{ "message": "查 TSMC 股價和最近 SEC 文件", "id": "sess-003" }` and the agent calls two tools in parallel
- **Then** each tool call has a unique `toolCallId`
- **And** each has a complete lifecycle: `tool-call-start` → `tool-call-end` → `tool-result`
- **And** the stream ends with a single `finish` event

Category: Illustrative
Origin: Multiple (PO seeded, Dev challenged ToolCallEnd burst C02)

### Rule: Session ID is mandatory and echoed in start event

#### S-stream-04: Session ID handling
> Verifies that session ID is required and echoed back in the start event

- **Given** a request to `POST /api/v1/chat/stream`
- **When** the request body is `<body>`
- **Then** the response is `<expected>`

| body | expected | notes |
|------|----------|-------|
| `{ "message": "hello", "id": "sess-abc" }` | SSE stream with `start` event containing `sessionId: "sess-abc"` | happy path |
| `{ "message": "hello" }` | HTTP 422 | `id` is mandatory |
| `{ "message": "hello", "id": "" }` | HTTP 422 | empty string rejected |

Category: Illustrative (table-driven)
Origin: Multiple (PO seeded, Dev challenged C07/C08)

### Rule: Invalid requests are rejected before streaming

#### S-stream-05: Empty or whitespace message rejected
> Verifies input validation prevents streaming for invalid messages

- **Given** a request to `POST /api/v1/chat/stream`
- **When** the request body is `<body>`
- **Then** the response is HTTP 422 with no SSE stream initiated

| body | notes |
|------|-------|
| `{ "message": "", "id": "sess-010" }` | empty string |
| `{ "message": "   \n\t  ", "id": "sess-011" }` | whitespace only |

Category: Illustrative (table-driven)
Origin: PO

#### S-stream-06: Conflicting message and trigger fields handled deterministically
> Verifies that ambiguous requests with both `message` and `trigger` have defined behavior

- **Given** session "sess-012" has an existing conversation
- **When** the API consumer sends `{ "message": "new question", "id": "sess-012", "trigger": "regenerate", "messageId": "msg_001" }`
- **Then** the endpoint returns a deterministic response (either processes as regenerate or as new message, not undefined behavior)

Category: Illustrative
Origin: Multiple (QA challenged C12, Dev confirmed C12)

---

### Journey Scenarios

#### J-stream-01: Complete financial analysis conversation
> Proves the full pipeline: send → tool call → context continuity → regenerate

- **Given** a new session "sess-j001"
- **When** the API consumer sends a financial question that triggers tool calls, receives a complete streamed response with tool progress, then sends a follow-up question referencing the first answer (same session), then triggers regenerate on the second response
- **Then** turn 1 has complete tool lifecycle with progress events and `finish(stop)`; turn 2 demonstrates context awareness (references turn 1 data); regenerate produces a new `messageId` and the stream completes successfully

Category: Journey
Origin: Multiple

---

## Feature: Conversation Continuity

### Context
The backend uses LangGraph's InMemorySaver checkpointer to maintain conversation history. Same `thread_id` (mapped from `id`) accumulates turns; different IDs are isolated.

### Rule: Same session ID accumulates conversation context

#### S-conv-01: Session context determines conversation continuity
> Verifies that session state is preserved within a session and isolated across sessions

- **Given** `<user>` sent `<first_message>` in session `<session_a>` and received a response
- **When** they send `<second_message>` in session `<session_b>`
- **Then** the response `<expectation>`

| user | first_message | session_a | second_message | session_b | expectation |
|------|--------------|-----------|----------------|-----------|-------------|
| Alice | "TSMC 最近股價多少？" | sess-100 | "跟上個月比呢？" | sess-100 | references TSMC without re-stating |
| Bob | "TSMC 最近股價多少？" | sess-200 | "跟上個月比呢？" | sess-201 | does NOT reference TSMC; asks for clarification |

Category: Illustrative (table-driven)
Origin: Multiple (PO seeded, QA challenged isolation)

### Rule: Conversation state is volatile (InMemorySaver) — accepted V1 behavior

#### S-conv-02: Post-restart session treated as new conversation
> Verifies that server restart clears all state; same session ID starts fresh without error

- **Given** session "sess-300" had a multi-turn conversation, then the server restarts
- **When** the API consumer sends a new message to session "sess-300"
- **Then** the stream completes normally (HTTP 200, valid SSE)
- **And** the agent responds with no memory of prior conversation (treats it as first message)

Category: Illustrative
Origin: Multiple (Dev challenged C15, accepted as V1 behavior)

---

## Feature: Regenerate (Retry Last Response)

### Context
API consumer can request the backend to discard the last assistant turn and re-generate. The complete assistant turn (AIMessage + associated ToolMessages) is removed, and the agent re-processes from scratch.

### Rule: Regenerate removes the complete last assistant turn and re-streams

#### S-regen-01: Regenerate produces a new response with new messageId
> Verifies that regenerate replaces the previous response with a fresh one

- **Given** session "sess-400" has a completed conversation where the last assistant response has `messageId: "msg_001"` and involved a tool call
- **When** the API consumer sends `{ "id": "sess-400", "trigger": "regenerate", "messageId": "msg_001" }`
- **Then** the stream starts with a new `messageId` (different from "msg_001")
- **And** the agent may re-execute tools (the full turn was removed, not just the text)
- **And** the stream completes with `finish(stop)`

Category: Illustrative
Origin: Multiple (PO seeded, Dev challenged turn removal scope C16)

### Rule: Regenerate validates preconditions strictly

#### S-regen-02: Regenerate precondition failures
> Verifies that invalid regenerate requests are rejected with appropriate errors

- **Given** `<precondition>`
- **When** the API consumer sends `<request>`
- **Then** the response is `<expected>`

| precondition | request | expected | notes |
|-------------|---------|----------|-------|
| Session "sess-none" does not exist | `{ "id": "sess-none", "trigger": "regenerate", "messageId": "msg_x" }` | HTTP 404 | non-existent session |
| Session "sess-new" exists with only one HumanMessage (no assistant reply yet) | `{ "id": "sess-new", "trigger": "regenerate", "messageId": "msg_x" }` | HTTP error (404 or 422) | nothing to regenerate |
| Session "sess-ok" has last assistant msg "msg_003" | `{ "id": "sess-ok", "trigger": "regenerate", "messageId": "msg_001" }` | HTTP 422 | messageId doesn't match last assistant message |

Category: Illustrative (table-driven)
Origin: Multiple (PO seeded 404, Dev challenged C17/C18, Q3 decision)

---

### Journey Scenarios

#### J-regen-01: Regenerate after tool failure recovers successfully
> Proves the regenerate → re-execution → success flow when the original response was unsatisfactory due to tool errors

- **Given** a session where the last assistant turn involved a tool that errored (data-tool-error emitted)
- **When** the API consumer triggers regenerate for that response
- **Then** the agent re-processes from scratch, may call tools again (which may now succeed), and produces a new complete response

Category: Journey
Origin: Multiple

---

## Feature: Tool Error Resilience

### Context
When a tool fails during execution, the stream continues. Tool errors produce `data-tool-error` events (custom event type), not stream-level errors. The agent receives the error and decides how to proceed.

### Rule: A single tool failure does not terminate the stream

#### S-tool-01: Partial tool failure — stream continues with available data
> Verifies that one tool's failure doesn't block the other's result or terminate the stream

- **Given** session "sess-600" exists
- **When** the API consumer sends a message that triggers two parallel tool calls, and one tool fails (e.g., yfinance timeout) while the other succeeds (e.g., tavily returns results)
- **Then** the stream contains `data-tool-error` for the failed tool and `tool-result` for the successful tool (in any order, each with correct `toolCallId`)
- **And** the agent produces a text response using the available data
- **And** `finishReason` is `"stop"` (not `"error"`)

Category: Illustrative
Origin: Multiple (PO seeded, Dev challenged ordering C21)

#### S-tool-02: All tools fail — agent explains gracefully
> Verifies that even when every tool fails, the stream completes normally

- **Given** session "sess-601" exists
- **When** the API consumer sends a message that triggers two tool calls, and both fail
- **Then** the stream contains `data-tool-error` for each failed tool
- **And** the agent produces a text response explaining the failures
- **And** `finishReason` is `"stop"`

Category: Illustrative
Origin: PO

### Rule: Tool error messages are sanitized at the system boundary

#### S-tool-03: Tool error does not expose internal credentials or paths
> Verifies that error content in data-tool-error events is safe for client consumption

- **Given** a tool that fails with an exception containing internal details (e.g., API URL with credentials, internal hostname)
- **When** the error flows through the pipeline to the SSE stream
- **Then** the `error` field in the `data-tool-error` event does not contain API keys, internal paths, connection strings, or stack traces

Category: Illustrative
Origin: Multiple (QA challenged C22, Dev confirmed security concern)

---

### Journey Scenarios

#### J-tool-01: Tool failure then recovery across turns
> Proves that tool errors in one turn don't prevent success in the next

- **Given** session "sess-j002" where turn 1 had a tool error (yfinance timeout)
- **When** the API consumer sends a follow-up asking to retry ("再試一次查股價")
- **Then** turn 2 shows the agent understands context from turn 1 (knows which stock to query)
- **And** the tool call succeeds in turn 2 with a complete result
- **And** both turns have `finishReason: "stop"`

Category: Journey
Origin: Multiple

---

## Feature: Stream-Level Error Handling

### Context
Unrecoverable errors (LLM unavailable, unexpected exceptions) terminate the stream with an `error` event followed by `finish(error)`. Open text blocks are closed before the error. Pending tool calls are NOT resolved with synthetic events — the client must clean them up on `finish(error)`.

### Rule: Unrecoverable errors produce error + finish("error")

#### S-err-01: LLM provider unavailable
> Verifies that LLM failure produces a clean error termination

- **Given** session "sess-700" exists and the LLM provider is unavailable
- **When** the API consumer sends a new message
- **Then** the stream contains a `start` event, an `error` event with human-readable text, and `finish` with `finishReason: "error"`

Category: Illustrative
Origin: PO

#### S-err-02: Error mid-text closes open text block first
> Verifies that lifecycle pairing is preserved even during errors

- **Given** session "sess-701" exists
- **When** the LLM produces partial text then crashes
- **Then** the open text block receives `text-end` before the `error` event
- **And** the stream ends with `finish(error)`

Category: Illustrative
Origin: PO

### Rule: Fatal error with pending tool calls does not emit synthetic tool events (DD-05)

#### S-err-03: Pending tools remain unresolved on fatal error
> Verifies that stream-level error does NOT emit synthetic ToolError for pending tool calls

- **Given** the agent has emitted `tool-call-start` for tools A, B, and C, and tool A has completed with `tool-result`
- **When** a fatal error occurs before tools B and C resolve
- **Then** the stream emits `error` + `finish(error)` without any `tool-result`, `tool-error`, or `data-tool-error` events for tools B and C
- **And** the client is responsible for marking pending tool calls as terminated based on `finish(error)`

Category: Illustrative
Origin: Multiple (Dev challenged C24, QA extended C25, user decided DD-05)

### Rule: Partial checkpoint after error may affect subsequent requests

#### S-err-04: Follow-up request after mid-stream error
> Verifies behavior when a prior request's error left partial state in the checkpointer

- **Given** session "sess-703" had a stream-level error after the agent node completed but before tools executed (checkpoint contains AIMessage with tool_calls but no ToolMessages)
- **When** the API consumer sends a new message to session "sess-703"
- **Then** the system handles the corrupted state — either recovers gracefully or produces a clear error (not a crash or hang)

Category: Illustrative
Origin: Dev (C27)

### Rule: Server crash produces no terminal event

#### S-err-05: Hard crash leaves no finish event
> Verifies that the client cannot rely solely on finish events for stream termination detection

- **Given** a streaming response is in progress
- **When** the server process crashes (OOM kill, pod eviction)
- **Then** the SSE connection drops with no `error` or `finish` event
- **And** the client must detect stream termination via connection close, not by waiting for a terminal event

Category: Illustrative
Origin: QA (C29)

---

### Journey Scenarios

#### J-err-01: Fatal error mid-conversation then recovery
> Proves that a session can recover after a stream-level error

- **Given** session "sess-j003" where turn 1 succeeded normally
- **When** turn 2 encounters a stream-level error (LLM crash mid-text → `text-end` → `error` → `finish(error)`)
- **And** the API consumer sends turn 3 to the same session
- **Then** turn 3 streams successfully, and the agent retains context from turn 1

Category: Journey
Origin: Multiple

---

## Feature: Tool Progress

### Context
Tools emit transient progress events via `get_stream_writer()`. These appear as `data-tool-progress` SSE events with `transient: true` and are not persisted in message history.

### Rule: Progress events are transient and carry tool context

#### S-prog-01: Progress event appears during tool execution
> Verifies that progress events are emitted between tool-call-end and tool-result with correct format

- **Given** session "sess-800" exists
- **When** the API consumer sends a message that triggers a tool call with progress reporting
- **Then** `data-tool-progress` events appear after `tool-call-end` and before `tool-result`
- **And** each progress event has `transient: true` and `data` containing `status`, `message`, and `toolName`

Category: Illustrative
Origin: PO

### Rule: Progress lookup failure is silently discarded

#### S-prog-02: Unmatched progress event does not disrupt the stream
> Verifies that a progress event with no matching pending tool call is dropped silently

- **Given** a custom chunk arrives with a `toolName` that doesn't match any pending tool call
- **When** the mapper attempts to reverse-lookup the `tool_call_id`
- **Then** no `data-tool-progress` event is emitted
- **And** the stream continues normally

Category: Illustrative
Origin: PO

### Rule: Parallel same-name tools have ambiguous progress attribution (V1 limitation)

#### S-prog-03: Progress attributed to first matching pending call when ambiguous
> Documents the expected degraded behavior for V1's toolName-based lookup

- **Given** the agent calls `yfinance_stock_quote` twice in parallel (tc_001 for TSMC, tc_002 for AAPL)
- **When** a progress event arrives with `toolName: "yfinance_stock_quote"`
- **Then** the progress is attributed to the first matching pending `tool_call_id` (arbitrary pick)
- **And** the attribution may be incorrect — this is a known V1 limitation

Category: Illustrative
Origin: Dev (C30)

---

## Feature: Concurrent Session Safety

### Context
A per-session lock prevents race conditions. Same-session concurrent requests are immediately rejected with HTTP 409. Different sessions process independently.

### Rule: Same-session concurrent requests receive immediate HTTP 409 (DD-03)

#### S-conc-01: Second request to active session is rejected
> Verifies that concurrent requests to the same session ID get 409

- **Given** session "sess-900" has an active streaming request in progress
- **When** a second request arrives for session "sess-900"
- **Then** the second request immediately receives HTTP 409 Conflict
- **And** the first request's stream is not affected

Category: Illustrative
Origin: Multiple (PO seeded, Dev challenged C32, user decided DD-03)

#### S-conc-02: Different sessions process in parallel
> Verifies that concurrent requests to different sessions are independent

- **Given** sessions "sess-901" and "sess-902" both receive requests concurrently
- **When** both streams are in progress simultaneously
- **Then** both complete independently with no blocking or interference

Category: Illustrative
Origin: PO

### Rule: Session lock is always released regardless of exit path

#### S-conc-03: Session is usable after a prior request errors
> Verifies that errors don't permanently deadlock a session

- **Given** session "sess-903" had a prior request that ended in a stream-level error
- **When** the API consumer sends a new request to session "sess-903"
- **Then** the request is accepted (not 409) and streams normally — the lock was released

Category: Illustrative
Origin: QA (C34)

---

## Feature: Client Disconnect Handling

### Context
When the API consumer disconnects mid-stream, FastAPI cancels the async generator. The server cleans up resources and flushes Langfuse traces. Checkpoint state may diverge from what the client received.

### Rule: Disconnect cancels server-side processing

#### S-disc-01: Disconnect during streaming cancels agent
> Verifies that server stops processing after client disconnects

- **Given** session "sess-950" has an active streaming response
- **When** the client connection is aborted mid-stream
- **Then** the server cancels the agent task (no orphaned LLM processing)
- **And** the Langfuse trace is flushed and properly closed

Category: Illustrative
Origin: PO

### Rule: Checkpoint may diverge from client perception after disconnect (DD-06 related)

#### S-disc-02: Full response checkpointed but client saw partial
> Verifies the known V1 divergence between server state and client perception

- **Given** the agent completes generating a full 500-token response and the checkpoint is saved
- **When** the client disconnects after receiving only 200 tokens
- **Then** the checkpoint contains the full response
- **And** on the next request to this session, the agent's history includes the complete prior response that the client never fully received

Category: Illustrative
Origin: Dev (C35)

### Rule: Client reconnection may duplicate messages in history

#### S-disc-03: Reconnect to same session after disconnect
> Verifies behavior when client reconnects and resends to the same session

- **Given** session "sess-952" had an in-progress stream that was interrupted by disconnect
- **When** the client reconnects and sends the same message again to session "sess-952"
- **Then** the message is added to history a second time (the first may have been partially checkpointed)
- **And** the agent sees duplicate context in conversation history

Category: Illustrative
Origin: QA (C38)

### Rule: MessageId is unique across all turns in a session

#### S-disc-04: Each turn produces a unique messageId
> Verifies that messageId never collides, even after server events

- **Given** a session with multiple completed turns, each with distinct messageIds
- **When** a new turn begins
- **Then** the `start` event's `messageId` is unique and does not match any prior turn's messageId

Category: Illustrative
Origin: Dev (C40)

---

### Journey Scenarios

#### J-disc-01: Disconnect then regenerate discards unseen response
> Proves the checkpoint/perception divergence manifests in a concrete user flow

- **Given** the client disconnected mid-stream from session "sess-j004" after seeing partial text, but the server checkpointed the full response
- **When** the client reconnects and sends a regenerate request (thinking the response was cut off)
- **Then** the server removes the complete (valid) checkpointed response and generates a new one
- **And** the user unknowingly discarded a valid response

Category: Journey
Origin: QA R2 (C39)
