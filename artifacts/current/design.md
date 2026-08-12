# Design: SEC Filing 偵測鏈 — Text Fallback Path(DEV-136)

## 來源與 Isolation 聲明

本文件完全依據 Linear issue DEV-136(spec + handoff comments)、已完成的 blocking issue
DEV-133(markdown H3/H4 偵測,本 fallback 承接的前二路)、以及 parent spec DEV-127
(`sec_text_pipeline` 重寫的 SSOT)彙整而成。撰寫過程未讀取任何 implementation code,
遵循 `behavior-validation-plan` 的 isolation principle:scenario 應對齊 design 而非
implementation,才能抓出兩者之間的落差(DEV-136 目前已在 Code Review 狀態,implementation
已存在於 branch 上,但本文件刻意不看它)。

## 系統背景

FinLab-X 需要把 SEC 10-K filing 的每個 Item(如 Item 1A "Risk Factors")內文切成結構化的
`blocks`(heading + 內容),供檢索使用。`sec_text_pipeline` 把每個 Item parse 成以下兩種
形狀之一(discriminated union):

- **StructuredItem** — `prelude`(可選的前言)+ `blocks`(heading+內容列表)+ `detection_source`
- **FlatItem** — Item 整段文字,不切分(三路偵測都失敗)

`detection_source` 是 `Literal["markdown_h3", "markdown_h4", "text_fallback"]`(來自 DEV-127
parent spec 的 schema 定義);FlatItem 不帶此欄位。

**偵測鏈(三路依序嘗試):**

1. Markdown H3 anchored search
2. Markdown H4 anchored search
3. **Title-Case text fallback** ← DEV-136 範圍

路徑 1、2 由 DEV-133 建置(已 merge,介面凍結)。DEV-136 新增路徑 3 並接入鏈路。

**共用關卡**(套用在三條路徑上,DEV-133 已建置,DEV-136 重用不重寫):

- **Plausibility check**:候選 anchor 數 ≥2 且第一個 anchor 位置落在 Item 文字前 30% 內,
  才算可信;否則此路不可信,降級到下一路。
- **Prelude validity threshold**:第一個 block heading 之前的文字,≤3,000 chars 才是有效
  prelude(整段附加為 metadata,不進索引,不截斷)。>3,000 chars 則不是 prelude,重新分類
  為無標題的 leading block,進入正常 chunk/索引流程。此機制保證**任何情況下都零 content
  loss** — 沒有任何文字會被靜默丟棄。
- 若三路都不可信,該 Item 變成 `FlatItem`(整段文字,不切分)— 這不是錯誤,是合理的降級
  結果(legible failure)。

## Feature: Title-Case Text Fallback Detection Path

### Overview

當 markdown H3、H4 兩路對某個 Item 都拿不到可信結果時,系統降級到用「看起來像 Title-Case
heading 的獨立行」來偵測 heading(沒有 markdown 語法可以錨定,純靠長度與上下文線索)。這不是
罕見的邊角案例 — 72-probe 研究驗證涵蓋 18 檔 tickers、63 個 Items,其中 8 個 Item 完全靠這條
路徑才有結構(MSFT 整份 filing 的 4 個 Item 全部靠它,因為 MSFT 的 filing markdown 品質劣化)。

### Rule: 候選 heading 行的 rejection 規則

Item 文字中的一行,只要符合以下任一條件就會被拒絕(不能當 fallback heading 候選):

1. 長度不在 5–120 chars 區間內
2. 含 digit cluster:regex `\d{3,}`(連續 3 碼以上數字,不論是否被字母包住,例如
   "Q42024" 含 5 碼連續數字會命中),或整行純數字
3. 該行是「Item 自引」(重複 Item 自己的標題,例如整行就是 "Item 1A" 或
   "Item 1A. Risk Factors")— 這種行不能當作自己這個 Item 的 fallback anchor
4. 上下文訊號不成立:上一行**必須**不是句尾標點結束,且下一行**必須**是 long prose
   (>80 chars)— 兩個條件都要成立,任一不成立就拒絕
5. 含 `|`、`$`、`%` 字元
6. 以 `.`、`,`、`;`、`:` 結尾
7. 以 `(數字)` 開頭(例如 "(1)ppt")— 財報表格 footnote 標籤的典型形狀

規則 5、6 沒有明寫在 DEV-136 issue 本文的摘要句裡,但透過 handoff comment(對照演算法源頭的
72-probe 研究 script)確認是已裁決、承重的規則組成部分。規則 7 則是**本輪討論期間才落地的
code review fix**(commit `e282763`,「review round 1 — footnote-label rejection」):財報
表格的 footnote 標記行(如 "(1)ppt")會被誤判成候選標題,fix 後 MSFT Item 7 的 block 數從
41 修正為 **38**(見下方 Acceptance Criteria 表格與 Known Limitations)。7 條規則視為同一個
Rule 的整體。

