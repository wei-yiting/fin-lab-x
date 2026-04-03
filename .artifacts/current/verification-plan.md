# Verification Plan

## Meta

- Scenarios Reference: `.artifacts/current/bdd-scenarios.md`
- Generated: 2026-04-03

---

## Automated Verification

### Deterministic

> This is a backend data pipeline with no UI. All scenarios use script-based deterministic verification. Callers are batch scripts and agent tools — verification exercises the Python API directly.

#### S-dl-01: Cache determines whether SEC is contacted
- **Method**: script
- **Steps**:
  1. Setup: ensure `data/sec_filings/NVDA/10-K/2024.md` exists (pre-saved fixture)
  2. Call `process("NVDA", "10-K", fiscal_year=2024)` — assert it returns ParsedFiling without triggering download (mock or spy on SECDownloader)
  3. Delete `data/sec_filings/AAPL/10-K/2023.md` if exists
  4. Call `process("AAPL", "10-K", fiscal_year=2023)` — assert SECDownloader was called, file now exists at expected path
  5. Call `process("NVDA", "10-K")` (no fiscal_year) — assert edgartools was contacted to resolve year, then cache was checked
- **Expected**: Cache hit skips download; cache miss triggers full pipeline; omitted fiscal_year contacts SEC for resolution before cache check

#### S-dl-02: Batch processes multiple tickers with mixed outcomes
- **Method**: script
- **Steps**:
  1. Pre-cache NVDA 10-K FY2024
  2. Ensure AAPL FY2023 is not cached
  3. Call `process_batch(["NVDA", "AAPL", "FAKECORP"], "10-K")`
  4. Assert result is `Dict[str, Result]` with exactly 3 keys
  5. Assert `result["NVDA"].status == "success"` and `result["NVDA"].from_cache == True`
  6. Assert `result["AAPL"].status == "success"` and `result["AAPL"].filing` is a valid ParsedFiling
  7. Assert `result["FAKECORP"].status == "error"` and error message contains "FAKECORP"
  8. Verify `data/sec_filings/AAPL/10-K/2023.md` was created
- **Expected**: Per-ticker results with clear status; successful downloads preserved despite FAKECORP failure

