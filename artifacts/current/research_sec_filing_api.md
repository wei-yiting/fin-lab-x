# Research: edgartools Structured API vs Custom Pipeline

## 背景

FinLab-X 有兩條 code path 在 parse SEC filings：

1. **Agent tool** (`backend/agent_engine/tools/sec.py`) — `sec_official_docs_retriever` 使用 `filing.text()` 後再用 `text.find()` 做 string matching 來擷取 section。
2. **Ingestion pipeline** (`backend/ingestion/sec_filing_pipeline/`) — 使用 `filing.html()` 後執行約 1000 行的自製 HTML preprocessing、heading 偵測、Markdown 轉換。

兩條路徑都用了 `edgartools` 來定位和下載 filing，但接著就**立刻丟棄 library 的結構化輸出**，退回到用 raw text/HTML parsing 搭配手寫 heuristic。

本文件記錄 edgartools 實際提供了哪些 API，以及為什麼應該用原生 API 取代現有實作。

---

## 問題：兩條 Code Path 都在重造 edgartools 已經提供的功能

### Pipeline 做了什麼

Pipeline 由 5 個 processing module 串接而成：

| Module | 行數 | 職責 |
|--------|------|------|
| `sec_downloader.py` | ~90 | 用 `Company.get_filings()` 定位 filing，呼叫 `filing.html()` 取得 raw HTML |
| `html_preprocessor.py` | ~300 | 清除 decorative CSS、估算 body font size、promote headings |
| `sec_heading_promoter.py` | ~365 | 用 regex + font-size/bold heuristic 偵測 Part/Item 邊界，promote 成 h1-h5 |
| `html_to_md_converter.py` | ~150 | 用 `html-to-markdown` + `markdownify` fallback 轉換成 Markdown |
| `markdown_cleaner.py` | ~100 | 後處理：清除 boilerplate、normalize whitespace |

合計約 1000 行自製 parsing code。

### 為什麼這個做法很脆弱

`sec_heading_promoter.py` 裡包含了公司專屬的 workaround，暴露了這套做法的根本脆弱性：

- **Donnelley/Workiva markup** — `<span>Item</span><span> 7.</span>` 被拆到相鄰的 span 裡
- **JNJ, MSFT, BAC** — body 裡的 PART 分隔線沒有 bold，導致 heuristic 退回到 ToC anchor
- **BRK.A/B** — Items 10-14 是 cross-reference 到合併 section，只存在於 ToC 而非 body；需要特殊的 "drop-pass" filter

每家新公司的 filing 都可能引入新的 HTML quirk，需要再加一個 workaround。這種 code 沒有收斂點。

### edgartools 已經提供了什麼

Pipeline 在 `sec_downloader.py` 第 74 行用了 `filing.html()` 就丟掉所有結構。但同一個 `filing` 物件其實支援：

```python
# 結構化 section 存取
tenk = filing.obj()              # 回傳 TenK 物件
risks = tenk["1A"]               # bracket notation — 直接拿到 section 內容
mda = tenk["7"]                  # 不需要 regex，不需要 heuristic
business = tenk["1"]

# key-based 存取（可區分 Part I vs Part II）
sec = tenk.sections.get("part_i_item_1a")
text = sec.text()

# 完整 markdown，保留 heading hierarchy
md = filing.markdown()           # 保留 Part/Item/sub-section headings
```

---

## Smoke Test：ADSK 10-K（edgartools 5.17.1）

測試對象為 Autodesk 最新的 10-K（filing date: 2026-03-03，period: FY ending 2026-01-31）。

### 透過 `tenk[key]` 取得的 Section 內容

| Section | `tenk[key]` 輸出 | 現有 tool 輸出 |
|---------|------------------|---------------|
| Business (Item 1) | 48,223 chars | 未 expose |
| Risk Factors (Item 1A) | **103,734 chars** 真實內容 | `"Item 1A. Risk Factors 15"`（ToC stub） |
| MD&A (Item 7) | **78,640 chars** 真實內容 | `"Item 7. Management's Discussion... 41"`（ToC stub） |
| Market Risk (Item 7A) | 3,860 chars | 未 expose |

`tenk["1A"]` 前 200 字元：

> ITEM 1A. RISK FACTORS
>
> We operate in a rapidly changing environment that involves significant risks, a number of which are beyond our control. In addition to the other information contained in this An...

零 ToC 污染。零公司專屬 workaround。

### 透過 `tenk.sections` 取得的結構化 Sections

回傳 24 個正確命名的 section key，可區分 Part/Item：

```
part_i_item_1, part_i_item_1a, part_i_item_1b, part_i_item_1c,
part_i_item_2, part_i_item_3, part_i_item_4,
part_ii_item_5, part_ii_item_6, part_ii_item_7, part_ii_item_7a, part_ii_item_8,
part_ii_item_9, part_ii_item_9a, part_ii_item_9b, part_ii_item_9c,
part_iii_item_10, part_iii_item_11, part_iii_item_12, part_iii_item_13, part_iii_item_14,
part_iv_item_15, part_iv_item_16, part_iv_signatures
```

### 透過 `filing.markdown()` 取得的完整 Markdown

- 總計 **572,954 chars**
- Heading 分布：**H1: 4, H2: 45, H3: 10, H4: 72**
- 結構對應：

| Markdown Level | SEC 文件層級 | 範例 |
|----------------|-------------|------|
| `# ...` (H1) | Part | `# PART I`, `# PART II`, `# PART III`, `# PART IV` |
| `## ...` (H2) | Item | `## ITEM 1.`, `## ITEM 1A.`, `## ITEM 7.` |
| `#### ...` (H4) | Sub-section | `#### RESULTS OF OPERATIONS`, `#### LIQUIDITY AND CAPITAL RESOURCES`, `#### FOREIGN CURRENCY EXCHANGE RISK` |

