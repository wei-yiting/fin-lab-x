# Fix Round 9 (envelope-review fixes)

> Fixer: Claude (general-purpose subagent) | Date: 2026-08-20
> Responds to review-round-9.md (post-convergence envelope review by a separate agent)
> per its Discussion Gate Outcome: F-9.1/9.2 correctness, F-9.3 option B (user decision),
> F-9.4/9.5-docs/9.7/9.9/9.10 accepted; F-9.6 dismissed (standing round-1 user decision),
> F-9.8 deferred.

## Fixed

| Issue ID | How Fixed | Files Changed |
|---|---|---|
| F-9.1 | Autouse `_unset_disable_jit` fixture (monkeypatch `delenv`) in the new pipeline's shared conftest, covering `unit/` + `integration/`; deliberate `setenv` tests still win. `backend/tests/scripts/` checked — no exposure (script never reads the flag, tests mock parse/ingest). | `backend/tests/ingestion/sec_dense_pipeline/conftest.py` |
| F-9.2 | `EmbeddingServiceError` moved to `sec_dense_pipeline/common.py` (vectorizer can't import from retriever), re-imported in `retriever.py`. `ingest_filing`'s `_embed_texts` call wrapped: `except FinLabError: raise` then `except Exception → EmbeddingServiceError` — already-classified taxonomy errors pass through unrelabeled. Cold-path test added running the real `ingest_filing_with_retry` chain. | `common.py`, `vectorizer.py`, `retriever.py`, `unit/test_retriever.py` |
| F-9.3 (option B) | `_TRANSIENT_SOURCE_TYPES` + `exc.source` inspection + ~50-line comment deleted. New classification: any `ResponseHandlingException` → `TransientError` (blanket single retry); `UnexpectedResponse` 5xx → `TransientError`; 4xx and everything else propagates. Tests reduced to 3. | `vectorizer.py`, `unit/test_vectorizer.py` |
| F-9.4 | Stdlib-pinning `set.discard` test deleted; missing-key coverage deduped to one parametrized `search()`-level test; log assertions trimmed to key fields (log channel itself kept — AC-mandated); repeated patch stack extracted into module-level `search_env` fixture consumed by 17 tests. | `unit/test_retriever.py` |
| F-9.5 (docs half) | `docs/observability.md` `_html` batch CLI reference → `embed_sec_filings_html.py`; `docs/agent_architecture.md` and `docs/file_structure.md` corrected only where this PR made them false; pipeline README's "single JIT query entry point" softened + stale internals references (taxonomy/sync-check) updated. Statements true until DEV-142 left untouched. | `docs/observability.md`, `docs/agent_architecture.md`, `docs/file_structure.md`, `backend/ingestion/sec_dense_pipeline/README.md` |
| F-9.7 | Sync `check_commit_marker_complete` deleted; `_marker_is_complete` inlined into the async function; `__init__.py` exports updated; `test_common.py` async-only; integration asserts switched to raw client `retrieve()`. Frozen `_html` copy untouched. | `common.py`, `__init__.py`, `unit/test_common.py`, `integration/test_search.py`, `integration/test_ingest.py` |
| F-9.9 | `_point_to_chunk` = `payload is None` guard + `Chunk(**payload, score=point.score)`. Verified against pydantic 2.12.5: extra keys ignored, missing required field → `ValidationError` (a `ValueError` subclass). Call-site except tuple narrowed to `ValueError`. | `retriever.py`, `unit/test_retriever.py` |
| F-9.10 | Public `@retry_transient resolve_latest_fiscal_year` added to `backend/common/sec_core.py` (new function only, freeze-compliant); `parse_filing_with_retry` moved to `sec_text_pipeline/parser.py` (fixer confirmed only the `ParsedFiling` schema is frozen there, not the module). Vectorizer copies deleted; all callers and test patch-targets re-pointed; wrapper tests relocated next to their new homes. `sec_filing_tools.py` untouched (pre-existing asymmetry, out of scope). | `sec_core.py`, `parser.py`, `vectorizer.py`, `retriever.py`, `embed_sec_filings.py`, `test_sec_core.py`, `test_parser.py`, `test_embed_sec_filings.py`, `unit/test_retriever.py` |

## Not Fixed

None in scope. (F-9.6 dismissed, F-9.8 deferred — untouched per the gate.)

## Tests Run

| Test Command | Result | Notes |
|---|---|---|
| `uv run pytest backend/tests/ -q` | 1274 passed, 61 deselected | Full suite |
| `SEC_DISABLE_JIT=1 uv run pytest backend/tests/ingestion/sec_dense_pipeline/ backend/tests/scripts/ -q` | 76 passed | F-9.1 acceptance (was 2 failures under this env) |
| `uv run pytest backend/tests/ingestion/sec_dense_pipeline/ -m integration -q` | 12 passed | Also green with `SEC_DISABLE_JIT=1` |
| `ruff check` / `ruff format --check` | clean | |
| pyright (pipeline + sec_core + parser) | 16 errors, all pre-existing | Verified identical on a temp HEAD worktree — zero new |

## Net test-line delta

Tests 1,272 inserted lines (was 1,680) vs production 827 — ratio **2.18× → ~1.54×**, now
under the §5 rule-5 ~2× threshold.

## Commit

`6b5a0ee` — `refactor(rag-ingestion): envelope-review fixes — retry altitude, error taxonomy, test trim`

## Fixer judgment call (flagged, orchestrator concurs)

F-9.2's ingest-side wrap uses `except FinLabError: raise` before the generic
`Exception → EmbeddingServiceError` wrap — slightly different from the query path's bare
`except Exception`, deliberately: an already-classified taxonomy error (e.g. a
`TransientError` injected at the embed seam, pinned by two integration tests) must not be
re-labeled. Taxonomically more correct; accepted.

## Orchestrator verification note (post-fixer, pre-round-10)

Spot-checked directly: `_TRANSIENT_SOURCE_TYPES` gone from `vectorizer.py`;
`EmbeddingServiceError` now defined in `common.py`; sync `check_commit_marker_complete`
gone; `parse_filing_with_retry` at `parser.py:113` and `resolve_latest_fiscal_year` at
`sec_core.py:376`; `Chunk(**payload, score=point.score)` at `retriever.py:218`. All match
the gate decisions. Dispatching a round-10 confirmation review pass on both axes.
