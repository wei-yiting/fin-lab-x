# BDD Scenarios

## Meta

- Design Reference (of record for reasoning UX): **ADR-0006** (`docs/adr/0006-reasoning-as-collapsed-transcript-chips.md`) + DEV-105 refactor spec + DEV-60 🔍 2026-07-24 ruling tables. On-disk `artifacts/current/design.md` 的 F5「ephemeral reasoning status」/ F6「19-state ReasoningIndicator」章節已被 2026-07-24 grilling 推翻(design.md 的 superseded 標記由 DEV-108 補)。
- Generated: 2026-05-01 · **Revised: 2026-07-24 for DEV-106 (F5 native reasoning parts + F6′ reasoning chips + placeholder ActivityIndicator + stall)**
- Discovery Method: Three Amigos (Agent Teams) — 2026-05 原版 27 topics / D1–D39;2026-07-24 DEV-106 修訂輪 (PO→Dev→QA challenge + cross-talk + judgment + contest),9 個 human 產品裁決見下表
- Scope (this revision = DEV-106 slice): 重寫 reasoning 傳輸 (native `reasoning-*` parts) 與呈現 (chips + placeholder + 10s stall) 兩塊。**未變更**:Provider Streaming Pipeline (F1/F2/F3/F8,僅把 reasoning-wire 斷言改 native parts)、**Langfuse Reasoning Persistence (F7) 整塊維持舊 per-call 設計**,其 trace-level 改版屬 DEV-107 / DEV-108,本次不動。

### DEV-106 human 產品裁決 (2026-07-24)

| # | 決策 | 裁決 |
|---|---|---|
| 1 | Multi-round chip 收合模型 | **只有當前輪 chip 展開**,前輪隨 loop 前進收合(Claude.ai 式);非 tail chip 由 finish/tail 驅動收合,非純 `part.state` |
| 2 | 「Thought for Xs」計時 | **在該輪第一個 tool-start 凍結**;abort 在 Stop 當下取樣 |
| 3 | 空 reasoning block | **只 suppress zero-delta**(完全不出 chip);已畫出的 chip(即使內容是 whitespace)保留、正常收合,不做事後移除 |
| 4 | Chip + tool card 重疊排版 | tool card 排在還開著的 chip **下方**,維持 part 到達順序 |
| 5 | Tool 執行期進度歸屬 | tool card 負責;chip→tool card 空檔不出 placeholder;長 (>10s) tool 期間無 degraded 面 |
| 6 | Aborted 半 chip header | **與完成區分**:`Stopped — thought for Xs`(完成為 `Thought for Xs`;error 但 reasoning-end 有到 → 乾淨 `Thought for Xs` + error 面) |
| 7 | 靜默 stall(無 TCP reset) | **Defer 自動偵測**;保留手動 Stop 逃生 + scenario;與既有「hung provider 需手動 Stop、keepalive deferred」一致 |
| 8 | Screen-reader | **加最小 `aria-live="polite"`** 於 placeholder + chip header |
| 9 | 串流中 reload | **丟掉進行中的 assistant turn**(無部分文字/chips/error 面;user prompt 留著) |

---

## Feature: Provider Streaming Pipeline

### Context

v1–v5 五個 agent version 統一綁到 Gemini 2.5 Flash（admin-configured per D24，user 無法 runtime 切換）；streaming pipeline 對 LangChain v1 chat model provider 跑通；驗收矩陣為 3 providers × 2 modes = 6 cases；non-streaming `Orchestrator.invoke` 路徑也支援多 provider。**本 Feature 於 DEV-106 僅微調 reasoning-wire 斷言(改 native `reasoning-*` parts);provider swap 本身 (F1/F2/F3) 屬 PR0/PR1a,scenario 保留。**

---

### Rule: Default agent provider binding 為 Gemini 2.5 Flash

#### S-stream-01: Default agent 跑 canonical SEC query 完成 streaming
> 驗證 v1–v5 agents 預設使用 `google_genai:gemini-2.5-flash` end-to-end streaming 跑通

- **Given** Alice 開啟 chat 介面，預設 agent version 為 v3
- **When** 她送出 D25 canonical prompt：「Compare Apple's 10-K fiscal year 2024 vs 2023 Item 1A risk factors and categorize changes (added / strengthened / removed)」
- **Then** Streaming 完成、final answer 渲染、無 console / network error
- **And** Backend 的 Langfuse trace 記錄該次 agent run 走 `google_genai:gemini-2.5-flash`

Category: Illustrative
Origin: PO

#### S-stream-02: 切換 agent version 在同一 session 內，新 turn 仍走 Gemini
> 驗證 agent version 切換對 streaming pipeline 不造成 regression

- **Given** Bob 在 session abc-123 用 v3 完成 3 個 turns
- **When** 他切換 active agent 到 v5 並送出新 query
- **Then** 新 turn streaming 完成走 Gemini 2.5 Flash；之前 turns 的 persisted `message.parts` 保持完整

Category: Illustrative
Origin: PO

---

### Rule: 6-case acceptance matrix（3 providers × 2 modes）跑通

#### S-stream-03: Multi-provider × multi-mode 矩陣 streaming 行為
> 驗證 streaming pipeline 對所有 LangChain v1 chat model provider × reasoning mode 都跑通。**DEV-106 修訂:reasoning 斷言改 native `reasoning-*` parts(移除舊 `data-reasoning-status` transient event 與 D12 multi-summary `\n` join)。**

- **Given** 設定 agent version 綁到 `<provider>` 並設 reasoning mode 為 `<mode>`
- **When** 送出 D25 canonical prompt
- **Then** Streaming 完成、final answer 渲染、wire 上 `reasoning-*` part 數量符合 `<parts_expectation>`

| provider                          | mode           | parts_expectation | notes                                    |
|-----------------------------------|----------------|-------------------|------------------------------------------|
| google_genai:gemini-2.5-flash     | reasoning-on   | ≥ 1 reasoning part | default agent baseline;multi-round → 多 parts |
| google_genai:gemini-2.5-flash     | reasoning-off  | = 0 reasoning parts | reasoning mode disabled                 |
| openai:gpt-5-mini-responses       | reasoning-on   | ≥ 1 reasoning part | OpenAI Responses summary blocks,raw passthrough(無 `\n` join)|
| openai:gpt-5-mini-responses       | reasoning-off  | = 0 reasoning parts | OpenAI Responses summary disabled       |
| anthropic:claude-4.x-sonnet       | reasoning-on   | ≥ 1 reasoning part | extended thinking;interleaved reasoning → 多 parts |
| anthropic:claude-4.x-sonnet       | reasoning-off  | = 0 reasoning parts | extended thinking disabled              |

