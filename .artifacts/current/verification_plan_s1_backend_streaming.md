# Verification Plan — S1 Backend Streaming

## Meta

- Scenarios Reference: `.artifacts/current/bdd_scenarios_s1_backend_streaming.md`
- Generated: 2026-03-31

---

## Automated Verification

### Deterministic

S1 is a backend-only subsystem — all scenarios are verified via API calls (curl/script). No browser automation.

---

#### S-stream-01: Text-only response is correctly framed

- **Method**: script
- **Steps**:
  1. `curl -s -N -X POST http://localhost:8000/api/v1/chat/stream -H "Content-Type: application/json" -d '{"id":"sess-001","message":"你好，請自我介紹"}' > /tmp/s-stream-01.txt`
  2. Wait for stream to complete (connection closes)
  3. Parse all SSE events from the output
  4. Assert: first event is `type: "start"` with a non-empty `messageId` and `sessionId: "sess-001"`
  5. Assert: exactly one `text-start` / `text-end` pair with matching `id`
  6. Assert: one or more `text-delta` events between `text-start` and `text-end`
  7. Assert: last event is `type: "finish"` with `finishReason: "stop"`
  8. Assert: no `tool-call-start` events present
- **Expected**: Clean text-only stream with correct lifecycle framing

---

#### S-stream-02: Tool call response has correct lifecycle and text block closure

- **Method**: script
- **Steps**:
  1. `curl -s -N -X POST http://localhost:8000/api/v1/chat/stream -H "Content-Type: application/json" -d '{"id":"sess-002","message":"TSMC 最近表現如何？"}' > /tmp/s-stream-02.txt`
  2. Wait for stream to complete
  3. Parse all SSE events
  4. If text-delta events exist before tool-call-start: assert `text-end` appears before the first `tool-call-start`
  5. For each `tool-call-start(toolCallId=X)`: assert matching `tool-call-end(toolCallId=X)` exists after it
  6. For each `tool-call-end(toolCallId=X)`: assert matching `tool-result(toolCallId=X)` or `data-tool-error(toolCallId=X)` exists after it
  7. If text-delta events exist after tool-result: assert they have a new `text-start` with a different `id` than the first text block
  8. Assert: final event is `finish(stop)`
- **Expected**: Text block properly closed before tool events; complete tool lifecycle; post-tool text has new block ID

---

#### S-stream-03: Parallel tool calls each produce complete lifecycle events

- **Method**: script
- **Steps**:
  1. `curl -s -N -X POST http://localhost:8000/api/v1/chat/stream -H "Content-Type: application/json" -d '{"id":"sess-003","message":"幫我查 TSMC 股價和最近的 SEC 文件"}' > /tmp/s-stream-03.txt`
  2. Wait for stream to complete
  3. Parse all SSE events; collect all unique `toolCallId` values from `tool-call-start` events
  4. Assert: at least 2 unique `toolCallId` values
  5. For each `toolCallId`: assert complete lifecycle (start → end → result/error)
  6. Assert: exactly one `finish` event
- **Expected**: Each parallel tool call has its own lifecycle; all are complete

---

#### S-stream-04: Session ID handling (table-driven)

- **Method**: script
- **Steps**:
  1. **Happy path**: `curl -s -o /dev/null -w "%{http_code}" -X POST http://localhost:8000/api/v1/chat/stream -H "Content-Type: application/json" -d '{"id":"sess-abc","message":"hello"}'` → assert 200; parse first event and assert `sessionId: "sess-abc"`
  2. **Missing id**: `curl -s -o /dev/null -w "%{http_code}" -X POST http://localhost:8000/api/v1/chat/stream -H "Content-Type: application/json" -d '{"message":"hello"}'` → assert 422
  3. **Empty string id**: `curl -s -o /dev/null -w "%{http_code}" -X POST http://localhost:8000/api/v1/chat/stream -H "Content-Type: application/json" -d '{"id":"","message":"hello"}'` → assert 422
- **Expected**: Valid ID returns 200 with echo; missing/empty ID returns 422

---

