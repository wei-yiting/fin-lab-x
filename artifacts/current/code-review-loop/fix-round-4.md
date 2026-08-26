# Fix Round 4

### Fixed

| Issue ID | How Fixed | Files Changed |
|----------|-----------|---------------|
| M-4.1 | Added `.strip()` to `segment` before `_ITEM_SEGMENT_RE.match()` in the `item_index` lookup, so whitespace-prefixed Item segments in `header_path` match the same way `parse_item()`'s own stripped match does. Added one new defensive test (`test_normalize_chunk_strips_whitespace_padded_item_segment_before_matching`) — verified via manual trace that it would have failed before the fix (unstripped regex returns `None`, chunk falls through unchanged). | `backend/evals/scenarios/sec_retrieval_ab/html_arm_compat.py`, `backend/tests/evals/test_html_arm_compat.py` |
| m-4.1 | Added `normalized is not chunk` + before/after snapshot equality (`original = dict(chunk)` ... `assert chunk == original`) to all 8 tests calling `normalize_chunk` directly. For the `normalize_chunks` list test, added snapshots of both input chunks plus `is not` checks on both result entries (verified the `_unknown` passthrough path's `dict(chunk)` does produce a fresh object). | `backend/tests/evals/test_html_arm_compat.py` |

### Not Fixed (with reason)

None.

### Tests Run

| Test Command | Result | Notes |
|--------------|--------|-------|
| `uv run pytest backend/tests/evals/test_html_arm_compat.py -v` | 9 passed | |
| `uv run pytest backend/tests/evals/ -v` | 256 passed | Full eval test suite, no regressions |
| `uv run ruff format` / `ruff check` | Clean (1 file reformatted for line length, re-verified green after) | |

### Tests Added or Modified

| Test File | Added/Modified | What It Tests |
|-----------|----------------|----------------|
| `backend/tests/evals/test_html_arm_compat.py` | Added | `test_normalize_chunk_strips_whitespace_padded_item_segment_before_matching` — M-4.1 regression |
| `backend/tests/evals/test_html_arm_compat.py` | Modified (all 8 pre-existing tests) | m-4.1 — non-mutation contract verification |

Orchestrator independently traced the new M-4.1 test by hand and confirmed it would have failed
before the fix (unstripped regex returns `None` for the whitespace-padded segment → chunk
returned unchanged → assertion mismatch).
