# BDD Scenarios

## Meta
- Design Reference: `.artifacts/current/design.md`
- Generated: 2026-04-03
- Discovery Method: Three Amigos (Agent Teams)

---

## Feature: SEC Filing Download & Caching

### Context
Pipeline downloads 10-K filings from SEC via edgartools, preprocesses HTML, converts to Markdown, and caches locally. Supports batch pre-load (script) and just-in-time (agent tool) modes with different error handling strategies.

### Rule: Pipeline checks cache before downloading

#### S-dl-01: Cache determines whether SEC is contacted
> Verifies cache-first behavior: cached filings skip download; cache misses trigger full pipeline; omitting fiscal_year requires SEC resolution first

- **Given** the filing store state for `<ticker>` 10-K `<fiscal_year>` is `<cache_state>`
- **When** `process("<ticker>", "10-K", <fiscal_year_arg>)` is called
- **Then** `<expected_behavior>`

| ticker | fiscal_year | fiscal_year_arg | cache_state | expected_behavior | notes |
|--------|-------------|-----------------|-------------|-------------------|-------|
| NVDA | 2024 | fiscal_year=2024 | cached | Returns cached ParsedFiling; SECDownloader not called | explicit year, cache hit |
| AAPL | 2023 | fiscal_year=2023 | not cached | Downloads from SEC, preprocesses, converts, saves, returns ParsedFiling | explicit year, cache miss |
| NVDA | 2024 | omitted | cached | Contacts edgartools to resolve latest year (2024), then returns cached filing | omitted year requires SEC metadata call before cache check |
| TSLA | 2024 | omitted | not cached | Contacts edgartools to resolve latest year, then downloads, processes, saves | omitted year, full pipeline |

Category: Illustrative (table-driven)
Origin: Multiple (PO seeded, Dev challenged fiscal_year omission, QA challenged resolution side effect)

### Rule: Batch returns per-ticker structured results

#### S-dl-02: Batch processes multiple tickers with mixed outcomes
> Verifies batch returns a Dict[str, Result] where each ticker has its own status, ParsedFiling, and error info

- **Given** `process_batch(["NVDA", "AAPL", "FAKECORP"], "10-K")` where NVDA is cached, AAPL is not cached, and FAKECORP has no SEC filings
- **When** the batch completes
- **Then** the result is a Dict with 3 entries: NVDA (success, from cache), AAPL (success, freshly downloaded), FAKECORP (failure, "no 10-K filings found")
- **And** NVDA and AAPL have valid ParsedFiling objects; FAKECORP has an error with actionable message

Category: Illustrative
Origin: Multiple (PO seeded, Dev challenged partial failure, QA challenged result contract)

### Rule: Fiscal year resolves correctly for all company types

#### S-dl-03: Non-calendar fiscal year companies store with correct fiscal_year
> Verifies that companies with non-calendar fiscal years have the correct fiscal_year in the storage path and metadata

- **Given** `<ticker>` has a fiscal year ending `<fy_end_date>` and edgartools reports fiscal_year as `<edgartools_fy>`
- **When** `process("<ticker>", "10-K")` completes
- **Then** the filing is stored at `data/sec_filings/<ticker>/10-K/<edgartools_fy>.md` with `fiscal_year: <edgartools_fy>` in frontmatter

| ticker | fy_end_date | edgartools_fy | notes |
|--------|-------------|---------------|-------|
| NVDA | 2025-01-26 | 2025 | FY ends January; edgartools convention followed |
| MSFT | 2024-06-30 | 2024 | FY ends June |
| AAPL | 2024-09-28 | 2024 | FY ends September |

Category: Illustrative (table-driven)
Origin: Dev (fiscal year extraction reliability)

#### S-dl-04: "Latest" returns most recently filed 10-K
> Verifies that omitting fiscal_year returns the latest available filing, not a future unfiled one

- **Given** today is January 15, 2025, and NVDA's most recent filed 10-K is for FY2024 (filed Feb 2024), with FY2025 10-K not yet filed
- **When** `process("NVDA", "10-K")` is called without fiscal_year
- **Then** the pipeline returns the FY2024 filing (the latest actually filed), not an error about FY2025

