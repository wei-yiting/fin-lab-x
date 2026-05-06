# Verification Plan

## Meta

- Scenarios Reference: `artifacts/current/bdd-scenarios.md`
- Design Reference: `artifacts/current/design.md`
- Generated: 2026-05-01
- Verification 環境：real backend (per memory `feedback_msw_vs_real_backend.md`)；browser-level via **Playwright + video recording**（repeatable CI guardrail，commit 進 `frontend/tests/e2e/`）；Browser-Use CLI 僅用於 agent-driven 一次性探索（不適用於本期 BDD 驗證）；Braintrust eval host CLI (per memory `feedback_braintrust_host_only.md`)
- Langfuse trace 驗證：每次 stream 結束 polling with retry + backoff（5s 內最多 retry 5 次）等 SDK flush，per memory `feedback_tracing_verification.md`

## 共用變數 / canonical prompt

```bash
BACKEND_BASE="http://localhost:8000"           # [POST-CODING: confirm chat stream endpoint base URL]
FRONTEND_BASE="http://localhost:5173"          # [POST-CODING: confirm frontend dev server URL]
LANGFUSE_API_BASE="https://cloud.langfuse.com" # or self-hosted instance per env
PROMPT="Compare Apple's 10-K fiscal year 2024 vs 2023 Item 1A risk factors and categorize changes (added / strengthened / removed)"
```

`PROMPT` 是 D25 canonical reasoning-rich prompt。所有 deterministic 跟 browser 場景共用。

## 共用 helper：Langfuse trace 等待與篩選

```bash
# 等 Langfuse SDK flush 完成（async, 1-2s 為常態，5s timeout）
wait_for_trace_flush() {
  local TRACE_ID="$1"
  for i in 1 2 3 4 5; do
    sleep 1
    if curl -s -H "Authorization: Bearer $LANGFUSE_KEY" \
            "$LANGFUSE_API_BASE/api/public/traces/$TRACE_ID" | jq -e '.observations | length > 0' > /dev/null; then
      return 0
    fi
  done
  return 1
}

# 取一個 trace 內所有 chat_model spans
get_chat_model_spans() {
  local TRACE_ID="$1"
  curl -s -H "Authorization: Bearer $LANGFUSE_KEY" \
       "$LANGFUSE_API_BASE/api/public/traces/$TRACE_ID" \
    | jq '[.observations[] | select(.name == "chat_model.invoke")]'
}
```

---

## Operator Runtime Guide

> 此章節吸收原本要寫進 `scripts/bdd/README.md` 的內容 — 視覺 lifecycle scenarios 的 dev flag 操作說明跟 6-case matrix 跑法集中在這裡，避免雙頭文件 drift。

### Dev-only feature flags

下列 6 個 env flag 由 Task 15 在 backend 加 `if os.environ.get(...)` 守衛實作；**只在 BDD 場景 inline 命令裡 set，正式 deploy 不應出現**：

| Env flag | 觸發行為 | 對應 BDD scenario |
|----------|----------|-----------------|
| `FORCE_LLM_FAIL=1` | 第一個 LLM call raise → mid-stream error | S-stream-04 mid-stream sub-case |
| ~~`STUB_LLM_HANG=1`~~ | ~~LLM provider 永不回應~~ | **移出本期 scope** — backend keepalive + first-chunk timeout（原 Task 13）整體挪到後續 PR；hung sub-case 不驗 |
| `FORCE_REASONING_NON_TRANSIENT=1` | SSE serializer 故意漏 `transient: true` flag | S-chan-03 |
| `EMIT_DELAYED_REASONING=1` | Emit 第一個 reasoning chunk 後強制 backend silence ≥12s 才 emit 下一個 | S-rsn-06 stalled 視覺 |
| `EMIT_LATE_REASONING=1` | `finish` 後 100ms 多 emit 一個 `data-reasoning-status` | S-rsn-12 |
| `STUB_REASONING_ONLY=1` | Emit reasoning blocks 後直接 finish，不 emit text/tool | S-trace-05 |
| `STUB_CONTENT_BLOCKS_NO_REASONING=<provider>` | 模擬該 provider `content_blocks` normalizer 失敗 | S-trace-09 |

操作範例（在 Playwright spec 內注入 dev flag）：
```typescript
// frontend/tests/e2e/lifecycle/reasoning-channel-isolation.spec.ts
test('S-chan-03 — non-transient flag drop is filtered by frontend', async ({ page }) => {
  // Dev flag 由 backend 啟動時 env 帶入；spec 假設已起一個對應 instance
  await page.goto(process.env.FRONTEND_BASE + '/chat');
  // ... per-scenario 步驟
});
```
Backend 起動命令 (operator 在 PR 上跑): `FORCE_REASONING_NON_TRANSIENT=1 uvicorn backend.api.main:app --port 8001 &` 然後 spec 用對應 `process.env.BACKEND_BASE` 連線。

### 6-case acceptance matrix（J-stream-01 ship gate）

由 Playwright spec 接管，無需 shell wrapper。命令：

```bash
cd frontend && npx playwright test tests/e2e/critical/multi-provider-matrix.spec.ts --grep @critical
```

Spec 內部 iterate 6 個 parameterized cases（3 providers × 2 reasoning modes），fixture 來自 `frontend/tests/e2e/critical/fixtures/agent-capability/`，video 自動錄到 `frontend/test-results/`。每個 case 結束 emit `trace_id` 到 stdout 給下游 verifier 用。

### Langfuse trace verifier CLI

```bash
uv run python backend/scripts/validation/verify_langfuse_trace.py $TRACE_ID \
    --expect-reasoning-on        # or --expect-reasoning-off / --expect-unsupported / --expect-aborted
```

Helper 等 Langfuse SDK flush（5×1s backoff）後對 chat_model span 執行 D29 schema 驗證 + D35 abort schema 驗證。Output JSON summary 給 shell 解析。

---

## Automated Verification — Deterministic

Backend 行為用 curl / script + Langfuse trace API 驗證。各 step 之間 chain state（前 step output 餵下 step input）。

### S-stream-01: Default agent 跑 canonical SEC query 完成 streaming

- **Method**: script + Langfuse trace API
- **Steps**:
  1. `SESSION_ID=$(uuidgen)`
  2. 送 query 到 default agent v3：`curl -s -N -X POST $BACKEND_BASE/api/v1/chat/stream -H "Content-Type: application/json" -d "{\"id\":\"$SESSION_ID\",\"agentVersion\":\"v3\",\"message\":\"$PROMPT\"}" > /tmp/s-stream-01.txt`
  3. 等 stream 完成（grep `[DONE]` 或 `finish` event）
  4. 從 SSE log 取出 `start` event 內 `traceId`：`TRACE_ID=$(grep '"type":"start"' /tmp/s-stream-01.txt | jq -r '.traceId')`
  5. `wait_for_trace_flush "$TRACE_ID"`
  6. 檢查 trace 內所有 chat_model span 的 model field：`get_chat_model_spans "$TRACE_ID" | jq '.[] | .input.metadata.ls_model_name'`
  7. Assert: 全部 model 字串 match `gemini-2.5-flash`（或 LangChain `init_chat_model("google_genai:gemini-2.5-flash")` 對應的 model field）
  8. Assert: SSE log 無 `error` event
