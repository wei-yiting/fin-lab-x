# Fix Round 1

> Fixer: Claude (general-purpose subagent) | Date: 2026-08-19

## Fixed

| Issue ID | How Fixed | Files Changed |
|----------|-----------|---------------|
| B-1.1 / SP-1.1 | `search()` now raises `ValueError` when `filters` is `None`/empty/lacks `"ticker"` (checked before any Qdrant/EDGAR work). `_build_query_filter(ticker, fiscal_year)` tightened to require both as concrete values — always builds a 2-condition filter now, no more optional branching. `fiscal_year`-without-`ticker` is resolved as a side effect. | `backend/ingestion/sec_dense_pipeline/retriever.py`, `backend/tests/ingestion/sec_dense_pipeline/unit/test_retriever.py` |
| M-1.1 | New standalone `backend/scripts/embed_sec_filings_html.py` restores the pre-cutover batch-ingest logic (`SECFilingPipeline` + `sec_dense_pipeline_html.vectorizer.ingest_filing`) against the frozen collection, keeping the `--year` flag name. Revived `test_batch_cli_failure_isolation_and_summary`, retargeted at the new script. Updated 3 docs to point at it. | `backend/scripts/embed_sec_filings_html.py` (new), `backend/tests/ingestion/sec_dense_pipeline_html/integration/test_ingest.py`, `backend/ingestion/sec_dense_pipeline_html/README.md`, `backend/scripts/README.md`, `backend/evals/scenarios/sec_retrieval/README.md` |
| M-1.2 / SP-1.3 | Restructured the `SEC_DISABLE_JIT` guard into two points: `search()` blocks only when `fiscal_year` is omitted (since resolving "latest" itself needs EDGAR); `_ensure_ingested()` blocks only after a genuine marker miss (checked *after* the marker-hit early-return), so an already-complete explicit-year hit always succeeds under the flag. | `backend/ingestion/sec_dense_pipeline/retriever.py`, `backend/tests/ingestion/sec_dense_pipeline/unit/test_retriever.py` |
| M-1.3 (+ Qdrant-5xx half of SP-1.5) | Verified against the installed qdrant-client 1.17.1 source (`api_client.py`) that `send_inner` wraps *every* transport exception (including `httpx.ConnectError/ConnectTimeout/ReadTimeout`) into `ResponseHandlingException` before it reaches caller code, and that response-validation failures (`pydantic.ValidationError`) use the same wrapper. Removed the now-confirmed-dead raw-`httpx.*` except-clause; `ResponseHandlingException` is now only classified transient when `exc.source` is connection/timeout-shaped; added `UnexpectedResponse` 5xx→transient classification (4xx untouched). | `backend/ingestion/sec_dense_pipeline/vectorizer.py`, `backend/tests/ingestion/sec_dense_pipeline/unit/test_vectorizer.py` |
| M-1.4 / SP-1.4 | Added `resolve_latest_fiscal_year_with_retry` in `vectorizer.py` (mirrors `parse_filing_with_retry`'s pattern/style), used from both `retriever.py::search()` and `embed_sec_filings.py::_embed_one()` instead of calling `_resolve_latest_fiscal_year` unwrapped. | `backend/ingestion/sec_dense_pipeline/vectorizer.py`, `backend/ingestion/sec_dense_pipeline/retriever.py`, `backend/scripts/embed_sec_filings.py`, plus corresponding test files |
| SP-1.6 | `_embed_one()` takes an optional `resolved_holder` dict, populated as soon as resolution completes, independent of later parse/ingest success. `main()`'s except-branch reads `resolved_holder.get("fiscal_year", args.fiscal_year)` instead of always falling back to `args.fiscal_year`. | `backend/scripts/embed_sec_filings.py`, `backend/tests/scripts/test_embed_sec_filings.py` |
| M-1.5 | `_ensure_ingested()` re-checks the commit marker (`async_check_commit_marker_complete`) immediately after successfully claiming the in-flight slot; if now complete, releases the slot and returns `cache_hit=True` without parsing/ingesting. | `backend/ingestion/sec_dense_pipeline/retriever.py`, `backend/tests/ingestion/sec_dense_pipeline/unit/test_retriever.py` |
| M-1.6 (doc-only) | Reworded `backend/scripts/README.md`'s stale "observability lives in the `search()` JIT path only" claim to say tracing for the new JIT path ships in a follow-up ticket. | `backend/scripts/README.md` |
| m-1.1 | Removed the `DEV-160` reference from `sec_dense_pipeline_html/README.md`; the descriptive rationale now stands alone. Done together with M-1.1's edit to the same paragraph/file in one coherent pass. | `backend/ingestion/sec_dense_pipeline_html/README.md` |
| S-1.1 | `_build_query_filter` now returns just `models.Filter` (no `applied` dict). Done together with B-1.1/SP-1.1 in one pass since both changed this function's signature. | `backend/ingestion/sec_dense_pipeline/retriever.py`, `backend/tests/ingestion/sec_dense_pipeline/unit/test_retriever.py` |

## Not Fixed

None — all 10 items landed.

## Reverted

None — no fix broke a test that required reverting.

## Tests Run

| Test Command | Result | Notes |
|--------------|--------|-------|
| `pytest backend/tests/ingestion/sec_dense_pipeline/ backend/tests/ingestion/sec_dense_pipeline_html/ backend/tests/scripts/ backend/tests/common/` | 216 passed, 39 deselected | The required gate command from the task, plus `backend/tests/common/` since the fix touches shared retry/error infra |
| `pytest backend/tests/ingestion/sec_dense_pipeline/integration/ backend/tests/ingestion/sec_dense_pipeline_html/integration/ -m integration` | 39 passed | Ran against real local Qdrant (confirmed running) for extra confidence beyond the required command — includes the revived batch-CLI test and the real-concurrency race test |
| `pytest backend/tests/` (full default suite) | 1266 passed, 61 deselected | Collateral-damage check across the whole backend |
| `ruff check` on all changed/new files | All checks passed | |
| `ruff format --check backend/` | 213 files already formatted | Matches CI's lint job exactly |

## Tests Added or Modified

| Test File | Added/Modified | What It Tests |
|-----------|----------------|---------------|
| `test_retriever.py` | Removed `test_build_query_filter_none_none_is_unfiltered_but_excludes_markers`, `test_build_query_filter_ticker_only`, `test_search_without_ticker_filter_skips_jit_entirely` | Locked in the now-forbidden unfiltered/partial-filter behavior |
| `test_retriever.py` | Added `test_search_raises_when_filters_is_none`, `test_search_raises_when_filters_empty`, `test_search_raises_when_fiscal_year_given_without_ticker` | `search()` rejects missing/absent ticker |
| `test_retriever.py` | Added `test_ensure_ingested_recheck_after_claim_catches_completed_race`, `test_ensure_ingested_raises_jit_disabled_on_miss` | Stale-marker race fix; disable-flag fires only on genuine miss |
| `test_retriever.py` | Added `test_search_disable_jit_allows_hot_hit_with_explicit_fiscal_year`, `test_search_disable_jit_still_blocks_explicit_fiscal_year_marker_miss` | Both halves of the SEC_DISABLE_JIT AC at the `search()` level |
| `test_retriever.py` | Modified `test_search_resolves_latest_fiscal_year_when_omitted` | Patch target renamed to the new retry wrapper |
| `test_retriever.py` | Modified `test_search_raises_corpus_unavailable_when_collection_missing`, `test_search_wraps_embedding_failure`, `test_search_maps_404_unexpected_response_to_corpus_unavailable`, `test_search_closes_client_even_on_failure` | Updated to pass a required ticker filter (previously called `search()` with no filters at all, which now hits the new mandatory-ticker `ValueError` before reaching the behavior under test) |
| `test_vectorizer.py` | Added `test_resolve_latest_fiscal_year_with_retry_retries_transient_then_succeeds`, `test_resolve_latest_fiscal_year_with_retry_does_not_retry_permanent_failure` | New retry wrapper, matching `parse_filing_with_retry`'s test pattern |
| `test_vectorizer.py` | Removed `test_ingest_filing_with_retry_classifies_response_handling_exception` (locked in "all `ResponseHandlingException` is transient"); replaced `..._classifies_connect_error...` with `..._classifies_connection_shaped_cause...` | Old tests didn't match qdrant-client's real wrapped-exception shape |
| `test_vectorizer.py` | Added `test_ingest_filing_with_retry_does_not_retry_validation_error_shaped_cause`, `test_ingest_filing_with_retry_classifies_5xx_unexpected_response_and_retries`, `test_ingest_filing_with_retry_does_not_retry_4xx_unexpected_response` | New classification rules, using real `ResponseHandlingException`/`UnexpectedResponse`/`pydantic.ValidationError` shapes |
| `test_embed_sec_filings.py` | Modified 3 tests (patch target rename), added `test_main_reports_resolved_year_when_ingest_fails_after_resolution` | Resolved year survives into the failure-branch summary row |
| `test_ingest.py` (sec_dense_pipeline_html/integration) | Revived `test_batch_cli_failure_isolation_and_summary`, retargeted at `embed_sec_filings_html` | Operator backfill script's failure isolation and Qdrant-observable summary |

## Commit

`1236497` — `fix(rag-ingestion): round-1 review fixes for the JIT retriever cutover` (11 files changed, 708 insertions, 148 deletions).

## Orchestrator follow-up (post-fixer, pre-round-2)

The fixer flagged one related but out-of-scope finding while investigating item M-1.1 (correctly did not fix it — not one of the 10 agreed items):
`backend/ingestion/sec_dense_pipeline_html/retriever.py` L254's `CorpusUnavailableError` message still told operators to run `embed_sec_filings.py` — that script no longer targets the frozen collection since this same fix round created `embed_sec_filings_html.py` for that purpose. This is a direct, mechanical consequence of the already-ratified M-1.1 decision (not a new scope decision), so the orchestrator applied the one-line fix directly rather than spinning up a fresh discussion-gate round: `embed_sec_filings.py` → `embed_sec_filings_html.py` in that message string. Committed separately (see git log) before Round 2 dispatch.
