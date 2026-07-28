# Streaming Tests

Unit + provider-shape integration tests for `backend.agent_engine.streaming` — domain events, `StreamEventMapper`, `ReasoningTraceCallback`, SSE serializer, tool-error sanitizer, and the Langfuse `_runs` contract guard.

Module under test: `backend/agent_engine/streaming/` (see its README for the layered architecture: domain events → event mapper → SSE serializer; reasoning callback runs in parallel).

## Files

| File | Surface under test |
|------|--------------------|
| `test_domain_events_schema.py` | Frozen `@dataclass` immutability, structural equality, chosen defaults, and the `DomainEvent` union-membership guard |
| `test_event_mapper.py` | `StreamEventMapper` core — `chunk.content_blocks` dispatch, text-block pairing, tool-call lifecycle, native reasoning parts (start/delta/end, raw passthrough, part boundaries, turn-unique ids), `finalize()`, per-request scope (D33) |
| `test_event_mapper_reasoning_integration.py` | Provider-shape integration — real `AIMessageChunk` sequences from Anthropic (interleaved reasoning+text → one part per contiguous block), OpenAI Responses (multi-summary explode → one part per summary), Gemini (CJK raw passthrough) fed end-to-end |
| `test_reasoning_trace_callback.py` | `ReasoningTraceCallback.on_llm_end` writes the always-write `metadata.reasoning` key; capability sentinels (`<unsupported>`); 500-KB UTF-8 byte cap; `_lookup_generation_by_run_id` drift-fallback chain (UUID → str → hex) with one-shot warning |
| `test_orchestrator_invoke_reasoning_path.py` | S-stream-05 — `invoke` (non-streaming) path also writes `metadata.reasoning` |
| `test_sse_serializer.py` | `singledispatch` registry → AI SDK UIMessage Stream Protocol v1 wire format, incl. native `reasoning-start` / `reasoning-delta` / `reasoning-end` frames |
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
- Reasoning wire tests assert the F5 native-part contract: one provider reasoning block = one `reasoning-start/delta*/end` sequence, deltas verbatim (no buffering / joining), part ids unique across the turn.
- Reasoning callback tests assert the D29 always-write-key contract on the completed path (`metadata.reasoning`). The abort path stamps only the root chain (`metadata.status="aborted"`) — covered in `backend/tests/agents/test_orchestrator_langfuse.py`.
- The Langfuse `_runs` contract guard is the most upgrade-fragile test in this folder. It is the load-bearing CI signal that catches an SDK key-shape drift before production silently misses reasoning metadata. Re-run it explicitly after every Langfuse version bump.