- **Expected**: Stream 完成；Langfuse trace 確認 default v3 用 Gemini 2.5 Flash 跑

### S-stream-02: 切換 agent version 在同一 session 內，新 turn 仍走 Gemini

- **Method**: script + Langfuse trace API + DB inspection
- **Steps**:
  1. `SESSION_ID=$(uuidgen)`
  2. 跑 3 個 turn 在 v3：迴圈三次 `curl -s -N -X POST $BACKEND_BASE/api/v1/chat/stream ... agentVersion=v3 message="turn-N"`
  3. 切換 agent 到 v5：`curl -s -X POST $BACKEND_BASE/api/v1/sessions/$SESSION_ID/agent -d '{"agentVersion":"v5"}'`（[POST-CODING: confirm agent-switch endpoint shape]）
  4. 送新 query：`curl -s -N -X POST $BACKEND_BASE/api/v1/chat/stream ... agentVersion=v5 message="$PROMPT" > /tmp/s-stream-02-newturn.txt`
  5. 從 SSE log 取 `traceId`，wait flush，檢查 chat_model spans model 仍為 `gemini-2.5-flash`
  6. 檢查 session messages：`curl -s $BACKEND_BASE/api/v1/sessions/$SESSION_ID/messages` 確認前 3 turn 的 assistant `parts`（text + tool 內容）完整保留
- **Expected**: 新 turn 走 Gemini；前 3 turn parts 完整；session 沒被切換破壞

### S-stream-03: Multi-provider × multi-mode 矩陣 streaming 行為

- **Method**: script (table-driven 6 runs)
- **Steps**: 對每個 row 跑：
  1. 設 agent config 對應 `<provider>` + `<mode>`（[POST-CODING: 確認 agent config / model binding 設定機制]）
  2. `SESSION_ID=$(uuidgen)`，`curl -s -N -X POST $BACKEND_BASE/api/v1/chat/stream ... -d "{\"id\":\"$SESSION_ID\",\"message\":\"$PROMPT\"}" > /tmp/s-stream-03-$row.txt`
  3. 從 SSE log count `data-reasoning-status` events：`grep -c '"type":"data-reasoning-status"' /tmp/s-stream-03-$row.txt`
  4. 從 SSE log 取 `traceId`，wait flush
  5. 檢查 trace 內每個 chat_model span 都有 `metadata.reasoning` key（不論 value）
  6. Assert event count 對應 expected：`reasoning-on` rows count ≥ 1；`reasoning-off` rows count = 0
  7. Assert SSE log 無 `error` event
- **Expected**: 6 rows 全部 streaming 完成；reasoning event count 跟 trace metadata key 都符合 D25 / D29 規格

### S-stream-04: Provider boot 失敗於不同階段對應不同 surface

- **Method**: script + log inspection (2 sub-cases — hung sub-case 隨 Task 13 移出本期 scope)
- **Steps**: 對每個 failure_state 跑：
  1. **Pre-SSE-open**: 暫時 unset `GOOGLE_API_KEY`（[POST-CODING: 確認 env load 機制 / restart 需求]），`curl -s -N -w "%{http_code}" -X POST $BACKEND_BASE/api/v1/chat/stream ... > /tmp/s-stream-04-presse.txt`
     - Assert: HTTP status 為 5xx（500 / 502 / 503）；body 不是 SSE format；frontend useChat onError callback 觸發（用 browser test 驗 [見 S-stream-04-fe]）
  2. **Mid-stream**: 故意把 first LLM call 設定為會 raise（[POST-CODING: stub mechanism — e.g., env var `FORCE_LLM_FAIL=1`]），送 query
     - Assert: SSE 有打開（200 status）；first event 為 `error` event；無 reasoning / text events
  3. ~~**Hung**~~: 已移出本期 scope（Task 13 backend first-chunk-only timeout 未實作；hung 行為等同 main：無自動偵測，user 需手動 Stop 才終止）
- **Expected**: 兩路分流符合 D23 簡化版 protocol（pre-SSE-open / mid-stream）；client-facing surface 分別為 HTTP error / SSE error event。Hung case 留待 backend keepalive + timeout 在後續 PR 補上後驗。

### S-stream-05: Batch eval `.invoke` 也產出 Langfuse reasoning trace

- **Method**: Python script + Langfuse trace API
- **Steps**:
  1. 跑 invoke：`python -c "from agent_engine.orchestrator import Orchestrator; r = Orchestrator().invoke(query='$PROMPT', agent_version='v3'); print(r.trace_id)" > /tmp/s-stream-05-traceid.txt`
  2. `TRACE_ID=$(cat /tmp/s-stream-05-traceid.txt)`，`wait_for_trace_flush "$TRACE_ID"`
  3. `get_chat_model_spans "$TRACE_ID" | jq '.[] | .metadata.reasoning'`
  4. Assert: 每個 chat_model span 都有 `metadata.reasoning` key 且 non-empty（per D29 reasoning-on 條件）
  5. **Cross-path equivalence check**：對相同 `$PROMPT` 跑一次 streaming version (S-stream-01 步驟)，比對 streaming-path span vs invoke-path span 的 `metadata.reasoning` 內容語義等價（substring match，allow 自然差異 D36）
- **Expected**: invoke path 跟 streaming path 產出 reasoning content 等價的 Langfuse traces

### S-stream-06: 90 秒 reasoning silence 不被 proxy 中斷 — **移出本期 scope**

> Task 13（backend SSE keepalive + first-chunk timeout）整體挪到後續 PR，此 scenario 對應的 backend behavior 不存在於本期，無從驗證。等 backend keepalive 在另立 PR 完成後再恢復此 scenario。

### S-stream-07: 同 session 兩 tab 並發 streaming 不互相污染

- **Method**: script (concurrent)
- **Steps**:
  1. `SESSION_ID=$(uuidgen)`
  2. 並發兩 request：
     ```bash
     curl -s -N -X POST $BACKEND_BASE/api/v1/chat/stream ... -d "{\"id\":\"$SESSION_ID\",\"message\":\"What is Apple's revenue\"}" > /tmp/s-stream-07-A.txt &
     curl -s -N -X POST $BACKEND_BASE/api/v1/chat/stream ... -d "{\"id\":\"$SESSION_ID\",\"message\":\"What is Microsoft's revenue\"}" > /tmp/s-stream-07-B.txt &
     wait
     ```
  3. 從各 stream log 取出 `traceId` 兩個值（應該不同）
  4. `wait_for_trace_flush` for both
  5. 檢查 trace A 的 chat_model spans 的 `metadata.reasoning` 不含「Microsoft」字眼；trace B 不含「Apple」字眼
  6. 檢查 stream log A 跟 B 的 `data-reasoning-status` events text 各自獨立（A 不出現 Microsoft、B 不出現 Apple）
