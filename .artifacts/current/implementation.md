# Implementation Plan: SEC 10-K Download & Parsing Pipeline

> Design Reference: [design.md](./design.md)
> BDD Scenarios: [bdd-scenarios.md](./bdd-scenarios.md)
> Verification Plan: [verification-plan.md](./verification-plan.md)

**Goal:** 建立 SEC 10-K filing 的 download + parsing pipeline，產出 RAG-friendly 的 Markdown 中間格式（帶 YAML frontmatter），供未來 v2 ingestion consume。

**Architecture / Key Decisions:** Pipeline 由四個 component 串接：SECDownloader（edgartools）→ HTMLPreprocessor（rule-based cleaning + heading promotion）→ HTMLToMarkdownConverter（html-to-markdown primary / markdownify fallback）→ LocalFilingStore（filesystem `.md` files）。SEC 10-K filing HTML **沒有 `<h>` 標籤**（modern filings 用 styled `<div><span font-weight:700>` 表示 heading，older filings 用 `<font><b>`），因此 preprocessor 必須包含 heading promotion 步驟，辨識 SEC Item patterns 並轉換為 `<h>` 標籤，才能讓 converter 產出正確的 ATX Markdown headings。

**Tech Stack:** Python 3.11+, edgartools (>=5.17.1), html-to-markdown (>=3.0.2,<4.0.0), markdownify (>=1.2.0), BeautifulSoup4, PyYAML, Pydantic, pytest

---

## Dependencies Verification

| Dependency | Version | Source | What Was Verified | Notes |
| --- | --- | --- | --- | --- |
| edgartools | >=5.17.1 (installed) | Live investigation | `Company(ticker)` → `get_filings(form='10-K')` → `.latest()` → `.html()` returns raw filing HTML; `period_of_report` string gives FY end date; `CompanyNotFoundError` for invalid tickers; `filings.latest()` returns `None` for empty results | No `fiscal_year` attribute — derive from `period_of_report[:4]` |
| html-to-markdown | >=3.0.2,<4.0.0 | Context7 `/kreuzberg-dev/html-to-markdown` | `convert(html, ConversionOptions(heading_style="atx"))` — default heading_style is "underlined", must set "atx" explicitly; `strip_tags` option available | Rust-based, ~208 MB/s; lacks linux-aarch64 wheel |
| markdownify | >=1.2.0 | Context7 `/matthewwithanm/python-markdownify` | `markdownify(html, heading_style=ATX)` — default is UNDERLINED; import `ATX` from markdownify | Pure Python fallback |
| beautifulsoup4 | >=4.12.0 | Known API | HTML parsing for preprocessor; `soup.find_all()`, `tag.unwrap()`, `tag.decompose()` | Already an edgartools transitive dependency |
| pyyaml | >=6.0.2 (installed) | Known API | YAML frontmatter serialization/deserialization | Already a project dependency |
| pydantic | >=2.0 | Known API | `BaseModel` for `FilingMetadata`, `ParsedFiling` validation | Already used in codebase |

## Constraints

- SEC rate limit: 10 req/sec（edgartools 內建 rate limiting）
- `html-to-markdown` 缺 linux-aarch64 wheel — Docker 需 `--platform linux/amd64`；fallback to markdownify
- SEC HTML 格式不統一：modern filings 用 styled `<div>/<span>`，older filings 用 `<font>/<b>` — preprocessor 必須處理兩種
- 不碰 `backend/agent_engine/tools/sec.py`（existing tool，不在 scope 內）
- `data/sec_filings/` 目錄結構不 commit（加入 `.gitignore`），fixture 檔案另外管理

---

## Investigation Findings: SEC HTML Structure

在寫 plan 前，實際下載並分析了多份 SEC 10-K filing HTML：

### Modern Filing (NVDA FY2026, filed 2026-02-25)
- HTML 大小：~2MB
- **零 `<h>` 標籤** — 所有 heading 都是 `<div><span style="font-weight:700;font-size:10pt">Item 1. Business</span></div>`
- 開頭有 `<div style="display:none"><ix:header>...</ix:header></div>` 包含 XBRL metadata（含 `dei:DocumentFiscalYearFocus`）
- 大量 `<ix:nonFraction>`, `<ix:nonNumeric>` inline XBRL tags
- 大量 decorative inline styles（font-family, font-size, color, padding）

### Older Filing (AAPL FY2010, filed 2010-10-27)
- HTML 大小：~1.3MB
- `<h5>` 僅用於 "Table of Contents" navigation links
- 實際 heading：`<FONT STYLE="font-family:Times New Roman" SIZE="2"><B>Item 1. Business</B></FONT>`
- 8949 個 `<font>` 標籤、426 個 `<b>` 標籤
- 包含 SEC cover page（"UNITED STATES SECURITIES AND EXCHANGE COMMISSION"）— 這是 filing 自身內容，非 EDGAR viewer chrome

### EDGAR Boilerplate Rule Resolution
- **edgartools 回傳的是 raw filing HTML**，不是 EDGAR viewer page
- **不需要** EDGAR boilerplate removal rule
- **需要**移除 hidden XBRL metadata div（`<div style="display:none">` containing `<ix:header>`）

