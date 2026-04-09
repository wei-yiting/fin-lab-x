
# Verification Plan — S3 Streaming Chat UI

## Meta

- Design Reference: `artifacts/current/design_streaming_chat_ui.md`
- BDD Scenarios Reference: `artifacts/current/bdd_scenarios_streaming_chat_ui.md` ← scenario specs（含 Verification Layer Summary table）
- Implementation Prerequisites Reference: `artifacts/current/implementation_prerequisites_streaming_chat_ui.md` ← DOM contract、MSW infra、V-1/V-2/V-3
- Implementation Test Cases Reference: `artifacts/current/implementation_test_cases_streaming_chat_ui.md` ← unit/component/hook/integration/e2e 的具體 TDD test code
- Generated: 2026-04-08

## Verification Approach: 5 Layers

每個 BDD scenario 由**最適合的 layer** 驗證。不重複 verification cost。

```
                                            CI (every PR)         Manual (one-shot)
                                            ──────────────       ──────────────────
                       ┌─ unit ──┐
                       │         │
   automated tests ────┼─ component │  →  Vitest + Playwright       (no manual)
   (in code)           │         │      via implementation_test_cases.md
                       ├─ hook ──┤
                       │         │
                       ├─ int ───┤
                       │         │
                       └─ e2e-T0─┘

   manual verification ┌─ bdd-real ──┐
   (post-impl one-shot)│             │  →  Browser-Use CLI agent run
                       ├─ bdd-visual │      see Section 2 / 3 of this doc
                       │             │
                       ├─ manual-mbt │
                       │             │
                       └─ manual-uat ┘
```

| Layer | Tool | 何時跑 | Owned by |
|---|---|---|---|
| `unit` / `component` / `hook` / `integration` | Vitest（jsdom + RTL + renderHook + msw/node）| watch mode + every commit | implementation phase via TDD |
| `e2e-tier0` | Playwright headless | every PR (CI gate) | implementation phase via TDD |
| **`bdd-real`** | **Browser-Use CLI agent + real S1 backend** | **post-implementation, one-shot** | **本文件 Section 2** |
| **`bdd-visual`** | **Browser-Use CLI agent + screenshot vs mockup** | **post-implementation, one-shot** | **本文件 Section 3** |
| `manual-mbt` | 人 | release 前 | 本文件 Section 5 |
| `manual-uat` | PO / user | release 前 | 本文件 Section 6 |

完整 scenario → layer 對照表見 `bdd_scenarios_streaming_chat_ui.md` 的 "Verification Layer Summary" 章節。

## URLs 約定

- **Real backend mode**: `http://localhost:5173/chat`
- **MSW mock mode**: `http://localhost:5173/chat?msw_fixture={fixture-name}`
- Backend API: `http://localhost:8000/api/v1/chat`（同時是 Vite proxy target）

## Selectors 約定

完整 `data-testid` / `data-status` / `data-tool-state` / `aria-label` contract 見 `implementation_prerequisites_streaming_chat_ui.md` Section 1。

## Prerequisites

- Backend healthy: `curl http://localhost:8000/api/v1/chat` 可 reach
- Frontend dev server running: `pnpm dev` in `frontend/`
- For MSW scenarios: dev server with MSW infrastructure setup（見 prerequisites Section 2）
- Browser-Use CLI 已連線到 Chrome

---

## Section 1: Automated Test Layers

> 這 5 層的 verification 是 **implementation phase 的責任**，由 coding agent TDD 寫成 code 跑。**本文件不重複 test code 內容** — 完整 spec 見 `implementation_test_cases_streaming_chat_ui.md`。

### Coverage by layer

| Layer | TC count | Test runner | File location |
|---|---|---|---|
| unit | 14 | Vitest | `frontend/src/lib/__tests__/*.test.ts` |
| component | 15 | Vitest + RTL + jsdom | `frontend/src/components/*/__tests__/*.test.tsx` |
| hook | 4 | Vitest + renderHook + msw/node | `frontend/src/hooks/__tests__/*.test.ts` |
| integration | 5 | Vitest + msw/node + RTL | `frontend/src/components/pages/__tests__/ChatPanel.integration.test.tsx` + `frontend/src/__tests__/contract/*.ts` |
| e2e-tier0 | 6 | Playwright | `frontend/tests/e2e/{security,smoke,critical}/*.spec.ts` |

