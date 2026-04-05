# Executable Verification Plan

## Meta
- Generated from: verification-plan.md + bdd-scenarios.md
- Placeholders resolved: 2026-04-03
- Environment: Docker sandbox (aarch64), html-to-markdown NOT available (Rust build fails), markdownify is fallback
- Cached filings: NVDA 10-K FY2026, AAPL 10-K FY2025

---

## Resolved POST-CODING Placeholders

1. **S-dl-03** `[POST-CODING: determine NVDA's latest fiscal_year from edgartools]` → FY2026 (period_of_report=2026-01-25)
2. **S-dl-05** `[POST-CODING: exact error class name]` → `TickerNotFoundError` (raised when `edgar.CompanyNotFoundError` is caught)
3. **S-conv-02** `[POST-CODING: heading inference]` → `HTMLPreprocessor._promote_headings()` detects bold text matching `PART I/II/III/IV` (→h1) or `Item N.` (→h2) and promotes the enclosing block tag
4. **S-conv-03** mocking:
   - Import-time: `unittest.mock.patch("backend.ingestion.sec_filing_pipeline.html_to_md_converter.HtmlToMarkdownAdapter.convert", side_effect=ImportError)`
   - RuntimeError: `unittest.mock.patch.object(HtmlToMarkdownAdapter, "convert", side_effect=RuntimeError("test"))`
   - Empty output: `unittest.mock.patch.object(HtmlToMarkdownAdapter, "convert", return_value="")`
5. **J-dl-03** `[POST-CODING: corrupt file]` → Overwrite the markdown body portion of the cached .md file with empty string while preserving frontmatter

## Adaptation Notes

- NVDA latest is FY2026, AAPL latest is FY2025 — scenarios adapted from original FY2024/FY2023
- `html-to-markdown` is unavailable in this container; `create_converter()` returns MarkdownifyAdapter
- S-conv-03 import-time fallback tested via `create_converter()` which already returns markdownify
- S-conv-04: HtmlToMarkdownAdapter cannot be tested directly (import fails); test verifies MarkdownifyAdapter produces ATX and that fallback path works

---

## Automated Scenarios

All scenarios below are executed via Python scripts using the project's API directly.

### S-prep-01: Nested XBRL tags stripped
- **Type**: Deterministic
- **Command**: Python script exercising `HTMLPreprocessor.preprocess()` with XBRL test HTML
- **Expected**: XBRL tags unwrapped, all text content preserved

### S-prep-02: Style stripping distinguishes decorative from structural
- **Type**: Deterministic
- **Command**: Python script exercising `HTMLPreprocessor.preprocess()` with styled HTML
- **Expected**: Decorative styles removed, text-align preserved, hidden elements removed

### S-prep-03: Older filings with font-tag content not emptied
- **Type**: Deterministic
- **Command**: Python script with pre-2010 style HTML through `HTMLPreprocessor.preprocess()`
- **Expected**: Content preserved, font tags unwrapped, output non-empty

### S-conv-01: Semantic HTML headings → ATX Markdown
- **Type**: Deterministic
- **Command**: Python script converting `<h2>/<h3>` HTML via MarkdownifyAdapter
- **Expected**: ATX-style `##`/`###` headings in output

### S-conv-02: Styled-p headings → heading hierarchy
- **Type**: Deterministic
- **Command**: Python script: preprocessor + converter pipeline on `<p><b><font>ITEM 1.</font></b></p>` HTML
- **Expected**: ATX heading in output containing "ITEM 1. BUSINESS"

### S-conv-03: Converter fallback triggers correctly
- **Type**: Deterministic
- **Command**: Python script testing 3 fallback modes via `convert_with_fallback()`
- **Expected**: All three failure modes trigger fallback to markdownify

### S-conv-04: Both adapters produce ATX headings
- **Type**: Deterministic
- **Command**: Python script testing MarkdownifyAdapter (and fallback path) for ATX output
- **Expected**: ATX headings, no Setext underlines

### S-store-01: save/exists/get/list_filings consistency
- **Type**: Deterministic
- **Command**: Python script with temp directory LocalFilingStore
- **Expected**: All four operations reflect consistent state

### S-store-02: First save creates directories
- **Type**: Deterministic
- **Command**: Python script saving to empty temp directory
- **Expected**: Intermediate directories auto-created