Category: Illustrative (table-driven)
Origin: PO (D6 / D25) · DEV-106 修訂 (native parts)

---

### Rule: Provider boot 失敗的 user-facing surface 分流

#### S-stream-04: Provider boot 失敗於不同階段對應不同 surface
> 驗證 D23 兩路分流 protocol：pre-SSE / mid-stream 各自有對應 UX。Hung sub-case 隨 backend keepalive + first-chunk timeout 移出本期 scope(與 DEV-106 決策 7「靜默 stall defer」一致)。

- **Given** Backend 對應某 provider 處於 `<failure_state>`
- **When** Carol 送出一個 query
- **Then** Frontend 看到的 surface 是 `<expected_surface>`

| failure_state                           | expected_surface                              | notes                        |
|-----------------------------------------|-----------------------------------------------|------------------------------|
| Provider 套件缺失 / API key 無效         | HTTP 5xx via fetch error；useChat onError 觸發 | pre-SSE-open                 |
| 第一個 LLM call 立即報錯                 | SSE `error` event → error surface(見 S-pres-03)| mid-stream                   |
| ~~Provider 30s 內無回應~~                | **移出本期 scope**（hung 行為等同 main：無自動偵測，user 必須手動 Stop,見 S-pres-02） | keepalive 另立 PR  |

Category: Illustrative (table-driven)
Origin: Multiple (Dev R2 / QA R1 / D23)

---

### Rule: Non-streaming `Orchestrator.invoke` 路徑也跑通〔F7-adjacent,DEV-107/108 將修訂 Langfuse 斷言〕

#### S-stream-05: Batch eval `.invoke` 也產出 Langfuse reasoning trace
> 驗證 F8 + D30 contract。**⚠ 本 scenario 的 Langfuse `metadata.reasoning` 斷言反映 pre-F7 per-call 設計;F7 trace-level 改版屬 DEV-107,本次不改。**

- **Given** Internal caller 建立 `Orchestrator.invoke(query, agent_version="v3")` 跑 D25 canonical prompt
- **When** invoke 完成
- **Then** Langfuse trace 內每個 chat_model span 都有 `metadata.reasoning` key〔pre-F7 契約〕
- **And** Reasoning content 跟相同 prompt 走 streaming path 的對應 span 內容語義等價

Category: Illustrative
Origin: QA R1 (C1.5) + Dev R2 contest (D30)

---

### ~~Rule: SSE keepalive 防止 idle proxy 砍連線~~ — 移出本期 scope

#### ~~S-stream-06: 90 秒 reasoning silence 不被 proxy 中斷~~ — 移出本期 scope
> Backend SSE keepalive 整體挪到後續 PR;與 DEV-106 決策 7 一致(靜默 stall 不做自動偵測)。

Category: Illustrative (deferred to follow-up PR)

---

### Rule: Multi-tab 並發 streaming 互相 isolated（chips + stall 為 per-tab）

#### S-stream-07: 同 session 兩 tab 並發 streaming 不互相污染
> 驗證 D33 per-request mapper scope。**DEV-106 修訂:reasoning isolation 由 chips 承接——chips 純由「該 tab 自己的 `useChat` messages」derive,per-tab、無 cross-tab sync、v1 無 stream resume(QA11 裁定 out-of-scope)。Langfuse 斷言為 pre-F7,DEV-107/108 修訂。**

- **Given** Eve 在 Tab A 跟 Tab B 都開啟同一 session 的 chat
- **When** 兩 tab 同時送出不同 query 並進入 streaming
- **Then** 各 tab 只渲染自己 turn 的 reasoning chips(無 cross-tab reasoning 洩漏;非串流 tab 不顯示對方 chips)
- **And** 〔pre-F7〕Langfuse 上對應兩個獨立 traces,各自 chat_model span `metadata.reasoning` 只含自己 tab 的 reasoning

Category: Illustrative
Origin: QA R1 (CR.4 + CR.6) · DEV-106 修訂 (per-tab chips)

---

### Rule: Provider 在 abort 後 next turn 不被 contaminated state 影響

#### S-stream-08: Abort 後立即 resend 同 session 仍可運作
> 驗證 backend cancellation cleanup 不留下 stale state（D35）。前端對應行為見 S-pres-02。

- **Given** Frank 送出 query 進入 reasoning streaming
- **When** 他在第 5 秒 click Stop，然後立即送出新 query
- **Then** 新 query 完整 streaming 完成；session checkpointer 不被 abort 半成品污染;〔pre-F7〕Langfuse 紀錄前一個 trace `metadata.status = "aborted"`，新 trace 為正常 completed

Category: Illustrative
Origin: Dev R2 (C3.6) + D35

---

### ~~Rule: CJK reasoning 無終止符時 segmenter 仍在 streaming 期間 emit~~ — 移除(F5 刪 segmenter)

#### ~~S-stream-09: 80 字 char-count fallback 在 CJK 無終止符 case 觸發 soft-emit~~ — 移除
> **F5 移除 `ReasoningSegmenter`,provider delta 原樣直通,無 char-count fallback。CJK streaming 呈現改由 chip 的 raw passthrough + CSS wrapping 處理,見 S-chip-02。**

Category: 移除 (segmenter deleted by F5)

---

### Journey Scenarios

#### J-stream-01: 完整 6-case matrix E2E lifecycle
> 驗證 streaming pipeline 對 3 provider × 2 mode 的 6 cases 都從 query 送出到 final answer 顯示完整跑通。**DEV-106 修訂:reasoning 斷言改 native parts。**

- **Given** 一個新 session
- **When** 對 6 cases 各跑一次 D25 canonical prompt（含 multi-tool synthesis 流程）
- **Then** 每個 case streaming 完成；reasoning-on cases wire 上至少 1 個 `reasoning-*` part 且 UI 至少 1 顆 chip;reasoning-off cases 0 reasoning parts / 0 chips；無 console / network error；6 個 Playwright video 錄影可供 reviewer 親眼看每家 streaming 行為

Category: Journey
Origin: Multiple (PO + Dev + QA via 6-case matrix Rule 3)

---

## Feature: Reasoning Parts on the Wire (F5 native transport) 〔NEW — 取代舊 "Reasoning Channel Isolation"〕

### Context

