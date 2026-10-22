# Code Review Round 2

> Reviewer: gpt-5.6-luna | Date: 2026-08-26

## Summary

| Metric | Count |
|--------|-------|
| Total issues | 2 |
| Blocking | 1 |
| Major | 1 |
| Minor | 0 |
| Suggestion | 0 |
| Library checks | 0 |

## Previous Round Status

| # | Issue ID | Status | Notes |
|---|----------|--------|-------|
| 1 | M-1.1 / SP-1.1 | Fixed | The three previously identified fabricated fixtures now use source-derived text. Independent verification confirmed the fixes. Two separate residual provenance violations are reported below. |
| 2 | m-1.1 | Dismissed (user decision) | not re-raised |

## Issues

### [Blocking] B-2.1: Recorded fixtures still contain altered payload content

- **File:** `backend/tests/evals/test_html_arm_compat.py` L83
- **Problem:** The `NVDA/2026` `chunk_index=25` fixture ends with `impacting our products.` while the CSV source continues `impacting our products, and may impose additional controls in the future.` The `AMD/2025` `chunk_index=152` fixture similarly ends at `revenue growth.` although the source continues `with net revenue increasing 34%...`. The AMD fixture also omits the recorded `/ Overview` header-path tail at L110. These are still altered recorded chunks, contrary to the declared real-fixture contract.
- **Fix:** Replace the altered fields with exact source-derived values or exact verbatim prefixes that preserve the source punctuation and wording. Preserve the recorded AMD header-path tail.

### [Major] M-2.1: Parser-supported `Item 9A(T)` is silently skipped

- **File:** `backend/evals/scenarios/sec_retrieval_ab/html_arm_compat.py` L64
- **Problem:** The frozen HTML parser explicitly emits `Item 9A(T)`, but this lookup produces `9a(t)`, which is absent from `TENK_STANDARD_TITLES` (`9a` is the canonical key). The function therefore returns the chunk unchanged at L65–L66, leaving the Part segment and causing a false retrieval miss for this valid parser output.
- **Fix:** Normalize the optional `(T)` suffix to the canonical `9a` key, then rebuild the header using the new pipeline's canonical `Item 9A. Controls and Procedures` label. Add regression coverage for this parser-supported variant.

## Documentation Gaps

| Folder | Missing |
|--------|---------|
| — | None identified |

## Official Standards Check

N/A — no external libraries in this change.

---

# Spec Conformance Round 2

> Reviewer: gpt-5.6-luna | Date: 2026-08-26

## Summary

| Metric | Count |
|--------|-------|
| Total findings | 1 |
| Missing | 0 |
| Scope creep | 0 |
| Misimplemented | 1 |

## Previous Findings Status

| # | Finding ID | Status | Notes |
|---|-----------|--------|-------|
| 1 | SP-1.1 | ⚠️ Partially Fixed | `chunk_index=134`（103 chars）、`308`（169 chars）、`128`（265 chars）均為 CSV 的 verbatim substring；但 `chunk_index=25` 仍在 list fixture 與 standalone fixture 中使用非 verbatim 的句點截斷，未完全修正。`Item 99` 為已明確揭露且可接受的 synthetic fixture。 |

## Findings

### [Blocking] SP-2.1: Retained fixtures alter recorded text at truncation boundaries

- **Type:** Misimplemented
- **Spec:** "As 這張 PR 的 reviewer, I want unit test 的 fixture 是從真實錄下的 frozen HTML pipeline 輸出取出來的，不是憑空編的字串, so that 我能相信測試反映的是 pipeline 的真實行為，不是簡化過的想像。"
- **File:** `backend/tests/evals/test_html_arm_compat.py` L56-57, L83-84, L114
- **Problem:** `NVDA/2026/chunk_index=25` 的 fixture 在第 135 個字元以 `products.` 結束，但 CSV 是 `products, and may impose additional controls...`；`AMD/2025/chunk_index=152` 在第 64 個字元以 `growth.` 結束，但 CSV 是 `growth with net revenue increasing...`。兩者都不是 recorded text 的 verbatim substring，而是改寫標點以製造完整句子。
- **Fix:** 從 CSV 複製真實連續文字；若需截斷，必須在原文已有的邊界截斷，不得新增句點。同步修正 `chunk_index=25` 的兩個 fixture 位置。

