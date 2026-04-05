# Fix Round 1

> Fixer: Claude | Date: 2026-04-04

## Fixed

| Issue ID | How Fixed | Files Changed |
|----------|-----------|---------------|
| M-1.1 | Moved cache check for `fiscal_year=None` path **before** the download call. Uses `store.list_filings()` to find the most recent cached year and returns it if found, completely avoiding the SEC request. Removed the misleading post-download `from_cache=True` path. | `pipeline.py`, `test_pipeline.py` |
| M-1.2 | Explicitly set `extract_metadata=True` in `ConversionOptions`. Added defensive type check: handles both `dict` (current behavior) and `str` return types. Verified actual library behavior: `convert()` returns a dict with `content` key when `extract_metadata=True` (the default). | `html_to_md_converter.py` |
| M-1.3 | Added a comment block before `_promote_headings()` explaining: (1) SEC filings use block elements with bold styling instead of semantic headings, (2) reverse traversal ensures inner matches are promoted first, (3) the descendant guard prevents redundant outer container promotion. | `html_preprocessor.py` |
| m-1.1 | Extracted `0.01` to `_MIN_OUTPUT_RATIO = 0.01` with a comment explaining the rationale (detects cases where the converter silently drops content, e.g. table-heavy filings). | `html_to_md_converter.py` |

## Not Fixed (with reason)

| Issue ID | Reason |
|----------|--------|
| S-1.1 | Suggestion only. `create_converter()` removal or wiring is a refactor beyond the scope of this fix round. Leaving for reviewer to decide. |

## Tests Run

| Test Command | Result | Notes |
|--------------|--------|-------|
| `uv run pytest backend/tests/ingestion/sec_filing_pipeline/ -v --tb=short -x -m "not sec_integration"` | ✅ Pass (114 passed, 8 deselected) | All unit tests pass |
| `uv run ruff check` + `uv run ruff format --check` | ✅ Pass | All 4 changed files clean |

## Tests Added or Modified

| Test File | Added/Modified | What It Tests |
|-----------|----------------|---------------|
| `backend/tests/ingestion/sec_filing_pipeline/test_pipeline.py` | Modified | Updated `mock_store` fixture to default `list_filings.return_value = []`. Renamed and rewrote `test_cache_check_uses_resolved_fiscal_year_when_omitted` to `test_cache_check_uses_list_filings_when_fiscal_year_omitted` to verify the new pre-download cache path. Updated `TestBatchFromCacheFlag` to set `list_filings` return values appropriately. |