- **Expected**: D33 per-request mapper isolated；兩 trace 內容無 cross-contamination

### S-stream-08: Abort 後立即 resend 同 session 仍可運作

- **Method**: script + Langfuse
- **Steps**:
  1. `SESSION_ID=$(uuidgen)`
  2. 啟動 stream 並 capture PID：`curl -s -N -X POST $BACKEND_BASE/api/v1/chat/stream ... -d "{\"id\":\"$SESSION_ID\",\"message\":\"$PROMPT\"}" > /tmp/s-stream-08-aborted.txt & CURL_PID=$!`
  3. 等 5s 確保 reasoning streaming 已開始：`sleep 5`
  4. `kill $CURL_PID`
  5. 從 partial SSE log 取 `traceId_1`，`wait_for_trace_flush "$traceId_1"`
  6. Assert: trace_1 root `agent.run` span `metadata.status == "aborted"`（per D35）
  7. 立即送新 query：`curl -s -N -X POST $BACKEND_BASE/api/v1/chat/stream ... -d "{\"id\":\"$SESSION_ID\",\"message\":\"What's Tesla's market cap\"}" > /tmp/s-stream-08-newturn.txt`
  8. 等 stream 完成；確認新 trace_id_2 完整、`metadata.status` 不為 aborted（無此 key 或為 completed）
  9. Assert: 新 turn 不 inherit 前 turn 的 stale state（response coherent，含 Tesla 相關內容）
- **Expected**: Abort cleanup protocol 完整跑完；後續 turn 不被污染

### S-stream-09: 80 字 char-count fallback 在 CJK 無終止符 case 觸發 soft-emit

- **Method**: pytest unit-level + integration script
- **Steps (unit)**:
  1. 構造 `ReasoningSegmenter` instance
  2. 呼叫 `feed("先看 10-K 結構並比對 Item 1A 跟 Item 7 找出 risk factors 變化包括新增加強刪去三類")`（85 個 CJK 字元無終止符）
  3. Assert: feed yield 出 1 個 sentence（80-char fallback 觸發 soft-emit）
  4. Assert: 餘下 5 字元保留在 internal buffer
  5. 補餵 `feed("再繼續處理")` 確認新一段 buffer 從 0 開始累積
- **Steps (integration)**:
  1. `[POST-CODING: stub provider 強制 emit 一個 110 字元 CJK reasoning chunk 無 `。`]`
  2. 跑 stream：`curl -s -N -X POST $BACKEND_BASE/api/v1/chat/stream ... > /tmp/s-stream-09.txt`
  3. 解析 SSE log，count `data-reasoning-status` events 在該 LLM call 內
  4. Assert: 至少 1 個 event 的 text 內容對應前 80 字元的 reasoning 段落（non-empty 在 LLM-call 結束前出現）
- **Expected**: D26 char-count fallback 確保 CJK 無終止符 case 在 streaming 期間仍 emit reasoning event；不須等 LLM-call boundary flush

### S-chan-01: Streaming 期間 reasoning 不在 persisted message body

- **Method**: script (SSE log inspection) + Playwright DOM polling
- **Steps**:
  1. 跑 stream：`curl -s -N -X POST $BACKEND_BASE/api/v1/chat/stream ... -d "{\"message\":\"$PROMPT\"}" > /tmp/s-chan-01.txt`
  2. 解析 SSE events，分類為 `data-reasoning-status` (transient) 跟其他 persistent type (`text-*` / `tool-*`)
  3. Assert: 所有 `data-reasoning-status` events payload 內 `transient: true`
  4. Assert: 沒有任何 reasoning sentence text 出現在 persistent type events 的 content
  5. **Mid-stream DOM check** (Playwright)：見 `frontend/tests/e2e/lifecycle/reasoning-channel-isolation.spec.ts` 內對 mid-stream DOM 的 polling assertion（與 J-chan-01 共用 spec）
- **Expected**: SSE wire 上 reasoning event 都有 transient flag；無 reasoning text 滲入 persistent events

### S-chan-02: Page reload 後 transcript 不顯示 reasoning

- **Method**: script + Playwright（混合）
- **Steps (script 部分)**:
  1. 完成一個 reasoning-on multi-call turn：`SESSION_ID=$(uuidgen)`，跑 stream，等完成
  2. `curl -s $BACKEND_BASE/api/v1/sessions/$SESSION_ID/messages > /tmp/s-chan-02-rehydrated.json`
  3. 解析每個 assistant message 的 `parts` array
  4. Assert: 沒有 part 的 `type` 開頭為 `data-reasoning-`；沒有 part 的 text content 包含原 reasoning sentences
  5. **Resume turn 階段**：在同 session 送下一個 turn `curl -s -N -X POST $BACKEND_BASE/api/v1/chat/stream ... -d "{\"id\":\"$SESSION_ID\",\"message\":\"follow-up\"}" > /tmp/s-chan-02-followup.txt`
  6. 解析 followup SSE log：assert LangGraph state-replay 階段（在第一個 chat_model.invoke 之前）**不**含 `data-reasoning-status` events；只有第二個 turn 自己 emit reasoning
- **Expected**: Rehydration response 純 text+tool；resume turn 不 re-emit 過去 reasoning

### S-chan-03: Frontend filter 阻擋意外進入 parts 的 reasoning event

- **Method**: Playwright spec + dev tools fault injection
- **Steps**:
  1. `[POST-CODING: 加 dev-only feature flag e.g. FORCE_REASONING_NON_TRANSIENT=1，讓 SSE serializer 故意不送 transient flag]`
  2. `await page.goto($FRONTEND_BASE/chat)`
  3. 送 query 觸發 reasoning：`await page.fill("[data-testid=chat-input]", "$PROMPT")` → `await page.click("[data-testid=send]")`
  4. 等 stream 完成：`await page.waitForSelector("[data-status='ready']")`
  5. `await page.screenshot({ path: "/tmp/s-chan-03-final.png" })`
  6. Assert: 螢幕上的 transcript 無 reasoning sentence 出現（filter 阻擋成功）
  7. 檢查 DOM：`await page.locator("[data-testid=assistant-message]").innerText()` 不含原 SSE log 的 reasoning text
  8. Cleanup feature flag
- **Expected**: 即使 backend 違反 transient contract，frontend filter (D39.b) 仍阻擋 reasoning 進入渲染

### S-chan-04: Backend SSE serializer assert + warn missing flag

