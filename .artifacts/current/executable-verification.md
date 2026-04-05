# Executable Verification Plan

## Resolved Placeholders

- **S-dl-03**: NVDA's latest fiscal_year from edgartools = **2026** (period_of_report: 2026-01-25). MSFT's latest = **2025** (period_of_report: 2025-06-30). AAPL's latest = **2025** (period_of_report: 2025-09-27).
- **S-dl-05**: Exact error class names: `TickerNotFoundError`, `FilingNotFoundError`, `UnsupportedFilingTypeError` (all in `backend.ingestion.sec_filing_pipeline.filing_models`)
- **S-conv-02**: The preprocessor handles styled-p heading inference via `_promote_headings()` method — detects bold "PART X" and "Item N" patterns in block elements (div, p, td, th, span) and rewrites them as `<h1>`/`<h2>` tags
- **S-conv-03**: 
  - Import-time mock: `unittest.mock.patch.dict('sys.modules', {'html_to_markdown': None})` then call `create_converter()`
  - Invocation error mock: `unittest.mock.patch.object(HtmlToMarkdownAdapter, 'convert', side_effect=RuntimeError)` then call `convert_with_fallback()`
  - Silent failure mock: `unittest.mock.patch.object(HtmlToMarkdownAdapter, 'convert', return_value='')` then call `convert_with_fallback()`
- **J-dl-03**: Corrupt saved .md file by overwriting markdown_content portion with empty string while keeping frontmatter valid
- **html-to-markdown availability**: The `html-to-markdown` Rust package cannot be built on this aarch64 Linux container (no C linker). `create_converter()` falls back to `MarkdownifyAdapter`. This means S-conv-03 import-time fallback is the default state. S-conv-04 cannot test HtmlToMarkdownAdapter directly — will test MarkdownifyAdapter only and note HtmlToMarkdownAdapter as unavailable.

## Environment

- `EDGAR_IDENTITY` must be set from `/workspace/.env`
- Run with: `UV_LINK_MODE=copy uv run python <script>`
- Existing cached filings: NVDA/10-K/2026.md, AAPL/10-K/2025.md

## Automated Scenarios

All scenarios below are **Deterministic** (script-based). No Browser Automation scenarios exist.

### S-dl-01 through S-dl-08, S-prep-01 through S-prep-03, S-conv-01 through S-conv-04, S-store-01 through S-store-05, J-dl-01 through J-dl-03, J-prep-01, J-conv-01, J-store-01

Each scenario is implemented as a self-contained Python script that prints PASS/FAIL with details.

## Manual Scenarios (PENDING — not automated)

### S-dl-07-manual: Overlapping writes with real SEC calls
- Type: Manual Behavior Test

### S-dl-05-manual: Invalid inputs with real SEC
- Type: Manual Behavior Test

### J-conv-01-uat: Full pipeline output quality check
- Type: User Acceptance Test

### S-prep-03-uat: Older filing preprocessing quality
- Type: User Acceptance Test