#### S-stream-05: Empty or whitespace message rejected (table-driven)

- **Method**: script
- **Steps**:
  1. `curl -s -o /dev/null -w "%{http_code}" -X POST http://localhost:8000/api/v1/chat/stream -H "Content-Type: application/json" -d '{"id":"sess-010","message":""}'` → assert 422
  2. `curl -s -o /dev/null -w "%{http_code}" -X POST http://localhost:8000/api/v1/chat/stream -H "Content-Type: application/json" -d '{"id":"sess-011","message":"   \n\t  "}'` → assert 422
- **Expected**: Both return 422 with no SSE stream

---

#### S-stream-06: Conflicting message and trigger fields

- **Method**: script
- **Steps**:
  1. Set up session "sess-012" with a completed conversation (send a message, wait for finish)
  2. Capture `messageId` from the start event
  3. `curl -s -o /dev/null -w "%{http_code}" -X POST http://localhost:8000/api/v1/chat/stream -H "Content-Type: application/json" -d '{"id":"sess-012","message":"new question","trigger":"regenerate","messageId":"<captured_id>"}'`
  4. Assert: response is deterministic (not a 500 or crash); `[POST-CODING: determine which takes precedence — trigger or message — and assert accordingly]`
- **Expected**: Endpoint handles ambiguous request deterministically

---

#### S-conv-01: Session context determines conversation continuity (table-driven)

- **Method**: script
- **Steps**:
  1. **Same session**: Send `{"id":"sess-100","message":"TSMC 最近股價多少？"}` → wait for finish → Send `{"id":"sess-100","message":"跟上個月比呢？"}` → capture response text → assert response references "TSMC" or "台積電"
  2. **Different session**: Send `{"id":"sess-200","message":"TSMC 最近股價多少？"}` → wait for finish → Send `{"id":"sess-201","message":"跟上個月比呢？"}` → capture response text → assert response does NOT reference "TSMC" or "台積電" (agent asks for clarification)
- **Expected**: Same session preserves context; different sessions are isolated

---

#### S-conv-02: Post-restart session treated as new conversation

- **Method**: script
- **Steps**:
  1. Send `{"id":"sess-300","message":"記住這個：代碼是 42"}` → wait for finish
  2. Restart the backend server: `[POST-CODING: determine restart command]`
  3. Wait for server to be healthy
  4. Send `{"id":"sess-300","message":"剛剛的代碼是什麼？"}` → capture response text
  5. Assert: HTTP 200 (not error); response does NOT contain "42"
- **Expected**: Post-restart, same session ID starts fresh — no error, just amnesia

---

#### S-regen-01: Regenerate produces a new response with new messageId

- **Method**: script
- **Steps**:
  1. Send `{"id":"sess-400","message":"分析 TSMC 近期表現"}` → capture full stream → extract `messageId` from `start` event as `MSG_ID_1`
  2. Send `{"id":"sess-400","trigger":"regenerate","messageId":"$MSG_ID_1"}` → capture full stream → extract `messageId` from `start` event as `MSG_ID_2`
  3. Assert: `MSG_ID_2` ≠ `MSG_ID_1`
  4. Assert: regenerated stream has `start` → content events → `finish(stop)`
  5. Send a follow-up `{"id":"sess-400","message":"繼續分析"}` → capture response → assert the agent only sees one assistant response for the original question (the regenerated one)
- **Expected**: Regenerate replaces previous response; new messageId; conversation continues correctly

---

#### S-regen-02: Regenerate precondition failures (table-driven)

- **Method**: script
- **Steps**:
  1. **Non-existent session**: `curl -s -o /dev/null -w "%{http_code}" -X POST http://localhost:8000/api/v1/chat/stream -H "Content-Type: application/json" -d '{"id":"sess-none","trigger":"regenerate","messageId":"msg_x"}'` → assert 404
  2. **No assistant messages**: Send `{"id":"sess-new","message":"hello"}` → wait for finish → immediately send `{"id":"sess-new","trigger":"regenerate","messageId":"nonexistent_id"}` → assert error response (404 or 422)
  3. **Wrong messageId**: Set up session "sess-ok" with 2 assistant turns (msg_001, msg_003) → send `{"id":"sess-ok","trigger":"regenerate","messageId":"msg_001"}` → assert 422 (msg_001 is not the last)