Category: Illustrative
Origin: Dev (fiscal year boundary ambiguity)

### Rule: Pipeline rejects invalid inputs with actionable errors

#### S-dl-05: Invalid inputs produce distinct, actionable error types
> Verifies that different error conditions produce distinguishable errors so callers (agent tools) can respond appropriately

- **Given** `<input_condition>`
- **When** `process("<ticker>", "<filing_type>", <fiscal_year>)` is called
- **Then** the pipeline raises `<error_type>` with a message containing `<key_info>`

| input_condition | ticker | filing_type | fiscal_year | error_type | key_info | notes |
|-----------------|--------|-------------|-------------|------------|----------|-------|
| Ticker not in SEC | NVDAA | 10-K | omitted | TickerNotFoundError | "NVDAA" | typo, not a real ticker |
| Valid ticker, no 10-K (foreign filer) | TSM | 10-K | omitted | FilingNotFoundError | "TSM", "10-K" | TSM files 20-F, not 10-K |
| Valid ticker, FY doesn't exist | NVDA | 10-K | 1985 | FilingNotFoundError | "NVDA", "1985" | predates SEC filings |
| Unsupported filing type | AAPL | 10-Q | omitted | UnsupportedFilingTypeError | "10-Q", supported types | 10-Q not in FilingType enum |

Category: Illustrative (table-driven)
Origin: Multiple (Dev: error distinction + FilingType enforcement, QA: TSM + FY1985)

### Rule: Ticker case is normalized to uppercase

#### S-dl-06: Lowercase and uppercase tickers produce identical results
> Verifies that ticker normalization happens at the pipeline entry point, preventing duplicate directories

- **Given** NVDA 10-K FY2024 was previously processed via `process("NVDA", "10-K", 2024)`
- **When** `process("nvda", "10-K", 2024)` is called with lowercase ticker
- **Then** the pipeline returns the cached filing from `data/sec_filings/NVDA/10-K/2024.md` (uppercase path)
- **And** no duplicate directory `data/sec_filings/nvda/` is created

Category: Illustrative
Origin: QA (ticker case normalization), Dev (store-level normalization)

### Rule: Concurrent batch and JIT writes produce valid output

#### S-dl-07: Overlapping writes to same filing produce a complete, valid file
> Verifies that when batch and JIT target the same ticker/year simultaneously, the stored file is never corrupted

- **Given** no cached file exists for AAPL 10-K FY2024
- **When** a batch script processing AAPL and an agent JIT call for AAPL run concurrently
- **Then** the file at `data/sec_filings/AAPL/10-K/2024.md` is a complete, valid ParsedFiling (not truncated or interleaved)
- **And** `store.get("AAPL", FilingType.TEN_K, 2024)` returns parseable content

Category: Illustrative
Origin: Dev (race condition, contested and upgraded), QA (batch+JIT overlap)

### Rule: Transient and permanent SEC errors are distinguishable

> **Note**: The retry mechanism itself (batch silent retry vs JIT fail-fast, exponential backoff, retry count) is tested at the unit test level via mocks, since SEC error responses cannot be controlled in integration tests. The BDD scenario below verifies the observable behavior with real SEC calls: that different error conditions produce distinguishable error types so callers can decide whether to retry.

*See S-dl-05 for the full error type distinction table, which covers both permanent errors (ticker not found, no 10-K, non-existent FY) and unsupported filing types — all testable with real SEC calls.*

### Rule: Cache recovery via force re-process

#### S-dl-08: force=True bypasses cache and re-processes
> Verifies that callers can force re-processing of a previously cached filing

- **Given** NVDA 10-K FY2024 is cached with `converter: markdownify` (from a previous fallback)
- **When** `process("NVDA", "10-K", fiscal_year=2024, force=True)` is called after html-to-markdown is now available
- **Then** the pipeline re-downloads, re-preprocesses, and re-converts the filing
- **And** the cached file is overwritten with `converter: html-to-markdown` and updated `parsed_at`

Category: Illustrative
Origin: Dev (save overwrite semantics), QA (bad cached content persists), User decision

---

### Journey Scenarios