### Fiscal Year Resolution
- `period_of_report` 是 string（如 "2026-01-25"）
- fiscal_year = `int(period_of_report[:4])`
- NVDA: period=2026-01-25 → FY2026；MSFT: period=2025-06-30 → FY2025；AAPL: period=2025-09-27 → FY2025

### Error Behavior
- Invalid ticker → `edgar.CompanyNotFoundError`
- Valid ticker, no 10-K → `filings.latest()` returns `None`（TSM: 0 filings, no exception）
- Specific fiscal year → `filings.filter(date='YYYY-01-01:YYYY+1-01-01')` 再 `.latest()`

---

## File Plan

| Operation | Path | Purpose |
| --- | --- | --- |
| Create | `backend/ingestion/__init__.py` | Ingestion package init |
| Create | `backend/ingestion/sec_filing_pipeline/__init__.py` | Package init, re-export public API |
| Create | `backend/ingestion/sec_filing_pipeline/filing_models.py` | `FilingType` enum, `FilingMetadata`, `ParsedFiling`, custom exceptions |
| Create | `backend/ingestion/sec_filing_pipeline/sec_downloader.py` | `SECDownloader` — edgartools wrapper |
| Create | `backend/ingestion/sec_filing_pipeline/html_preprocessor.py` | `HTMLPreprocessor` — rule-based HTML cleaning + heading promotion |
| Create | `backend/ingestion/sec_filing_pipeline/html_to_md_converter.py` | `HTMLToMarkdownConverter` protocol, `HtmlToMarkdownAdapter`, `MarkdownifyAdapter`, factory |
| Create | `backend/ingestion/sec_filing_pipeline/filing_store.py` | `FilingStore` protocol, `LocalFilingStore` — filesystem persistence |
| Create | `backend/ingestion/sec_filing_pipeline/pipeline.py` | `SECFilingPipeline` — orchestrator with `process()` / `process_batch()` |
| Create | `backend/tests/ingestion/__init__.py` | Ingestion test package |
| Create | `backend/tests/ingestion/sec_filing_pipeline/__init__.py` | Test package |
| Create | `backend/tests/ingestion/sec_filing_pipeline/test_filing_models.py` | Model validation tests |
| Create | `backend/tests/ingestion/sec_filing_pipeline/test_html_preprocessor.py` | Preprocessor unit tests (S-prep-01, S-prep-02, S-prep-03) |
| Create | `backend/tests/ingestion/sec_filing_pipeline/test_html_to_md_converter.py` | Converter unit tests (S-conv-01, S-conv-02, S-conv-04) |
| Create | `backend/tests/ingestion/sec_filing_pipeline/test_filing_store.py` | Store unit tests (S-store-01 through S-store-05) |
| Create | `backend/tests/ingestion/sec_filing_pipeline/test_sec_downloader.py` | Downloader unit tests (error mapping) |
| Create | `backend/tests/ingestion/sec_filing_pipeline/test_pipeline.py` | Pipeline integration tests (S-dl-01 through S-dl-10, journey scenarios) |
| Create | `backend/tests/ingestion/sec_filing_pipeline/conftest.py` | Shared fixtures (sample HTML, temp store dirs) |
| Update | `pyproject.toml` | Add html-to-markdown, markdownify, beautifulsoup4 dependencies |
| Update | `.gitignore` | Add `data/sec_filings/` |

**Structure sketch:**

```text
backend/
  ingestion/
    __init__.py
    sec_filing_pipeline/
      __init__.py
      filing_models.py
      sec_downloader.py
      html_preprocessor.py
      html_to_md_converter.py
      filing_store.py
      pipeline.py
  tests/
    ingestion/
      __init__.py
      sec_filing_pipeline/
        __init__.py
        conftest.py
        test_filing_models.py
        test_html_preprocessor.py
        test_html_to_md_converter.py
        test_filing_store.py
        test_sec_downloader.py
        test_pipeline.py
data/
  sec_filings/          ← runtime output, gitignored
    {TICKER}/10-K/{fiscal_year}.md
```

---

### Task 1: Project Setup — Dependencies & Models

**Files:**

- Update: `pyproject.toml`
- Update: `.gitignore`
- Create: `backend/ingestion/__init__.py`
- Create: `backend/ingestion/sec_filing_pipeline/__init__.py`
- Create: `backend/ingestion/sec_filing_pipeline/filing_models.py`
- Create: `backend/tests/ingestion/__init__.py`
- Create: `backend/tests/ingestion/sec_filing_pipeline/__init__.py`
- Create: `backend/tests/ingestion/sec_filing_pipeline/conftest.py`
- Create: `backend/tests/ingestion/sec_filing_pipeline/test_filing_models.py`

**What & Why:** 建立 package 骨架、安裝 dependencies、定義所有 shared types（`FilingType` enum, `FilingMetadata`, `ParsedFiling`, custom exceptions）。這些 types 被所有後續 task 依賴，必須先定義。

