# Evaluation System

This folder has two different evaluation tracks. They serve different goals and should not be mixed.

## Two Evaluation Tracks

| Track | Goal | Entry Point | Typical Frequency | Output |
|---|---|---|---|---|
| Regression Guardrail | Catch severe regressions on critical behavior | `pytest` (`backend/evals/test_*.py`) | Before merge / release gate | pytest pass/fail |
| Quality Improvement | Measure agent quality changes over scenario datasets | `eval_runner` (`python -m backend.evals.eval_runner ...`) | Prompt iteration / model tuning | Result CSV + optional Braintrust experiment |

Use this rule:

- If the question is "did we break critical behavior?" -> **Regression Guardrail** (`pytest`)
- If the question is "did quality improve across scenarios?" -> **Quality Improvement** (`eval_runner`)

## Running Evaluations

### 1) Quality Improvement (Scenario Runner)

This is the primary flow for dataset-based quality evaluation.

```bash
# Local mode (recommended for development)
uv run python -m backend.evals.eval_runner language_policy --local-only

# Platform mode (uploads to Braintrust)
uv run python -m backend.evals.eval_runner language_policy

# Run all scenarios
uv run python -m backend.evals.eval_runner --all --local-only

# Custom output folder
uv run python -m backend.evals.eval_runner language_policy --local-only --output-dir ./tmp/eval-results
```

### 2) Regression Guardrail (pytest)

Use this for a compact "no serious regression" signal.

```bash
# Run guardrail eval tests
uv run pytest backend/evals/ -m eval -v --tb=short

# Run one case
uv run pytest backend/evals/ -m eval -k "LP-01" -v

# Unit tests only (CI default)
uv run pytest
```

`pyproject.toml` sets `testpaths = ["backend/tests"]` and `addopts = "-m 'not eval'"`, so bare `uv run pytest` excludes eval-marked tests unless explicitly requested.

## Prerequisites

Both tracks call real LLM/tools. Configure environment variables in `backend/.env`.

| Variable | Guardrail (pytest) | Quality Improvement (`--local-only`) | Quality Improvement (Braintrust mode) | Purpose |
|---|---|---|---|---|
| `OPENAI_API_KEY` | Yes | Yes | Yes | LLM calls |
| `TAVILY_API_KEY` | Scenario-dependent | Scenario-dependent | Scenario-dependent | Search tool calls |
| `EDGAR_IDENTITY` | Scenario-dependent | Scenario-dependent | Scenario-dependent | SEC retrieval |
| `BRAINTRUST_API_KEY` | No | No | Yes | Braintrust upload |

If `BRAINTRUST_API_KEY` is missing and `--local-only` is not set, `eval_runner` fails fast.

## File Manifest

```
backend/evals/
├── README.md
├── braintrust_config.yaml
├── scenario_config.py
├── dataset_loader.py
├── scorer_registry.py
├── eval_tasks.py
├── eval_runner.py
├── eval_helpers.py
├── scorers/
│   ├── README.md
│   └── language_policy_scorer.py
├── scenarios/
│   └── language_policy/
│       ├── README.md
│       ├── eval_spec.yaml
│       └── dataset.csv
├── results/
├── conftest.py
└── test_language_policy.py
```

## Architecture and Design

### Scenario-driven quality evaluation

- `scenarios/<name>/dataset.csv` stores evaluation cases.
- `scenarios/<name>/eval_spec.yaml` defines task function, column mapping, and scorers.
- `eval_runner` discovers scenarios, executes tasks, computes scores, and writes result CSV.

### Guardrail evaluation

- `test_language_policy.py` provides targeted regression checks using pytest.
- These tests should stay compact and stable; they are not the main vehicle for broad quality analysis.

### Scoring

- Prefer programmatic scorers when checks are structurally decidable.
- Use LLM-as-judge only when semantic judgment is required.

## Implementation Guidelines

### Add a new quality-improvement scenario

1. Create `backend/evals/scenarios/<scenario_name>/`.
2. Add `dataset.csv` and `eval_spec.yaml`.
3. Add/update task functions in `backend/evals/eval_tasks.py`.
4. Add/update scorers under `backend/evals/scorers/`.
5. Run `uv run python -m backend.evals.eval_runner <scenario_name> --local-only`.

### Add a new regression guardrail

1. Add/update `backend/evals/test_*.py` with `@pytest.mark.eval`.
2. Keep assertions focused on severe regression signals.
3. Run `uv run pytest backend/evals/ -m eval -v`.

### Separation rule (important)

- Do not force broad quality-improvement evaluations into pytest.
- Do not overload guardrail tests with large exploratory datasets.
- Keep `pytest` for **regression gate** and `eval_runner` for **quality iteration**.

## Future Implementation

When adding LlamaIndex-based evaluations, Braintrust integration should use
`braintrust[otel]` plus an OpenTelemetry exporter, keeping tracing explicit and
separate from evaluation logic.