#### J-dl-03: Force re-process corrects bad cached output
> Proves the cache recovery flow: bad output is detected, force re-processes, and produces corrected output

- **Given** NVDA 10-K FY2024 was previously cached but the Markdown body is empty (converter silent failure at the time)
- **When** a user detects the issue during manual inspection
- **And** calls `process("NVDA", "10-K", fiscal_year=2024, force=True)`
- **Then** the pipeline re-downloads and re-processes the filing
- **And** the cached file is replaced with a valid ParsedFiling containing Markdown with heading structure

Category: Journey
Origin: Multiple (Dev: overwrite semantics, QA: bad cached content, User: force=True)

---

## Feature: HTML Preprocessing

### Context
Preprocessor cleans SEC-specific HTML noise (XBRL inline tags, decorative styles, hidden elements) while preserving content and structural signals needed by the Markdown converter. The preprocessor must be aware that downstream heading detection depends on certain style attributes.

### Rule: XBRL tags are unwrapped, preserving all inner content

#### S-prep-01: Nested XBRL tags stripped with all text content preserved
> Verifies that XBRL inline tags are unwrapped (children kept) regardless of nesting depth

- **Given** HTML containing `<xbrl_pattern>`
- **When** the preprocessor runs
- **Then** the output contains `<expected_output>`

| xbrl_pattern | expected_output | notes |
|--------------|-----------------|-------|
| `<ix:nonFraction contextRef="c-1" name="us-gaap:Revenues">47525000000</ix:nonFraction>` | `47525000000` | simple number wrapping |
| `<ix:nonNumeric contextRef="c-1"><p>Revenue was <ix:nonFraction>47525</ix:nonFraction> million</p></ix:nonNumeric>` | `<p>Revenue was 47525 million</p>` | nested XBRL, both layers unwrapped |
| `<ix:nonNumeric name="dei:EntityDescription"><h2>Item 1: Business</h2><p>NVIDIA designs GPUs...</p></ix:nonNumeric>` | `<h2>Item 1: Business</h2><p>NVIDIA designs GPUs...</p>` | section-wrapping XBRL, children preserved |

Category: Illustrative (table-driven)
Origin: Multiple (PO seeded, Dev challenged nesting, QA challenged section-wrapping)

### Rule: Decorative styles removed, semantic styles preserved

#### S-prep-02: Style stripping distinguishes decorative from structural
> Verifies that purely decorative CSS properties are removed while layout-meaningful ones are preserved

- **Given** HTML containing `<element>`
- **When** the preprocessor runs
- **Then** the output is `<expected>`

| element | expected | notes |
|---------|----------|-------|
| `<p style="font-family:Times New Roman; font-size:10pt; color:#000">Revenue grew 125%</p>` | `<p>Revenue grew 125%</p>` | decorative styles stripped, text preserved |
| `<td style="text-align:right; padding-left:4px; font-family:Arial">$47,525</td>` | `<td style="text-align:right">$47,525</td>` | text-align preserved for table formatting |
| `<div style="display:none">SEC metadata block</div>` | *(removed entirely)* | hidden element removed with all children |

Category: Illustrative (table-driven)
Origin: Multiple (PO seeded, Dev challenged legitimate styles, QA challenged table alignment)

### Rule: Content-bearing elements are unwrapped, not deleted

#### S-prep-03: Older filings with font-tag content are not emptied by preprocessing
> Verifies that font/span tags carrying visible content are unwrapped (tag removed, children kept), not deleted

- **Given** a pre-2010 filing where the document body contains `<font style="font-family:Times New Roman" size="4"><b>Item 1: Business</b></font><font style="font-family:Times New Roman">NVIDIA designs and sells GPUs for gaming and data centers...</font>`
- **When** the preprocessor runs
- **Then** the output preserves all text content: `<b>Item 1: Business</b>NVIDIA designs and sells GPUs for gaming and data centers...`
- **And** the output is NOT empty

Category: Illustrative
Origin: Multiple (Dev: unwrap vs remove, QA: empty document after aggressive preprocessing)

### Rule: EDGAR boilerplate removal [UNCERTAIN — deferred to Implementation Planning]