Reasoning 傳輸改走 **AI SDK v6 UIMessage Stream Protocol native `reasoning-*` parts**（`reasoning-start` / `reasoning-delta` / `reasoning-end`,見 SSE stream-protocol 文件）。Provider reasoning delta **原樣直通**(無 buffer、無句界切分、無 `\n` join)。邊界:**one provider reasoning block = one part**;multi-round tool loop 自然產生多 parts,無特判。舊自訂 transient SSE channel / `ReasoningSegmenter` / D39 雙層防護 / 5 個 reasoning dev flags 全移除(`FORCE_LLM_FAIL` 保留)。

> 設計註記:AI SDK 於 `finish-step` 會 reset active reasoning part map、**允許 part id 跨 step 重用**。故 backend 必須讓每個 reasoning part 的 `id` 在**一個 turn 內唯一**(非 step-local),否則前端 React key / timer ref 會跨輪撞號(見 S-parts-01 wire 斷言;根因 Dev D18)。

---

### Rule: One provider reasoning block = one native part（id turn-unique）

#### S-parts-01: 一個 reasoning block 對應一組 start/delta*/end,multi-round 產生多 parts
> 驗證 A1 — part 邊界與順序;並斷言 reasoning part id 在 turn 內唯一(防 finish-step id 重用撞號)

- **Given** Alice 送出會觸發單一 reasoning block 的短 prompt「What is a 10-K?」(reasoning-on)
- **When** Wire 觀察該 turn
- **Then** 恰好一組 `reasoning-start` … `reasoning-delta`* … `reasoning-end`(同一 `id`)
- **And** 換送 D25 canonical prompt(reason → `list_sec_sections` → reason → `get_section` → reason → answer)時,wire 上出現 3 組獨立 `reasoning-*` 序列,依到達順序與 tool part 交錯,且 3 個 reasoning part 的 `id` **彼此不同**(turn-unique)

Category: Illustrative
Origin: PO A1 + Dev D18 (id-reuse wire contract)

---

### Rule: Provider reasoning deltas 原樣直通

#### S-parts-02: raw passthrough,不 buffer 不切句
> 驗證 A2 — 移除 segmenter / hold-and-flush / `\n` join 後,delta 逐字直通

- **Given** Provider 對某 reasoning block 送出被切在字中間的 delta（如 `"…Apple's fiscal 2024 10-K li"`)且兩段 summary 段落間含 `\n\n`
- **When** Wire 觀察該 block 的 `reasoning-delta` 序列
- **Then** 字中間的片段原樣出現在 delta,不被扣到句界/字界才送;`\n\n` 逐字保留(不 strip、不跨空行 join);無 char-count soft-emit re-chunk

Category: Illustrative
Origin: Dev R1 (A2) + QA R1

---

### Rule: Abort 靜默關閉 reasoning 串流

#### S-parts-03: user abort 中途 reasoning → 無 reasoning-end
> 驗證 A3 — abort wire 靜默(fetch abort 已斷 socket,不補 close frame)

- **Given** Bob 送出 D25 prompt,round-2 reasoning 正在串流
- **When** 他 click Stop
- **Then** 該 reasoning part 最後一個 frame 是 `reasoning-delta`(**無** `reasoning-end`),stream 關閉;backend 不寫任何最終 SSE frame

Category: Illustrative
Origin: PO A3

#### S-parts-04: error 先補 reasoning-end 再 error;tool 中出錯不偽造 end
> 驗證 A4 — error path 與 abort 的不對稱

- **Given** Provider 在某 turn 出錯於 `<phase>`
- **When** Backend 發出終止序列
- **Then** frame 順序符合 `<expected_order>`

| phase | expected_order |
|---|---|
| round-1 reasoning 串流中出錯 | `reasoning-end`(補完該 part) → `error` → `finish` |
| `get_section` 執行中出錯(無開著的 reasoning part) | (不偽造 `reasoning-end`) `error` → `finish` |

Category: Illustrative (table-driven)
Origin: PO A4 + Dev Q-A4 guard

---

### Rule: 無 reasoning 的 turn 不發 reasoning parts

#### S-parts-05: reasoning-off / 空 reasoning → zero parts → zero chips
> 驗證 A5

- **Given** Dan 送出 D25 prompt 於 `<mode>`
- **When** Turn 完成
- **Then** wire 上 `reasoning-*` part 數 = 0;UI 0 顆 chip;tool 事件與 answer text 照常

| mode | notes |
|---|---|
| reasoning-off config | reasoning 能力關閉 |
| reasoning-on 但 model 該 turn 沒 emit reasoning | 短 prompt 邊角 |

Category: Illustrative (table-driven)
Origin: PO A5

---

### Journey Scenarios

#### J-parts-01: D25 wire trace — reasoning 與 tool native parts 依序交錯
> 驗證 F5 端到端 wire 契約:one block = one part、順序、id turn-unique

- **Given** Eve 送出 D25 canonical prompt 走 reasoning-on Gemini
- **When** 完整擷取該 turn 的 SSE part 序列
- **Then** 序列為 reasoning part₁ → tool(`list_sec_sections`) → reasoning part₂ → tool(`get_section`) → reasoning part₃ → answer text,依到達順序;每個 reasoning part 有唯一 `id`、完整 start/delta*/end(除非該 turn 被 abort);無殘留的自訂 transient reasoning event

Category: Journey
Origin: Multiple (A1/A2/A4)

---

## Feature: Reasoning Chips (F6′) 〔NEW — 取代舊 "Reasoning Indicator Lifecycle" chip 半邊〕

### Context

每個 reasoning part 渲染成一顆 **`ReasoningChip`**,依 part 到達順序與 tool cards 交錯。串流時全文顯示、`max-height` ~3–4 行、釘底自動捲;該輪 reasoning 結束後收合為 `Thought for Xs`(X = **client 量測**,在該輪**第一個 tool-start 凍結**;唯一允許的非 derived 前端狀態是 chip 計時 ref)。**只有當前輪 chip 展開**,前輪隨 loop 前進自然收合(Claude.ai 式)。點開可讀全文,user 的展開/收合選擇會覆蓋 derivation。Abort 半 chip 收合保留、header 標 `Stopped — thought for Xs`。Chips **不跨 reload**;串流中 reload 丟掉整個進行中的 turn。舊 19-state hook/component/測試群 + frozen `STOPPED` indicator + `abortedMessages` 追蹤整批刪除。

> 設計註記(非 scenario,但須成立):① streaming chip body 以 raw `white-space: pre-wrap` 渲染(非 markdown),避免半截 markdown 逐 delta re-parse 抖動(Dev D13/QA12);② 計時器為 wall-clock delta(`performance.now()`/`Date.now()`)而非 interval tick-counter,使背景分頁 throttle 不污染 X(QA6);③ chip 展開/收合 override 為 `Map<partId,bool>`,在 derivation 前先讀、每 turn/step 清空,且**不**餵入 placeholder/stall 的「有無活元素」判斷(QA1);④ CJK/長 token chip 需 `overflow-wrap: anywhere` 使釘底 scrollHeight 數學成立(QA4)。

