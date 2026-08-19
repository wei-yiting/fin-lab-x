# Code Review Round 2

> Reviewer: gpt-5.6-sol | Date: 2026-08-19

## Summary

| Metric | Count |
|--------|-------|
| Total issues | 9 |
| Blocking | 0 |
| Major | 4 |
| Minor | 3 |
| Suggestion | 2 |
| Library checks | 1 |

## Previous Round Status

| # | Issue ID | Verified Status | Notes |
|---|----------|-----------------|-------|
| 1 | B-1.1 / SP-1.1 | Resolved | `search()` 確實拒絕 `filters=None`、`filters={}` 與只有 `fiscal_year` 的 filters。成功路徑的 `_build_query_filter()` 固定產生 `ticker`、`fiscal_year` 兩個 `must` conditions。較廣泛的 filter 型別與 shape 問題另列為 M-2.3。 |
| 2 | M-1.1 | Dismissed (user decision); operator consequence resolved | 未重提 runtime consumer。新的 `embed_sec_filings_html.py` 使用 frozen `SECFilingPipeline` 與 `_html` vectorizer，逐 ticker 隔離失敗並回傳非零 exit code；retargeted integration test 會確認成功 ticker 的 complete markers 及失敗 summary。 |
| 3 | M-1.2 / SP-1.3 | Resolved | 省略 fiscal year 時，flag 會在 EDGAR resolution 前阻擋；明確 fiscal year 的 complete-marker hit 可通過，marker miss 才由 `_ensure_ingested()` 拋出 `JITDisabledError`。兩半皆有對應 tests。 |
| 4 | M-1.3 (+ Qdrant-5xx half of SP-1.5) | Partially resolved | Raw `httpx.*` catch 已移除、validation-shaped `ResponseHandlingException` 不會 retry、`UnexpectedResponse` 5xx/4xx 分類正確；但 `_TRANSIENT_SOURCE_TYPES` 只涵蓋部分 connection/timeout failures，詳見 M-2.1。 |
| 5 | M-1.4 / SP-1.4 | Resolved | `resolve_latest_fiscal_year_with_retry()` 存在且同時被 `retriever.search()` 與 `embed_sec_filings._embed_one()` 使用；transient/permanent tests 皆存在。 |
| 6 | M-1.5 | Resolved | 第二次 marker check 位於成功 claim slot 之後、`parse_filing_with_retry()` 之前；`finally` 仍保證 release slot。 |
| 7 | M-1.6 | Dismissed (user decision); documentation corrected | 未重提 trace-root 決策。scripts README 已改為 follow-up tracing 說明，frozen retriever 的 operator message 也已指向 `embed_sec_filings_html.py`。 |
| 8 | m-1.1 | Resolved | `sec_dense_pipeline_html/README.md` 已移除 `DEV-160`。其他新加入的 durable issue IDs 另列為 m-2.2。 |
| 9 | S-1.1 | Resolved | `_build_query_filter()` 現在只回傳 `models.Filter`，沒有 unused metadata。 |
| 10 | SP-1.2 | Dismissed (user decision) | DEV-171 的 re-scope 前提未因目前 code 改變；未重提。 |
| 11 | SP-1.5 (embedding half) | Dismissed (user decision) | OpenAI SDK internal retry 的既定決策仍反映於 `ingest_filing_with_retry()`；未重提。 |
| 12 | SP-1.6 | Resolved | Resolution 完成後立即寫入 `resolved_holder`，後續 parse/ingest 失敗時 summary 會使用該年度；對應 test 通過。 |

## Issues

### [Major] M-2.1: Qdrant transient classification still omits valid transport failures
- **File:** `backend/ingestion/sec_dense_pipeline/vectorizer.py` L227
- **Problem:** `_TRANSIENT_SOURCE_TYPES` 只有 `ConnectError`、`ConnectTimeout`、`ReadTimeout`。在 pinned httpx 0.28.1 中，`WriteTimeout`、`PoolTimeout`、`ReadError`、`WriteError` 與 `CloseError` 是同層的 timeout/network failures，但目前都會直接傳播而沒有 design-envelope §2 要求的 single retry。現有 test 只使用 `ConnectError`，因此無法揭露此缺口。
- **Fix:** 使用穩定的 base classes（至少 `httpx.TimeoutException` 與 `httpx.NetworkError`），並明確決定 remote-protocol failure 的政策；新增 representative `WriteTimeout`／`ReadError` tests，保留 validation error 不 retry 的 test。
- **Context7:** qdrant-client 1.17.1 的 sync/async `send_inner()` 會包裝底層所有 httpx exceptions 為 `ResponseHandlingException(source=...)`。目前有正確檢查 `source`，但分類集合不完整。

