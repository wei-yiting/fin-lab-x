# Fix Round 2

> Fixer: Claude (general-purpose subagent) | Date: 2026-08-19

## Fixed

| Issue ID | How Fixed | Files Changed |
|----------|-----------|---------------|
| M-2.1 | Broadened `_TRANSIENT_SOURCE_TYPES` to `(httpx.TimeoutException, httpx.NetworkError)` (verified against installed httpx 0.28.1), covering `ConnectTimeout/ReadTimeout/WriteTimeout/PoolTimeout/ConnectError/ReadError/WriteError/CloseError`. `httpx.RemoteProtocolError` deliberately excluded — reasoning documented in a code comment and pinned by a test. | `backend/ingestion/sec_dense_pipeline/vectorizer.py`, `backend/tests/ingestion/sec_dense_pipeline/unit/test_vectorizer.py` |
| M-2.2 | Removed `M-1.2/SP-1.3`, `SP-1.6` docstring prefixes and bare "the AC"/"same AC" phrasing, replaced with plain behavioral descriptions. Grepped the full branch diff for other occurrences — none found beyond the three files named. | `backend/ingestion/sec_dense_pipeline/retriever.py`, `backend/tests/ingestion/sec_dense_pipeline/unit/test_retriever.py`, `backend/tests/scripts/test_embed_sec_filings.py` |
| M-2.3 | Added `SearchFilters` TypedDict (`ticker: str`, `fiscal_year: NotRequired[int]`) and `_validate_filters()`, called before any Qdrant/EDGAR work: rejects unknown keys, non-string `ticker`, non-int (incl. `bool`) `fiscal_year` with clear `ValueError`s. | `backend/ingestion/sec_dense_pipeline/retriever.py`, `backend/tests/ingestion/sec_dense_pipeline/unit/test_retriever.py` |
| M-2.4 | Removed the `except Exception: return False` swallow in both `check_commit_marker_complete` and `async_check_commit_marker_complete`; only a successful retrieve with no complete marker returns `False` now. Confirmed `search()`'s existing exception mapping needs no new handling. This exposed two integration tests relying on the swallowed behavior (calling the marker check against a deliberately never-created collection, a shape `search()` itself never produces) — fixed by removing their now-redundant assertions (see orchestrator verification note below). | `backend/ingestion/sec_dense_pipeline/common.py`, `backend/tests/ingestion/sec_dense_pipeline/unit/test_common.py` (new), `backend/tests/ingestion/sec_dense_pipeline/unit/test_retriever.py`, `backend/tests/ingestion/sec_dense_pipeline/integration/test_ingest.py`, `backend/tests/ingestion/sec_dense_pipeline/integration/test_search.py` |
| m-2.1 | Deleted `_clear_registry_for_ensure_ingested_tests`, kept `_clear_registry` (accurate name + docstring for a module-wide concern). | `backend/tests/ingestion/sec_dense_pipeline/unit/test_retriever.py` |
| m-2.2 | Removed `DEV-113` from `retriever.py`'s docstring/`ValueError`, `DEV-138`/`DEV-162` from `embed_sec_filings_html.py`, `DEV-138` from `backend/scripts/README.md` — descriptive rationale kept, IDs dropped. | `backend/ingestion/sec_dense_pipeline/retriever.py`, `backend/scripts/embed_sec_filings_html.py`, `backend/scripts/README.md` |
| m-2.3 | `_point_to_chunk(point: models.ScoredPoint)`, `_marker_is_complete(points: list[models.Record])`; added `BatchIngestResult` TypedDict (with `Literal["success","failed"]` status) in both batch scripts, replacing bare `list[dict]`. | `backend/ingestion/sec_dense_pipeline/retriever.py`, `backend/ingestion/sec_dense_pipeline/common.py`, `backend/scripts/embed_sec_filings.py`, `backend/scripts/embed_sec_filings_html.py` |
| S-2.1 | Removed the `resolved_holder` mutable out-parameter. Fiscal year is now resolved eagerly in `main()`'s per-ticker loop before calling the renamed `_parse_and_ingest(ticker, fiscal_year)`, which takes only a concrete year. SP-1.6 behavior (resolved year survives a later failure) preserved, same test still passes (docstring reworded). | `backend/scripts/embed_sec_filings.py`, `backend/tests/scripts/test_embed_sec_filings.py` |
| S-2.2 | Removed the dead `if not await client.collection_exists(collection): raise CorpusUnavailableError(...)` branch (unreachable after `async_ensure_collection_and_indexes` already creates-or-raises) and its extra Qdrant round-trip. Removed the test that only reached it via an artificial mock; re-targeted the adjacent 404-mapping test at `query_points()`, a call site that still exists. | `backend/ingestion/sec_dense_pipeline/retriever.py`, `backend/tests/ingestion/sec_dense_pipeline/unit/test_retriever.py` |
| Doc gap (carried over from Round 1) | Added `retriever.py` to the Structure Map, plus a new "JIT retrieval" section covering the search contract, hot/cold flow, in-process concurrency, error-mapping table, and retry boundaries; added `SEC_DISABLE_JIT` to the Configuration table. | `backend/ingestion/sec_dense_pipeline/README.md` |