---

### Rule: 串流中的 chip 顯示即時全文並釘底

#### S-chip-01: streaming chip 全文顯示、max-height 3–4 行、釘底自動捲
> 驗證 B1

- **Given** Grace 送出 D25 prompt,round-1 reasoning 開始串流且文字超過 4 行
- **When** reasoning delta 持續抵達
- **Then** chip 展開,內容裁到 ~3–4 行高、最新文字釘在底部可見、較舊文字捲出視野;若該輪 reasoning 只有 2 短行則全文顯示、無捲軸

Category: Illustrative
Origin: PO B1

#### S-chip-02: 600 字無終止符 CJK reasoning 在釘底視窗內正確 wrap
> 驗證 B1 + QA4 — segmenter 移除後,raw CJK passthrough 的呈現(取代舊 S-stream-09)

- **Given** Provider emit 一段 ~600 個繁中字元、無 `。！？\n` 的 reasoning(Gemini 繁中常態)
- **When** 該段串流進 chip 的 3–4 行釘底視窗
- **Then** 內容以字元換行、維持釘底(最新字在底部),不撐破寬度;收合後點開可讀完整 600 字

Category: Illustrative
Origin: QA R1 (QA4) + Dev R2

---

### Rule: 該輪 reasoning 結束後 chip 收合為「Thought for Xs」

#### S-chip-03: 收合為 Thought for Xs,X 在第一個 tool-start 凍結,多輪各自獨立
> 驗證 B2 + 決策 2(計時語意)。X 由 client 量測。

- **Given** Hank 送出 D25 prompt
- **When** round-1 reasoning 結束(其後接 `list_sec_sections`)
- **Then** chip₁ 收合為 `Thought for Xs`,X = 從該輪 reasoning 起算到**該輪第一個 tool-start**凍結的秒數(不含其後 tool 執行時間)
- **And** 三輪跑完後,transcript 有三顆各自時長獨立的收合 chip(如 `Thought for 2s` / `Thought for 3s` / `Thought for 1s`);因 part id turn-unique,三顆時長不互相污染

Category: Illustrative
Origin: PO B2 + 決策 2 + Dev D18

---

### Rule: 只有當前輪 chip 展開,前輪隨 loop 前進收合

#### S-chip-04: round-2 開始時 round-1 chip 已收合;同時只有一顆 chip 展開
> 驗證 B5 + 決策 1(chip 收合模型)

- **Given** Ivan 送出 D25 prompt,round-1 reasoning 串流中(chip₁ 展開)
- **When** round-1 結束、round-2 reasoning 開始串流
- **Then** chip₁ 已收合為 `Thought for Xs`、chip₂ 展開串流;任一時刻最多一顆 chip 處於展開/串流態
- **And** 當最終 answer text 開始串流時,不存在任何仍在「思考」串流的 chip(無 chip 與答案文字並存 spinning,cf. QA14)

Category: Illustrative
Origin: PO B5 + 決策 1 + QA14

---

### Rule: 收合的 chip 可點開,且 user 的展開選擇覆蓋 derivation

#### S-chip-05: 串流中點開前一顆 chip 讀取,該 chip 保持展開不被 derivation 收回
> 驗證 B3 + QA1(user override beats derivation)

- **Given** Judy 的 D25 turn 中,chip₁ 已收合(`Thought for 3s`)、chip₂ 正在串流
- **When** 她點開收合的 chip₁ 讀取內容,此時 chip₂ 仍在收到 delta
- **Then** chip₁ 保持展開(user override 勝過「只有當前輪展開」的 derivation),chip₂ 的後續 delta 不會把 chip₁ 收回;再次點擊 chip₁ 收合,選擇持續有效
- **And** 若她改為手動收合仍在串流的 chip₂,placeholder 不因此出現(chip₂ 對 stall/placeholder 判斷仍算「當前活躍串流元素」)

Category: Illustrative
Origin: QA1 + Dev R2 (override composition)

---

### Rule: reasoning parts 以 chips 呈現、與 tool cards 依到達順序交錯

#### S-chip-06: 三輪 D25 依序 chip→tool→chip→tool→chip→answer;重疊時 tool card 排在開著的 chip 下方
> 驗證 B4 / B8 + 決策 4(重疊排版)。取代舊「reasoning 過濾出 transcript」為 chip renderer。

- **Given** Kevin 送出 D25 prompt(reasoning-on Gemini)
- **When** 完整看完 streaming
- **Then** transcript 依到達順序呈現 chip₁ → `list_sec_sections` card → chip₂ → `get_section` card → chip₃ → answer text
- **And** 當 Gemini 在 chip₁ 的 `reasoning-end` 之前就送 `list_sec_sections` 的 tool 參數(part 時間重疊)時,tool card 渲染在**仍開著的 chip₁ 下方**(維持 part-start 順序),不強制立即收合 chip₁

Category: Illustrative
Origin: PO B4/B8 + 決策 4 + Dev/QA D6/QA15

---

### Rule: Abort 保留收合的半 chip,並與完成區分

#### S-chip-07: abort 半 chip 收合保留,header 標 Stopped;error(reasoning-end 有到)維持乾淨 header
> 驗證 B6 + 決策 6(aborted header 區分)

- **Given** Olivia 送 D25,chip₁ 已完成(`Thought for 3s`),round-2 reasoning 串流中
- **When** 她在 round-2 中途 click Stop(A3:無 `reasoning-end`)
- **Then** chip₂ 收合並保留其半截文字,header 顯示 `Stopped — thought for Xs`(與完成的 `Thought for Xs` 視覺可區分);chip₁ 維持 `Thought for 3s`;畫面上無元素消失
- **And** 對照:若該 round 是 error 而非 abort(A4:`reasoning-end` 已送達),則其 chip 收合為**乾淨**的 `Thought for Xs` + error 面,**不**標 `Stopped`

Category: Illustrative
Origin: PO B6 + 決策 6 + Dev (error-header 三態)

---

### Rule: 空 reasoning block 不留 ghost chip

#### S-chip-08: zero-delta part 完全不出 chip;已畫出的 whitespace chip 保留不事後移除
> 驗證 決策 3(空 block 處理)+ D5/D15/QA9a/QA17

