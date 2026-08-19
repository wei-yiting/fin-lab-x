# Code Review Round 4

> Reviewer: gpt-5.6-sol | Date: 2026-08-19

## Summary

| Metric | Count |
|--------|-------|
| Total issues | 4 |
| Blocking | 0 |
| Major | 2 |
| Minor | 2 |
| Suggestion | 0 |
| Library checks | 0 |

Round 3 的五項修正均已落地。Fresh review 另發現兩個 boundary-validation 缺口，以及兩個測試／文件維護問題。

## Previous Round Status

| # | Issue ID | Status | Notes |
|---|----------|--------|-------|
| 1 | M-3.1 | ✅ Fixed | `_TRANSIENT_SOURCE_TYPES` 明確包含 `httpx.RemoteProtocolError`，未包含較廣的 `ProtocolError`，因此 `LocalProtocolError` 仍排除。註解與 tests 均反映已 settled 的分類理由。 |
| 2 | M-3.2 | ✅ Fixed | `search()` signature 為 `filters: SearchFilters`，沒有 default 或 `None` union；README 也明確說明此參數必填。 |
| 3 | M-3.3 | ✅ Fixed within reported scope | `_point_to_chunk()` 明確拒絕 `payload is None`；per-point conversion 將 `ValueError`／`pydantic.ValidationError` 映射成 `CorpusUnavailableError`。使用 `.venv/bin/pyright --pythonpath .venv/bin/python` 驗證為 0 errors；相關 targeted unit suites 共 59 tests 通過。另一個會繞過 validation 的 required-field fallback 另列 M-4.2。 |
| 4 | m-3.1 | ✅ Fixed | 對 cumulative non-artifact diff 搜尋 `DEV-\d+` 與 finding-ID patterns，沒有命中。 |
| 5 | m-3.2 | ✅ Fixed | concurrency integration test 已使用兩個 `asyncio.Event`，確保第二個 caller 在第一個 caller 已 claim slot 且 ingest 尚未完成時進場。Barrier 的 failure-path hang 風險另列 m-4.2。 |

## Issues

### [Major] M-4.1: Runtime filter validation 仍假設輸入一定是 mapping
- **File:** `backend/ingestion/sec_dense_pipeline/retriever.py` L162–168, L320
- **Problem:** `search()` 在 `_validate_filters()` 前執行 `"ticker" not in filters`，而 `_validate_filters()` 隨後直接使用 `set(filters)` 與 `filters["ticker"]`。非 mapping 的 untyped／deserialized input 不會得到文件承諾的 legible `ValueError`：實際驗證顯示 `filters=123` 拋出 raw `TypeError: argument of type 'int' is not iterable`，`filters=["ticker"]` 則拋出 raw indexing `TypeError`。這違反 design-envelope §4 的 basic shape validation 與 stable error contract。Round 2／3 對 M-2.3 的驗證只涵蓋 dict-shaped invalid values，因而錯誤地將 top-level container shape 視為已完整驗證。
- **Fix:** 在任何 membership／index 操作前先拒絕非-dict input，並維持 public signature 為 required `SearchFilters`。新增 integer、list 等非-mapping cases，確認它們在任何 Qdrant／EDGAR I/O 前收到一致的 `ValueError`。

### [Major] M-4.2: Missing required `ingested_at` 被靜默轉成空字串
- **File:** `backend/ingestion/sec_dense_pipeline/retriever.py` L234, L391–407
- **Problem:** `_point_to_chunk()` 使用 `payload.get("ingested_at", "")`。因此缺少 required persisted field 的 Qdrant payload 會成功產生 `Chunk(ingested_at="")`，而不是進入 M-3.3 新增的 malformed-payload mapping。README 的 per-chunk contract 明列 `ingested_at`，且 vectorizer 在每次 upsert 前都會寫入它；缺少此欄位代表 corpus corruption，不是合法 optional state。這是 design-envelope §4 禁止的 silent partial external-data acceptance。M-3.3 的 `None` payload 與 Pydantic validation 修正本身成立，但先前 verification 沒有檢查用 fallback 繞過 validation 的欄位。
- **Fix:** 將 persisted required fields（包含 `ingested_at`）視為真正 required；缺欄時以帶 point ID context 的 `CorpusUnavailableError` 回報。若 `_point_to_chunk()` 以 key access 驗證，per-point mapping 也應涵蓋 `KeyError`，並新增 missing-`ingested_at` test。

