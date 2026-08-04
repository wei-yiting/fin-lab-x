# Verification Plan — Multi-provider Streaming Reasoning (DEV-108)

## Meta

- Scenarios Reference: `artifacts/current/bdd-scenarios.md`
- Generated: 2026-08-04 (DEV-108)
- Normative sources：同 `bdd-scenarios.md` Meta（DEV-108 normative-sources 包、ADR-0006、ADR-0007、`CONTEXT.md`、`docs/design-envelope.md`、AI SDK v6 UIMessage Stream Protocol）
- Clean-room 原則：本計畫未讀任何 implementation code；所有需要 code/DOM 事實的位置以 `[BIND-AT-RUN: …]` 標記，由 DEV-109 執行時對照綁定——**綁不上本身就是 finding**。
- Known coverage gap：不驗 Anthropic → 單次 LLM call 內 interleaved reasoning 的多 chip 路徑無真實驗證（多 chip 僅由 tool loop 驅動）。
- 工具分流（human ratified）：時序敏感條目 → **Playwright**（semantic anchor + `[BIND-AT-RUN]` selector）；其餘 browser 行為 → **Browser-Use CLI**（自然語言任務 + 明確斷言點）；wire/API → **curl/jq script**；Reasoning transcript → **Langfuse SDK 讀回 script**（Expected 為平台無關語意，僅 Steps 綁 Langfuse——DEV-114 遷 Braintrust 時只換 Steps）。
- 環境事實（執行時再確認）：backend SSE `POST http://localhost:8000/api/v1/chat/stream`；frontend dev server `http://localhost:5173`；canonical prompt = `Compare Apple's 10-K fiscal year 2024 vs 2023 Item 1A risk factors and categorize changes (added / strengthened / removed)`。
- Provider/reasoning 三態切換為 admin 在 codebase 設定 `[BIND-AT-RUN: config 檔位置與 Gemini on / Gemini off / GPT on / unsupported 的設定值]`。
- MSW / route mock 僅用於 error/edge case（S-chip-06、S-place-04、S-place-05）；其餘 browser 條目一律打真 backend。

---

## Automated Verification

### Deterministic（curl/jq、script、Langfuse SDK 讀回）

#### S-wire-01: 單一 reasoning block 產生一組完整的 reasoning parts

- **Method**: curl + jq（SSE capture）
- **Steps**:
  1. 設定 backend 為 Gemini reasoning-on `[BIND-AT-RUN: config 切換]`，啟動 backend
  2. `curl -N -X POST http://localhost:8000/api/v1/chat/stream -H 'Content-Type: application/json' -d '<payload：session + message "Briefly explain what a 10-K filing is">' [BIND-AT-RUN: request payload schema] | tee /tmp/s-wire-01.sse`
  3. 以 jq/grep 萃取 `data:` 行中 `type` 以 `reasoning-` 開頭的事件序列
- **Expected**: 依序出現 `reasoning-start` → ≥1 個 `reasoning-delta`（帶 `delta` 字串）→ `reasoning-end`，三者 `id` 相同；capture 中無任何非 AI SDK 協定的自訂 reasoning 事件型別。

#### S-wire-02: tool loop 多個 reasoning blocks 的 part `id` 在 Chat turn 內唯一

- **Method**: curl + jq
- **Steps**:
  1. Gemini reasoning-on，對 stream endpoint 送 canonical prompt，capture 全串流
  2. 萃取所有 `reasoning-start` 的 `id` 列表
- **Expected**: `reasoning-start` 數 ≥2；`id` 列表去重後長度不變（同一 Chat turn 內 turn-unique）；每個 `id` 的 start/delta/end 配對完整。

#### S-wire-03: mid-Reasoning-stream abort 後 wire 無補償事件

- **Method**: script（curl 於收到首個 `reasoning-delta` 後主動斷線）
- **Steps**:
  1. Gemini reasoning-on，以 script 開啟 stream（canonical prompt），偵測到第一個 `reasoning-delta` 後立即關閉連線，保留已收 capture
  2. 檢查 capture 中該開啟 part 的事件序列
