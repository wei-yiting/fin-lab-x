# BDD Scenarios — Multi-provider Streaming Reasoning (DEV-108)

## Meta

- Generated: 2026-08-04 (DEV-108)
- Discovery Method: Three Amigos（condensed single-session；覆蓋範圍為 human ratified 之 DEV-108 裁決，discovery 聚焦規則抽取與矛盾/缺口偵測）
- Normative sources（唯一行為規格來源，clean-room）:
  - DEV-108 normative-sources 包（DEV-105 issue body + 🔧 裁決 comments、DEV-106 issue body + 裁決、DEV-107 issue body 摘要）
  - `docs/adr/0008-reasoning-as-collapsed-transcript-chips.md`
  - `docs/adr/0009-trace-level-reasoning-transcript-on-self-owned-root-span.md`
  - `CONTEXT.md`（glossary SSOT）、`docs/design-envelope.md`
  - AI SDK v6 UIMessage Stream Protocol wire 格式（Context7 `/vercel/ai` 查證）
- Clean-room 原則：本文件所有 scenario 僅派生自上列 normative sources，未讀任何 implementation code——規格驗 code，而非 code 驗 code。
- Known coverage gap（明文接受）：provider browser 主線僅 3 案（Gemini reasoning-on / Gemini reasoning-off / GPT reasoning-on），**不驗 Anthropic**；因此「單次 LLM call 內 interleaved reasoning → 多顆 Reasoning chip」路徑無真實驗證，多 chip 行為僅由 tool loop（多次 LLM call）驅動覆蓋。
- 詞彙依 `CONTEXT.md` glossary：`Chat turn`、`Stream stall`、`Activity indicator`、`Reasoning chip`、`Reasoning stream`、`Reasoning transcript`、`Tool progress`、`Session`。

---

## Feature: Reasoning on the wire（F5 — AI SDK native parts）

### Context

Reasoning stream 以 AI SDK v6 UIMessage Stream Protocol 的 native `reasoning-start` / `reasoning-delta` / `reasoning-end` parts 傳輸；provider delta 原樣直通（無 buffer、無句界切分）。One provider reasoning block = one part = 前端一顆 Reasoning chip。

### Rule: Reasoning stream 以 native `reasoning-*` parts 傳輸，one provider reasoning block = one part

#### S-wire-01: 單一 reasoning block 產生一組完整的 reasoning parts
> 驗證 wire 上出現成對的 `reasoning-start`/`reasoning-end` 與中間的 `reasoning-delta`，且非自訂 SSE channel。

- **Given** backend 以 Gemini reasoning-on 設定運行，一個新 Session
- **When** 送出一個會觸發 reasoning 但不觸發 tool 的簡單提問（如 "Briefly explain what a 10-K filing is"）
- **Then** SSE stream 依序含 `{"type":"reasoning-start","id":...}` → 一至多個 `{"type":"reasoning-delta","id":...,"delta":...}` → `{"type":"reasoning-end","id":...}`，三者共用同一 `id`
- **And** stream 中不存在任何自訂 transient reasoning channel 事件

Category: Illustrative
Origin: PO

#### S-wire-02: tool loop 多個 reasoning blocks 的 part `id` 在 Chat turn 內唯一
> 驗證跨 LLM call 的 reasoning part id turn-unique（AI SDK 於 `finish-step` 會重用 id，規格要求不得重複）。

- **Given** backend 以 Gemini reasoning-on 設定運行
- **When** 送出 canonical multi-tool prompt（觸發 reason → tool → reason 的多段 loop）
- **Then** wire 上出現 ≥2 組 `reasoning-start/…/reasoning-end`
- **And** 各組的 `id` 互不相同（同一 Chat turn 內唯一）

Category: Illustrative
Origin: Dev

### Rule: abort 時 wire 靜默關閉，不補發 `reasoning-end`

#### S-wire-03: mid-Reasoning-stream abort 後 wire 無補償事件
> 驗證 abort 不在 wire 上補 `reasoning-end`；tail 寫入責任完全屬 Reasoning transcript（F7）。

