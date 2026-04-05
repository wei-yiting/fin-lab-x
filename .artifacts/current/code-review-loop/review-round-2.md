# Code Review Round 2

> Reviewer: Codex | Date: 2026-04-04

## Summary

| Metric | Count |
|--------|-------|
| Total issues | 5 |
| Blocking | 0 |
| Major | 3 |
| Minor | 2 |
| Suggestion | 0 |
| Library checks | 6 |

## Previous Round Status

| # | Issue ID | Status | Notes |
|---|----------|--------|-------|
| 1 | M-1.1 | ✅ Fixed | Cache check moved before download via `list_filings()` |
| 2 | M-1.2 | ⚠️ Partially Fixed | `extract_metadata=True` added, but type check only handles concrete `dict` |
| 3 | M-1.3 | ✅ Fixed | WHY comments added |
| 4 | m-1.1 | ✅ Fixed | Named constant `_MIN_OUTPUT_RATIO` extracted |
| 5 | S-1.1 | ⚠️ Not Fixed | Acceptable deferral (suggestion only) |

## Issues

### [Major] M-2.1: Direct `pydantic` dependency is missing

- **File:** `pyproject.toml` L6
- **Problem:** The pipeline imports `pydantic.BaseModel` and tests import `ValidationError`, but `pydantic` is not in `[project.dependencies]`. Works only because `fastapi` pulls it transitively. Fragile packaging.
- **Fix:** Add `pydantic` as a direct dependency.

### [Major] M-2.2: `html-to-markdown` response handling is still too narrow

- **File:** `backend/ingestion/sec_filing_pipeline/html_to_md_converter.py` L36
- **Problem:** Only checks `isinstance(result, dict)`. Any mapping-like wrapper that is not concrete `dict` falls through to `str(result)`, returning serialized container instead of Markdown content.
- **Fix:** Check for mapping-like interface (`collections.abc.Mapping`) and extract `content` key explicitly; if shape is wrong, raise a clear error.

### [Major] M-2.3: Batch retry logic is dead for real downloader failures

- **File:** `backend/ingestion/sec_filing_pipeline/sec_downloader.py` L43
- **Problem:** `_process_with_retry()` only retries `TransientError`, but `SECDownloader.download()` only maps `CompanyNotFoundError`. Failures from `get_filings()`, `.filter()`, `.latest()`, or `filing.html()` escape as foreign exceptions, bypassing retry completely.
- **Fix:** Catch transient edgartools/network exceptions in the downloader and re-raise as `TransientError`. Keep permanent errors mapped to domain exceptions.

### [Minor] m-2.1: Integration test hardcodes a real personal email address

- **File:** `backend/tests/ingestion/sec_filing_pipeline/test_pipeline.py` L410
- **Problem:** The `sec_integration` fixture commits a real personal email address. Unnecessary personal data in source control.
- **Fix:** Read `EDGAR_IDENTITY` from environment or use a clearly fake placeholder.

### [Minor] m-2.2: Tests do not cover the real transient-error contract

- **File:** `backend/tests/ingestion/sec_filing_pipeline/test_sec_downloader.py` L134
- **Problem:** Downloader tests cover permanent error mapping only. Retry tests mock the downloader directly, never verifying real edgartools transient failures become `TransientError`.
- **Fix:** Add downloader-level tests for transient failures and pipeline test exercising retry through downloader's real exception contract.

## Documentation Gaps

| Folder | Missing |
|--------|---------|
| `backend/ingestion/sec_filing_pipeline` | `README.md` explaining module boundaries and data flow |

## Official Standards Check

| Library | Version | API Used | Status | Notes |
|---------|---------|----------|--------|-------|
| html-to-markdown | >=3.0.2,<4.0.0 | `convert(..., options=ConversionOptions(heading_style="atx", extract_metadata=True))` | ❌ Wrong | Option usage correct, but result handling wrong for dict-like contract |
| edgartools | >=5.17.1 | `set_identity`, `Company(...)`, `get_filings(form=...)`, `.filter(date=...)`, `.latest()` | ✅ Current | Usage matches official references |
| markdownify | >=1.2.0 | `markdownify(..., heading_style=ATX)` | ✅ Current | Matches official docs |
| beautifulsoup4 | >=4.12.0 | `BeautifulSoup(...)`, `find_all`, `unwrap`, `decompose` | ✅ Current | Standard API |
| pyyaml | >=6.0.2 | `yaml.dump`, `yaml.safe_load` | ✅ Current | Correct usage |
| pydantic | transitive only | `BaseModel`, `model_dump` | ✅ Current | API usage correct, but missing direct dependency |