- **Expected**: capture 含 `reasoning-start` 與部分 `reasoning-delta`，**無**對應 `reasoning-end`、無 error/finish 補償事件（wire 靜默關閉）。（弱斷言已裁決保留——反向可抓「abort 前錯誤提早關閉 part」；見 bdd-scenarios 裁決 3。）

#### S-wire-04: reasoning 進行中發生 LLM error 的事件順序

- **Method**: curl + jq（error 注入）
- **Steps**:
  1. 以 `FORCE_LLM_FAIL` 啟動 backend `[BIND-AT-RUN: 觸發方式與失敗時點——若無法於 reasoning part 開啟期間失敗，依 bdd-scenarios 裁決 6 由 DEV-109 判定（route-level mock 或記 finding）]`
  2. 送出提問並 capture 全串流
  3. 萃取事件型別序列
- **Expected**: 若 error 時有開啟中的 reasoning part，序列為 `reasoning-end` → `error` → `finish`（順序嚴格）；stream 正常終止而非斷線。

#### S-wire-05: Gemini reasoning-off 的 wire 乾淨

- **Method**: curl + jq
- **Steps**:
  1. 設定 Gemini reasoning-off `[BIND-AT-RUN: config 切換]`，送 canonical prompt 並 capture 全串流
  2. 檢查全部事件型別
- **Expected**: 無任何 `reasoning-start`/`reasoning-delta`/`reasoning-end`；text 與 tool parts 照常、`finish` 正常收尾。

#### S-trace-01: 正常對話的 root trace 帶完整 Reasoning transcript

- **Method**: curl（觸發）+ Langfuse SDK 讀回 script
- **Steps**:
  1. Gemini reasoning-on，經 stream endpoint 完成一個 canonical prompt Chat turn，capture wire 以計得 reasoning part 數 N
  2. Python script：以 Langfuse SDK 取回該 Chat turn 的 root trace（root span 名 `chat_turn`）`[BIND-AT-RUN: trace id 關聯方式——session/thread id 或時間窗過濾]`
  3. 讀取 root trace metadata 的 `reasoning` key
- **Expected**（平台無關語意）: 該 Chat turn 的 root trace 帶 Reasoning transcript：單一 key、值為完整 reasoning 全文、以 `=== segment 1 ===` … `=== segment N ===` 分隔；segment 數 = wire 上 reasoning part 數 N；各 segment 內容與 wire 上對應 part 的 delta 串接一致。

#### S-trace-02: abort Chat turn 的 transcript tail 與標記

- **Method**: script（mid-segment abort）+ Langfuse SDK 讀回
- **Steps**:
  1. 重用 S-wire-03 的 abort script 產生一個 mid-segment abort 的 Chat turn
  2. Langfuse SDK 取回該 turn 的 root trace，讀 `reasoning` 值與 status 相關 metadata `[BIND-AT-RUN: status key 的實際欄位]`
- **Expected**（平台無關語意）: Reasoning transcript 含中斷前 tail 且值以 `=== aborted ===` 收尾（mid-segment 中斷標記）；turn 層級 abort 由獨立的 `status: "aborted"` 記錄承載；兩者屬同一次寫入的結果。

#### S-trace-03: off / unsupported 的值語意（含 unsupported wire 斷言）

- **Method**: curl + jq + Langfuse SDK 讀回（backend deterministic script 一條，human ratified）
- **Steps**:
  1. 設定 reasoning off，完成一個 Chat turn，SDK 讀回 root trace 的 `reasoning` 值
  2. 設定 reasoning unsupported `[BIND-AT-RUN: 何種 provider/model 組合落入 unsupported——若現行設定無法產生，記為 finding]`，完成一個 Chat turn，capture wire 並 SDK 讀回
- **Expected**（平台無關語意）: off → transcript key 存在、值為 `""`；unsupported → key 存在、值為 `"<unsupported>"`，且該 turn 的 wire capture 無任何 `reasoning-*` parts（always-write-key 契約成立）。

#### S-iso-01: 雙 Session 並發互不干擾

- **Method**: script（並發 curl ×2）+ Langfuse SDK 讀回
- **Steps**:
  1. Gemini reasoning-on，以兩個不同 session id `[BIND-AT-RUN: session/thread id 欄位]` 同時開啟兩條 stream（不同 prompt 以利區分內容），各自 capture
  2. SDK 分別讀回兩個 Chat turn 的 root trace
