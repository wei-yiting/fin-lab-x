# BDD Scenarios — S3 Streaming Chat UI

## Meta

- Design Reference: `artifacts/current/design_streaming_chat_ui.md`
- Generated: 2026-04-08
- Discovery Method: Three Amigos（Agent Teams：PO / Dev / QA）
- Source Inputs:
  - PO Round 1 Example Seeds（9 Features、22 examples、7 Questions）
  - Dev Round 1 Technical Challenges（27 items）+ Round 2 Sharpens & New（15 items）
  - QA Round 1 Destructive Challenges（40 items）+ Round 2 Build-ons & New（12 items）
  - PO Round 3 Value Judgments：26 Include / 45 Demote / 6 Reject / 9 Needs User Input
  - User Answers（Q-USR-1 ~ Q-USR-10）鎖定所有 ambiguous 決策
- Scenario Count: 38 Illustrative + 10 Journey = 48 total

## Scenario ID Convention

- `S-` Illustrative scenario prefix；`J-` Journey scenario prefix
- Feature abbreviations: `stream`（Streaming Lifecycle）、`tool`（Tool Card）、`md`（Markdown Sources）、`regen`（Regenerate）、`err`（Error）、`clear`（Clear Session）、`empty`（Empty State）、`stop`（Stop）、`scroll`（Scroll）、`cross`（Cross-Feature）
- Origin: `PO` / `Dev` / `QA` / `Multiple` / `UserInput`（user-pinned decision）

## Important: BDD scenarios are specs, not tests themselves

每個 scenario 描述「期望的 user-observable behavior」，是**永久 reference 規格**。實際驗證它的 test 屬於某一層，由 implementation 階段寫成 code。**不要把 scenario 跟 test 1:1 對應到單一 tool**。

5 個 verification layer：

| Layer | Tool | 何時跑 | 寫在哪 |
|---|---|---|---|
| `unit` | Vitest 純函式 | watch mode + CI | `implementation_test_cases.md` §1 |
| `component` | Vitest + RTL + jsdom | watch mode + CI | `implementation_test_cases.md` §2 |
| `hook` | Vitest + renderHook + msw/node | watch mode + CI | `implementation_test_cases.md` §3 |
| `integration` | Vitest + ChatPanel + msw/node | watch mode + CI | `implementation_test_cases.md` §4 |
| `e2e-tier0` | Playwright headless | every PR (CI gate) | `implementation_test_cases.md` §5 |
| `bdd-real` | Browser-Use CLI agent | implementation 完成後一次 | `verification_plan.md` Section 2 |
| `bdd-visual` | Browser-Use CLI agent | implementation 完成後一次 | `verification_plan.md` Section 3 |
| `manual-mbt` | 人 | release 前 | `verification_plan.md` Section 5 |
| `manual-uat` | 人 | release 前 | `verification_plan.md` Section 6 |

## Verification Layer Summary

每個 scenario 對應的 verification layer + 具體 TC ID（unit/component/hook/integration/e2e）或 verification plan section（bdd-real/bdd-visual/manual）：

### Feature 1: Streaming Lifecycle

| Scenario | Layer(s) | TC / Section |
|---|---|---|
| S-stream-01 | bdd-real + bdd-visual | verification_plan §2 / §3 |
| S-stream-02 | e2e-tier0 + bdd-real | TC-e2e-smoke-tool-01 + verification_plan §2 |
| S-stream-03 | bdd-real | verification_plan §2 |
| S-stream-04 | component | TC-comp-composer-02 |
| S-stream-05 | component | TC-comp-composer-01 |
| S-stream-06 | component | TC-comp-typing-02 |
| S-stream-07 | component | TC-comp-typing-01 (table case) |
| S-stream-08 | component | TC-comp-typing-01 (table case) |

### Feature 2: Tool Card State Machine

| Scenario | Layer(s) | TC / Section |
|---|---|---|
| S-tool-01 | component + bdd-visual | TC-comp-toolcard-01 + verification_plan §3 |
| S-tool-02 | component + unit | TC-comp-toolcard-01 + TC-unit-err-03 |
| S-tool-03 | component | TC-comp-assistant-01 |
| S-tool-04 | hook | TC-hook-progress-02 |
| S-tool-05 | hook | TC-hook-progress-01 |
| S-tool-06 | component | TC-comp-toolcard-01 (variant) |
| S-tool-07 | component | TC-comp-toolcard-02 |
| S-tool-08 | manual-mbt | verification_plan §5 (MBT-04) |
| S-tool-09 | component | TC-comp-toolcard-02 (variant) |

### Feature 3: Markdown Rendering & Sources Extraction

| Scenario | Layer(s) | TC / Section |
|---|---|---|
| S-md-streaming-plain-text | component | TC-comp-assistant-01 (defer-to-ready streaming phase) |
| S-md-ready-upgrade | component | TC-comp-assistant-01 (defer-to-ready ready phase) |
| S-md-01 | unit + component + bdd-real | TC-unit-md-01/02 + TC-comp-sources-01 + verification_plan §2 |
| S-md-02 | unit | TC-unit-md-03 |
| S-md-03 | unit + component + **e2e-tier0** | TC-unit-md-04 + TC-comp-sources-02 + **TC-e2e-xss-01** |
| S-md-05 | unit | TC-unit-md-06 |
| S-md-07 | bdd-visual | verification_plan §3 |
| S-md-08 | bdd-visual | verification_plan §3 |

### Feature 4: Regenerate Last Response

| Scenario | Layer(s) | TC / Section |
|---|---|---|
| S-regen-01 | integration | covered by TC-int-retry-01 setup |
| S-regen-02 | component | TC-comp-assistant-03 |
| S-regen-03 | component | TC-comp-assistant-03 |
| S-regen-04 | component | TC-comp-composer-02 |
| S-regen-05 | component | TC-comp-toolcard-02 (variant) |

### Feature 5: Stream Error Handling

| Scenario | Layer(s) | TC / Section |
|---|---|---|
| S-err-01 | unit + component | TC-unit-err-01/02/03/04 + TC-comp-error-01 |
| S-err-02 | integration + e2e-tier0 | TC-int-v2-01 + TC-e2e-smoke-error-01 |
| S-err-03 | component | TC-comp-typing-01 (state derivation) |
| S-err-04 | integration | **TC-int-retry-01** |
| S-err-05 | component | TC-comp-assistant-01 |
| S-err-06 | component | TC-comp-assistant-02 |
| S-err-07 | integration | **TC-int-aborted-01** |
| S-err-08 | integration | TC-int-retry-01 (variant) |
| S-err-09 | hook + bdd-visual | TC-hook-followbottom-01 (variant) + verification_plan §3 |

### Feature 6: Clear Session

| Scenario | Layer(s) | TC / Section |
|---|---|---|
| S-clear-01 | integration + e2e-tier0 | TC-int-stop-clear-01 + **TC-e2e-smoke-clear-01** |
| S-clear-02 | component | TC-comp-header-01 |
| S-clear-03 | bdd-real | verification_plan §2 |
| S-clear-04 | integration | **TC-int-stop-clear-01** |

### Feature 7: Empty State + Prompt Chips

| Scenario | Layer(s) | TC / Section |
|---|---|---|
| S-empty-01 | component + bdd-visual | TC-comp-empty-01 + verification_plan §3 |
| S-empty-02 | component | TC-comp-composer-03 |

### Feature 8: Stop Streaming

| Scenario | Layer(s) | TC / Section |
|---|---|---|
| S-stop-01 | integration + **e2e-tier0** | TC-int-stop-clear-01 + **TC-e2e-stop-01** |
| S-stop-02 | integration | TC-int-v3-01 |
| S-stop-03 | integration | TC-int-aborted-01 (variant) |
| S-stop-04 | **e2e-tier0** | **TC-e2e-stop-01** |

### Feature 9: Auto-scroll / Follow-Bottom

