# agent_engine/utils

## Scope

Runtime helpers for the Agent Engine that are too small to deserve their own
subpackage but too stateful or data-coupled to live as free functions on
`base.py`. Today the only helper is the **model context-window registry** used
by the Orchestrator to render `{section_soft_cap_chars}` into system prompts.

## Map

- `model_context.py`: `get_model_context_window(model_name)` and
  `compute_section_soft_cap_chars(model_name, fraction=0.4)`. Reads the
  materialized registry and falls back to `DEFAULT_CONTEXT_WINDOW` (128 000
  tokens) with a warn-once log on miss.
- `model_context_registry.yaml`: **committed, materialized** per-model
  `max_input_tokens` table. Production imports of this module do **not**
  pull in `litellm` (~80 MB). Edit this file manually for ad-hoc entries or
  run the refresh script below to re-materialize from `litellm`.

## Workflow — adding or updating a model

1. Add the new model name to the relevant `backend/agent_engine/agents/versions/*/orchestrator_config.yaml`.
2. Regenerate the registry:
   ```bash
   uv run --extra dev python backend/scripts/refresh_model_context_registry.py
   ```
   The script reads every `versions/*/orchestrator_config.yaml`, calls
   `litellm.get_model_info(name)` per unique model, and rewrites
   `model_context_registry.yaml` sorted by key. Existing `source: manual`
   rows are preserved when `litellm` has no data for that model.
3. Commit both the config change and the regenerated YAML in the same PR —
   out-of-sync state triggers the `DEFAULT_CONTEXT_WINDOW` fallback with a
   warn-once log at runtime.

## Design Pattern

- **Materialized registry**: YAML is the source of truth at runtime;
  `litellm` is a dev-only dependency used to regenerate it. Keeps
  production image size down and removes a network dependency from
  Orchestrator startup.
- **Warn-once fallback**: unknown models do not crash the agent. They
  fall through to `DEFAULT_CONTEXT_WINDOW` with a one-time `logger.warning`
  so long-running processes do not spam logs, but CI / manual testing
  catches the miss on first invocation.
