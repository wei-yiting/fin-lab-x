# Verification Results — S3 Streaming Chat UI

## Meta

- Implementation Plan: `artifacts/current/implementation_streaming_chat_ui.md`
- Generated during Milestone 0+ execution.

## V-1 Result: PASS — S1 接受 partial-turn regenerate（HTTP 200）

- **Probe script**: `scripts/v1-partial-regen-probe.sh`
- **Runner**: `bash scripts/v1-partial-regen-probe.sh`
- **觀察日期**: 2026-04-09
- **Backend**: `http://localhost:8000`，後端版本對應 commit `20fe80d`（feat(backend): SSE streaming chat with AI SDK v6 wire format）
- **Session ID**: `47c5ca1b-f121-4518-b50d-b0a41da55b88`
- **Partial messageId**: `lc_run--019d7058-6b3b-7b23-83e6-4c516b078947`
- **Regen HTTP status**: **`200`**
- **Regen response Content-Type**: `text/event-stream`（fresh SSE stream，含新的 `messageId` 與新一輪 tool calls）

### 觀察過程

1. 對 `POST /api/v1/chat` 送出 finance 查詢（"Give me a detailed analysis of NVDA..."），讓後端 orchestrator 進入 tool-calling 路徑（觸發 `yfinance_stock_quote` / `tavily_financial_search` / `yfinance_get_available_fields`）。
2. curl 用 `--max-time 4` 模擬使用者按下 Stop — exit code `28`（timeout），且捕捉到的 SSE 內**沒有** `finish` chunk，確認這是真正的 partial turn。
3. 從 partial SSE 的 `start` chunk 解出 `messageId`，立即用 `trigger=regenerate` + 同一 session id 對 `POST /api/v1/chat` 送 regenerate 請求。
4. Backend 回 `200 OK` + 新的 SSE stream（新 `messageId`，新一輪 tool-input-available 事件）。

### Raw 證據

**Partial SSE（首 800 bytes）**：

```
data: {"type": "start", "messageId": "lc_run--019d7058-6b3b-7b23-83e6-4c516b078947", "messageMetadata": {"sessionId": "47c5ca1b-f121-4518-b50d-b0a41da55b88"}}

data: {"type": "tool-input-available", "toolCallId": "call_JgNz967iFCq3EzZAbDEQ8HrA", "toolName": "yfinance_stock_quote", "input": {"ticker": "NVDA"}}

data: {"type": "tool-input-available", "toolCallId": "call_DPMJELX9G0gSShnJSMEOhXU1", "toolName": "tavily_financial_search", "input": {"query": "recent news", "ticker": "NVDA"}}

data: {"type": "tool-input-available", "toolCallId": "call_TFizj2nvMTGV149xJTyrSLlO", "toolName": "yfinance_get_available_fields", "input": {"ticker": "NVDA"}}

data: {"type": "data-tool-progress", "id": "call_TFizj2nvMTGV149xJTyrSLlO", "data": {"status": "querying_fields", "message": "Discovering fields for
```

**Regen response（首 1000 bytes，HTTP 200）**：

```
data: {"type": "start", "messageId": "lc_run--019d7058-7ba9-7290-a4e3-861a4da0d0d9", "messageMetadata": {"sessionId": "47c5ca1b-f121-4518-b50d-b0a41da55b88"}}

data: {"type": "tool-input-available", "toolCallId": "call_x4HVElK6yNQpkzeBbv5ujqwn", "toolName": "yfinance_stock_quote", "input": {"ticker": "NVDA"}}

data: {"type": "tool-input-available", "toolCallId": "call_3ojCNr4L1EqziADMEHSpXRPM", "toolName": "tavily_financial_search", "input": {"query": "recent news", "ticker": "NVDA"}}

data: {"type": "tool-input-available", "toolCallId": "call_xiaLeTGd45NgmdVfMagvJJzH", "toolName": "yfinance_get_available_fields", "input": {"ticker": "NVDA"}}

data: {"type": "data-tool-progress", "id": "call_3ojCNr4L1EqziADMEHSpXRPM", "data": {"status": "searching_news", "message": "Searching news for NVDA...", "toolName": "tavily_financial_search", "toolCallId": "call_3ojCNr4L1EqziADMEHSpXRPM"}, "transient": true}
```

### 解讀

對照 prerequisites §4 V-1 的 outcome table：

| HTTP status | 觀察結果 | 對 implementation 的影響 |
|---|---|---|
| **200** + new SSE stream | ✅ **本次觀察結果** | S1 接受 partial-turn 的 regenerate；smart retry 可以直接 regenerate（不需降級為 sendMessage） |

