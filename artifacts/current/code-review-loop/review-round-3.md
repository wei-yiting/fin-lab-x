# Code Review Round 3

> Reviewer: gpt-5.6-sol | Date: 2026-08-19

## Summary

| Metric | Count |
|--------|-------|
| Total issues | 5 |
| Blocking | 0 |
| Major | 3 |
| Minor | 2 |
| Suggestion | 0 |
| Library checks | 1 |

## Previous Round Status

| # | Issue ID | Status | Notes |
|---|----------|--------|-------|
| 1 | M-2.1 | ⚠️ Partially Fixed | `_TRANSIENT_SOURCE_TYPES` 確實涵蓋完整的 `TimeoutException`／`NetworkError` subclasses，但 `RemoteProtocolError` 排除政策並不成立，詳見 M-3.1。先前只驗證 hierarchy，沒有充分驗證 policy。 |
| 2 | M-2.2 | ✅ Fixed | 全部 changed backend files 已重新 grep；沒有 `M-1.x`／`M-2.x`／`SP-1.x`／`SP-2.x` 或 bare "the AC"／"same AC"。 |
| 3 | M-2.3 | ⚠️ Partially Fixed | `SearchFilters`、`NotRequired[int]` 與 runtime validation 均正確，且 invalid shape 在 I/O 前被拒絕；但 public signature 仍是 `SearchFilters \| None = None`，沒有完成已核准的 required-parameter fix，詳見 M-3.2。 |
| 4 | M-2.4 | ✅ Fixed | Structured pipeline 的 sync／async marker helpers 均不再捕捉 exceptions；成功 retrieve 且沒有 complete marker 才回傳 `False`。Frozen `_html` copy 未被修改。 |
| 5 | m-2.1 | ✅ Fixed | `test_retriever.py` 僅剩一個 module-wide autouse registry-cleanup fixture。 |
| 6 | m-2.2 | ❌ Still Open | `DEV-138`／`DEV-162` 已移除，但 `DEV-113` 仍留在 `test_retriever.py` L276。先前 fixer verification 漏查了 test docstring，詳見 m-3.1。 |
| 7 | m-2.3 | ✅ Fixed | `_point_to_chunk`、`_marker_is_complete` 與兩個 batch summary types 都已有 concrete annotations；該 annotation 新揭露的 optional-payload typing/API 問題另列 M-3.3。 |
| 8 | S-2.1 | ✅ Fixed | `resolved_holder` 已移除；`main()` 在 per-ticker flow 中先 resolve fiscal year，再呼叫 `_parse_and_ingest()`。 |
| 9 | S-2.2 | ✅ Fixed | `search()` 已移除 post-bootstrap `collection_exists()` round-trip 與 artificial test。 |
| 10 | Doc gap | ✅ Fixed | `sec_dense_pipeline/README.md` 已補上 Structure Map、search contract、JIT flow、concurrency、error mapping 與 retry boundaries。 |

## Issues

