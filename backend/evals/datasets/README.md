# Eval Datasets

## Folder Responsibility

This directory owns **evaluation case definitions** — the structured inputs and expected-output thresholds consumed by the parametrized tests in `backend/evals/test_*.py`. It is the single source of truth for *what* we evaluate; the test files define *how* we assert.

## File Manifest

| File | Role |
|---|---|
| `__init__.py` | Package marker (empty). |
| `language_policy.py` | Dataclass (`LangPolicyEvalCase`) and case list (`LANGUAGE_POLICY_CASES`) for language-policy compliance evals. |

## Architecture & Design

Each dataset module follows a consistent pattern:

1. **Frozen dataclass** — defines the schema for one eval case (ID, prompt, expected thresholds).
2. **Module-level list** — collects all cases; test files import this list for `@pytest.mark.parametrize`.

This separation means adding a new scenario is a data-only change — no test logic needs to be modified.

## Implementation Guidelines

When adding a new eval dataset:

1. Create a new Python file in this directory (e.g., `hallucination.py`).
2. Define a frozen dataclass for the case schema.
3. Export a module-level list of cases.
4. Import the list in the corresponding `test_*.py` and parametrize.
5. Update this README's File Manifest.