- **Expected**: Each precondition failure returns the appropriate HTTP error code

---

#### S-tool-01: Partial tool failure — stream continues with available data

- **Method**: script
- **Steps**:
  1. `[POST-CODING: configure a test scenario where one tool fails (e.g., mock yfinance to timeout) while another succeeds (e.g., tavily returns normally)]`
  2. Send `{"id":"sess-600","message":"查 TSMC 股價和最近新聞"}` → capture full stream
  3. Parse events: collect all `data-tool-error` and `tool-result` events
  4. Assert: at least one `data-tool-error` event with a `toolCallId`
  5. Assert: at least one `tool-result` event with a different `toolCallId`
  6. Assert: text-delta events exist after the tool results (agent generated text)
  7. Assert: `finishReason` is `"stop"` (not `"error"`)
- **Expected**: Failed tool gets data-tool-error; successful tool gets tool-result; agent responds with available data

---

#### S-tool-02: All tools fail — agent explains gracefully

- **Method**: script
- **Steps**:
  1. `[POST-CODING: configure all tools to fail (e.g., mock external APIs to return errors)]`
  2. Send `{"id":"sess-601","message":"查 TSMC 股價和新聞"}` → capture full stream
  3. Assert: multiple `data-tool-error` events present
  4. Assert: no `tool-result` events
  5. Assert: text-delta events exist (agent explains the failures)
  6. Assert: `finishReason` is `"stop"`
- **Expected**: All tools fail but stream completes normally with agent explanation

---

#### S-tool-03: Tool error does not expose internal credentials

- **Method**: script
- **Steps**:
  1. `[POST-CODING: configure a tool to raise an exception containing sensitive info, e.g., "ConnectionError: https://api.example.com?api_key=sk-secret-123"]`
  2. Send a message that triggers the failing tool → capture full stream
  3. Parse `data-tool-error` events
  4. Assert: `error` field does NOT contain the string "sk-secret", "api_key=", or any URL with credentials
  5. Assert: `error` field contains a sanitized, human-readable message
- **Expected**: Error message is sanitized at the system boundary

---

#### S-err-01: LLM provider unavailable

- **Method**: script
- **Steps**:
  1. `[POST-CODING: configure the LLM to be unavailable — e.g., invalid API key or mock 503 response]`
  2. Send `{"id":"sess-700","message":"你好"}` → capture full stream
  3. Assert: `start` event present
  4. Assert: `error` event present with non-empty `errorText`
  5. Assert: `finish` event with `finishReason: "error"`
  6. Assert: no text-delta events (LLM never started generating)
- **Expected**: Clean error termination with error + finish(error)

---

#### S-err-02: Error mid-text closes open text block first

- **Method**: script
- **Steps**:
  1. `[POST-CODING: configure LLM to crash after producing partial text — e.g., inject error after N tokens]`
  2. Send `{"id":"sess-701","message":"分析一下市場"}` → capture full stream
  3. Parse events in order
  4. Assert: `text-start` is present
  5. Assert: `text-end` appears before `error` event (if text block was opened)
  6. Assert: `finish` with `finishReason: "error"`
- **Expected**: Open text block closed before error event; lifecycle pairing preserved

---

#### S-err-03: Pending tools remain unresolved on fatal error

- **Method**: script
- **Steps**:
  1. `[POST-CODING: configure scenario where agent emits tool-call-start(s) then a fatal error occurs before tool results]`
  2. Send message → capture full stream
  3. Parse events; collect all `tool-call-start` toolCallIds
  4. Collect all `tool-result`, `tool-error`, `data-tool-error` toolCallIds
  5. Assert: at least one `tool-call-start` toolCallId has NO matching resolution event
  6. Assert: `error` event present
  7. Assert: `finish(error)` present
  8. Assert: NO synthetic `data-tool-error` events were emitted for the unresolved tools (DD-05)