## Not Fixed

None.

## Reverted

None.

## Tests Run

| Test Command | Result | Notes |
|--------------|--------|-------|
| `pytest backend/tests/ingestion/sec_dense_pipeline/ backend/tests/ingestion/sec_dense_pipeline_html/ backend/tests/scripts/ backend/tests/common/` | 224 passed, 39 deselected | Required gate command |
| Same command with `-m integration` | 39 passed | Run proactively against live local Qdrant — this is what surfaced the M-2.4 integration-test fallout the default deselect would have hidden |
| `pytest backend/tests/` (whole backend suite) | 1274 passed, 61 deselected | Broad regression check |
| `ruff format --check backend/` | 214 files, clean | Matches CI |
| `ruff check backend/` | All checks passed | Matches CI |

## Tests Added or Modified

| Test File | Added/Modified | What It Tests |
|-----------|----------------|---------------|
| `test_vectorizer.py` | Added 3 | `WriteTimeout`/`ReadError` now retry (previously-uncovered subclasses); `RemoteProtocolError` still does not retry |
| `test_common.py` (new) | Added 2 | Sync/async marker-check propagate a Qdrant `retrieve()` failure instead of swallowing it to `False` |
| `test_retriever.py` | Added 5, removed 2, ~6 docstrings reworded | New: legacy `year` key / non-string `ticker` / non-int `fiscal_year` / bool `fiscal_year` rejected; `_ensure_ingested` propagates a marker-check failure without attempting parse/ingest. Removed: the dead-branch test and the now-unused `collection_exists` kwarg on `_mock_client`. Adapted: 404-mapping test now injects via `query_points()` |
| `integration/test_search.py` | Modified 1 | Removed a precondition assertion that depended on the swallowed-exception bug; `clean_collection` fixture already guarantees the invariant it was checking |
| `integration/test_ingest.py` | Modified 1 | Removed a redundant marker-check assertion; the adjacent `collection_exists` check already proves the invariant directly |
| `test_embed_sec_filings.py` | Replaced 2 with 1, 1 docstring reworded | New `_parse_and_ingest` unit test (no longer does resolution); resolution-when-omitted behavior remains covered at the `main()` level by a pre-existing test |

## Commit

`7c046ec` — `fix(rag-ingestion): round-2 review fixes for the JIT retriever cutover` (13 files changed excluding this artifact commit).

## Orchestrator verification note (post-fixer, pre-round-3)

The fixer flagged that fixing M-2.4 (marker-check exception propagation) broke two integration tests relying on the exact bug being fixed — surfaced only because the fixer proactively ran `-m integration` beyond the task's specified default command. Orchestrator read both diffs directly (`git show 7c046ec` on the two files) before accepting: both removed assertions were calling `check_commit_marker_complete`/its async twin directly against a collection deliberately never created (a call shape `search()` itself never produces — it always ensures the collection first via `async_ensure_collection_and_indexes`), and in both cases a stronger, more direct check already sits alongside the removed line (`clean_collection` fixture's guarantee in one case, an adjacent `collection_exists()` assertion in the other). Confirmed as legitimate necessary fallout, not test-weakening — no further action needed.