### S-store-03: list_filings ignores non-filing files
- **Type**: Deterministic
- **Command**: Python script adding .DS_Store and .tmp files to store dir
- **Expected**: Only valid {year}.md files returned

### S-store-04: Frontmatter special characters roundtrip
- **Type**: Deterministic
- **Command**: Python script saving/loading filings with apostrophes, ampersands, commas
- **Expected**: Exact character preservation through save/get

### S-store-05: All required metadata fields present
- **Type**: Deterministic
- **Command**: Python script reading cached NVDA filing and checking all fields
- **Expected**: All 10 metadata fields present with correct types

### S-dl-01: Cache determines whether SEC is contacted
- **Type**: Deterministic
- **Command**: Python script testing cache hit (NVDA FY2026 exists), cache miss, and omitted fiscal_year
- **Expected**: Cache hit skips download; cache miss triggers pipeline; omitted FY contacts SEC

### S-dl-02: Batch processes multiple tickers with mixed outcomes
- **Type**: Deterministic
- **Command**: Python script calling `process_batch(["NVDA", "AAPL", "FAKECORP"], "10-K")`
- **Expected**: Per-ticker results; NVDA/AAPL success, FAKECORP error

### S-dl-03: Non-calendar FY companies store with correct fiscal_year
- **Type**: Deterministic
- **Command**: Python script checking NVDA (FY ends Jan) fiscal_year from edgartools matches stored
- **Expected**: fiscal_year in path/metadata aligns with edgartools convention

### S-dl-04: "Latest" returns most recently filed 10-K
- **Type**: Deterministic
- **Command**: Python script calling process("NVDA", "10-K") without fiscal_year
- **Expected**: Returns latest filed 10-K (FY2026)

### S-dl-05: Invalid inputs produce distinct error types
- **Type**: Deterministic
- **Command**: Python script testing 4 invalid input cases
- **Expected**: TickerNotFoundError, FilingNotFoundError, FilingNotFoundError, UnsupportedFilingTypeError

### S-dl-06: Lowercase/uppercase tickers produce identical results
- **Type**: Deterministic
- **Command**: Python script calling process with "nvda" and "NVDA"
- **Expected**: Same result, no duplicate directory

### S-dl-07: Overlapping writes produce valid file
- **Type**: Deterministic
- **Command**: Python script using concurrent.futures to run two process() calls simultaneously
- **Expected**: File is complete and valid

### S-dl-08: force=True bypasses cache
- **Type**: Deterministic
- **Command**: Python script: process normally, then process with force=True
- **Expected**: parsed_at changes, file re-processed

### J-dl-01: Batch pre-load → cache-only re-run
- **Type**: Deterministic (Journey)
- **Command**: Python script running process_batch twice
- **Expected**: First run downloads; second run all from cache

### J-dl-02: Agent JIT cache miss → download → cache hit
- **Type**: Deterministic (Journey)
- **Command**: Python script: process MSFT (no FY), then process again
- **Expected**: Second call from cache

### J-dl-03: Force re-process corrects bad cached output
- **Type**: Deterministic (Journey)
- **Command**: Python script: process, corrupt file, process (no force = bad), process (force = fixed)
- **Expected**: force=True re-downloads and corrects

### J-prep-01: Real filing HTML through full preprocess
- **Type**: Deterministic (Journey)
- **Command**: Python script downloading real HTML and running preprocessor
- **Expected**: Content preserved ≥80%, no XBRL tags, non-empty output

### J-conv-01: Full pipeline with mixed content
- **Type**: Deterministic (Journey)
- **Command**: Python script checking cached NVDA filing for structure
- **Expected**: Valid YAML frontmatter, ≥3 ATX headings, ≥1 table, no HTML tags, >10KB body

### J-store-01: Multi-ticker filing lifecycle
- **Type**: Deterministic (Journey)
- **Command**: Python script with temp store, multiple save/get/list operations
- **Expected**: Correct isolation by ticker and fiscal year

---

## Manual Scenarios (PENDING — not executed in automated stage)

### S-dl-07-manual: Overlapping writes with real SEC calls
- **Type**: Manual Behavior Test

### S-dl-05-manual: Invalid inputs with real SEC
- **Type**: Manual Behavior Test

### J-conv-01-uat: Full pipeline output quality check
- **Type**: User Acceptance Test

### S-prep-03-uat / S-conv-02-uat: Older filing preprocessing quality
- **Type**: User Acceptance Test