#### S-dl-03: Non-calendar fiscal year companies store with correct fiscal_year
- **Method**: script
- **Steps**:
  1. Call `process("NVDA", "10-K")` — let it resolve and download the latest 10-K
  2. Read the saved file's frontmatter: `store.get("NVDA", FilingType.TEN_K, [POST-CODING: determine NVDA's latest fiscal_year from edgartools])`
  3. Assert `fiscal_year` in frontmatter matches edgartools' fiscal year for NVDA (company convention, not calendar year)
  4. Assert the storage path uses the same fiscal year value
  5. Repeat for MSFT to cover a different fiscal year end (June)
- **Expected**: fiscal_year in path and metadata aligns with edgartools/company convention for non-calendar FY companies

#### S-dl-04: "Latest" returns most recently filed 10-K
- **Method**: script
- **Steps**:
  1. Call `process("NVDA", "10-K")` without fiscal_year
  2. Separately query edgartools for NVDA's latest 10-K filing to get the expected fiscal year
  3. Assert the returned ParsedFiling's `fiscal_year` matches the edgartools query result
  4. Assert the filing exists at the expected path `data/sec_filings/NVDA/10-K/{expected_fy}.md`
- **Expected**: Omitting fiscal_year returns the most recently filed 10-K per edgartools

#### S-dl-05: Invalid inputs produce distinct, actionable error types
- **Method**: script
- **Steps**:
  1. Call `process("NVDAA", "10-K")` — assert raises `[POST-CODING: exact error class name]` with "NVDAA" in message
  2. Call `process("TSM", "10-K")` — assert raises a different error class indicating no 10-K filings (not "ticker not found")
  3. Call `process("NVDA", "10-K", fiscal_year=1985)` — assert raises filing-not-found error with "1985" in message
  4. Call `process("AAPL", "10-Q")` — assert raises unsupported-filing-type error listing supported types
  5. Assert all four error types are distinct classes (or have distinct error codes)
- **Expected**: Each invalid input produces a distinguishable, actionable error — not a generic exception

#### S-dl-06: Lowercase and uppercase tickers produce identical results
- **Method**: script
- **Steps**:
  1. Call `process("NVDA", "10-K", fiscal_year=2024)` — save result
  2. Call `process("nvda", "10-K", fiscal_year=2024)` — save result
  3. Assert both return the same ParsedFiling (same content, same path)
  4. Assert only one directory exists: `data/sec_filings/NVDA/` (uppercase)
  5. Assert `data/sec_filings/nvda/` does NOT exist (on case-sensitive filesystem)
  6. Call `store.get("nvda", FilingType.TEN_K, 2024)` — assert returns same filing (store normalizes too)
- **Expected**: Ticker normalized to uppercase at pipeline and store level; no duplicate directories

#### S-dl-07: Overlapping writes to same filing produce a complete, valid file
- **Method**: script
- **Steps**:
  1. Ensure AAPL 10-K FY2024 is not cached
  2. Launch two concurrent calls: `process("AAPL", "10-K", fiscal_year=2024)` in parallel (e.g., via `asyncio.gather` or `concurrent.futures`)
  3. Wait for both to complete
  4. Read `data/sec_filings/AAPL/10-K/2024.md`
  5. Assert the file has valid YAML frontmatter (parseable, all fields present)
  6. Assert the Markdown body is non-empty and contains heading structure
  7. Assert `store.get("AAPL", FilingType.TEN_K, 2024)` returns a valid ParsedFiling
- **Expected**: File is complete and valid regardless of write ordering; no corruption from concurrent access

> **S-dl-08/S-dl-09 (retry mechanism) demoted to unit test**: Batch retry (silent, max 3, exponential backoff) and JIT fail-fast behavior require mocking SEC HTTP responses, making them unit tests by nature. The error type distinction is already covered by S-dl-05 using real SEC calls. Unit tests should verify: (1) batch retries transient 503 up to 3 times then reports error, (2) JIT raises TransientError immediately on 503, (3) permanent 404 errors are never retried in either mode.

#### S-dl-08: force=True bypasses cache and re-processes
- **Method**: script
- **Steps**:
  1. Process NVDA 10-K FY2024 normally — file saved with `parsed_at: T1`
  2. Record the original `parsed_at` and `converter` values from frontmatter
  3. Call `process("NVDA", "10-K", fiscal_year=2024, force=True)`
  4. Read the file again
  5. Assert `parsed_at` has changed (T2 > T1)
  6. Assert the file contains valid Markdown (re-processed, not just timestamp update)
  7. Verify SECDownloader was called (not served from cache)
- **Expected**: force=True bypasses exists() check, re-downloads, and overwrites the cached file

---

### Deterministic — Preprocessing

#### S-prep-01: Nested XBRL tags stripped with all text content preserved
- **Method**: script
- **Steps**:
  1. Create test HTML strings for each table row case (simple number, nested, section-wrapping)
  2. Pass each through `HTMLPreprocessor.preprocess()`
  3. Assert output matches expected (no `ix:` namespace tags, all text content present)
  4. Assert no orphaned closing tags remain
- **Expected**: XBRL tags unwrapped at all nesting levels; text content intact

#### S-prep-02: Style stripping distinguishes decorative from structural
- **Method**: script
- **Steps**:
  1. Create test HTML with decorative styles (font-family, color) and semantic styles (text-align)
  2. Pass through `HTMLPreprocessor.preprocess()`
  3. Assert decorative styles are removed
  4. Assert `text-align` on table cells is preserved
  5. Create HTML with `<div style="display:none">hidden content</div>`
  6. Assert the entire div is removed (not just style stripped)
- **Expected**: Decorative CSS removed; text-align preserved; hidden elements fully removed

#### S-prep-03: Older filings with font-tag content are not emptied
- **Method**: script
- **Steps**:
  1. Create test HTML mimicking a pre-2010 filing: `<body><font style="..." size="4"><b>Item 1</b></font><font style="...">50,000 words of content</font></body>`
  2. Pass through `HTMLPreprocessor.preprocess()`
  3. Assert output contains "Item 1" and "50,000 words of content"
  4. Assert output is NOT empty
  5. Assert `<font>` tags are unwrapped (removed but children kept)
- **Expected**: Content-bearing font tags unwrapped; output non-empty

---

### Deterministic — Conversion

#### S-conv-01: Filings with semantic HTML headings convert to ATX Markdown headings
- **Method**: script
- **Steps**:
  1. Create preprocessed HTML: `<h2>Item 1: Business</h2><p>Content</p><h2>Item 1A: Risk Factors</h2><h3>Market Competition</h3>`
  2. Convert via `HtmlToMarkdownAdapter`
  3. Assert output contains `## Item 1: Business`, `## Item 1A: Risk Factors`, `### Market Competition` in order
  4. Assert headings use ATX format (start with `#`), not Setext