- **Given** 一個 Chat turn 正在 Reasoning stream 中（已收到 `reasoning-start` 與部分 `reasoning-delta`）
- **When** client 中斷該串流（abort）
- **Then** 截至中斷為止的 capture 中，該開啟中的 reasoning part 沒有對應的 `reasoning-end`，也沒有任何補償性 finish 事件

Category: Illustrative
Origin: Dev

### Rule: stream error 時先補 `reasoning-end`，再送 `error` 與 `finish`

#### S-wire-04: reasoning 進行中發生 LLM error 的事件順序
> 驗證 error 路徑會先關閉開啟中的 reasoning part，讓前端得以收合 chip 再顯示錯誤。

- **Given** backend 設定為會在 LLM call 失敗（`FORCE_LLM_FAIL` 保留原地）
- **When** 送出提問且 stream 進入 error 路徑
- **Then** 若 error 發生時有開啟中的 reasoning part，wire 順序為 `reasoning-end` → `error` → `finish`

Category: Illustrative
Origin: QA

### Rule: reasoning off 時 wire 不含任何 `reasoning-*` parts

#### S-wire-05: Gemini reasoning-off 的 wire 乾淨
> 驗證三態中的 off：關閉 reasoning 後 wire 與既有 text/tool 傳輸完全一致、無 reasoning parts。

- **Given** backend 以 Gemini reasoning-off 設定運行
- **When** 送出 canonical multi-tool prompt
- **Then** wire 上不出現任何 `reasoning-start`/`reasoning-delta`/`reasoning-end` part
- **And** text 與 tool 相關 parts 照常出現，Chat turn 正常完成

Category: Illustrative
Origin: PO

---

## Feature: Reasoning chips（F6′ — 收合式 transcript chips）

### Context

每個 reasoning segment 渲染為一顆可收合的 Reasoning chip：streaming 時展開即時滾動，結束後收合為 `Thought for Xs` header，永久留在 transcript 內可點開回看；與 tool cards 依 part 到達順序交錯（ADR-0008）。

### Rule: streaming 中的 Reasoning chip 即時顯示全文（釘底自動捲、`pre-wrap`）

#### S-chip-01: 首個 reasoning delta 後 chip 出現並隨 delta 增長
> 驗證 streaming chip 是活的 DOM 元素：出現、內容持續增長、樣式為純文字。

- **Given** 一個新 Session，Gemini reasoning-on
- **When** 送出會觸發 reasoning 的提問，Reasoning stream 開始
- **Then** transcript 中出現一顆展開中的 Reasoning chip，內文隨 delta 持續增長（`white-space: pre-wrap` 純文字，非 markdown）
- **And** chip header 具 `aria-live="polite"`

Category: Illustrative
Origin: Multiple

### Rule: reasoning segment 結束後 chip 收合為 `Thought for Xs`，點開可讀全文；X 於該輪第一個 tool-start 凍結

#### S-chip-02: segment 結束時 chip 收合且內容可回讀
> 驗證收合瞬間的行為與收合後的永久可讀性。

- **Given** 一顆 Reasoning chip 正在 streaming
- **When** 該 reasoning segment 結束（`reasoning-end` 抵達）
- **Then** chip 收合為 `Thought for Xs` header（X 為秒數）
- **And** 點開該 chip 可讀到該 segment 的完整 reasoning 全文

Category: Illustrative
Origin: PO

#### S-chip-03: `Thought for Xs` 的 X 不含 tool 執行時間
> 驗證計時停點：X 在該輪第一個 tool-start 凍結（client 端 wall-clock 量測）。

- **Given** 一個會觸發 tool 呼叫的 Chat turn，第一段 reasoning 歷時約 T 秒後接 tool 執行（tool 執行顯著耗時）
- **When** 該 reasoning segment 的 chip 收合
- **Then** header 顯示的 X 落在 T 的 tolerance band 內，不包含其後 tool 執行時間

Category: Illustrative
Origin: Dev

### Rule: 只有當前輪（tail）chip 展開，前輪 chip 隨下一個 part 收合

#### S-chip-04: 第二個 reasoning segment 開始時前一顆 chip 收合
> 驗證 Claude.ai 式 tail-only 展開：任一時刻至多一顆 chip 展開。

