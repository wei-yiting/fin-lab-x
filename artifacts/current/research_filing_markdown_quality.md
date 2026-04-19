# Research: `filing.markdown()` Output Quality & Pipeline 重建方案

## 背景

[research_sec_filing_api.md](./research_sec_filing_api.md) 建議 Pipeline 路徑用 `filing.markdown()` 取代現有 ~1000 行的 HTML parsing pipeline。本文件記錄對 `filing.markdown()` 的實測結果，以及根據發現提出的替代方案。

---

## `filing.markdown()` 實測結果

測試 edgartools 5.17.1，對 ADSK、AAPL、MSFT 三家公司的最新 10-K 呼叫 `filing.markdown()`。

### 問題總覽

| 問題 | ADSK | AAPL | MSFT |
|------|------|------|------|
| Cover page (SEC boilerplate) | 121 行 | 132 行 | 78 行（在 div 裡） |
| Page separators `---` | 0 | 0 | 0 |
| Page number `<div align='center'>N</div>` | **105 個** | 0 | 2 |
| Residual HTML tags | 有 | 有 | **115 行** |
| Part III stubs (incorporated by reference) | 有 | 有 | 有 |
| Split titles (`## ITEM 1.` + `## BUSINESS` 分兩行) | **每個 Item** | 無 | 無 |
| Body text 被標成 `##` | 無 | 無 | **25 行** |
| `# PART I/II/III/IV` H1 headings | 有 | 有 | **完全沒有** |

### 關鍵發現

**`filing.markdown()` 在 MSFT 上嚴重損壞：**

- PART headings 被包在 `<div align='center'>PARTI</div>` 裡，不是 markdown heading
- Body 段落被錯標為 `##`（25 行 > 150 chars 的 body text 被當成 H2）
- 零個 H1 heading

這代表 `filing.markdown()` **不能作為跨公司可靠的 RAG pipeline 來源**。

### 相比之下：`tenk[key]` 結構化 API

| | ADSK | AAPL | MSFT |
|---|---|---|---|
| Section 數量 | 24 | 24 | 24 |
| Confidence | 0.95 | 0.95 | 0.95 |
| 內容正確性 | 完整，零 ToC 污染 | 完整 | 完整 |
| `.item` / `.part` 屬性 | 有（`item='7'`, `part='II'`） | 未測 | **None**（需從 key 或 text parse） |

`tenk[key]` 在所有測試公司都完美運作，不受 `filing.markdown()` 的問題影響。

### Section key 格式不一致

edgartools 的 section key 格式因公司而異：

- ADSK: `part_i_item_1a`, `part_ii_item_7`（含 part prefix，`.item='1A'`, `.part='I'`）
- MSFT: `Item 1A`, `Item 7`（無 part prefix，`.item=None`, `.part=None`）

但 **section.text() 的第一行格式一致**：都是 `ITEM {N}. {TITLE}`，可以從 text 本身 parse 出 item number 和 title。

---

## 替代方案：從 `section.text()` 重建 Markdown

### 設計

不用 `filing.markdown()`，改用 `tenk.sections` 取得結構化 skeleton，對每個 section 取 `.text()` 並重建帶 heading 的 markdown。

```
tenk = filing.obj()                    # TenK 物件
sections = tenk.sections               # 結構化 section map

for key in sections:
    sec = sections.get(key)
    text = sec.text()                  # 純文字，第一行是 ITEM heading

    # Parse item number + title from text first line
    # 加上 # Part / ## Item / ### sub-heading
    # 組合成 markdown
```

### Data Flow

```
edgartools TenK.sections
    │
    ├─ sec.item / sec.part (ADSK 有, MSFT 為 None)
    ├─ sec.text() 第一行: "ITEM 7. MANAGEMENT'S DISCUSSION..."
    │
    ▼
重建 Markdown:
    # Part II                          ← 從 PART_MAP 推斷（10-K Item→Part 對應是固定的）
    ## Item 7. Management's Discussion  ← 從 text 第一行 parse
    ### OVERVIEW                        ← ALL CAPS 短行偵測
    ### SUMMARY RESULTS OF OPERATIONS   ← ALL CAPS 短行偵測
    ...
    │
    ▼
MarkdownNodeParser
    │
    ▼
Chunks with heading path metadata:
    Header_1: "Part II"
    Header_2: "Item 7. Management's Discussion..."
    Header_3: "OVERVIEW"
    header_path: "Part II / Item 7. ... / OVERVIEW"
```

### H2 Item Heading：用 STANDARD_TITLES 常數表

**不從 `section.text()` parse heading。** 實測發現 text 第一行格式不一致：

