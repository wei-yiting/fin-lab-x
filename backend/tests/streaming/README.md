# Streaming Tests

Unit + provider-shape integration tests for `backend.agent_engine.streaming` — domain events, `StreamEventMapper`, `ReasoningSegmenter`, `ReasoningTraceCallback`, SSE serializer, tool-error sanitizer, dev-only env flags, and the Langfuse `_runs` contract guard.

Module under test: `backend/agent_engine/streaming/` (see its README for the layered architecture: domain events → event mapper → SSE serializer; reasoning callback runs in parallel).

## Files

| File | Surface under test |
|------|--------------------|
| `test_domain_events_schema.py` | Frozen `@dataclass` immutability, construction, equality of `TextStarted` / `TextDelta` / `ToolCallStarted` / `ReasoningStatus` / etc. |
| `test_event_mapper.py` | `StreamEventMapper` core — `chunk.content_blocks` dispatch, text-block pairing, tool-call lifecycle, `finalize()`, per-request scope (D33) |
| `test_event_mapper_dev_flags.py` | Dev-only env flags on the mapper (e.g., `BYPASS_TOOL_LIMIT`, debug emission paths) |
| `test_event_mapper_reasoning_integration.py` | Provider-shape integration — real `AIMessageChunk` sequences from Anthropic (interleaved reasoning+text), OpenAI Responses (multi-summary), Gemini (empty-then-text) fed end-to-end |
| `test_reasoning_segmenter.py` | Sentence-boundary splitter — half-width `.!?` / full-width `。！？` / `\n` (CRLF-aware) / 80-char CJK fallback (D26) |
| `test_reasoning_trace_callback.py` | `ReasoningTraceCallback.on_llm_end` writes the always-write `metadata.reasoning` key; capability sentinels (`<unsupported>`); 500-KB UTF-8 byte cap; `_lookup_generation_by_run_id` drift-fallback chain (UUID → str → hex) with one-shot warning |
| `test_orchestrator_invoke_reasoning_path.py` | S-stream-05 — `invoke` (non-streaming) path also writes `metadata.reasoning` |
| `test_sse_serializer.py` | `singledispatch` registry → AI SDK UIMessage Stream Protocol v1 wire format; `data-reasoning-status` carries `transient: True` |
| `test_sse_serializer_dev_flags.py` | Dev-only serializer flag (`FORCE_REASONING_NON_TRANSIENT` strips `transient`; assert-helper still raises in dev/CI, warn-logs in prod) |
| `test_tool_error_sanitizer.py` | Strips secrets / file paths / connection strings / stack traces from tool error messages before they reach the client |
| `test_langfuse_runs_contract.py` | Pinning the `langfuse.langchain.CallbackHandler._runs` private contract — drives Langfuse's real `on_chain_start` / `on_chat_model_start` bookkeeping path and asserts EXACT UUID key + concrete observation types. Marker: `langfuse_internal_contract`. |

## Run

```bash
uv run pytest backend/tests/streaming/ -q

# Just the Langfuse SDK-contract guard (run after any langfuse upgrade)
uv run pytest -m langfuse_internal_contract -q
```

## Conventions

- Mock LLM chunks with `langchain_core.messages.AIMessageChunk` carrying `content_blocks=[{"type":"reasoning","reasoning":...}, {"type":"text","text":...}]`. Provider-shape integration tests live in `test_event_mapper_reasoning_integration.py`.
- Reasoning callback tests assert the D29 always-write-key contract on both completed path (`reasoning`) and abort path (`reasoning_tail_aborted`, always written when an in-flight generation exists, `""` for empty buffers).
- SSE serializer tests assert `transient: True` is present on every `data-reasoning-status` event; the dev-only `FORCE_REASONING_NON_TRANSIENT` flag is the one knob that intentionally violates this and triggers `_assert_reasoning_transient` to raise (dev/CI) or warn (prod).
- The Langfuse `_runs` contract guard is the most upgrade-fragile test in this folder. It is the load-bearing CI signal that catches an SDK key-shape drift before production silently misses reasoning metadata. Re-run it explicitly after every Langfuse version bump.
