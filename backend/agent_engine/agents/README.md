## Scope
Profile-agnostic Orchestrator and configuration loading. This module provides the central reasoning engine that loads capabilities and constraints from Workflow Profile directories.

## Map
- `base.py`: Defines the `Orchestrator` class, which uses LangChain to manage the ReAct tool-calling loop. `_init_model()` translates `ModelConfig` into provider-aware reasoning kwargs (see Multi-Provider Reasoning Configuration below). `_build_langfuse_config()` attaches a per-request `CallbackHandler` plus a `RunnableConfig` carrying `run_name="chat-turn"` and `metadata={langfuse_trace_name: f"{config.name}_{mode}", request_id: ...}`; `propagate_attributes(trace_name=..., session_id=...)` wraps the invocation for OTel-context correlation. Extracts results via `_extract_result`.
- `config_loader.py`: Implements `ProfileConfigLoader` and `WorkflowProfileConfig` Pydantic models for loading `orchestrator_config.yaml` and `system_prompt.md` from profile directories. `ModelConfig` exposes `reasoning` (`"on"` / `"off"` / `"unsupported"`) and `thinking_budget` for admin-configured reasoning capability binding — see `profiles/README.md` for field semantics and provider examples.
- `profiles/`: Subdirectory containing the Workflow Profiles, one per capability tier (`baseline` … `analyst`).

## Design Pattern
- **Strategy Pattern**: The `Orchestrator` behavior is determined by the `WorkflowProfileConfig` passed at initialization, allowing different analysis strategies (baseline, reader, quant, etc.) without changing the core logic.
- **Singleton Pattern**: The `Orchestrator` is typically managed as a singleton within the application lifecycle to maintain consistent state and resource usage.

## Prompt Template Rendering

`Orchestrator._render_prompt()` substitutes `{identifier}` placeholders in system prompts at construction time. Unknown placeholders raise `ValueError` at startup — drift fails fast.

| Placeholder | Source |
|-------------|--------|
| `{section_soft_cap_chars}` | `backend.agent_engine.utils.model_context.compute_section_soft_cap_chars(model_name)` |
| `{max_tool_calls_per_run}` | `config.constraints.max_tool_calls_per_run` (same value `RunBudgetMiddleware` enforces) |

## Multi-Provider Reasoning Configuration

`_init_model()` translates `ModelConfig.reasoning` + `thinking_budget` into the provider-specific kwargs `init_chat_model` expects. Each provider's reasoning API has different requirements; some misconfigurations are caught explicitly at `_init_model()` construction time (see the Hard constraints column below), others would otherwise only surface as a provider API error on first request — the matrix below enforces the former explicitly wherever practical.

| Provider prefix       | `reasoning="on"`                                                            | `reasoning="off"`     | Hard constraints                                                                                       |
| --------------------- | --------------------------------------------------------------------------- | --------------------- | ------------------------------------------------------------------------------------------------------ |
| `google_genai`        | `thinking_budget=<budget>` + `include_thoughts=True`                         | `thinking_budget=0`   | `include_thoughts` is required, or the response carries no reasoning content_blocks (silent empty); with `reasoning="on"`, `thinking_budget` must be `None`, `-1`, or a positive integer — `0` or `< -1` raises `ValueError` |
| `anthropic`           | `thinking={"type":"enabled","budget_tokens":<budget>}`                       | (no `thinking` kwarg) | `thinking_budget >= 1024` AND `temperature == 1.0`; otherwise the Anthropic API returns HTTP 400      |
| `openai` (default for bare names) | `reasoning={"effort":"medium","summary":"auto"}` + `use_responses_api=True` | `reasoning_effort="minimal"` | `summary="auto"` is required, or gpt-5 / o4 emit no reasoning content_blocks. `reasoning="off"` **assumes a reasoning-capable model (gpt-5 tier)** and still needs `reasoning_effort="minimal"` explicitly — omitting it leaves gpt-5-tier models at the provider's own default effort, which empirically still burns billed reasoning tokens; `"none"` is rejected by the API for these models. Classic non-reasoning OpenAI models (gpt-4o, gpt-4o-mini, gpt-3.5, etc.) are **not compatible** with `reasoning="off"` on this provider — the API rejects `reasoning_effort` for them; use `reasoning="unsupported"` instead |
| Unrecognized provider | Raises `ValueError` — no reasoning kwarg mapping implemented | no-op (only `temperature` is passed) | — |
| Any                   | `reasoning="unsupported"` short-circuits before any provider branch — no reasoning kwarg passed | — | Use for a model that has no reasoning capability at all (e.g. gpt-4o-mini), or one whose reasoning cannot be controlled via these kwargs (e.g. gemini-2.5-pro, which cannot have thinking disabled). Provider-default reasoning behavior may still apply and may still be billed |

`thinking_budget=None` is accepted for Gemini (provider default) and OpenAI (unused). It raises `ValueError` at startup for Anthropic with `reasoning="on"` because the API requires an explicit `budget_tokens`.

## Startup Validation

`Orchestrator.__init__` runs `_validate_edgar_identity(config)` before instantiating tools — profiles that load any SEC EDGAR tool require `EDGAR_IDENTITY` or raise `backend.common.sec_core.ConfigurationError`. Tests that mock edgartools get a placeholder identity via the autouse fixture in `backend/tests/conftest.py`.

## Extension Algorithm
1. **Modify Orchestrator Logic**: Update the `Orchestrator` class in `base.py` to change how agents are initialized or how results are extracted.
2. **Add Configuration Fields**: Update the `WorkflowProfileConfig`, `ModelConfig`, or `ConstraintsConfig` classes in `config_loader.py` to support new configuration parameters.
3. **Update System Prompts**: Modify the `_DEFAULT_SYSTEM_PROMPT` in `base.py` for global changes, or update individual `system_prompt.md` files in the `profiles/` directory.