- **Given** 一個 multi-tool Chat turn 已完成第一段 reasoning（chip 1 已收合）並執行完 tool
- **When** 第二段 reasoning 的 part 開始 streaming
- **Then** 只有 chip 2 處於展開 streaming 狀態；chip 1 維持收合
- **And** Chat turn 結束後兩顆 chip 皆為收合態，各自可獨立點開

Category: Illustrative
Origin: QA

### Rule: chips 與 tool cards 依 part 到達順序交錯；tool 參數抵達即關閉該輪 reasoning part（chip 於 tool-start 收合）

#### S-chip-05: 多輪 tool loop 的 chips 與 tool cards 順序交錯
> 驗證 agent 工作節奏（想→查→再想→回答）在 transcript 中依序可讀。

- **Given** Gemini reasoning-on，一個新 Session
- **When** 送出 canonical multi-tool prompt 並等 Chat turn 完成
- **Then** transcript 中 Reasoning chips 與 tool cards 依 part 到達順序交錯排列（chip → tool card(s) → chip → … → reply text）
- **And** tool 參數抵達即代表該輪 reasoning block 結束——mapper 關閉 reasoning part，chip 於 tool-start 收合，tool card 排在已收合的 chip 下方（抵達序不變）。（⚖️ 2026-08-04 DEV-109 追加裁決，取代原「重疊時 tool card 排在開著的 chip 下方」條件式斷言——原裁決假設重疊為偶發，實測在預設 provider 上為每輪必然，成本假設失效）

Category: Illustrative
Origin: Multiple

### Rule: zero-delta reasoning block 完全不出 chip；已畫出的 chip 保留

#### S-chip-06: zero-delta block suppress 與 whitespace chip 保留
> 驗證空 reasoning block 的邊界：無 delta 不畫 chip；有內容（即使 whitespace）的 chip 不事後移除。

- **Given** 一條 stream 內含一組無任何 `reasoning-delta` 的 `reasoning-start`+`reasoning-end`，以及一組僅含 whitespace delta 的 reasoning part（以 edge-case mock 注入）
- **When** stream 播放完畢
- **Then** zero-delta 的 block 不產生任何 chip（該空窗由 Activity indicator 持續蓋住）
- **And** whitespace 內容的 chip 正常出現並收合，不被事後移除

Category: Illustrative
Origin: QA

### Rule: reasoning off 時 transcript 無任何 Reasoning chip

#### S-chip-07: Gemini reasoning-off 的畫面行為（browser 主線案 2/3）
> 驗證 off 態下 UI 完全退回既有行為：無 chip、Activity indicator 與 reply 照常。

- **Given** backend 以 Gemini reasoning-off 設定運行，一個新 Session
- **When** 送出 canonical multi-tool prompt 並等 Chat turn 完成
- **Then** 整個流程無任何 Reasoning chip 出現；Activity indicator（`Thinking…`）與 tool cards、reply text 串流照常
- **And** transcript 最終僅含 tool cards 與答案文字

Category: Illustrative
Origin: PO

### Rule: abort 的半顆 chip 收合保留，header 為 `Stopped — thought for Xs`

#### S-chip-08: mid-Reasoning-stream abort 的半顆 chip
> 驗證 abort 時 chip 的終態：收合保留、header 與完成態可區分、X 於 Stop 當下取樣。

- **Given** 一顆 Reasoning chip 正在 streaming
- **When** 使用者按 Stop 中斷該 Chat turn
- **Then** 該半顆 chip 收合保留於 transcript，header 為 `Stopped — thought for Xs`（非 `Thought for Xs`）
- **And** 點開可讀到中斷前已收到的 partial reasoning 全文

Category: Illustrative
Origin: Multiple

### Rule: chips 不跨 reload；串流中 reload 丟棄整個進行中的 assistant turn

#### S-chip-09: 串流中 reload 的丟棄語意（現況：無 history hydration）
> 驗證第一版明文接受的 reload 行為：進行中 turn 全部丟棄，且現況 reload = 全新 chat。

- **Given** 一個 Chat turn 正在串流（chip 或 text 進行中）
- **When** 使用者 reload 頁面
- **Then** 進行中的 assistant turn 完全丟棄（無 partial text、無 chips、無 error 面）
- **And** 現況下（app 無 history hydration）reload 後為全新空白 chat——「chips 不跨 reload」自然成立

