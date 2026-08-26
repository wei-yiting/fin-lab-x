# Fix Round 4

> Fixer: Claude (code-fixer subagent) | Date: 2026-08-20

## Fixed

| Issue ID | How Fixed | Files Changed |
|----------|-----------|---------------|
| M-4.2 / SP-4.1 (same underlying gap, found independently by both review axes) | `locate_filing_ref()` now validates the FORMAT of EDGAR metadata, not just its presence. Added `_ACCESSION_NUMBER_RE = re.compile(r"^\d{10}-\d{2}-\d{6}$")`; a non-empty accession number that doesn't match EDGAR's `NNNNNNNNNN-NN-NNNNNN` format now raises `SECError` (previously only an empty/`None` value was caught). Replaced `int(period_of_report[:4])` (which only validated a 4-character prefix) with `date.fromisoformat(period_of_report).year`, which validates the whole string as a real ISO date and routes any failure through the existing `_classify_edgar_error(...)` path. Added tests for a malformed-but-non-empty accession number and an invalid full date with a valid-looking year prefix. | `backend/common/sec_core.py`, `backend/tests/common/test_sec_core.py` |
| M-4.4 | Rewrote ADR-0018's Decision paragraph to match the actual `EvidenceChunk`/`EvidenceGroup` code shape (a pre-existing inaccuracy dating to the original 2026-08-05 text, never caught by rounds 1-3): the chunk carries `source`, a composed `title`, optional `subsection`, `content`, `score` — no per-chunk ordinal; ticker/fiscal_year/item are properties of the enclosing group, not the chunk. Added a cross-reference to ADR-0019 at the URL-resolution sentence. No new fields were added to the code — prose was corrected to match the shipped shape. | `docs/adr/0018-sec-citations-are-prompt-driven-and-model-numbered.md` |
| m-4.2 | Added `backend.agent_engine.tools.sec_filing_search` to `sec_core.py`'s module docstring "Shared by" sentence — it's a real consumer of `locate_filing_ref`, `TENK_STANDARD_TITLES`, and `FilingType`, all already documented in the same docstring. | `backend/common/sec_core.py` |

## Not Fixed

None — all three approved fixes landed.

## Reverted (fix broke tests)

None.

## Tests Run

| Test Command | Result | Notes |
|--------------|--------|-------|
| `uv run ruff format backend/` | ✅ Pass | 210 files unchanged |
| `uv run ruff check backend/` | ✅ Pass | All checks passed |
| `uv run pytest backend/tests/ -q` | ✅ Pass | 1265 passed, 55 deselected (was 1262 before this round; +3 new tests, 0 regressions) |

Orchestrator independently re-ran `ruff check` and the full test suite after the fixer completed — both green — and read the full diff on both changed files against the exact instructions given. Everything matched precisely.

## Tests Added or Modified

| Test File | Added/Modified | What It Tests |
|-----------|----------------|----------------|
| `backend/tests/common/test_sec_core.py` | Added `test_locate_filing_ref_malformed_accession_number_raises_sec_error` | Non-empty, format-invalid accession number (`"not-an-accession"`) → `SECError` |
| `backend/tests/common/test_sec_core.py` | Added `test_locate_filing_ref_invalid_full_date_raises_classified_error` (parametrized: `"2025-99-99"`, `"2025-invalid"`) | A `period_of_report` with a valid-looking 4-digit year prefix but an invalid full ISO date → classified error, not a bare `ValueError` |

---

## Discussion Gate Record (Round 4) — items resolved without a code change

### Dismissed (user decision, with investigation) — will not be fixed, do not re-raise

| Issue ID | Reason |
|----------|--------|
| M-4.1 | `query`/`ticker`/`fiscal_year` boundary validation flagged as still incomplete (no query max length, no ticker character-set constraint, no fiscal_year upper bound). Investigated: the reviewer's `ticker="../../"` example evoked path traversal, but `LocalFilingStore._validate_ticker()` already rejects any character outside `A-Z0-9.-` before any filesystem path is built from a ticker — the actual risk is already closed at the point of use. The remaining sub-items (query max length, fiscal_year upper bound) would only ever surface as a clean downstream error, not silent corruption — judged low marginal value at this point in the loop. Dismissed. |
| M-4.3 | Flagged that retrieved chunks are never cross-checked against the requested (ticker, fiscal_year). Investigated: `search()`'s Qdrant query uses `Filter(must=[ticker, year])`, a database-level hard guarantee — Qdrant physically cannot return a non-matching point, so an application-level re-check would be redundant (it couldn't catch anything the DB filter doesn't already prevent, and couldn't catch a payload-level data-quality bug either, since the redundant check would read the same wrong data). A narrower, real edge case was identified: `accession_number` is NOT part of the Qdrant filter, so a chunk from a stale ingest could theoretically carry a different accession number than what `locate_filing_ref()` resolves live if a company re-filed for the same fiscal year. Logged to Linear DEV-160 (the ingestion/production-routing ticket) as the correct owner of ingest-time data consistency — out of scope for this read-time tool. |
| m-4.1 | Re-raised two already-settled items: (1) `EvidenceChunk`'s docstring "once DEV-143 lands" — a deliberately approved transitional phrase (see round 3's M-1.1 discussion and the note left on DEV-143), not oversight; (2) `DEV-125`/`DEV-126` references in ADR prose — an established repo convention already verified present in several pre-existing, unrelated ADRs (0005, 0013, 0014) predating this branch. Neither needs to change. |