- **Expected**: Orphaned tool calls are not resolved; only StreamError + Finish emitted

---

#### S-err-04: Follow-up request after mid-stream error

- **Method**: script
- **Steps**:
  1. Set up a scenario where a stream error leaves partial checkpoint state in session "sess-703" `[POST-CODING: determine exact setup]`
  2. Send a new message to session "sess-703": `curl -s -N -X POST http://localhost:8000/api/v1/chat/stream -H "Content-Type: application/json" -d '{"id":"sess-703","message":"繼續"}'`
  3. Assert: response is either a valid SSE stream or a clear HTTP error — not a 500 crash or infinite hang
- **Expected**: Corrupted state handled gracefully (no crash)

---

#### S-err-05: Hard crash leaves no finish event

- **Method**: script
- **Steps**:
  1. Start a streaming request in background: `curl -s -N -X POST http://localhost:8000/api/v1/chat/stream -H "Content-Type: application/json" -d '{"id":"sess-crash","message":"Write a very detailed analysis"}' > /tmp/s-err-05.txt & CURL_PID=$!`
  2. Wait 2 seconds for streaming to begin
  3. Kill the server process: `[POST-CODING: determine PID or kill command for the backend]`
  4. Wait for curl to exit (connection closed by server death)
  5. Parse events from /tmp/s-err-05.txt
  6. Assert: no `finish` event present (server died before emitting it)
  7. Assert: curl exit code indicates connection was closed unexpectedly
- **Expected**: No terminal event on hard crash — client must detect via connection close

---

#### S-prog-01: Progress event appears during tool execution

- **Method**: script
- **Steps**:
  1. Send `{"id":"sess-800","message":"查 2330.TW 股價"}` → capture full stream
  2. Parse events; find `data-tool-progress` events
  3. Assert: at least one `data-tool-progress` event exists
  4. Assert: it has `transient: true`
  5. Assert: `data` field contains `status`, `message`, and `toolName`
  6. Assert: the `data-tool-progress` event appears after `tool-call-end` and before `tool-result` for its `toolCallId`
- **Expected**: Progress event correctly positioned in lifecycle with proper format

---

#### S-prog-02: Unmatched progress event does not disrupt the stream

- **Method**: script
- **Steps**:
  1. `[POST-CODING: configure a scenario where a custom chunk has a toolName not matching any pending tool — e.g., inject a stale progress event]`
  2. Send a message → capture full stream
  3. Assert: stream completes normally with `finish(stop)`
  4. Assert: no unexpected error events
- **Expected**: Unmatched progress silently discarded; stream unaffected

---

#### S-prog-03: Parallel same-name tools — ambiguous progress attribution

- **Method**: script
- **Steps**:
  1. `[POST-CODING: configure a scenario where the agent calls the same tool twice in parallel]`
  2. Send a message → capture full stream
  3. Parse `data-tool-progress` events; check their `toolCallId` values
  4. Document: the `toolCallId` on progress events may not match the actual tool instance that emitted the progress (V1 limitation)
  5. Assert: stream completes normally regardless of attribution
- **Expected**: Progress events are emitted but may be attributed to wrong tool call — accepted V1 behavior

---

#### S-conc-01: Second request to active session is rejected

- **Method**: script
- **Steps**:
  1. Start first request in background: `curl -s -N -X POST http://localhost:8000/api/v1/chat/stream -H "Content-Type: application/json" -d '{"id":"sess-900","message":"寫一篇長分析"}' > /tmp/s-conc-01-first.txt & CURL_PID=$!`
  2. Wait 1 second for first request to begin streaming
  3. Send second request: `HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" -X POST http://localhost:8000/api/v1/chat/stream -H "Content-Type: application/json" -d '{"id":"sess-900","message":"第二個問題"}')`
  4. Assert: `HTTP_CODE` is 409
  5. Wait for first request to complete: `wait $CURL_PID`
  6. Parse first request output; assert it completed normally with `finish(stop)`
- **Expected**: Second request gets 409; first request unaffected

---