**Critical Contract:**

```python
# backend/ingestion/sec_filing_pipeline/filing_models.py
from enum import StrEnum
from pydantic import BaseModel, Field
from datetime import datetime

class FilingType(StrEnum):
    TEN_K = "10-K"

class FilingMetadata(BaseModel):
    ticker: str
    cik: str
    company_name: str
    filing_type: FilingType
    filing_date: str          # ISO date "YYYY-MM-DD"
    fiscal_year: int
    accession_number: str     # dashed format "0001045810-24-000029"
    source_url: str
    parsed_at: str            # ISO 8601 UTC "2026-04-03T10:30:00Z"
    converter: str            # "html-to-markdown" or "markdownify"

class ParsedFiling(BaseModel):
    metadata: FilingMetadata
    markdown_content: str

# Custom exceptions
class SECPipelineError(Exception): ...
class TickerNotFoundError(SECPipelineError): ...
class FilingNotFoundError(SECPipelineError): ...
class UnsupportedFilingTypeError(SECPipelineError): ...
class TransientError(SECPipelineError): ...
```

**Test Strategy:** 驗證 `FilingType` enum 值、`FilingMetadata` 的 Pydantic validation（required fields, type constraints）、exception hierarchy。純 model 測試，不需 mock。

**Verification:**

| Scope | Command | Expected Result | Why |
| --- | --- | --- | --- |
| Dependencies | `cd /Users/dong.wyt/Documents/dev-projects/fin-lab-x-sec-download-parsing && uv sync` | Install completes without error, html-to-markdown and markdownify importable | New dependencies installed |
| Tests | `cd /Users/dong.wyt/Documents/dev-projects/fin-lab-x-sec-download-parsing && uv run pytest backend/tests/ingestion/sec_filing_pipeline/test_filing_models.py -v` | All tests pass | Models correctly defined |
| Lint | `cd /Users/dong.wyt/Documents/dev-projects/fin-lab-x-sec-download-parsing && uv run ruff check backend/ingestion/sec_filing_pipeline/` | No errors | Code style OK |

**Execution Checklist:**

- [ ] Add `html-to-markdown>=3.0.2,<4.0.0`, `markdownify>=1.2.0`, `beautifulsoup4>=4.12.0` to `pyproject.toml` dependencies
- [ ] Add `data/sec_filings/` to `.gitignore`
- [ ] Run `uv sync` to install
- [ ] Create `backend/ingestion/__init__.py`, `backend/ingestion/sec_filing_pipeline/__init__.py` and `filing_models.py`
- [ ] Create `backend/tests/ingestion/sec_filing_pipeline/__init__.py` and `conftest.py`
- [ ] 🔴 Write `test_filing_models.py`: FilingType enum values, FilingMetadata validation (happy path + missing fields), exception inheritance hierarchy
- [ ] 🔴 Run tests — confirm they **fail** (module not yet importable or incomplete)
- [ ] 🟢 Complete `filing_models.py` with all types and exceptions
- [ ] 🟢 Run tests — confirm they **pass**
- [ ] 🔵 Review: check Pydantic model field types, exception hierarchy
- [ ] 🔵 Run tests — confirm they **still pass**
- [ ] Run lint: `uv run ruff check backend/ingestion/sec_filing_pipeline/`
- [ ] Commit: `git commit -m "feat(sec-pipeline): add project setup, models, and exceptions"`

---

### Task 2: LocalFilingStore — Filesystem Persistence

**Files:**

- Create: `backend/ingestion/sec_filing_pipeline/filing_store.py`
- Create: `backend/tests/ingestion/sec_filing_pipeline/test_filing_store.py`

**What & Why:** 實作 `FilingStore` protocol 和 `LocalFilingStore`。Store 負責 `.md` 檔案的 save/get/exists/list_filings 操作，含 YAML frontmatter 的序列化/反序列化。Store 是 pipeline 的 persistence layer，其他 component 不直接操作 filesystem。

**Implementation Notes:**

- `save()` 使用 atomic write（寫入 `.tmp` 再 `os.replace`）來防止 concurrent write 導致的 corruption（S-dl-07）
- `save()` 自動 `os.makedirs(exist_ok=True)` 建立目錄（S-store-02）
- `get()` 解析 YAML frontmatter → `FilingMetadata`，body → `markdown_content`
- `list_filings()` 只回傳 stem 是合法整數的 `.md` 檔案（過濾 `.DS_Store`, `.tmp` 等）（S-store-03）
- Ticker 在 store 層 normalize 為 uppercase（S-dl-06）
- YAML serialization 使用 `yaml.dump(default_flow_style=False, allow_unicode=True)` 確保 special chars roundtrip（S-store-04）

**Critical Contract:**

```python
# backend/ingestion/sec_filing_pipeline/filing_store.py
from typing import Protocol, runtime_checkable

@runtime_checkable
class FilingStore(Protocol):
    def save(self, filing: ParsedFiling) -> None: ...
    def get(self, ticker: str, filing_type: FilingType, fiscal_year: int) -> ParsedFiling | None: ...
    def exists(self, ticker: str, filing_type: FilingType, fiscal_year: int) -> bool: ...
    def list_filings(self, ticker: str, filing_type: FilingType) -> list[int]: ...

class LocalFilingStore:
    def __init__(self, base_dir: str = "data/sec_filings") -> None: ...
    # Implements FilingStore protocol
```

