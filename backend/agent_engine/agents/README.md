## Scope
Profile-agnostic Orchestrator and configuration loading. This module provides the central reasoning engine that loads capabilities and constraints from Workflow Profile directories.

## Map
- `base.py`: Defines the `Orchestrator` class, which uses LangChain to manage the ReAct tool-calling loop. `_init_model()` translates `ModelConfig` into provider-aware reasoning kwargs (see Multi-Provider Reasoning Configuration below). `_build_langfuse_config()` attaches a per-request `CallbackHandler` plus a `RunnableConfig` carrying `run_name="chat_turn"` and `metadata={langfuse_trace_name: f"{config.name}_{mode}", request_id: ...}`; `propagate_attributes(trace_name=..., session_id=...)` wraps the invocation for OTel-context correlation. `astream_run()` owns the request's root span and writes the trace-level reasoning transcript at conversation end; `_handle_abort_cleanup()` writes the reasoning tail + `metadata.status="aborted"` on user abort (see Streaming Reasoning Trace & Abort Protocol). Extracts results via `_extract_result`.
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

`_init_model()` translates `ModelConfig.reasoning` + `thinking_budget` into the provider-specific kwargs `init_chat_model` expects. Each provider's reasoning API has different requirements; mis-configuration fails at first request, not at startup, so the matrix below is enforced explicitly in `_init_model`.

| Provider prefix       | `reasoning="on"`                                                            | `reasoning="off"`     | Hard constraints                                                                                       |
| --------------------- | --------------------------------------------------------------------------- | --------------------- | ------------------------------------------------------------------------------------------------------ |
| `google_genai`        | `thinking_budget=<budget>` + `include_thoughts=True`                         | `thinking_budget=0`   | `include_thoughts` is required, or the response carries no reasoning content_blocks (silent empty)     |
| `anthropic`           | `thinking={"type":"enabled","budget_tokens":<budget>}`                       | (no `thinking` kwarg) | `thinking_budget >= 1024` AND `temperature == 1.0`; otherwise the Anthropic API returns HTTP 400      |
| `openai` (default for bare names) | `reasoning={"effort":"medium","summary":"auto"}` + `use_responses_api=True` | (no `reasoning` kwarg) | `summary="auto"` is required, or gpt-5 / o4 emit no reasoning content_blocks                          |
| Any                   | `reasoning="unsupported"` short-circuits before any provider branch — no reasoning kwarg passed | — | Use for bound models that physically reject reasoning kwargs (e.g. gemini-1.5, gemini-2.5-pro disabled) |

`thinking_budget=None` is accepted for Gemini (provider default) and OpenAI (unused). It raises `ValueError` at startup for Anthropic with `reasoning="on"` because the API requires an explicit `budget_tokens`.

## Streaming Reasoning Trace & Abort Protocol

`astream_run()` owns the request's root Langfuse span (ADR-0007): it opens
`start_as_current_observation(as_type="span", name="chat_turn")` around the
whole stream, so the `CallbackHandler` chain tree nests under it. A
`ReasoningTranscriptAccumulator` observes the reasoning domain events as they
are yielded; the transcript value contract is documented in
`agent_engine/streaming/README.md`.

Two termination hooks around `agent.astream()`:

- **Natural termination** — the transcript is written once to the root span's
  `metadata.reasoning` (holding the span reference makes the write
  deterministic — no OTel current-span lookup), then `mapper.finalize()`
  closes any open reasoning part / text block and emits a `Finish` event.
- **User abort (`asyncio.CancelledError`)** — `_handle_abort_cleanup()` runs
  synchronously by design; sync code is not interruptible by `CancelledError`
  so cleanup completes even while the parent task is being cancelled. One
  update on the root span writes the reasoning tail (with the aborted marker
  when a segment was cut mid-flight) plus `metadata.status="aborted"`. The
  wire stays silent (no final SSE frame).

Operator queries read the root span: `metadata.reasoning` for the transcript,
`metadata.status` for the conversation outcome.
`backend/scripts/validation/verify_langfuse_trace.py --expect-aborted`
enforces this shape in CI and post-deploy.

## Startup Validation

`Orchestrator.__init__` runs `_validate_edgar_identity(config)` before instantiating tools — profiles that load any SEC EDGAR tool require `EDGAR_IDENTITY` or raise `backend.common.sec_core.ConfigurationError`. Tests that mock edgartools get a placeholder identity via the autouse fixture in `backend/tests/conftest.py`.

## Extension Algorithm
1. **Modify Orchestrator Logic**: Update the `Orchestrator` class in `base.py` to change how agents are initialized or how results are extracted.
2. **Add Configuration Fields**: Update the `WorkflowProfileConfig`, `ModelConfig`, or `ConstraintsConfig` classes in `config_loader.py` to support new configuration parameters.
3. **Update System Prompts**: Modify the `_DEFAULT_SYSTEM_PROMPT` in `base.py` for global changes, or update individual `system_prompt.md` files in the `profiles/` directory.