### How to verify these passed

```bash
# Unit + component + hook + integration（Vitest）
cd frontend && pnpm test

# E2E Tier 0（Playwright）— 在 CI 跑或手動
cd frontend && pnpm playwright test --grep "@smoke|@critical|@security"
```

每個 test case 的 BDD scenario mapping 見 `bdd_scenarios.md` Verification Layer Summary 表 + `implementation_test_cases.md` Section 6 reverse lookup。

### Coverage gates

- Unit / hook layer: ≥ 90% statement coverage
- Component layer: ≥ 80% statement coverage
- Integration layer: ≥ 70% branch coverage on `ChatPanel` orchestration paths
- E2E Tier 0: 6 個 specific tests 全 pass，無 % target

---

## Section 2: BDD Real Backend Verification (Browser-Use CLI)

> **目的**: 抓「real S1 + real LLM + real network」會出現但 mocked 環境抓不到的 fail mode。一次性 post-implementation verification。
>
> **不適用 CI**：依賴 real LLM 的非 deterministic 回答，無法當 regression gate。
>
> **覆蓋 ~9 個 BDD scenarios**。

### V2-01: S-stream-01 — Pure text streaming with real LLM

- **Goal**: 證明 SSE wire format 跟 AI SDK v6 真實 align、cursor 在 real network 條件下正常 blink
- **Steps**:
  1. `browser-use open http://localhost:5173/chat`（無 msw_fixture）
  2. `browser-use input {composer-textarea} "Briefly explain NVIDIA Blackwell architecture"`
  3. `browser-use click {composer-send-btn}`
  4. `browser-use wait selector "[data-testid='user-bubble']"` → user bubble 出現
  5. `browser-use wait selector "[data-testid='typing-indicator']"` → typing dots
  6. `browser-use screenshot /tmp/v2-01-typing.png`
  7. `browser-use wait selector "[data-testid='assistant-message'] [data-testid='cursor']"` → text 開始 + cursor
  8. `browser-use screenshot /tmp/v2-01-streaming.png`
  9. `browser-use wait selector "[data-testid='message-list'][data-status='ready']"` → ready
  10. `browser-use screenshot /tmp/v2-01-complete.png`
- **Expected**: 三段 screenshot 顯示 typing dots → partial text + cursor → complete text，流暢無斷。Real backend 跟 mock 行為一致

### V2-02: S-stream-02 — Tool + text mixed flow with real backend

- **Goal**: Real S1 + real yfinance tool 整合，驗證 wire format 在 tool event 下也對齊
- **Steps**:
  1. `browser-use open http://localhost:5173/chat`
  2. `browser-use input {composer-textarea} "What is the current price of AAPL?"`
  3. `browser-use click {composer-send-btn}`
  4. Wait `[data-tool-state="input-available"]` → ToolCard running
  5. `browser-use screenshot /tmp/v2-02-tool-running.png`
  6. Wait `[data-tool-state="output-available"]` → ToolCard success
  7. Wait text-delta 開始 → cursor 出現
  8. Wait `data-status="ready"`
  9. `browser-use screenshot /tmp/v2-02-complete.png`
- **Expected**: Tool 真的執行成功，回的 OUTPUT JSON 結構符合預期，text 引用 tool 結果

### V2-03: S-stream-03 — Pure tool query with no follow-up text

- **Goal**: 找一個 LLM 只 call tool 不寫 text 的真實 prompt（罕見但可能發生），驗 status 仍正確切回 ready
- **Steps**:
  1. `[POST-CODING: 找到一個能讓 real LLM 只 call tool 不寫 text 的 prompt，例如 'just call yfinance and return raw data, no commentary']`
  2. Send prompt
  3. Wait tool output-available
  4. Wait `data-status="ready"` 即使無 text-delta
  5. Composer button 應切回 Send
- **Expected**: 即使無 text，stream 完成後 UI 不卡

### V2-04: S-md-01 — Real LLM Sources block formatting

- **Goal**: 驗證 backend system prompt 的 reference link format 要求是否真的被 LLM 遵守
- **Steps**:
  1. `browser-use open http://localhost:5173/chat`
  2. `browser-use input {composer-textarea} "NVDA 最近有什麼新聞？引用來源"`
  3. Send，等待 ready
  4. `browser-use screenshot /tmp/v2-04-sources.png`
  5. Get text of `[data-testid="sources-block"]` → 確認顯示 title（不是 hostname）
  6. Verify body 中有 superscript `[1]` `[2]` 連結