- **Given** Provider 對某 turn `<empty_case>`
- **When** 該 part 渲染
- **Then** 結果為 `<expected>`

| empty_case | expected |
|---|---|
| reasoning-start 之後緊接 reasoning-end、zero delta | **不出任何 chip**;不觸發 placeholder churn;transcript 無 `Thought for 0s` ghost |
| 已串出 chip、但內容結果全是 whitespace deltas | chip 保留、正常收合為 header(不做事後移除,避免 flash-then-vanish) |

Category: Illustrative (table-driven)
Origin: 決策 3 + QA (streamed-whitespace 界線)

---

### Rule: Chips 不跨 reload;串流中 reload 丟掉進行中的 turn

#### S-chip-09: 完成後 reload → transcript 僅剩 answer text + tool cards,chips 消失
> 驗證 B7 / D12(v1 明確接受;非 replay)

- **Given** Grace 完成一個 reasoning-on D25 turn(transcript 有數顆收合 chip)
- **When** 她 reload 頁面,frontend 從 backend 重新 hydrate messages
- **Then** rehydrated transcript 僅含 answer text + tool cards;所有 reasoning chips(串流中與收合的)都不出現

Category: Illustrative
Origin: PO B7 + Dev D12

#### S-chip-10: 串流中 reload → 進行中的 assistant turn 整個消失,user prompt 留著
> 驗證 決策 9(串流中 reload)+ QA19。與 S-chip-09 相反的斷言(進行中 → answer text 也消失)

- **Given** Judy 在某 D25 turn round-2、部分 answer text 已串出時 reload
- **When** 頁面重載、history rehydrate
- **Then** 該進行中的 assistant turn 整個不見(無部分 answer text、無 chips、無 error 面);她自己的 user prompt 仍在
- **And** 不出現「半截答案看起來像完整」的狀態

Category: Illustrative
Origin: 決策 9 + QA19

---

### Journey Scenarios

#### J-chip-01: 收合 chips 黃金路徑(DEV-106 §9 acceptance)
> 驗證 submit → placeholder → chip 串流 → 收合 → tool → 第二顆 chip → answer 的完整可見序列

- **Given** Victor 開新 chat,送 D25 canonical prompt(reasoning-on,不 abort 不 error)
- **When** 完整觀察 streaming 後再 reload
- **Then** 依序:submit 後出 placeholder「Thinking…」→ chip₁ 串流(全文釘底)→ 收合為 `Thought for Xs` → `list_sec_sections` / `get_section` tool cards 照常 → 第二顆 chip 串流後收合 → 一旦 reply text 開始、placeholder 消失
- **And** 完成後 transcript 的 reasoning 僅以收合 chips 呈現、每顆可點開讀全文;reload 後 chips 全數消失

Category: Journey
Origin: Multiple (§9 golden path)

---

## Feature: Activity Placeholder & Stall Degradation (F6′) 〔NEW〕

### Context

`ActivityIndicator` 縮為 **placeholder**,只補「畫面無活元素」的空窗:(a) submit 後到首個串流內容(對應 `useChat` `status === 'submitted'`),(b) chip 收合後到 reply text 開始。**tool 執行中不出現**(tool card 是活元素);chip 串流中不出現。State 數 3:Hidden / Waiting(`Thinking…`)/ Waiting+降級(`Still working…`),永不含 reasoning 文字。全域單一 **10s stall 碼表**,任何 stream part 抵達即歸零;降級文案兩消費者:placeholder 與 streaming chip header。文案(英文,i18n 前慣例):`Thinking…` / `Still working…` / `Thought for Xs`。決策 8:placeholder + chip header 加最小 `aria-live="polite"`。

> 設計註記:① `useChat.status` 實為 4 值 `submitted | streaming | ready | error`。**〔已 superseded,人工測試後修正〕** 舊規則「placeholder 空窗 (a) 應 key 在 `status === 'submitted'`,非『streaming 且 parts 為空』(Dev D17)」已不符 shipped 實作:實際規則是 `status === 'submitted'` **或**(`status === 'streaming'` 且該 turn 尚未 render 出任何可見內容,見 `frontend/src/lib/reasoning-chips.ts` 的 `turnHasRenderableContent`,實作於 `frontend/src/hooks/useDeadAirPlaceholder.ts` 的 `windowA`)。修正原因:人工測試量測到 wire 的 `start` frame 到第一個可 render 的 reasoning delta 之間最長可達 ~8s 的 dead air(`reasoning-start` 可先於其首個 delta 抵達數秒),且完全 zero-delta 的 reasoning block 永遠不會 render 出任何東西——僅 key 在 `submitted` 會讓這兩種情況在 `streaming` 期間空等、畫面卻已無 placeholder 覆蓋。此修正方向已獲兩輪獨立 spec-conformance review 確認;正式 scenario 補充與 Linear 決策記錄更新另立 DEV-108 處理,此處僅作事實更正。② 碼表為 wall-clock(`Date.now() - lastPartArrival`,render 時求值),reset 由 part-arrival 事件驅動(背景分頁 fetch stream 不被 throttle);③ 因 `experimental_throttle` 可能合併更新,所有計時斷言用 tolerance band,非逐 frame 精確(Dev D20);④ 決策 5:chip→tool card 空檔不出 placeholder,長 tool 期間無降級面。

---

### Rule: placeholder 只補 dead-air 空窗

#### S-place-01: submit 後(status submitted)出 placeholder;tool 與 chip 串流中不出
> 驗證 C1 + D17(4 值 status)

- **Given** Alice 送出 D25 prompt,backend 首個 chunk 有 ~1.5s 延遲
- **When** 這段延遲期間(`status === 'submitted'`)
- **Then** placeholder 顯示「Thinking…」
- **And** 之後 `get_section` tool card 執行中、以及任一 chip 正在串流時,placeholder 皆隱藏

Category: Illustrative
Origin: PO C1 + Dev D17

#### S-place-02: chip 收合到 reply text 開始之間出 placeholder
> 驗證 C1 window (b) + 決策 5(chip→tool 空檔不出)

- **Given** Bob 的 D25 turn,最後一顆 reasoning chip 剛收合、final answer text 尚未開始
- **When** 這段空窗
- **Then** placeholder 顯示「Thinking…」直到 reply text 首字出現;而 chip 收合後緊接的若是 **tool card**(非 reply text),則該空檔不出 placeholder(tool card 負責回饋)

Category: Illustrative
Origin: PO C1 + 決策 5

---

### Rule: placeholder 三態,永不含 reasoning 文字

#### S-place-03: Hidden / Waiting / Waiting+降級,無 reasoning token
> 驗證 C2 / C5

