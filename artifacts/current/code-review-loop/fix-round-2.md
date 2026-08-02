# Fix Round 2

> Fixer: claude (code-fixer subagent) | Date: 2026-08-02

### Fixed

| Issue ID | How Fixed | Files Changed |
|----------|-----------|---------------|
| M-2.1 (Major) | Changed `ScorerConfig.temperature` from `float = 0.0` to `float = Field(default=0.0, ge=0.0, le=2.0, allow_inf_nan=False)`, matching the OpenAI documented 0–2 range; added `Field` to the existing `pydantic` import line. Added exactly one regression test for an out-of-range value (`temperature=2.5` on an `llm_judge` scorer). No negative/nan/inf tests added, per the human owner's ruling. No hand-rolled validator — the documented Pydantic v2 `Field` constraint API is used, verified against Context7 (`/pydantic/pydantic`: `ge`/`le` numeric constraints, `allow_inf_nan` for float fields). | `backend/evals/eval_spec_schema.py`, `backend/tests/evals/test_scorer_registry.py` |
| m-2.1 (Minor) | Reworded the L26 comment to `# Local mode (default — needs OPENAI_API_KEY, but no BRAINTRUST_API_KEY)`. One line, same shape as the neighbouring `# Upload mode (...)` line; code block and prerequisites table untouched. | `backend/evals/README.md` |

### Not Fixed (with reason)

| Issue ID | Reason |
|----------|--------|
| M-1.1 (ADR-0007 word count) | Explicitly declined by the human owner (2026-08-02). Accepted deviation, already confirmed by the Round 2 reviewer as not-to-be-re-raised. |
| M-2.1 negative / nan / inf test matrix | Explicitly declined by the human owner as testing Pydantic's own implementation rather than repo code. The reviewer's fix instruction was accepted at reduced scope: the `Field` constraint (which is what actually enforces all three cases) landed; only the redundant test matrix was dropped. |

### Reverted (fix broke tests)

None.

### Tests Run

| Test Command | Result | Notes |
|--------------|--------|-------|
| `uv run pytest backend/tests/evals/ -q` | ✅ 134 passed | Includes the new test plus the two Round 1 `model_fields_set` tests. |
| `uv run pytest backend/tests/ -q` | ✅ 854 passed, 49 deselected | Deselected are the pre-existing `-m 'not eval'` exclusions. |
| `uv run ruff check backend/` | ✅ All checks passed | |
| `uv run ruff format --check backend/` | ✅ 156 files already formatted | |
| Ad-hoc: `load_scenario_config` on `language_policy/eval_spec.yaml` | ✅ Loaded OK | Returned scenario `language_policy` with scorers `tool_arg_no_cjk` / `response_language` / `response_relevance`, all `temperature=0.0`. |
| Ad-hoc: `model_fields_set` interaction check | ✅ Passed | `ScorerConfig(name=..., function=...)` (temperature omitted) yields `model_fields_set == {'function', 'name'}` and `temperature == 0.0` — `Field(default=...)` does **not** populate `model_fields_set`, so the Round 1 rejection of explicitly-set temperature on programmatic scorers is intact. |

### Tests Added or Modified

| Test File | Added/Modified | What It Tests |
|-----------|----------------|---------------|
| `backend/tests/evals/test_scorer_registry.py` | Added `test_scorer_config_rejects_out_of_range_temperature_on_llm_judge` | An `llm_judge` `ScorerConfig` with `temperature=2.5` raises a validation error at config-load time. Asserted via `pytest.raises(ValueError, match="less than or equal to 2")` — Pydantic's `ValidationError` subclasses `ValueError`, matching the neighbouring tests' style. |
