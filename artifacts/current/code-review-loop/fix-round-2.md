# Fix Round 2

> Fixer: claude-fable-5 (isolated subagent) | Date: 2026-08-06
> Scope: all Round 2 findings. M-2.4 resolved via AGENTS.md subsection per user
> ruling (ADR declined — coexistence is time-boxed; deletion is tracked in the
> sunset issue's checklist). Spec-axis SP-2.1 (EmptyFilingError) declined by
> prior ruling; contract recorded in the DEV-132 issue description.

### Fixed

| Issue ID | How Fixed | Files Changed |
|----------|-----------|---------------|
| SP-2.1 | `_trim_section_text` rewritten: no longer delegates to `sec_core.trim_text_to_item_boundary` (same inline false-positive; left frozen for its callers). New `_ITEM_HEADING_RE` + `_is_structural_boundary`: a foreign `Item N.` is a boundary only at start-of-string, line start, or glued to a non-whitespace char. Inline space-preceded cross-references ("...under Item 1A. Risk Factors...") survive; self-references skipped; dangling glued `PART <roman>` still stripped. | parser.py, test_parser.py |
| M-2.1 | Acquisition split: new `_locate_filing_cached` (lru; Company → get_filings → pick filing + error branches). `_fetch_filing_obj_cached` = locate + `filing.obj()` only — original pre-refactor network behavior, no `filing.document` read. `_fetch_filing_bundle_cached` reuses the locate lru + reads metadata + shares the TenK cache. Regression test: `fetch_filing_obj` never touches `filing.document`; bundle reads it exactly once; both share one `edgar.Company` call. | sec_core.py, tests/common/conftest.py, test_sec_core.py |
| M-2.2 | Bundle metadata reads (incl. network-backed `filing.document`) wrapped in `_classify_edgar_error`; missing primary document → `SECError` with ticker + accession. Tests: 429 → RateLimitError (retry_after surfaced), 503 → TransientError, missing document → SECError. | sec_core.py, test_sec_core.py |
| M-2.3 | Ticker regex tightened to `^[A-Z0-9][A-Z0-9.\-]*$` (rejects ".", "..", ".AAPL", "-AAPL"; keeps "BRK.B"). Frozen HTML store untouched. | filing_store.py, test_filing_store.py |
| M-2.4 | AGENTS.md §4 gains "Ingestion Rewrite Coexistence (temporary until sunset)": HTML pipeline frozen as A/B baseline, sec_core only-add, ParsedFiling schema frozen (ratified reachability exception), subsection deleted in the sunset PR. Sunset issue checklist updated accordingly. | AGENTS.md |
| m-2.1 | Last `design.md` reference removed (test_sec_core.py cites the AGENTS.md subsection); inspect helper rephrased as planned future extension in filing_store.py + README; package-wide sweep confirms zero `design.md` tokens. | test_sec_core.py, filing_store.py, README.md |
| m-2.2 | Renamed `test_force_bypasses_store_and_reparses`; pre-seeds a different stored filing, asserts force bypasses it and persists the fresh parse. | test_parser.py |
| (orchestrator follow-up) | `_ITEM_HEADING_RE` extended to also match ALL-CAPS `ITEM N.` headings (real heading form, e.g. ADSK "ITEM 1A. RISK FACTORS") so bleed in ALL-CAPS filings is still cut; lowercase "item" stays excluded. Test added. | parser.py, test_parser.py |

### Tests Run

| Test Command | Result | Notes |
|--------------|--------|-------|
| `uv run pytest backend/tests/ingestion/sec_text_pipeline/ backend/tests/common/ -q` | ✅ 129 passed | includes new structural-boundary, ALL-CAPS, document-access, and ticker-validation tests |
| `uv run ruff check backend/` + `uv run ruff format backend/` | ✅ clean | |
| `uv run pytest backend/tests/ -q` | ✅ 978 passed, 49 deselected | inflight seam tests still pass |
| Live smoke (orchestrator): AAPL FY2025 `force=True` real EDGAR | ✅ | 17 items; 10/11/12/13 dropped; substantive items full length (1: 16054, 1a: 68163, 7: 18018, 8: 60874 — no over-trim); round-trip green |