### [Minor] m-4.1: Module-level retry 說明已與實作矛盾
- **File:** `backend/ingestion/sec_dense_pipeline/vectorizer.py` L12–14
- **Problem:** Module docstring 仍寫著「No retry wrapper here」並稱 recovery 是由 operator re-run，但同一模組現在提供 `@retry_transient` 的 `ingest_filing_with_retry()`，會自動重跑 transient Qdrant failures。後方 function docstring 才記錄真正的 boundary，前後說法互相衝突；`backend/ingestion/sec_dense_pipeline/README.md` L62–64 也使用容易被理解成整個 ingest path 沒有 retry 的相似措辭。
- **Fix:** 明確區分 bare `ingest_filing()`、Qdrant-only `ingest_filing_with_retry()` 與 OpenAI SDK internal retry，移除「No retry wrapper here」這個已過時的概括。

### [Minor] m-4.2: Barrier test 在第一個 task 提早失敗時會無限等待
- **File:** `backend/tests/ingestion/sec_dense_pipeline/integration/test_search.py` L176–189
- **Problem:** Test 直接等待 `await ingest_claimed.wait()`。如果第一個 `search()` 在到達 patched ingest 前因 regression 失敗，`first_call` 會結束但 event 永遠不會 set，測試不會呈現原始 failure，而會掛住 integration gate。Repository 雖安裝 `pytest-timeout`，但 pytest config 沒有全域 timeout。
- **Fix:** 對 barrier wait 使用 bounded timeout，或同時等待 event 與 `first_call`，在 task 提早完成時立即傳播其 exception；cleanup path 應確保 release 並 await／cancel task。

## Documentation Gaps

| Folder | Missing |
|--------|---------|
| None | None |

## Official Standards Check

| Library | Version | API Used | Status | Notes |
|---------|---------|----------|--------|-------|
| None | — | — | N/A | 本輪沒有新的 external library usage；依 prompt 未重做 Round 1–3 已 settled 的 httpx／qdrant-client verification。 |

---

# Spec Conformance Round 4

> Reviewer: gpt-5.6-sol | Date: 2026-08-19

## Summary

| Metric | Count |
|--------|-------|
| Total findings | 0 |
| Missing | 0 |
| Scope creep | 0 |
| Misimplemented | 0 |

## Findings

No findings.

The three Round 3 behavior changes remain within the approved scope:

- Required `filters` leaves spec-compliant ticker/year callers unaffected.
- `RemoteProtocolError` receives at most one retry through `retry_transient`.
- Malformed-payload handling is additive; well-formed `Chunk` conversion is unchanged.

## Covered Requirements

✅ Cold searches perform parse → ingest → retrieve within one `search()` call — `backend/ingestion/sec_dense_pipeline/retriever.py`

✅ Hot searches use complete commit markers and skip parsing and ingestion — `backend/ingestion/sec_dense_pipeline/retriever.py`

✅ Filing-store parsing cache and Qdrant commit markers jointly support the cold/hot path — `backend/ingestion/sec_dense_pipeline/retriever.py`

✅ `cache_hit` correctly distinguishes hot hits, completed races, and JIT ingestion through logs — `backend/ingestion/sec_dense_pipeline/retriever.py`

✅ `SEC_DISABLE_JIT=1` blocks cold EDGAR/JIT work while permitting explicit-year hot hits — `backend/ingestion/sec_dense_pipeline/retriever.py`

