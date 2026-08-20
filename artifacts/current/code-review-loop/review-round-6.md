# Code Review Round 6

> Reviewer: gpt-5.6-sol | Date: 2026-08-20

## Summary

| Metric | Count |
|--------|-------|
| Total issues | 1 |
| Blocking | 0 |
| Major | 0 |
| Minor | 1 |
| Suggestion | 0 |
| Library checks | 0 |

## Previous Round Status

| # | Issue ID | Verified Status | Notes |
|---|----------|-----------------|-------|
| 1 | M-5.1 | ✅ Fixed | `_point_to_chunk()` 現在以 `payload["block_heading"]` 與 `payload["prelude"]` 存取兩個 required-but-nullable fields。兩者缺 key 的 conversion/search tests 均存在；既有「key 存在、value 為 `None`」test 仍保留並通過。對 `retriever.py`、`vectorizer.py`、`common.py` 的 sibling sweep 未發現另一個會把 malformed content payload 靜默轉成合法 `Chunk` 的同型問題；`_marker_is_complete()` 的 fail-safe `.get("status")` 仍屬不同風險形狀。 |

## Issues

### [Minor] m-6.1: Frozen pipeline Quick Start 宣稱會 JIT ingest，但範例沒有提供 ticker filter
- **File:** `backend/ingestion/sec_dense_pipeline_html/README.md` L11–13
- **Problem:** Quick Start 現在先啟動空的 Qdrant，接著執行 `search(query=..., top_k=10)`，並宣稱該呼叫會在 cache miss 時 JIT ingest。然而 frozen retriever 只有在 `filters` 包含 `ticker` 時才進入 JIT path；此範例沒有 filter，面對 fresh Qdrant 只會在 collection pre-check 拋出錯誤。本 branch 同時移除了 Quick Start 原本的 batch-ingest 步驟，因此這不再只是省略 filter 的 unfiltered-search 範例，而是無法依序成功執行的 Quick Start。
- **Fix:** 將範例改成例如 `search(query="NVIDIA export control risks", filters={"ticker": "NVDA"}, top_k=10)`，使其實際觸發下方文件描述的 JIT flow。
- **Sibling sweep:** Repo-wide 檢查其他 `search()` 範例後，只有既有 eval task 刻意對已預載的 frozen collection 執行 unfiltered retrieval；其他 JIT tests 都傳入 ticker。沒有第二個 changed documentation example 具有相同的「宣稱 JIT、卻省略 ticker」問題。

## Documentation Gaps

| Folder | Missing |
|--------|---------|
| None | None |

## Official Standards Check

| Library | Version | API Used | Status | Notes |
|---------|---------|----------|--------|-------|
| None | — | — | N/A | Round 5 後沒有新增或修改 external library usage；依 prompt 不重做已 settled 的 library checks。 |

---

# Spec Conformance Round 6

> Reviewer: gpt-5.6-sol | Date: 2026-08-20

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

✅ `cache_hit` correctly distinguishes hot hits, completed races, and JIT ingestion through logs — `backend/ingestion/sec_dense_pipeline/retriever.py`

✅ `SEC_DISABLE_JIT=1` blocks cold EDGAR/JIT work while permitting explicit-year hot hits — `backend/ingestion/sec_dense_pipeline/retriever.py`

✅ Every successful search applies mandatory `ticker` and resolved `fiscal_year` Qdrant conditions — `backend/ingestion/sec_dense_pipeline/retriever.py`

✅ Omitted `fiscal_year` resolves through the shared latest-year resolver and is applied to retrieval — `backend/ingestion/sec_dense_pipeline/retriever.py`

✅ The batch script uses the structured parser/vectorizer contract and reports the resolved fiscal year, including after later failure — `backend/scripts/embed_sec_filings.py`

✅ JIT parsing and latest-year resolution use the shared single-retry policy — `backend/ingestion/sec_dense_pipeline/vectorizer.py`

✅ Retryable Qdrant transport and 5xx failures receive at most one repo-owned retry; permanent failures do not — `backend/ingestion/sec_dense_pipeline/vectorizer.py`

✅ Same-key concurrent JIT uses atomic in-process claiming, legible rejection, post-claim marker recheck, and `finally` cleanup — `backend/ingestion/sec_dense_pipeline/retriever.py`

✅ Retrieval and structured ingestion consistently use `SEC_TEXT_QDRANT_COLLECTION` — `backend/ingestion/sec_dense_pipeline/vectorizer.py`

✅ The frozen baseline retains its explicitly approved operator/eval backfill path — `backend/scripts/embed_sec_filings_html.py`

✅ Qdrant and embedding clients remain function-local — `backend/ingestion/sec_dense_pipeline/retriever.py`, `backend/ingestion/sec_dense_pipeline/vectorizer.py`

✅ `build_chunk_payloads()` unconditionally writes both `block_heading` and `prelude` keys for every legitimate chunk, including explicit `None` values — `backend/ingestion/sec_dense_pipeline/chunking.py`

✅ `ingest_filing()` preserves those keys through the normal payload-to-upsert path, so bracket access cannot reject correctly ingested chunks — `backend/ingestion/sec_dense_pipeline/vectorizer.py`

✅ Missing `block_heading` or `prelude` now identifies malformed stored data, while present keys containing `None` remain accepted — `backend/ingestion/sec_dense_pipeline/retriever.py`

✅ Whole-filing zero-item failures propagate as typed errors; individual source-level missing Items remain re-scoped to DEV-171 — `backend/ingestion/sec_dense_pipeline/retriever.py`

✅ Braintrust tracing remains deliberately deferred to DEV-161 — `backend/ingestion/sec_dense_pipeline/retriever.py`

✅ The SEC agent tool import/filter/citation switch remains deliberately deferred to DEV-142 — `backend/agent_engine/tools/`

---

## Discussion Gate Outcome (Round 6)

Orchestrator verified m-6.1 directly against the README and the frozen retriever's
`search()` signature (`if filters and "ticker" in filters:` — confirmed the example's
`search(query=..., top_k=10)` call never reaches the JIT path it claims to demonstrate).
Traced the root cause to the orchestrator's own round-1 fix (M-1.1: rewrote the
surrounding paragraph when adding the `embed_sec_filings_html.py` operator backfill path,
without checking the code example immediately above it still made sense once the
batch-ingest step it originally followed was removed). Spec axis: zero findings, fifth
consecutive clean round.

**No dispute — applied directly** (one-line doc example, no code/test surface, same class
of trivial fix as the orchestrator's earlier direct edits in rounds 1 and 5): added
`filters={"ticker": "NVDA"}` to the Quick Start example.

Proceeding to a 7th review pass to check for convergence to zero.

---