- **Given** Carol 處於一個 waiting 空窗
- **When** 碼表 `<elapsed>`
- **Then** placeholder 顯示 `<copy>`,且不含任何 reasoning 文字

| elapsed | copy |
|---|---|
| < 10s | `Thinking…` |
| ≥ 10s | `Still working…` |

Category: Illustrative (table-driven)
Origin: PO C2 + C5

---

### Rule: 全域單一 10s stall 碼表,任何 stream part 歸零

#### S-place-04: 10s 無 part → 降級;8s 有 delta → 歸零不降級
> 驗證 C3。10s 預設值另由 stall hook 單元測試(fake timers)驗;此處驗 wiring(以 tolerance band 斷言)

- **Given** David 送出 query
- **When** `<event>`
- **Then** `<result>`

| event | result |
|---|---|
| submit 後連續 10s 無任何 stream part | 碼表越過 10s → 降級文案出現 |
| reasoning delta 於第 8s 抵達 | 碼表歸零,不出降級 |
| tool 事件於第 9s 抵達 | 碼表歸零,不出降級 |

Category: Illustrative (table-driven)
Origin: PO C3

#### S-place-05: 碼表在新 turn 起點歸零;aborted turn 的 stale 值不滲入下一 turn
> 驗證 C3 reset 邊界(Dev D8)+ 長 tool 後 reasoning-start 先歸零再 derive(QA18)

- **Given** Eve 的 turn stall 到碼表讀 14s,她 abort 後**立即**送新 message
- **When** 新 turn 的 placeholder 在首個 `reasoning-start` 前渲染
- **Then** 新 turn placeholder 顯示「Thinking…」(非「Still working…」);stale 14s 不滲入(P2 no-contamination)
- **And** 另一情形:某輪 `get_section` 執行 12s(碼表越過 10s、無活動面)後,round-2 `reasoning-start` 抵達;chip₂ 開場 header 顯示「Thinking…」而非「Still working…」(reset 在 header derive 之前發生)

Category: Illustrative
Origin: Dev D8 + QA18

---

### Rule: 降級文案顯示於當前活躍的那個面

#### S-place-06: 空窗時降級落在 placeholder;chip 串流時降級落在 chip header
> 驗證 C4 + 決策 5(長 tool 無降級面)

- **Given** Frank 的 turn 於 `<surface_state>` 時 stall ≥ 10s
- **When** 碼表越過 10s
- **Then** 降級文案「Still working…」出現於 `<surface>`

| surface_state | surface |
|---|---|
| dead-air 空窗(placeholder 顯示中) | placeholder 文字換「Still working…」 |
| 某 chip 正在串流 | 該 streaming chip 的 header 顯示「Still working…」 |
| 長 `get_section` 執行中(placeholder 隱藏、無 chip 串流) | **無降級面**(tool card 負責回饋;決策 5 接受) |

Category: Illustrative (table-driven)
Origin: PO C4 + 決策 5 + Dev D9

---

### Rule: reasoning 進度以 aria-live 播報給 assistive tech（決策 8）

#### S-place-07: screen reader 收到 placeholder + chip header 的 aria-live 播報
> 驗證 決策 8 — 補回被刪的 LiveStatusAnnouncer 的最小替代(QA10)

- **Given** Grace 用 screen reader 送出 D25 prompt
- **When** placeholder 出現、chip 串流、chip 收合為 `Thought for Xs`
- **Then** aria-live="polite" 區把高層級狀態播報出去(如「Thinking…」/「Thought for 3s」),reasoning 逐字內容不逐句灌入 polite queue

Category: Illustrative
Origin: QA10 + 決策 8

---

### Journey Scenarios

#### J-place-01: placeholder + stall 生命週期(慢 backend)
> 驗證 dead-air placeholder → 10s 降級 → 首內容恢復的完整序列

- **Given** Hank 送出 query,backend 首 chunk 刻意慢(> 10s)
- **When** 他觀察等待期
- **Then** 依序:placeholder「Thinking…」→ 越過 10s 轉「Still working…」→ 首個 reasoning delta 抵達,placeholder 讓位給串流中的 chip、碼表歸零

Category: Journey
Origin: Multiple (C1/C3/C4)

---

## Feature: Preserved Chat Behaviors under the Reasoning Refactor 〔PRESERVED — verify-unchanged vs main〕

### Context

DEV-106 是 refactor:下列 tool / abort / error / regenerate / text-streaming 行為必須**維持不變**。驗證方式為對照 main 行為(no regression),並涵蓋 refactor 新引入的 guard(如 abort→ready flip 期間的 Stop 競態、靜默 stall 的手動 Stop 逃生)。

---

### Rule: tool cards 照常渲染與顯示進度（P1）

#### S-pres-01: D25 tool cards running→done,與 chips 交錯
> 驗證 P1 — refactor 不改變工具回饋

- **Given** Ivan 送出 D25 prompt
- **When** agent 走 multi-tool flow
- **Then** `list_sec_sections` / `get_section` cards 各自渲染並顯示 running→done 進度,依到達順序與 reasoning chips 交錯

Category: Illustrative (verify-unchanged)
Origin: P1

---

### Rule: abort 後畫面安定並可乾淨重送（P2）

#### S-pres-02: abort→重送乾淨;composer/Stop 在 streaming 期禁用;abort→ready 競態不誤殺重送;靜默 stall 可手動 Stop
> 驗證 P2 + QA2(送出 guard)+ QA7/D19(double-Stop 競態)+ 決策 7(靜默 stall 逃生)

- **Given** Judy 送出 D25 prompt 進入串流
- **When** 她在中途 click Stop,然後立即送出新 query
- **Then** 畫面安定(半 chip 收合為 `Stopped — thought for Xs`、任何 partial answer text 保留),新 query 完整串流、無前一 turn 污染
- **And** `status ∈ {submitted, streaming}` 期間 composer 與送出被禁用(concurrent turn 不能經 UI 觸發)
- **And** 若她在 abort→ready 過渡的極短窗內連按第二次 Stop,該次 Stop **不**中止新的重送 turn(D19 guard)
- **And** 靜默 stall(連續 N 秒無 part、`status` 仍 streaming)時,Stop 按鈕維持可見,click 後狀態安定回 `ready`(決策 7 的手動逃生)

Category: Illustrative (verify-unchanged + new guards)
Origin: P2 + QA2 + Dev D19 + 決策 7

---

### Rule: stream error 給明確回饋而非畫面掛死（P3）

