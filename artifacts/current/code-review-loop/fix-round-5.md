# Fix Round 5

> Fixer: Claude (general-purpose subagent) | Date: 2026-08-20
> User explicitly authorized continuing past the skill's 5-round cap until convergence
> (see review-round-5.md's Orchestrator Note and the follow-up conversation).

## Fixed

| Issue ID | How Fixed | Files Changed |
|----------|-----------|---------------|
| M-5.1 | In `_point_to_chunk()`, changed `payload.get("block_heading")` / `payload.get("prelude")` to `payload["block_heading"]` / `payload["prelude"]`, matching every other field's access pattern in that function. A missing key now raises `KeyError` (caught by the existing `except (ValueError, KeyError)` in `search()` and mapped to `CorpusUnavailableError`); a present key with a stored `None` value is unaffected. | `backend/ingestion/sec_dense_pipeline/retriever.py` |

## Sibling Sweep Result

Fixer grepped all three core files (`retriever.py`, `vectorizer.py`, `common.py`) for
`.get(`/`getattr(`/`.setdefault(`/`.pop(` and evaluated every hit:
- Env-var lookups (`SEC_DISABLE_JIT`, `QDRANT_URL`) — not schema fields, correctly excluded.
- `filters.get("fiscal_year")` — legitimately `NotRequired` per `SearchFilters`, external
  caller input, correctly excluded.
- `getattr(e, "status_code", None)` — reading off a third-party exception object, not our
  data contract, correctly excluded.
- `common.py`'s `_marker_is_complete()`: `(points[0].payload or {}).get("status") ==
  "complete"` — the one real candidate considered. Evaluated and rejected: this function is
  deliberately fail-safe by design (any anomaly collapses to "not complete," triggering a
  safe re-ingest) — the opposite risk shape from `block_heading`/`prelude`/`ingested_at`,
  where a missing key silently produced a plausible-but-wrong `Chunk` returned to the
  caller as valid data. Left unchanged; reasoning is sound.

No other instance of the pattern found. The orchestrator's own pre-dispatch grep (see
review-round-5.md's Orchestrator Note) had already narrowed this to the same two lines;
the fixer's independent sweep concurred.

## Not Fixed

None.

## Tests Run

| Test Command | Result | Notes |
|--------------|--------|-------|
| `uv run pytest backend/tests/ingestion/sec_dense_pipeline/ backend/tests/ingestion/sec_dense_pipeline_html/ backend/tests/scripts/ backend/tests/common/` | 235 passed, 39 deselected | |
| Same command with `-m integration` | 39 passed, 235 deselected | Local Qdrant |
| `ruff format --check` / `ruff check` on touched files | Clean | |

## Tests Added or Modified

| Test File | Added/Modified | What It Tests |
|-----------|----------------|---------------|
| `test_retriever.py` | Added `test_point_to_chunk_raises_keyerror_on_missing_nullable_field` (parametrized: `block_heading`, `prelude`) | Missing key raises `KeyError` directly from `_point_to_chunk` |
| `test_retriever.py` | Added `test_search_maps_missing_nullable_field_to_corpus_unavailable` (same parametrization) | Surfaces as `CorpusUnavailableError` through `search()` |

Existing `test_point_to_chunk_handles_none_block_heading_and_prelude` (key present, value
`None`) still passes unchanged — confirms the legitimate-nullable case is unaffected.

## Commit

`27ba6b5` — `fix(rag-ingestion): round-6 review fixes for the JIT retriever cutover` (commit
message numbering predates this file's renumbering to match `review-round-5.md`'s pairing;
content is accurate).

## Orchestrator verification note (post-fixer, pre-round-6-review)

Spot-checked directly: `retriever.py` lines 229–230 now read `payload["block_heading"]` /
`payload["prelude"]`, consistent with every sibling field's access pattern in the same
constructor call. Confirmed via `git log`/`git status` that the commit landed and the tree
is clean. Proceeding to dispatch the next (6th) review pass on both axes to check for
convergence to zero.
