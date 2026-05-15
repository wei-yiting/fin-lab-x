# Agent Tests

Unit tests for `backend.agent_engine.agents` — `Orchestrator`, `_init_model` provider routing, `VersionConfigLoader`, prompt rendering / EDGAR identity fast-fail, dev-only env-flag handlers, and Langfuse `CallbackHandler` injection.

## Files

| File | Surface under test |
|------|--------------------|
| `test_base.py` | `Orchestrator` end-to-end shape + `_extract_result` |
| `test_init_model.py` | Provider prefix routing in `_init_model` (OpenAI / Anthropic / Gemini); reasoning capability + `thinking_budget` config |
| `test_config_loader.py` | `VersionConfigLoader` strict schema, `ModelConfig.reasoning` field, registry lookup |
| `test_orchestrator_prompt_rendering.py` | `_render_prompt()` placeholder substitution; EDGAR identity fast-fail |
| `test_orchestrator_langfuse.py` | `CallbackHandler` injection, `ReasoningTraceCallback` wiring, abort cleanup writes the always-write `reasoning_tail_aborted` key |
| `test_orchestrator_dev_flags.py` | `BYPASS_TOOL_LIMIT` / `FORCE_REASONING_NON_TRANSIENT` and other dev env flags |
| `test_utils_model_context.py` | `compute_section_soft_cap_chars` for the prompt template variable |

## Run

```bash
uv run pytest backend/tests/agents/ -q
```

Network / live-API tests live under `backend/tests/integration/` (marker: `@pytest.mark.integration`) and are excluded by default — they require `EDGAR_IDENTITY`, provider API keys, and a reachable Langfuse host.

## Conventions

- Mock LangChain models with `langchain_core.messages.AIMessage` fixtures; mock Langfuse via `pytest-mock` patches against `langfuse.get_client` and the `langfuse.langchain.CallbackHandler` constructor.
- For tests that exercise the orchestrator's startup validation (`_validate_edgar_identity`), rely on the autouse fixture in `backend/tests/conftest.py` that supplies a placeholder `EDGAR_IDENTITY` env var.
- Reasoning callback tests assert on the always-write-key contract (D29): every chat-model completion writes `metadata.reasoning`; every abort with an in-flight `LangfuseGeneration` writes `metadata.reasoning_tail_aborted` (`""` when buffer is empty).