同一輪 review 也發現、但**明確裁決不修**的第二個誤判案例:MSFT Item 1 裡一個財報表格儲存格
「Vice Chair and President」被誤判成候選標題(它恰好符合現行全部規則的上下文條件,且找不到
能安全排除它、又不誤傷真正標題的規則)。已寫成專屬 regression test 釘住現況,裁決依據與
DEV-133 DIS-7 known limitation 同一先例:等待未來 A/B failure mining 累積更多證據再議。

### Rule: Assembly 是逐字重現 — 不做 prelude carve-out

這個演算法的研究階段草稿,曾經在量測/附加 prelude 前,把 Item 自己的標題行從 prelude 文字中
剝除,避免「重複」。這個做法在 DEV-133 review 時已被明確裁決推翻:user 的裁決是「重複不重要,
zero content loss 才重要」。Fallback 的 prelude/blocks assembly 必須逐字重現(沿用與 markdown
路徑相同的 `_assemble` 行為)— 不排除任何文字。

(註:「Item 自引 skip」規則是不同的事 — 那是「哪些行可以被選為候選 heading anchor」,不是
「assembly 時要排除哪些文字」。兩者不衝突:一行自引文字不能被選為 anchor,但它的文字內容不會
從 assembled 輸出中被刪除。)

### Rule: Fallback 結果要通過與 markdown 路徑相同的關卡

Fallback 路徑找到候選 heading 之後,其結果要通過跟 markdown 路徑完全相同的 plausibility check
與 prelude validity threshold — fallback 沒有比較寬鬆的標準。如果 fallback 自己的候選也不通過
plausibility,該 Item 變成 FlatItem(三路都已窮盡)。

### Rule: Fallback 不會搶在可信的 markdown 結果之前

偵測依序嘗試 markdown H3 → H4 → fallback,在第一個產出可信結果的路徑就停止。Fallback 只有在
兩條 markdown 路徑都試過且都不可信時才會執行。即使 fallback 路徑「如果跑了」也會找到東西,只
要 markdown 路徑已經可信,fallback 就不能執行或覆蓋其結果。

## Acceptance Criteria(來自 DEV-136,轉譯為 business outcome 而非 implementation checklist)

真實 filing 案例(來自本專案 72-probe 研究驗證,已錄製為 fixtures):

| Filing(ticker) | Item | 原始 Item 文字量(約) | 預期結果 | 預期 block 數 |
|---|---|---|---|---|
| MSFT FY2026 | 1 | — | 經 `text_fallback` 產出 StructuredItem(兩條 markdown 路徑在此 filing 上皆劣化/不可信) | 27 |
| MSFT FY2026 | 1A | — | 經 `text_fallback` 產出 StructuredItem | 14 |
| MSFT FY2026 | 7 | — | 經 `text_fallback` 產出 StructuredItem | 38(原始 72-probe 數字是 41,review round 1 加上 footnote-label 規則後拿掉 3 個 "(1)ppt" 誤判 anchor,修正為 38) |
| MSFT FY2026 | 7A | — | 經 `text_fallback` 產出 StructuredItem | 5 |
| GE FY2025 | 1A | 61,747 chars | FlatItem — 三路都找不到結構,不捏造假 heading | 無 blocks |
| WMT | 7A | — | markdown anchor 存在但不可信(僅 1 個淺層 anchor)→ 降級到 fallback → 經 fallback 產出 StructuredItem | — |
| DIS | 7A | — | markdown anchor 存在但不可信(僅 1 個深層 anchor)→ 降級到 fallback → 經 fallback 產出 StructuredItem | — |
| WMT | 1 / 1A | — | markdown 路徑本身可信 → fallback 不得介入/覆蓋(順序/優先權測試) | — (經 markdown 路徑) |

MSFT 四個 Item 全部完全依賴 fallback 路徑才有結構 — MSFT 的 filing markdown 已劣化,若
fallback 路徑被移除或壞掉,四個 Item 都會錯誤地變成 FlatItem。這就是 issue 標題把這條路徑
稱為「承重牆」而非備援的原因。

## Known Limitations(已裁決,來自 parent spec DEV-127 — 不要當作待補的 gap)

1. **False-valid prelude**(已觀察 1/58 個 structured items,案例為 DIS Item 7):看起來像短
   prelude(例如摘要表格)但其實是本文內容的文字,可能被誤判為 prelude metadata 附加,而非
   進索引成為可搜尋的 block。有界:每個 Item 最多受影響 3,000 chars,且內容並非永久遺失
   (仍會透過 payload 搭同 Item 其他有命中的 chunk 一起送到 LLM)。已裁決的處置方式:若未來
   有更多證據,可加 content-signal check(如數字/表格密度)— 但**不要**因為這單一樣本去調整
   3,000-char 門檻。