✅ `filters` is genuinely required, while valid `{"ticker": ..., "fiscal_year": ...}` callers remain unaffected — `backend/ingestion/sec_dense_pipeline/retriever.py`

✅ Every successful search applies mandatory `ticker` and resolved `fiscal_year` Qdrant conditions — `backend/ingestion/sec_dense_pipeline/retriever.py`

✅ Omitted `fiscal_year` resolves through the shared latest-year resolver and is applied to retrieval — `backend/ingestion/sec_dense_pipeline/retriever.py`

✅ The batch script uses the structured parser/vectorizer contract and keeps `--fiscal-year` optional — `backend/scripts/embed_sec_filings.py`

✅ Batch summaries report the resolved fiscal year even after subsequent parse or ingestion failure — `backend/scripts/embed_sec_filings.py`

✅ JIT parsing and latest-year resolution use the shared single-retry policy — `backend/ingestion/sec_dense_pipeline/vectorizer.py`

✅ Qdrant timeout, network, remote-protocol, and 5xx failures receive at most one repo-owned retry — `backend/ingestion/sec_dense_pipeline/vectorizer.py`

✅ Permanent Qdrant failures, including local protocol errors, 4xx responses, and validation failures, are not retried — `backend/ingestion/sec_dense_pipeline/vectorizer.py`

✅ Same-key concurrent JIT uses atomic in-process claiming, immediate legible rejection, post-claim marker recheck, and `finally` cleanup — `backend/ingestion/sec_dense_pipeline/retriever.py`

✅ Retrieval and structured ingestion consistently use `SEC_TEXT_QDRANT_COLLECTION`; frozen collection access remains limited to baseline JIT and operator/eval backfills — `backend/ingestion/sec_dense_pipeline/vectorizer.py`, `backend/scripts/embed_sec_filings_html.py`

✅ Qdrant and embedding clients remain function-local — `backend/ingestion/sec_dense_pipeline/retriever.py`, `backend/ingestion/sec_dense_pipeline/vectorizer.py`

✅ Malformed Qdrant payloads surface as `CorpusUnavailableError`, while successful well-formed conversion returns the unchanged `Chunk` fields — `backend/ingestion/sec_dense_pipeline/retriever.py`

✅ Whole-filing zero-item failures propagate as typed `EmptyFilingError`; individual source-level missing Items remain re-scoped to DEV-171 — `backend/ingestion/sec_dense_pipeline/retriever.py`

✅ Braintrust tracing remains deliberately deferred to DEV-161 — `backend/ingestion/sec_dense_pipeline/retriever.py`

✅ The SEC agent tool import/filter/citation switch remains deliberately deferred to DEV-142 — `backend/agent_engine/tools/`

---

## Discussion Gate Outcome (Round 4)

Orchestrator verified all 4 quality-axis findings directly against the current code
(read `search()`'s pre-`_validate_filters` gate and `_validate_filters` itself for M-4.1;
read `chunking.py`'s `ChunkPayload` TypedDict — `ingested_at: NotRequired[str]` at build
time, but the vectorizer stamps it on every payload before upsert per M-4.2's premise;
read `vectorizer.py`'s stale module docstring for m-4.1; read the actual barrier test for
m-4.2). Spec axis: zero findings, third consecutive clean round.

**No disputed findings — all 4 approved to fix as reported.** All are grounded in
design-envelope §4's explicit boundary-validation requirement, not over-reach.

**Round-limit note:** this loop caps at 5 rounds (rule 6 of the skill). This is round 4;
dispatching the fixer for the items above advances to round 5 — the last one. If round 5's
reviewers report zero new findings, the loop proceeds to Step 4 (Final Verification). If
round 5 still finds any Blocking/Major/Minor issue, the loop rule requires stopping and
handing off to the user for manual review rather than attempting a 6th cycle — flagged to
the user before dispatching this round's fixer.

---