**Test Strategy:** 覆蓋 S-store-01 through S-store-05：
- S-store-01: save/exists/get/list_filings 一致性 — 測試 post-save retrieval, non-existent filing, multi-year listing
- S-store-02: 首次 save 自動建立 directory
- S-store-03: list_filings 過濾 `.DS_Store`, `.tmp` 等 non-filing files
- S-store-04: special characters（Moody's, AT&T, T. Rowe Price）YAML roundtrip
- S-store-05: 所有 metadata fields 型別正確
- 全部使用 `tmp_path` fixture，不 mock filesystem

**Verification:**

| Scope | Command | Expected Result | Why |
| --- | --- | --- | --- |
| Tests | `uv run pytest backend/tests/ingestion/sec_filing_pipeline/test_filing_store.py -v` | All tests pass | Store operations correct |
| Lint | `uv run ruff check backend/ingestion/sec_filing_pipeline/filing_store.py` | No errors | Code style OK |

**Execution Checklist:**

- [ ] 🔴 Write `test_filing_store.py` with all S-store scenarios using `tmp_path`
- [ ] 🔴 Run tests — confirm they **fail**
- [ ] 🟢 Implement `LocalFilingStore` in `filing_store.py`
- [ ] 🟢 Run tests — confirm they **pass**
- [ ] 🔵 Review: atomic write, ticker normalization, YAML serialization edge cases
- [ ] 🔵 Run tests — confirm they **still pass**
- [ ] Commit: `git commit -m "feat(sec-pipeline): implement LocalFilingStore with atomic writes"`

---

### Task 3: HTMLPreprocessor — Rule-Based Cleaning + Heading Promotion

**Files:**

- Create: `backend/ingestion/sec_filing_pipeline/html_preprocessor.py`
- Create: `backend/tests/ingestion/sec_filing_pipeline/test_html_preprocessor.py`
- Update: `backend/tests/ingestion/sec_filing_pipeline/conftest.py` (add sample HTML fixtures)

**What & Why:** Preprocessor 是 pipeline 的核心 quality gate。它負責：(1) XBRL tag stripping, (2) decorative style removal, (3) hidden element removal, (4) `<font>` tag unwrapping, (5) **heading promotion** — 將 SEC Item patterns 轉為 `<h>` 標籤。

Heading promotion 是最關鍵的步驟。調查發現 modern 和 older filings 都沒有語義化的 `<h>` 標籤。Preprocessor 必須辨識 SEC 10-K section headers 並插入 `<h2>` / `<h3>` 標籤，converter 才能產出正確的 ATX Markdown headings。

**Approach Decision:**

| Option | Summary | Status | Why |
| --- | --- | --- | --- |
| A: Pattern-based heading promotion | 辨識已知 SEC 10-K Item patterns（PART I/II/III/IV, Item 1/1A/1B/2...15），用 regex 比對 text content，promote 到 `<h2>`/`<h3>` | Selected | SEC 10-K 結構標準化，pattern 有限且已知；比 font-size heuristic 更可靠 |
| B: Font-size heuristic | 根據 font-size / font-weight 推斷 heading level | Rejected | 不同公司用不同 font-size 表示 heading，threshold 難以通用化 |

**Implementation Notes:**

- Preprocessor 由一組獨立的 cleaning rules 組成，依序執行：
  1. `strip_xbrl_tags` — unwrap all `<ix:*>` namespace tags，保留 children（S-prep-01）
  2. `remove_hidden_elements` — 移除 `display:none` elements（含 XBRL `<ix:header>` block）（S-prep-02）
  3. `strip_decorative_styles` — 移除 font-family, font-size, color, padding 等 decorative CSS properties；保留 `text-align`（S-prep-02）
  4. `unwrap_font_tags` — unwrap `<font>` tags，保留 children（S-prep-03）
  5. `promote_headings` — 辨識 SEC Item patterns 並轉為 `<h2>`/`<h3>`（S-conv-02 的 prerequisite）
- 使用 BeautifulSoup4 做 HTML manipulation
- Heading promotion 規則：
  - **PART level**：regex `r'PART\s+(I{1,3}V?|IV)\b'` → `<h1>`
  - **Item level**：regex `r'Item\s+\d+[A-Z]?\.' ` → `<h2>`（covers Item 1. through Item 15.）
  - 比對目標：element 的 text content（strip tags 後），且 element 必須帶有 bold signal（`<b>`, `<strong>`, `font-weight:700`, 或 `font-weight:bold`）
  - 將匹配的 parent block element（`<div>`, `<p>`, `<td>`）替換為對應的 `<h>` tag