注意：H3 幾乎沒用到（僅 10 個）。edgartools 忠實保留了原始 HTML 的視覺層級 — Autodesk 的 filing 使用三層視覺結構，對應到 H1/H2/H4，跳過 H3。這不是 bug；不同公司的 heading level 分布可能不同。

### Section 物件 API

`tenk.sections.get(key)` 回傳的 `Section` 物件 expose 了以下 attributes：

```
confidence, detection_method, end_offset, item, name, node,
parse_section_name, part, search, start_offset, tables, text, title, validated
```

- `.text()` 回傳**純文字** — sub-section headings 被攤平成一般文字行
- `Section` 上沒有 `.markdown()` 方法
- `.start_offset` / `.end_offset` / `.node` 存在但尚未驗證是否可用來切割 `filing.markdown()`，以取得保留 sub-heading 的 per-section markdown 片段

---

## 比較總結

| 面向 | 現有實作 | edgartools 原生 API |
|------|---------|-------------------|
| Section 擷取 | `text.find()` 對 flattened text 做搜尋 — 命中 ToC | `tenk["1A"]` — 語義化 section 存取 |
| Heading 偵測 | 365 行 font-size/bold/regex heuristic | `filing.markdown()` — 預建的 heading hierarchy |
| 公司專屬 hack | JNJ, MSFT, BAC, BRK workarounds | 不需要 — 內部處理 XBRL/HTML 結構 |
| Part I vs Part II 區分 | 未處理 | `part_i_item_1a` vs `part_ii_item_5` keys |
| ToC 污染 | 根本性 bug（first match = ToC） | 不可能發生（結構化 parsing） |
| Sub-section headings（RAG 用） | 自製 h3/h4/h5 promotion（font-size ranking） | `filing.markdown()` 中保留為 H4 |
| 維護成本 | 每家新公司 = 可能需要新 workaround | 零 — edgartools 在 upstream 處理 |
| Code 量 | 5 個 module 合計約 1000 行 | 每個 use case 約 10 行 |

---

## 設計決策

### 兩條路徑各用不同 API

edgartools 提供的兩個 API 恰好對應兩個不同的使用場景，不需要額外的 bridge（如 `Section.start_offset` / `end_offset`）：

| 路徑 | 使用的 API | 用途 | Sub-heading 需求 |
|------|-----------|------|-----------------|
| V1 Agent Tool（直接 search） | `tenk[key]`（純文字） | LLM 直接閱讀 section 內容並回答 | 不需要 — LLM 讀純文字就夠了 |
| V2 RAG Pipeline（ingestion） | `filing.markdown()`（完整 markdown） | `MarkdownNodeParser` parsing + chunking | 需要 — heading hierarchy 決定 chunk 的 heading path |

### V1 Agent Tool 的 Multi-Section 長度管理

`tenk["1A"]` 回傳 103K chars（≈26K tokens），`tenk["7"]` 回傳 78K chars（≈20K tokens）。單一 section 在現代 LLM 的 context window（128K-200K tokens）裡放得下，但 agent 可能一次想拿多個 section。

設計方向：**tool 分兩步走，先給 metadata、再按優先序 fetch**。

1. **第一步：回傳可用 sections 的 metadata**（名稱 + 字元數） — agent 看到所有 section 的大小
2. **第二步：agent 根據 query 排優先序**，從最相關的 section 開始 fetch，累加長度
3. **當累計長度即將超過 context budget 時停止** — agent 自行判斷「再拿就不夠了」，不再請求更多 section
4. **單一 section 不截斷** — 完整回傳以公平呈現 tool-only 的能力

這讓 agent 在 context budget 內拿到最多有用資料，同時不會因為截斷而降低品質。

### Heading Level 正規化 — 不需要

已確認 LlamaIndex `MarkdownNodeParser` 的 source code 明確處理了 non-consecutive heading levels。其 `header_stack` 用 raw `header_level`（`#` 的數量）做比較，而非 stack depth，原始碼註解直接寫著：*"markdown headers can jump from H1 to H3, for example"*。以 `filing.markdown()` 的 H1→H2→H4 結構為例，heading path 會正確產出 `PART I/ITEM 1A./RESULTS OF OPERATIONS` — level 數字被跳過不影響 path 的正確性。因此不需要做 heading level 正規化。

---

## 保留、移除、修改

### 保留（有獨立價值）

- `filing_store.py` — 按 ticker/filing_type/fiscal_year 的本地 cache
- `pipeline.py` — orchestration，含 retry、batch processing、download 前的 cache 檢查
- `filing_models.py` — domain types（FilingMetadata, ParsedFiling, error hierarchy）

### 移除（被 edgartools API 取代）

- `sec_heading_promoter.py` — 全部 365 行；`filing.markdown()` 提供 heading hierarchy
- `html_preprocessor.py` — decorative CSS 清理、font-size 估算、heading promotion
- `html_to_md_converter.py` — HTML-to-Markdown 轉換；`filing.markdown()` 已提供
- `markdown_cleaner.py` — 後處理清理；原生 markdown 輸出已足夠乾淨
- `sec.py` 中的 `_extract_section()` — 由 `filing.obj()` bracket access 取代

### 修改

- `sec_downloader.py` — 從 `filing.html()` 改為 `filing.markdown()` 或 `filing.obj()`
- `sec.py`（agent tool）— 用 `filing.obj()` + bracket access 取代 `_extract_section()`
