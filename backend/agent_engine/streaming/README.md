# Streaming Pipeline

Three-layer architecture that transforms LangGraph agent output into SSE wire format.

## Layers

| Layer | File | Responsibility |
|-------|------|----------------|
| Domain Events | `domain_events_schema.py` | Frozen dataclass value objects defining the shared contract between mapper and serializer. |
| Event Mapper | `event_mapper.py` | Stateful translator: LangGraph `astream()` chunks → domain events. Handles text block pairing, message framing, tool call lifecycle, and reasoning sentence dispatch via `ReasoningSegmenter`. Per-request scope (D33) — never share across requests. |
| Reasoning Segmenter | `reasoning_segmenter.py` | Sentence-boundary splitter for streaming reasoning text. Half-width `.!?` + whitespace, full-width `。！？`, `\n` (CRLF-aware). 80-char soft-emit fallback for CJK without terminators. |
| Reasoning Trace Callback | `reasoning_trace_callback.py` | LangChain `BaseCallbackHandler` that writes `metadata.reasoning` to the current Langfuse generation on `on_llm_end`. Must run BEFORE `langfuse.langchain.CallbackHandler` (`run_inline = True` enforces ordering across sync + async dispatch). Mode-aware schema: completed-path writes `reasoning`; orchestrator abort cleanup writes `reasoning_tail_aborted` instead. |
| SSE Serializer | `sse_serializer.py` | Stateless: domain events → AI SDK UIMessage Stream Protocol v1 wire format (`data: {json}\n\n`). Uses `singledispatch`. `data-reasoning-status` events always carry `transient: True` (asserted by `_assert_reasoning_transient`). |

Additional module:
- `tool_error_sanitizer.py` — strips secrets, paths, and stack traces from error messages before they reach the client.

## Reasoning Pipeline

```
LangChain AIMessageChunk (with reasoning content_blocks)
        │
        ▼
  StreamEventMapper._handle_reasoning_block
        │
        ▼
  ReasoningSegmenter.feed(delta) ──► [sentence, ...]
        │
        ▼
  ReasoningStatus(reasoning_id, text)
        │
        ▼
  serialize_event ──► data: {"type":"data-reasoning-status","transient":true,...}
```

Persistence runs in parallel via `ReasoningTraceCallback.on_llm_end` writing the joined reasoning to `metadata.reasoning` on the current chat_model generation span.

## Data Flow

```
LangGraph astream() chunks
        │
        ▼
  StreamEventMapper.process_chunk()  ──►  list[DomainEvent]
        │
        ▼
  serialize_event(event)             ──►  SSE string
        │
        ▼
  StreamingResponse body
```

## Adding a New Event Type

1. **Define** the dataclass in `domain_events_schema.py` (must be `frozen=True`).
2. **Add** it to the `DomainEvent` union type at the bottom of the same file.
3. **Emit** it from the appropriate `StreamEventMapper` handler (`_handle_messages`, `_handle_updates`, or `_handle_custom`).
4. **Register** a `@serialize_event.register` function in `sse_serializer.py`.
5. **Add tests** in `tests/streaming/` for both mapper emission and serializer wire format.

## Dev-only Stub Flags

Used by Playwright BDD specs to drive deterministic visual scenarios. **Never set these in production.**

| Flag | Effect |
|------|--------|
| `FORCE_LLM_FAIL=1` | `Orchestrator.astream_run` raises before `agent.astream` (mid-stream error path). |
| `FORCE_REASONING_NON_TRANSIENT=1` | SSE serializer strips `transient` from reasoning payload (D39 guard test path). |
| `EMIT_DELAYED_REASONING=1` | Mapper emits one reasoning chunk per request, drops the rest (frontend `.stalled` modifier triggers via 10s silence). |
| `EMIT_LATE_REASONING=1` | `finalize()` appends a synthetic `ReasoningStatus` after `Finish` (frontend `finishedRef` guard test). |
| `STUB_REASONING_ONLY=1` | Mapper drops text + tool_call_chunk blocks; reasoning-only stream. |
| `STUB_CONTENT_BLOCKS_NO_REASONING=<provider>` | Mapper drops reasoning blocks (graceful-degrade test path). |
