## Scope
Version-agnostic Orchestrator and configuration loading. This module provides the central reasoning engine that loads capabilities and constraints from versioned configuration files.

## Map
- `base.py`: Defines the `Orchestrator` class, which uses LangChain to manage the ReAct tool-calling loop. `_build_langfuse_config()` attaches a per-request `CallbackHandler` plus a `RunnableConfig` carrying `run_name="chat-turn"` and `metadata={langfuse_trace_name: f"{config.name}_{mode}", request_id: ...}`; `propagate_attributes(trace_name=..., session_id=...)` wraps the invocation for OTel-context correlation. Extracts results via `_extract_result`.
- `config_loader.py`: Implements `VersionConfigLoader` and `VersionConfig` Pydantic models for loading `orchestrator_config.yaml` and `system_prompt.md` from version directories.
- `versions/`: Subdirectory containing versioned workflow configurations (v1-v5).

## Design Pattern
- **Strategy Pattern**: The `Orchestrator` behavior is determined by the `VersionConfig` passed at initialization, allowing different analysis strategies (baseline, reader, quant, etc.) without changing the core logic.
- **Singleton Pattern**: The `Orchestrator` is typically managed as a singleton within the application lifecycle to maintain consistent state and resource usage.

## Prompt Template Rendering

System prompts may reference orchestrator-provided variables using `{identifier}` placeholders. `Orchestrator._render_prompt()` substitutes them at construction time:

| Placeholder | Source | Notes |
|-------------|--------|-------|
| `{section_soft_cap_chars}` | `backend.agent_engine.utils.model_context.compute_section_soft_cap_chars(model_name)` | Computed from the active model's context window — recomputes when the version config swaps the model. |
| `{max_tool_calls_per_run}` | `config.constraints.max_tool_calls_per_run` | Same value the `RunBudgetMiddleware` enforces, so the prompt and the runtime tell the agent the same number. |

The renderer matches `{name}` only where `name` is a Python-style identifier, so literal JSON fragments such as `{"role": "user"}` pass through unchanged. Any placeholder that is not in the provided table raises `ValueError` at construction time — prompts that drift away from the rendering contract fail fast at startup, never silently at first request.

## Startup Validation

`Orchestrator.__init__` runs `_validate_edgar_identity(config)` before instantiating tools. If the version config loads any tool that requires SEC EDGAR access and `EDGAR_IDENTITY` is not set, the orchestrator raises `backend.common.sec_core.ConfigurationError` immediately. Versions that don't reference SEC tools are unaffected; tests that fully mock edgartools provide a placeholder via the autouse fixture in `backend/tests/conftest.py`.

## Extension Algorithm
1. **Modify Orchestrator Logic**: Update the `Orchestrator` class in `base.py` to change how agents are initialized or how results are extracted.
2. **Add Configuration Fields**: Update the `VersionConfig`, `ModelConfig`, or `ConstraintsConfig` classes in `config_loader.py` to support new configuration parameters.
3. **Update System Prompts**: Modify the `_DEFAULT_SYSTEM_PROMPT` in `base.py` for global changes, or update individual `system_prompt.md` files in the `versions/` directory.