| Scenario | Layer(s) | TC / Section |
|---|---|---|
| S-scroll-01 | hook | TC-hook-followbottom-01 |
| S-scroll-02 | hook | TC-hook-followbottom-01 |
| S-scroll-03 | hook | TC-hook-followbottom-01 |
| S-scroll-04 | hook | TC-hook-followbottom-01 |
| S-scroll-05 | hook + manual-mbt | TC-hook-followbottom-01 (variant) + verification_plan §5 |

### Cross-Feature

| Scenario | Layer(s) | TC / Section |
|---|---|---|
| S-cross-01 | **e2e-tier0** | **TC-e2e-refresh-01** |
| S-cross-02 | manual-mbt | verification_plan §5 |

### Journey Scenarios

| Scenario | Layer(s) | TC / Section |
|---|---|---|
| J-stream-01 | bdd-real + bdd-visual | verification_plan §2 / §3 |
| J-stream-02 | **e2e-tier0** | **TC-e2e-smoke-tool-01** |
| J-tool-01 | bdd-real | verification_plan §2 |
| J-md-01 | bdd-visual | verification_plan §3 |
| J-regen-01 | integration | TC-int-retry-01 setup |
| J-err-01 | **e2e-tier0** | **TC-e2e-smoke-error-01** |
| J-err-02 | integration | TC-int-retry-01 variant |
| J-clear-01 | **e2e-tier0** | **TC-e2e-smoke-clear-01** |
| J-empty-01 | bdd-real | verification_plan §2 |
| J-stop-01 | **e2e-tier0** | **TC-e2e-stop-01** |
| J-scroll-01 | bdd-visual | verification_plan §3 |
| J-cross-01 | **e2e-tier0** | TC-e2e-refresh-01 |

### Layer 分布總計

| Layer | 數量 | 比例 |
|---|---|---|
| unit | 5 | 7% |
| component | 26 | 34% |
| hook | 6 | 8% |
| integration | 9 | 12% |
| **e2e-tier0** | **9** (含 journey) | **12%** |
| bdd-real | 11 | 14% |
| bdd-visual | 8 | 10% |
| manual-mbt | 4 | 5% |
| manual-uat | (5, 列在 verification_plan) | — |

部分 scenarios 屬多 layer（例如 S-md-03 同時有 unit + component + e2e 三層 defense），所以總和 > 76。

---

## Feature: Streaming Message Lifecycle

### Context

User 送出 message 後，backend 透過 SSE 串流回覆（text-delta / tool events / finish），`useChat` 的 status 依序轉換 `ready` → `submitted` → `streaming` → `ready`。UI 在不同階段呈現 TypingIndicator、逐字 Markdown、trailing Cursor、Composer button 切換等狀態。

### Rule: 送出訊息後，user 依序看到 thinking → assistant 串流 → 完成

#### S-stream-01: 純 text 回覆的完整串流生命週期

> 驗證從 send 到 finish 期間 UI 狀態正確依序出現

- **Given** Alice 剛開啟 chat 面板，處於 EmptyState，chatId 為自動生成的 UUID
- **When** 她輸入「NVDA 最近營收狀況？」並按下 Send
- **Then** user bubble 立即出現在對話串右側
- **And** 下方立即顯示 `TypingIndicator`（3 pulsing dots）
- **And** backend 開始串流 text 後 TypingIndicator 消失、assistant 內容逐字出現、文末帶 blinking `Cursor`
- **And** finish 事件到達後 Cursor 消失，Composer button 從 Stop 切回 Send

Category: Illustrative
Origin: PO

#### S-stream-02: Tool 先於 text 的混合回覆流程

> 驗證 tool event 到達時 TypingIndicator 跟 ToolCard 不會同時顯示

- **Given** Bob 處於 EmptyState
- **When** 他輸入「幫我查 NVDA 現價」並按下 Send
- **Then** user bubble 出現，短暫顯示 TypingIndicator
- **And** 收到 `tool-input-available` 時 TypingIndicator 消失，改為 🟠 running ToolCard
- **And** tool 完成後 ToolCard 變 🟢 success
- **And** 隨後 assistant 文字逐字出現，完成後 Cursor 消失

Category: Illustrative
Origin: PO

#### S-stream-03: 純 tool 查詢無後續 text 的 stream 完成

> 驗證即使沒有 text-delta，stream 完成後 Composer 仍回到可用狀態

- **Given** Carol 處於 EmptyState
- **When** 她送出純工具查詢（backend 只回 tool events + finish，無 text-delta）
- **Then** ToolCard 從 running 轉 success
- **And** 無 text 輸出時 finish 事件一到 Composer button 即切回 Send，textarea 重新可輸入

Category: Illustrative
Origin: PO

#### S-stream-04: 串流中 in-progress textarea 內容不被 finish 事件清除

> 驗證 user 在等待 stream 時繼續打字的輸入不會消失

- **Given** Alice 的 assistant 正在串流回答她上一題「What is NVDA Q2 revenue?」
- **And** Alice 在 Composer textarea 輸入「and compare to Q1」尚未送出
- **When** stream 自然完成（finish 事件到達，status 轉 ready）
- **Then** textarea 內容仍精確保留「and compare to Q1」
- **And** textarea focus / cursor 位置未被重設
- **And** Send button 立即 enabled，按 Enter 直接送「and compare to Q1」為新的 user message

Category: Illustrative
Origin: QA（textarea preservation，user-visible data loss guard）

#### S-stream-05: Rapid double-Enter 不產生重複 user bubble

> 驗證連按 Enter / double-click Send 的 race-condition 防護

- **Given** Bob 處於 `status === 'ready'` 狀態
- **When** 他輸入訊息並在 80 ms 內連按 Enter 兩次
- **Then** 對話串中只出現一則 user bubble
- **And** network 層只有一個對應的 POST `/api/v1/chat` request
- **And** 第二次 Enter 在 Composer guard 阻擋下 no-op

Category: Illustrative
Origin: QA（concurrent user action）

### Rule: TypingIndicator 只在「assistant 尚未有任何可渲染 part」時顯示

#### S-stream-06: 先收 transient progress 時 TypingIndicator 繼續顯示

> 驗證 transient sidecar 不算 "rendered part"

- **Given** Frank 送出訊息，status 轉為 `submitted`
- **When** backend 第一個 event 是 `data-tool-progress`（transient sidecar，不進 messages array）
- **Then** TypingIndicator 仍然顯示（因 `messages` array 內無任何 assistant rendered part）
- **And** 畫面上不出現 ToolCard（尚未收 `tool-input-available`）
- **And** 直到第一個 `text-delta` 或 `tool-input-available` 到達，TypingIndicator 才切換

Category: Illustrative
Origin: Dev（design Rule 1.2 邊界）

#### S-stream-07: Error 是 rendered part，TypingIndicator 應立即隱藏

> 驗證 assistant message 只有 error part 時的視覺優先級

- **Given** Frank 送出訊息，status 轉為 `streaming`
- **When** backend 發出 `start` event 後緊接 `error` event（LLM 被 rate-limited，無任何 text）
- **Then** useChat 將 error part append 到 last assistant message
- **And** TypingIndicator 消失（存在 rendered part）
- **And** 對應位置顯示 inline ErrorBlock
- **And** 不出現「ErrorBlock 旁邊仍有 typing dots」的衝突視覺

Category: Illustrative
Origin: QA（F1 × F5 cross-feature boundary）

#### S-stream-08: status === 'ready' 且有歷史 assistant 訊息時不顯示 TypingIndicator

> 驗證 idle 狀態下 UI 不誤顯示 loading

- **Given** Dave 完成一輪對話，last message 是 assistant 且 status === `ready`
- **When** 沒有任何新訊息在送
- **Then** 畫面上不應顯示 TypingIndicator

Category: Illustrative
Origin: PO

### Journey Scenarios

#### J-stream-01: Pure text 回答端到端完整生命週期

> 證明 "send → SSE stream → text-delta → finish → ready" 整條 pipeline 對使用者可感知

- **Given** 一位新 user 開啟 chat 面板
- **When** 她輸入一個無工具需求的開放問題並按 Send、等待完整回覆、stream 結束後 button 回到 Send mode
- **Then** 她看到自己的問題、短暫 thinking dots、逐字顯示的 markdown 內容與結尾 blinking cursor、最後 Cursor 消失 Composer 回到 Send 狀態