> This rule's necessity depends on whether edgartools returns raw filing HTML (without EDGAR viewer chrome) or the full EDGAR viewer page. To be verified during Implementation Planning by actually fetching sample filings. If edgartools returns raw filing HTML only, this rule is unnecessary and should be removed.

---

### Journey Scenarios

#### J-prep-01: Real filing HTML through full preprocess produces intact content
> Proves the preprocessor preserves all meaningful content through the full cleaning pipeline

- **Given** a real 10-K filing HTML for NVDA FY2024 (containing XBRL inline tags, inline styles, and hidden metadata elements)
- **When** the full preprocessing pipeline runs (all cleaning rules applied sequentially)
- **Then** the output HTML contains all visible text content from the original
- **And** no XBRL namespace tags remain
- **And** the output is not empty or significantly shorter than the original visible text

Category: Journey
Origin: Multiple

---

## Feature: Markdown Conversion & Output Quality

### Context
Converter transforms preprocessed HTML to Markdown, preserving heading hierarchy for downstream RAG chunking. Two adapters available: html-to-markdown (Rust, primary) and markdownify (Python, fallback). Both must produce ATX-style headings for consistency.

### Rule: Heading hierarchy is preserved in output

#### S-conv-01: Filings with semantic HTML headings convert to ATX Markdown headings
> Verifies that standard h1-h6 tags become ATX-style Markdown headings in correct order

- **Given** preprocessed HTML containing `<h2>Item 1: Business</h2>` followed by `<h2>Item 1A: Risk Factors</h2>` followed by `<h3>Market Competition</h3>`
- **When** the converter processes the HTML
- **Then** the Markdown output contains `## Item 1: Business`, `## Item 1A: Risk Factors`, and `### Market Competition` in that order

Category: Illustrative
Origin: PO

#### S-conv-02: Filings with styled-p headings still produce heading hierarchy
> Verifies end-to-end that the preprocessor preserves enough structural signal for the converter to identify headings in older filings

- **Given** a filing where section headers are `<p><b><font size="4">ITEM 1. BUSINESS</font></b></p>` with no h1-h6 tags
- **When** the full pipeline runs (preprocess → convert)
- **Then** the Markdown output has "ITEM 1. BUSINESS" as a heading (ATX format), not as a plain paragraph
- **And** the document has at least one `#`/`##` heading in the output

Category: Illustrative
Origin: Multiple (Dev: styled-p headings, QA: no-heading filings, QA: preprocessor/converter ordering conflict)

### Rule: Converter falls back gracefully at import-time and invocation-time

#### S-conv-03: Converter fallback triggers correctly
> Verifies that the pipeline falls back to markdownify under various failure conditions

- **Given** `<failure_condition>`
- **When** a filing is processed through the conversion step
- **Then** `<expected_behavior>` and the frontmatter records `converter: <converter_used>`

| failure_condition | expected_behavior | converter_used | notes |
|-------------------|-------------------|----------------|-------|
| html-to-markdown cannot be imported (linux-aarch64, no wheel) | markdownify used for all conversions from startup | markdownify | import-time fallback |
| html-to-markdown raises exception on specific HTML input | markdownify used for that filing only | markdownify | invocation-time fallback |
| html-to-markdown returns empty string or whitespace-only output | Detected as silent failure; markdownify used for that filing | markdownify | silent failure detection |

> **Note**: Fallback triggers on exception, empty output, or whitespace-only output. Ratio-based size thresholds (e.g., output < X% of input) are intentionally excluded — HTML preprocessing legitimately strips large amounts of XBRL/style noise, so a small output relative to raw HTML does not indicate converter failure. Content quality (e.g., missing sections) is validated by UAT manual inspection, not by automated fallback.

Category: Illustrative (table-driven)
Origin: Multiple (Dev: import vs invocation, Dev: silent failure, QA: threshold definition, User: Q3 decision)

### Rule: Both converters produce ATX-style headings

#### S-conv-04: Same input produces ATX headings from both adapters
> Verifies that both html-to-markdown and markdownify produce `## Heading` format (not Setext `Heading\n------`)

