# Fix Round 4

> Fixer: Claude (general-purpose subagent) | Date: 2026-08-19

## Fixed

| Issue ID | How Fixed | Files Changed |
|----------|-----------|---------------|
| M-4.1 (filter type validation) | Added `if filters and not isinstance(filters, dict): raise ValueError(...)` in `search()`, placed before the pre-existing `not filters or "ticker" not in filters` membership check so it intercepts truthy non-mapping values (`123`, `["ticker"]`, etc.) before any `in`/indexing operation runs. Scoped with `filters and ...` (not a standalone check) so `None`/`{}` still fall through to the original message unchanged — a bare `isinstance` guard as the very first check would have altered the existing, tested error message for `filters=None`. | `backend/ingestion/sec_dense_pipeline/retriever.py` |
| M-4.2 (`ingested_at` silent default) | Changed `payload.get("ingested_at", "")` to `payload["ingested_at"]` in `_point_to_chunk()`, matching every other required field's access pattern. Extended the `except ValueError as e:` around the `_point_to_chunk` call site in `search()` to `except (ValueError, KeyError) as e:` so a missing required field now maps to `CorpusUnavailableError` with point-id context, rather than falling through to the generic exception handler. | `backend/ingestion/sec_dense_pipeline/retriever.py` |
| m-4.1 (stale docstring) | Reworded the `vectorizer.py` module docstring and README.md lines 62–64 to distinguish the three retry surfaces that actually exist: bare `ingest_filing` (none), `ingest_filing_with_retry` (one retry for transient Qdrant failures), and the embedding client's own internal retry — replacing the stale "no retry wrapper here" claim that predated round 1's `ingest_filing_with_retry`. | `backend/ingestion/sec_dense_pipeline/vectorizer.py`, `backend/ingestion/sec_dense_pipeline/README.md` |
| m-4.2 (hanging barrier test) | Raced `ingest_claimed.wait()` against `first_call` via `asyncio.wait({claimed_wait, first_call}, return_when=asyncio.FIRST_COMPLETED)`, wrapped in `asyncio.wait_for(..., timeout=10)` as a bounded backstop. If `first_call` completes before signalling the barrier, `first_call.result()` re-raises its real exception immediately. `finally` now cancels/awaits `claimed_wait` and awaits (bounded) `first_call` in every outcome. | `backend/tests/ingestion/sec_dense_pipeline/integration/test_search.py` |

## Not Fixed

None.

## Reverted

None. One self-caught issue during development: an initial unconditional `isinstance` guard broke the existing `filters=None` rejection test's message; fixed in-place by scoping the check to `filters and not isinstance(...)` before committing — never landed broken.

## Tests Run

| Test Command | Result | Notes |
|--------------|--------|-------|
| `pytest backend/tests/ingestion/sec_dense_pipeline/ backend/tests/ingestion/sec_dense_pipeline_html/ backend/tests/scripts/ backend/tests/common/` | 231 passed, 39 deselected | |
| Same command with `-m integration` | 39 passed, 231 deselected | Local Qdrant |
| Barrier test run 15x in a row | 15/15 passed, ~0.5–0.7s each | Determinism check |
| Throwaway repro (not committed): barrier test's race logic with an early failure forced before the barrier | Resolved in 0.18–0.42s surfacing the real underlying exception instead of hanging | Confirms the hang-fix's actual failure-path behavior, not just happy-path determinism |
| `ruff format --check` / `ruff check` on touched files | Clean | |

## Tests Added or Modified

| Test File | Added/Modified | What It Tests |
|-----------|----------------|---------------|
| `test_retriever.py` | Added `test_search_rejects_non_dict_filters_int`, `test_search_rejects_non_dict_filters_list` | Non-mapping `filters` rejected with `ValueError`, not `TypeError` |
| `test_retriever.py` | Added `test_point_to_chunk_raises_keyerror_on_missing_ingested_at` | `_point_to_chunk` raises `KeyError` on missing `ingested_at` instead of defaulting |
| `test_retriever.py` | Added `test_search_maps_missing_ingested_at_to_corpus_unavailable` | End-to-end: missing `ingested_at` surfaces as `CorpusUnavailableError` |
| `integration/test_search.py` | Modified concurrency test | Same behavioral assertions, now with a bounded, hang-proof barrier wait |

## Commit

`2dc4c50` — `fix(rag-ingestion): round-4 review fixes for the JIT retriever cutover`.

## Orchestrator verification note (post-fixer, pre-round-5)

Spot-checked both Major fixes directly: the `isinstance` guard is correctly scoped
(`filters and not isinstance(filters, dict)`) so it doesn't disturb the existing
`None`/`{}` rejection path, with a comment explaining why the scoping matters. The
`_point_to_chunk` call site's exception handling is now `except (ValueError, KeyError) as
e:`, confirming `KeyError` from the new `payload["ingested_at"]` access is caught and
mapped to `CorpusUnavailableError` rather than escaping to the outer handler. Both match
the fix instructions. This is round 4 of a 5-round-max loop — round 5 is next.
