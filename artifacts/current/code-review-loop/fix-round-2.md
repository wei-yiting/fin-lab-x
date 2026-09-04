# Fix Round 2

### Fixed

| Issue ID | How Fixed | Files Changed |
|----------|-----------|---------------|
| B-2.1 / SP-2.1 | Corrected NVDA/2026 `chunk_index=25` `text` to end at the real sentence boundary (`"...and may impose additional controls in the future."`) in both `test_normalize_chunks_maps_normalize_chunk_over_a_list` and `test_normalize_chunk_drops_part_segment_when_title_already_matches_canonical`. Corrected AMD/2025 `chunk_index=152` `text` to end at the real sentence boundary and added the missing `" / Overview"` tail to both the input `header_path` and the expected normalized `header_path` in `test_normalize_chunk_replaces_curly_apostrophe_title_with_canonical_straight_form`. All values re-verified byte-for-byte against the CSV via `csv.DictReader` + `ast.literal_eval`, not just transcription. | `backend/tests/evals/test_html_arm_compat.py` |
| M-2.1 | Added `.removesuffix("(t)")` to the lowercased item-key lookup in `normalize_chunk` so `"Item 9A(T)"` resolves to the same canonical title as `"Item 9A"` instead of silently falling into the "no canonical title" passthrough branch. Added new synthetic test `test_normalize_chunk_strips_temporary_suffix_before_canonical_title_lookup` (confirmed via CSV grep that no real `(T)`-suffixed item exists in the recorded data, so it's disclosed as synthetic, matching the file's existing convention). | `backend/evals/scenarios/sec_retrieval_ab/html_arm_compat.py`, `backend/tests/evals/test_html_arm_compat.py` |

### Not Fixed (with reason)

None.

### Reverted (fix broke tests)

None.

### Tests Run

| Test Command | Result | Notes |
|--------------|--------|-------|
| `uv run pytest backend/tests/evals/test_html_arm_compat.py -v` | 8/8 passed | |
| `uv run pytest backend/tests/evals/` (full suite) | 255 passed, 1 warning | Warning is a pre-existing unrelated langgraph deprecation notice |
| `uv run ruff format` + `uv run ruff check` on both changed files | Clean | |

### Tests Added or Modified

| Test File | Added/Modified | What It Tests |
|-----------|----------------|----------------|
| `backend/tests/evals/test_html_arm_compat.py` | Modified (3 tests) | Corrected `text`/`header_path` fixture values to match the real CSV rows exactly |
| `backend/tests/evals/test_html_arm_compat.py` | Added | `test_normalize_chunk_strips_temporary_suffix_before_canonical_title_lookup` — synthetic `Item 9A(T)` chunk asserting header_path is correctly rebuilt instead of silently skipped |

Orchestrator independently traced through `normalize_chunk` with the new test's input by hand
before committing and confirmed the fix produces the expected `"ZZZZ / 2009 / Item 9A(T).
Controls and Procedures"` output.