**為什麼 S1 會接受**：閱讀 `backend/api/routers/chat.py` + `backend/agent_engine/agents/base.py::_find_regenerate_target` 後可確認 — backend 的 validate_regenerate 是對 LangGraph checkpointer 持久化後的 state 做查詢，而 LangGraph 在 tool-call AIMessage 產生的瞬間就會把該 message 寫進 checkpoint。所以即使 client 半路 disconnect，那個帶 tool_calls 的 partial AIMessage 已經在 state 中以 `lc_run--019d7058-6b3b-...` 這個 ID 存在；regenerate 走 `_find_regenerate_target` 時會把它認定為 "last AI turn"、通過 message_id 比對、然後走 `_prepare_regenerate` 把它連同後續所有 messages remove 掉再重跑 — 這就是 200 的成因。

### Action

**No implementation change needed for the design's smart-retry path — but the design's *default assumption* should be flipped from 422 to 200.**

具體影響：

1. **Q-USR-7 smart retry strategy**: 設計文件原本假設「S1 拒絕 partial turn → smart retry 必須降級為 `sendMessage(originalUserText)`」。實測 S1 接受 → smart retry 可以直接呼叫 `regenerate({ messageId })`，但仍**必須**處理一個現實限制（見下方 caveat）。
2. **BDD `S-regen-03`** (regenerate after stop)：原本寫成 fallback 路徑（sendMessage 重發），現在可以改成直接 regenerate 路徑；BDD scenario 仍應保留 happy-path 斷言「assistant message 被替換成新一輪內容」。
3. **BDD `S-err-04`** (regenerate after error)：happy path 成立，可直接走 regenerate trigger。

### Frontend messageId mapping — AI SDK v6 actually handles this for us

第一輪 V-1 報告原本擔心「backend `start` chunk 的 `lc_run--...` messageId 不會自動寫進 `UIMessage.id`，需要 ChatPanel 自行 stash」。**追加實證後修正：這個擔心是錯的**。

直接讀 `frontend/node_modules/ai/dist/index.js` 的 chat store reducer（行 5813-5821）：

```js
case "start": {
  if (chunk.messageId != null) {
    state.message.id = chunk.messageId;   // ← backend ID 直接覆蓋進 UIMessage.id
  }
  await updateMessageMetadata(chunk.messageMetadata);
  ...
}
```

並對照 `UIMessageChunk` type（`index.d.ts` 行 2264-2266）：

```ts
| {
    type: 'start';
    messageId?: string;
    messageMetadata?: METADATA;
}
```

⇒ AI SDK v6 在收到第一個 `start` chunk 的當下就把 `chunk.messageId` 直接寫進 `state.message.id`。`messages` array 內的對應 UIMessage `.id` 從那一刻起就是 backend 發的 `lc_run--...`，**不是** client 端 generate 的 UUID。所以 `regenerate({ messageId: lastAssistantMessage.id })` 直接就會送對的 ID，**不需要**手動 stash、不需要 onData 攔截、不需要 transport-layer hack。

此修正同時解掉了「Task 5.2 額外 sub-requirement」的負擔 — Task 5.2 的設計其實已經正確（就用 `last.messageId`，那個值天然就是 backend ID）。

### 一個需注意的 race window

雖然這次觀察到 200，但觸發成功的前提是：
1. Backend 在 client disconnect 之前已經至少 emit 過一個 tool-call AIMessage（讓 LangGraph checkpoint 把它持久化）。
2. 若 client 在 LLM 第一個 token 還沒出來前就斷線（極短 partial），LangGraph 可能還沒寫 checkpoint，那時 `_find_regenerate_target` 會 fall back 到上一個完整的 AI turn（可能是不相關的舊 message）或 raise `"No assistant message to regenerate"` → HTTP 404。

**Implementation guidance**：
- Smart retry **應該** 直接呼叫 `regenerate({ messageId })`，但**必須** catch 任何 4xx response（404 = no AI message，422 = messageId mismatch）並降級為 `sendMessage(originalUserText)`。
- 換句話說：design 的 "default 422 fallback" 路徑**仍然要實作**作為防禦網，只是它從「always-on default」變成「exception handler」（而且必須涵蓋 404，不只是 422）。

### 結論

