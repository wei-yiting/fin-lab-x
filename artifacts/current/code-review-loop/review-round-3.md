# Code Review Round 3

> Reviewer: gpt-5.6-luna | Date: 2026-08-26

## Summary

| Metric | Count |
|--------|-------|
| Total issues | 2 |
| Blocking | 1 |
| Major | 0 |
| Minor | 1 |
| Suggestion | 0 |
| Library checks | 0 |

## Previous Round Status

| # | Issue ID | Status | Notes |
|---|----------|--------|-------|
| 1 | M-1.1 / SP-1.1 | Fixed | 先前三個 fabricated `text` fixtures 現在都是 CSV 的 byte-exact prefixes。 |
| 2 | m-1.1 | Dismissed (user decision) | not re-raised |
| 3 | B-2.1 / SP-2.1 | Fixed | `chunk_index=25`、`152` 的 truncation 與 `/ Overview` tail 已修正。 |
| 4 | M-2.1 | Fixed | `(T)` suffix lookup 與 synthetic regression test 已加入。 |

## Issues

### [Blocking] B-3.1: Real fixture metadata still does not match the recorded CSV

- **File:** `backend/tests/evals/test_html_arm_compat.py` L19
- **Problem:** 完整 re-audit 發現多個宣稱為 recorded chunks 的 scalar fields 仍非 CSV 原值：
  - `INTC/2025`, `chunk_index=134`: `ingested_at` 應為 `2026-08-19T11:27:28.460399+00:00`，目前為 `...39.553783+00:00`；`score` 應為 `0.6546018`，目前為 `0.5`。
  - `NVDA/2026`, `chunk_index=25`: `ingested_at` 使用了 AMD 的 timestamp；`score=0.6` 不等於 CSV 中任一筆 `0.64136106` 或 `0.5651047`。
  - `AMD/2025`, `chunk_index=152`: `score=0.55`，CSV 為 `0.6476879` 或 `0.5581541`。
  - `NVDA/2026`, `chunk_index=308`: `score=0.49`，CSV 為 `0.6156119` 或 `0.4874158`。
  - `NVDA/2026`, `chunk_index=128`: `score=0.42`，CSV 為 `0.61342305`。
  - `test_normalize_chunks_maps_normalize_chunk_over_a_list` 中兩個 real fixtures 另外缺少 `filing_date`、`filing_type`、`accession_number`、`ingested_at`、`score`。
- **Fix:** 從 CSV 中選取明確的 source occurrence，補齊每個 real fixture 的所有指定 fields，並逐欄 byte-compare。

### [Minor] m-3.1: Module docstring still claims only one synthetic test

- **File:** `backend/tests/evals/test_html_arm_compat.py` L1
- **Problem:** Module docstring 寫的是「except the one test」，但目前有兩個 synthetic tests：`Item 99` 與 `Item 9A(T)`。
- **Fix:** 改為明確寫出 two synthetic tests，或移除數量性描述。

## Documentation Gaps

| Folder | Missing |
|--------|---------|
| — | None identified |

## Official Standards Check

N/A — no external libraries in this change.

---

# Spec Conformance Round 3

> Reviewer: gpt-5.6-luna | Date: 2026-08-26

## Summary

| Metric | Count |
|--------|-------|
| Total findings | 0 |
| Missing | 0 |
| Scope creep | 0 |
| Misimplemented | 0 |

## Previous Findings Status

| # | Finding ID | Status | Notes |
|---|-----------|--------|-------|
| 1 | SP-1.1 | ✅ | Round 1 修正維持有效。 |
| 2 | SP-2.1 | ✅ | NVDA `chunk_index=25`、AMD `chunk_index=152` 的 text 與 header_path 均為 CSV 的 offset-0 verbatim prefix，逐字元 hash 相符。 |

## Findings

None.

## Covered Requirements

