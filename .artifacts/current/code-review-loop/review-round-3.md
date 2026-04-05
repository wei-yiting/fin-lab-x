# Code Review Round 3

> Reviewer: Codex | Date: 2026-04-04

## Summary

| Metric | Count |
|--------|-------|
| Total issues | 4 |
| Blocking | 0 |
| Major | 1 |
| Minor | 2 |
| Suggestion | 1 |
| Library checks | 3 |

## Previous Round Status

| # | Issue ID | Status | Notes |
|---|----------|--------|-------|
| 1 | M-2.1 | ✅ Fixed | `pydantic>=2.0` in pyproject.toml |
| 2 | M-2.2 | ✅ Fixed | Three-way str/Mapping/TypeError handling |
| 3 | M-2.3 | ✅ Fixed | Transient error wrapping in downloader |
| 4 | m-2.1 | ✅ Fixed | EDGAR_IDENTITY from env |
| 5 | m-2.2 | ⚠️ Partially Fixed | 6 tests added but `filings.filter()` and `filings.latest()` paths uncovered |

## Issues

### [Major] M-3.1: Integration test doesn't verify fiscal-year derivation from `period_of_report`

- **File:** `backend/tests/ingestion/sec_filing_pipeline/test_pipeline.py` L544
- **Problem:** `test_s_dl_03_non_calendar_fy_nvda` claims to verify fiscal-year derivation but never inspects `period_of_report`. The assigned variable at L550 is unused, and assertions would pass even if implementation derived FY from `filing_date` instead.
- **Fix:** Rewrite to assert against the actual EDGAR filing object's `period_of_report`, or use a fixture/company where `period_of_report` year and `filing_date` year diverge so regression is observable.

### [Minor] m-3.1: No tests for converter Mapping/TypeError branches

- **File:** `backend/tests/ingestion/sec_filing_pipeline/test_html_to_md_converter.py` L28, L99
- **Problem:** The new response-shape handling (str/Mapping/TypeError) has no dedicated test coverage.
- **Fix:** Add adapter-level tests stubbing `html_to_markdown.convert()` to return `str`, `Mapping`, and invalid object; assert content extraction and `TypeError`.

### [Minor] m-3.2: Missing transient error tests for `filings.filter()` and `filings.latest()`

- **File:** `backend/tests/ingestion/sec_filing_pipeline/test_sec_downloader.py` L176
- **Problem:** `TestTransientErrorMapping` doesn't cover `filings.filter()` and `filings.latest()` transient paths.
- **Fix:** Add tests where `filings.filter.side_effect` and `filings.latest.side_effect` raise transient exceptions, assert `TransientError`.

### [Suggestion] S-3.1: `create_converter()` bypassed by production code

- **File:** `backend/ingestion/sec_filing_pipeline/pipeline.py` L59
- **Suggestion:** Wire `create_converter()` into `SECFilingPipeline.create()` or remove the unused factory.

## Documentation Gaps

| Folder | Missing |
|--------|---------|
| `backend/ingestion/sec_filing_pipeline` | README.md explaining pipeline stages, storage contract, extension guidelines |

## Official Standards Check

| Library | Version | API Used | Status | Notes |
|---------|---------|----------|--------|-------|
| html-to-markdown | >=3.0.2,<4.0.0 | `convert(...)`, `ConversionOptions` | ⚠️ | Defensive str/Mapping handling reasonable but only partially doc-backed |
| edgartools | >=5.17.1 | `Company(...)`, `get_filings(...)`, `.filter(...)`, `.latest()` | ✅ | Usage confirmed |
| edgartools | >=5.17.1 | Filing accessors: `html()`, `filing_date`, `period_of_report` | ⚠️ | Not fully re-verified from docs this round |