Category: Illustrative
Origin: Dev

---

## Feature: Activity indicator 與 Stream stall（F6′ — placeholder）

### Context

Activity indicator 縮為純 placeholder：只在畫面無活元素的空窗出現（submit → 首個 renderable content、chip 收合 → reply text、tool round 全數完成 → 下一個內容 ⚖️ 2026-08-04 DEV-109 追加），永不包含 reasoning 文字；Stream stall（10 秒無任何 stream part）時當前 live surface 換降級文案。文案（英文）：`Thinking…` / `Still working…`。

### Rule: Activity indicator 由 submit 起持續顯示，直到第一個 renderable content 出現

#### S-place-01: submit 後立即出現 placeholder，首個內容抵達即消失
> 驗證修正後的 window (a) 語意：`submitted` 或 `streaming`-且-尚無-renderable-content 都由 placeholder 蓋住（首個 reasoning delta 可晚 ~8s）。

- **Given** 一個新 Session，Gemini reasoning-on
- **When** 送出提問
- **Then** Activity indicator（`Thinking…`）立即出現，且在第一個可渲染內容（chip 首個 delta 或 text）出現前持續顯示
- **And** 首個內容出現後 placeholder 消失；placeholder 具 `aria-live="polite"` 且不含任何 reasoning 文字

Category: Illustrative
Origin: Multiple

### Rule: 無活元素的空窗顯示 placeholder（300ms grace）；chip 收合 → tool card 空窗不顯示

#### S-place-02: 收合後空窗的 placeholder 分流
> 驗證 `PLACEHOLDER_GRACE_MS = 300ms` 的行為語意：chip→tool 空檔不閃現、真正的 dead air 會被蓋住。
> ⚖️ 2026-08-04 DEV-109 追加裁決：(1) 因 mapper 於 tool-start 關閉 reasoning part，最後一顆 chip 的
> `reasoning-end` 與 `text-start` 同批抵達——「chip 收合 → reply text」空窗結構上 ≈0ms，
> 該空窗不出現 placeholder 是 grace 設計下的**正確**行為；(2) 新增空窗：tool round 全數完成
> （所有 tool parts 皆 terminal）→ 下一個內容抵達前的 dead air 由 placeholder 覆蓋（同 300ms grace）。

- **Given** 一個 multi-tool Chat turn 進行中
- **When** 某輪 tool round 全數完成（所有 tool cards 呈結果態）、下一個內容（下輪 reasoning / reply text）尚未抵達
- **Then** placeholder 在該空窗出現（相對空窗起點可有 ≤300ms grace 延遲），下一個內容抵達即消失
- **And** 在「chip 收合 → tool card」的空檔中，placeholder 不出現
- **And** 任何時刻 placeholder 不與 streaming 中的 chip 或執行中的 tool card 同時出現

Category: Illustrative
Origin: Dev

### Rule: tool 執行中不出現 Activity indicator

#### S-place-03: tool 執行期間畫面有活元素、無 placeholder
> 驗證 placeholder 只補「無活元素」空窗——tool card / Tool progress 顯示中即為活元素。

- **Given** 一個 Chat turn 正在執行 tool（tool card 與 Tool progress 顯示中）
- **When** tool 執行持續進行
- **Then** Activity indicator 不出現

Category: Illustrative
Origin: PO

### Rule: Stream stall（10s 無任何 stream part）時當前 live surface 換降級文案，part 抵達即恢復

#### S-place-04: Stream stall 降級與恢復
> 驗證全域單一 10 秒碼表的行為：降級文案出現在當前 live surface，任何 part 抵達即歸零恢復。（10s 預設值已由 DEV-106 單元測試鎖定；此為整合層唯一 1 case。）

- **Given** 一條 stream 進入 10 秒以上無任何 stream part 的靜默（以 edge-case delayed-stream mock 製造）
- **When** Stream stall 觸發
- **Then** 當下 live surface 換降級文案：Activity indicator 顯示 `Still working…`；若當下是 streaming 中的 Reasoning chip，則其 header 換降級文案
- **And** 下一個 stream part 抵達後，文案恢復正常狀態

