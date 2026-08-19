# Fix Round 3

> Fixer: Claude (general-purpose subagent) | Date: 2026-08-19

## Fixed

| Issue ID | How Fixed | Files Changed |
|----------|-----------|---------------|
| M-3.1 | Added `httpx.RemoteProtocolError` to `_TRANSIENT_SOURCE_TYPES` (kept `LocalProtocolError` excluded). Rewrote the reasoning comment to cite httpx's own hierarchy (verified against the installed 0.28.1 `_exceptions.py` docstring: `TimeoutException`/`NetworkError`/`ProtocolError` are siblings under `TransportError`, separate from `DecodingError`). Also fixed the now-stale "only connection/timeout-shaped causes" phrase in `ingest_filing_with_retry`'s docstring. | `backend/ingestion/sec_dense_pipeline/vectorizer.py` |
| M-3.2 | Changed `search()`'s signature to `filters: SearchFilters` (no default/`None`). Updated `SearchFilters`'s docstring and the README's "required and, when present" contradiction to say `filters` is unconditionally required. | `backend/ingestion/sec_dense_pipeline/retriever.py`, `backend/ingestion/sec_dense_pipeline/README.md` |
| M-3.3 | `_point_to_chunk` now raises `ValueError` on `payload is None` (verified `ScoredPoint.payload: dict[str, Any] \| None` against installed qdrant-client 1.17.1). `search()`'s point-conversion loop wraps each `_point_to_chunk` call in `except ValueError` (which also catches `pydantic.ValidationError`, a `ValueError` subclass) and re-raises as `CorpusUnavailableError` with the offending point's id, before the outer `except (ValueError, FinLabError): raise` passthrough can see a raw `ValueError`. Pyright on `retriever.py`: 14 errors → 0. | `backend/ingestion/sec_dense_pipeline/retriever.py` |
| m-3.1 | Removed `(DEV-113: ...)` from `test_search_raises_when_filters_is_none`'s docstring, replaced with the self-contained "naive search is a proven-harmful retrieval mode" rationale. Re-grepped the entire branch diff (all non-`artifacts/` files) for `DEV-\d+`/`[MSB]-\d+\.\d+`/`SP-\d+\.\d+` — this was the only hit. | `backend/tests/ingestion/sec_dense_pipeline/unit/test_retriever.py` |
| m-3.2 | Replaced the unsynchronized `asyncio.gather()` race with an `asyncio.Event` barrier: `ingest_filing_with_retry` is patched so the first call signals `ingest_claimed` (which only fires after it has already claimed the in-flight slot) and then blocks on `release_ingest` before doing the real ingest; the test waits for `ingest_claimed`, then issues the second call and asserts it deterministically gets `IngestionInProgressError`, then releases the first call. Confirmed the "other outcome" (hot hit when the first caller already fully completed) is already covered by the existing `test_ensure_ingested_returns_true_on_marker_hit_without_jit` and the stale-marker recheck by `test_ensure_ingested_recheck_after_claim_catches_completed_race` — both accurate, not duplicated. | `backend/tests/ingestion/sec_dense_pipeline/integration/test_search.py` |

## Not Fixed

None.

## Reverted

None.

## Tests Run

| Test Command | Result | Notes |
|--------------|--------|-------|
| `pytest backend/tests/ingestion/sec_dense_pipeline/ backend/tests/ingestion/sec_dense_pipeline_html/ backend/tests/scripts/ backend/tests/common/` | 227 passed, 39 deselected | Non-integration suite, run twice (before commit and again post-format) |
| Same command with `-m integration` | 39 passed, 227 deselected | Against local Qdrant (`fin-lab-x-qdrant-1`, v1.17.1), run twice |
| `test_concurrent_jit_...one_wins_one_gets_legible_error -m integration` × 15 | 15/15 passed | Repeated to confirm the new barrier-based test is actually deterministic, not passing once by luck |
| `pyright backend/ingestion/sec_dense_pipeline/retriever.py` | 0 errors, 0 warnings | Was 14 `reportOptionalSubscript`/`reportOptionalMemberAccess` errors before the fix |
| `pyright backend/ingestion/sec_dense_pipeline/vectorizer.py` | 1 pre-existing error (unrelated) | `PointStruct(payload=ChunkPayload)` type mismatch at line 161; confirmed via `git stash` that this error exists identically on unmodified HEAD — out of scope for this round, left untouched |
| `ruff format --check backend/` | 214 files, clean | |
| `ruff check backend/` | All checks passed | |

## Tests Added or Modified

| Test File | Added/Modified | What It Tests |
|-----------|----------------|---------------|
| `test_vectorizer.py` | Modified | `test_ingest_filing_with_retry_does_not_retry_remote_protocol_error` → renamed `..._classifies_remote_protocol_error_and_retries`; now asserts first attempt raises, second succeeds |
| `test_vectorizer.py` | Added | `test_ingest_filing_with_retry_does_not_retry_local_protocol_error` |
| `test_retriever.py` | Modified | `_make_point()` helper now sets `id=` (needed since production code's new error path references `point.id`) |
| `test_retriever.py` | Added | `test_point_to_chunk_rejects_none_payload_with_clear_error` |
| `test_retriever.py` | Modified | `test_search_rejects_invalid_top_k` now passes explicit valid `filters` |
| `test_retriever.py` | Modified | `test_search_raises_when_filters_is_none` now passes explicit `filters=None` (`# type: ignore[arg-type]`); DEV-113 removed |
| `test_retriever.py` | Added | `test_search_maps_malformed_payload_to_corpus_unavailable` |
| `integration/test_search.py` | Modified | Concurrency test rewritten with an `asyncio.Event` barrier for a deterministic race |

## Commit

`04c5e8a` — `fix(rag-ingestion): round-3 review fixes for the JIT retriever cutover`.

## Orchestrator verification note (post-fixer, pre-round-4)

Spot-checked the two highest-stakes changes directly: `search()`'s signature is now
`(query: str, filters: SearchFilters, top_k: int = 10)` — `filters` truly required, no
default — confirming M-3.2 landed as corrected in this round's discussion gate.
`_point_to_chunk` now guards `payload is None` and its docstring correctly states the
`pydantic.ValidationError` mapping strategy. Both match the fix instructions. No further
action needed before dispatching round 4.