- **Expected**: 各 capture 只含自己 Chat turn 的 parts（id 與內容無交叉）；兩份 Reasoning transcript 內容互斥、各自與自己 wire 的 reasoning 內容一致。

#### S-iso-02: abort 的累積狀態不外洩到下一個 Chat turn

- **Method**: script + Langfuse SDK 讀回
- **Steps**:
  1. 同一 session：Chat turn A 以 abort script 於 mid-segment 中斷
  2. 同一 session：Chat turn B 送簡單 reasoning 提問並完成，capture wire
  3. SDK 讀回 B 的 root trace
- **Expected**: B 的 wire 僅含 B 的 parts；B 的 Reasoning transcript 僅含 B 的 segments、無 `=== aborted ===`、無 A 的任何內容片段。

#### S-iso-03: non-streaming invoke path 不寫 Reasoning transcript

- **Method**: curl + Langfuse SDK 讀回
- **Steps**:
  1. reasoning-on 設定下，呼叫 non-streaming invoke endpoint `[BIND-AT-RUN: invoke path 的 route——若不存在對外 endpoint，改以 repo 既有 invoke 呼叫方式執行]`
  2. SDK 檢查該次執行對應的 trace
- **Expected**: 請求正常回應；該次執行不產生 Reasoning transcript 寫入（無 reasoning 全文記錄）。

---

### Browser Automation — Playwright（時序敏感條目；selector 一律 semantic anchor + `[BIND-AT-RUN]`）

> 共用前置：`npm run dev` 於 `http://localhost:5173`，backend 真實運行（僅 S-chip-06 / S-place-04 / S-place-05 允許 route-level mock）。Selector 錨點如 `[BIND-AT-RUN: Reasoning chip 容器]` 於執行時對照 DOM 綁定；綁不上即 finding。

#### S-chip-02: segment 結束時 chip 收合且內容可回讀

- **Method**: Browser automation (Playwright script)
- **Steps**:
  1. 送出會觸發 reasoning 的提問，等待 Reasoning chip `[BIND-AT-RUN: chip 元素錨點]` 進入 streaming 展開態
  2. 等待該 segment 結束，斷言 chip 收合且 header 文字符合 `/^Thought for \d+s$/`
  3. 點擊 chip，斷言展開內容為非空 reasoning 全文；附帶斷言 chip header 具 `aria-live="polite"`（承接 S-chip-01 的屬性子斷言）
- **Checkpoints**: 收合瞬間截圖；展開後截圖
- **Expected**: 收合行為即時、header 格式正確、全文可回讀。

#### S-chip-03: `Thought for Xs` 的 X 不含 tool 執行時間

- **Method**: Browser automation (Playwright script)
- **Steps**:
  1. 送出 canonical prompt；記錄第一顆 chip 出現時刻 t0 與第一個 tool card `[BIND-AT-RUN: tool card 錨點]` 出現時刻 t1
  2. 等 Chat turn 完成後讀第一顆 chip header 的 X
- **Expected**: X ≈ (t1 − t0)，tolerance band ±2s（wall-clock 量測）；X 顯著小於整個 Chat turn 耗時（證明不含 tool 執行時間）。

#### S-chip-04: 第二個 reasoning segment 開始時前一顆 chip 收合

- **Method**: Browser automation (Playwright script)
- **Steps**:
  1. 送出 canonical prompt；等第二顆 Reasoning chip 進入 streaming
  2. 於該瞬間斷言：chip 2 為展開態、chip 1 為收合態（tail-only）
  3. Chat turn 完成後斷言兩顆皆收合、各自可點開
- **Checkpoints**: chip 2 開始 streaming 當下截圖
- **Expected**: 任一時刻至多一顆 chip 展開；前輪 chip 隨下一個 part 收合。

#### S-chip-06: zero-delta block suppress 與 whitespace chip 保留

- **Method**: Browser automation (Playwright script) + route-level stream mock（edge case，MSW/route interception 已 ratified）
- **Steps**:
  1. 以 Playwright route interception 回放一條合成 UIMessage stream：`reasoning-start`+`reasoning-end`（無 delta）→ 一組僅含 whitespace delta 的 reasoning part → text
  2. 播放期間與結束後斷言 chip 數量與 placeholder 行為