Category: Illustrative
Origin: QA

### Rule: 靜默 stall 無自動偵測（defer），保留手動 Stop 逃生

#### S-place-05: 長時間靜默下手動 Stop 逃生可用
> 驗證 defer 決策的另一半：無 idle-watchdog，但使用者隨時可 Stop 並得到正常 abort 行為。

- **Given** 一條 stream 長時間靜默（降級文案已顯示）
- **When** 使用者按 Stop
- **Then** Chat turn 正常 abort：畫面立即安定，若有半顆 chip 則依 abort 語意收合保留，可重新送出

Category: Illustrative
Origin: QA

---

## Feature: Reasoning transcript（F7 — trace-level 全文）

### Context

Chat turn 結束時，累積的全部 reasoning 段落一次寫入該 turn 的 root trace（self-owned root span，ADR-0009）：單一 `reasoning` key、值內 `=== segment N ===` per-segment 分隔（segment = reasoning part = 前端一顆 chip）。斷言語意平台無關（DEV-114 將遷 Braintrust）；平台特定的讀回呼叫僅存在於 verification plan 的 Steps。

### Rule: Chat turn 結束時 Reasoning transcript 以單一 key + in-value segment markers 寫入 root trace

#### S-trace-01: 正常對話的 root trace 帶完整 Reasoning transcript
> 驗證 F7 核心：全文一次寫入、per-segment 分隔、segment 數與前端 chips 一對一。

- **Given** Gemini reasoning-on，完成一個 canonical multi-tool Chat turn（前端出現 N 顆 Reasoning chips）
- **When** 讀回該 Chat turn 的 root trace
- **Then** root trace 帶有 Reasoning transcript：單一 `reasoning` key，值內含 `=== segment 1 ===` … `=== segment N ===` 分隔的完整 reasoning 全文
- **And** segment 數 = N（與前端 chips 一對一），且各 segment 內容與對應 chip 點開所見一致

Category: Illustrative
Origin: PO

### Rule: mid-segment abort 時 reasoning tail 仍寫入並標記；turn 層級 abort 由 status 單獨記錄

#### S-trace-02: abort Chat turn 的 transcript tail 與標記
> 驗證 abort 語意的雙層記錄：`=== aborted ===` 僅標 mid-segment 中斷（transcript 完整性），turn 層級 abort 屬 `status: "aborted"`；兩者同一次寫入。

- **Given** 一個 Chat turn 在 Reasoning stream 進行中（mid-segment）被 abort
- **When** 讀回該 Chat turn 的 root trace
- **Then** Reasoning transcript 含中斷前已收到的 reasoning tail，且該值以 `=== aborted ===` 標記收尾
- **And** trace 另帶 turn 層級的 `status: "aborted"` 記錄（與 transcript 同一次寫入）

Category: Illustrative
Origin: Multiple

### Rule: always-write-key 契約——off 寫 `""`、unsupported 寫 `"<unsupported>"`（unsupported 同時 wire 無 reasoning parts）

#### S-trace-03: off / unsupported 的值語意（deterministic，含 unsupported wire 斷言）
> 驗證三態中 off 與 unsupported 的持久化契約；unsupported 不寫 browser scenario，僅此一條 deterministic（human ratified）。

- **Given** backend 分別以 reasoning off 與 reasoning unsupported 設定運行
- **When** 各完成一個 Chat turn 並讀回 root trace
- **Then** off：Reasoning transcript key 存在且值為 `""`
- **And** unsupported：Reasoning transcript key 存在且值為 `"<unsupported>"`，且該 Chat turn 的 wire 上無任何 `reasoning-*` parts

Category: Illustrative
Origin: Dev

---

## Feature: Preserved behaviors 回歸（B — 重構不變項）

### Context

本次為 refactor + 呈現改版；以下既有行為必須保持不變（primary rule：existing behavior must not change）。

### Rule: tool 呼叫照常顯示 tool cards 與 Tool progress

#### S-pres-01: tool cards 與進度回饋與重構前一致
> 驗證重構不改變使用者熟悉的工具回饋。

