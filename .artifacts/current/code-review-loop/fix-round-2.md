# Fix Round 2

> Fixer: Claude | Date: 2026-04-04

## Fixed

| Issue ID | How Fixed | Files Changed |
|----------|-----------|---------------|
| M-2.1 | Added `pydantic>=2.0` to `[project.dependencies]` and ran `uv sync` to update `uv.lock` | `pyproject.toml`, `uv.lock` |
| M-2.2 | Replaced `isinstance(result, dict)` with three-way check: `str` first, then `collections.abc.Mapping`, then raise `TypeError` for unexpected types | `html_to_md_converter.py` |
| M-2.3 | Wrapped all edgartools calls in outer try/except that re-raises domain errors directly and maps `ConnectionError`, `TimeoutError`, `OSError` to `TransientError` | `sec_downloader.py` |
| m-2.1 | Removed hardcoded personal email from integration test; now reads `EDGAR_IDENTITY` from env var and skips if not set | `test_pipeline.py` |
| m-2.2 | Added 7 new tests in `TestTransientErrorMapping` class covering transient exceptions at various edgartools call sites, plus negative test for permanent errors | `test_sec_downloader.py` |

## Not Fixed (with reason)

(none)

## Tests Run

| Test Command | Result | Notes |
|--------------|--------|-------|
| `uv run pytest backend/tests/ingestion/sec_filing_pipeline/ -v --tb=short -x -m "not sec_integration"` | ✅ Pass (120 passed, 8 deselected) | All existing + new tests pass |

## Tests Added or Modified

| Test File | Added/Modified | What It Tests |
|-----------|----------------|---------------|
| `test_sec_downloader.py` | Added `TestTransientErrorMapping` (7 tests) | `ConnectionError`, `TimeoutError`, `OSError` mapping to `TransientError` at various call sites; permanent errors pass through |
| `test_pipeline.py` | Modified `setup_pipeline` fixture | Integration tests read `EDGAR_IDENTITY` from env instead of hardcoded email |