- **Method**: pytest unit-level + production log inspection
- **Steps**:
  1. **Dev/CI mode** unit test: 直接呼叫 `serialize_event(ReasoningStatus(...))` 並 monkey-patch payload 移除 `transient: true` → assert raise AssertionError
  2. **Prod mode**: deploy with `LOG_LEVEL=WARNING`，跑同樣 fault injection (S-chan-03 機制)，inspect logs 確認 warning log 含 `"reasoning SSE event missing transient flag"`
- **Expected**: D39.c assert 在 dev/CI raise，prod 改為 warning log

### S-rsn-10: 最後一句 synthesizing reasoning 在 text-start 之前送達 frontend

- **Method**: script (SSE log timestamp inspection)
- **Steps**:
  1. 跑 stream：`curl -s -N -X POST ... -d "{\"message\":\"$PROMPT\"}" > /tmp/s-rsn-10.txt`
  2. 解析 SSE log 的 events 順序
  3. 找出最後一個 `data-reasoning-status` event 跟其後第一個 `text-start` event 的 timestamp / line index
  4. Assert: `data-reasoning-status` line index < `text-start` line index（hold-and-flush ordering D28）
  5. **Playwright 補充**：對應 spec 用 `use.video: 'on'` 錄 video，slow-motion playback 檢查 reasoning text "整理新增/加強/刪去 三類" visible at least 1 frame；見 J-rsn-01
- **Expected**: SSE wire 順序保證 final reasoning 在 text-start 前；視覺驗證留 browser flow

### S-rsn-12: Finish 後 late-arriving data-* events 不出現 ghost indicator

- **Method**: Playwright spec + fault injection
- **Steps**:
  1. `[POST-CODING: 加 dev-only feature flag e.g. EMIT_LATE_REASONING=1，讓 backend 在 finish 後 100ms 多送一個 data-reasoning-status]`
  2. `await page.goto($FRONTEND_BASE/chat)`
  3. 送 query 完成：`await page.fill("[data-testid=chat-input]", "$PROMPT")` → `click send` → `await page.waitForSelector("[data-status='ready']")`
  4. `await page.waitForTimeout(2s)`（等 late event 抵達 + render 機會）
  5. `await page.screenshot({ path: "/tmp/s-rsn-12-after-finish.png" })`
  6. Assert: 螢幕上 ReasoningIndicator 不可見（finishedRef guard 生效）
  7. Cleanup flag
- **Expected**: Late event 被 finishedRef ignore；無 ghost re-appear

### S-trace-01: Reasoning-on multi-call turn 對應 N 個獨立 chat_model spans

- **Method**: script + Langfuse trace API
- **Steps**:
  1. 跑 stream：`SESSION_ID=$(uuidgen)`，`curl ... -d "{\"id\":\"$SESSION_ID\",\"message\":\"$PROMPT\"}" > /tmp/s-trace-01.txt`
  2. 從 SSE log 取 `traceId`，`wait_for_trace_flush`
  3. 取 trace tree：`curl ... /api/public/traces/$TRACE_ID > /tmp/s-trace-01-tree.json`
  4. 解析 observations，找 type="span" name="agent.run"（parent）跟 name="chat_model.invoke"（children）
  5. Assert: 至少 3 個 chat_model spans（multi-call turn）
  6. Assert: 每個 chat_model span 有 `metadata.reasoning` key
  7. Assert: 各 span `metadata.reasoning` content 各自獨立（不 cumulative；`spans[i].metadata.reasoning` 不是 `spans[i-1].metadata.reasoning` 的 substring）
  8. Assert: parent `agent.run` span 自己**不**有 `metadata.reasoning` key
- **Expected**: D29 + D37 — per-LLM-call reasoning，落在對應 chat_model span 而非 parent

### S-trace-02: 各種 reasoning content 狀態的 schema 一致性

- **Method**: script (table-driven 5 sub-runs，搭配 fault injection / mock provider)
- **Steps**: 對每 row 跑：
  1. 設定對應 scenario：reasoning-on real / reasoning-on short prompt / reasoning-off mode / non-reasoning provider stub / oversize content stub（各需 [POST-CODING: setup mechanism]）
  2. 跑 stream，wait flush
  3. 檢查 trace chat_model span 的 `metadata.reasoning` value
  4. Assert match expected_value table
- **Expected**: 5 種 scenario 各自符合 D29 schema

### S-trace-03: Operator query 涵蓋 4 種語意篩選

- **Method**: Langfuse SQL / API filter
- **Steps**:
  1. 預先 seed 一批混合 traces（從 S-trace-02 跑出來的）
  2. 對 4 種 query 各跑一次（用 Langfuse API filter 或 SDK SQL interface）
  3. Assert 各 query 篩出來的 spans 集合符合 D29 contract
- **Expected**: Operator query 4 種語意全部正確

### S-trace-04: Judge gpt-5-mini calls 不出現 metadata.reasoning

- **Method**: Braintrust eval CLI + Langfuse inspection
- **Steps**:
  1. 跑 eval batch：`braintrust run eval/sec_risk_factors.eval.ts --judge gpt-5-mini`（[POST-CODING: 確認 eval CLI 命令格式]）
  2. 取 batch 內每個 eval run 對應的 Langfuse trace ID
  3. 對每個 trace：找出 judge call 對應的 chat_model spans（model 為 `gpt-5-mini`）
  4. Assert: judge spans 的 metadata 內**沒有** `reasoning` key
  5. Assert: 對應的 agent spans（model 為 `gemini-2.5-flash`）**有** `metadata.reasoning` key
- **Expected**: D30 scope 限制生效；judge 不污染 production trace

### S-trace-05: Reasoning 是 last block 自然結束 trace 仍完整

- **Method**: script + provider stub
- **Steps**:
  1. `[POST-CODING: 加 dev-only stub provider e.g. STUB_REASONING_ONLY=1，emit reasoning blocks 後直接 finish 不 emit text/tool]`
  2. 跑 stream：`curl ... -d "{\"message\":\"trigger reasoning-only edge case\"}" > /tmp/s-trace-05.txt`
  3. 從 SSE log 取 `traceId`，`wait_for_trace_flush`
  4. 取 chat_model span `metadata.reasoning`
  5. 比對 SSE log 內所有 `data-reasoning-status` events 的 text concat 內容跟 trace metadata.reasoning 內容（D34 finalize emit 應確保 buffer 尾段也出現）
  6. Assert: `metadata.reasoning` 完整含所有 reasoning content（無因 missing flush trigger 而 lost 尾段）
- **Expected**: Stream-loop finalize 補洞成功，無 reasoning content 遺失

### S-trace-06: User abort 後 trace 標記 status 並保留尾段 reasoning

- **Method**: script + Langfuse
- **Steps**:
  1. 啟動 stream（同 S-stream-08 step 2）
  2. 等 5s，kill curl
  3. 取 SSE log 內 `traceId`，`wait_for_trace_flush`
  4. Assert: trace 的 root `agent.run` span `metadata.status == "aborted"`
  5. Assert: 最後一個 chat_model span（abort 當下進行中的 call）的 `metadata.reasoning_tail_aborted` 包含 abort 之前 buffer 內 reasoning 尾段（implementation Task 6 `_handle_abort_cleanup` 寫入；distinct key 跟 D29 `metadata.reasoning`，避免污染 on_chat_model_end-completed schema）。若 abort 當下 segmenter buffer 為 empty（i.e. 該 in-flight LLM call 還沒 emit 任何 reasoning），則此 key 可不存在；status="aborted" 仍必須存在
