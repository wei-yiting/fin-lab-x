# backend/tests/evals/

## Scope

Unit tests for the `backend/evals/` evaluation framework. These tests validate scenario discovery, configuration parsing, dataset loading, scorer resolution, task function wrappers, and CSV result output — all without hitting real LLM APIs.

## Structure Map

| File | What It Tests |
|------|---------------|
| `test_eval_runner.py` | Scenario discovery, `run_scenario()` orchestration, `write_result_csv()` output, `_wrap_task` / `_wrap_scorer` error isolation, CLI `main()` |
| `test_eval_tasks.py` | Task functions (`run_v1`) — input extraction, orchestrator delegation, result structure |
| `test_scenario_config.py` | `ScenarioConfig` / `BraintrustConfig` YAML parsing and Pydantic validation |
| `test_dataset_loader.py` | CSV loading, column mapping, cell type conversion |
| `test_scorer_registry.py` | Dynamic scorer resolution from dotpath strings |

## Test Execution

```bash
# Run all eval unit tests
uv run pytest backend/tests/evals/

# Run a single test file
uv run pytest backend/tests/evals/test_eval_runner.py

# Run a specific test
uv run pytest backend/tests/evals/test_eval_runner.py::TestRunScenario::test_run_scenario_local_produces_result_csv
```

## Architecture & Design

### Testing Boundaries

These tests validate the **evaluation framework plumbing** — config parsing, data loading, scorer wiring, CSV output, and CLI orchestration. They do **not** test LLM output quality or real scorer accuracy; those concerns belong in `backend/evaluation/` integration tests.

### Mocking Rationale

- **Task functions** are mocked to avoid LLM API calls and ensure deterministic outputs.
- **Scorers** are mocked in orchestration tests (`TestRunScenario`) to isolate runner logic from scorer implementation. Dedicated scorer tests live in `test_scorer_registry.py` and scorer-specific test files.
- **Braintrust SDK** is never imported in unit tests; `local_only=True` mode is used to verify the local evaluation path.

### When to Use Integration / Eval Tests

| Need | Where |
|------|-------|
| Verify CSV column mapping, scorer wiring, CLI flags | `backend/tests/evals/` (here) |
| Validate real scorer logic with known inputs | `backend/tests/evals/` with real scorer imports (no mocks) |
| End-to-end LLM quality checks against Braintrust | `backend/evaluation/` |
| Regression tests for prompt or model changes | `backend/evaluation/` |

## Extension Guidance

- **Adding a new eval module?** Create a corresponding `test_<module>.py` in this directory.
- All tests should mock external dependencies (LLM APIs, Braintrust SDK) — never make real network calls.
- Use `tmp_path` fixtures for filesystem-dependent tests (scenario dirs, CSV output).
- Follow existing patterns: `@patch` decorators for dependency injection, `_make_*` helpers for test data construction.
