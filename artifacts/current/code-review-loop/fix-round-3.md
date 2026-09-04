# Fix Round 3

### Fixed

| Issue ID | How Fixed | Files Changed |
|----------|-----------|---------------|
| m-3.1 | Reworded module docstring to "except the tests that exercise defensive paths not actually observed in that data, each of which says so in its own docstring" — now accurately reflects two synthetic tests without naming them (brittle to name in the module docstring). | `backend/tests/evals/test_html_arm_compat.py` |
| B-3.1 | Removed `ingested_at`/`score` keys entirely from the 5 real-fixture tests (INTC/134, NVDA/25, AMD/152, NVDA/308, NVDA/128), per the discussion-gate resolution: neither field is read by the code under test, and `score` has no well-defined "correct value" in a query-less unit test (it's a property of the (query, chunk) pair, not the chunk alone — traced to `retriever.py` L342's `point.score`). Assertions build the expected dict via `{**chunk, ...}` spread, so no assertion logic changed. The two synthetic tests (Item 99, Item 9A(T)) and `test_normalize_chunks_maps_normalize_chunk_over_a_list` (which already lacked these fields) were left untouched. | `backend/tests/evals/test_html_arm_compat.py` |

### Not Fixed (with reason)

None.

### Tests Run

| Test Command | Result | Notes |
|--------------|--------|-------|
| `uv run pytest backend/tests/evals/test_html_arm_compat.py -v` | 8 passed | |
| `uv run pytest backend/tests/evals/ -v` | 255 passed, 1 warning | Pre-existing unrelated LangChain deprecation warning |
| `uv run ruff format` / `ruff check` | Clean | |