#### S-pres-03: 可偵測 error → error 面 + retry;chips 收合後 tool 出錯的版面
> 驗證 P3 + QA5a(可偵測 disconnect 由 SDK 處理)+ QA13(error-after-chips 版面)

- **Given** Karen 處於一個 reasoning-on turn
- **When** 發生 `<error_case>`
- **Then** `<expected>`

| error_case | expected |
|---|---|
| 可偵測 stream error(RST / stream error frame) | `status='error'`;error 面出現、附 retry;click retry 觸發 regenerate 並成功重串 |
| chip₁/chip₂ 已收合、`get_section` 執行中 backend error→finish(A4:無偽造 reasoning-end) | error 面渲染(於失敗 tool card 處 / 收合 chips 下方);已收合的 chips 仍可點開;errored-but-completed 的 chip 維持乾淨 `Thought for Xs`(非 `Stopped`) |

Category: Illustrative (table-driven,verify-unchanged + new layout)
Origin: P3 + QA5a + QA13 + Dev(error-header)

---

### Rule: regenerate 行為與首次生成一致（P4）

#### S-pres-04: regenerate 走 placeholder→chips→answer;舊 chips 先清、展開態不殘留
> 驗證 P4 + D14(regenerate resets)+ QA16(展開 override 不跨 turn)

- **Given** Larry 完成一個 D25 turn(三顆收合 chip),並手動點開其中 round-2 那顆
- **When** 他 click Regenerate
- **Then** 舊的三顆 chip 在重生前清除,新 turn 依序 placeholder → chips → answer(如首次生成)
- **And** 新 turn 剛串流的 chip **不**繼承上一個 turn 那顆被手動展開的狀態(override map 已按 turn 清空,即使 part id 被重用)

Category: Illustrative (verify-unchanged + new reset)
Origin: P4 + Dev D14 + QA16

---

### Rule: reply text 仍逐字串流（P5）

#### S-pres-05: answer text 逐 token 渲染
> 驗證 P5

- **Given** Mary 送出任一 reasoning-on turn 並進到 answer 階段
- **When** reply text 開始
- **Then** 文字逐 token 出現、非一次整塊

Category: Illustrative (verify-unchanged)
Origin: P5

---

### Journey Scenarios

#### J-pres-01: abort 中段然後乾淨重送
> 驗證 abort 半 chip 保留 + 畫面安定 + 重送無污染(碼表歸零)

- **Given** Wendy 開新 turn,送 D25 → 等到第二顆 chip 串流中 → click Stop
- **When** 她看到半 chip 收合為 `Stopped — thought for Xs`、畫面安定後,立即送新 message 並跑完
- **Then** prior bubble 保留收合 chips(含 `Stopped` 那顆);新 bubble 完整跑完 placeholder→chips→answer;stall 碼表歸零、無「Still working…」滲入;兩 bubbles 並存

Category: Journey
Origin: Multiple (P2 + 決策 6/7 + D8)

---

## Feature: Langfuse Reasoning Persistence 〔F7 — 未在 DEV-106 變更;反映 pre-F7 per-call 設計〕

> ⚠ **本整塊 Feature 維持 2026-05 的 per-LLM-call 設計,DEV-106 不動。** F7 已裁決降級為 **trace-level 全文**(移除 `CallbackHandler._runs` 私有 API 依賴),該改版屬 **DEV-107**,artifacts 修訂屬 **DEV-108**。下列 S-trace-* scenarios 於 DEV-107/108 重寫前**暫留原樣**,僅供追溯;請勿據此驗 DEV-106 終態。

### Context

每個 chat_model LLM call 的 reasoning content 寫到 Langfuse `metadata.reasoning`（per LLM call 一塊）；schema 統一（empty `""` / sentinel `<unsupported>` / 500KB truncate marker）；judge model `gpt-5-mini` 不掛 `ReasoningTraceCallback`（避免 rubric 洩漏）；live UX 跟 trace 內容可接受 divergence。

---

### Rule: 每個 chat_model span 都有 `metadata.reasoning` key〔pre-F7〕

#### S-trace-01: Reasoning-on multi-call turn 對應 N 個獨立 chat_model spans
> 驗證 F7〔pre-F7 per-call〕— per-LLM-call reasoning 不 cumulative

- **Given** Xiang 跑 D25 canonical prompt 走 reasoning-on Gemini，產出 3 個 LLM calls
- **When** Turn 完成、Langfuse SDK flush 後（驗證時 polling with retry+backoff 5 秒）
- **Then** Trace tree 含 1 個 `agent.run` parent span + 3 個 `chat_model.invoke` child spans
- **And** 每個 chat_model span 有自己的 `metadata.reasoning`，內容只含該 call 的 reasoning（不 cumulative）
- **And** Parent `agent.run` span 自己**不**含 `metadata.reasoning`

Category: Illustrative
Origin: PO Rule 5 + Dev R1 (C5.1) + D29 + D37

#### S-trace-02: 各種 reasoning content 狀態的 schema 一致性〔pre-F7〕
> 驗證 D29 / §6.2 — completed path 5 種狀態對應 5 種 value 形式(DEV-107 將收斂為單一 key + 值內 marker)

- **Given** Yara 跑 turn 對應 `<scenario>`（completed path）
- **When** Turn 完成、Langfuse trace 檢查
- **Then** chat_model span `metadata.reasoning` value 為 `<expected_value>`

| scenario | expected_value |
|---|---|
| reasoning-on，model emit reasoning content | 實際 reasoning 文字（多 reasoning blocks join） |
| reasoning-on，但 short prompt 沒 emit reasoning | `""` empty string |
| reasoning-off mode（reasoning-capable provider） | `""` empty string |
| Non-reasoning-capable provider | `"<unsupported>"` sentinel |
| Reasoning content > 500KB | 前 500KB + `... [truncated, original {N} bytes]` marker |

Category: Illustrative (table-driven)
Origin: Multiple (Dev + QA + D29)

#### S-trace-03: Operator query 涵蓋 4 種語意篩選〔pre-F7〕
> 驗證 D29 operator query contract

- **Given** Langfuse 內已存有混合各種 reasoning state 的 traces
- **When** Operator 跑 query
- **Then** 每種 query 涵蓋對應的 spans（`IS NOT NULL` / `length > 0` / `!= '<unsupported>'` / `LIKE '%[truncated%'`）

Category: Illustrative (operational verification)
Origin: D29

#### S-trace-04: Judge gpt-5-mini calls 不出現 metadata.reasoning〔pre-F7〕
> 驗證 D30 — judge invocation path 顯式 exclude `ReasoningTraceCallback`