**Test Strategy:** 覆蓋 S-prep-01, S-prep-02, S-prep-03 的所有 table rows，加上 heading promotion 測試：
- S-prep-01: XBRL tags（simple, nested, section-wrapping）unwrap 後 text 完整
- S-prep-02: decorative styles 移除、text-align 保留、hidden elements 完整移除
- S-prep-03: `<font>` tag unwrap 不丟失 content（模擬 pre-2010 filing）
- Heading promotion: known Item patterns → `<h2>`; PART patterns → `<h1>`; non-heading bold text 不被錯誤 promote
- 全部用 construct HTML string 做 input，assert output 的 structure

**Verification:**

| Scope | Command | Expected Result | Why |
| --- | --- | --- | --- |
| Tests | `uv run pytest backend/tests/ingestion/sec_filing_pipeline/test_html_preprocessor.py -v` | All tests pass | All cleaning rules work correctly |
| Lint | `uv run ruff check backend/ingestion/sec_filing_pipeline/html_preprocessor.py` | No errors | Code style OK |

**Execution Checklist:**

- [ ] 🔴 Write `test_html_preprocessor.py`: XBRL stripping, style stripping, hidden element removal, font unwrap, heading promotion (happy path + edge cases)
- [ ] 🔴 Run tests — confirm they **fail**
- [ ] 🟢 Implement `HTMLPreprocessor` with all 5 rules
- [ ] 🟢 Run tests — confirm they **pass**
- [ ] 🔵 Review: rule ordering, regex patterns, edge cases (empty text, deeply nested XBRL)
- [ ] 🔵 Run tests — confirm they **still pass**
- [ ] Commit: `git commit -m "feat(sec-pipeline): implement HTMLPreprocessor with heading promotion"`

---

### Task 4: HTMLToMarkdownConverter — Dual Adapter with Fallback

**Files:**

- Create: `backend/ingestion/sec_filing_pipeline/html_to_md_converter.py`
- Create: `backend/tests/ingestion/sec_filing_pipeline/test_html_to_md_converter.py`

**What & Why:** 實作 converter protocol 和兩個 adapter。`HtmlToMarkdownAdapter` 是 primary（Rust-based, 極快），`MarkdownifyAdapter` 是 fallback。Factory function 處理 import-time fallback 和 invocation-time fallback（S-conv-03）。

**Implementation Notes:**

- `HTMLToMarkdownConverter` protocol 只有一個 method: `convert(html: str) -> str`，加上 `name` property 回傳 converter 名稱
- `HtmlToMarkdownAdapter`:
  - `convert()` 呼叫 `html_to_markdown.convert(html, ConversionOptions(heading_style="atx"))`
  - 名稱回傳 `"html-to-markdown"`
- `MarkdownifyAdapter`:
  - `convert()` 呼叫 `markdownify.markdownify(html, heading_style=markdownify.ATX)`
  - 名稱回傳 `"markdownify"`
- `create_converter()` factory:
  - 嘗試 import `html_to_markdown`；失敗 → 回傳 `MarkdownifyAdapter`
  - 成功 → 回傳 `HtmlToMarkdownAdapter`
- `convert_with_fallback(html, primary, fallback)` function:
  - 呼叫 primary converter；catch exception → 改用 fallback
  - 檢查 output 是否為空或 suspiciously small（< 1% of input length）→ 改用 fallback
  - 回傳 `(markdown_str, converter_name)` tuple

**Test Strategy:** 覆蓋 S-conv-01, S-conv-03, S-conv-04：
- S-conv-01: preprocessed HTML 含 `<h2>`, `<h3>` → converter 產出 ATX headings
- S-conv-04: 兩個 adapter 對同一 input 都產出 ATX headings
- S-conv-03: 四種 fallback condition（import error, runtime error, empty output, tiny output）
- Fallback tests mock `html_to_markdown` module 的不同 failure modes

**Verification:**

| Scope | Command | Expected Result | Why |
| --- | --- | --- | --- |
| Tests | `uv run pytest backend/tests/ingestion/sec_filing_pipeline/test_html_to_md_converter.py -v` | All tests pass | Both adapters and fallback logic work |
| Lint | `uv run ruff check backend/ingestion/sec_filing_pipeline/html_to_md_converter.py` | No errors | Code style OK |

**Execution Checklist:**

- [ ] 🔴 Write `test_html_to_md_converter.py`: ATX heading output, both adapters, all 4 fallback conditions
- [ ] 🔴 Run tests — confirm they **fail**
- [ ] 🟢 Implement `html_to_md_converter.py` with protocol, both adapters, factory, and fallback logic
- [ ] 🟢 Run tests — confirm they **pass**
- [ ] 🔵 Review: ConversionOptions settings, fallback threshold, error handling
- [ ] 🔵 Run tests — confirm they **still pass**
- [ ] Commit: `git commit -m "feat(sec-pipeline): implement HTMLToMarkdownConverter with fallback"`

---

### Flow Verification: Preprocessing + Conversion Chain

> Tasks 3-4 完成 preprocessing → conversion 的 data transformation chain。
> 這兩個 component 的整合必須驗證 end-to-end 的 heading preservation。