- **V-1 outcome**: HTTP `200` — direct-regen path 可用。
- **Action**:
  1. **不需要** 改 ChatPanel 整體架構。
  2. **不需要** 額外 stash backend messageId — AI SDK v6 已經把 `start.messageId` 寫進 `UIMessage.id`，`regenerate({ messageId: lastAssistantMessage.id })` 天然送對的 ID。
  3. **要** 把 Task 5.2 的 retry classifier fallback condition 從「`pre-stream-422`」放寬到「任何 4xx」（涵蓋 race-window 的 404）— 修改 `lib/error-classifier.ts` enum 多 `'pre-stream-4xx'` 或在 `handleRetry` 改用範圍判斷。
  4. **要** 在 Task 5.2 description 補一行 BDD scenario interpretation：S-regen-03 / S-err-04 happy path 走直接 regenerate（之前的設計假設這條會 fallback 到 sendMessage，現在改成 happy path 直接成立）。


## V-2 Result: PASS — useChat pre-stream HTTP 500 user-message lifecycle

- **Contract test**: `frontend/src/__tests__/contract/use-chat-error-lifecycle.test.ts`
- **Runner**: `pnpm vitest run src/__tests__/contract/use-chat-error-lifecycle.test.ts --reporter=verbose`
- **Result**: 1 passed / 0 failed（`Tests 1 passed (1)`）
- **Assertions confirmed**：
  - `result.current.error` 在 HTTP 500 之後成為 truthy（MSW 攔截 `POST /api/v1/chat` 回 500）。
  - `result.current.messages.length === 1`
  - `result.current.messages[0].role === 'user'`
- **結論**：AI SDK v6（`@ai-sdk/react@3.0.144` + `ai@6.0.142`）在 pre-stream HTTP 500 時**會保留** user message 在 `messages` array 中。`BDD S-err-02` 與 `Ch-Dev-1` 所假設的「user bubble 還在」前提成立，`ChatPanel` **不需要**自己做 `lastUserText` stash/restore（至少對此 SDK 版本而言）。

### Plan defect found — TC-int-v2-01 import path
- `artifacts/current/implementation_test_cases_streaming_chat_ui.md` lines 1637–1640 的 verbatim 版本寫：
  ```ts
  import { useChat, DefaultChatTransport } from '@ai-sdk/react'
  ```
- 但在實際安裝的 AI SDK v6 中，`@ai-sdk/react` 僅 re-export `CreateUIMessage` / `UIMessage` / `UseCompletionOptions`，`DefaultChatTransport` 住在 `ai` package。直接照抄會得到 `TypeError: DefaultChatTransport is not a constructor`，而非 V-2 contract 結果。
- 已在 test file 中修正為：
  ```ts
  import { useChat } from '@ai-sdk/react'
  import { DefaultChatTransport } from 'ai'
  ```
- **行動建議**：後續更新 `implementation_test_cases_streaming_chat_ui.md` 的 TC-int-v2-01 範例（以及 TC-int-v3-01 若引用相同 import），避免 Milestone 1+ 工作者再次踩到同一個坑。此問題與 V-2 contract 本身無關，純粹是計畫文件的 import-path typo。

### Additional notes
- Vitest 設定 `globals: false`，因此 test file 最頂端額外加上 `import { test, expect, beforeAll, afterAll } from 'vitest'`（計畫的 verbatim 片段未包含）。
- `msw@2.13.2` 已加入 `frontend/package.json` devDependencies（僅套件本身，未執行 `pnpm dlx msw init public/`，service worker 初始化屬 M1 範疇）。

## V-3 Result: PASS — useChat.stop() abort semantic

- **Contract test**: `frontend/src/__tests__/contract/use-chat-stop-semantic.test.ts`
- **Runner**: `pnpm vitest run src/__tests__/contract/use-chat-stop-semantic.test.ts --reporter=verbose`
- **Result**: 1 passed / 0 failed（`Tests 1 passed (1)`，duration ≈ 117ms — 遠低於 fixture 的 5s 長尾，證明 `stop()` 真的有中斷 stream。註：實作初稿曾經報 ~246ms 的 PASS，但那是 false positive；詳見下方 plan-defect post-mortem。）
- **Assertions confirmed**：
  - `result.current.status` 在 `await result.current.stop()` 之後成功 transition 回 `'ready'`（`waitFor` 成功 resolve）。
  - `result.current.error` 在 stop 之後維持 `undefined`（**未** 被 `AbortError` 污染成 truthy）。
- **結論**：AI SDK v6（`@ai-sdk/react@3.0.144` + `ai@6.0.142`）的 `useChat().stop()` 在 streaming 中途呼叫時，會 cleanly 中斷 fetch、把 status 拉回 `'ready'`、且**不會**把 `AbortError` 寫入 `error` field。BDD scenarios `S-stop-01/02/03` 假設的「stop 後 status 立即回 ready、error 保持 nil」前提**成立**。`ChatPanel.handleStop` **不需要** wrap try-catch + filter `AbortError` + 強制 `setStatus`，可直接呼叫 `useChat().stop()`。