- **Expected**: LLM 正確輸出 `[1]: url "title"` 格式，frontend 抽取為 Sources block 顯示 title。如果 LLM 漏 title，會 fallback 到 hostname — 此時 user 應 escalate 給 backend system prompt 加強

### V2-05: S-tool-01 — Real tool success state visual transition

- **Goal**: 驗證 tool state 在 real backend 真的依序 input-available → output-available，不會跳過 running 視覺
- **Steps**:
  1. `browser-use open http://localhost:5173/chat`
  2. Send prompt 觸發 yfinance: `"AAPL price"`
  3. **立即** `browser-use screenshot /tmp/v2-05-running.png`（要在 tool 完成前抓到 running 狀態）
  4. Wait output-available
  5. `browser-use screenshot /tmp/v2-05-success.png`
- **Expected**: running screenshot 顯示 🟠 amber pulsing dot，success screenshot 顯示 🟢 綠色 dot，視覺有明顯轉換

### V2-06: S-clear-03 — Backend chatId isolation

- **Goal**: 驗 clear session 換新 chatId 後 backend 真的視為新 conversation（不會記得舊的 context）
- **Steps**:
  1. `browser-use open http://localhost:5173/chat`
  2. Send `"Remember this code: 42"`，等 ready
  3. `OLD_ID=$(browser-use javascript "document.querySelector('[data-testid=\"chat-panel\"]').dataset.chatId")`
  4. Send `"What was the code?"`，等 ready
  5. Verify assistant 回答含「42」
  6. Click `[data-testid="composer-clear-btn"]`
  7. `NEW_ID=$(browser-use javascript "document.querySelector('[data-testid=\"chat-panel\"]').dataset.chatId")` → assert `NEW_ID !== OLD_ID`
  8. Send `"What was the code I mentioned earlier?"`，等 ready
  9. Verify assistant **不**含「42」
- **Expected**: 新 chatId 對 S1 來說是全新 conversation，無歷史 context 洩漏

### V2-07: J-stream-01 — Pure text journey real backend smoke

- **Goal**: 整個 pipeline 跟 real LLM 一起跑一輪確認沒有 wire format drift
- **Steps**: 跟 V2-01 類似但使用較長的 prompt 觸發更長 stream，verify 整個 flow 無中斷
- **Expected**: 完整 SSE pipeline + finish event 符合預期

### V2-08: J-tool-01 — Parallel tools real backend journey

- **Goal**: Real LLM 真的觸發兩個並列 tool 時的整體互動
- **Steps**:
  1. `browser-use open http://localhost:5173/chat`
  2. Send `"Compare current price of AAPL and MSFT and show me recent news for both"`
  3. Wait 兩張 ToolCard 出現（`browser-use get count "[data-testid='tool-card']"` === 2）
  4. `browser-use screenshot /tmp/v2-08-parallel.png`
  5. Wait 兩張都 output-available
  6. Wait text 整合兩 tool 結果
  7. Wait ready
- **Expected**: 兩 tool 順序穩定、各自顯示自己的 progress 文字（如果有的話）、終態各自正確、text 真的整合兩個結果

### V2-09: J-empty-01 — Onboarding via real prompt chip

- **Goal**: 完整 onboarding flow 透過 chip + real LLM
- **Steps**:
  1. `browser-use open http://localhost:5173/chat`
  2. Wait empty-state visible
  3. `browser-use screenshot /tmp/v2-09-empty.png`
  4. Click `[data-testid="prompt-chip"][data-chip-index="1"]`
  5. Verify textarea 被填入
  6. Optionally edit textarea
  7. Click send
  8. Wait ready
  9. `browser-use screenshot /tmp/v2-09-complete.png`
- **Expected**: 流暢 onboarding，empty state 順利切換到 active chat

---

## Section 3: BDD Visual Mockup Comparison (Browser-Use CLI)

> **目的**: 對 implementation 做的視覺輸出跟 `S3_state_storyboard.html` / `S3_layout_wireframe.html` 做 agent 級別的視覺比對。Agent 看圖描述差異，比 pixel diff 更寬容彈性。
>
> **覆蓋 ~8 個 BDD scenarios + 視覺項目**。