Category: Journey
Origin: Multiple

#### J-stream-02: Tool + text 混合回答端到端流程

> 證明 tool lifecycle 跟 text streaming 在同一個 assistant turn 正確並存

- **Given** 一位新 user 開啟 chat 面板
- **When** 她輸入會觸發 tool 查詢的問題、等待 tool 執行、等待 tool 完成、等待 text 串流與 finish
- **Then** 她依序看到 user bubble、typing dots、🟠 running ToolCard、🟢 success ToolCard、逐字 text 出現、trailing Cursor、finish 後 Composer 回復 Send mode 且 ToolCard 與 text 同時可見

Category: Journey
Origin: Multiple

---

## Feature: Tool Card State Machine

### Context

Tool invocation 有 3 個視覺狀態（🟠 running / 🟢 success / 🔴 error），以 `ToolUIPart.state` 為 SoT；`data-tool-progress` 是 transient sidecar，即時更新 running ToolCard 的 label，不進入 messages array。用戶答案 Q-USR-3 額外新增 **aborted**（灰色）視覺狀態用於 stop/mid-stream error 時的 running tool。

### Rule: ToolCard 依 `ToolUIPart.state` 顯示 running / success / error 三種視覺狀態

#### S-tool-01: Tool success 視覺狀態轉換

- **Given** Grace 送出「查 AAPL 現價」，tool_call_id 為 `tc_g1`
- **When** backend 依序發 `tool-input-available` → `tool-output-available`
- **Then** ToolCard 先呈現 🟠 amber pulsing dot + label「Calling yfinance...」
- **And** 收到 `tool-output-available` 後轉為 🟢 綠點 + label `"Completed"`
- **And** 點擊 header 可展開查看 INPUT / OUTPUT JSON 區塊

Category: Illustrative
Origin: PO

#### S-tool-02: Tool error inline 呈現 friendly translated text（不顯示 backend raw）

- **Given** Heidi 送出一個會失敗的查詢，tool_call_id 為 `tc_h1`
- **When** backend 依序發 `tool-input-available` → `tool-output-error` 帶 backend raw errorText `"API rate limit exceeded"`
- **Then** ToolCard 呈現 🔴 紅點 + inline 顯示 friendly translated title `"Too many requests. Please wait a moment and try again."`
- **And** inline **不直接顯示** backend raw `"API rate limit exceeded"`
- **And** 展開後可查看 INPUT JSON 區塊與「ERROR DETAIL」block，後者顯示原始 backend raw message 供 debug

Category: Illustrative
Origin: PO（base）+ Q-USR-4 friendly mapping refinement

#### S-tool-03: 並列 tool 的視覺狀態互不影響

> 驗證多 tool 並列時各自獨立呈現，順序穩定

- **Given** Ivan 送出一個需要兩個 tool 的問題
- **When** backend 依序發 `tool-input-available(tc_i1)` → `tool-input-available(tc_i2)` → `tool-output-available(tc_i1)` → `tool-output-error(tc_i2)`
- **Then** 同一則 assistant message 內出現兩張獨立 ToolCard
- **And** tc_i1 顯示 🟢，tc_i2 顯示 🔴，狀態互不影響
- **And** 兩張 ToolCard 的視覺順序在整個 streaming 過程中 stable（由 arrival order 決定）
- **And** tc_i1 完成時 user 展開的狀態不會因 tc_i2 後續完成而重設

Category: Illustrative
Origin: Multiple（PO seeded + QA 加強 render order stability）

### Rule: `data-tool-progress` 即時更新 running ToolCard label，不跨 tool 污染

#### S-tool-04: 單一 tool 的 progress 訊息即時更新

- **Given** Judy 的 tool_call_id `tc_j1` 處於 running 狀態
- **When** backend 發出 `data-tool-progress` `{id: "tc_j1", data: {message: "Fetching NVDA quote..."}}`
- **Then** ToolCard 的 label 從 `"Calling yfinance..."` 更新為 `"Fetching NVDA quote..."` 即時反映

Category: Illustrative
Origin: PO

#### S-tool-05: 並列 tool 的 progress 路由獨立不互相污染

> 驗證 `useToolProgress` Record 以 `toolCallId` 為 key，跨 tool 不串流

- **Given** Ivan 的 assistant 同時 running `tc_i1`（yfinance）與 `tc_i2`（news_search）
- **When** backend 發出 `data-tool-progress {id: "tc_i2", data: {message: "Searching news..."}}`
- **Then** 只有 tc_i2 對應的 ToolCard 顯示 `"Searching news..."`
- **And** tc_i1 對應的 ToolCard 繼續顯示 `"Calling yfinance..."`
- **And** tc_i1 的 ToolCard 不因 tc_i2 的 progress 事件而 re-render label

Category: Illustrative
Origin: Dev

#### S-tool-06: Tool success 後 progress 文字不沿用

- **Given** Laura 的 tool_call_id `tc_l1` 曾收過 progress `"Fetching quote..."`
- **When** backend 發出 `tool-output-available`
- **Then** ToolCard 變為 🟢 success
- **And** label 改顯示 generic `"Completed"`，不沿用 progress 文字

Category: Illustrative
Origin: PO

### Rule: ToolCard 預設 collapsed，展開可看 INPUT / OUTPUT JSON

#### S-tool-07: Success ToolCard 展開查看 INPUT / OUTPUT

- **Given** Mike 看到一張 🟢 success ToolCard
- **When** 他點擊 ToolCard header
- **Then** 下方展開顯示 INPUT / OUTPUT 兩個 JSON 區塊，各帶 `INPUT` / `OUTPUT` badge label

Category: Illustrative
Origin: PO

#### S-tool-08: 大型 OUTPUT JSON 展開不 freeze 主執行緒

> 驗證 500KB payload（例如 sec_10k_sections）的渲染效能

- **Given** Mike 的 tool `tc_m1` 完成，OUTPUT 是約 500KB 的 JSON payload
- **When** 他點擊 ToolCard header 展開
- **Then** UI 在合理時間內完成展開（不出現肉眼可見的 freeze）
- **And** 展開後若有同時進行的其他 stream，stop button 仍保持 responsive
- **And** 展開期間 Composer textarea 仍可正常輸入

Category: Illustrative
Origin: QA（boundary value / payload size）

#### S-tool-09: Error ToolCard 展開顯示 INPUT

- **Given** Nancy 看到一張 🔴 error ToolCard
- **When** 她點擊 header 展開
- **Then** 展開可看到 INPUT JSON 區塊

Category: Illustrative
Origin: PO

### Journey Scenarios

#### J-tool-01: 並列 tools 完整 lifecycle 與獨立順序

> 證明多 tool 並列場景下視覺狀態、progress 路由、展開互動全部正確隔離

- **Given** 一位 user 問了一個需要兩個並列 tool 查詢的問題
- **When** 兩個 tool 分別進入 running 狀態、接收各自的 progress 更新、其中一個成功一個錯誤、user 在其中一個 running 時展開查看 INPUT
- **Then** 兩張 ToolCard 依 arrival 順序穩定排列，progress 文字各自正確更新，success/error 終態互不污染，user 展開的狀態不被另一張 card 的事件重設

Category: Journey
Origin: Multiple

---

## Feature: Markdown Rendering & Sources Extraction

### Context

Assistant 回覆支援 GFM markdown（表格、strikethrough）。Sources extraction 採 **defer-to-ready 策略**：streaming 期間 `[N]` 保留為純文字、Sources block **不渲染**、reference definition 暫時以 raw markdown 顯示；stream 結束（`status` 轉 `ready` 或 mid-stream `error`）後 AssistantMessage 一次性呼叫 `extractSources(text)`，正文 `[N]` 升級為 `RefSup` 上標、definition 行從顯示的 text 中被 strip、底部出現 Sources block（顯示 title，無則 hostname fallback）。

用戶答案鎖定：dedup = first-wins（Q-USR-8），orphan body ref 顯為純文字、orphan def 仍顯示（Q-USR-9），非 http(s) scheme 不得渲染為 `<a>`（Q-USR-11 security）。

