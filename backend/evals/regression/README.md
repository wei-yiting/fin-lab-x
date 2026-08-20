# Regression Suite

The manual pre-merge gate answering "did existing behavior get worse" with a
binary red/green verdict. Burns real LLM/API calls — deliberately not in CI.
Run it with `pytest backend/evals/regression/ -m eval` (see `AGENTS.md` for
profile selection and single-case debugging).

## Layout

| Path | Responsibility |
| --- | --- |
| `test_regression.py` | Pytest wrapper: discovers enabled scenarios, runs each through the unified profile path, asserts the gate verdict |
| `conftest.py` | Eval-marker wiring and `EVAL_PROFILE` resolution (read only here) |
| `verdict.py` | Gate evaluation: aggregates per-case scores per gated scorer and compares against each `metric_floor` (semantics: ADR-0008, ADR-0015) |
| `metric-floor-policy.md` | How floor numbers are derived and recorded: formula, margin rationale, measurement count, gate membership, re-derivation triggers |
| `reference_measurements/<scenario>/` | The recorded reference measurements backing each scenario's floors — one dated `.md` record + raw per-case `.csv` per measurement |
