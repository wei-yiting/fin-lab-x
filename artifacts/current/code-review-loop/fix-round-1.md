# Fix Round 1

> Fixer: claude (code-fixer subagent) | Date: 2026-08-02

### Fixed

| Issue ID | How Fixed | Files Changed |
|----------|-----------|---------------|
| m-1.1 | Replaced the value-based check `if self.temperature != 0.0` with the presence-based check `if "temperature" in self.model_fields_set` in `ScorerConfig.validate_mode`, so any explicitly-provided `temperature` on a programmatic scorer is rejected regardless of value. Added two regression tests. | `backend/evals/eval_spec_schema.py` (L50), `backend/tests/evals/test_scorer_registry.py` |
| m-1.2 | Added `temperature: float          # (optional) Judge sampling temperature, default 0.0; llm_judge only` to the `llm_judge` scorer block in the `Eval Spec YAML Schema` section, matching the neighbouring `model:` / `use_cot:` comment style. | `backend/evals/README.md` (after L167) |

### Not Fixed (with reason)

| Issue ID | Reason |
|----------|--------|
| M-1.1 (ADR-0007 word count) | Explicitly declined by the human owner (2026-08-02): ADR-0007 keeps its current length. DEV-120's decision D6 mandates six specific content areas that do not fit the envelope §4 ≤100-word limit, and no existing ADR in `docs/adr/` meets that limit either. `docs/adr/0007-llm-judge-bypasses-braintrust-gateway.md` untouched. Orchestrator note: this is an accepted deviation, not a fixer refusal — do not re-raise. |

### Reverted (fix broke tests)

None.

### Tests Run

| Test Command | Result | Notes |
|--------------|--------|-------|
| `uv run pytest backend/tests/evals/ -q` | ✅ 133 passed | Run immediately after the schema change |
| `uv run pytest backend/tests/ -q` | ✅ 853 passed, 49 deselected | Full suite, no regressions |
| `uv run ruff check backend/` | ✅ All checks passed | |
| `uv run ruff format --check backend/` | ✅ 156 files already formatted | |
| Ad-hoc: `load_scenario_config` on `language_policy/eval_spec.yaml` | ✅ Loads clean | Confirms the production spec still validates: programmatic scorers report `model_fields_set` without `temperature`; `response_relevance` (llm_judge) has it set |

### Tests Added or Modified

| Test File | Added/Modified | What It Tests |
|-----------|----------------|---------------|
| `backend/tests/evals/test_scorer_registry.py` | Added `test_scorer_config_rejects_explicit_zero_temperature_on_programmatic_scorer` | The m-1.1 regression: a programmatic scorer explicitly passing `temperature=0.0` now raises `ValueError` |
| `backend/tests/evals/test_scorer_registry.py` | Added `test_scorer_config_allows_programmatic_scorer_without_temperature` | Guards the other side of the split — omitting `temperature` still validates and keeps the `0.0` default, so the stricter check didn't break normal programmatic configs |

### Fixer note

The new explicit-zero test's `def` line exceeds 88 chars with a plain `-> None`, so `ruff format` wrapped the return annotation as `-> (\n    None\n):`. That is ruff's own formatting, not a hand-choice.