### [Major] M-2.2: Round-1 review vocabulary leaked into durable tests and docstrings
- **File:** `backend/tests/ingestion/sec_dense_pipeline/unit/test_retriever.py` L297
- **Problem:** Test docstring 直接寫入 `M-1.2/SP-1.3`；`backend/tests/scripts/test_embed_sec_filings.py` L141 也寫入 `SP-1.6`。此外，`retriever.py` L128 與 tests L334、L441 使用沒有獨立上下文的「the AC」「same AC」「AC verification channel」。這些是 review/process identifiers，不是長期有效的 behavior vocabulary，依本輪明確標準屬 Major code cruft。
- **Fix:** 以永久有效的行為描述取代所有 finding IDs 與模糊的 AC references，例如「hot cache hits remain available while JIT is disabled」及「resolved year survives later ingestion failure」。

### [Major] M-2.3: Required search filters remain optional, untyped, and silently permissive
- **File:** `backend/ingestion/sec_dense_pipeline/retriever.py` L215
- **Problem:** `filters: dict | None = None` 仍向 type checker 宣告 filters 可省略，且沒有 key/value types。Runtime 只檢查 `ticker` 是否存在：未知 keys 被靜默忽略，例如舊 contract 的 `{"ticker": "AAPL", "year": 2024}` 會忽略 `year` 並改查 latest filing；string/bool fiscal years 也可能形成錯誤 Qdrant predicates。非字串 ticker 產生的 `TypeError` 還會被 generic handler 包成 `CorpusUnavailableError`，將 caller input error 誤報為 vector-store failure。這違反 AGENTS.md 的 strict typing 要求及 design-envelope §4 的 boundary-validation contract。
- **Fix:** 讓 filters 成為 required parameter，以 `TypedDict` 表達 required `ticker` 與 optional `fiscal_year`，並在建立 client 前做簡單 runtime shape/type validation；拒絕 unknown keys、非字串 ticker 及非整數 fiscal year。補上 legacy `year` key、錯誤型別與 unknown-key tests。

### [Major] M-2.4: Marker lookup failures are silently converted into cache misses
- **File:** `backend/ingestion/sec_dense_pipeline/common.py` L79
- **Problem:** `async_check_commit_marker_complete()` 捕捉所有 exceptions 並回傳 `False`。因此 Qdrant transport、HTTP 或 response-validation failure 都會被當作「資料未 ingest」，觸發第二次 lookup，之後甚至執行 EDGAR parse、embedding 及 wipe/re-ingest。永久 response-shape failure 可能因此被完全隱藏；暫時 Qdrant failure 也會造成不必要的外部成本。這違反 design-envelope §2 的 legible failure semantics 與 §4 的 JIT failure legibility。
- **Fix:** 只有成功 retrieve 但沒有 complete marker 才回傳 `False`；讓 Qdrant exceptions 傳播至 `search()` 的 typed errorмapping。新增 marker lookup exception test，確認不會呼叫 parse 或 ingest。

### [Minor] m-2.1: Two autouse fixtures perform the same registry cleanup
- **File:** `backend/tests/ingestion/sec_dense_pipeline/unit/test_retriever.py` L134
- **Problem:** `_clear_registry_for_ensure_ingested_tests` 與 L240 的 `_clear_registry` 都是 module-wide `autouse=True` fixtures，而且都在每個 test 前後清空 `_inflight_ingests`。這是 Fowler 的 Duplicated Code smell，也讓第一個 fixture 名稱所暗示的 scope 與實際行為不一致。
- **Fix:** 保留單一 module-level autouse fixture，刪除另一個。

### [Minor] m-2.2: Durable code and documentation contain unnecessary DEV issue IDs
- **File:** `backend/ingestion/sec_dense_pipeline/retriever.py` L224
- **Problem:** `DEV-113` 出現在 production docstring 及 L247 的 user-facing `ValueError`；`embed_sec_filings_html.py` L20–21 與 `backend/scripts/README.md` L61 另含 `DEV-138`／`DEV-162`。各處的描述性文字已足以表達 harmful unfiltered search、A/B eval 與 dataset backfill 用途，issue IDs 對後續讀者與 CLI caller 沒有額外資訊。
- **Fix:** 移除 DEV IDs，保留自足的行為與 operator-use rationale。

