# Fix Round 1

> Fixer: claude-fable-5 (isolated subagent) | Date: 2026-08-06
> Scope ruling by user: fix M-1.1/SP-1.2, M-1.4, m-1.1, m-1.2, m-1.3 (+ docstring
> decision-ID sweep), M-1.2 as docs-only (force = re-parse semantics confirmed).
> Deferred pending user decision: M-1.3 (private `_filing` access), M-1.5 (kept —
> schema freeze ruling (a), to be recorded in PR body), SP-1.1 (param name),
> SP-1.3 (fiscal_year=None mode / store= injection).

### Fixed

| Issue ID | How Fixed | Files Changed |
|----------|-----------|---------------|
| M-1.1 / SP-1.2 | `_parse_items` trims each section body to its own Item boundary before stub classification and FlatItem build. `sec_core.trim_text_to_item_boundary` handles "reference.Item 12." but its `(?<![A-Za-z])` lookbehind rejects uppercase-glued forms ("PART IIIItem 10.", "53PART IVItem 15."); per the sec_core only-add rule, a local `_trim_section_text` helper in parser.py delegates to the shared trim first, then runs a second pass with `_ITEM_HEADING_RE` (`(?<![a-z])(?i:item\s+(\d{1,2}[a-c]?)\s*\.(?!\d))` — lowercase-only lookbehind lets uppercase glue match while "subitem" does not) plus stripping of a dangling glued "PART <roman>" label. Fixture result: Item 11 trims to its pure pointer stub and drops; Item 9C trims to "Not applicable." and survives clean; Item 4's bleed into PART II is cut. | parser.py, test_parser.py |
| M-1.4 | New `EmptyFilingError(SECError)` in parser.py (exported from package `__init__`). `parse_filing` raises before any `store.save` when the parsed item list is empty; message carries ticker, fiscal year, accession number. | parser.py, __init__.py, test_parser.py |
| m-1.1 | `model_config = ConfigDict(extra="forbid")` on all five models; round-trip tests prove unknown top-level and nested fields raise ValidationError. | filing_models.py, test_filing_models.py |
| m-1.2 | Corrupt-cache test now requires `pydantic.ValidationError` specifically. | test_filing_store.py |
| m-1.3 | New `backend/ingestion/sec_text_pipeline/README.md` (scope, module map, data flow, A/B coexistence boundary, two-cache rationale, extension guidelines). Swept all decision-document IDs (design.md §…, DEV-127/125, spec R8, Q1, Seam-1) from docstrings/comments across the package, the sec_core docstring hunks, and tests — rationale inlined self-containedly. `envelope §0` reference kept deliberately: docs/design-envelope.md is repo-resolvable and AGENTS.md mandates citing it by section number. | README.md (new), parser.py, filing_models.py, filing_store.py, stub_detection.py, conftest.py, test_stub_detection.py, test_filing_models.py, backend/common/sec_core.py (docstrings only) |
| M-1.2 (docs) | `parse_filing` docstring documents force semantics: bypasses the on-disk filing store and overwrites stored JSON; does NOT invalidate the in-process EDGAR fetch cache (filings immutable per ticker+year; amendments are separate filings). Behavior unchanged per user ruling. | parser.py |

### Not Fixed (with reason)

| Issue ID | Reason |
|----------|--------|
| M-1.3 | Deferred — user deciding between `fetch_filing_bundle` (sec_core only-add) vs keeping contained private access. |
| M-1.5 | User ruling (a): schema freeze is the ticket's explicit deliverable; keep, record ruling in PR body. |
| SP-1.1 | Deferred — param naming `fiscal_year` vs spec-literal `year` awaiting user ruling. |
| SP-1.3 | Deferred — orchestrator recommends removing `fiscal_year=None` mode and keeping `store=` (keyword-only); awaiting user ruling. |

### Tests Run

| Test Command | Result | Notes |
|--------------|--------|-------|
| `uv run pytest backend/tests/ingestion/sec_text_pipeline/ backend/tests/common/ -q` | ✅ 113 passed | includes is_stub_section v1 equivalence tests |
| `uv run ruff check backend/ --fix` + `uv run ruff format backend/` | ✅ clean | |
| `uv run pytest backend/tests/ -q` | ✅ 962 passed, 49 deselected | full suite |
| Live smoke (orchestrator): AAPL FY2025 `force=True` real EDGAR parse | ✅ | emitted 17 items; 10/11/12/13 dropped; 9C text free of Item 10; round-trip green |

### Tests Added or Modified

| Test File | Added/Modified | What It Tests |
|-----------|----------------|---------------|
| test_parser.py | Modified test_stub_items_are_dropped | dropped ⊇ {6,10,11,12,13}; emitted ⊇ {1,1a,7} |
| test_parser.py | Added test_emitted_text_contains_no_foreign_item_heading | no emitted item text contains another item's heading; 9c lacks "Item 10." |
| test_parser.py | Added test_all_sections_empty_or_stub_raises_and_saves_nothing | EmptyFilingError with ticker/FY/accession; nothing saved |
| test_filing_models.py | Added unknown-field tests (top-level + nested) | extra="forbid" enforcement |
| test_filing_store.py | Modified corrupt-JSON test | requires pydantic.ValidationError |
