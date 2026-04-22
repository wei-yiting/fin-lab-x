# AI SDK v6 Contract Findings

These behaviors of `@ai-sdk/react@3.0.144` + `ai@6.0.142` are not documented in the AI SDK release notes. They were verified against the S1 backend (`backend/api/routers/chat.py`) during pre-coding contract probes and the code-review loop. Record them here so future readers do not re-derive them from SDK internals.

## 1. SSE `error` chunks do **not** persist into `message.parts[]`

AI SDK v6's chat store reducer (`case "error"`) only calls `onError` and sets `status` to `"error"`. It does not push an `error`-typed part into the message. Consequences:

- `UIMessage.parts` never contains an item with `type === "error"`.
- Any `useEffect` that expects to fire on `parts.some(p => p.type === 'error')` will never run.
- The correct signal for stream-level errors is `status === 'error'` combined with the top-level `error` field from `useChat`.

The mid-stream `ErrorBlock` therefore renders at the **`ChatPanel` level** (reading `useChat.error`), not inline inside `AssistantMessage`.

## 2. `useChat.stop()` is clean — it does not pollute `error`

Calling `stop()` during streaming:

- transitions `status` back to `'ready'`
- leaves `error` as `undefined` (not `null`, not an `AbortError`)

No `try/catch` wrapper, no `AbortError` filter, and no manual `setStatus` is required inside `handleStop`.

Two implementation notes that surfaced during verification:

- The SDK's `error` field is typed `Error | undefined`. Use `.toBeUndefined()` in tests, not `.toBeNull()`.
- MSW handlers for stream fixtures **must** listen to `request.signal.abort` and close the server-side stream when the client aborts. Otherwise the SDK waits for end-of-stream that never comes, producing false-negative abort tests.

## 3. S1 accepts `regenerate` on a partial turn (HTTP 200)

When the client disconnects mid-stream, LangGraph has already persisted the partial `AIMessage` to its checkpointer. `POST /api/v1/chat` with `trigger: regenerate-message` and the partial `messageId` returns HTTP 200 and a fresh SSE stream (new `messageId`, tool calls re-issued).

**Race window**: if the client disconnects before LangGraph commits any `AIMessage`, the backend falls back to an earlier turn or raises `"No assistant message to regenerate"` (HTTP 404). This is why `handleRetry` must fall back to `sendMessage` on any pre-stream 4xx — not just 422.

**Re-verification**: this finding is captured as an executable probe at `scripts/v1-partial-regen-probe.sh`. Run it manually whenever the S1 backend, its checkpointer, or its LangGraph version changes. The script:

1. Opens `/api/v1/chat` with a prompt that takes >4s, then `curl --max-time 4` kills the connection (simulating user Stop).
2. Asserts the captured SSE does not contain a `finish` chunk (confirms partial turn).
3. Extracts `messageId` from the `start` chunk.
4. Re-hits `/api/v1/chat` with `trigger: regenerate` + that partial `messageId` and records the HTTP status + response body.

The script burns real LLM tokens — do not loop it.

## 4. SSE text-delta field name is `delta`, not `textDelta`

The v6 `UIMessageChunk` type uses `delta` for incremental text. Fixtures that write `textDelta` are silently dropped by the SDK (the chunk fails schema validation), producing a stream that looks valid to the test runner but is actually empty. The backend serializer (`sse_serializer.py`) already uses `delta`; frontend fixtures must match.

## 5. AI SDK v6 request body is nested

The backend expects `{ id, messages: [{role, parts: [{type, text}]}], trigger, messageId? }`. Flat `{ message: string }` payloads from v5-style clients are rejected. See `StreamChatRequest` in `backend/api/routers/chat.py`.