- **Given** Eval pipeline 跑一批 D25 prompts 並用 `gpt-5-mini` judge 打分
- **When** Eval 完成、檢查 Langfuse production trace
- **Then** agent traces 含 `metadata.reasoning`；judge 對應 chat_model spans **沒有** `metadata.reasoning`
- **And** Judge reasoning 由 Braintrust 處理（memory `feedback_braintrust_host_only.md`）

Category: Illustrative
Origin: QA R1 (C5.5/C5.6) + Dev R2 + D30

#### S-trace-05 / S-trace-06 / S-trace-07 / S-trace-08 / S-trace-09〔pre-F7,原樣保留〕
> stream-loop finalize (D34)、abort cleanup + `reasoning_tail_aborted` (D35)、UX↔trace divergence (D36)、multi-tab trace isolation (D37)、content_blocks graceful degrade (D38)。**這些依賴 segmenter / per-call callback,DEV-107 重寫後將大幅簡化或移除;此處不重述細節,見 archive `2026-07-24-pre-dev106-ephemeral-indicator/bdd-scenarios.md`。**

Category: Illustrative
Origin: 2026-05 原版

---

### Journey Scenarios

#### J-trace-01: Multi-call 完整 trace tree 對齊 SEC 範例〔pre-F7〕
> 驗證 reasoning-on multi-call turn 在 Langfuse 上產生 §6.3 規格的 trace tree(DEV-107 後改 trace-level 全文)

- **Given** Erin 跑 D25 canonical prompt 走 reasoning-on Gemini default agent
- **When** Turn 完成 + Langfuse SDK flush
- **Then** Trace tree 結構符合 §6.3 範例;每個 chat_model span `metadata.reasoning` 符合 §6.2 schema

Category: Journey
Origin: Multiple (PO §6 + D29/D30/D37)

---

# 註記

## ~~Cross-Feature Risk Mitigation / S-cross-01~~ — 移除(POC 已 ship)

原 R1 content_blocks + R5 callback ordering POC ship gate(S-cross-01)已於 branch 完成並驗證,不再是待驗 scenario。

## Scope 移除

- **F7 Langfuse trace-level 改版** → DEV-107;artifacts(含上方 S-trace-* 重寫)→ DEV-108。本次不改。
- **Provider swap 矩陣 (F1/F2/F3)** 本身 → PR0/PR1a;本次僅把其 reasoning-wire 斷言改 native parts。
- **Chips 跨 reload 回放**(history 不含 reasoning parts)→ defer until evidence。
- **靜默 stall 自動偵測 idle-watchdog** → defer(決策 7);手動 Stop 為逃生。
- **Cross-tab reasoning sync / stream resume** → out(QA11;chips + stall 為 per-tab)。
- **i18n**(chip/placeholder 文案先英文)。
- **(per D24)** Mid-session provider switch + signature contamination:user 不能 runtime 切 model,cross-provider session resume 非 user flow。

## 設計註記(實作指令,非 scenario,但須成立)

- **Reasoning part `id` turn-unique**:SDK 於 `finish-step` reset active reasoning map、允許 id 跨 step 重用;backend 須讓每 reasoning part id 在 turn 內唯一(否則 React key / timer ref 撞號)。Wire 斷言在 S-parts-01 / J-parts-01。(根因 Dev D18 / D4)
- **計時器 = wall-clock delta**(`performance.now()`/`Date.now()`),非 interval tick-counter,使背景分頁 throttle 不污染「Thought for Xs」與 stall 碼表。(QA6)
- **streaming chip body = raw `white-space: pre-wrap`**(非 markdown),避免半截 markdown 逐 delta re-parse 抖動;收合的 chip 可安全 markdown 渲染。(Dev D13 / QA12)
- **chip expand/collapse override = `Map<partId,bool>`**,derivation 前先讀、每 turn/step 清空,且**不**餵入 placeholder/stall 的「有無活元素」判斷。(QA1)
- **CJK/長 token chip** 需 `overflow-wrap: anywhere` 使釘底 scrollHeight 數學成立。(QA4)
- **計時斷言用 tolerance band**,非逐 frame 精確,因 `experimental_throttle` 可能合併更新。(Dev D20)
- **`useChat.status` 為 4 值** `submitted | streaming | ready | error`;placeholder 空窗 (a) key 在 `submitted`。(Dev D17)

## Demoted to unit / hook test（不寫 BDD scenario）

- **10s stall 預設值** → stall hook 單元測試(fake timers);**恰好 1 個** ChatPanel 整合測試(mock 小 threshold + MSW 真實時間)驗 wiring(F6 裁決)。
- **timer-ref 以 turn-unique id keying、survive re-render/interleave 重整**(Dev D4/D18)→ hook test(user-visible 症狀由 S-chip-03 duration 正確性把關,但需 turn-unique-id 前提)。
- **stall reset 於任何 part 含 reasoning-start、reset-before-derive 排序**(Dev D10/QA18)→ hook test(症狀於 S-place-05)。
- **背景分頁 throttle 下 wall-clock timer 正確**(QA6)→ hook test。
- **regenerate override map 清空**(QA16)→ hook test(症狀於 S-pres-04)。
- **codepoint 安全的 delta concat**;僅 grapheme-cluster 一 frame 自癒抖動(QA3,Context7 已證 wire codepoint-safe)→ documented cosmetic note,不寫 scenario。
- **sub-frame round auto-batch**(QA9b)→ known-behavior note。
- **layout jitter / 4→1 行收合 scroll 穩定**(Dev D16 / QA8)→ layout directive(reserve header 高度 / anchor scroll)+ manual visual。
- (2026-05 原保留)C1.6 callback wiring parity、C2.4 historical replay re-emit、C5.2 always-write key、C6.1 <16ms React batching、C6.9 segmenter buffer overflow、CR.7 reasoning-id collision。

## Verification method 對應（詳見 verification-plan.md）

- **Wire / deterministic**(S-parts-01..05, J-parts-01;S-stream-03/04/05/08, J-stream-01;S-trace-* pre-F7):curl / SSE part 擷取 / API / Langfuse trace inspection。
- **Frontend / browser**(S-chip-01..10, J-chip-01;S-place-01..07, J-place-01;S-pres-01/03/04/05, J-pres-01;S-stream-07):Playwright + video record(`frontend/tests/e2e/`,commit 進 repo 為 repeatable CI guardrail)。Browser-Use CLI 僅用於 agent-driven 一次性探索。
- **Cross-cutting**(S-pres-02:wire + browser + integration;S-place-04/05:兩層,以 tolerance band 斷言)。
