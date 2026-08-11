# Code Review Round 2

> Reviewer: claude-sonnet-5 | Date: 2026-08-11
>
> Provider note: this round ran on the Claude fallback reviewer (read-only subagent,
> session-isolated). Two consecutive Codex dispatch attempts hung at turn start with
> zero activity for 20–30 minutes each (jobs `task-mso3n1p7-sluqmy`, `task-mso4rbep-zn2ovk`,
> both cancelled) — Codex-side instability, not a review-content failure. Round 1's
> cross-model review (gpt-5.6-sol) stands.

## Fix Verification

| Round 1 Issue | Verdict | Evidence |
|---------------|---------|----------|
| B-1.2 | ✅ Verified fixed | `backend/ingestion/sec_dense_pipeline/chunking.py:86` normalizes once per Item (`item_key = item.item.strip().lower()`); payload uses `item_key` (line 114), display label uses `item_key.upper()` (line 87). Parametrized test `test_item_is_normalized_at_the_contract_boundary` (`backend/tests/ingestion/sec_dense_pipeline/unit/test_chunking.py:142-163`) covers `"7A"` / `" 7a "` / `" 7A "` and asserts both payload key `"7a"` and `header_path` prefix `Item 7A.`. |
| B-1.3 | ✅ Verified fixed | `backend/ingestion/sec_dense_pipeline/vectorizer.py:46-51` defines `EmptyIngestError(SECError)` (SECError extends FinLabError — taxonomy-conformant); guard at lines 91-98 runs `build_chunk_payloads` before the `AsyncQdrantClient` is even constructed (line 103), so no marker, no wipe, no collection creation. Integration test `test_empty_filing_raises_and_leaves_no_trace` (`backend/tests/ingestion/sec_dense_pipeline/integration/test_ingest.py:111-139`) asserts `not qdrant_client.collection_exists(TEST_COLLECTION)` — the strongest possible "no mutation" assertion. The redundant late `build_chunk_payloads` call was removed (payloads built once, reused). |
| m-1.1 | ✅ Verified fixed | `backend/ingestion/sec_dense_pipeline/vectorizer.py:67-76`: caller-owned `httpx.AsyncClient()` injected via `async_http_client=`, `await async_client.aclose()` in `finally` (covers constructor failure too). Independently verified via `inspect.signature` against the installed pinned llama-index-embeddings-openai 0.6.0: `async_http_client: Optional[httpx.AsyncClient] = None` exists. No private `_aclient` access remains. |
| m-1.2 | ✅ Verified fixed | `backend/ingestion/sec_dense_pipeline/chunking.py:33-53`: `ChunkPayload(TypedDict)` with all 13 fields, `ingested_at: NotRequired[str]` (correct — stamped later by the vectorizer); `build_chunk_payloads -> list[ChunkPayload]` (lines 69, 80). Unit test fixture annotation updated (`test_chunking.py:39`). |
| m-1.3 | ✅ Verified fixed | `backend/tests/ingestion/sec_dense_pipeline/integration/conftest.py:40-47`: yielding `qdrant_client` fixture with `finally: client.close()`; `clean_collection` (lines 50-57) depends on it, so teardown ordering is correct (cleanup runs before close). `_client()` helper is gone; all six integration tests take the fixture. |
| m-1.4 | ✅ Verified fixed | `docs/file_structure.md:63-66` adds `sec_text_pipeline/` + `sec_dense_pipeline/` entries and marks both `_html` trees "Frozen A/B baseline (deleted whole at sunset)"; §2.8 test map (line 91) includes both new test dirs. `backend/README.md:13` and root `README.md:239-242` consistent. |
| m-1.5 | ✅ Verified fixed | `integration/conftest.py:3-11` and `integration/test_ingest.py:9-30`: all imports at module top (`QdrantClient`, `_EMBED_DIM`, `numpy`); no function-body imports remain in either file. |
| S-1.1 | ✅ Verified fixed | `backend/ingestion/sec_dense_pipeline/README.md:29-38` env-var table (all six vars match code defaults — cross-checked against `chunking.py:59-60` and `vectorizer.py:39-42, 56, 101`); lines 40-43 lockstep extension note naming all four touch points; lines 52-54 document `EmptyIngestError` semantics. |

(User-ratified items B-1.1 / M-1.1 / M-1.2 / M-1.3: no invalidating evidence found — repo-wide grep confirms still zero production callers of `ingest_filing`, consistent with the recorded DEV-137 premise. Closed.)

Verification run: `pytest backend/tests/ingestion/sec_dense_pipeline/ -q -m "integration or not integration"` → 19 passed; `ruff check` + `ruff format --check` clean on all changed Python files.

## Summary

| Metric | Count |
|--------|-------|
| Total NEW issues | 2 |
| Blocking | 0 |
| Major | 0 |
| Minor | 1 |
| Suggestion | 1 |

## Issues

### [Minor] m-2.1: `EmptyIngestError` is part of the public contract but missing from the package surface

**File:** `backend/ingestion/sec_dense_pipeline/__init__.py:20-25`
**Problem:** The B-1.3 fix made `EmptyIngestError` part of the observable contract of the package's sole entry point — the module README documents it as raised by ingest, and the future JIT caller (DEV-137) must catch it to render the legible failure required by envelope §4 (JIT failure legibility zone). Yet the package `__init__` — whose docstring explicitly claims "Public surface: `ingest_filing` plus the marker helpers" — neither imports nor lists it in `__all__`. A caller doing `from backend.ingestion.sec_dense_pipeline import ...` (the pattern the package sets up) cannot reach the one exception the entry point is documented to raise without dipping into the `vectorizer` submodule.
**Fix:** Add `EmptyIngestError` to the `__init__` import and `__all__` (and the docstring's public-surface sentence).

### [Suggestion] s-2.1: Inconsistent env-read timing inside `vectorizer.py`

**File:** `backend/ingestion/sec_dense_pipeline/vectorizer.py:39-40`
**Problem:** `SEC_EMBED_MODEL` / `SEC_EMBED_DIM` are read once at import time, while `SEC_TEXT_QDRANT_COLLECTION` (line 56) and `SEC_CHUNK_SIZE`/`SEC_CHUNK_OVERLAP` (`chunking.py:59-60`) are read per call. The integration suite relies on the call-time behavior to `monkeypatch.setenv` the collection; the same technique would silently not work for the embed vars. This mirrors the frozen `_html` baseline's pattern and no in-repo consumer is currently affected, so per envelope §7.4 this is optional polish — mentioned once, not blocking.
**Fix:** If touched anyway, read all env vars at call time (or none); otherwise leave as is.

---

# Spec Conformance Round 2

Not dispatched — per the skill's dispatch criteria (round 2+ runs only when the previous
round has SP- findings to confirm or still open; round 1 had zero SP- findings).
