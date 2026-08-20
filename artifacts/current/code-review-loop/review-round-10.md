# Code Review Round 10 (confirmation pass)

> Reviewer: gpt-5.6-sol | Date: 2026-08-20

## Summary

| Metric | Count |
|--------|-------|
| Total issues | 1 |
| Blocking | 0 |
| Major | 0 |
| Minor | 1 |
| Suggestion | 0 |

8 項修正的 production behavior 均正確落地。唯一 finding 是 F-9.3 留下的一行 test-only dependency pinning，不影響 runtime correctness。

## Fix Verification

| # | Fix | Verified Status | Notes |
|---|---|---|---|
| 1 | F-9.1 | ✅ | Shared conftest 已加入 autouse `SEC_DISABLE_JIT` clearing fixture，fixture scope 涵蓋 unit／integration。以外部 `SEC_DISABLE_JIT=1` 執行 50 個相關 unit tests 全數通過；3 個 deliberate `setenv` cases 亦通過。 |
| 2 | F-9.2 | ✅ | `EmbeddingServiceError` 位於 `common.py`，繼承 `FinLabError`；ingest 的 generic embedding failure end-to-end 保持為 `EmbeddingServiceError`。手動執行 real retry chain smoke check 通過；`except FinLabError: raise` 亦確認保留既有 `TransientError`。所有 import order 正常，無 circular import。 |
| 3 | F-9.3 | ⚠️ | Production classification 正確：source inspection／taxonomy 已完全刪除；blanket `ResponseHandlingException`、5xx retry、4xx／其他原樣傳播；tests 縮為 3 個。但其中一個 test 仍 pin `httpx.ConnectError`，見 m-10.1。 |
| 4 | F-9.9 | ✅ | `_point_to_chunk` 為 None guard 加 `Chunk(**payload, score=point.score)`；call site 僅捕捉 `ValueError`。已確認 Pydantic 2.12.5 的 `ValidationError` 繼承 `ValueError`，missing-field end-to-end tests 通過。 |
| 5 | F-9.4 | ✅ | Stdlib-pinning test 已刪除；missing-key coverage 僅保留 search-level parametrized test；log assertions 改為關鍵欄位；`search_env` 實際由 search tests 共用。Test／production inserted-line ratio 降至 1.54×，符合 envelope §5。 |
| 6 | F-9.5 | ✅ | 三份 docs 與 pipeline README 的 batch CLI target、structured-pipeline JIT wording 均正確。DEV-142 前仍成立的敘述未被提前改寫。 |
| 7 | F-9.10 | ✅ | `resolve_latest_fiscal_year` 已新增於 `sec_core.py`，diff 顯示沒有修改任何既有 public signature；`parse_filing_with_retry` 位於 parser；vectorizer 不再持有兩者。Repository-wide old-name scan 為空；所有 patch targets 可解析。 |
| 8 | F-9.7 | ✅ | Sync marker API 與 shared predicate 已移除；async function 自包含；package exports 一致。Integration assertions 已改用 raw client `retrieve()`。 |

## Issues

### m-10.1 — Retry test 仍 pin `httpx.ConnectError` — Minor
- `test_vectorizer.py` 仍 import `httpx` 並以 `ResponseHandlingException(httpx.ConnectError(...))` 建 source。Production 已不再檢查 wrapped source，此 coupling 違反 F-9.3 的移除意圖（envelope §5 rule 1 精神）。
- Fix：改用任意 generic exception（如 `RuntimeError`）作 source，移除 `httpx` import。

---

# Spec Conformance Round 10 (confirmation pass)

> Reviewer: gpt-5.6-sol | Date: 2026-08-20

## Summary

| Metric | Count |
|--------|-------|
| Total findings | 0 |
| Missing | 0 |
| Scope creep | 0 |
| Misimplemented | 0 |

fix-round-9 未破壞任何 spec-mandated behavior。

## Findings

沒有 findings。

## Re-verified Requirements

✅ Qdrant-boundary retry AC — `vectorizer.py`；`unit/test_vectorizer.py`

✅ `retry_transient` remains the single retry mechanism；JIT 與 batch callers 仍經過 relocated wrappers，無 bespoke retry loop — `sec_core.py:375`；`parser.py:112`；`retriever.py:264`；`embed_sec_filings.py:54`

✅ `sec_core` freeze：diff 僅新增 import 與 public resolver，沒有變更既有 signature

✅ Latest-year resolution 與 resolved-year reporting 保持完整（含 resolution 後 ingest failure）

✅ Legible failure taxonomy：cold-path embedding failure 為 `EmbeddingServiceError`；`EmptyFilingError`/`FinLabError` passthrough 原樣

✅ `cache_hit` observability：log 仍含 `ticker`、`fiscal_year`、`cache_hit`，逐欄斷言

✅ `SEC_DISABLE_JIT` AC：autouse fixture 僅存在於 tests，production guard 未變，兩半皆有 coverage

✅ 其餘 spot-check：cold/hot path、mandatory filter、concurrent JIT rejection、routing 皆維持

---

## Discussion Gate Outcome (Round 10)

Quality: 1 Minor (m-10.1, test-only, one line). Spec: zero — refactor broke nothing.

**m-10.1 applied directly by the orchestrator** (same class as rounds 6–7's direct
fixes): replaced `httpx.ConnectError` with `RuntimeError("transport failure")` as the
`ResponseHandlingException` source in the blanket-retry test, removed the now-unused
`httpx` import. Verified: 3 tests pass, ruff clean.

With that applied, both axes are at zero. The envelope-review cycle (rounds 9–10) is
closed; combined with the original loop's convergence at round 8, the changeset has now
cleanly converged twice — once under the loop's quality/spec standards, once under the
dedicated envelope/over-engineering lens.