- **Expected**: zero-delta block 不產生 chip（其空窗由 Activity indicator 持續蓋住）；whitespace chip 出現並正常收合、不被移除；最終 transcript 恰有 1 顆 chip。

#### S-chip-08: mid-Reasoning-stream abort 的半顆 chip

- **Method**: Browser automation (Playwright script)
- **Steps**:
  1. 送出 canonical prompt，等 Reasoning chip 進入 streaming 且內文非空
  2. 點擊 Stop `[BIND-AT-RUN: Stop 控制錨點]`
  3. 斷言 chip 收合、header 符合 `/^Stopped — thought for \d+s$/`；點開斷言 partial 全文可讀
- **Checkpoints**: Stop 後 1s 內截圖（畫面安定）
- **Expected**: 半顆 chip 收合保留、header 與完成態可區分、X 於 Stop 當下取樣。

#### S-chip-09: 串流中 reload 的丟棄語意

- **Method**: Browser automation (Playwright script)
- **Steps**:
  1. 送出 canonical prompt，等 chip 或 text 進入 streaming
  2. `page.reload()`
  3. 斷言頁面狀態
- **Expected**: reload 後無 partial text、無 chips、無 error 面；現況（無 history hydration）下為全新空白 chat。

#### S-place-02: 收合後空窗的 placeholder 分流（300ms grace）

- **Method**: Browser automation (Playwright script)
- **Steps**:
  1. 送出 canonical prompt；於「chip 收合 → tool card 出現」的空檔內持續輪詢 Activity indicator `[BIND-AT-RUN: placeholder 錨點]`——斷言全程不出現
  2. 於「最後一顆 chip 收合 → reply text 開始」的空窗內斷言 placeholder 出現（允許相對收合時點 ≤300ms + 誤差 的延遲）；附帶斷言 placeholder 具 `aria-live="polite"`（承接 S-place-01 的屬性子斷言）
- **Expected**: chip→tool 空檔 placeholder 不閃現；chip→reply text 空窗 placeholder 出現後隨 text 抵達消失。

#### S-place-04: Stream stall 降級與恢復

- **Method**: Browser automation (Playwright script) + route-level delayed-stream mock（edge case）
- **Steps**:
  1. 以 route interception 回放一條「reasoning streaming → 靜默 12s → 續傳」的合成 stream
  2. 靜默 10s 後斷言：若當下 live surface 為 placeholder → 文案為 `Still working…`；若為 streaming chip → 其 header 換降級文案
  3. 續傳 part 抵達後斷言文案恢復
- **Expected**: Stream stall 於 10s 觸發（單一全域碼表）、降級文案出現在當前 live surface、任何 part 抵達即恢復。（整合層唯一 1 case；10s 預設值由 DEV-106 單元測試鎖定。）

#### S-place-05: 長時間靜默下手動 Stop 逃生可用

- **Method**: Browser automation (Playwright script) + route-level delayed-stream mock（edge case）
- **Steps**:
  1. 回放一條進入長時間靜默的合成 stream（降級文案已顯示）
  2. 點擊 Stop，斷言 abort 終態（畫面安定、半顆 chip 依 abort 語意收合、輸入框可再送出）
- **Expected**: 靜默期間 Stop 隨時可用且 abort 行為正常（defer 自動偵測、保留逃生的裁決成立）。

#### J-03: abort 與恢復 journey

- **Method**: Browser automation (Playwright script) + Langfuse SDK 讀回 script
- **Steps**:
  1. Gemini reasoning-on 真 backend；送出 canonical prompt，於第一顆 chip streaming 中點 Stop
  2. 斷言 S-chip-08 終態；隨即重新送出簡單提問並等完成，斷言新 Chat turn 全流程正常（placeholder → 內容 → 完成）
  3. SDK 讀回兩個 Chat turn 的 root trace
- **Checkpoints**: Stop 後畫面；重送完成後 transcript 全貌
- **Expected**: 被中斷 turn 的 Reasoning transcript 以 `=== aborted ===` 收尾且帶 `status: "aborted"`；重送 turn 的 trace 乾淨無殘留；UI 端到端與 trace 端語意一致。

