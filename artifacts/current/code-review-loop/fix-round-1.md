# Fix Round 1

> Fixer: claude-sonnet-5 subagent | Date: 2026-08-11 | Commit: `a338e3a`

Four findings were ratified by the user as no-change decisions before this round
(recorded in DEV-135's「Review round 1 裁決紀錄」section):

| Issue ID | Disposition |
|----------|-------------|
| B-1.1 (concurrent ingest) | Deferred to DEV-137 — no caller exists in this slice, so no concurrent invocation path; registered as a DEV-137 agent todo. |
| M-1.1 (prelude size cap) | No change — the evidence-gate guards live upstream in DEV-133's detection layer (3,000-char validity threshold, 72-probe calibrated); ingest trusts the producer contract (single definition point). |
| M-1.2 (zero production caller) | Ratified as an explicit envelope §0 reachability exception, following the DEV-132 (`StructuredItem`) and DEV-141 (`retry_transient`) precedents; first caller is DEV-137. Recorded in issue + will be in PR body. |
| M-1.3 (missing tracing) | Deferred to DEV-137 — `traced_span` only emits inside an active outer trace, which the DEV-137 JIT chain establishes; registered as a DEV-137 agent todo. |

## Fixer report (verbatim)

### Fixed

| Issue ID | How Fixed | Files Changed |
|----------|-----------|---------------|
| B-1.2 | Checked `sec_core.parse_item_number()` first — it is agent-facing whitelist validation (raises `SectionNotFoundError` for keys outside `TENK_STANDARD_TITLES`), so reusing it would reject schema-valid parsed items. Instead, normalize once per Item in `build_chunk_payloads` (`item_key = item.item.strip().lower()`); payload gets `item_key`, `header_path` display layer uses `item_key.upper()` ("Item 7A"). | `backend/ingestion/sec_dense_pipeline/chunking.py`, `backend/tests/ingestion/sec_dense_pipeline/unit/test_chunking.py` |
| B-1.3 | New `EmptyIngestError(SECError)` defined in `vectorizer.py` (sec_core untouched, only-add respected). `build_chunk_payloads(filing)` is now called at the top of `ingest_filing`, before the Qdrant client is even created; empty result raises with ticker/fiscal_year in the message — no marker, no wipe, no collection creation. Integration test asserts `pytest.raises(EmptyIngestError)` plus `collection_exists() is False` and `check_commit_marker_complete() is False` (retrieval side sees absent). | `backend/ingestion/sec_dense_pipeline/vectorizer.py`, `backend/tests/ingestion/sec_dense_pipeline/integration/test_ingest.py` |
| m-1.1 | Verified pinned signature via `inspect.signature(OpenAIEmbedding.__init__)` — it accepts `async_http_client: Optional[httpx.AsyncClient]`. `_embed_texts` now creates a caller-owned `httpx.AsyncClient()`, injects it via `async_http_client=`, and does `await async_client.aclose()` in `finally`; the private `embed_model._aclient` access is gone. | `backend/ingestion/sec_dense_pipeline/vectorizer.py` |
| m-1.2 | `ChunkPayload(TypedDict)` with all 13 build-time fields plus `ingested_at: NotRequired[str]`; `build_chunk_payloads -> list[ChunkPayload]`; vectorizer infers the typed list (its inline `payloads` annotation removed); unit-test fixture annotation updated. | `backend/ingestion/sec_dense_pipeline/chunking.py`, `backend/ingestion/sec_dense_pipeline/vectorizer.py`, `backend/tests/ingestion/sec_dense_pipeline/unit/test_chunking.py` |
| m-1.3 | New yielding `qdrant_client` fixture (`try/finally: client.close()`) in integration conftest; `clean_collection` now depends on it (setup + cleanup share the client); all six integration tests take the fixture; `_client()` helper deleted. | `backend/tests/ingestion/sec_dense_pipeline/integration/conftest.py`, `backend/tests/ingestion/sec_dense_pipeline/integration/test_ingest.py` |
| m-1.4 | `docs/file_structure.md` §2.4: both HTML pipelines marked "Frozen A/B baseline (deleted whole at sunset)", `sec_text_pipeline/` and `sec_dense_pipeline/` entries added; §2.8 test map now lists all five ingestion test dirs. `backend/README.md` ingestion bullet rewritten (new path + frozen baselines + fundamentals). Root `README.md` tree block updated with all five pipelines and frozen annotations. English, minimal diff. | `docs/file_structure.md`, `backend/README.md`, `README.md` |
| m-1.5 | `_EMBED_DIM` and `QdrantClient` imports moved to module top in integration conftest; `_EMBED_DIM` in-function import in `test_ingest.py` moved to the top-level vectorizer import (patching unaffected — string targets). | `backend/tests/ingestion/sec_dense_pipeline/integration/conftest.py`, `backend/tests/ingestion/sec_dense_pipeline/integration/test_ingest.py` |
| S-1.1 | Module README gains an Environment Variables table (all 6 vars with defaults) and the extension note: payload filter field changes must be applied in lockstep to payload construction, index bootstrap, marker exclusion, and retrieval side. Also one sentence in the Integrity section documenting `EmptyIngestError`. | `backend/ingestion/sec_dense_pipeline/README.md` |

### Not Fixed (with reason)

| Issue ID | Reason |
|----------|--------|
| — | (none) |

### Reverted (fix broke tests)

| Issue ID | What Broke | Reverted Files | Suggested Alternative |
|----------|------------|----------------|----------------------|
| — | — | — | — |

### Tests Run

| Test Command | Result | Notes |
|--------------|--------|-------|
| `uv run ruff format backend/ && uv run ruff check backend/` | Pass | 187 files unchanged; all checks passed |
| `uv run pytest backend/tests/ingestion/sec_dense_pipeline/ -q -m "integration or not integration"` | Pass | 19 passed (local Qdrant on :6333) |
| `uv run pytest backend/tests/ -q` | Pass | 994 passed, 55 deselected |

### Tests Added or Modified

| Test File | Added/Modified | What It Tests |
|-----------|----------------|---------------|
| `backend/tests/ingestion/sec_dense_pipeline/unit/test_chunking.py` | Added `test_item_is_normalized_at_the_contract_boundary` (parametrized: `"7A"`, `" 7a "`, `" 7A "`) | B-1.2: schema-valid mixed-case/whitespace `item` → payload `"7a"`, header_path `"Item 7A."` |
| `backend/tests/ingestion/sec_dense_pipeline/integration/test_ingest.py` | Added `test_empty_filing_raises_and_leaves_no_trace` | B-1.3: empty `FlatItem.text` filing → `EmptyIngestError`, collection never created, marker check false |
| `backend/tests/ingestion/sec_dense_pipeline/integration/test_ingest.py` | Modified | All tests use shared `qdrant_client` fixture; `_client()` removed; `_EMBED_DIM` imported at module top |
| `backend/tests/ingestion/sec_dense_pipeline/integration/conftest.py` | Modified | Yielding `qdrant_client` fixture with `finally: close()`; `clean_collection` reuses it; lazy imports hoisted |

### Commit

| SHA | Message |
|-----|---------|
| `a338e3a` | `fix(rag-ingestion): address review round 1 — item normalization, empty-ingest guard, typing, docs` |

Fixer note: for m-1.1 the pinned `llama-index-embeddings-openai` does support `async_http_client` (verified via `inspect.signature`), so the documented-API injection path was taken — no pinned-version workaround comment was needed.
