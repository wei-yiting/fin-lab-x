# Fix Round 3

> Fixer: Claude | Date: 2026-04-04

## Fixed

| Issue ID | How Fixed | Files Changed |
|----------|-----------|---------------|
| M-3.1 | Added 2 unit tests in `TestFiscalYearDerivation` with mocks where `period_of_report` and `filing_date` years differ. Removed unused `period_of_report` variable from integration test. | `test_sec_downloader.py`, `test_pipeline.py` |
| m-3.1 | Added 3 tests in `TestAdapterResponseShapes`: dict extracts `content`, string passes through, unexpected type raises `TypeError` | `test_html_to_md_converter.py` |
| m-3.2 | Added 2 tests: `filter()` ConnectionError and `latest()` TimeoutError both map to `TransientError` | `test_sec_downloader.py` |
| S-3.1 | Wired `create_converter()` into `SECFilingPipeline.create()`, removed unused `HtmlToMarkdownAdapter` import from pipeline, updated test | `pipeline.py`, `test_pipeline.py` |

## Not Fixed (with reason)

(none)

## Tests Run

| Test Command | Result | Notes |
|--------------|--------|-------|
| `uv run pytest backend/tests/ingestion/sec_filing_pipeline/ -v --tb=short -x -m "not sec_integration"` | ✅ Pass (127 passed, 8 deselected) | All tests pass |

## Tests Added or Modified

| Test File | Added/Modified | What It Tests |
|-----------|----------------|---------------|
| `test_sec_downloader.py` | Added `TestFiscalYearDerivation` (2 tests) | fiscal_year from period_of_report, not filing_date |
| `test_sec_downloader.py` | Added 2 in `TestTransientErrorMapping` | filter()/latest() transient error paths |
| `test_html_to_md_converter.py` | Added `TestAdapterResponseShapes` (3 tests) | Mapping/str/TypeError branches |
| `test_pipeline.py` | Modified `TestCreateClassMethod` + integration test | create_converter wiring + removed dead variable |