### [Minor] m-2.3: New production helpers do not meet the repository's explicit typing standard
- **File:** `backend/ingestion/sec_dense_pipeline/retriever.py` L142
- **Problem:** `_point_to_chunk(point)` 沒有 argument type；`common.py` L50 使用 bare `list`；兩個 batch scripts 使用 bare `list[dict]`。AGENTS.md 要求所有 function arguments/returns 明確標註且 collection types 必須具體，這些新 code 未達標。
- **Fix:** 使用 qdrant-client 的 concrete point/record types，並為 batch summary row 定義小型 `TypedDict`；避免 bare `list`／`dict`。

### [Suggestion] S-2.1: Mutable one-key out-parameter obscures batch progress
- **File:** `backend/scripts/embed_sec_filings.py` L34
- **Suggestion:** `resolved_holder: dict[str, int]` 是帶 magic key 的 mutable out-parameter，只為了在 exception 後取回部分進度。把 year resolution 留在每個 ticker 的 linear `try` flow，然後將已解析的 concrete year 傳給 parse/ingest helper，可在不使用 side channel 的情況下保留相同行為。

### [Suggestion] S-2.2: Post-bootstrap collection existence check is effectively dead
- **File:** `backend/ingestion/sec_dense_pipeline/retriever.py` L296
- **Suggestion:** `async_ensure_collection_and_indexes()` 已在 L275 建立缺少的 collection 或拋出錯誤，因此隨後的 `collection_exists()` false branch 只在 concurrent deletion 等 envelope 外情境才可達。它讓每次 search 多一次 Qdrant call，而對應 test 只能藉由 mock 掉 ensure 才抵達。移除 branch 與該 artificial test。

## Documentation Gaps

| Folder | Missing |
|--------|---------|
| `backend/ingestion/sec_dense_pipeline/` | 現有 README 仍只將此 folder 描述為 ingest stage；Structure Map 未列出新的 `retriever.py`，也未記錄 required `ticker`/resolved-year search contract、hot/cold JIT flow、in-process concurrency resolution、error mapping 與新增 retry boundaries。 |

## Official Standards Check

| Library | Version | API Used | Status | Notes |
|---------|---------|----------|--------|-------|
| qdrant-client | 1.17.1 | exception classification in `ingest_filing_with_retry` | ⚠️ | `ResponseHandlingException.source` inspection、validation-error passthrough 及 `UnexpectedResponse` 5xx/4xx gating 均正確；但 transient source tuple 未涵蓋 httpx 0.28.1 的完整 timeout/network hierarchy，詳見 M-2.1。 |

---

# Spec Conformance Round 2

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

| # | Finding | Verified status | Notes |
|---|---------|-----------------|-------|
| 1 | SP-1.1 (bare search allowed) | ✅ Fixed — user-modified direction | `search()` rejects `filters=None`, `{}`, and fiscal-year-only filters with `ValueError` before constructing a Qdrant client. Every successful path builds mandatory `ticker` and resolved `fiscal_year` conditions. |
| 2 | SP-1.2 (GE-style source-level missing Item) | Dismissed (user decision) — re-scoped to DEV-171 | Not re-raised. Direct Linear verification was unavailable: `gh` could not connect and does not expose Linear issues. The authoritative Round 1 discussion gate records the DEV-160 AC as struck through and moved to DEV-171. |
| 3 | SP-1.3 (`SEC_DISABLE_JIT` blocks hot hits) | ✅ Fixed | Explicit-year complete-marker hits bypass the JIT guard. Explicit-year marker misses and omitted-year requests remain blocked before EDGAR access. |
| 4 | SP-1.4 (latest-year resolution bypasses `retry_transient`) | ✅ Fixed | `resolve_latest_fiscal_year_with_retry` uses `retry_transient` and is called by both `search()` and the structured-contract batch script. |
| 5 | SP-1.5 (embedding/Qdrant retry classification) | ✅ Fixed within the ratified scope / embedding half dismissed | Qdrant connection/timeout wrappers and 5xx `UnexpectedResponse` failures are classified for retry; 4xx and validation failures are not. No new embedding-path wrapper was added. |
| 6 | SP-1.6 (batch summary loses resolved year after failure) | ✅ Fixed | The resolved year is captured immediately after resolution and retained in failed summary rows when parsing or ingestion subsequently fails. |