- **Given** 一個新 Session
- **When** 送出會觸發 tool 呼叫的提問
- **Then** 每個 tool 呼叫照常顯示 tool card，執行中有 Tool progress 更新，完成後 card 呈現結果狀態

Category: Illustrative
Origin: PO

### Rule: abort 後畫面立即安定且可正常重送

#### S-pres-02: Stop 之後畫面安定、重送成功
> 驗證中斷操作乾淨可預期：無殘留活元素，下一次送出行為正常。

- **Given** 一個 Chat turn 串流中被使用者 Stop
- **When** 畫面安定後使用者重新送出新提問
- **Then** abort 當下畫面立即安定（無殘留 placeholder/spinner；半顆 chip 依 abort 語意收合保留）
- **And** 新的 Chat turn 完整正常執行（placeholder → 內容 → 完成）

Category: Illustrative
Origin: Multiple

### Rule: stream error 時給出明確錯誤回饋而非畫面掛死（legible failure）

#### S-pres-03: LLM/連線錯誤的明確回饋
> 驗證 error 路徑的使用者體驗：結構化錯誤呈現，使用者可決定重試。

- **Given** backend 設定為 LLM call 會失敗（`FORCE_LLM_FAIL`）
- **When** 送出提問且 stream 進入 error
- **Then** 畫面出現明確的錯誤回饋（結構化、可理解），不掛死、不留下永久轉圈的活元素
- **And** 使用者可再次送出提問

Category: Illustrative
Origin: QA

### Rule: regenerate 的行為與首次生成一致

#### S-pres-04: regenerate 重演完整流程（含 placeholder 與 chips）
> 驗證操作心智模型統一：重新生成不是簡化版流程。

- **Given** 一個已完成的 Chat turn（含 Reasoning chips 與答案）
- **When** 使用者對該回覆執行 regenerate
- **Then** 重新生成的流程與首次一致：placeholder 出現 → Reasoning chip streaming/收合 →（如有）tool cards → reply text 串流

Category: Illustrative
Origin: PO

### Rule: reply text 逐字串流

#### S-pres-05: 答案文字隨 stream 增長
> 驗證 reply text 仍為 streaming 呈現，而非完成後一次貼出。（上游 provider buffer-then-flush 造成的 text burst 屬上游行為，不視為 bug。）

- **Given** 一個 Chat turn 進入答案生成階段
- **When** reply text 開始串流
- **Then** 答案文字在畫面上隨 stream 分多次增長至完整

Category: Illustrative
Origin: PO

---

## Feature: 周邊隔離（D — deterministic 邊界）

### Context

跨 Session、跨 Chat turn 與非 streaming path 的隔離性；全部以 backend deterministic script 驗證，不進 browser（human ratified）。

### Rule: 不同 Session 的串流與 Reasoning transcript 互不污染

#### S-iso-01: 雙 Session 並發互不干擾
> 驗證 multi-tab（= 多 Session）情境下 wire 與 trace 的隔離。

- **Given** 兩個不同 Session 同時各發起一個 Chat turn（並發串流，≤3 concurrent users 屬 envelope §1 範圍內）
- **When** 兩條 stream 各自完成
- **Then** 各 Session 的 wire 只含自己 Chat turn 的 parts（reasoning part id 與內容無交叉）
- **And** 兩個 Chat turn 各自的 root trace 的 Reasoning transcript 僅含自己 Session 的 reasoning 段落

Category: Illustrative
Origin: Dev

### Rule: abort 後下一個 Chat turn 無殘留污染

#### S-iso-02: abort 的累積狀態不外洩到下一個 Chat turn
> 驗證 accumulator 生命週期以 Chat turn 為界：abort turn 的 tail 不混入後續 turn。

- **Given** 同一 Session 中，Chat turn A 於 mid-segment abort
- **When** 接著在同一 Session 完成 Chat turn B
- **Then** Chat turn B 的 wire 僅含 B 自己的 parts
- **And** B 的 root trace Reasoning transcript 僅含 B 的 segments，無 `=== aborted ===` 標記、無 A 的殘留內容

Category: Illustrative
Origin: QA

### Rule: non-streaming invoke path 不寫 Reasoning transcript

