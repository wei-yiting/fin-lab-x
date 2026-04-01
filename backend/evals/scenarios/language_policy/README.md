# Language Policy Scenario

## Folder Responsibility

This directory defines the **language policy evaluation scenario** — the dataset and configuration that verify the agent responds in the correct language (Traditional Chinese for zh prompts, English for en prompts) and keeps tool arguments in English regardless of input language.

## File Manifest

| File | Role |
|---|---|
| `eval_spec.yaml` | Scenario configuration: declares the task function, CSV dataset path, column-to-field mapping, and the list of scorers (two programmatic + one LLM judge). |
| `dataset.csv` | Evaluation cases with columns: `id`, `description`, `prompt`, `prompt_language`, `ticker`, `expect_tool`, `expect_search_query_no_cjk`, `expect_response_cjk_min`, `expect_response_cjk_max`. Currently 8 cases covering Chinese, English, and mixed-language prompts. |

## Architecture & Design

This scenario follows the **CSV-driven eval pattern** established by the eval framework:

1. **`eval_spec.yaml`** is the entry point. The `eval_runner.py` discovers scenario directories, loads this file via `scenario_config.py`, and assembles a Braintrust `Eval()` run.
2. **`column_mapping`** in the YAML maps CSV column names to the structured `input`, `expected`, and `metadata` fields consumed by scorers. This decouples the CSV schema from scorer internals.
3. **Scorers** are declared by reference:
   - `tool_arg_no_cjk` and `response_language` — programmatic scorers in `backend/evals/scorers/language_policy_scorer.py`.
   - `response_relevance` — an `llm_judge` scorer using GPT-4o with a rubric template that checks the agent stays on-topic for the expected ticker.

The dataset is intentionally small (8 cases) to keep eval runs fast while covering the key language combinations.

## Implementation Guidelines

When modifying or extending this scenario:

1. **Adding cases** — Append rows to `dataset.csv`. No code changes needed; the `dataset_loader.py` picks up new rows automatically.
2. **Adding scorers** — Add a new entry under `scorers:` in `eval_spec.yaml`. For programmatic scorers, provide `function:` with the full dotpath. For LLM judges, set `type: llm_judge` with `rubric:`, `model:`, and `choice_scores:`.
3. **Adding expected columns** — Add the column to `dataset.csv` and map it in `column_mapping`. Use the `expected.<field>` prefix so the value is available in the scorer's `expected` dict.
4. **Running this scenario** — `uv run pytest backend/evals/ -m eval -k "language_policy" -v`.
5. Update this README's File Manifest if new files are added.