> **策略 rationale**：原 design 嘗試在 streaming 中把 sources 逐步 populate，但 react-markdown 不暴露 unified plugin 的 `file.data`，必須雙 parse；且 AssistantMessage 被迫從 stateless 變 stateful 以接收 callback sources。defer-to-ready 把 extraction 壓到 stream 結束的單次 `useMemo`，解掉雙 parse + stateless 違反兩個問題。代價是 streaming 中 reference 為 pop-in 效果（ChatGPT / Claude.ai 都是此做法），此 UX 決議由 user 確認。

### Rule: Reference 與 Sources block 在 stream 結束（status 離開 `streaming`）後一次性呈現

#### S-md-streaming-plain-text: Streaming 期間 reference 顯示為純文字，無 Sources block

> 驗證 defer-to-ready 策略的 streaming phase behavior

- **Given** assistant 正在串流，已接收文字為：
  ```
  NVDA 宣布擴大 Blackwell 產能 [1]，第二季營收優於預期 [2]。

  [1]: https://reuters.com "Reuters"
  ```
- **When** status === `streaming` 且該 message 為 last
- **Then** 正文中 `[1]` `[2]` 顯示為純文字，**非**可點 RefSup
- **And** 底部**不出現** Sources block
- **And** definition 行 `[1]: https://reuters.com "Reuters"` 以 raw markdown 暫時顯示在文字末端
- **And** trailing Cursor 在 markdown block 末端閃爍

Category: Illustrative
Origin: UserInput（defer-to-ready 策略決議）

#### S-md-ready-upgrade: Stream 結束後 reference 升級為 RefSup + Sources block 出現

> 驗證 defer-to-ready 策略的 ready phase behavior

- **Given** S-md-streaming-plain-text 的狀態 — streaming 中 `[1]` 為純文字、definition 以 raw 顯示
- **When** backend 發 `finish` event，status 從 `streaming` 轉為 `ready`
- **Then** AssistantMessage 的 `useMemo` recomputes，呼叫 `extractSources(concatenatedText)` 拿到 `[{label: "1", url: "https://reuters.com", title: "Reuters", hostname: "reuters.com"}]`
- **And** 正文中 `[1]` 升級為可點 `<RefSup label="1" href="#src-1">` 上標
- **And** 底部出現 Sources block 顯示「1 · Reuters」
- **And** displayText strip 掉 `[1]: https://reuters.com "Reuters"` 這行，raw definition 從顯示中消失
- **And** trailing Cursor 消失

Category: Illustrative
Origin: UserInput（defer-to-ready 策略決議）

### Rule: Reference definition 被抽取為 Sources block，不以底部純文字列表呈現

#### S-md-01: Sources block 依 title / hostname fallback 顯示

> Table-driven：驗證 definition 有 title 顯示 title、無 title 顯示 hostname

- **Given** assistant 回覆包含 reference `<label>`，URL `<url>`，定義是否帶 title 為 `<with_title>`
- **When** stream 完成
- **Then** Sources block 顯示一行 `<expected_display>`，正文中 `[<label>]` 為可點的 superscript 連結
- **And** 底部不出現 raw `[<label>]: <url>` 文字列

| label | url                                   | with_title | expected_display                              | notes              |
|-------|---------------------------------------|------------|-----------------------------------------------|--------------------|
| 1     | https://reuters.com/nvda-blackwell-expansion | yes | 1 · Reuters: NVIDIA expands Blackwell production | title 優先         |
| 2     | https://bloomberg.com/nvda-q2                | no  | 2 · bloomberg.com                                 | hostname fallback  |
| 3     | https://cnbc.com/nvda-news                   | yes | 3 · CNBC: NVDA news                               | 同 row 1 pattern   |

Category: Illustrative（table-driven）
Origin: PO

#### S-md-02: Duplicate reference label first-wins dedup

> 驗證 LLM 重複 `[1]: a` `[1]: b` 時 Sources block 只顯示第一個

- **Given** assistant 回覆 markdown 包含兩個同 label 的 definition：`[1]: https://reuters.com/a "Reuters A"` 與 `[1]: https://bloomberg.com/b "Bloomberg B"`
- **When** stream 完成
- **Then** Sources block 只顯示一條 entry「1 · Reuters A」（first-wins）
- **And** 正文中所有 `[1]` superscript 連結的 href 都指向第一個 definition 的 anchor
- **And** DOM 中 `id="src-1"` 唯一存在，無重複 id

Category: Illustrative
Origin: QA + UserInput（Q-USR-8: first-wins）

#### S-md-03: 非 http(s) URL 不得渲染為可點的 `<a>` 元素

> Security guard：防止 `javascript:` scheme 造成 XSS

- **Given** assistant 回覆 markdown 包含 `[1]: javascript:alert(1) "Click me"`
- **When** stream 完成
- **Then** Sources block 該條目的連結**不得為可點的 `<a href="javascript:...">`**
- **And** 該 entry 或被 filter out、或降級為純文字顯示
- **And** 給定 `[2]: mailto:ir@nvidia.com "Contact IR"` 時同樣處理（非 http(s) 一律不渲染為可點外連結）
- **And** 整個 Markdown organism 不因此 throw / 白屏

Category: Illustrative
Origin: QA（security boundary, critical）

#### S-md-05: Orphan reference 處理 — body 孤兒顯為文字、def 孤兒仍顯示

> 驗證 user answer Q-USR-9 的處理規則

- **Given** assistant 回覆 markdown：
  ```
  NVDA 很棒 [3]。

  [1]: https://reuters.com "Reuters"
  ```
  （body 引用 `[3]` 但無對應 def；`[1]` 的 def 存在但 body 未引用）
- **When** stream 完成
- **Then** 正文中 `[3]` 顯示為純文字「[3]」而非可點 RefSup
- **And** Sources block 仍顯示 def 孤兒「1 · Reuters」供使用者參考
- **And** 沒有 href 指向不存在的 anchor，點擊正文 `[3]` 不會 404 跳轉

Category: Illustrative
Origin: QA + UserInput（Q-USR-9）

### Rule: Inline reference superscript 點擊跳轉至 Sources 對應條目

#### S-md-07: RefSup 點擊在 ScrollArea viewport 內 scroll 到對應 anchor

> 驗證 ScrollArea container 內的 anchor 跳轉不依賴 document-level scroll

- **Given** Rachel 閱讀一則有 5 條 reference 的長回覆
- **And** MessageList viewport 被 scroll 到對話中段，Sources block 在 viewport 內但 `[3]` 對應條目不在視窗內
- **When** 她點擊正文中的 `[3]` superscript
- **Then** MessageList 的 ScrollArea viewport scroll 到 `#src-3` 條目位置可見
- **And** document.scrollTop 不變（跳轉侷限在 ScrollArea 內部）
- **And** 若當時 follow-bottom 為 true，此點擊暫停 follow-bottom，後續新訊息不把 viewport 拉回底部

Category: Illustrative
Origin: Dev + QA（merged）

### Rule: Markdown 隨 text-delta 增量呈現，結尾 cursor 顯示串流中

#### S-md-08: 逐字呈現 + trailing cursor 的 streaming markdown

- **Given** Sam 送出一個有 markdown 格式（粗體、list）的問題
- **When** backend 每 50 ms 送出一段 text-delta
- **Then** 文字逐段出現並重新 render 各種 markdown 格式
- **And** 最後一個字元後緊跟 blinking `Cursor`
- **And** finish 事件到達後 Cursor 消失

Category: Illustrative
Origin: PO

### Journey Scenarios

#### J-md-01: 長回答端到端 — streaming markdown、Sources populate、RefSup 跳轉

> 證明 markdown pipeline + Sources extraction + anchor scroll 在完整 stream 過程中正確運作

- **Given** 一位 user 問了一個會產生長回答且含 3 條 reference 的問題
- **When** stream 過程中 text 逐字出現、reference definitions 陸續到達、Sources block 從空逐步成長、stream 完成後 user 點擊正文中的 `[2]` RefSup
- **Then** 她看到 markdown 格式正常渲染、Sources block 依 label number 排序、點擊 RefSup 後 ScrollArea 捲到對應條目