#### S-iso-03: invoke path 無 reasoning 持久化
> 驗證裁決：invoke（非 streaming）path 的 reasoning 持久化已移除（無事件流、無 consumer）——不得要求其寫 transcript。

- **Given** backend 以 reasoning-on 設定運行
- **When** 經 non-streaming invoke path 完成一次請求
- **Then** 請求正常回應
- **And** 該次執行不產生 Reasoning transcript 寫入（對應 trace 上無 reasoning 全文記錄）

Category: Illustrative
Origin: Dev

---

## Journey Scenarios

（Journeys 橫跨全部 Features：F5 wire、F6′ chips/placeholder、F7 transcript、preserved behaviors。）

#### J-01: Gemini reasoning-on 的 canonical multi-tool 全流程（browser 主線案 1/3）
> 覆蓋完整 agent loop：submit → placeholder → chip → tools → 第二顆 chip → 答案 → 事後 wire 與 trace 全鏈驗證。

- **Given** backend 以 Gemini reasoning-on 設定運行，一個新 Session
- **When** 使用者送出 canonical multi-tool prompt（Apple 10-K FY2024 vs FY2023 Item 1A 比較）並等 Chat turn 完成
- **Then** 全程依序可見：Activity indicator（`Thinking…`）→ 第一顆 Reasoning chip streaming（全文釘底）→ 收合 `Thought for Xs` → tool cards 依序執行 → 第二顆 Reasoning chip → reply text 開始後 placeholder 消失 → 答案完整
- **And** 完成後 transcript 中 reasoning 僅以收合 chips 呈現、每顆可點開回看；wire 上有多組 turn-unique 的 native reasoning parts；root trace 的 Reasoning transcript segment 數與 chips 數一致

Category: Journey
Origin: Multiple

#### J-02: GPT (OpenAI) reasoning-on 的 canonical 全流程（browser 主線案 3/3）
> 覆蓋 provider matrix 的第二個 reasoning-on provider：行為語意須與 J-01 一致。

- **Given** backend 以 GPT (OpenAI) reasoning-on 設定運行，一個新 Session
- **When** 使用者送出 canonical multi-tool prompt 並等 Chat turn 完成
- **Then** 行為與 J-01 語意一致：placeholder → Reasoning chip(s) streaming/收合 → tool cards 交錯 → reply text → chips 永久可點開；root trace 帶完整 Reasoning transcript

Category: Journey
Origin: Multiple

#### J-03: abort 與恢復 journey（半顆 chip → 重送 → trace 雙面驗證）
> 覆蓋中斷主線：mid-segment Stop 的 UI 終態、恢復能力、與 abort trace 語意的端到端一致性。

- **Given** Gemini reasoning-on，一個 Chat turn 的 Reasoning stream 進行中
- **When** 使用者按 Stop，確認畫面安定後重新送出一個簡單提問並等其完成
- **Then** 被中斷的 Chat turn：半顆 chip 收合保留、header `Stopped — thought for Xs`、點開可讀 partial 全文；其 root trace 的 Reasoning transcript 以 `=== aborted ===` 收尾且帶 `status: "aborted"`
- **And** 重送的 Chat turn 完整正常，其 trace 乾淨無前一 turn 殘留

Category: Journey
Origin: Multiple

---

## Open Questions — 已全數裁決（2026-08-04 human 裁決）

> 起草時發現的 8 個規格縫隙，已由 human 逐條裁決如下；保留全文供 DEV-109 執行時參照。

