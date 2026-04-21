# Eval Scorers

## Folder Responsibility

This directory contains **programmatic scorer functions** used by evaluation scenarios. Each scorer receives the agent's output and expected values, then returns an `autoevals.Score` indicating pass/fail. Scorers are referenced by their Python dotpath in scenario `eval_spec.yaml` files and resolved at runtime by `scorer_registry.py`.

## File Manifest

| File | Role |
|---|---|
| `__init__.py` | Re-exports all scorer functions for convenient imports. |
| `language_policy_scorer.py` | Two programmatic scorers for language policy compliance: `response_language` (CJK character ratio check) and `tool_arg_no_cjk` (ensures tool arguments contain no CJK characters). |
| `sec_retrieval_scorer.py` | Four retrieval-level scorers for SEC dense pipeline: `header_path_recall_at_5`, `header_path_recall_at_10` (fraction of expected header paths matched in top-K), `mean_reciprocal_rank`, and `mean_average_precision`. Uses composite hit logic: header_path startswith + optional answer snippet contains. |

## Architecture & Design

Scorers follow the **autoevals scorer protocol**:

```python
def scorer(output: Any, expected: Any, *, input: Any) -> Score:
```

- **`output`** — Dict with the agent's response and tool outputs.
- **`expected`** — Dict with threshold values (e.g., `cjk_min`, `cjk_max`) mapped from the dataset CSV via `column_mapping` in `eval_spec.yaml`.
- **`input`** — The original user prompt.

This signature is compatible with both Braintrust's `Eval()` runner and direct pytest invocation. Scorers are pure functions with no side effects — they inspect output and return a `Score(name=..., score=0.0|1.0)`.

The `scorer_registry.py` in the parent directory dynamically imports scorer functions by dotpath (e.g., `backend.evals.scorers.language_policy_scorer.tool_arg_no_cjk`), so scorers do not need manual registration beyond being importable.

## Implementation Guidelines

When adding a new scorer:

1. Create a new file in this directory named `<scenario>_scorer.py`.
2. Implement one or more functions matching the `(output, expected, *, input) -> Score` signature.
3. Return `Score(name="<scorer_name>", score=1.0)` for pass and `Score(name="<scorer_name>", score=0.0)` for fail.
4. Use helper utilities from `backend.evals.eval_helpers` for shared logic (e.g., `contains_cjk`, `cjk_ratio`).
5. Export the new functions in `__init__.py`.
6. Reference the scorer by its full dotpath in the scenario's `eval_spec.yaml` under `scorers[].function`.
7. Update this README's File Manifest.