- **Expected**: D35 abort cleanup protocol 完整；status 標記 + 尾段 reasoning 保留於 distinct key

### S-trace-07: Trace 跟 UX 內容可能微小差異但都來自 model ground truth

- **Method**: script (abort case 比對)
- **Steps**:
  1. 重複 S-trace-06 跑 abort case
  2. 從 SSE log 取所有 `data-reasoning-status` events 的 `data.text`，concat 為 `live_ux_text`
  3. 從 trace 取最後 chat_model span 的 `metadata.reasoning_tail_aborted` 為 `trace_text`（abort 場景；對於非 abort 完成的 chat_model spans 仍讀 `metadata.reasoning`）
  4. Assert: 兩者**至少**部分內容對齊（substring match >= 50% 字元 or 高 text similarity）；不要求完全相同（D36 accept divergence）
  5. Assert: 兩者都不是 empty（前提 abort 當下 segmenter buffer 非空 — 否則此 scenario 不適用，需重跑直到捕捉到 mid-reasoning abort）
- **Expected**: 兩路徑各自獨立但內容語義對齊，可接受微小差異

### S-trace-08: 同 session 兩 tab 並發產生兩個獨立 traces

- **Method**: script (同 S-stream-07 + Langfuse 視角)
- **Steps**:
  1. 重複 S-stream-07 步驟 1-3 取兩個 traceId
  2. `wait_for_trace_flush` for both
  3. 檢查兩 traces 的 attributes（用 Langfuse API filter）：confirm `session_id` 相同（同 session）但 `trace_id` 不同
  4. 對每個 trace 內各個 chat_model span：assert `session_id` 跟 trace 相同（contextvars propagation 成功，per D37）
  5. Assert: 兩 trace 的 reasoning content 各自獨立（同 S-stream-07 step 5）
- **Expected**: D33 + D37 isolation；trace-level attributes 正確 propagate

### S-trace-09: Provider content_blocks 失敗 reasoning empty 但其他正常運作

- **Method**: script + content_blocks stub
- **Steps**:
  1. `[POST-CODING: 加 dev-only stub e.g. STUB_CONTENT_BLOCKS_NO_REASONING=<provider>，模擬該 provider content_blocks 不輸出 reasoning blocks]`
  2. 跑 stream 對該 provider reasoning-on agent
  3. Assert: SSE log `data-reasoning-status` events count = 0
  4. Assert: SSE log 仍包含 `text-*` 跟 `tool-*` events，stream 完成 `finish` event
  5. 取 trace，wait flush
  6. Assert: chat_model spans `metadata.reasoning == ""`（D38 graceful degrade）
  7. **Frontend 補充**：browser flow（見 S-rsn-07 idle text 顯示）確認 user 看到 "Synthesizing..." idle text
- **Expected**: 系統 graceful degrade；無 reasoning content 但 stream 仍完成；不 hard block

### S-cross-01: POC 階段一輪 thinking model 驗證 callback chain 正確

- **Method**: script + Langfuse trace 詳細 inspection
- **Steps**:
  1. 跑 reasoning-on Gemini 一次 D25 prompt：`SESSION_ID=$(uuidgen)`，`curl ... > /tmp/poc.txt`
  2. 取 traceId，wait flush
  3. 取整個 trace tree：assert `agent.run` parent span 沒有 `metadata.reasoning`；child chat_model spans 各有自己的 `metadata.reasoning`
  4. 取 trace-level attributes：assert `session_id` / `user_id` 在 root span 設定
  5. 對每個 chat_model span：assert `session_id` / `user_id` attribute 跟 root 相同（contextvars propagate 正確）
  6. 用 Langfuse API `filter session_id=$SESSION_ID` 查詢：assert 能撈到 chat_model spans（不只 root span）
- **Expected**: D37 POC ship gate 通過；callback ordering + contextvars propagation 都正確

---

## Automated Verification — Browser Automation (Playwright)

Frontend 視覺行為用 **Playwright + video recording** 驗證（commit 進 `frontend/tests/e2e/` 變成 repeatable CI guardrail）。Browser-Use CLI 僅用於 agent-driven 一次性探索，不適用本期 BDD scenario 驗證。每個 scenario 對應一個 Playwright spec 檔案；常用 API：`page.goto` / `page.fill` / `page.click` / `page.waitForSelector` / `page.screenshot` / `page.evaluate` / `page.locator(...).innerHTML`。Backend stub 行為由 Task 15 的 dev-only env-flag handler 注入。

### S-rsn-01: Multi-call turn 走過 10-state 標準 lifecycle

- **Method**: Playwright spec + slow-motion screenshot
- **Steps**:
  1. `await page.goto($FRONTEND_BASE/chat)`
  2. `await page.fill("[data-testid=chat-input]", "$PROMPT")` → `await page.click("[data-testid=send]")`
  3. **State 1 capture**：`await page.waitForSelector("[data-testid='reasoning-indicator-idle']")` → `await page.screenshot({ path: "/tmp/s-rsn-01-state1.png" })`
  4. **State 2 capture**：`await page.waitForSelector("[data-reasoning-text]")` → screenshot
  5. **State 3 capture**：`await page.waitForSelector("[data-tool-state='input-available']")` → screenshot
  6. **State 4 capture**：等下個 reasoning text → screenshot
  7. **State 5 capture**：等多個 ToolCard → screenshot
  8. **State 6 capture**：等最後一個 reasoning（synthesizing）→ screenshot
  9. **State 7 capture**：`await page.waitForSelector("[data-text-streaming]")` → screenshot
  10. **State 8 capture**：`await page.waitForSelector("[data-status='ready']")` → screenshot
- **Checkpoints**: 每階段截圖比對 mockup `reasoning_status_states.html` 對應 state
- **Expected**: 10-state lifecycle 視覺序列完整對齊 mockup

### S-rsn-02: Pre-response idle 顯示 3-dot 直到第一個 SSE event

- **Method**: Playwright spec + frame timing inspection
- **Steps**:
  1. `await page.goto($FRONTEND_BASE/chat)`
  2. `await page.fill("[data-testid=chat-input]", "$PROMPT")` → `click send`
  3. **Immediately**：`await page.screenshot({ path: "/tmp/s-rsn-02-state1.png" })`
  4. Assert screenshot 顯示 3-dot bouncing animation（無 text）
  5. `await page.waitForSelector("[data-reasoning-text]")` → 第一個 reasoning text 抵達
  6. `await page.screenshot({ path: "/tmp/s-rsn-02-state2.png" })`
  7. **Vertical alignment check**: 用 image diff tool 比對兩 screenshot：dots 底部 y 座標 vs reasoning text 底部 y 座標 應該對齊（per D17 9a 視覺規格）
