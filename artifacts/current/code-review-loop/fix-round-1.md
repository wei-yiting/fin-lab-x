# Fix Round 1

All fixes applied and verified against the CSV directly.

### Fixed

| Issue ID | How Fixed | Files Changed |
|----------|-----------|---------------|
| M-1.1/SP-1.1 | Replaced invented `"text": "unchanged"` placeholders in `test_normalize_chunks_maps_normalize_chunk_over_a_list` with the same verbatim excerpts already used for the same underlying chunks (INTC/2025 chunk_index=134, NVDA/2026 chunk_index=25) elsewhere in the file. Replaced the fabricated "...Taiwan-headquartered suppliers." text in `test_normalize_chunk_replaces_wording_divergent_title_with_canonical_form` (chunk_index=308) with the real first-sentence verbatim excerpt confirmed against the CSV. Replaced the hand-simplified single-row markdown table in `test_normalize_chunk_preserves_nested_block_heading_tail` (chunk_index=128) with a verbatim prefix (heading line + real header-separator table row) confirmed against the CSV. | `backend/tests/evals/test_html_arm_compat.py` |

### Not Fixed (with reason)

| Issue ID | Reason |
|----------|--------|
| (none) | — |

### Reverted (fix broke tests)

| Issue ID | What Broke | Reverted Files | Suggested Alternative |
|----------|------------|----------------|----------------------|
| (none) | — | — | — |

### Tests Run

| Test Command | Result | Notes |
|--------------|--------|-------|
| `pytest backend/tests/evals/test_html_arm_compat.py -v` | 7 passed | No assertions changed; only fixture `text` values changed |
| `pytest backend/tests/evals/ -v` | 254 passed | Full eval test suite, no regressions |
| `ruff format --check backend/tests/evals/test_html_arm_compat.py` | already formatted | No reformat needed |
| `ruff check backend/tests/evals/test_html_arm_compat.py` | all checks passed | |

### Tests Added or Modified

| Test File | Added/Modified | What It Tests |
|-----------|----------------|---------------|
| `backend/tests/evals/test_html_arm_compat.py` | Modified (fixture `text` values only, in 3 tests) | Same behavior as before — `normalize_chunk`/`normalize_chunks` pass-through and header_path normalization; no assertion logic changed |

### m-1.1 (untyped `dict`)

Out of scope for this round — dismissed by user in the Round 1 discussion gate. Not touched.

## Orchestrator follow-up (post-fix, pre-round-2)

While verifying the fixer's work, the fixer flagged and the orchestrator independently confirmed
a secondary issue in two fixtures the fixer reused as "already correct" verbatim excerpts:

- `test_normalize_chunk_drops_part_segment_when_title_already_matches_canonical` (NVDA
  chunk_index=25, and the copy reused in `test_normalize_chunks_maps_normalize_chunk_over_a_list`):
  real CSV text is `"...impacting our products, and may impose additional controls in the
  future."`; the fixture text ends `"...impacting our products."` — a comma was silently
  replaced with a period at the truncation point.
- `test_normalize_chunk_replaces_curly_apostrophe_title_with_canonical_straight_form` (AMD
  chunk_index=152): real CSV text continues `"...revenue growth with net revenue increasing
  34%..."`; the fixture text ends `"...revenue growth."` — same pattern, a fabricated
  sentence-ending period at a mid-sentence truncation point.

User decision: leave as-is, defer to the Round 2 reviewer's own judgment rather than fix
preemptively. Not included in this fix round's scope.