- **Given** a preprocessed HTML snippet containing `<h2>Item 7: Management's Discussion</h2>`
- **When** the same HTML is converted by HtmlToMarkdownAdapter and by MarkdownifyAdapter separately
- **Then** both outputs contain `## Item 7: Management's Discussion` (ATX format)
- **And** neither output uses Setext-style headings

Category: Illustrative
Origin: Dev (converter normalization, contested and upgraded by User Q4 decision)

---

### Journey Scenarios

#### J-conv-01: Full pipeline with mixed content produces structured Markdown
> Proves the complete pipeline preserves document structure through all stages

- **Given** a real 10-K filing HTML containing headings, paragraphs, financial tables, and XBRL inline tags
- **When** the full pipeline runs: download → preprocess → convert → save
- **Then** the saved Markdown file has YAML frontmatter with all required fields
- **And** the Markdown body contains ATX headings reflecting the filing's section structure
- **And** financial tables are present as Markdown tables
- **And** no residual HTML tags or XBRL namespace tags remain in the body

Category: Journey
Origin: Multiple

---

## Feature: Filing Store & Output Contract

### Context
LocalFilingStore persists ParsedFilings as .md files with YAML frontmatter at `data/sec_filings/{ticker}/{filing_type}/{fiscal_year}.md`. Store operations must be consistent, handle real-world filesystem conditions, and produce correctly typed metadata.

### Rule: Store operations are mutually consistent

#### S-store-01: save/exists/get/list_filings are consistent with each other
> Verifies that all four store operations reflect the same state

- **Given** `<precondition>`
- **When** `<operation>` is called
- **Then** `<expected_result>`

| precondition | operation | expected_result | notes |
|--------------|-----------|-----------------|-------|
| TSLA 10-K FY2024 saved | `exists("TSLA", FilingType.TEN_K, 2024)` | `True` | post-save existence |
| TSLA 10-K FY2024 saved | `get("TSLA", FilingType.TEN_K, 2024)` | Returns ParsedFiling with valid frontmatter | post-save retrieval |
| No TSLA FY2023 saved | `exists("TSLA", FilingType.TEN_K, 2023)` | `False` | non-existent filing |
| No TSLA FY2023 saved | `get("TSLA", FilingType.TEN_K, 2023)` | `None` | non-existent filing |
| NVDA FY2024, 2023, 2022 saved | `list_filings("NVDA", FilingType.TEN_K)` | Returns `[2024, 2023, 2022]` | list all fiscal years |
| No MSFT filings saved | `list_filings("MSFT", FilingType.TEN_K)` | Returns `[]` | empty list |

Category: Illustrative (table-driven)
Origin: PO

### Rule: Store creates directories automatically on first save

#### S-store-02: First save for a new ticker creates the directory structure
> Verifies that save() creates intermediate directories when they don't exist

- **Given** `data/sec_filings/TSLA/` directory does not exist
- **When** `save()` is called for TSLA 10-K FY2024
- **Then** the directory `data/sec_filings/TSLA/10-K/` is created automatically
- **And** the file `data/sec_filings/TSLA/10-K/2024.md` is written successfully

Category: Illustrative
Origin: Dev (directory auto-creation)

### Rule: list_filings filters non-filing files

#### S-store-03: Non-filing files in the directory are excluded from list results
> Verifies that filesystem artifacts don't pollute list_filings results

- **Given** `data/sec_filings/NVDA/10-K/` contains `2024.md`, `2023.md`, `.DS_Store`, and `2024.md.tmp`
- **When** `list_filings("NVDA", FilingType.TEN_K)` is called
- **Then** the result is `[2024, 2023]` — only valid `{year}.md` files are included

Category: Illustrative
Origin: QA (.DS_Store), QA (temp file orphans)

### Rule: ParsedFiling metadata roundtrips correctly through save/get

#### S-store-04: Frontmatter with special characters survives save/get roundtrip
> Verifies that company names with YAML-problematic characters are serialized and deserialized correctly

- **Given** a ParsedFiling for `<ticker>` with company_name `<company_name>` is saved
- **When** `store.get("<ticker>", FilingType.TEN_K, <year>)` is called
- **Then** the returned ParsedFiling has `company_name` equal to `<company_name>` (exact match)