### [Major] M-3.1: `RemoteProtocolError` 被錯誤視為 permanent failure
- **File:** `backend/ingestion/sec_dense_pipeline/vectorizer.py` L235
- **Problem:** Comment 主張 `RemoteProtocolError` 表示 response cycle 已開始、接近 permanent schema mismatch；但 HTTPX 也用它表示 server 在沒有送出 response 時中斷連線。HTTPX 官方維護者討論明確將 asynchronous connection close 視為可由 caller retry 的情境。Qdrant ingest 使用 deterministic IDs、wipe-before-upsert，整體設計本來就允許安全 rerun；完全排除此 exception 會讓 design-envelope §2 要求的 single retry 漏掉常見 transient disconnect。`test_ingest_filing_with_retry_does_not_retry_remote_protocol_error` 只是把錯誤政策鎖死，不能證明其正確性。
- **Fix:** 將 `httpx.RemoteProtocolError` 納入 transient source classification，並將現有 test 改為驗證第一次 protocol disconnect、第二次成功。保留 `LocalProtocolError` 排除，因為它代表 client-side protocol misuse。
- **Context7:** [HTTPX exception hierarchy](https://www.python-httpx.org/exceptions/) 將 `RemoteProtocolError` 定義為 server-side protocol violation；[HTTPX maintainer discussion](https://github.com/encode/httpx/discussions/2056) 記錄了 server disconnect without response 與 idempotent request retry 的情境。Installed `httpx 0.28.1` 也確認它是獨立的 `ProtocolError` branch，而 installed `qdrant-client 1.17.1` 會將它包成 `ResponseHandlingException.source`。

### [Major] M-3.2: Required `filters` contract 仍被 type signature 宣告為 optional
- **File:** `backend/ingestion/sec_dense_pipeline/retriever.py` L279
- **Problem:** Round 2 已核准讓 `filters` 成為 required `SearchFilters` parameter，但目前仍是 `filters: SearchFilters | None = None`。Typed caller 因此可合法省略 filters，直到 runtime 才收到 `ValueError`；這與 docstring、README 的 required contract 相衝突，也沒有修掉 M-2.3 指出的 static API 問題。README L68–70 的「required and, when present」正反映了這個矛盾。Design-envelope §4 要求 typed、stable API contract。
- **Fix:** 將 signature 改成 required `filters: SearchFilters`，移除 default 與 `None` union。若仍要測試 untyped caller 明確傳入 `None` 的 runtime rejection，可保留該 case 並在 test boundary 做適當 type suppression；省略 argument 則應由 Python signature 直接拒絕。同步修正 README 的矛盾措辭。

### [Major] M-3.3: Qdrant payload conversion 既不通過 strict typing，也會洩漏 raw validation error
- **File:** `backend/ingestion/sec_dense_pipeline/retriever.py` L206
- **Problem:** `models.ScoredPoint.payload` 的官方 type 是 optional，但 `_point_to_chunk()` 在沒有 guard 的情況下直接 indexing。以 repository venv 執行 Pyright，L209–222 產生 14 個 `reportOptionalSubscript`／`reportOptionalMemberAccess` errors，違反 AGENTS.md strict-typing requirement。更嚴重的是 payload field type 錯誤會讓 `Chunk` 拋出 `pydantic.ValidationError`；該 exception 是 `ValueError` subclass，因此會被 `search()` L382 的 caller-input passthrough 原樣拋出，而不是轉成 typed `CorpusUnavailableError`。這違反 design-envelope §4 對 external-data boundary validation 與 stable、actionable errors 的要求。
- **Fix:** 在 `_point_to_chunk()` 明確拒絕 `payload is None`，並將 Qdrant payload schema validation failures 映射為帶 context 的 `CorpusUnavailableError`。將 caller-input validation／ticker canonicalization 移到 Qdrant `try` block 前，或縮窄 L382 的 `ValueError` passthrough，避免 downstream Pydantic errors 被誤認成 caller errors。修正後以正確 venv 執行 Pyright，確保此檔零 errors。

### [Minor] m-3.1: `DEV-113` 仍洩漏在 durable test docstring
- **File:** `backend/tests/ingestion/sec_dense_pipeline/unit/test_retriever.py` L276
- **Problem:** `test_search_raises_when_filters_is_none()` 仍包含 `DEV-113`。這直接推翻 fix-round-2 對 m-2.2 的完整修復宣稱；先前 verification 顯然只檢查了列出的 production/docs locations，漏掉同一 changed test file。Issue ID 對後續維護者沒有額外價值。
- **Fix:** 移除 `(DEV-113: ...)`，保留「naive search is a proven-harmful retrieval mode」的自足行為理由。

### [Minor] m-3.2: Concurrent integration test 對合法 scheduling outcome 做出不穩定斷言
- **File:** `backend/tests/ingestion/sec_dense_pipeline/integration/test_search.py` L140
- **Problem:** Test 直接 `asyncio.gather()` 兩個 calls，卻沒有 barrier 保證第二個 caller 在第一個完成 ingest 前抵達 slot claim。若第一個 call 較快完成，第二個 call 合法地在 initial marker check 看見 `complete` 並成為 hot hit；此時兩個 calls 都成功，但 test 固定要求一個 `IngestionInProgressError`。這使 manual integration gate 依 scheduler／Qdrant timing 偶發失敗，也沒有精確驗證其命名所述的「overlapping in-flight」情境。
- **Fix:** 用 event/barrier 暫停第一個 call，使其已 claim slot、但尚未完成 ingest，再啟動第二個 call並斷言 legible error，最後 release 第一個 call。另保留 stale-marker unit test 驗證「第一個已完成時，第二個可成為 hot hit」。

## Documentation Gaps

| Folder | Missing |
|--------|---------|
| None | None |

## Official Standards Check

| Library | Version | API Used | Status | Notes |
|---------|---------|----------|--------|-------|
| httpx | 0.28.1 | `_TRANSIENT_SOURCE_TYPES` classification | ❌ | `TimeoutException` 與 `NetworkError` 正確涵蓋各自全部 subclasses；但整體 transient policy 錯誤排除可代表 server disconnect 的 `RemoteProtocolError`。HTTPX [官方 hierarchy](https://www.python-httpx.org/exceptions/) 與[官方 maintainer discussion](https://github.com/encode/httpx/discussions/2056)不支持目前「接近 permanent schema mismatch」的概括。 |

---

# Spec Conformance Round 3

> Reviewer: gpt-5.6-sol | Date: 2026-08-19
> (Copy `gpt-5.6-sol` and `2026-08-19` verbatim — do not self-identify.)

## Summary

| Metric | Count |
|--------|-------|
| Total findings | 0 |
| Missing | 0 |
| Scope creep | 0 |
| Misimplemented | 0 |

## Previous Spec Findings

All previous spec findings remain resolved under the authoritative Discussion Gate decisions. Round 2's fixes introduce zero new spec concerns.

Direct Linear verification (via a connected Linear tool) confirms that DEV-160 strikes the source-level missing-Item AC and re-scopes it to DEV-171.

## Findings

No new findings.

## Covered Requirements

✅ Cold searches perform parse → ingest → retrieve within one `search()` call — `backend/ingestion/sec_dense_pipeline/retriever.py`

✅ Hot searches use the complete commit marker and skip parse/ingest — `backend/ingestion/sec_dense_pipeline/retriever.py`

✅ `cache_hit` accurately distinguishes hot hits, completed races, and JIT ingestion through the emitted log — `backend/ingestion/sec_dense_pipeline/retriever.py`

✅ Genuine marker misses still resolve to `False` and trigger JIT; actual Qdrant failures propagate instead — `backend/ingestion/sec_dense_pipeline/common.py`

✅ `SEC_DISABLE_JIT=1` blocks cold EDGAR/JIT work while allowing explicit-year hot hits — `backend/ingestion/sec_dense_pipeline/retriever.py`

✅ Valid `{"ticker": ..., "fiscal_year": ...}` calls remain accepted and produce mandatory ticker/year Qdrant filters — `backend/ingestion/sec_dense_pipeline/retriever.py`

✅ Omitted `fiscal_year` remains supported and resolves through the shared latest-year resolver — `backend/ingestion/sec_dense_pipeline/retriever.py`

✅ `SearchFilters` validation proportionately rejects only invalid or non-contract shapes, including the legacy `year` key, unknown keys, and wrong value types — `backend/ingestion/sec_dense_pipeline/retriever.py`

✅ The structured-contract batch script uses the new parser/vectorizer contract and keeps `--fiscal-year` optional — `backend/scripts/embed_sec_filings.py`

✅ A resolved batch fiscal year survives later parse or ingestion failure and appears in the failure summary — `backend/scripts/embed_sec_filings.py`

✅ JIT parsing, latest-year resolution, and retryable Qdrant ingestion use the shared `retry_transient` policy — `backend/ingestion/sec_dense_pipeline/vectorizer.py`

✅ Same-key concurrent JIT uses an in-process atomic claim, immediate legible rejection, post-claim marker recheck, and `finally` cleanup — `backend/ingestion/sec_dense_pipeline/retriever.py`

✅ Retrieval and ingestion consistently use `SEC_TEXT_QDRANT_COLLECTION`; the restored HTML script is limited to frozen-baseline operator backfills — `backend/ingestion/sec_dense_pipeline/vectorizer.py`, `backend/scripts/embed_sec_filings_html.py`

✅ Embedding and Qdrant clients remain function-local — `backend/ingestion/sec_dense_pipeline/retriever.py`, `backend/ingestion/sec_dense_pipeline/vectorizer.py`

✅ Individual source-level missing Items remain correctly re-scoped to DEV-171; DEV-160 retains whole-filing `EmptyFilingError` propagation — `backend/ingestion/sec_dense_pipeline/retriever.py`

✅ Braintrust tracing remains deferred to DEV-161 — `backend/ingestion/sec_dense_pipeline/retriever.py`

✅ The SEC agent tool import/filter/citation switch remains deferred to DEV-142 — `backend/agent_engine/tools/`

---

## Discussion Gate Outcome (Round 3)

Orchestrator verified all 5 quality-axis findings against the current code and, for M-3.1,
against httpx's official exception-hierarchy documentation (`_exceptions.py`'s docstring,
fetched via Context7) before this gate. Spec axis: zero findings again.

**No disputed findings — all 5 approved to fix as reported**, with one correction the
orchestrator owns:

- **M-3.1**: confirmed via httpx's own hierarchy comment that `ProtocolError` (parent of
  `RemoteProtocolError`) sits under `TransportError` as a sibling of `TimeoutException`/
  `NetworkError` — not under `DecodingError` (the "received but malformed" branch). Round
  2's exclusion of `RemoteProtocolError`, while explicitly flagged there as "a judgment
  call, not a settled taxonomy fact," does not hold up against the library's own
  structure. Reclassify as transient.
- **M-3.2**: the orchestrator's own round-2 fixer instructions explicitly told the fixer
  to keep `filters: SearchFilters | None = None` (preserve the legible `ValueError` path
  for a caller passing nothing) rather than tighten the signature — so this was not an
  incomplete fix, it was exactly what was asked for. On reconsideration prompted by this
  finding, the orchestrator now judges the original instruction overly conservative:
  making `filters` a true required parameter still fails legibly (a caller omitting it
  gets Python's own `TypeError`; a caller explicitly passing `None` — matching the
  existing tests' shape — still hits the custom `ValueError`), and better matches
  AGENTS.md's strict-typing mandate. Revised: fix as the reviewer suggests.
- **M-3.3**, **m-3.1**, **m-3.2**: verified directly against the code (unguarded
  `payload` access + `pydantic.ValidationError` leaking through the `except (ValueError,
  FinLabError): raise` passthrough; `DEV-113` still present at `test_retriever.py:276`;
  the concurrency integration test's `asyncio.gather()` has no barrier forcing the
  intended race window). All confirmed as reported.

---