### V3-01: S-empty-01 — Empty state vs wireframe

- **Goal**: 比對 empty state 整體 layout 跟 `S3_layout_wireframe.html` 一致
- **Steps**:
  1. `browser-use open http://localhost:5173/chat`
  2. Wait empty-state
  3. `browser-use screenshot /tmp/v3-01-actual.png`
  4. Browser-Use agent 對比 actual vs `artifacts/current/S3_layout_wireframe.html` 的 empty state mockup
  5. Agent 描述差異：welcome card title size、4 chips layout、disclaimer 位置、整體視覺權重
- **Expected**: 跟 wireframe 視覺一致或差異可解釋（可接受的 fidelity loss）

### V3-02: S-tool-01 — ToolCard 三狀態 vs storyboard

- **Goal**: 三個 tool state 視覺跟 storyboard 一致
- **Steps**:
  1. 跑一個 tool query
  2. 截圖 running / success 兩個 state（如果可以也截 error，需另一個 prompt）
  3. Agent 對比 actual 跟 `S3_state_storyboard.html` 中對應 state
  4. 重點檢查：dot 顏色、pulse 動畫、label 排版、tool name 字型
- **Expected**: 三狀態視覺對齊 storyboard

### V3-03: S-md-08 — Streaming markdown + cursor visual

- **Goal**: Cursor 出現時機跟視覺感受跟 storyboard "streaming" state 對齊
- **Steps**:
  1. Send 一個會產生 markdown 內容的 prompt
  2. 在 streaming 期間每 200ms screenshot 一次（連續 5 frames）
  3. Agent 描述 cursor 的視覺存在感、blink rate、是否有 jank
  4. Wait ready
  5. 確認 cursor 消失
- **Expected**: Cursor 流暢 blink、stream 結束乾淨消失、無 visual artifact

### V3-04: S-md-07 — RefSup click anchor scroll visual

- **Goal**: 點擊 RefSup 跳轉的視覺體感
- **Steps**:
  1. 觸發長回覆含多 reference（real LLM）
  2. Wait ready
  3. Manually scroll viewport 到中段
  4. `browser-use screenshot /tmp/v3-04-before.png`
  5. Click `[data-testid="ref-sup"][data-ref-label="3"]`
  6. `browser-use screenshot /tmp/v3-04-after.png`
  7. Agent 描述：跳轉是否流暢、有沒有 highlight 視覺回饋、scroll 動作是否 smooth
- **Expected**: 跳轉乾淨，target 條目可見

### V3-05: S-err-09 — ErrorBlock auto-scroll visual

- **Goal**: error 出現時 viewport 自動 scroll 的視覺體感
- **Steps**:
  1. 完成幾輪對話建立 scroll 空間
  2. Trigger pre-stream error（用 MSW fixture 或 manual force regenerate failure）
  3. `browser-use screenshot /tmp/v3-05-after.png`
  4. Agent 描述 ErrorBlock 是否在 viewport 內可見、scroll transition 是否突兀
- **Expected**: ErrorBlock 自然出現在 viewport，無 jarring jump

### V3-06: J-md-01 — Long markdown journey visual

- **Goal**: 長 markdown 含多 reference 的整體 reading experience
- **Steps**:
  1. Real LLM 觸發長回覆含 5+ references
  2. Wait ready
  3. Multi-screenshot 涵蓋 message body + Sources block
  4. Agent 描述：整體閱讀感、Sources block 顯示是否清晰、ref superscript 視覺對齊
- **Expected**: Markdown rendering 美觀符合 mockup 設計水準

### V3-07: J-scroll-01 — Multi-turn scroll lifecycle visual

- **Goal**: Follow-bottom 跟 user scroll 互動的整體視覺體感
- **Steps**:
  1. 完成 5 輪對話
  2. 在 streaming 中 scroll 到上方
  3. 等 stream 完成
  4. 再 send 新訊息看 force-follow 行為
  5. Agent 描述 scroll 平滑度、follow-bottom 是否 jittery
- **Expected**: Scroll 行為符合 user intent，無 fight-the-user 感

### V3-08: S-stream-01 supplementary — Streaming smoothness vs storyboard

- **Goal**: 對比 storyboard 中 "streaming" state 跟 implementation 真實 render
- **Steps**: 跟 V2-01 共用 screenshot，但 focus 在 visual fidelity description
- **Expected**: Token-by-token render 流暢自然，跟 storyboard 一致