## Findings

No new findings.

## Covered Requirements

✅ Cold queries perform parse → ingest → retrieve within one `search()` call — `backend/ingestion/sec_dense_pipeline/retriever.py`

✅ Complete commit markers produce hot hits without parsing or ingestion — `backend/ingestion/sec_dense_pipeline/retriever.py`

✅ `SEC_DISABLE_JIT=1` permits explicit-year hot hits while blocking explicit-year misses and omitted-year EDGAR resolution — `backend/ingestion/sec_dense_pipeline/retriever.py`

✅ Every successful search reaches Qdrant with mandatory `ticker` and resolved `fiscal_year` `must` conditions — `backend/ingestion/sec_dense_pipeline/retriever.py`

✅ Missing, empty, and fiscal-year-only filters are rejected at the `search()` boundary — `backend/ingestion/sec_dense_pipeline/retriever.py`

✅ Omitted fiscal years are resolved through the shared single-retry policy — `backend/ingestion/sec_dense_pipeline/vectorizer.py`

✅ Both JIT retrieval and batch ingestion use the retry-wrapped latest-year resolver — `backend/ingestion/sec_dense_pipeline/retriever.py`, `backend/scripts/embed_sec_filings.py`

✅ Qdrant connection/timeouts and HTTP 5xx failures receive one repo-owned retry; permanent response failures do not — `backend/ingestion/sec_dense_pipeline/vectorizer.py`

✅ Embedding continues to rely on the OpenAI SDK retry without an additional `retry_transient` layer — `backend/ingestion/sec_dense_pipeline/vectorizer.py`

✅ Same-key concurrent JIT uses immediate rejection and rechecks the commit marker after claiming the slot — `backend/ingestion/sec_dense_pipeline/retriever.py`

✅ In-flight slots are released after success or failure — `backend/ingestion/sec_dense_pipeline/retriever.py`

✅ `cache_hit` remains independently observable — `backend/ingestion/sec_dense_pipeline/retriever.py`

✅ The structured-contract batch script uses `ParsedFiling`, the new vectorizer, and `--fiscal-year` — `backend/scripts/embed_sec_filings.py`

✅ Batch summaries preserve the resolved year after later parse or ingest failure — `backend/scripts/embed_sec_filings.py`

✅ The frozen baseline backfill script faithfully restores `SECFilingPipeline`, old `ingest_filing`, failure isolation, and the original `--year` flag — `backend/scripts/embed_sec_filings_html.py`

✅ Eval and operator documentation route frozen-collection backfills through the restored HTML script — `backend/evals/scenarios/sec_retrieval/README.md`, `backend/scripts/README.md`

✅ The structured-contract pipeline uses `SEC_TEXT_QDRANT_COLLECTION` — `backend/ingestion/sec_dense_pipeline/vectorizer.py`

✅ Qdrant and embedding clients remain function-local — `backend/ingestion/sec_dense_pipeline/retriever.py`, `backend/ingestion/sec_dense_pipeline/vectorizer.py`

✅ Braintrust tracing remains deferred to DEV-161 — `backend/ingestion/sec_dense_pipeline/retriever.py`

✅ The SEC agent tool import/filter switch remains deferred to DEV-142 — `backend/agent_engine/tools/`

---

## Discussion Gate Outcome (Round 2)

Orchestrator verified all 9 quality-axis findings against the current code before this gate (M-2.1 through S-2.2 — read the actual `_TRANSIENT_SOURCE_TYPES` tuple, grepped for leaked finding IDs, traced the `filters` unknown-key and non-string-ticker paths, confirmed the marker-check swallow-all, confirmed the dead `collection_exists()` branch). Spec axis had zero findings.

**No disputed findings — all 9 approved to fix as reported**, plus one carried-over item the orchestrator owns responsibility for:

- The `backend/ingestion/sec_dense_pipeline/` README Documentation Gap (missing `retriever.py` in the Structure Map, missing description of the required-`ticker`/JIT/concurrency/retry contract) was already flagged in Round 1's Documentation Gaps table but was not included in Round 1's fixer task list — an orchestrator oversight, not a user dismissal. Folded into this round's fix list.

User confirmed M-2.3's full scope (TypedDict + reject-unknown-keys) rather than a lighter type-only-validation version, after the orchestrator flagged it as the one item with meaningfully larger scope than the rest.

---