#### S-conc-02: Different sessions process in parallel

- **Method**: script
- **Steps**:
  1. Start two requests in parallel:
     - `curl -s -N -X POST http://localhost:8000/api/v1/chat/stream -H "Content-Type: application/json" -d '{"id":"sess-901","message":"查 TSMC"}' > /tmp/conc-a.txt & PID_A=$!`
     - `curl -s -N -X POST http://localhost:8000/api/v1/chat/stream -H "Content-Type: application/json" -d '{"id":"sess-902","message":"查 AAPL"}' > /tmp/conc-b.txt & PID_B=$!`
  2. Wait for both: `wait $PID_A $PID_B`
  3. Assert: both outputs contain `finish(stop)` — both completed successfully
  4. Assert: sess-901's response references TSMC; sess-902's response references AAPL (no cross-contamination)
- **Expected**: Both sessions complete independently; no blocking or interference

---

#### S-conc-03: Session is usable after a prior request errors

- **Method**: script
- **Steps**:
  1. Trigger a stream-level error on session "sess-903": `[POST-CODING: configure LLM to fail for first request]`
  2. Send first request → wait for error + finish(error) stream to complete
  3. `[POST-CODING: restore normal LLM operation]`
  4. Send second request: `curl -s -N -X POST http://localhost:8000/api/v1/chat/stream -H "Content-Type: application/json" -d '{"id":"sess-903","message":"hello"}' > /tmp/s-conc-03.txt`
  5. Assert: HTTP 200 (not 409 — lock was released)
  6. Assert: stream contains `finish(stop)` — completed normally
- **Expected**: Session lock released after error; session is not deadlocked

---

#### S-disc-01: Disconnect during streaming cancels agent

- **Method**: script
- **Steps**:
  1. Start request in background: `curl -s -N -X POST http://localhost:8000/api/v1/chat/stream -H "Content-Type: application/json" -d '{"id":"sess-950","message":"寫一篇 TSMC 長篇分析報告"}' > /tmp/s-disc-01.txt & CURL_PID=$!`
  2. Wait 2 seconds for streaming to begin
  3. Kill client: `kill $CURL_PID`
  4. `[POST-CODING: check server logs or Langfuse traces to confirm: (a) agent task was cancelled, (b) Langfuse trace is flushed and closed, (c) no ongoing LLM processing for this request]`
- **Expected**: Server stops processing after disconnect; trace properly closed

---

#### S-disc-02: Full response checkpointed but client saw partial

- **Method**: script
- **Steps**:
  1. Start streaming: `curl -s -N -X POST http://localhost:8000/api/v1/chat/stream -H "Content-Type: application/json" -d '{"id":"sess-951","message":"詳細分析台股走勢"}' > /tmp/s-disc-02.txt & CURL_PID=$!`
  2. Wait 2 seconds; kill client: `kill $CURL_PID`
  3. Count text-delta events received in /tmp/s-disc-02.txt (partial)
  4. Send follow-up: `curl -s -N -X POST http://localhost:8000/api/v1/chat/stream -H "Content-Type: application/json" -d '{"id":"sess-951","message":"你剛剛說了什麼？"}' > /tmp/s-disc-02-followup.txt`
  5. Parse follow-up response
  6. Document: the agent may reference content from the full checkpointed response that the client never received
- **Expected**: Checkpoint contains more than client saw — this divergence is accepted V1 behavior

---

#### S-disc-03: Reconnect to same session after disconnect

- **Method**: script
- **Steps**:
  1. Send a message to session "sess-952", disconnect mid-stream (same as S-disc-01 setup)
  2. Wait 2 seconds for server to process disconnect
  3. Send the same message again: `curl -s -N -X POST http://localhost:8000/api/v1/chat/stream -H "Content-Type: application/json" -d '{"id":"sess-952","message":"查 TSMC 股價"}' > /tmp/s-disc-03.txt`
  4. Assert: HTTP 200 (session lock was released after disconnect)
  5. Send a third request asking about history: `curl -s -N -X POST http://localhost:8000/api/v1/chat/stream -H "Content-Type: application/json" -d '{"id":"sess-952","message":"我問了你幾次問題？"}'`
  6. Document: conversation history may contain the message twice (once from interrupted request, once from reconnect)