- **Expected**: h-tags become ATX Markdown headings preserving hierarchy

#### S-conv-02: Filings with styled-p headings still produce heading hierarchy
- **Method**: script (end-to-end through preprocessor + converter)
- **Steps**:
  1. Create HTML where headings are `<p><b><font size="4">ITEM 1. BUSINESS</font></b></p>` (no h-tags)
  2. Pass through full pipeline: `HTMLPreprocessor.preprocess()` → `converter.convert()`
  3. Assert the Markdown output contains "ITEM 1. BUSINESS" as a heading with `#` prefix
  4. Assert at least one ATX heading exists in the output
  5. `[POST-CODING: determine how the preprocessor/converter handles styled-p heading inference — this may require a heading detection step]`
- **Expected**: Styled-p headings detected and converted to ATX Markdown headings through the pipeline

#### S-conv-03: Converter fallback triggers correctly
- **Method**: script
- **Steps**:
  1. **Import-time**: `[POST-CODING: mock ImportError for html-to-markdown module]` → instantiate pipeline → assert markdownify is the active converter
  2. **Invocation error**: `[POST-CODING: mock html-to-markdown to raise RuntimeError on convert()]` → process a filing → assert output saved with `converter: markdownify`
  3. **Silent failure (empty/whitespace)**: `[POST-CODING: mock html-to-markdown to return "" or whitespace]` → process a filing → assert fallback triggered, output saved with `converter: markdownify` and non-empty body
- **Expected**: All three failure modes correctly trigger fallback to markdownify. Ratio-based size thresholds are not used — preprocessing legitimately reduces HTML size significantly.

#### S-conv-04: Same input produces ATX headings from both adapters
- **Method**: script
- **Steps**:
  1. Create preprocessed HTML with `<h2>Item 7: Management's Discussion</h2><p>Content here</p>`
  2. Convert via `HtmlToMarkdownAdapter` → capture output A
  3. Convert via `MarkdownifyAdapter` → capture output B
  4. Assert output A contains `## Item 7: Management's Discussion` (ATX)
  5. Assert output B contains `## Item 7: Management's Discussion` (ATX)
  6. Assert neither output contains Setext-style heading underlines (`---` or `===`)
- **Expected**: Both adapters produce ATX-style headings for consistent downstream parsing

---

### Deterministic — Filing Store

#### S-store-01: save/exists/get/list_filings are consistent
- **Method**: script
- **Steps**:
  1. Create a fresh LocalFilingStore with a temp directory
  2. Save TSLA 10-K FY2024 filing
  3. Assert `exists("TSLA", FilingType.TEN_K, 2024)` returns True
  4. Assert `get("TSLA", FilingType.TEN_K, 2024)` returns ParsedFiling with valid frontmatter
  5. Assert `exists("TSLA", FilingType.TEN_K, 2023)` returns False
  6. Assert `get("TSLA", FilingType.TEN_K, 2023)` returns None
  7. Save NVDA for FY2024, 2023, 2022
  8. Assert `list_filings("NVDA", FilingType.TEN_K)` returns `[2024, 2023, 2022]` (as a set, order may vary)
  9. Assert `list_filings("MSFT", FilingType.TEN_K)` returns `[]`
- **Expected**: All four operations reflect consistent state

#### S-store-02: First save creates directories automatically
- **Method**: script
- **Steps**:
  1. Create a fresh LocalFilingStore with a temp directory (no subdirectories)
  2. Save TSLA 10-K FY2024
  3. Assert `{store_root}/TSLA/10-K/` directory exists
  4. Assert `{store_root}/TSLA/10-K/2024.md` file exists and is non-empty
- **Expected**: Intermediate directories created on first write

#### S-store-03: list_filings ignores non-filing files
- **Method**: script
- **Steps**:
  1. Create a LocalFilingStore and save NVDA 10-K FY2024 and FY2023
  2. Manually create `.DS_Store` and `2024.md.tmp` in `{store_root}/NVDA/10-K/`
  3. Call `list_filings("NVDA", FilingType.TEN_K)`
  4. Assert result is `[2024, 2023]` — no `.DS_Store`, no `.tmp` file