Category: Journey
Origin: Multiple

---

## Feature: Regenerate Last Response

### Context

最後一則 assistant message 底部顯示 ghost `RegenerateButton`，點擊後移除該 turn 重新串流。Backend `_find_regenerate_target()` 僅允許最後一個 assistant turn。依 user answer Q-USR-1：streaming 進行中 button 一律隱藏。

### Rule: 最後一則 assistant message 顯示 `RegenerateButton`

#### S-regen-01: 點擊 RegenerateButton 重新串流

- **Given** Uma 完成一輪對話，畫面上最後一則 assistant message 已完成
- **When** 她點擊該訊息底部的 ghost RegenerateButton
- **Then** 該則 assistant message 立即從畫面移除
- **And** 畫面重新進入 streaming 狀態（TypingIndicator → 新內容逐字出現）
- **And** Composer button 切為 Stop mode

Category: Illustrative
Origin: PO

#### S-regen-02: 只有最後一則 assistant message 有 RegenerateButton

- **Given** Victor 完成 3 輪對話，對話串含 3 則 assistant messages
- **When** 她觀察三則 assistant messages
- **Then** 僅第 3 則（最後一則）底部顯示 RegenerateButton
- **And** 第 1、2 則 assistant messages 不顯示 RegenerateButton

Category: Illustrative
Origin: PO

#### S-regen-03: Streaming 進行中所有 assistant messages 皆不顯示 RegenerateButton

> 依 Q-USR-1 pin：避免 stale button 觸發 422

- **Given** Wendy 送出新問題後 assistant 正在串流新回覆
- **When** `useChat.status === 'streaming'`
- **Then** 目前正在串流的 assistant message 不顯示 RegenerateButton
- **And** 任何既有歷史 assistant messages 也不顯示 RegenerateButton（即使是之前的 "最後一則"）
- **When** streaming 結束 status 轉為 `ready`
- **Then** 新的 last assistant message（剛完成的那則）顯示 RegenerateButton

Category: Illustrative
Origin: Dev + UserInput（Q-USR-1）

#### S-regen-04: Regenerate 觸發時保留 Composer textarea 內的 in-progress 輸入

> 驗證 regenerate 不清 user 正在打的新問題

- **Given** Wendy 完成一輪對話，畫面上有最後的 assistant message
- **And** Wendy 在 Composer textarea 輸入「and also what about Q3 earnings?」尚未送出
- **When** 她點擊 RegenerateButton
- **Then** 該則 assistant message 被移除，重新進入 streaming
- **And** Composer textarea 內容仍精確保留「and also what about Q3 earnings?」
- **And** regenerate 完成後 button 回到 Send，textarea 內容可直接 Enter 送出

Category: Illustrative
Origin: QA（textarea preservation across regenerate）

#### S-regen-05: Regenerate 後新 ToolCard 為 collapsed 且不繼承舊 state / progress

> Merged: Ch-QA-9 + Ch-Dev-13 + Ch-QA-R2-4（跨 turn 的 ToolCard state 隔離）

- **Given** Uma 上一則 assistant message 含 🟢 success ToolCard（tc_u1）user 已展開查看 OUTPUT，且 toolProgress Record 殘留 `"Fetch complete"` 文字
- **When** 她點擊 RegenerateButton
- **Then** 舊的 tc_u1 ToolCard 與其展開狀態一併移除
- **And** `toolProgress` Record 中 tc_u1 對應的 entry 被清除
- **And** 新 stream 產生的 ToolCard（即使 toolCallId 恰好與舊的相同）預設 collapsed
- **And** 新 ToolCard 不顯示舊 progress 文字

Category: Illustrative
Origin: Multiple

### Journey Scenarios

#### J-regen-01: 完整 regenerate recovery flow

> 證明從不滿意的回答 → 點擊 regenerate → 新回答完整呈現的 E2E

- **Given** 一位 user 已經完成一輪對話但不滿意回答
- **When** 她點擊最後一則 assistant message 底部的 RegenerateButton，等待新 stream 完成
- **Then** 舊 assistant message（含其 ToolCard 與 Sources）被完整移除，新 stream 從頭進行直到 ready，新 assistant message 有自己獨立的 parts、ToolCard 初始 collapsed、Sources 重新抽取

Category: Journey
Origin: Multiple

---

## Feature: Stream Error Handling

### Context

錯誤路徑分兩條：**pre-stream HTTP error**（`useChat.error` 被 set，ErrorBlock 渲染為對話串末尾獨立元素，不 append 到 messages）與 **mid-stream SSE error**（`error` part append 到 last assistant message，ErrorBlock inline 呈現）。兩者 Retry 按鈕都 route 到 `handleRetry` callback。依 user answers：error messaging = distinct friendly per class（Q-USR-4），error text > 200 字截斷 + 展開（Q-USR-6），retry 失敗降級策略 = smart retry 422-on-regen → sendMessage（Q-USR-7）。

### Rule: Pre-stream HTTP error 顯示為獨立 ErrorBlock 元素

#### S-err-01: Pre-stream HTTP error 顯示 friendly English distinct messaging

> Table-driven：驗證 user answer Q-USR-4 的 distinct messaging。所有 user-facing error text 為 user-friendly **English**（對齊 Q5 V1 UI 英文政策）。

- **Given** user 觸發某個 action 後 backend 回 `<status>` 錯誤
- **When** MessageList render
- **Then** 對話串末尾出現獨立 ErrorBlock（Alert variant=destructive + `AlertCircle` icon）
- **And** 錯誤文字精確等於 `<expected_title>`（透過 `lib/error-messages.ts` 翻譯，**非 backend raw message**）
- **And** Retry button 出現與否符合 `<retriable>`
- **And** ErrorBlock 不 append 到 `messages` array，後續 regenerate 不會誤把它當成 assistant turn

| status            | action                  | expected_title                                                       | retriable | origin |
|-------------------|-------------------------|-----------------------------------------------------------------------|-----------|--------|
| 422               | regenerate              | Couldn't regenerate that message. Please try again.                  | yes       | PO     |
| 404               | sendMessage new         | Conversation not found. Refresh to start a new one.                  | no        | PO     |
| 409 session busy  | sendMessage during busy | The system is busy. Please try again in a moment.                    | yes       | QA     |
| 500               | sendMessage             | Server error. Please try again.                                      | yes       | PO     |
| Network offline   | sendMessage             | Connection lost. Check your network and try again.                   | yes       | QA     |
| 5xx unknown       | sendMessage             | Something went wrong. Please try again.                              | yes       | Dev    |

Category: Illustrative（table-driven）
Origin: Multiple + UserInput（Q-USR-4）

#### S-err-02: Pre-stream error 時 user bubble 保留且 retry 不 dup

> Merged: Ch-Dev-1 + Ch-QA-18（optimistic user bubble preservation）

- **Given** Xavier 在已有 2 則對話的 session 送出新訊息，status 轉為 `submitted`
- **When** backend 回 HTTP 500 在任何 SSE 開始前
- **Then** user bubble 保留在 MessageList 末尾
- **And** 對話串顯示獨立 ErrorBlock（Alert + Retry）
- **And** `useChat.error` 被 set，TypingIndicator 消失
- **When** Xavier 點擊 Retry
- **Then** 原 ErrorBlock 立即消失
- **And** 對話串中只剩一則 user bubble（無複製）
- **And** 重新進入 streaming 狀態

Category: Illustrative
Origin: Multiple

#### S-err-03: Retry 後 ErrorBlock 與 TypingIndicator 不並存

> Ch-Dev-17: 驗證 retry 後 error state 被 useChat 立即清除

- **Given** Zach 看到一個 ErrorBlock（來自 pre-stream 422）
- **When** 他點擊 Retry 按鈕
- **Then** `useChat.error` 被 clear，ErrorBlock 立即從 DOM 消失
- **And** 新 request 進入 `submitted` 狀態，TypingIndicator 可出現
- **And** 同一時刻不同時看到 ErrorBlock 與 TypingIndicator

