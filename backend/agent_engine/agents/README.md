## Scope
Version-agnostic Orchestrator and configuration loading. This module provides the central reasoning engine that loads capabilities and constraints from versioned configuration files.

## Map
- `base.py`: Defines the `Orchestrator` class, which uses LangChain to manage the ReAct tool-calling loop. `_init_model()` translates `ModelConfig` into provider-aware reasoning kwargs (see Multi-Provider Reasoning Configuration below). `_build_langfuse_config()` attaches a per-request `CallbackHandler` + a `ReasoningTraceCallback` plus a `RunnableConfig` carrying `run_name="chat-turn"` and `metadata={langfuse_trace_name: f"{config.name}_{mode}", request_id: ...}`; `propagate_attributes(trace_name=..., session_id=...)` wraps the invocation for OTel-context correlation. `_handle_abort_cleanup()` drains the segmenter tail and stamps the trace on user abort (see Streaming Reasoning Trace & Abort Protocol). Extracts results via `_extract_result`.
- `config_loader.py`: Implements `VersionConfigLoader` and `VersionConfig` Pydantic models for loading `orchestrator_config.yaml` and `system_prompt.md` from version directories. `ModelConfig` exposes `reasoning` (`"on"` / `"off"` / `"unsupported"`) and `thinking_budget` for admin-configured reasoning capability binding — see `versions/README.md` for field semantics and provider examples.
- `versions/`: Subdirectory containing versioned workflow configurations (v1-v5).

## Design Pattern
- **Strategy Pattern**: The `Orchestrator` behavior is determined by the `VersionConfig` passed at initialization, allowing different analysis strategies (baseline, reader, quant, etc.) without changing the core logic.
- **Singleton Pattern**: The `Orchestrator` is typically managed as a singleton within the application lifecycle to maintain consistent state and resource usage.

## Prompt Template Rendering

`Orchestrator._render_prompt()` substitutes `{identifier}` placeholders in system prompts at construction time. Unknown placeholders raise `ValueError` at startup — drift fails fast.

| Placeholder | Source |
|-------------|--------|
| `{section_soft_cap_chars}` | `backend.agent_engine.utils.model_context.compute_section_soft_cap_chars(model_name)` |
| `{max_tool_calls_per_run}` | `config.constraints.max_tool_calls_per_run` (same value `RunBudgetMiddleware` enforces) |

## Multi-Provider Reasoning Configuration

`_init_model()` translates `ModelConfig.reasoning` + `thinking_budget` into the provider-specific kwargs `init_chat_model` expects. Each provider's reasoning API has different requirements; mis-configuration fails at first request, not at startup, so the matrix below is enforced explicitly in `_init_model`.

| Provider prefix       | `reasoning="on"`                                                            | `reasoning="off"`     | Hard constraints                                                                                       |
| --------------------- | --------------------------------------------------------------------------- | --------------------- | ------------------------------------------------------------------------------------------------------ |
| `google_genai`        | `thinking_budget=<budget>` + `include_thoughts=True`                         | `thinking_budget=0`   | `include_thoughts` is required, or the response carries no reasoning content_blocks (silent empty)     |
| `anthropic`           | `thinking={"type":"enabled","budget_tokens":<budget>}`                       | (no `thinking` kwarg) | `thinking_budget >= 1024` AND `temperature == 1.0`; otherwise the Anthropic API returns HTTP 400      |
| `openai` (default for bare names) | `reasoning={"effort":"medium","summary":"auto"}` + `use_responses_api=True` | (no `reasoning` kwarg) | `summary="auto"` is required, or gpt-5 / o4 emit no reasoning content_blocks                          |
| Any                   | `reasoning="unsupported"` short-circuits before any provider branch — no reasoning kwarg passed | — | Use for bound models that physically reject reasoning kwargs (e.g. gemini-1.5, gemini-2.5-pro disabled) |

`thinking_budget=None` is accepted for Gemini (provider default) and OpenAI (unused). It raises `ValueError` at startup for Anthropic with `reasoning="on"` because the API requires an explicit `budget_tokens`.

## Streaming Reasoning Trace & Abort Protocol

`_build_langfuse_config()` injects two callbacks per request, in order:

1. **`ReasoningTraceCallback`** — writes `metadata.reasoning` to each chat-model GENERATION on `on_llm_end`. Holds a reference to the Langfuse `CallbackHandler` so it can look the GENERATION up by `run_id` from `handler._runs` (avoiding OTel current-span propagation bugs under LangChain's async dispatch). The 5 value states are documented in `agent_engine/streaming/README.md`.
2. **`langfuse.langchain.CallbackHandler`** — standard span ingest.

Ordering is documented but not load-bearing for correctness: lookup-by-run_id makes the reasoning write deterministic as soon as the Langfuse handler registers the GENERATION at `on_chat_model_start`. Keeping the reasoning callback first means `metadata.reasoning` lands before any downstream handler observes the GENERATION.

`astream_run()` adds two D34 / D35 hooks around `agent.astream()`:

- **Natural termination** — after `agent.astream()` exhausts, `mapper.finalize()` drains any segmenter tail (last reasoning sentence without a terminator) and emits a `Finish` event.
- **User abort (`asyncio.CancelledError`)** — `_handle_abort_cleanup()` runs synchronously by design; sync code is not interruptible by `CancelledError` so cleanup completes even while the parent task is being cancelled. It:
  - Iterates `handler._runs.values()` (immune to key-shape drift — UUID / str / hex; only observation-type drift breaks `isinstance`, which is caught by `test_langfuse_runs_contract.py`) to locate the in-flight `LangfuseGeneration` and the root `LangfuseChain`.
  - Writes `metadata.reasoning_tail_aborted` — a **distinct key** from the completed-path `metadata.reasoning`. Value may be `""` when the segmenter buffer was empty; the key is always written (the always-write-key contract on the abort path).
  - Stamps the root chain with `metadata.status="aborted"`.

Operator queries on aborted traces must read `metadata.reasoning_tail_aborted` + `metadata.status` rather than expecting `metadata.reasoning` on the in-flight GENERATION (`on_llm_end` never fires for cancelled LLM calls). `backend/scripts/validation/verify_langfuse_trace.py --expect-aborted` enforces this shape in CI and post-deploy.

## Startup Validation

`Orchestrator.__init__` runs `_validate_edgar_identity(config)` before instantiating tools — versions that load any SEC EDGAR tool require `EDGAR_IDENTITY` or raise `backend.common.sec_core.ConfigurationError`. Tests that mock edgartools get a placeholder identity via the autouse fixture in `backend/tests/conftest.py`.

## Extension Algorithm
1. **Modify Orchestrator Logic**: Update the `Orchestrator` class in `base.py` to change how agents are initialized or how results are extracted.
2. **Add Configuration Fields**: Update the `VersionConfig`, `ModelConfig`, or `ConstraintsConfig` classes in `config_loader.py` to support new configuration parameters.
3. **Update System Prompts**: Modify the `_DEFAULT_SYSTEM_PROMPT` in `base.py` for global changes, or update individual `system_prompt.md` files in the `versions/` directory.
