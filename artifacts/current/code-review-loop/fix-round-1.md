# Fix Round 1

> Fixer: Claude Fable 5 (main session) | Date: 2026-08-12
> Scope: round 1 裁決後的 accepted findings(見 review-round-1.md 裁決表)

## Applied fixes

### M-1.1 — CLI behavioral tests(scoped to envelope §5)
- New `backend/tests/ingestion/sec_text_pipeline/test_main.py`:
  - `test_default_prints_summary` — default mode prints summary, no body content, forwards `("AAPL", 2024, False)` to `parse_filing`
  - `test_section_prints_plain_text` — `--section 1A`(uppercase)prints the flat item body verbatim
  - `test_inspect_writes_file_and_prints_path` — `SEC_TEXT_INSPECT_DIR` routed to `tmp_path`; asserts file path echo, file content header, and `--force` forwarding(ratified per SP-1.2)
  - `test_malformed_ticker_fails_legibly` — real path(no patch, no network): `../BAD` → exit 1, `Invalid ticker` on stderr, no traceback;doubles as m-1.1 regression test
- `backend/tests/common/test_data_paths.py`: `get_sec_text_inspect_dir` added to the CWD-independence test + new `SEC_TEXT_INSPECT_DIR` override test

### m-1.1 — ticker ValueError legibility
- `__main__.py` `_load_filing` now catches `(FinLabError, ValueError)`;ValueError source(filing store ticker validation)noted in comment

### m-1.2 — unreachable branch
- `inspect_view.py` `_item_chars` narrowed to `StructuredItem`;`isinstance(item, FlatItem)` branch removed

### m-1.3 — filing_store doc de-stale
- Module docstring: "planned inspect helper (future extension, not yet built)" → points at the implemented `inspect_view` + package CLI
- `FilingStore` Protocol docstring: speculative "(e.g. the inspect CLI's listing needs)" example removed

## Not fixed (user verdicts)

- SP-1.1 — dismissed;AC wording in Linear DEV-134 updated to「prelude 判定(valid/reclassified 附 chars 數)」instead
- SP-1.2 — declined;`--force` ratified into the issue description

## Verification

- `ruff check backend/` ✅ `ruff format backend/`(no changes)✅
- `pytest backend/tests/ingestion/sec_text_pipeline/ backend/tests/common/test_data_paths.py` → 130 passed