- **Expected**: State 1 → State 2 切換無垂直跳動

### S-rsn-03: Reasoning text 以 plain text 渲染不解析 markdown

- **Method**: Playwright spec + DOM inspection
- **Steps**:
  1. `[POST-CODING: 用 stub provider 設計一個 reasoning sentence 含 backticks 跟 asterisks，e.g. "I should call \`list_sec_sections\` to get **the sections**"]`
  2. `await page.goto($FRONTEND_BASE/chat)`，送 query 觸發該 reasoning
  3. `await page.waitForSelector("[data-reasoning-text]")`
  4. `await page.locator("[data-testid=data-reasoning-text]").innerHTML()` 取 DOM
  5. Assert: HTML 內含字面 backtick 跟 asterisk（無 `<code>` / `<strong>` element）
  6. `await page.screenshot({ path: "/tmp/s-rsn-03.png" })`
  7. Visual assert: backticks 顯示為字面字元
- **Expected**: D20 plain rendering — markdown syntax 字面顯示

### S-rsn-04: 600+ 字 CJK reasoning sentence 不破壞 layout

- **Method**: Playwright spec + viewport measurement
- **Steps**:
  1. `[POST-CODING: stub provider 強制 emit 一個 600 字無 `。` 的 reasoning sentence]`
  2. `await page.goto($FRONTEND_BASE/chat)`，送 query
  3. `await page.waitForSelector("[data-reasoning-text]")`
  4. 用 `await page.evaluate(...)` 檢查 `.reasoning-status` element 的 height vs `0.72rem * 1.5`：assert height ≈ single line
  5. 檢查 `.reasoning-status-text` 的 `overflow: hidden` 跟 `white-space: nowrap` 屬性實際生效（用 computed style）
  6. 檢查 `.reasoning-status-dots` 仍 visible 在 clip 邊界右側
  7. Visual screenshot：`await page.screenshot({ path: "/tmp/s-rsn-04.png" })`
- **Expected**: D21 hard-clip 生效；layout 維持單行；dots 始終 visible

### S-rsn-05: 同一 LLM call 內 reasoning → text → reasoning 切換

- **Method**: Playwright spec + slow-motion video（搭 Anthropic provider）
- **Steps**:
  1. 設定 agent 走 `anthropic:claude-4.x-sonnet` reasoning-on
  2. `[POST-CODING: 找出能誘發 Anthropic interleaved reasoning 的 prompt — 可能需要 specifically 觸發 extended thinking 跟 mid-response re-think]`
  3. `await page.goto($FRONTEND_BASE/chat)`，送 prompt
  4. **Frame-by-frame video record**：用 (自動 video record via `use.video: on` 落到 `frontend/test-results//tmp/s-rsn-05.webm`)
  5. 觀察序列：State 2 reasoning A → State 7 text streaming → State 7a reasoning B (under text) → State 7b text resume → ...
  6. Slow-motion playback 確認 indicator 出現位置在已 streamed text 下方
- **Expected**: D13 / §7.2 — Anthropic re-entry 視覺正確；可多次切換

### S-rsn-06: Reasoning 靜默 10s+ 觸發 stalled 視覺

- **Method**: Playwright spec + provider stub
- **Steps**:
  1. `[POST-CODING: stub provider 在 emit 第一個 reasoning sentence 後強制 sleep 12s，再 emit 下個]`
  2. `await page.goto($FRONTEND_BASE/chat)`，送 query
  3. `await page.waitForSelector("[data-reasoning-text]")` → 第一句 reasoning 抵達
  4. `await page.screenshot({ path: "/tmp/s-rsn-06-normal.png" })` → 此刻 dots 1.4s cycle，opacity 1.0
  5. `await page.waitForTimeout(11s)`（讓 stalled 觸發）
  6. `await page.screenshot({ path: "/tmp/s-rsn-06-stalled.png" })`
  7. 檢查 `.reasoning-status` element 已加上 `.stalled` class（用 evaluate 拿 className）
  8. 用 evaluate 拿 dots `.dot` 的 computed `animation-duration`：assert `2.5s`
  9. 用 evaluate 拿 `.reasoning-status-dots` 的 opacity：assert `0.55`
  10. Reasoning text 維持不變（compare text content normal vs stalled screenshot）
- **Expected**: D14 stalled modifier 生效；text 不變動

### S-rsn-07: Reasoning-off model post-tool gap 顯示 idle text

- **Method**: Playwright spec (table-driven 2 cases)
- **Steps**: 對每 row：
  1. 設定 reasoning-off agent
  2. `await page.goto($FRONTEND_BASE/chat)`，送 query 觸發 multi-tool flow
  3. 等到 `<gap_type>` 階段：
     - "Synthesizing"：等所有 tools complete 後 + text-start 之前 (3-7s 視窗)
     - "Thinking"：等第一個 tool complete 後 + 第二個 tool input-available 之前
  4. `await page.screenshot({ path: "/tmp/s-rsn-07-$row.png" })`
  5. Assert: ReasoningIndicator 顯示 `<idle_text>` + dots cycler；視覺與 reasoning streaming 同 Variant A
- **Expected**: D15 post-tool idle text 補洞；兩種 idle text context-aware

### S-rsn-08: Abort sub-state 對應 visible content 各自處理

- **Method**: Playwright spec (table-driven 5 phases)
- **Steps**: 對每 abort_phase：
  1. `await page.goto($FRONTEND_BASE/chat)`，送 query
  2. 等到對應 phase 出現
  3. `await page.click("[data-testid=stop-button]")`
  4. `await page.screenshot({ path: "/tmp/s-rsn-08-$phase.png" })`
  5. Assert visual 對應 expected_visual table
- **Expected**: 5 種 abort phase 各自符合 D17 / §7.5 + D19 / §7.6 規格

### S-rsn-09: Stream error 維持 D11 asymmetry — 隱藏 ephemeral content + ErrorBlock

- **Method**: Playwright spec + fault injection (table-driven 3 phases)
- **Steps**: 對每 error_phase：
  1. `[POST-CODING: error injection mechanism per phase — pre-text / tool-running / mid-text]`
  2. `await page.goto($FRONTEND_BASE/chat)`，送 query
  3. 等到對應 phase
  4. 觸發 error
  5. `await page.screenshot({ path: "/tmp/s-rsn-09-$phase.png" })`
  6. Assert visual：
     - Pre-text/reasoning/idle 階段：ephemeral content 隱藏 + ErrorBlock 顯示
     - Tool running：ToolCard errored state + ErrorBlock
     - Mid-text-start：partial text 保留 + ErrorBlock 在下方（無 inline ERROR marker）
- **Expected**: D18 / D19 對應 error phase 視覺正確