### Plan defect found — V-3 verbatim snippet uses `.toBeNull()` on a field typed `Error | undefined`
- `artifacts/current/implementation_prerequisites_streaming_chat_ui.md` Section 4 V-3（行 617）的 verbatim 寫法是：
  ```ts
  expect(result.current.error).toBeNull() // 不能變 'error' 狀態
  ```
- 但 AI SDK v6 中 `useChat()` 回傳的 `error` 型別是 `Error | undefined`（不是 `Error | null`），參見 `node_modules/@ai-sdk/react/dist/index.d.ts`：
  ```ts
  error: Error | undefined;
  ```
  在 clean abort 路徑下 `error` 從未被 set，所以實際值是 `undefined`，原版 assertion 會誤報 `AssertionError: expected undefined to be null`，看起來像 V-3 FAIL，但其實是測試 assertion 用錯 matcher。
- 已在 test file 修正為符合 SDK type 的兩段 assertion（保留 contract 的「無 error」語意）：
  ```ts
  expect(result.current.error).toBeUndefined()
  expect(result.current.error).toBeFalsy()
  ```
- **行動建議**：後續更新 `implementation_prerequisites_streaming_chat_ui.md` Section 4 V-3 範例（行 617），把 `.toBeNull()` 換成 `.toBeUndefined()`，避免 Milestone 1+ 工作者再次踩到。此問題與 V-3 contract 本身無關，純粹是計畫文件對 AI SDK type 的記憶錯誤；BDD scenarios 用的「error stays nil」自然語言仍然成立（`undefined` 即為 nil 的一種具體形式）。

### Additional notes
- 同樣需要顯式 `import { test, expect, beforeAll, afterAll } from 'vitest'`（Vitest `globals: false`）。
- MSW handler 用 `delay(5000)` 模擬長 stream，但測試只跑 ~117ms，證明 `stop()` 的 abort 訊號的確 propagate 到 `fetch` underlying 的 `AbortController`，而不是讓 test runner 等到 stream 自然結束。
- 結論可繼續放行 BDD `S-stop-01/02/03` 的設計與 M5 ChatPanel 的 `handleStop` 直接呼叫策略。

### Plan defect found — `text-delta` payload field name (silent killer for M1+ fixtures)
- 第一輪 V-3 用了 plan verbatim 的 `textDelta` field name，例如：
  ```ts
  { type: 'text-delta', id: 't1', textDelta: 'hello' }
  ```
  測試 PASS，但**這是 false positive** — 因為 SDK 收到的 chunk 不是 `text-delta` schema 的合法 shape，SDK 直接把該 part 丟掉，stream 等於沒有 in-flight text；於是 `stop()` 看起來「幾乎立刻」就回 `'ready'`。
- 改成正確的 field 名稱（`delta`，與 `node_modules/ai/dist/index.d.ts` 的 v6 type 與 backend `sse_serializer.py` 一致）後，stream 真的有正在 process 的 text part，原版測試會在 `waitFor(ready)` 卡住超過 1 秒並失敗 — 但這**也是 false negative**，因為 MSW handler 沒有監聽 `request.signal.abort`，client 端 fetch abort 後 server 端 stream 依然停在 `await delay(5000)`，client side 的 SDK 一直等不到 stream end。
- 真正的 V-3 contract test 必須同時滿足兩個條件：
  1. 用正確的 `delta` field（與 SDK / backend 一致），讓 SDK 真的解析 chunk。
  2. MSW handler 監聽 `request.signal.abort`，當 client 端 stop 時也關掉 server 端 stream，讓 SDK 看到 end-of-stream。
- 修正後的版本 PASS in ~117ms，這才是真正成立的 V-3 contract（status → 'ready'，error 仍 undefined）。
- **行動建議**：
  - `implementation_prerequisites_streaming_chat_ui.md` Section 2 fixture types（`UIMessageChunk`）+ §3 fixture 範例 + §4 V-3 範例：所有 `text-delta` chunk 一律使用 `delta` field（已批次修正完成）。
  - `implementation_test_cases_streaming_chat_ui.md`：同一個 typo 出現在 4 個地方（已批次修正）。
  - M1 `__tests__/msw/handlers.ts` 與所有 streaming fixture 寫法都必須監聽 `request.signal.abort` 並關閉 stream，否則 `S-stop-*` 系列 BDD scenarios 會 false-fail。本檔的 `use-chat-stop-semantic.test.ts` 可作為 reference。
