# Code Review Round 5

> Reviewer: gpt-5.6-sol | Date: 2026-08-19

## Summary

| Metric | Count |
|--------|-------|
| Total issues | 1 |
| Blocking | 0 |
| Major | 1 |
| Minor | 0 |
| Suggestion | 0 |
| Library checks | 0 |

Round 5 仍有 Major issue；依五輪 hard cap，changeset 應交由 human manual review，不進入第六輪。

## Previous Round Status

| # | Issue ID | Status | Notes |
|---|----------|--------|-------|
| 1 | M-4.1 | ✅ Fixed | `search()` 在任何 membership/index 操作前拒絕 truthy non-dict `filters`。`123`、`["ticker"]` 會得到 `ValueError`；`None`、`{}` 仍走原本且訊息不變的 ticker-required path。 |
| 2 | M-4.2 | ✅ Fixed | `ingested_at` 已改成 `payload["ingested_at"]`；conversion call site 捕捉 `(ValueError, KeyError)` 並映射成 `CorpusUnavailableError`。但 fixer report 所稱「every other required field」皆採 key access 並不成立，詳見 M-5.1。 |
| 3 | m-4.1 | ✅ Fixed | `vectorizer.py` module docstring 與 pipeline README 均已區分 bare `ingest_filing`、Qdrant retry wrapper 及 OpenAI SDK internal retry，不再宣稱整個 module 沒有 retry wrapper。 |
| 4 | m-4.2 | ✅ Fixed | Barrier wait 同時 race `ingest_claimed.wait()` 與 `first_call`，並有 10 秒 timeout；第一個 task 提早結束時會立即取出 result／exception，cleanup 也會 release、cancel 並 await tasks。 |

## Issues

### [Major] M-5.1: Required nullable payload keys are still silently accepted when absent
- **File:** `backend/ingestion/sec_dense_pipeline/retriever.py` L229–230
- **Problem:** `_point_to_chunk()` 仍使用：

  ```python
  block_heading=payload.get("block_heading"),
  prelude=payload.get("prelude"),
  ```

  `ChunkPayload` 將這兩者定義為 required-but-nullable keys，且 vectorizer 每次都會 persist 它們。`.get()` 卻把「key 不存在」與「明確儲存 `None`」混為同一狀態。直接以缺少兩個 keys 的 payload 呼叫 current `_point_to_chunk()`，仍會成功產生 `Chunk(block_heading=None, prelude=None)`，使 malformed Qdrant data 靜默通過並可能遺失 heading／prelude context。這違反 design-envelope §4 對 external-data boundary validation 與禁止 silent partial answers 的要求。

  Round 4 對 M-4.2 的驗證只檢查 `ingested_at`，未核對 fixer report 宣稱的「every other required field's access pattern」；current lines 229–230 證明該較廣泛前提不正確。
- **Fix:** 對兩個 required keys 使用 `payload["block_heading"]` 與 `payload["prelude"]`。現有 `(ValueError, KeyError)` handler 即可將缺欄映射為帶 point ID 的 `CorpusUnavailableError`。新增 parametrized tests，分別移除這兩個 keys 並驗證 conversion/search rejection。

## Documentation Gaps

| Folder | Missing |
|--------|---------|
| None | None |

## Official Standards Check

| Library | Version | API Used | Status | Notes |
|---------|---------|----------|--------|-------|
| None | — | — | N/A | Round 4 後沒有新增或修改 external library usage；依 review scope 不重做已 settled 的 library checks。 |

---

# Spec Conformance Round 5

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

## Covered Requirements

✅ Cold searches perform parse → ingest → retrieve within one `search()` call — `backend/ingestion/sec_dense_pipeline/retriever.py`

✅ Hot searches use complete commit markers and skip parsing and ingestion — `backend/ingestion/sec_dense_pipeline/retriever.py`

✅ Filing-store parsing cache and Qdrant commit markers jointly support the cold/hot path — `backend/ingestion/sec_dense_pipeline/retriever.py`

✅ `cache_hit` correctly distinguishes hot hits, completed races, and JIT ingestion through logs — `backend/ingestion/sec_dense_pipeline/retriever.py`

✅ `SEC_DISABLE_JIT=1` blocks cold EDGAR/JIT work while permitting explicit-year hot hits — `backend/ingestion/sec_dense_pipeline/retriever.py`

✅ `filters` is required, and the new non-dict rejection is purely defensive; valid `{"ticker": ..., "fiscal_year": ...}` calls remain unaffected — `backend/ingestion/sec_dense_pipeline/retriever.py`

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

✅ Every legitimate content payload is stamped with `ingested_at` before point construction and upsert, so requiring it during retrieval cannot reject a correctly ingested chunk — `backend/ingestion/sec_dense_pipeline/vectorizer.py`

✅ Malformed Qdrant payloads, including missing `ingested_at`, surface as `CorpusUnavailableError`; well-formed chunk conversion remains unchanged — `backend/ingestion/sec_dense_pipeline/retriever.py`

✅ Whole-filing zero-item failures propagate as typed `EmptyFilingError`; individual source-level missing Items remain re-scoped to DEV-171 — `backend/ingestion/sec_dense_pipeline/retriever.py`

✅ Braintrust tracing remains deliberately deferred to DEV-161 — `backend/ingestion/sec_dense_pipeline/retriever.py`

✅ The SEC agent tool import/filter/citation switch remains deliberately deferred to DEV-142 — `backend/agent_engine/tools/`

---

## Orchestrator Note — Loop Terminated at Round Cap

Per skill rule 6 ("Max 5 rounds — if issues persist after 5 rounds, stop and hand off to
the user"), this loop stops here. This is round 5, and the quality axis reported one
unresolved Major finding (M-5.1); the loop rule requires stopping regardless of the
finding's severity or how trivial the fix would be — that judgment belongs to the user at
this gate, not to the orchestrator.

The orchestrator independently verified M-5.1 against the current code before reporting it
(read `_point_to_chunk()` L218–235; confirmed `chunking.py`'s `ChunkPayload` TypedDict
declares `block_heading: str | None` and `prelude: str | None` as required-but-nullable —
no `NotRequired` marker, unlike `ingested_at`'s prior `NotRequired[str]` — and that
`build_chunk_payloads()` always writes both keys explicitly, even when the value is
`None`). The finding is accurate: this is the identical category of gap as M-4.2
(`ingested_at`), on two fields that round 4's fix missed despite its own report claiming
the fix matched "every other required field's access pattern." The fix is mechanically
identical to M-4.2's — `.get(key)` → `[key]` — and safe: switching to bracket access does
not disturb the legitimate "key present, value `None`" case at all, only the "key entirely
absent" corruption case the finding is about.