---

### Browser Automation — Browser-Use CLI（自然語言任務 + 明確斷言點；一律打真 backend）

#### S-chip-01: 首個 reasoning delta 後 chip 出現並隨 delta 增長

- **Method**: Browser-Use CLI
- **Steps**:
  1. 任務：「開啟 http://localhost:5173，送出提問 'Briefly explain what a 10-K filing is'。觀察回覆區域。」
  2. 斷言點：(a) 送出後不久出現一個展開中的 reasoning 區塊（Reasoning chip），內含持續增加的思考文字；(b) 文字為純文字逐行呈現（非 markdown 渲染）；(c) 思考結束後該區塊收合為 "Thought for Xs" 標題
- **Expected**: chip 作為活的 transcript 元素出現且內容隨串流增長。（`aria-live` 屬性子斷言由 S-chip-02 的 Playwright script 承接。）

#### S-chip-05: 多輪 tool loop 的 chips 與 tool cards 順序交錯

- **Method**: Browser-Use CLI
- **Steps**:
  1. 任務：「送出 canonical prompt（Apple 10-K FY2024 vs FY2023 Item 1A 比較），等整個回覆完成。」
  2. 斷言點：(a) 對話中出現 ≥2 顆收合的 reasoning 區塊與多張 tool 卡片；(b) 由上而下的順序為：reasoning → tool 卡片(們) → reasoning → … → 最終答案文字；(c) 若觀察到 tool 卡片在某顆尚未收合的 reasoning 區塊下方出現，記錄之（條件式斷言：順序仍維持抵達序）
- **Expected**: 想→查→再想→回答的節奏依 part 順序呈現於 transcript。

#### S-chip-07: Gemini reasoning-off 的畫面行為（browser 主線案 2/3）

- **Method**: Browser-Use CLI（前置：backend 切至 Gemini reasoning-off `[BIND-AT-RUN: config 切換]`）
- **Steps**:
  1. 任務：「送出 canonical prompt，觀察整個回覆過程直到完成。」
  2. 斷言點：(a) 全程未出現任何 reasoning/thinking 區塊；(b) 送出後出現 "Thinking…" 等待提示，首個內容出現後消失；(c) tool 卡片與答案文字照常串流；(d) 完成後對話中僅有 tool 卡片與答案
- **Expected**: off 態 UI 完全退回既有行為，無任何 Reasoning chip 痕跡。

#### S-place-01: submit 後立即出現 placeholder，首個內容抵達即消失

- **Method**: Browser-Use CLI
- **Steps**:
  1. 任務：「送出 canonical prompt，緊盯送出後到第一段內容出現前的畫面。」
  2. 斷言點：(a) 送出後立即出現 "Thinking…" 提示（即使首個 reasoning 內容晚數秒才到，提示持續顯示）；(b) 第一個 reasoning 文字或答案文字出現後提示消失；(c) 提示行內不含任何思考內容文字
- **Expected**: placeholder 覆蓋 submit → 首個 renderable content 的整段空窗。（`aria-live` 子斷言由 S-place-02 Playwright 承接。）

#### S-place-03: tool 執行期間無 placeholder

- **Method**: Browser-Use CLI
- **Steps**:
  1. 任務：「送出 canonical prompt，觀察 tool 卡片執行中的畫面。」
  2. 斷言點：tool 卡片顯示執行進度期間，畫面上沒有 "Thinking…"/"Still working…" 等待提示
- **Expected**: tool 執行中畫面有活元素，Activity indicator 不出現。

#### S-pres-01: tool cards 與進度回饋與重構前一致

- **Method**: Browser-Use CLI
- **Steps**:
  1. 任務：「送出 canonical prompt，觀察 tool 卡片的完整生命週期。」
  2. 斷言點：每個 tool 呼叫有對應卡片、執行中有進度更新（Tool progress）、完成後卡片呈現結果狀態
- **Expected**: 工具回饋行為不因重構改變。

#### S-pres-02: Stop 之後畫面安定、重送成功

- **Method**: Browser-Use CLI
- **Steps**:
  1. 任務：「送出 canonical prompt，回覆進行中按 Stop；畫面靜止後重新送出 'What does Item 1A cover?' 並等完成。」
  2. 斷言點：(a) Stop 後畫面快速安定，無殘留等待提示或轉圈元素；(b) 重送的回覆完整正常（等待提示 → 內容 → 完成）