---

## Section 4: BDD Real Interaction Feel (Browser-Use CLI)

> **目的**: 抓 automated test 抓不到的「整體互動感受」— 非 boolean assertion，是 agent 寫描述性 report。
>
> 跑完後 agent 寫一份 free-form report `verification_results_streaming_chat_ui.md` 描述以下面向。

### V4-01: Streaming chat 整體流暢度 report

執行 V2-01 + V2-02 + V2-04 + V2-08 後，agent 描述：

- TypingIndicator → cursor 切換是否自然
- Token-by-token rendering 是否 jittery
- Markdown rerender 過程是否有閃爍
- Tool card 狀態切換是否流暢
- Send → Stop → Send mode 切換的 1-frame latency 是否體感得到

### V4-02: Error handling 體感 report

執行 mid-stream error scenario 後 agent 描述：

- ErrorBlock 出現是否突兀
- 已收 partial content 的保留是否乾淨（無視覺殘留）
- Retry 點下去到 new stream 開始的 latency 是否 acceptable

### V4-03: Stop / Clear 體感 report

執行 stop + clear scenarios 後 agent 描述：

- Stop button 點下去 button 變回 Send 的 perceived latency
- Clear session 從 active chat 跳到 empty state 的視覺切換流暢度
- 切換後 textarea focus 行為

### V4-04: Tool progress message 真實內容感受

執行 V2-02 / V2-08 中 tool 有 progress message 的時段，agent 描述：

- Progress 文字是否有意義、user 看了是否覺得「系統知道在做什麼」
- 多 tool 並列時 progress 是否互不干擾
- Progress 過長時的截斷處理（如果有 rendered）

### V4-05: 字型 + 暗色主題視覺一致性

跑完 several 個 prompts 後 agent 描述：

- Inter / JetBrains Mono / Noto Sans TC 三字型 fallback 在實際 UI 上的視覺融洽度
- 暗色 oklch 色票對比度是否舒適
- CJK 跟 Latin 混排的 baseline 一致性

---

## Section 5: Manual Behavior Test

> **目的**: Coding agent 跟 automated tests 都做不到、需要人手動測的 edge cases。

### MBT-01: 250-char no-space progress overflow layout

- **Reason**: CSS overflow 行為依賴視覺判斷
- **Steps**:
  1. 透過 MSW 或 backend mock 送超長 progress message（250 chars no space）
  2. 觀察 ToolCard 是否 ellipsis 截斷或正常 wrap
  3. 確認 Chevron toggle 仍在 viewport 可點
- **Expected**: Layout 無橫向 scroll，toggle 可用

### MBT-02: CJK / emoji / 全形 pipes 混合 markdown

- **Reason**: 字型 per-character fallback + CJK punctuation 行為難自動驗
- **Steps**:
  1. 送一個會回 CJK + emoji + Latin 混排的 prompt
  2. 視覺檢查 baseline 一致
  3. 嘗試 table 含全形 `｜`
- **Expected**: Mixed scripts 正常顯示；全形 pipes 至少不 crash

### MBT-03: Window resize / DevTools open 對 follow-bottom 的影響

- **Reason**: 非常見 user action，Browser-Use 中操作不便
- **Steps**:
  1. 進入 streaming，follow-bottom active
  2. 拖動視窗 / 開合 DevTools
  3. 觀察 viewport 是否維持貼底
- **Expected**: Resize 後仍貼底，無 jump flicker

### MBT-04: 50k 字 paste bomb（也對應 S-tool-08 大型 OUTPUT JSON）

- **Reason**: 測 React controlled textarea 在大 input 下的 perf
- **Steps**:
  1. 複製 50,000 字 lorem ipsum
  2. Paste 到 textarea
  3. 觀察 freeze 時間 < 1 秒
  4. Send 觀察 backend 是否 413
- **Expected**: UI 可用不 freeze；backend 413 觸發 ErrorBlock friendly message

### MBT-05: Background tab throttling 復原

- **Reason**: 需 user 手動切 tab，browser automation 不保證 throttling
- **Steps**:
  1. 送長問題 → streaming 開始
  2. 切到別 tab 等 30 秒
  3. 切回來
  4. 確認 scroll 位置、status、final stream 狀態