| # | Method | Step | Expected Result |
| --- | --- | --- | --- |
| 1 | Script (in test) | 建立模擬 modern filing HTML（styled `<div><span font-weight:700>Item 1. Business</span></div>` + XBRL tags + decorative styles），通過 preprocessor → converter | Markdown output 包含 `## Item 1. Business` ATX heading |
| 2 | Script (in test) | 建立模擬 older filing HTML（`<FONT><B>Item 1. Business</B></FONT>` + `<font>` tags），通過 preprocessor → converter | Markdown output 包含 `## Item 1. Business` ATX heading，無殘留 `<font>` tags |
| 3 | Script (in test) | 驗證 S-conv-02 完整場景：no-h-tag HTML → preprocessor heading promotion → converter → ATX heading output | 至少一個 `##` heading 在 output 中 |

- [ ] All flow verifications pass（在 `test_html_to_md_converter.py` 中加入 integration tests）

---

### Task 5: SECDownloader — edgartools Wrapper

**Files:**

- Create: `backend/ingestion/sec_filing_pipeline/sec_downloader.py`
- Create: `backend/tests/ingestion/sec_filing_pipeline/test_sec_downloader.py`

**What & Why:** SECDownloader 封裝 edgartools 的 API，提供統一的 download interface 並處理 error mapping。將 edgartools 的各種 exception 和 return 值轉換為 pipeline 的 custom exceptions。

**Implementation Notes:**

- `download(ticker, filing_type, fiscal_year=None)` method:
  - Normalize ticker to uppercase
  - Validate filing_type against `FilingType` enum → `UnsupportedFilingTypeError`
  - `Company(ticker)` → catch `CompanyNotFoundError` → raise `TickerNotFoundError`
  - `company.get_filings(form=filing_type.value)`
  - 如果 `fiscal_year` 指定：`filings.filter(date='{fy-1}-01-01:{fy+1}-01-01')` 尋找包含該 FY 的 filing
  - 如果 `fiscal_year` 省略：`filings.latest()`
  - Result 是 `None` → raise `FilingNotFoundError`
  - 取得 `filing.html()`, `filing.period_of_report`, `filing.filing_date`, `filing.accession_no`
  - 組裝 `RawFiling` dataclass（html + metadata）
- `RawFiling` 包含 raw HTML string + 所有 metadata fields（ticker, cik, company_name, filing_date, fiscal_year, accession_number, source_url）
- fiscal_year 從 `period_of_report` 推導：`int(str(filing.period_of_report)[:4])`
- 如果 `fiscal_year` 有指定但 download 到的 filing 的 fiscal_year 不 match → raise `FilingNotFoundError`

**Test Strategy:** Mock edgartools 來測試所有 error paths（S-dl-05 的 error mapping）：
- `CompanyNotFoundError` → `TickerNotFoundError`
- `filings.latest()` returns `None` → `FilingNotFoundError`
- `filing_type` not in `FilingType` → `UnsupportedFilingTypeError`
- Specific fiscal year not found → `FilingNotFoundError`
- Happy path: returns `RawFiling` with correct metadata
- Mock 的是 edgartools 的 `Company`, `set_identity`，不 mock pipeline 自己的邏輯

**Verification:**

| Scope | Command | Expected Result | Why |
| --- | --- | --- | --- |
| Tests | `uv run pytest backend/tests/ingestion/sec_filing_pipeline/test_sec_downloader.py -v` | All tests pass | Error mapping and metadata extraction correct |
| Lint | `uv run ruff check backend/ingestion/sec_filing_pipeline/sec_downloader.py` | No errors | Code style OK |

**Execution Checklist:**

- [ ] 🔴 Write `test_sec_downloader.py`: happy path, all 4 error types from S-dl-05, fiscal_year resolution
- [ ] 🔴 Run tests — confirm they **fail**
- [ ] 🟢 Implement `SECDownloader` in `sec_downloader.py`
- [ ] 🟢 Run tests — confirm they **pass**
- [ ] 🔵 Review: error mapping completeness, fiscal_year derivation logic
- [ ] 🔵 Run tests — confirm they **still pass**
- [ ] Commit: `git commit -m "feat(sec-pipeline): implement SECDownloader with error mapping"`

---

### Task 6: SECFilingPipeline — Orchestrator

**Files:**

- Create: `backend/ingestion/sec_filing_pipeline/pipeline.py`
- Update: `backend/ingestion/sec_filing_pipeline/__init__.py` (re-export public API)
- Create: `backend/tests/ingestion/sec_filing_pipeline/test_pipeline.py`

**What & Why:** Pipeline 串接所有 component（downloader → preprocessor → converter → store），提供 `process()` 和 `process_batch()` entry points。這是 BDD scenarios 的主要測試對象。

**Implementation Notes:**