Category: Illustrative
Origin: Dev

#### S-err-04: Smart retry — regenerate 422 自動降級為 sendMessage 避免無限 loop

> 驗證 user answer Q-USR-7

- **Given** Yvonne 看到一個 ErrorBlock，錯誤來源是 regenerate 回 422「last turn not assistant」
- **When** 她點擊 Retry
- **Then** handleRetry 判斷錯誤類型為 422-on-regenerate
- **And** 降級為 `sendMessage(originalUserText)` 重送原 user message（而非再次呼叫 regenerate）
- **And** 新 stream 成功展開
- **And** 不陷入無限 422 loop

Category: Illustrative
Origin: Dev R2 + UserInput（Q-USR-7）

### Rule: Mid-stream SSE error 顯示為 assistant message 內嵌 ErrorBlock

#### S-err-05: Mid-stream error 保留已接收 text 與已抽取 Sources

> Merged: Ch-QA-22（preserve partial sources）+ base

- **Given** Amy 送出複雜查詢，assistant 正在串流
- **And** 已接收內容包含 2 段 text「NVDA Q2 表現 [1] 優於預期，另據 [2] 分析」與 definition `[1]: https://reuters.com "Reuters NVDA Q2"`（`[2]:` 尚未到達）
- **When** backend 發出 `error` event（orchestrator 拋 exception）
- **Then** 已接收的 2 段 text 完整保留顯示
- **And** Sources block 顯示「1 · Reuters NVDA Q2」已抽取條目
- **And** 正文中 `[1]` 仍為可點 RefSup
- **And** 正文中 `[2]` 為純文字（對應 def 從未到達）
- **And** 該 assistant message 下方出現紅色 inline ErrorBlock 帶 Retry

Category: Illustrative
Origin: Multiple

#### S-err-06: Mid-stream error 後已成功的 Tool 不被降級

> Ch-QA-23: 驗證 tool lifecycle 與 stream error 互相獨立

- **Given** Amy 的 assistant 已完成 `tc_a1`（ToolCard 🟢 success）但 text 尚未開始
- **When** backend 發出 mid-stream `error` event（LLM context overflow）
- **Then** ToolCard tc_a1 維持 🟢 success 狀態（實際上成功了）
- **And** ErrorBlock 出現在 ToolCard **下方**（同一 assistant message 內）
- **And** RegenerateButton 不在此時顯示（stream 尚未結束，依 S-regen-03）

Category: Illustrative
Origin: QA

#### S-err-07: Mid-stream error 時 running ToolCard 轉為 aborted 灰色狀態

> 依 user answer Q-USR-3：新增 aborted visual state 用於 error / stop 場景

- **Given** Amy 的 assistant 有 `tc_a2` 處於 `input-available`（🟠 running）且已收 2 段 text-delta
- **When** backend 發出 mid-stream `error` event
- **Then** 2 段 text 保留顯示
- **And** ToolCard tc_a2 轉為 **aborted 灰色視覺狀態**（不再 pulsing、不沿用 running 文字）
- **And** 該 ToolCard 仍可展開查看 INPUT JSON
- **And** inline ErrorBlock 出現在 assistant message 內

Category: Illustrative
Origin: UserInput（Q-USR-3）+ QA

#### S-err-08: Mid-stream error retry 移除整個 assistant turn 重新串流

> Ch-Dev-18: optimistic rollback

- **Given** Ben 的 assistant message 有 partial text「NVDA...」+ inline ErrorBlock
- **When** 他點擊 inline Retry（regenerate 同 message id）
- **Then** 該則 assistant message 連同 partial text、部分 Sources、aborted ToolCard、inline ErrorBlock 一併立即從畫面移除
- **And** 不存在「舊 partial text + loading state」並存的過渡期
- **And** 新 stream 從頭開始

Category: Illustrative
Origin: Dev

#### S-err-09: ErrorBlock 出現時在 follow-bottom 模式下自動捲到可見位置

> Ch-Dev-R2-3: error 跟 scroll 的互動

- **Given** Xavier 的 messages 原本貼底，`shouldFollowBottom === true`
- **When** regenerate 回 422，`useChat.error` 被 set，ErrorBlock 插入對話串末尾
- **Then** MessageList 自動 scroll 讓 ErrorBlock 完整可見
- **And** 若當時 `shouldFollowBottom === false`（user 在對話中段閱讀），則不強制 scroll、保留 user 位置

Category: Illustrative
Origin: Dev R2

### Journey Scenarios

#### J-err-01: Pre-stream error 完整 recovery

> 從送出 → error → retry → 成功的 E2E

- **Given** 一位 user 處於空對話或有歷史對話的狀態
- **When** 她送出訊息、backend 回 pre-stream 錯誤、她點擊 Retry、backend 第二次回應成功並完整串流
- **Then** 她看到 user bubble 保留、friendly 錯誤訊息、點擊 Retry 後錯誤消失、新 stream 順利完成、最終對話串中只有一則 user bubble 與一則完整 assistant message

Category: Journey
Origin: Multiple

#### J-err-02: Mid-stream error recovery

> 從 partial response → error → retry → 成功的 E2E

- **Given** 一位 user 送出需要 tool + text 的複雜問題
- **When** tool 成功執行、text 串流一部分後 mid-stream error 到達、她點擊 inline Retry、backend 第二次成功完整串流
- **Then** 她看到 partial text + aborted ToolCard + inline ErrorBlock 完整被替換為新的完整 assistant message

Category: Journey
Origin: Multiple

---

## Feature: Clear Session

### Context

`"Clear conversation"` 將 `chatId` 重新 generate UUID，觸發 `useChat` 重 mount 清空 messages，並顯式呼叫 `useToolProgress.clearProgress()`。依 user answer Q-USR-5：streaming 中允許清除（內部先 stop 再 reset chatId）。Backend 不通知（舊 chatId 資料閒置）。

### Rule: 點擊 `"Clear conversation"` 回到 EmptyState 並使用新 chatId

#### S-clear-01: 對話進行中清除 → EmptyState + 新 chatId

- **Given** Cindy 在 chatId `sess-C1` 有 4 則 messages 的對話，且 assistant 已完成 tool 有 progress 殘留
- **When** 她點擊 ChatHeader 的 `"Clear conversation"` button（當時 status === `ready`）
- **Then** messages array 清空
- **And** `toolProgress` Record 清空
- **And** 畫面回到 EmptyState（welcome card + 4 prompt chips）
- **And** 內部 chatId 換為新 UUID（後續送出的新訊息使用新 chatId）

Category: Illustrative
Origin: PO

#### S-clear-02: EmptyState 時 `"Clear conversation"` button 為 disabled

- **Given** Dana 剛開啟 app，畫面是 EmptyState（`messages.length === 0`）
- **When** 她觀察 ChatHeader 的 `"Clear conversation"` button
- **Then** button 處於 disabled 狀態
- **And** 即使 click 也無 effect

Category: Illustrative
Origin: PO

#### S-clear-03: 清除後立即送新訊息使用新 chatId

- **Given** Erin 已點擊 `"Clear conversation"`，畫面是 EmptyState
- **When** 她輸入新問題並送出
- **Then** 新 stream 順利展開
- **And** 新訊息送到 backend 時使用的是新 chatId（而非舊的 `sess-C1`）
- **And** assistant 回答不反映舊 session 的任何 context

Category: Illustrative
Origin: PO

#### S-clear-04: Streaming 中清除 → graceful abort，無殘留 delta 渲染

> Ch-Dev-20 + UserInput Q-USR-5: 允許 streaming 中清除

- **Given** Cindy 的 assistant 正在串流，已接收 3 段 text-delta
- **When** 她點擊 `"Clear conversation"` button
- **Then** useChat 的舊 stream 立即 abort（AbortController fire）
- **And** messages 立即清空、`toolProgress` 清空、畫面回到 EmptyState
- **And** chatId 換為新 UUID
- **And** 舊 stream 後續到達的任何 SSE chunk 都被丟棄，不渲染到新 session 畫面
- **And** 不會出現「舊 assistant 殘餘 text 漂浮在新 EmptyState 上」的視覺衝突