- **Expected**: Only `{year}.md` files with valid integer year stems are included

#### S-store-04: Frontmatter with special characters survives roundtrip
- **Method**: script
- **Steps**:
  1. Create ParsedFiling objects for: MCO (Moody's Corporation), T (AT&T Inc.), TROW (T. Rowe Price Group, Inc.)
  2. Save each via `store.save()`
  3. Read back each via `store.get()`
  4. Assert `company_name` in the returned object exactly matches the original (apostrophes, ampersands, commas preserved)
  5. Read the raw `.md` file and verify the YAML frontmatter is valid (parseable by PyYAML)
- **Expected**: Special characters in company names do not corrupt YAML serialization

#### S-store-05: All required metadata fields present and correctly typed
- **Method**: script
- **Steps**:
  1. Process NVDA 10-K FY2024 through the full pipeline (or create a fixture)
  2. Call `store.get("NVDA", FilingType.TEN_K, 2024)`
  3. Assert all fields present: `ticker` (str), `cik` (str), `company_name` (str), `filing_type` (str), `filing_date` (str, ISO date), `fiscal_year` (int), `accession_number` (str, dashed format), `source_url` (str, URL), `parsed_at` (str, ISO 8601 with timezone), `converter` (str, one of "html-to-markdown" or "markdownify")
  4. Assert `parsed_at` ends with "Z" or contains "+00:00" (UTC)
  5. Assert `ticker` is uppercase
  6. Assert `cik` is a string (not int), preserving format from edgartools
- **Expected**: All metadata fields present, correctly typed, and following the contract

---

### Deterministic — Journey Scenarios

#### J-dl-01: Batch pre-load followed by cache-only re-run
- **Method**: script
- **Steps**:
  1. Ensure no filings cached for NVDA, AAPL, TSLA
  2. Call `process_batch(["NVDA", "AAPL", "TSLA"], "10-K")` — record download count
  3. Assert 3 successes in result dict; 3 files created in store
  4. Call `process_batch(["NVDA", "AAPL", "TSLA"], "10-K")` again
  5. Assert 3 successes; verify SECDownloader was NOT called (0 downloads in second run)
  6. Compare `parsed_at` timestamps — should be identical between runs (files not re-processed)
- **Expected**: First run downloads 3 filings; second run serves all from cache with zero SEC contact

#### J-dl-02: Agent JIT cache miss → download → cache hit
- **Method**: script
- **Steps**:
  1. Ensure MSFT 10-K is not cached
  2. Call `process("MSFT", "10-K")` (no fiscal_year) — assert returns ParsedFiling
  3. Record the fiscal_year from the returned filing's metadata
  4. Call `process("MSFT", "10-K")` again
  5. Assert second call returns the same filing from cache (same `parsed_at`, no download)
  6. Call `process("MSFT", "10-K", fiscal_year=<recorded_fy>)` — assert also returns from cache
- **Expected**: JIT download succeeds; subsequent calls (with or without fiscal_year) served from cache

#### J-dl-03: Force re-process corrects bad cached output
- **Method**: script
- **Steps**:
  1. Process NVDA 10-K FY2024 normally — assert file saved
  2. `[POST-CODING: manually corrupt the saved .md file — replace body with empty string or garbage HTML]`
  3. Call `process("NVDA", "10-K", fiscal_year=2024)` (without force) — assert returns the corrupted content (cache hit)
  4. Call `process("NVDA", "10-K", fiscal_year=2024, force=True)` — assert returns valid ParsedFiling
  5. Assert `parsed_at` has been updated (more recent than original)
  6. Assert Markdown body is non-empty and contains heading structure
- **Expected**: Without force, bad cache is served; with force, filing is re-processed and corrected

#### J-prep-01: Real filing HTML through full preprocess produces intact content
- **Method**: script
- **Steps**:
  1. Download a real 10-K HTML for NVDA FY2024 via edgartools
  2. Record the visible text length of the raw HTML (strip tags, count chars)
  3. Pass through `HTMLPreprocessor.preprocess()`
  4. Record the visible text length of preprocessed HTML
  5. Assert preprocessed text length is at least 80% of original (no massive content loss)
  6. Assert no `<ix:` namespace tags remain
  7. Assert output is non-empty
- **Expected**: Preprocessing preserves content volume; XBRL tags removed; output substantial

#### J-conv-01: Full pipeline with mixed content produces structured Markdown
- **Method**: script
- **Steps**:
  1. Call `process("NVDA", "10-K", fiscal_year=2024)` through the full pipeline
  2. Read the saved `.md` file
  3. Assert YAML frontmatter is valid and contains all required fields
  4. Assert Markdown body contains at least 3 ATX headings (`##` or `###`)
  5. Assert Markdown body contains at least 1 table (lines with `|` separators)
  6. Assert no residual HTML tags (`<div>`, `<span>`, `<ix:`) in body
  7. Assert body length > 10KB (a real 10-K should produce substantial Markdown)
- **Expected**: Full pipeline produces rich, structured Markdown with headings, tables, and clean text

#### J-store-01: Multi-ticker filing lifecycle through the store
- **Method**: script
- **Steps**:
  1. Create fresh LocalFilingStore
  2. Process and save NVDA FY2024, NVDA FY2023, AAPL FY2024
  3. Assert `list_filings("NVDA", FilingType.TEN_K)` returns `[2024, 2023]`
  4. Assert `list_filings("AAPL", FilingType.TEN_K)` returns `[2024]`
  5. Get NVDA FY2024 and AAPL FY2024 — assert different `ticker`, `cik`, `company_name`
  6. Get NVDA FY2024 and NVDA FY2023 — assert same `ticker` but different `fiscal_year`, `filing_date`
- **Expected**: Store correctly isolates filings by ticker and fiscal year; metadata is ticker-specific

---

## Manual Verification

### Manual Behavior Test

> Tests requiring real SEC network calls or conditions that cannot be reliably mocked.

#### S-dl-07: Overlapping writes to same filing (with real SEC calls)
- **Reason**: True concurrency with real network I/O is difficult to mock reliably; real SEC latency creates the actual race window
- **Steps**:
  1. Delete cached AAPL 10-K FY2024 if exists
  2. Open two terminal sessions
  3. In both, run `process("AAPL", "10-K", fiscal_year=2024)` simultaneously (within 1 second of each other)
  4. After both complete, inspect `data/sec_filings/AAPL/10-K/2024.md`
  5. Verify the file has valid YAML frontmatter and non-empty Markdown body
- **Expected**: File is valid regardless of which process "won" the write

#### S-dl-05: Invalid inputs produce distinct errors (with real SEC)
- **Reason**: Error type distinction for permanent errors is testable against real SEC; confirms edgartools' error propagation end-to-end
- **Steps**:
  1. Call `process("DEFINITELYNOTAREALTICKER12345", "10-K")` — expect "ticker not found" error
  2. Call `process("TSM", "10-K")` — expect "no 10-K filings" error (distinct from ticker not found)
  3. Verify both produce clear, distinct, actionable error messages
- **Expected**: Real SEC permanent errors produce distinguishable error types

### User Acceptance Test

> User validates that the pipeline's output meets requirements for downstream RAG use.

#### J-conv-01: Full pipeline output quality check
- **Acceptance Question**: Does the parsed Markdown faithfully represent the 10-K filing content in a RAG-friendly format?
- **Steps**:
  1. Process 3-5 real tickers (NVDA, AAPL, MSFT) for their latest 10-K
  2. Open each `.md` file in a Markdown viewer (e.g., VS Code preview, Obsidian)
  3. Verify: heading hierarchy matches the original 10-K sections (Item 1, 1A, 7, 7A, 8)
  4. Verify: financial tables are readable (numbers aligned, columns distinguishable)
  5. Verify: no residual HTML tags, XBRL artifacts, or garbled text
  6. Verify: frontmatter metadata matches SEC filing details
  7. Compare output from html-to-markdown vs markdownify for one filing: are headings consistent (both ATX)?
- **Expected**: Clean, structured Markdown that a human can read and a MarkdownNodeParser can chunk into meaningful sections

#### S-prep-03 / S-conv-02: Older filing preprocessing quality
- **Acceptance Question**: Does the pipeline handle older SEC filings (pre-2015) without destroying content?
- **Steps**:
  1. Process 2-3 older filings (e.g., AAPL FY2010, GE FY2008) — filings likely to use `<font>` tags instead of semantic headings
  2. Open the `.md` files and inspect
  3. Verify: content is present (not empty or near-empty)
  4. Verify: some heading structure exists (even if imperfect for very old filings)
  5. Note any filings where heading detection failed completely — these are known limitations to document
- **Expected**: Content preserved for older filings; heading detection is best-effort for pre-semantic-HTML filings