- `SECFilingPipeline.__init__()` 接收所有 dependencies（downloader, preprocessor, converter, fallback_converter, store）；提供 `create()` class method 用 default 組裝
- `process(ticker, filing_type, fiscal_year=None, force=False)`:
  1. Normalize ticker to uppercase
  2. Validate filing_type
  3. 如果 `fiscal_year` 指定且 `not force` → `store.exists()` check → cache hit 直接 `store.get()` 回傳
  4. 如果 `fiscal_year` 省略 → call downloader 取得 latest（即使 cache 裡有，也需要先 resolve fiscal_year）；resolve 後再 check cache
  5. Cache miss 或 `force=True` → download → preprocess → convert_with_fallback → 組裝 `ParsedFiling` → `store.save()`
  6. 回傳 `ParsedFiling`
- `process_batch(tickers, filing_type)`:
  - 對每個 ticker 呼叫 `process()`，捕獲 exception
  - Transient errors（HTTP 503 等）: retry up to 3 times with exponential backoff（S-dl-08）
  - Permanent errors: 不 retry（S-dl-09）
  - 回傳 `dict[str, BatchResult]`，每個 entry 有 status, filing (optional), error (optional), from_cache flag
- JIT mode（direct `process()` call）不做 retry — raise exception 讓 caller 決定（S-dl-08）
- `BatchResult` dataclass: `status: Literal["success", "error"]`, `filing: ParsedFiling | None`, `error: str | None`, `from_cache: bool`

**Test Strategy:** 這是最大的 test file，覆蓋大部分 BDD scenarios：
- S-dl-01: cache hit / cache miss / omitted fiscal_year（mock downloader + store）
- S-dl-02: batch mixed outcomes（mock downloader to succeed for 2, fail for 1）
- S-dl-03: fiscal_year 從 `period_of_report` 正確推導（mock downloader metadata）
- S-dl-04: omitted fiscal_year returns latest filed 10-K（mock downloader）
- S-dl-06: lowercase ticker → same cache path（via store normalization）
- S-dl-07: concurrent writes produce valid file — 依賴 Task 2 的 atomic write，在 integration test 中驗證
- S-dl-08: batch retries transient errors; JIT raises（mock downloader to raise `TransientError`）
- S-dl-09: permanent errors not retried（mock downloader to raise `FilingNotFoundError`）
- S-dl-10: `force=True` bypasses cache（mock store.exists to return True, assert downloader still called）
- Unit tests mock downloader / preprocessor / converter / store 來測試 orchestration logic
- Distinct from integration tests which use real components

**Verification:**

| Scope | Command | Expected Result | Why |
| --- | --- | --- | --- |
| Tests | `uv run pytest backend/tests/ingestion/sec_filing_pipeline/test_pipeline.py -v` | All tests pass | Pipeline orchestration correct |
| Full suite | `uv run pytest backend/tests/ingestion/sec_filing_pipeline/ -v` | All tests across all modules pass | No regressions |
| Lint | `uv run ruff check backend/ingestion/sec_filing_pipeline/` | No errors | Code style OK |

**Execution Checklist:**

- [ ] 🔴 Write `test_pipeline.py`: S-dl-01 (cache behavior), S-dl-02 (batch), S-dl-06 (ticker normalization), S-dl-08 (retry/no-retry), S-dl-09 (permanent errors), S-dl-10 (force)
- [ ] 🔴 Run tests — confirm they **fail**
- [ ] 🟢 Implement `SECFilingPipeline` in `pipeline.py`
- [ ] 🟢 Run tests — confirm they **pass**
- [ ] 🔵 Review: cache logic, retry logic, batch error handling, force flag
- [ ] 🔵 Run tests — confirm they **still pass**
- [ ] Update `__init__.py` to re-export public API: `SECFilingPipeline`, `ParsedFiling`, `FilingType`, exceptions
- [ ] Run full test suite: `uv run pytest backend/tests/ingestion/sec_filing_pipeline/ -v`
- [ ] Commit: `git commit -m "feat(sec-pipeline): implement SECFilingPipeline orchestrator"`

---

### Flow Verification: Full Pipeline (Unit Level)

> Tasks 1-6 完成整個 pipeline 的 unit-level 實作。所有 component 透過 mock 測試整合正確。

| # | Method | Step | Expected Result |
| --- | --- | --- | --- |
| 1 | Script | `uv run pytest backend/tests/ingestion/sec_filing_pipeline/ -v` | 所有 unit tests pass |
| 2 | Script | `uv run ruff check backend/ingestion/sec_filing_pipeline/` | No lint errors |
| 3 | Script | `uv run python -c "from backend.ingestion.sec_filing_pipeline import SECFilingPipeline, ParsedFiling, FilingType"` | Import succeeds, public API accessible |

- [ ] All flow verifications pass

---

### Task 7: Integration Tests — Real SEC Data

**Files:**

- Update: `backend/tests/ingestion/sec_filing_pipeline/test_pipeline.py` (add integration test class)
- Update: `pyproject.toml` (add `sec_integration` pytest marker)

**What & Why:** 使用真實 SEC data 驗證 full pipeline end-to-end。這些 tests 需要 network access 並標記為 `sec_integration` marker，預設不執行（避免 CI 中 hit SEC API）。覆蓋 journey scenarios 和 output quality。

**Implementation Notes:**