### S-rsn-11: Clear 後 in-flight buffered SSE 不重新填上 reasoning

- **Method**: Playwright spec + slow buffer simulation
- **Steps**:
  1. `[POST-CODING: stub backend 在 reasoning streaming 中段強制 buffer 200ms 後再送下一個 reasoning event]`
  2. `await page.goto($FRONTEND_BASE/chat)`，送 query
  3. `await page.waitForSelector("[data-reasoning-text]")` → 第一個 reasoning 抵達
  4. `await page.click("[data-testid=clear-conversation-button]")`
  5. **Within 200ms**: `await page.screenshot({ path: "/tmp/s-rsn-11-cleared.png" })`
  6. Assert: reasoning indicator 不可見
  7. `await page.waitForTimeout(300ms)`，再 screenshot 一次
  8. Assert: reasoning indicator 仍不可見（buffered events 被 clearedRef 阻擋）
- **Expected**: D31 clearedRef guard 生效

### S-rsn-13: Abort 後立即送新 message 兩個 assistant bubbles 並存

- **Method**: Playwright spec
- **Steps**:
  1. `await page.goto($FRONTEND_BASE/chat)`，送 query 1
  2. `await page.waitForSelector("[data-reasoning-text]")`
  3. `await page.click("[data-testid=stop-button]")`
  4. `await page.screenshot({ path: "/tmp/s-rsn-13-aborted.png" })` → confirm prior bubble 顯示 frozen + STOPPED
  5. **Immediately**: `await page.fill("[data-testid=chat-input]", "follow-up question")` → `click send`
  6. `await page.waitForSelector("[data-status='streaming']")` → 新 turn streaming 開始
  7. `await page.screenshot({ path: "/tmp/s-rsn-13-coexist.png" })`
  8. Assert: 兩個 assistant bubbles 都 visible：第一個 frozen + STOPPED；第二個 streaming
  9. 等新 turn 完成
- **Expected**: D32 — 兩 bubbles 並存；prior STOPPED 自然 persist

### S-rsn-14: Screen reader 收到 transition-level status 而非逐句 reasoning

- **Method**: Playwright spec + accessibility tree inspection（半自動，部分需 manual）
- **Steps**:
  1. `await page.goto($FRONTEND_BASE/chat)`
  2. 用 `await page.evaluate(...)` 拿 accessibility tree (用 `axe-core` 或 Chrome DevTools Protocol)
  3. 確認 `LiveStatusAnnouncer` div 有 `role="status"` + `aria-live="polite"` + `.sr-only` 屬性
  4. 確認 `ReasoningIndicator` div 有 `aria-hidden="true"`
  5. 確認 `ToolCard` div 有 `aria-hidden="true"`
  6. 送 query 觸發 multi-call turn
  7. 在每個 transition 抓取 `LiveStatusAnnouncer` text content（用 evaluate）
  8. Assert: transition 序列 announce 為「Generating response」→「Calling list_sec_sections」→「Tool list_sec_sections completed」→ ...→「Response complete」
  9. Assert: reasoning text 沒出現在 announcer 內（不逐句 announce）
  10. **Manual screen reader 驗證**（見 Manual Verification section）
- **Expected**: D22 ARIA 結構正確 + announcement transitions 正確

### S-chan-03 / S-chan-04 covered above

---

## Automated Verification — Journey Scenarios

### J-stream-01: 完整 6-case matrix E2E lifecycle

- **Method**: Playwright（per design §9）+ video record + browser flow
- **Steps**: 對 6 cases 各跑一次：
  1. Setup agent 對應 `<provider>` × `<mode>`
  2. `playwright open $FRONTEND_BASE/chat`，video record start
  3. `input "$PROMPT"` → `click send`
  4. 等 stream 完成（`wait selector "[data-status='ready']"`）
  5. Video record stop → `/tmp/j-stream-01-$case.webm`
  6. Assert: streaming 完成、無 console error、無 network error、reasoning-on cases 至少 1 個 `data-reasoning-status` event 在 SSE log
  7. 取 traceId，wait flush，assert 每個 chat_model span 有 `metadata.reasoning` key
- **Checkpoints**: 6 個 video 連 PR 描述供 reviewer 親眼看每家 streaming 行為（per design §9）
- **Expected**: 6 cases 全綠；6 video reviewable；trace metadata schema 符合 D29

### J-chan-01: 完整 reasoning channel isolation lifecycle

- **Method**: Playwright spec + 多階段 DOM polling
- **Steps**:
  1. `await page.goto($FRONTEND_BASE/chat)`
  2. 送 D25 canonical prompt
  3. **Mid-stream**: 等 reasoning streaming 中段，`await page.locator("[data-testid=chat-area]").innerHTML()` → assert `message.parts` 對應 DOM 不含 reasoning sentence
  4. **Post-finish**: `await page.waitForSelector("[data-status='ready']")` → 再次 `get html` → assert transcript 僅 text + tool
  5. **Reload**: `await page.reload()` → `wait` rehydration → screenshot → assert transcript 不含 reasoning
  6. **New turn**: 送 follow-up query → 監視 SSE log → assert state-replay 階段不 emit `data-reasoning-status`
- **Expected**: 4 個檢查點 reasoning 永遠不洩漏

### J-rsn-01: 完整 reasoning indicator 10-state 走過一輪
（同 S-rsn-01 步驟，加 video record 跟 reviewer hand-off）

- **Method**: Playwright spec + slow-motion video
- **Steps**:
  1. 同 S-rsn-01 的 10-state 截圖序列
  2. 加 video record `/tmp/j-rsn-01.webm`
  3. Reviewer 比對 video 各 state 跟 mockup `reasoning_status_states.html` 對應 section
- **Checkpoints**: 10 個 screenshot 比對 mockup state cards
- **Expected**: 10-state 視覺 lifecycle 完整且符合 mockup

### J-rsn-02: Abort 中段然後 resend，前後 turn 都正確顯示

- **Method**: Playwright spec
- **Steps**:
  1. `await page.goto($FRONTEND_BASE/chat)`
  2. 送 query 1，等到 State 6 synthesizing
  3. `click stop` → screenshot 確認 9 frozen + STOPPED
  4. `input "follow-up"` → `click send`
  5. `wait selector "[data-status='streaming']"` → 新 turn 開始
  6. screenshot 確認兩 bubbles 並存
  7. `wait selector "[data-status='ready']"` → 新 turn 完成
  8. 最終 screenshot 確認 prior bubble 仍含 STOPPED label，新 bubble 為完整 final answer
- **Expected**: D17 + D32 共同運作 — abort lifecycle 跟 resend 並存乾淨

### J-trace-01: Multi-call 完整 trace tree 對齊 SEC 範例