✅ User Story #3, #4, #9, #10 all confirmed implemented (see full detail in agent output).
✅ `Item 9A(T)` fix judged in-spec, not scope creep — natural extension of User Story #3's canonical-reconstruction principle, and correctly distinguishes "detected but format-variant" from User Story #4's genuine detection-failure case.

---

## Orchestrator Verification (2026-08-26)

Verified B-3.1 directly against the CSV via `csv.DictReader` + `ast.literal_eval`, extracting
every occurrence of each disputed `chunk_index` across all 10 query rows:

| chunk_index | ticker/year | occurrences | ingested_at (all occurrences) | score (all occurrences) |
|---|---|---|---|---|
| 134 | INTC/2025 | 1 | `...28.460399+00:00` (fixed, invariant) | `0.6546018` (single value) |
| 25 | NVDA/2026 | 2 | `...20.472400+00:00` (fixed, invariant) | `0.64136106` / `0.5651047` (query-dependent) |
| 152 | AMD/2025 | 2 | `...39.553783+00:00` (fixed, invariant) | `0.6476879` / `0.5581541` (query-dependent) |
| 308 | NVDA/2026 | 2 | `...20.472400+00:00` (fixed, invariant) | `0.6156119` / `0.4874158` (query-dependent) |
| 128 | NVDA/2026 | 1 | `...20.472400+00:00` (fixed, invariant) | `0.61342305` (single value) |

Two distinct sub-issues, confirmed real:

1. **`ingested_at` is genuinely invariant per chunk** (indexing-time metadata, independent of
   which query retrieved it) — and two fixtures have the **wrong value cross-contaminated from
   a different chunk**: `INTC/134` and `NVDA/25` both currently use
   `"2026-08-19T11:27:39.553783+00:00"`, which is actually `AMD/152`'s timestamp. This is a real
   authoring mistake, not a defensible simplification.
2. **`score` is genuinely query-dependent** (the same chunk can be a top-k result for multiple
   different questions, each with its own relevance score) — there is no single "correct" score
   per chunk. However, every current fixture's `score` value matches **none** of the real
   observed values for its chunk (they're round numbers: 0.5, 0.6, 0.55, 0.49, 0.42), so they
   are fabricated rather than "one of the real occurrences."

Neither field is read by `normalize_chunk`/`normalize_chunks` — both pass through completely
untouched and are never asserted against specific content by any test beyond echoing back
whatever the fixture provides. So unlike the Round 1/2 findings (fabricated words, altered
header_path structure), this issue cannot mask a real behavioral bug in the code under test —
its only cost is that the fixtures aren't fully faithful reproductions of one real recorded row,
which is what the module's docstring and spec User Story #9 literally promise.

## Discussion Gate Resolution (orchestrator + user, 2026-08-26)

**m-3.1** — Undisputed. Fix directly (docstring now discloses two synthetic tests, not one).

**B-3.1** — Undisputed that the underlying facts are real, but resolved differently than a
literal "match the CSV" fix. User asked what `score` actually represents; orchestrator traced
it to `backend/ingestion/sec_dense_pipeline_html/retriever.py` L342 (`point.score`, the Qdrant
query-embedding-to-chunk cosine similarity) — it is a property of the **(query, chunk) pair**,
not the chunk alone. Since `normalize_chunk`'s unit tests exercise a single chunk with no query
context at all, `score` has no well-defined "correct value" in this context (unlike
`ingested_at`, which genuinely is chunk-invariant and was a real authoring mistake —
cross-contaminated from a different chunk's timestamp).

**Resolution: drop both `ingested_at` and `score` from every "real" fixture in this test file**,
rather than correcting them to match the CSV. Neither field is read by the code under test;
`test_normalize_chunks_maps_normalize_chunk_over_a_list` already omits several fields
(`filing_date`, `filing_type`, `accession_number`) without complaint, establishing "fixtures
carry only the fields the test cares about" as this file's existing convention. Removing a
field the test doesn't need is more honest than keeping a fabricated/contaminated value that
looks authoritative but isn't.