| 公司 | Section | 第一行 | 問題 |
|------|---------|--------|------|
| ADSK | Item 1 | `ITEM 1.BUSINESS` | period 後沒有空格 |
| ADSK | Item 9 | `Table of Contents` | heading 在第三行 |
| ADSK | Item 9C | `ITEM 9C. \xa0\xa0\xa0\xa0DISCLOSURE...` | non-breaking spaces |
| AAPL | Item 1 | `Item 1.\xa0\xa0\xa0\xa0Business` | `\xa0` + Title Case |
| AAPL | Item 8 (Part IV) | `Apple Inc.` | 不是 ITEM heading |

改用 SEC 規定的標準 Item title 常數表：

```python
STANDARD_TITLES = {
    "1":  "Business",
    "1A": "Risk Factors",
    "1B": "Unresolved Staff Comments",
    "1C": "Cybersecurity",
    "2":  "Properties",
    "3":  "Legal Proceedings",
    "4":  "Mine Safety Disclosures",
    "5":  "Market for Registrant's Common Equity",
    "6":  "[Reserved]",
    "7":  "Management's Discussion and Analysis",
    "7A": "Quantitative and Qualitative Disclosures About Market Risk",
    "8":  "Financial Statements and Supplementary Data",
    "9":  "Changes in and Disagreements with Accountants",
    "9A": "Controls and Procedures",
    "9B": "Other Information",
    "9C": "Disclosure Regarding Foreign Jurisdictions",
    "10": "Directors, Executive Officers and Corporate Governance",
    "11": "Executive Compensation",
    "12": "Security Ownership of Certain Beneficial Owners and Management",
    "13": "Certain Relationships and Related Transactions",
    "14": "Principal Accountant Fees and Services",
    "15": "Exhibits and Financial Statement Schedules",
    "16": "Form 10-K Summary",
}
```

Item number 從 section key parse（`part_i_item_1a` → `1A`，`Item 1A` → `1A`），title 查表。**零 regex on filing content for headings。**

Body text 處理：跳過開頭的 ITEM heading 行和 "Table of Contents" 行即可。

### H3 Sub-heading 偵測規則

`section.text()` 中的 sub-heading 表現為 ALL CAPS 的短行。偵測條件：

- `stripped.isupper()` — 全大寫
- `5 < len(stripped) < 120` — 長度在合理範圍
- 不是純數字（排除頁碼）
- 不含 `|`, `$`, `%`（排除 table data）

### Part 推斷

10-K 的 Item→Part 對應是固定的（SEC 規定），不需要從 filing 裡偵測：

```python
PART_MAP = {
    'I':   ['1', '1A', '1B', '1C', '2', '3', '4'],
    'II':  ['5', '6', '7', '7A', '8', '9', '9A', '9B', '9C'],
    'III': ['10', '11', '12', '13', '14'],
    'IV':  ['15', '16'],
}
```

### MSFT 實測結果

| 指標 | `filing.markdown()` 原始 | 重建後 |
|------|--------------------------|--------|
| H1 (Part) | 0 | 4 |
| H2 (Item) | 61（含 body text 誤標） | 23 |
| H3 (Sub-section) | 0 | 70 |
| Cover page | 有 | 無 |
| Residual HTML | 115 行 | 無 |
| Total length | 421,988 chars | 336,668 chars |

### 已知限制

1. **H3 偵測只捕捉 ALL CAPS sub-heading** — Title Case 的 sub-heading（如 MSFT 的 "What We Offer"）會被當成 body text，不會升格為 `###`。但 H1/H2 是 100% 正確的。

2. **Table 格式丟失** — `section.text()` 回傳純文字，表格被攤平。對 RAG text chunk 影響有限（embedding 不依賴 table formatting），但若需要 table 結構化資料，需另外處理 `sec.tables()`。

3. **~~Item heading title 大小寫~~** — 已解決：改用 `STANDARD_TITLES` 常數表，不再從 text parse title。

### 相比現有 Pipeline

| 面向 | 現有 Pipeline | 重建方案 |
|------|---------------|----------|
| Code 量 | ~1000 行（5 個 module） | ~50-80 行 |
| 跨公司一致性 | 需要公司專屬 workaround | 完全一致（結構來自 edgartools） |
| Heading 正確性 | 依賴 font-size/bold heuristic | H1/H2 保證正確，H3 靠 ALL CAPS |
| HTML parsing | 需要 BeautifulSoup | 不需要 |
| 維護成本 | 每家新公司可能需要新 heuristic | 零 |
| Table 格式 | 保留（透過 HTML→MD 轉換） | 丟失（純文字） |

---

## 補充：`tenk[key]` 用於 Agent Tool

與 pipeline 無關，但一併記錄：`tenk[key]` 在所有測試公司都正確回傳 section 內容，零 ToC 污染，可直接取代現有 `_extract_section()` 的 `text.find()` 做法。

```python
# 現有做法（命中 ToC stub）
text = filing.text()
section = _extract_section(text, start_markers, end_markers)  # ToC 污染

# 新做法（結構化存取）
tenk = filing.obj()
section = tenk["1A"]  # 直接拿到 Risk Factors 完整內容
```