- **Expected**: abort 乾淨可預期，重送與正常 Chat turn 無異。

#### S-pres-03: LLM/連線錯誤的明確回饋

- **Method**: Browser-Use CLI（前置：backend 以 `FORCE_LLM_FAIL` 啟動 `[BIND-AT-RUN: 啟動方式]`）
- **Steps**:
  1. 任務：「送出任意提問，觀察錯誤呈現。」
  2. 斷言點：(a) 出現明確的錯誤訊息區塊（非空白、非永久轉圈）；(b) 輸入框可再次送出
- **Expected**: legible failure——結構化錯誤回饋、畫面不掛死、可重試。

#### S-pres-04: regenerate 重演完整流程

- **Method**: Browser-Use CLI
- **Steps**:
  1. 任務：「送出 canonical prompt 等完成，然後對該回覆執行 regenerate `[BIND-AT-RUN: regenerate 控制項]`，觀察重新生成全程。」
  2. 斷言點：regenerate 流程依序出現：等待提示 → reasoning 區塊 streaming/收合 → tool 卡片 → 答案串流——與首次一致
- **Expected**: regenerate 與首次生成行為一致（含 placeholder 與 chips）。

#### S-pres-05: 答案文字隨 stream 增長

- **Method**: Browser-Use CLI
- **Steps**:
  1. 任務：「送出 canonical prompt，觀察最終答案文字的出現方式。」
  2. 斷言點：答案文字分多次增長至完整，而非完成後一次貼出（provider 端 burst 造成的階段性爆量可接受，不視為 fail）
- **Expected**: reply text 逐字/逐段串流呈現。

#### J-01: Gemini reasoning-on 的 canonical multi-tool 全流程（browser 主線案 1/3）

- **Method**: Browser-Use CLI + curl/jq（wire chain）+ Langfuse SDK 讀回
- **Steps**:
  1. Browser-Use 任務：「送出 canonical prompt，全程觀察並依序確認：Thinking… 提示 → 第一個 reasoning 區塊即時滾動 → 收合為 Thought for Xs → tool 卡片依序執行 → 第二個 reasoning 區塊 → 答案開始後等待提示消失 → 答案完整；完成後逐一點開每顆 reasoning 區塊確認全文可讀。」
  2. Deterministic chain：以 curl 對同一 backend 重放 canonical prompt，capture wire，斷言多組 turn-unique reasoning parts（同 S-wire-02 斷言）
  3. SDK 讀回該 Chat turn root trace，斷言 transcript segment 數 = browser 觀察到的 chips 數
- **Checkpoints**: 完成後 transcript 全貌截圖
- **Expected**: UI 流程、wire 協定、Reasoning transcript 三面一致——同一行為在三個觀察面都成立。

#### J-02: GPT (OpenAI) reasoning-on 的 canonical 全流程（browser 主線案 3/3）

- **Method**: Browser-Use CLI + Langfuse SDK 讀回（前置：backend 切至 GPT reasoning-on `[BIND-AT-RUN: config 切換]`）
- **Steps**:
  1. Browser-Use 任務同 J-01 步驟 1
  2. SDK 讀回 root trace，斷言 Reasoning transcript 存在且 segment 分隔完整
- **Expected**: 行為語意與 J-01 一致（chips、placeholder、tool cards、transcript）——證明 native parts 抽象跨 provider 成立。

---

## Manual Verification

### Manual Behavior Test

> 真正需人眼的主觀品質項（human ratified 收斂為 5 條）。每條寫明「要看什麼、什麼算過」。

#### M-01: 多輪 Reasoning transcript 閱讀節奏

- **Reason**: 「節奏一眼可讀」是主觀閱讀體驗，無法自動斷言
- **Steps**:
  1. 完成一次 canonical prompt Chat turn（Gemini reasoning-on）
  2. 不展開任何 chip，由上而下閱讀 transcript
- **要看什麼**: 想→查→再想→回答的 agent 工作節奏是否一眼可辨；reasoning 是否與答案文字乾淨分離
- **什麼算過**: 不需展開任何 Reasoning chip 就能說出這個 Chat turn 做了幾輪、每輪在做什麼；答案區無 reasoning 混入

