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
| `verdict.py` | Gate evaluation: aggregates per-case scores per gated scorer and compares against each `metric_floor` (semantics: ADR-0008, ADR-0016) |
| `sec_retrieval-metric-floors.md` | Decision record: why `sec_retrieval`'s floors have the values they do (formula, margin rationale, gate membership, re-derivation triggers) |
| `reference_measurements/<scenario>/` | The recorded reference measurements backing a scenario's calibrated floors. Each measurement is a dated record with its raw run data: `<YYYY-MM-DD>_<git-sha>.md` (what was measured: dataset version and provenance, retriever/pipeline and collection, model, per-scorer measured value → floor, per-case results, expiry conditions) + `<YYYY-MM-DD>_<git-sha>.csv` (the raw per-case run data, curated from the gitignored `backend/evals/results/` — the "run worth keeping" pattern from the `CONTEXT.md` Eval run entry) |