| ticker | company_name | year | yaml_issue |
|--------|-------------|------|------------|
| MCO | Moody's Corporation | 2024 | apostrophe |
| T | AT&T Inc. | 2024 | ampersand |
| TROW | T. Rowe Price Group, Inc. | 2024 | comma and periods |

Category: Illustrative (table-driven)
Origin: Multiple (QA: YAML special chars, Dev: YAML serializer roundtrip)

#### S-store-05: All required metadata fields are present and correctly typed
> Verifies that a saved ParsedFiling has the complete frontmatter contract

- **Given** NVDA 10-K FY2024 has been processed and saved
- **When** `store.get("NVDA", FilingType.TEN_K, 2024)` is called
- **Then** the frontmatter contains all required fields:
  - `ticker`: "NVDA" (string, uppercase)
  - `cik`: string (e.g., "1045810")
  - `company_name`: string (e.g., "NVIDIA Corporation")
  - `filing_type`: "10-K" (string)
  - `filing_date`: ISO date string
  - `fiscal_year`: 2024 (integer)
  - `accession_number`: string in dashed format (e.g., "0001045810-24-000029")
  - `source_url`: valid URL string
  - `parsed_at`: ISO 8601 UTC datetime with timezone (e.g., "2026-04-03T10:30:00Z")
  - `converter`: "html-to-markdown" or "markdownify" (string)

Category: Illustrative
Origin: PO

---

### Journey Scenarios

#### J-store-01: Multi-ticker filing lifecycle through the store
> Proves store operations work correctly across multiple tickers and fiscal years

- **Given** a fresh (empty) filing store
- **When** filings are saved for NVDA FY2024, NVDA FY2023, and AAPL FY2024
- **And** `list_filings("NVDA", FilingType.TEN_K)` is called
- **And** `get("NVDA", FilingType.TEN_K, 2024)` is called
- **And** `get("AAPL", FilingType.TEN_K, 2024)` is called
- **Then** list_filings returns `[2024, 2023]` for NVDA
- **And** both get() calls return ParsedFilings with correct ticker-specific metadata
- **And** NVDA's filing is distinct from AAPL's (different ticker, cik, company_name)

Category: Journey
Origin: Multiple

---

## Feature: CLI & Agent Tool Entry Points

### Context
Pipeline provides two entry points beyond the Python API: a CLI (`__main__.py`) for human terminal use and batch pre-load scripts, and a LangChain agent tool (`sec_filing_downloader`) for JIT download during agent runtime. Both are thin wrappers over `SECFilingPipeline`. The CLI uses `argparse` and supports single/batch modes with output formatting options. The agent tool returns metadata + file_path for downstream RAG consumption.

### Rule: CLI single mode produces correct summary output

#### S-ep-01: CLI single mode prints concise summary without markdown content
> Verifies that the CLI outputs a one-liner summary to stdout and never prints the full filing content

- **Given** AAPL 10-K is processable
- **When** `python -m backend.ingestion.sec_filing_pipeline AAPL 10-K` is run
- **Then** stdout contains a single line with ticker, fiscal year, parsed_at, content length, and file path
- **And** stdout does NOT contain the full markdown content of the filing

Category: Illustrative
Origin: Task spec ("Never print the full markdown content to stdout")

#### S-ep-02: CLI --json outputs parseable JSON with metadata and file path
> Verifies that --json output is machine-consumable with the complete metadata contract

- **Given** AAPL 10-K is processable
- **When** `python -m backend.ingestion.sec_filing_pipeline AAPL 10-K --json` is run
- **Then** stdout is valid JSON parseable by `json.loads`
- **And** the JSON contains `metadata` (all FilingMetadata fields), `content_length` (integer), and `file_path` (string path)

Category: Illustrative
Origin: Task spec (--json for programmatic consumption)

### Rule: CLI batch mode prints per-ticker results and reflects in exit code

#### S-ep-03: Batch with partial failure prints per-ticker status and exits non-zero
> Verifies that batch mode reports each ticker's outcome individually and exits 1 when any fail

- **Given** AAPL is processable and FAKECORP is not a valid ticker
- **When** `python -m backend.ingestion.sec_filing_pipeline batch AAPL FAKECORP --filing-type 10-K` is run
- **Then** stdout shows AAPL with "ok" status and file path, and FAKECORP with "err" status and error message
- **And** the process exits with code 1