## Covered Requirements

✅ 相容層從 chunk 的 item、ticker/year 與 TENK_STANDARD_TITLES 重建 Item-level header_path — `backend/evals/scenarios/sec_retrieval_ab/html_arm_compat.py` L60-L85
✅ 移除 Part、保留 Item 後的多層 block heading tail — `html_arm_compat.py` L68-L85；測試 L160-L195
✅ 未辨識 item 時保持原 chunk 不變 — `html_arm_compat.py` L60-L78；測試 L15-L34、L198-L219
✅ normalize_chunks 提供 list-shaped adapter，且未修改既有 scorer — `html_arm_compat.py` L88-L90
✅ 修正後的 chunk_index=134、308、128 fixture 均為 reference CSV 的 verbatim substring — `test_html_arm_compat.py` L47-L57、L136-L181
⚠️ 我判定 comma/period truncation 是 spec violation：它們不符合「不是憑空編的字串」，已記錄為 SP-2.1 — `test_html_arm_compat.py` L56-L57、L83-L84、L114

---

## Orchestrator Verification (2026-08-26)

Both axes independently confirmed the same root issue (the comma→period truncations in
`chunk_index=25` and `chunk_index=152`) — this is now a converged, independently-verified
finding across both reviewer passes, not just the orchestrator's earlier observation.

The quality reviewer additionally found something neither the spec reviewer nor Round 1 caught:
the `chunk_index=152` fixture's `header_path` (test file L107-112) is missing a `/ Overview`
tail that the real recorded chunk has. Orchestrator independently confirmed against the CSV:

```
real: '...Management's Discussion and Analysis of Financial Condition and Results of
       Operations / Overview', 'chunk_index': 152, ...
test: "AMD / 2025 / Part II / Item 7. Management's Discussion and Analysis of Financial
       Condition and Results of Operations"   (no "/ Overview" tail)
```

Confirmed real — same class of fixture-fidelity problem, in `header_path` instead of `text`.

M-2.1 (`Item 9A(T)` canonical lookup gap) — orchestrator independently confirmed via code
inspection: `backend/ingestion/sec_dense_pipeline_html/vectorizer.py` L27 uses the regex
`r"^(Item \d+[A-Z]?(?:\(T\))?)\.?"`, confirming the frozen pipeline's own item-anchor detection
explicitly recognizes and can emit `(T)`-suffixed items (a historical SEC provision, ~2008-2010,
for the temporary internal-control-attestation exemption). `html_arm_compat.py`'s
`_ITEM_SEGMENT_RE` copies this exact pattern for locating the header_path segment, but the
canonical-title lookup key (`item[len("Item "):].lower()`) does not strip the `(T)` suffix
before querying `TENK_STANDARD_TITLES`, which only has bare `9a`. Confirmed real bug: an
`Item 9A(T)` chunk is silently treated as "no canonical title found" and returned with its Part
segment intact, causing a false scoring miss against the Item-level (no Part) ground truth.

## Discussion Gate Resolution (orchestrator + user, 2026-08-26)

All three findings undisputed — user agreed to fix all:

1. **B-2.1 / SP-2.1** — comma→period truncation fabrications in `chunk_index=25` (both its
   occurrences) and `chunk_index=152` fixtures. Fix: exact verbatim excerpts from the CSV.
2. **AMD `chunk_index=152` header_path missing `/ Overview` tail** (found by quality reviewer,
   verified by orchestrator) — fix alongside B-2.1 since it's the same fixture.
3. **M-2.1** — `Item 9A(T)` canonical-title lookup gap in `html_arm_compat.py`. Real production
   bug, not a test issue. Fix: strip/normalize the `(T)` suffix before the `TENK_STANDARD_TITLES`
   lookup, add regression test coverage for this parser-supported variant.