- **Expected**: Reconnect succeeds but may produce duplicate messages in history

---

#### S-disc-04: Each turn produces a unique messageId

- **Method**: script
- **Steps**:
  1. Send 3 turns to session "sess-960":
     - Turn 1: `{"id":"sess-960","message":"first"}` → extract `messageId` as M1
     - Turn 2: `{"id":"sess-960","message":"second"}` → extract `messageId` as M2
     - Turn 3: `{"id":"sess-960","message":"third"}` → extract `messageId` as M3
  2. Assert: M1 ≠ M2 ≠ M3 (all unique)
- **Expected**: Every turn gets a unique messageId

---

## Automated Verification — Journey Scenarios

#### J-stream-01: Complete financial analysis conversation

- **Method**: script
- **Steps**:
  1. Turn 1: `curl -s -N -X POST http://localhost:8000/api/v1/chat/stream -H "Content-Type: application/json" -d '{"id":"sess-j001","message":"TSMC 最近表現如何？"}' > /tmp/j01-turn1.txt`
  2. Wait for finish event; extract messageId as M1
  3. Assert: tool-call-start + tool-result present (tool was invoked); data-tool-progress present; finish(stop)
  4. Turn 2: `curl -s -N -X POST http://localhost:8000/api/v1/chat/stream -H "Content-Type: application/json" -d '{"id":"sess-j001","message":"有什麼相關新聞嗎？"}' > /tmp/j01-turn2.txt`
  5. Wait for finish; extract messageId as M2; assert M2 ≠ M1
  6. Concatenate text-delta from turn 2; assert response implies context awareness (references TSMC or stock-related topics without user restating)
  7. Turn 3 (regenerate): Extract M2; `curl -s -N -X POST http://localhost:8000/api/v1/chat/stream -H "Content-Type: application/json" -d '{"id":"sess-j001","trigger":"regenerate","messageId":"'$M2'"}'  > /tmp/j01-regen.txt`
  8. Wait for finish; extract messageId as M3; assert M3 ≠ M2
  9. Assert: regenerated stream completes with finish(stop)
- **Expected**: Three-phase flow (send → context-aware follow-up → regenerate) all complete successfully

---

#### J-regen-01: Regenerate after tool failure recovers successfully

- **Method**: script
- **Steps**:
  1. `[POST-CODING: configure one tool to fail for first invocation]`
  2. Turn 1: Send `{"id":"sess-j-regen","message":"查 TSMC 股價"}` → capture stream → assert `data-tool-error` present; extract messageId as M1
  3. `[POST-CODING: restore tool to normal]`
  4. Regenerate: Send `{"id":"sess-j-regen","trigger":"regenerate","messageId":"'$M1'"}` → capture stream
  5. Assert: regenerated stream has tool-call-start → tool-result (tool succeeds this time)
  6. Assert: finish(stop)
- **Expected**: Regenerate re-executes tools; previously-failing tool now succeeds

---

#### J-tool-01: Tool failure and recovery across turns

- **Method**: script
- **Steps**:
  1. `[POST-CODING: configure yfinance to fail]`
  2. Turn 1: Send `{"id":"sess-j002","message":"查 AAPL 股價和 SEC 10-K 報告"}` → capture stream
  3. Assert: `data-tool-error` for yfinance; `tool-result` for SEC; text response uses SEC data; finish(stop)
  4. `[POST-CODING: restore yfinance to normal]`
  5. Turn 2: Send `{"id":"sess-j002","message":"再試一次查股價"}` → capture stream
  6. Assert: tool-call-start for yfinance; tool-result (success); text references AAPL price
  7. Assert: agent demonstrates context awareness from turn 1 (knows user wants AAPL)
- **Expected**: Tool error in turn 1 → success in turn 2; context preserved across turns

---

#### J-err-01: Fatal error mid-conversation then recovery