1. **F7 scenario 數 vs unsupported deterministic 條目** — ⚖️ **裁決：維持合併**。S-trace-03 單條 deterministic 同時涵蓋 off `""`、unsupported `"<unsupported>"`、unsupported wire 無 parts（unsupported 環境切換成本高，切一次驗兩面）。
2. **unsupported 態的觸發方式** — ⚖️ **裁決：維持 `[BIND-AT-RUN]`**。DEV-109 執行時查 config 綁定；若現行 admin 設定配不出 unsupported 組合，該事實本身記為 finding（「三態保留」裁決缺乏可執行驗證路徑）。
3. **S-wire-03 的可觀察性**（abort capture 斷言力道有限）— ⚖️ **裁決：保留**。接受弱斷言；其反向價值是能抓到「backend 在 abort 前錯誤提早關閉 part」（capture 中出現不該有的 `reasoning-end`），成本趨近零。
4. **chip 與 tool card 時間重疊**（S-chip-05 的 And 句）— ⚖️ **裁決：接受 opportunistic 條件式斷言**。重疊發生時驗順序維持 part 序；未發生記 not-exercised 不算 fail。若 DEV-109 全程 not-exercised，屆時再議是否補 route mock（defer until evidence）。
5. **非主線 browser scenarios 的預設 provider** — ⚖️ **裁決：照假設**。用 repo 現行 admin 預設的 reasoning-on 設定，執行時 bind。
6. **`FORCE_LLM_FAIL` 能否於 mid-Reasoning-stream 觸發** — ⚖️ **裁決：維持 `[BIND-AT-RUN]`**。若失敗時點無法落在 reasoning part 開啟期間，S-wire-04 的順序斷言由 DEV-109 判定（改 route-level mock 或記 finding）。
7. **500KB cap（截尾留頭 + `[truncated…]`）** — ⚖️ **裁決：不寫**（先前 F7 收斂裁決已明文排除 500KB truncation 斷言；視為 DEV-107 單元層已鎖）。
8. **同一 Session 並發的 busy-guard（HTTP 409）** — ⚖️ **裁決：不補**。尊重 ratified 的 B/D 清單邊界；409 錯誤面屬 DEV-71 範圍。列為已知未覆蓋（known non-coverage），非遺漏。

---

## DEV-109 執行期追加裁決（2026-08-04 human 裁決,round 2）

BDD 重跑期間由 human 手動測試發現、經 wire/code 交叉驗證後上呈裁決:

9. **Deferred reasoning-end（統一 root cause）** — ⚖️ **裁決:選 A**。mapper 收到 `tool_call_chunk`
   即關閉該輪 reasoning part(比照 text block),取代 DEV-106 §B 的 keep-open 允許——原裁決假設
   overlap 為偶發 edge case,實測在預設 provider(GPT-5-mini)上為每輪必然,成本假設失效。
   效果:chip 於 tool-start 收合(與 `Thought for Xs` 凍結時點一致)、tool 執行中 stall 降級文案
   不再落在 chip header、抵達序不變。上述裁決 4(opportunistic 條件式斷言)隨之作廢。
   完整分析:`temp/finding-deferred-reasoning-end.md`。
10. **tool-complete → next content 的 dead air** — ⚖️ **裁決:補 placeholder**(window C)。
    所有 tool parts 皆 terminal 且下一個內容未抵達的空窗由 Activity indicator 覆蓋,同 300ms grace。
    「chip 收合 → reply text」空窗因裁決 9 結構上 ≈0ms,不出現 placeholder 為正確行為
    (S-place-02 斷言同步改寫,正向驗證改用 deterministic MSW fixture `tool-deadair-then-text`)。

11. **Turn-level Interrupted 標記** — ⚖️ **裁決:採 (a) 通用版**(2026-08-04 round 4)。
    使用者 Stop 一律在被中斷的 turn 下方留下明確的 `Interrupted` 標記列(Claude Code 式),
    不論當下是否已有 chip(`Stopped — thought for Xs`)或 tool card(`Aborted`)承載 abort 態。
    背景:DEV-106 曾裁決刪除舊 frozen `STOPPED` indicator,abort 態改由元素承載——但 Stop 落在
    placeholder 或 reply text streaming 時無承載元素,transcript 事後無任何 abort 痕跡,
    被截斷的答案讀起來像完整回答(legible-failure 缺口)。regenerate 該 turn 時標記隨之清除。

另,執行期發現並修復一個 implementation bug(非 spec 變更):client abort 落在 stream generator
懸停於 `yield` 的瞬間時,abort 以 `GeneratorExit`(而非 `asyncio.CancelledError`)送達,
原 cleanup 只掛在後者上,導致 reasoning tail + `status: "aborted"` 靜默漏寫(時序 race)。
已補 `except GeneratorExit` 分支 + 單元測試;S-trace-02 / J-03 語意不變。