#### M-02: chip 互動手感與釘底捲動

- **Reason**: 捲動流暢度、layout shift、動畫突兀感屬體感品質
- **Steps**:
  1. 送出 canonical prompt，全程注視 streaming 中的 Reasoning chip
  2. 完成後展開/收合各 chip 數次
- **要看什麼**: streaming 時內文是否釘底自動捲（最新文字始終可見）、max-height 約 3–4 行、無跳動；展開/收合是否順暢不突兀
- **什麼算過**: 捲動平順、無干擾閱讀的 layout shift；展開收合一步到位

#### M-03: `Thought for Xs` 秒數體感

- **Reason**: tolerance band 自動驗證已涵蓋量值，體感合理性需人判
- **Steps**:
  1. 完成含 tool 呼叫的 Chat turn，心中默數第一段思考的等待時間
  2. 對照收合 header 的 X；另做一次 mid-Reasoning abort，對照 `Stopped — thought for Xs` 的 X
- **要看什麼**: X 與實際等待體感是否相符（tool 執行時間不計入；abort 於 Stop 當下取樣）
- **什麼算過**: 無明顯離譜值（如 0s、或把 tool 時間算進去的過大值）；體感誤差在可接受範圍

#### M-04: abort 後畫面安定感

- **Reason**: 「安定感」是瞬時視覺印象，截圖斷言無法完全捕捉閃爍
- **Steps**:
  1. 於 reasoning streaming 中按 Stop，注視 Stop 後一秒內的畫面
  2. 重複 2–3 次（不同時點：chip streaming 中、tool 執行中）
- **要看什麼**: Stop 當下是否一步到位安定——無元素閃爍、無殘留 spinner、半顆 chip 直接落定為收合態
- **什麼算過**: 約半秒內畫面完全靜止且語意清楚（看得出「這輪被停了」）

#### M-05: 慢 provider 下降級文案時機

- **Reason**: `Still working…` 的出現時機是否「自然」需在真實慢回應下體感判斷（mock 驗的是機制，不是體感）
- **Steps**:
  1. 以真實 provider 送出 canonical 級複雜提問數次，遇到慢回應時觀察文案切換
- **要看什麼**: 降級文案是否太敏感（正常間隔就頻繁跳出）或太遲（已懷疑當機才出現）；part 抵達後是否即時恢復
- **什麼算過**: 文案切換不引發「當機了嗎」的誤判，也不會在正常串流節奏中反覆閃現

### User Acceptance Test

> PO 視角驗收，於 PR review 時執行。

#### UAT-01: 使用者視角走完 canonical 級複雜提問

- **Acceptance Question**: 「整個等待與回答過程，我是否隨時知道系統在幹嘛，且事後能回看它怎麼想的？」
- **Steps**:
  1. 以使用者身分開啟 app，送出一個 canonical 級複雜提問（如 Apple 10-K 風險因子比較）
  2. 全程不操作，觀察回饋；完成後回看 transcript 並點開各 Reasoning chip
  3. 再做一次中途 Stop 與一次 regenerate
- **Expected**: 全程無「卡死了嗎」的時刻（placeholder/chips/tool cards 銜接無空窗焦慮）；答案聚焦且 reasoning 不干擾閱讀；事後每輪思考可回看；Stop 與 regenerate 的行為符合直覺。以上皆成立即驗收通過。

---

## Scenario ID 對照

| bdd-scenarios.md | 本計畫 Method |
|---|---|
| S-wire-01～05 | Deterministic（curl/jq） |
| S-trace-01~03 | Deterministic（+ Langfuse SDK 讀回；Expected 平台無關） |
| S-iso-01～03 | Deterministic（script + SDK） |
| S-chip-02/03/04/06/08/09、S-place-02/04/05、J-03 | Playwright（時序敏感；S-chip-06、S-place-04/05 用 edge-case mock） |
| S-chip-01/05/07、S-place-01/03、S-pres-01～05、J-01、J-02 | Browser-Use CLI（真 backend） |
| M-01～05 | Manual Behavior Test |
| UAT-01 | User Acceptance Test |