- 新增 pytest marker: `sec_integration` — 預設 exclude（`addopts` 加 `-m 'not eval and not sec_integration'`）
- 使用 `tmp_path` 作為 store base_dir，避免污染 `data/`
- 每個 integration test 使用真實 `SECFilingPipeline.create()` 組裝，只 override store 的 base_dir

**Test Strategy:** 覆蓋 journey scenarios + output quality checks：
- J-dl-01: batch pre-load 3 tickers → re-run → all from cache
- J-dl-02: JIT cache miss → download → cache hit on follow-up
- J-dl-03: force re-process corrects cached output
- J-prep-01: real filing HTML preprocessed — text content preserved (>80% of original visible text)
- J-conv-01: full pipeline output — YAML frontmatter valid, ATX headings present, tables present, no residual HTML/XBRL tags, body > 10KB
- J-store-01: multi-ticker lifecycle
- S-dl-03: non-calendar FY companies（NVDA, MSFT）fiscal_year 正確
- S-dl-07: concurrent writes — launch 2 parallel `process()` calls, verify file valid

**Verification:**

| Scope | Command | Expected Result | Why |
| --- | --- | --- | --- |
| Integration | `EDGAR_IDENTITY="YI-TING WEI yiting.wei.tina@gmail.com" uv run pytest backend/tests/ingestion/sec_filing_pipeline/test_pipeline.py -m sec_integration -v --timeout=120` | All integration tests pass | Full pipeline works with real SEC data |
| Unit (no regression) | `uv run pytest backend/tests/ingestion/sec_filing_pipeline/ -v` | All unit tests still pass | Integration additions don't break units |

**Execution Checklist:**

- [ ] Add `sec_integration` marker to `pyproject.toml`
- [ ] 🔴 Write integration tests in `test_pipeline.py`（separate class with `@pytest.mark.sec_integration`）
- [ ] 🔴 Run integration tests — confirm they **fail**（pipeline not fully wired or SEC network issues）
- [ ] 🟢 Fix any integration issues discovered（typically: edgartools API nuances, HTML edge cases, fiscal_year derivation）
- [ ] 🟢 Run integration tests — confirm they **pass**
- [ ] 🔵 Review: test isolation (tmp_path), test stability (SEC availability), output quality assertions
- [ ] 🔵 Run full suite（unit + integration）— confirm they **still pass**
- [ ] Commit: `git commit -m "test(sec-pipeline): add integration tests with real SEC data"`

---

### Flow Verification: End-to-End Pipeline with Real SEC Data

> Task 7 完成後，驗證 pipeline 對真實 SEC 資料的 end-to-end 行為。

| # | Method | Step | Expected Result |
| --- | --- | --- | --- |
| 1 | Runtime invocation | `EDGAR_IDENTITY="..." uv run python -c "from backend.ingestion.sec_filing_pipeline import SECFilingPipeline, FilingType; p = SECFilingPipeline.create(); r = p.process('NVDA', FilingType.TEN_K); print(f'FY={r.metadata.fiscal_year}, len={len(r.markdown_content)}, converter={r.metadata.converter}')"` | 印出 FY=2026, len>10000, converter=html-to-markdown |
| 2 | Runtime invocation | 再次執行同一 command | 從 cache 回傳（速度明顯更快，無 SEC network call） |
| 3 | Runtime invocation | `uv run python -c "from backend.ingestion.sec_filing_pipeline import SECFilingPipeline, FilingType; p = SECFilingPipeline.create(); r = p.process_batch(['NVDA', 'AAPL', 'FAKECORP'], FilingType.TEN_K); print({k: v.status for k, v in r.items()})"` | `{'NVDA': 'success', 'AAPL': 'success', 'FAKECORP': 'error'}` |
| 4 | File inspection | 打開 `data/sec_filings/NVDA/10-K/{fy}.md`，檢查：(a) YAML frontmatter 完整、(b) ATX headings 存在、(c) 無殘留 HTML tags、(d) 內容可讀 | Clean, structured Markdown with correct metadata |

- [ ] All flow verifications pass

---

## Pre-delivery Checklist

### Code Level (TDD)

- [ ] All unit tests pass: `uv run pytest backend/tests/ingestion/sec_filing_pipeline/ -v`
- [ ] All integration tests pass: `EDGAR_IDENTITY="..." uv run pytest backend/tests/ingestion/sec_filing_pipeline/ -m sec_integration -v`
- [ ] Lint passes: `uv run ruff check backend/ingestion/sec_filing_pipeline/`
- [ ] Format passes: `uv run ruff format --check backend/ingestion/sec_filing_pipeline/`
- [ ] Type check passes: `uv run pyright backend/ingestion/sec_filing_pipeline/`

### Flow Level (Behavioral)

- [ ] All flow verification steps executed and passed
- [ ] Flow: Preprocessing + Conversion Chain — PASS / FAIL
- [ ] Flow: Full Pipeline (Unit Level) — PASS / FAIL
- [ ] Flow: End-to-End Pipeline with Real SEC Data — PASS / FAIL

### Summary

- [ ] Both levels pass → ready for delivery
- [ ] Any failure is documented with cause and next action
