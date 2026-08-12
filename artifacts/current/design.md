# Design: DEV-134 — Inspect View + CLI

> 本檔案是從 Linear issue DEV-134（+ 必要的 parent/blocked-by context）整理而成，供
> `behavior-validation-plan` 的 Three Amigos 流程使用。**未讀取任何 code
> implementation** — 所有 schema/規則描述均來自已完成票（DEV-132、DEV-133）的 issue
> 內文，非程式碼考古。

## 背景（來自 parent spec DEV-127）

FinLab-X 的 RAG path 正在把 SEC 10-K 的 parsing 從舊的 HTML heuristic 重寫成
`sec_text_pipeline`（基於 edgartools 結構化 API）。新 pipeline 產出 `ParsedFiling`
（Item → prelude + blocks 的結構化資料），取代舊版「產出 markdown 字串、下游再
re-parse」的作法。

Detection（判斷一個 Item 該怎麼切 block、prelude 算不算數）目前分三條路徑
（markdown H3 anchored → H4 anchored → Title-Case text fallback），且 prelude 的
「有效 / 該轉正文」判定是用一個 3,000 字元 threshold 做的語意判斷，不是簡單規則。
這些判斷都可能出錯，出錯的後果是內容從檢索索引中消失（content loss）— 對一個標榜
「隨問隨答任何美股 ticker」的系統，是很直接的品質風險。

Parent spec 的 user story #12 明確要這個工具：

> As the operator, I want 一個 human-readable 的 inspect view 顯示 detection 結果
> （含 detection path 與 prelude 判定）, so that 我能對照 SEC 原文確認「retrieval
> 問題不出在 chunking 之前」

換句話說：**inspect 是給人（operator）手動抽查 detection/prelude 判定品質、以及做
四象限 failure 分析用的工具**，不是給下游 pipeline 消費的資料格式。

## Feature: Inspect View + CLI（DEV-134）

### 目標

1. 獨立 view module `sec_text_pipeline/inspect_view.py`，提供
   `to_inspect_markdown(filing: ParsedFiling) -> str`：把一份 `ParsedFiling` 完整
   render 成人讀 markdown，每個 Item 的 kind、detection_source、prelude 判定、blocks
   邊界都要顯式攤開。
   - **不修改凍結的 `filing_models.py`**（DEV-132 裁決：schema module 是
     downstream stages 的穩定契約，render 是 view concern，必須放在別的 module）。
2. CLI 三個入口（新增 `sec_text_pipeline/__main__.py`，
   `python -m backend.ingestion.sec_text_pipeline`，比照 `_html` pipeline 既有
   CLI 慣例，但**不讀 `_html` CLI 原始碼**，僅需知道「有慣例可比照」這件事）：
   - **`--verbose`**：一頁摘要表（無 mode flag 時的預設行為）。
   - **`--section <key>`**：單一 Item 的純文字（key 是 lowercase item key，如
     `7`、`1a`；CLI 端大小寫不敏感）。
   - **`inspect` subcommand**：完整 render 到 gitignored 目錄，印出檔案路徑。

### 依賴的凍結 schema（DEV-132，已 merge，PR #37）

> Inspect 只 render，不改變以下 schema。以下欄位描述是 render 邏輯的輸入契約。

- `ParsedFiling` = metadata + `list[StructuredItem | FlatItem]`（discriminated
  union，用 `kind` 欄位區分）。
- `StructuredItem`：有 `detection_source`、`prelude`、`blocks`（**至少一個
  block**，schema 層 enforce 這個 invariant，理論上不會是空 list）。
- `FlatItem`：schema **只有** `item / title / text` 三欄 — 沒有
  detection_source / prelude / blocks 可以 render。
- `FilingMetadata`：含 `accession_number` / `cik` / `primary_document`（citation
  用途，inspect 不一定要顯示，但屬於 filing 層級 metadata）。
- Stub items（`is_stub_section` 判定為 stub 的 section）在 parse 階段就被 drop，
  不會出現在 `ParsedFiling.items` 裡 — inspect 看不到、也不用管 stub。
- `parse_filing(ticker, fiscal_year, force)` 對「全部 section 皆空或 stub」的
  filing 會拋 `EmptyFilingError`（帶 ticker/年度/accession），且**不落地**
  filing store。這是 inspect CLI 呼叫 `parse_filing` 時可能會撞到的例外。

### 依賴的 prelude/detection 判定規則（DEV-133，已 merge，PR #39）

Prelude 判定是 **render 時推斷**，schema 沒有存判定結果本身（`prelude` 欄位就是
一個 `str`，`""` 代表無）：

| 資料狀態 | Render 判定 |
|---|---|
| `prelude` 非空字串 | **valid prelude** → 附 chars 數顯示 |
| `prelude == ""` 且 `blocks[0].heading == ""` | **reclassified leading block**（原本 >3,000 chars 的偽 prelude，被 DEV-133 的邏輯轉成無標題的第一個 block；`heading == ""` 是 reclassify 的**唯一** marker，因為正常錨定到的 heading 一定非空） |
| `prelude == ""` 且其他情況（`blocks[0].heading` 非空） | **無 prelude**（這個 Item 本來就沒有 prelude 文字） |