2. **大型 flat item**(已觀察 1/63,案例為 GE Item 1A,61k chars):偶爾三路都找不到結構,
   整個 Item 維持單一 FlatItem。零 content loss,但該 Item 失去 block 層級的結構(chunk 較
   大、主題混雜)。這是已接受的現狀,不是要「偵測得更聰明」去修的缺陷。
3. **Source 層級缺失**(4/72 probes:GE Items 1/7A、GS Items 1A/7A):部分非標準 filer,
   edgartools 本身就找不到 Item 邊界。這是 detection 之前、更上游的問題(另開 DEV-147 追蹤),
   **不屬於本 feature 範圍**。
4. **表格無特殊處理**:block 內的表格會被壓扁成文字進行 chunk/embed(可搜尋,但對結構化數字
   查詢語意較弱)。這是設計現狀,不是缺陷。
5. **官職表格儲存格誤判為 heading**(已觀察 1 例,MSFT Item 1):財報裡的官職對照表,儲存格
   內容(如 "Vice Chair and President")恰好符合現行全部 7 條 rejection 規則的條件,被誤判
   為候選標題。Review round 1 明確裁決不修——找不到能安全排除這類儲存格、又不會誤傷真正標題
   的結構性規則;裁決先例與 DEV-133 的 DIS Item 7 known limitation 相同,等待未來 A/B
   failure mining 累積更多證據再議。已有專屬 regression test 釘住現況。

## DEV-136 明確排除的範圍(Out of Scope)

- 讓 fallback(或任何路徑)去偵測目前三路都會失敗的 filing 結構(例如「改善」GE 1A 的偵測)
  — exhaustive filing-variant coverage 是 non-goal。
- 因為單一已知的 false-valid-prelude 案例去調整 3,000-char prelude validity 門檻。
- 任何 UI/前端介面 — 這是純粹的 backend parsing/detection 行為,沒有直接的終端使用者互動。
  本票範圍內唯一的「消費者」是 `ParsedFiling` 資料結構,以及(供人工抽查用的)`inspect`
  view。下游檢索/citation/UI 行為是其他票(DEV-135、DEV-137、DEV-125)的範圍,不在本次驗證
  計畫內。
- 針對 prelude validity 加 content-signal(數字/表格密度)check — 已明確裁決延後,需要更多
  證據才做。

## Design Envelope 校準重點(docs/design-envelope.md — 引用時標明章節號)

- **§1 JIT ingestion**:「JIT must handle the happy path robustly and fail legibly on the
  rest.」Detection 的 happy path = 正確切出結構;legible failure = 乾淨降級成 FlatItem,
  絕不靜默遺失資料。
- **§2 Reliability**:「Silent partial/empty answers are bugs; exhaustively handling every
  filing variant is over-engineering.」Zero-content-loss 是需要徹底驗證的硬性不變量。但要求
  偵測「完美處理每一種可能的畸形 filing」則明確不是這張票的責任。
- **§3 Non-Goals**:「exhaustive SEC filing-variant coverage」與「adversarial input
  hardening... fuzzing」明確排除在範圍外。不要提出對 rejection rules 做 fuzzing 式、任意生成
  惡意文字的 stress test scenario。這個 pipeline 也沒有 concurrency/network 相關的 scale
  pressure(§1:operators=1、request rate <1 QPS;本 detection 函式操作已經抓好的文字,不是
  即時網路呼叫)。
- **§4 Production-Grade Zones**:「JIT failure legibility」列為 production 標準的 zone —
  涵蓋「三路全失敗 → FlatItem」與「zero content loss」這兩個具體行為。6 條 rejection rule
  的精確調參本身,不是 §4 明列的 zone。
- **§5 Testing Envelope**:「§4 zones: Behavior-driven, thorough.」「Everything else: happy
  path + one legible-failure case per behavior. Stop there.」另外 rule 5:「Volume is a
  signal, not a virtue」— 不要為每一種字元類別各生一個 rejection scenario,每條規則抓一個
  代表性的邊界案例就夠。zero-content-loss / FlatItem-fallback 行為要用 §4 深度驗證;6 條
  rejection rule 各自的調參用「everything else」的淺深度就好。
- 不要提出把上述三個 Known Limitations 當作缺陷重新討論的 scenario — 它們已經裁決/接受。
  可以驗證「已接受的降級行為真的發生了」(例如「GE Item 1A 變成 FlatItem,而非拋出錯誤」)
  — 這是合理的 legible-failure scenario,不是要求修掉它。

## 給 Scenario 撰寫者的框架提醒

這個 feature **沒有 UI**。Given/When/Then 請用 filing/Item 資料流過 pipeline 的語言描述
(business language:ticker、Item 編號、「該 filing Item 1A 的文字」、「偵測鏈」、「產出的
StructuredItem/FlatItem」),不要用技術內部細節(不要用 function 名稱、不要用 code)。所有
驗證都會是 backend/deterministic(靠 fixture 資料驅動),不需要 browser automation。