Category: Illustrative
Origin: Dev + UserInput（Q-USR-5）

### Journey Scenarios

#### J-clear-01: 對話 → 清除 → 新對話的完整 session reset flow

> 證明 clear session 的 E2E 語意隔離

- **Given** 一位 user 進行 3 輪對話，其中包含 tool 查詢與引用來源
- **When** 她點擊 `"Clear conversation"`，確認畫面回到 EmptyState，然後送出一個測試 context 是否清空的新問題（例如 `"Do you remember what I mentioned earlier?"`）
- **Then** 她看到全部 messages 消失、prompt chips 重新出現、新 stream 成功、assistant 回答不反映先前對話內容

Category: Journey
Origin: Multiple

---

## Feature: Empty State + Prompt Chips

### Context

空對話顯示 welcome card（28px bold title + description）與 4 個英文 prompt chips。依 user answer Q-USR-2：點擊 chip 為 last-wins 覆蓋 textarea，不自動送出。

### Rule: Prompt chip 點擊填入 Composer textarea 但不自動送出

#### S-empty-01: 點擊 prompt chip 填入 textarea，不自動送出

- **Given** Faye 剛開啟 app，畫面顯示 EmptyState 含 4 個 prompt chips
- **When** 她點擊第 2 個 prompt chip（例如 `"Latest market news"`）
- **Then** Composer textarea 立即被填入完整 chip 文字
- **And** 不自動 trigger send（不產生 POST、不轉 streaming）
- **And** textarea focus 移入 chip 文字末尾，user 可繼續編輯或按 Send 送出

Category: Illustrative
Origin: PO

#### S-empty-02: 第 2 次點擊 prompt chip 覆蓋既有輸入（last-wins）

> 依 user answer Q-USR-2: 覆蓋而非 append

- **Given** Gina 已在 Composer textarea 輸入 `"analyze this"`
- **When** 她點擊某個 prompt chip（例如 `"Show revenue chart"`）
- **Then** textarea 內容被覆蓋為 `"Show revenue chart"`（last-wins）
- **And** 不變成 `"analyze this\nShow revenue chart"` 的 append 合併
- **When** 她再點擊第 3 個 chip
- **Then** textarea 內容再次被新 chip 文字完全覆蓋

Category: Illustrative
Origin: Dev + UserInput（Q-USR-2）

### Journey Scenarios

#### J-empty-01: Onboarding via prompt chip

> 證明新用戶可透過 chip 順利完成第一次對話

- **Given** 一位新 user 首次開啟 chat 面板看到 EmptyState
- **When** 她點擊某個 prompt chip、稍微編輯 chip 填入的文字、按 Send、等待 stream 完成
- **Then** 她看到 chip 文字填入 textarea、自己的編輯保留、user bubble 出現、assistant 正常回覆完整

Category: Journey
Origin: Multiple

---

## Feature: Stop Streaming

### Context

串流中 Composer button 從 Send 切為 Stop，點擊 Stop 呼叫 `useChat.stop()` 觸發 AbortController，backend 偵測 disconnect 後停止 LLM。依 user answer Q-USR-3：stop 時 running ToolCard 轉 aborted 灰色狀態。

### Rule: 串流中按下 Stop 可中止回覆並保留已接收內容

#### S-stop-01: Stop 中止 text 串流，保留已接收內容

- **Given** Hank 送出問題，assistant 正在串流，已接收 3 段 text-delta
- **When** 他點擊 Composer 的 Stop button
- **Then** 串流立即中止
- **And** 已接收的 3 段文字完整保留顯示
- **And** trailing Cursor 立即消失
- **And** Composer button 在 1 個 paint frame 內切回 Send mode
- **And** Composer textarea 重新可輸入（無 disabled 殘留）

Category: Illustrative
Origin: PO + Dev（sharpened to 1-frame latency）

#### S-stop-02: Stop 後 UI 無論 `stop()` promise 結果都必須立即 ready

> Merged: Ch-Dev-25 + Ch-Dev-R2-1 + Ch-QA-R2-8（AbortError / reject path）

- **Given** Hank 正在 streaming，網路狀況不穩
- **When** 他點擊 Stop，AbortController fire 但 `stop()` promise 可能 reject（例如 fetch 已自行 drop）
- **Then** `useChat.status` 必須轉為 `ready`（不能是 `error`）
- **And** `useChat.error` 保持 null（不被 AbortError 污染）
- **And** 不出現 ErrorBlock
- **And** partial text 保留可見
- **And** Composer 完全 re-enabled

Category: Illustrative
Origin: Multiple

#### S-stop-03: Stop 時 running tool 轉 aborted 灰色視覺狀態

> 依 user answer Q-USR-3

- **Given** Iris 的 assistant 有 `tc_i1` 處於 `input-available`（🟠 running），streaming 正進行中
- **When** 她點擊 Stop
- **Then** 串流中止，`status === 'ready'`
- **And** ToolCard tc_i1 從 🟠 running 轉為 **aborted 灰色狀態**（不再 pulsing、label 改為 `"Aborted"`）
- **And** 該 ToolCard 仍可展開查看 INPUT JSON
- **And** `toolProgress[tc_i1]` 的殘留文字被清除（不再顯示進行中暗示）

Category: Illustrative
Origin: UserInput（Q-USR-3）+ Dev

#### S-stop-04: Submitted 狀態下 Stop 保留 user bubble 但無 ghost assistant

> Ch-QA-30: user 送出後立即反悔的場景

- **Given** user 送出「What's the weather?」，`status === 'submitted'`，尚無任何 SSE event
- **When** 她點擊 Stop button
- **Then** user bubble 完整保留在對話串
- **And** 不出現空白/幽靈 assistant message
- **And** 不出現 ErrorBlock（她是主動 stop，不是錯誤）
- **And** `status === 'ready'`
- **And** Composer 恢復 Send mode，textarea 可編輯 / 送出新問題
- **And** 此時若觀察 RegenerateButton 不顯示（沒有 assistant turn）

Category: Illustrative
Origin: QA

### Journey Scenarios

#### J-stop-01: Stop + compose new question 的完整 flow

> 證明 stop 後可繼續正常使用

- **Given** 一位 user 送出一個會產生冗長回答的問題
- **When** 她看到 streaming 開始後覺得方向不對，點擊 Stop、確認 partial text 保留、在 Composer 輸入新的精確問題、按 Send、等待新 stream 完成
- **Then** 她看到 Stop 後 button 立即變 Send、partial 保留可讀、新 question 送出後 stream 從新一則 user bubble 開始、整個互動無 blocking

Category: Journey
Origin: Multiple

---

## Feature: Auto-scroll / Follow-Bottom

### Context

MessageList 使用 `useFollowBottom` hook 偵測 user scroll intent：當 user 離底部 100 CSS px 以內時 shouldFollowBottom=true，新 delta 自動捲到底；離開此範圍時保留 user 位置。依 user answer Q-USR-10：送新 message 時 force-follow 優先於 user intent。

### Rule: 100 px threshold smart tracking，Send 時 force-follow 勝出

#### S-scroll-01: 貼底時自動跟隨新 content

- **Given** Jake 貼在對話底部閱讀正在串流的 assistant message
- **When** 新 text-delta 持續到達
- **Then** viewport 自動跟著捲到底，新內容持續貼底顯示
- **And** 不出現「距底 50 px drift 卡住」的現象

Category: Illustrative
Origin: PO

#### S-scroll-02: 滾離底部時不打斷 user 閱讀

- **Given** Kim 正在看第 1 則 message（viewport 在對話最上方）
- **When** assistant 正在串流第 3 則 message
- **Then** viewport 維持在第 1 則 message 位置
- **And** 持續到達的 text-delta 不 auto-scroll viewport

Category: Illustrative
Origin: PO

#### S-scroll-03: 重回底部時恢復 follow-bottom 追蹤

- **Given** Lee 手動 scroll 到距底部 < 100 px 的位置
- **When** 新 text-delta 到達
- **Then** `shouldFollowBottom` 重新啟動
- **And** viewport 繼續跟隨到底