- `detection_source` 目前資料只會出現 `"markdown_h3"` / `"markdown_h4"` 兩種值
  （`"text_fallback"` 的 producer 是尚未完成的 DEV-136，merge 後同一支 CLI 會自動
  顯示第三種值，**DEV-134 不被 DEV-136 blocked，可平行做**）。
- `FlatItem` 沒有 `detection_source` 欄位（見上方 schema 定義），render 邏輯不能
  假設每個 Item 都有這個欄位。

### Render 規則（DEV-134 本票明文規則）

- **StructuredItem**：顯示 detection_source、prelude 判定（依上表，valid 的話附
  chars 數）、每個 block 的 heading 與內容。
- **FlatItem**：顯示 `kind=flat` + 字數（或 preview）；不顯示
  detection_source / prelude / blocks（schema 沒有這些欄位）。
- **Chunking 不在本票 render 範圍**：chunk（block 再切 512/50 token）是 DEV-135
  （dense ingest）層的概念，不存在於 `ParsedFiling` 裡，inspect 不 render chunk
  邊界。「blocks 邊界」是 detection 切出的段落邊界，跟 embedding chunk 是不同層
  的概念，兩者不要混。

### 輸出路徑與 caching

- Inspect 輸出目錄要透過 `backend/common/data_paths.py` 的新 resolver 取得
  （env-var overridable），**CLI 不能 hardcode 路徑字串**。
- 該輸出目錄必須被 gitignore；順便補上 `data/sec_text/`（DEV-132 filing store 的
  runtime 輸出）目前在 `.gitignore` 裡缺漏的規則。
- Cache miss 時 CLI 直接呼叫 `parse_filing`（該函式已內建 cache-first 邏輯，命中
  filing store 就不重打 EDGAR，miss 就自動 fetch + parse + 落地），CLI 端不用自己
  判斷 cache 命中與否。

### Acceptance Criteria（逐字對照 DEV-134）

- [ ] `inspect --ticker X --fiscal-year Y` 產出完整 markdown：每 Item 依 Render
      規則攤開（StructuredItem 三要素齊全；FlatItem 只有 kind + 字數），可對照
      SEC 原文人工檢查。
- [ ] `--verbose` 一個螢幕內的摘要表（不含內文）；`--section <key>` 輸出單 Item
      純 plain text（CLI 端 key 大小寫不敏感）。
- [ ] Inspect 輸出目錄走 `data_paths.py` resolver、已 gitignore；`data/sec_text/`
      gitignore 缺漏一併補上；cache miss 自動 fetch + parse。
- [ ] Render 邏輯的 tests 用手工構造的 toy `ParsedFiling`（結構斷言，不打
      EDGAR、不打真實 filing）。

### 明確排除（Out of scope）

- **Chunking**：block 再切 512/50 token 是 DEV-135（dense ingest）的概念，不存在
  於 `ParsedFiling`，inspect 不 render、不需要驗證。
- **`text_fallback` 的實際輸出品質**：producer 是 DEV-136，尚未 merge。DEV-134
  只要「有第三種 `detection_source` 值出現時 CLI 能正確顯示」這件事本身是對的
  （render 邏輯要能處理這個 literal 值），不需要驗證 DEV-136 產出的 fallback 內容
  好不好。

### Spec 已定案、不需重新討論的調整（2026-08-11 記錄）

- `to_inspect_markdown` 是獨立 view module 的 free function，不是
  `ParsedFiling` 的 method（避免污染凍結 schema module）。
- CLI flag 是 `--fiscal-year`（不是 `--year`），對齊 DEV-132 已定案的參數名，且
  **必填**（latest-year 自動解析已裁決延後，不在本票範圍）。
- Prelude 判定推斷規則（見上表）是本票明文規則，避免誤以為 schema 有存判定結果。

## 校準備註（Design Envelope）

依 [`docs/design-envelope.md`](../../docs/design-envelope.md) — inspect CLI **不是**
§4 列出的任一 Production-Grade Zone（Eval 測量嚴謹度 / Observability / ADR /
JIT failure legibility / API contract）。它是 operator 手動抽查用的內部工具，讀取
對象是已經被 DEV-132/DEV-133 驗證過的 `ParsedFiling` 結構。

依 §5 Testing Envelope，「Everything else」的標準是 **happy path + 每個 behavior
一個 legible-failure case，到此為止** — 不需要窮舉每種
detection_source × prelude 判定 × item kind 的排列組合（那是 DEV-133 detection
邏輯本身的測試責任，DEV-134 只要證明「render 邏輯正確反映 schema 資料」）。

這份校準會直接影響 Three Amigos 的 scenario 數量：**優先覆蓋「每個 render 分支
至少一個具體例子」，不做窮舉性 edge case 爆炸**。QA 仍可以指出邊界情況，但 PO 在
Round 3 判斷 Include vs Reject 時，應該把這條 envelope 校準當作判斷依據之一。