- **Method**: script
- **Steps**:
  1. Turn 1: Send `{"id":"sess-j003","message":"你好"}` → wait for finish(stop) — success
  2. `[POST-CODING: configure LLM to fail for next request]`
  3. Turn 2: Send `{"id":"sess-j003","message":"分析市場趨勢"}` → capture stream
  4. Assert: start event present; error event present; finish(error) present
  5. `[POST-CODING: restore LLM]`
  6. Turn 3: Send `{"id":"sess-j003","message":"你好嗎？"}` → capture stream
  7. Assert: HTTP 200 (not 409 — lock was released after error)
  8. Assert: finish(stop) — recovery successful
- **Expected**: Session recovers after stream error; turn 1 context may or may not survive depending on checkpoint state

---

#### J-disc-01: Disconnect then regenerate discards unseen response

- **Method**: script
- **Steps**:
  1. Start stream: `curl -s -N -X POST http://localhost:8000/api/v1/chat/stream -H "Content-Type: application/json" -d '{"id":"sess-j004","message":"詳細分析台積電"}' > /tmp/j-disc-partial.txt & CURL_PID=$!`
  2. Wait 3 seconds; kill client: `kill $CURL_PID`
  3. Wait 2 seconds for server cleanup
  4. Need the messageId from the partial stream: extract from /tmp/j-disc-partial.txt start event as M1
  5. Send regenerate: `curl -s -N -X POST http://localhost:8000/api/v1/chat/stream -H "Content-Type: application/json" -d '{"id":"sess-j004","trigger":"regenerate","messageId":"'$M1'"}' > /tmp/j-disc-regen.txt`
  6. Assert: regenerate stream starts with new messageId M2 ≠ M1
  7. Assert: finish(stop)
  8. Document: the server discarded a potentially complete response that the client never fully received
- **Expected**: Regenerate succeeds but discards the server-complete response — accepted V1 behavior

---

## Manual Verification

### Manual Behavior Test

> Tests that cannot be reliably automated via script due to timing, infrastructure, or external system dependencies.

#### S-err-05: Hard crash leaves no finish event

- **Reason**: Requires killing the server process mid-stream, which is difficult to reliably automate and coordinate with the streaming client
- **Steps**:
  1. Start a streaming request with a long prompt
  2. While streaming, kill the backend process (`kill -9 <pid>`)
  3. Observe curl output — verify no `finish` event was received
  4. Verify curl exits with a connection error
- **Expected**: Stream terminates without terminal event; client detects via connection close

#### S-disc-01: Disconnect during streaming — Langfuse verification

- **Reason**: Langfuse trace verification requires manual inspection of the Langfuse dashboard
- **Steps**:
  1. Execute the automated S-disc-01 steps
  2. Open Langfuse dashboard; find the trace for session "sess-950"
  3. Verify: trace exists and is marked as closed (not pending)
  4. Verify: observations up to the disconnect point are recorded
- **Expected**: Trace properly flushed and closed on disconnect

### User Acceptance Test

> User validates that the overall streaming behavior meets requirements.

#### J-stream-01: Complete financial analysis conversation

- **Acceptance Question**: Does the streaming API correctly support a multi-turn financial analysis workflow?
- **Steps**:
  1. Use curl or a test client to execute the J-stream-01 script
  2. Review: Are SSE events well-formed and in the correct order?
  3. Review: Does the second turn demonstrate context awareness?
  4. Review: Does regenerate produce a new, different response?
  5. Review: Are tool progress events informative?
- **Expected**: Complete, well-ordered streaming with correct tool lifecycle, context continuity, and working regenerate

#### S-tool-03: Tool error sanitization

- **Acceptance Question**: Are tool error messages safe for end-user consumption?
- **Steps**:
  1. Trigger various tool failures (timeout, auth error, network error)
  2. Review `data-tool-error` events in the SSE output
  3. Check: Do any errors expose API keys, internal URLs, file paths, or stack traces?
  4. Check: Are error messages informative enough for the user to understand what went wrong?
- **Expected**: Error messages are sanitized but still informative; no credential leakage