Category: Illustrative
Origin: PO

#### S-scroll-04: 送新訊息時 force-follow 優先於 user scroll intent

> 依 user answer Q-USR-10: force-follow 勝

- **Given** Maya 正在 streaming 中，手動 scroll 到上方讀歷史（離底 500 px，`shouldFollowBottom === false`）
- **When** 她在 Composer 輸入新問題並按 Send
- **Then** 立即強制 scroll 到底（force-follow）
- **And** `shouldFollowBottom` 被設為 true
- **And** viewport 捲到包含新 user bubble 的 scrollHeight（不是 send 前的舊高度）
- **And** 後續新 stream 持續跟隨到底

Category: Illustrative
Origin: PO + Dev + UserInput（Q-USR-10）

#### S-scroll-05: Keyboard scroll（PageUp / Space）正確打斷 follow-bottom

> Ch-QA-32: accessibility baseline

- **Given** Kim 正在閱讀 streaming 回答，當時 `shouldFollowBottom === true`
- **When** 她用鍵盤（Tab 聚焦到 ScrollArea 或類似 focusable 容器後按 PageUp / Space / Arrow Up）向上捲動
- **Then** `useFollowBottom` 偵測到 user 主動離底，`shouldFollowBottom === false`
- **And** 後續 text-delta 不自動 scroll 回底
- **When** 她按 End key 捲到底
- **Then** follow-bottom 重新啟動

Category: Illustrative
Origin: QA（accessibility）

### Journey Scenarios

#### J-scroll-01: 滑上去讀歷史、送新問題、自動追蹤的完整互動

> 證明 scroll lifecycle 在真實多輪對話下運作正確

- **Given** 一位 user 已有 5 輪對話，當前 assistant 正在串流第 6 則
- **When** 她滾到對話上方看第 2 則歷史、確認 viewport 不被自動捲下、送一個 follow-up 新問題、force-follow 啟動捲到底、新 stream 完成
- **Then** 她看到上滾時 viewport 穩定、送新問題後 viewport 立即跳到底、新 stream 持續追蹤、整個過程無違反意圖的 scroll 跳動

Category: Journey
Origin: Multiple

---

## Feature: Cross-Feature Invariants

### Context

跨 Feature 的系統層 invariants，涵蓋 browser lifecycle 與 session 語意。

### Rule: Browser 刷新 / back / forward 維持「refresh = 新對話」invariant（Design Q2）

#### S-cross-01: Browser refresh 生成新 chatId，舊對話消失

> 對應 design Q2「純記憶體 UUID，refresh = 新對話」

- **Given** 一位 user 有 10 則對話的完整 session，chatId 為 `uuid-A`
- **When** 她按 browser refresh（Cmd+R / F5）
- **Then** 畫面重新載入到 EmptyState
- **And** 新 chatId 為另一個 UUID（不等於 `uuid-A`）
- **And** 後續送出的新訊息不反映 `uuid-A` 的任何 context

Category: Illustrative
Origin: QA + Dev R2（pin design invariant）

#### S-cross-02: Browser back/forward 不重建舊對話

> Ch-QA-38: 跟 refresh 同語意的 invariant

- **Given** 一位 user 有 3 則對話的 session
- **When** 她點 browser Back 按鈕離開 /chat，10 秒後點 Forward 回到 /chat
- **Then** 畫面回到 EmptyState（對話未 restore）
- **And** chatId 為新 UUID
- **And** 行為與 refresh 一致（V1 無 session restore）

Category: Illustrative
Origin: QA + UserInput（pin as invariant）

### Journey Scenarios

#### J-cross-01: Refresh 在對話中段執行的完整 recovery flow

> 證明 refresh 語意對 user 可預期

- **Given** 一位 user 已完成數輪對話
- **When** 她不小心 refresh 頁面、看到回到 EmptyState、明白舊對話已消失、重新開始新對話
- **Then** 整個過程無 error、無殘留 UI 狀態、新對話完全獨立

Category: Journey
Origin: Multiple

---

## Scenario Summary

| Feature | Rules | Illustrative | Journey | Total |
|---|---|---|---|---|
| Streaming Lifecycle | 2 | 8 | 2 | 10 |
| Tool Card | 3 | 9 | 1 | 10 |
| Markdown & Sources | 4 | 8 | 1 | 9 |
| Regenerate | 1 | 5 | 1 | 6 |
| Stream Error | 2 | 9 | 2 | 11 |
| Clear Session | 1 | 4 | 1 | 5 |
| Empty State | 1 | 2 | 1 | 3 |
| Stop Streaming | 1 | 4 | 1 | 5 |
| Scroll / Follow-Bottom | 1 | 5 | 1 | 6 |
| Cross-Feature | 1 | 2 | 1 | 3 |
| **Total** | **17** | **56** | **12** | **68** |

**Markdown & Sources breakdown**：8 illustrative = 2 defer-to-ready behavior (S-md-streaming-plain-text, S-md-ready-upgrade) + 6 final-state extraction behavior (S-md-01/02/03/05/07/08)。原 S-md-04 (URL chunk boundary) 與 S-md-06 (incremental populate) 在 defer-to-ready 策略下不再適用，已移除；對應的 TC-unit-md-05 (malformed URL robustness) 與 TC-unit-md-07 (numeric label sort) 保留為 `extractSources` 的 internal invariant unit tests，不再 1:1 對應 BDD scenario。

Note: 某些 scenarios 為 table-driven（S-md-01、S-err-01），每 row 算一個獨立驗證點。

## Excluded from BDD scope（processed by PO Round 3 as Demote / Reject）

以下項目經討論後**不進入 BDD scenario**，改由 unit test / component test / contract test / manual smoke / design invariant 處理。這些項目仍然重要，但屬於 verification 層次而非 behavior test：

- **Component unit tests**: TypingIndicator visibility truth-table、`_isLast` derivation、Collapsible stable key、`useFollowBottom` hook reducer、`useToolProgress` batching、ErrorBlock 不注入假 message、`new URL()` defensive parse fallback
- **Contract tests**: `transient: true` S1/S3 wire format、S1 對 partial turn regenerate 的回應碼、AI SDK v6 pre-stream error 時 user message lifecycle
- **Manual smoke tests**: 250-char no-space progress overflow、CJK / emoji / full-width pipes 表格 render、horizontal scroll 內 `<pre>`、window resize、background tab throttling、50 k 字 paste bomb
- **Design invariants（禁止違反，非 runtime 驗證）**: Clear session 無 confirm dialog（V1 刻意 simplistic）、backend chatId orphan 不通知（Q2 accepted）、禁止用 localStorage persist chatId、mobile / virtual keyboard OOS
- **Reject items**: QA Ch-QA-25 / Ch-QA-35 / Ch-QA-37 / Ch-Dev-22 / Ch-Dev-R2-2（理由見 PO Round 3 Judgments）

---

## Appendix: User-Pinned Decisions（Q-USR-1 ~ Q-USR-10）

| # | Question | Decision |
|---|---|---|
| Q-USR-1 | Streaming 中 RegenerateButton 是否顯示 | 隱藏（ready 後才顯示）|
| Q-USR-2 | PromptChip 點擊時既有 textarea 處理 | 覆蓋 last-wins |
| Q-USR-3 | Stop / error 時 running ToolCard 視覺 | 新增 aborted 灰色狀態 |
| Q-USR-4 | ErrorBlock messaging 粒度 | Distinct friendly per class |
| Q-USR-5 | Streaming 中可否 `"Clear conversation"` | 允許（內部 stop → reset chatId）|
| Q-USR-6 | Error text 過長處理 | 截斷 200 字 + 展開更多 |
| Q-USR-7 | Retry 失敗 fallback | Smart retry: 422-on-regen → sendMessage |
| Q-USR-8 | Duplicate reference definition | First-wins |
| Q-USR-9 | Orphan reference 處理 | Body 孤兒文字化，def 孤兒仍顯示 |
| Q-USR-10 | Send vs user scroll intent | Force-follow 勝 |