- **Expected**: 無 frozen UI、無 missing events、scroll 正確

### MBT-06: Horizontal scroll hijacking in `<pre>`

- **Reason**: Trackpad 橫向手勢不易模擬
- **Steps**:
  1. 展開一個寬 JSON ToolCard
  2. 在 `<pre>` 內橫向 scroll
  3. 確認 message-list viewport 不受影響（follow-bottom 未中斷）

### MBT-07: Browser zoom 200% 與 50% threshold 行為

- **Reason**: Zoom 切換 + auto-scroll 測試需多次操作
- **Steps**:
  1. Zoom 到 200%，送 prompt，觀察 follow-bottom
  2. Zoom 到 50%，再次觀察
- **Expected**: 不同 zoom 下行為一致

### MBT-08: S-cross-02 — Browser back / forward navigation

- **Reason**: 跟 S-cross-01 refresh 互補，需手動 navigate
- **Steps**:
  1. 從別頁導航到 `/chat`，建立對話
  2. Browser back，等 5 秒
  3. Browser forward 回 `/chat`
- **Expected**: 行為與 refresh 一致（empty state + 新 chatId）

### MBT-09: S-scroll-05 — Keyboard scroll a11y

- **Reason**: 鍵盤導航體驗驗證（hook test 已 cover 邏輯，這裡驗 real browser）
- **Steps**:
  1. Tab 聚焦到 ScrollArea
  2. PageUp / Space / Arrow keys scroll
  3. 觀察 follow-bottom 是否正確 disable
  4. End key 跳底
- **Expected**: 鍵盤 user 完整可用，等同 mouse user

---

## Section 6: User Acceptance Test

> 由 Product Owner / 實際 user 驗收，從 end-user 視角評估體驗。

### UAT-01: Streaming chat 整體感受

- **Acceptance Question**: 整個 streaming chat 體驗是否流暢、可信、具備 ChatGPT-level polish？
- **Steps**:
  1. 送幾個不同類型問題（純 text、有 tool、有 references）
  2. 觀察逐字呈現、ToolCard 狀態轉換、Sources block 是否有用
  3. 嘗試 Stop / Regenerate / Clear 各一次
  4. 看 Error 場景（觸發一次 404 或 offline）
- **Expected**: 整體順暢無 jarring transition；錯誤訊息友善可理解；操作回饋即時

### UAT-02: Empty state 與新 user onboarding

- **Acceptance Question**: 新 user 首次進入能否透過 prompt chips 順利開始對話？
- **Steps**:
  1. Fresh open
  2. 閱讀 welcome 文案
  3. Click 各 chip 觀察填入行為
  4. 選一個最有興趣的 chip → edit → send
- **Expected**: Welcome 清楚、chips 代表性足、填入流程符合預期

### UAT-03: Tool card 展開體驗

- **Acceptance Question**: 用戶能否從 tool card 了解 agent 做了什麼、結果如何？
- **Steps**:
  1. 觸發各種 tool（stock quote、news search、10-K 分析等）
  2. 觀察 running 狀態 label、success 後 generic `"Completed"`
  3. 點開看 INPUT / OUTPUT JSON
- **Expected**: 每個 tool 視覺與 label 一致；展開後資訊有意義

### UAT-04: Error messaging 友善度

- **Acceptance Question**: 錯誤訊息是否告訴 user 該怎麼辦？
- **Steps**:
  1. 觸發各 error class（422 / 409 / offline / 500）
  2. 閱讀 ErrorBlock 文字
  3. 嘗試 Retry
- **Expected**: 每個 error 都有 actionable message，不只是「Something went wrong」

### UAT-05: 暗色主題視覺一致性

- **Acceptance Question**: 暗色主題下對比度、閱讀性、品牌感是否符合設計？
- **Steps**:
  1. 完整走過 S-stream-01 ~ S-clear-04 的情境
  2. 對比 `S3_state_storyboard.html` 各 state snapshot
- **Expected**: 視覺與 storyboard 一致；文字可讀、色彩有層次

---

## Section 7: Pre-Coding Contract Verifications

> Implementation 開始前必須確認的 backend / library 行為。詳細步驟見 `implementation_prerequisites_streaming_chat_ui.md` Section 4。