- **Method**: script + Langfuse trace API
- **Steps**:
  1. 跑 D25 canonical prompt：`SESSION_ID=$(uuidgen)`，`curl ... > /tmp/j-trace-01.txt`
  2. 取 traceId，wait flush
  3. 取 trace tree 結構：`curl /api/public/traces/$TRACE_ID | jq '.observations'`
  4. Assert: 結構符合 §6.3 範例
     - 1 trace `chat_request`
     - 1 child span `agent.run`
     - agent.run 下含 ≥ 3 個 `chat_model.invoke` spans（依 SEC 範例為 3）
     - chat_model spans 之間穿插 tool spans (`tool.list_sec_sections`、`tool.get_section` ×2)
  5. 對每個 chat_model span 檢查 `metadata.reasoning` 符合 D29 schema（non-empty for reasoning-on）
  6. 對所有 spans 檢查 trace-level attributes (`session_id`, `user_id`) 都繼承
- **Expected**: trace tree 結構 + metadata schema + attribute propagation 全部對齊

---

## Manual Verification — Manual Behavior Test

> Coding Agent 無法自動化、需 user 手動驗證才能完成的 E2E behaviors。

### S-rsn-14 (manual portion): Screen reader 實際聽感驗證

- **Reason**: Coding Agent 沒有實際 screen reader（VoiceOver / NVDA / JAWS）；僅能驗證 ARIA structure 不能驗證 actual audio output
- **Steps**:
  1. macOS 開 VoiceOver（Cmd+F5）
  2. `await page.goto($FRONTEND_BASE/chat)` 並用鍵盤 navigate 到 chat input
  3. 送 D25 canonical prompt
  4. 聽整個 turn 的 audio output
  5. 確認 announcement 序列符合 D22 規格（generate response → calling tool → tool completed → ... → response complete）
  6. 確認 reasoning text 不被逐句 announce（無 reasoning content overflow queue）
  7. 確認 ErrorBlock 在 error case 觸發 `role="alert"` 立即播報
- **Expected**: 視障 user 體驗符合 D22 hybrid pattern

### ~~S-stream-06 (production deployment portion)~~ — 移出本期 scope

> 隨 Task 13 移除；backend keepalive 未實作，無 keepalive 機制可在 staging 驗證。等後續 PR 補上 backend keepalive 後再恢復此 manual verification。

---

## Manual Verification — User Acceptance Test

> Product Owner / 使用者驗證整體成果是否符合 design 期待。

### J-stream-01 + J-rsn-01: 完整 streaming + reasoning UX 體驗
- **Acceptance Question**: 整體 streaming + reasoning UX 是否流暢、清晰、值得 ship？
- **Steps**:
  1. 開 chat 介面
  2. 跑數個不同類型的 query：簡短 / 多 tool / reasoning-rich / reasoning-off agent / abort 中段
  3. 對 6-case matrix 各跑一次（透過切換 agent version）
  4. 觀察：
     - Reasoning indicator 是否清楚但不打擾？字級夠小但仍可讀？
     - State 1 → State 2 切換是否平順無跳動（dots/text bottom 對齊）？
     - 多 reasoning sentence 切換是否視覺平順？
     - Long-silence stalled 是否提供足夠「系統還活著」訊號？
     - Post-tool idle text "Synthesizing"/"Thinking" 是否正確補洞？
     - Anthropic interleaved 場景下 indicator re-entry 是否合理？
     - Long-sentence overflow 是否乾淨（hard-clip 無雙 dots 撞）？
     - Abort 後 partial text + STOPPED 是否清楚？
- **Expected**: 整體 UX 對 reviewer 視覺上 polished、no jarring jumps、no broken states

### J-trace-01: Operator 觀測體驗
- **Acceptance Question**: 從 Langfuse trace 上 operator 是否能查到該知道的 reasoning 資訊？
- **Steps**:
  1. 跑數個 production-like sessions
  2. 在 Langfuse UI 中：
     - 用 `session_id` filter 撈某 session 的 trace
     - 點擊 trace 看 trace tree
     - 點擊 chat_model span 確認 `metadata.reasoning` 顯示
  3. 跑 SQL query 試 4 種 D29 operator query 語意
- **Expected**: Operator 能順利查 reasoning content；schema 一致；abort/error/non-reasoning 不同 case 都能區分

---

## Notes

### Test environment

- Backend / Frontend: real services (per memory `feedback_msw_vs_real_backend.md`)
- Browser: **Playwright** (`frontend/tests/e2e/`，commit 進 repo 為 repeatable CI guardrail) — Browser-Use CLI 僅用於 agent-driven 一次性探索，不適用本期 BDD 驗證
- Eval: Braintrust on host CLI (per `feedback_braintrust_host_only.md`)
- Tracing: Langfuse SDK + REST API (per `feedback_tracing_verification.md`)

### Trace flush wait pattern

每次 stream 結束驗證 trace 內容前必須 `wait_for_trace_flush`：retry 5 次每次 sleep 1s，避免 Langfuse SDK async flush 還沒完成就 query 拿到 stale 結果。

### POST-CODING placeholders

下列 placeholder 在實作階段需確認 / 補上：
- 各 backend endpoint URL（chat stream / agent switch / sessions / messages）
- Frontend URL（dev server port + chat route）
- Agent config / model binding 設定機制
- Dev-only feature flags（詳見上方 Operator Runtime Guide 章節的對照表）：`FORCE_LLM_FAIL`、`FORCE_REASONING_NON_TRANSIENT`、`EMIT_DELAYED_REASONING`、`EMIT_LATE_REASONING`、`STUB_REASONING_ONLY`、`STUB_CONTENT_BLOCKS_NO_REASONING`（`STUB_LLM_HANG` 已隨 Task 13 移出 scope）
- DOM testid attributes（`data-testid='reasoning-indicator-idle'`、`[data-status='ready']` 等）
- Eval CLI 命令格式（braintrust）
- ~~Staging deployment URL~~（S-stream-06 已移出本期 scope，本期不需 staging deployment）

### Scenarios not in this plan

下列 scenarios 已在 bdd-scenarios.md 註明 demoted 或 scope 移除，**不**需要 verification entry：
- C1.3 / C1.4 (D24 scope removed)
- C1.6 / C2.4 / C5.2 / C6.1 / C6.9 / CR.7 (demoted to unit test or coverage 折入其他 scenarios)

每個 demoted item 的覆蓋路徑：
- C1.6 → S-stream-05 verification 已涵蓋 invoke-path 跟 streaming-path 的 metadata 等價性
- C2.4 → S-chan-02 step 5-6（resume turn 不 re-emit reasoning）已涵蓋
- C5.2 → S-trace-02 schema 表格已涵蓋 completed-path always-write-key（abort-path 由 S-trace-06 涵蓋；兩者構成 D29 mode-aware contract 全貌）
- C6.1 → 16-32ms frame overlap below human perception，no verification needed
- C6.9 segmenter side → ReasoningSegmenter 單元測試（Phase 5 implementation 階段）
- CR.7 reasoning-id collision → reasoning-id generator 單元測試