Category: Illustrative
Origin: Task spec (exit code 1 if any fail)

#### S-ep-04: Batch with all success exits with code 0
> Verifies that batch mode exits cleanly when all tickers succeed

- **Given** AAPL and NVDA are both processable
- **When** `python -m backend.ingestion.sec_filing_pipeline batch AAPL NVDA --filing-type 10-K` is run
- **Then** stdout shows both tickers with "ok" status
- **And** the process exits with code 0

Category: Illustrative
Origin: Task spec (exit code 0 if all succeed)

### Rule: CLI error outputs to stderr with non-zero exit code

#### S-ep-05: Invalid ticker produces stderr error and non-zero exit
> Verifies that pipeline errors go to stderr (not stdout) with the error type name

- **Given** ZZZZ is not a valid SEC ticker
- **When** `python -m backend.ingestion.sec_filing_pipeline ZZZZ 10-K` is run
- **Then** stderr contains the error type name (e.g., "TickerNotFoundError") and "ZZZZ"
- **And** stdout is empty
- **And** the process exits with code 1

Category: Illustrative
Origin: Task spec (error to stderr, non-zero exit)

### Rule: Agent tool returns metadata + file_path without raising exceptions

#### S-ep-06: Successful download returns metadata dict with file_path
> Verifies that the agent tool wraps pipeline output into the expected dict contract

- **Given** AAPL 10-K is processable
- **When** `sec_filing_downloader.invoke({"ticker": "AAPL", "filing_type": "10-K"})` is called
- **Then** the return dict contains `ticker`, `company_name`, `fiscal_year`, `filing_date`, `parsed_at`, and `file_path`
- **And** the dict does NOT contain an `error` key
- **And** `file_path` matches `data/sec_filings/AAPL/10-K/{fiscal_year}.md`

Category: Illustrative
Origin: Design (JIT use case, metadata + file_path contract)

#### S-ep-07: Pipeline error returns error dict instead of raising
> Verifies that the agent tool catches pipeline exceptions and returns a structured error

- **Given** ZZZZ is not a valid SEC ticker
- **When** `sec_filing_downloader.invoke({"ticker": "ZZZZ", "filing_type": "10-K"})` is called
- **Then** the return dict contains `{"error": True, "message": "..."}` where message includes the error type name
- **And** no exception is raised to the caller

Category: Illustrative
Origin: Design (agent tool must not crash the agent)

---

### Journey Scenarios

#### J-ep-01: CLI batch pre-load followed by CLI single verify
> Proves the full CLI batch workflow: download multiple filings, then verify individual results via CLI

- **Given** no filings are cached for NVDA, AAPL, or TSLA
- **When** `python -m backend.ingestion.sec_filing_pipeline batch NVDA AAPL TSLA --filing-type 10-K` is run
- **Then** stdout shows 3 "ok" entries with file paths, and the process exits with code 0
- **And** when the same batch command is run again
- **Then** all 3 are served from cache (identical output, zero SEC downloads)
- **And** when `python -m backend.ingestion.sec_filing_pipeline NVDA 10-K --json` is run
- **Then** the JSON output contains the correct metadata matching the batch-cached filing

Category: Journey
Origin: Replaces J-dl-01 (elevated from Python API to CLI entry point)

#### J-ep-02: Agent tool JIT download then cache hit on follow-up
> Proves the JIT flow through the agent tool: first call downloads, second call hits cache

- **Given** no filing exists for MSFT 10-K in the store
- **When** `sec_filing_downloader.invoke({"ticker": "MSFT", "filing_type": "10-K"})` is called
- **Then** the return contains `file_path` and `fiscal_year` (freshly downloaded)
- **And** when `sec_filing_downloader.invoke({"ticker": "MSFT", "filing_type": "10-K"})` is called again
- **Then** the return contains the same `file_path` and `fiscal_year` (from cache)
- **And** no duplicate SEC download occurred

Category: Journey
Origin: Replaces J-dl-02 (elevated from Python API to agent tool entry point)