| ID | What | Test type | Owned by |
|---|---|---|---|
| **V-1** | S1 對 partial turn regenerate 的回應碼（200 vs 422）| Curl script | Milestone 0 |
| **V-2** | AI SDK v6 useChat 對 pre-stream HTTP error 的 user message lifecycle（optimistic append?） | Vitest contract test (TC-int-v2-01) | Milestone 0 |
| **V-3** | AI SDK v6 useChat.stop() 的 abort semantic（status → ready, not error） | Vitest contract test (TC-int-v3-01) | Milestone 0 |

任一失敗 → 回頭調整 BDD scenarios + smart retry routing 策略。

---

## Verification Execution Order（建議）

```
Phase A: Implementation 階段（每次 commit）
├── Vitest watch（unit/component/hook/integration）
└── Pre-commit hook 跑相關 tests

Phase B: PR 階段（每次 PR）
├── CI: Vitest full suite
├── CI: Playwright Tier 0（@smoke + @critical + @security）
└── 失敗則 block PR

Phase C: Pre-merge 一次性 verification
├── Section 2: BDD Real Backend Verification（V2-01 ~ V2-09）
├── Section 3: Visual Mockup Comparison（V3-01 ~ V3-08）
├── Section 4: Real Interaction Feel reports（V4-01 ~ V4-05）
└── 結果寫入 verification_results_streaming_chat_ui.md

Phase D: Release 前
├── Section 5: Manual Behavior Tests（MBT-01 ~ MBT-09）
└── Section 6: User Acceptance Test（UAT-01 ~ UAT-05）
```

---

## POST-CODING TODO Summary

Implementation 完成後仍需釐清 / 補的項目：

### Real backend behavior 釐清

1. 確認 S1 是否有 conversation `404` 路徑，或 conversation 不存在統一以 422 處理（影響 V2 行為）
2. 確認 S1 是否實作 session busy `409` 或採取其他並發控制策略
3. 觸發 500 的 fault injection 方法（V2 補強用）

### Real backend test data 尋找

4. V2-03 純 tool 無 text 的真實 prompt（或退而求 MSW fixture）
5. 找會失敗的真實 tool query（V2 可選變體）

### Browser-Use CLI 工具查詢

6. Browser-Use CLI 對 alert dialog 的處理 API（V3-01 中如 XSS 防護失效會觸發）
7. Browser-Use CLI navigate_back / navigate_forward 實際 API（MBT-08）

### 已解決（不再 POST-CODING）

| 原 TODO | 解決方式 |
|---|---|
| MSW SSE 控制機制 | `implementation_prerequisites.md` Section 2 完整定義 |
| ~21 個 MSW fixture 設計 | `implementation_prerequisites.md` Section 3 catalog |
| 純 tool 無 text 測試（automated）| MSW fixture `pure-tool-no-text` |
| Flaky network simulation | MSW fixture `flaky-network-mid-stream` |
| Frontend chatId debug hook | `data-chat-id` attribute on `[data-testid="chat-panel"]` |
| V-1: S1 partial turn regenerate | `implementation_prerequisites.md` §4 V-1（Milestone 0）|
| V-2: AI SDK pre-stream user message lifecycle | TC-int-v2-01 in `implementation_test_cases.md` |
| V-3: AI SDK stop() abort semantic | TC-int-v3-01 in `implementation_test_cases.md` |
| 全部 unit/component/hook/integration test 寫法 | `implementation_test_cases.md` §1-§4 完整 spec |
| 6 個 E2E Tier 0 test 寫法 | `implementation_test_cases.md` §5 |

---

## Cross-Reference Index

| Need | 看這個 |
|---|---|
| 一個 BDD scenario 在哪一層 verify？ | `bdd_scenarios.md` "Verification Layer Summary" |
| 一個 unit/component/hook/integration/e2e 的具體 test 怎麼寫？ | `implementation_test_cases.md` §1-§5 |
| testid contract / DOM 約定？ | `implementation_prerequisites.md` §1 |
| MSW fixture 怎麼建 / 啟用？ | `implementation_prerequisites.md` §2-§3 |
| Smart retry / aborted state 怎麼實作？ | `implementation_prerequisites.md` §5-§6 |
| Real backend 整合驗證怎麼跑？ | **本文件 §2** |
| 視覺對齊 mockup 怎麼驗？ | **本文件 §3** |
| Manual smoke / UAT 跑什麼？ | **本文件 §5-§6** |
