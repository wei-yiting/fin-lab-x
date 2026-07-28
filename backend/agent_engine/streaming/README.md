# Streaming Pipeline

Three-layer architecture that transforms LangGraph agent output into SSE wire format.

## Layers

| Layer | File | Responsibility |
|-------|------|----------------|
| Domain Events | `domain_events_schema.py` | Frozen dataclass value objects defining the shared contract between mapper and serializer. |
| Event Mapper | `event_mapper.py` | Stateful translator: LangGraph `astream()` chunks → domain events. Handles text block pairing, message framing, tool call lifecycle, and native reasoning part dispatch. Per-request scope (D33) — never share across requests. |
| Reasoning Trace Callback | `reasoning_trace_callback.py` | LangChain `BaseCallbackHandler` that writes `metadata.reasoning` to the current Langfuse generation on `on_llm_end`. Must run BEFORE `langfuse.langchain.CallbackHandler` (`run_inline = True` enforces ordering across sync + async dispatch). |
| SSE Serializer | `sse_serializer.py` | Stateless: domain events → AI SDK UIMessage Stream Protocol v1 wire format (`data: {json}\n\n`). Uses `singledispatch`. |

Additional module:
- `tool_error_sanitizer.py` — strips secrets, paths, and stack traces from error messages before they reach the client.

## Reasoning Pipeline (F5 — native parts)

Reasoning streams as AI SDK native `reasoning-*` parts. **One provider
reasoning block = one part**; provider deltas pass through verbatim (no
buffering, no sentence segmentation, no separator joining).

```
LangChain AIMessageChunk (with reasoning content_blocks)
        │
        ▼
  StreamEventMapper._handle_reasoning_block
        │
        ▼
  ReasoningStart(id) / ReasoningDelta(id, delta) / ReasoningEnd(id)
        │
        ▼
  serialize_event ──► data: {"type":"reasoning-start","id":...}
                      data: {"type":"reasoning-delta","id":...,"delta":...}
                      data: {"type":"reasoning-end","id":...}
```

Part boundaries (when the open part closes):

- a `text` or `tool_call_chunk` block arrives (provider moved on),
- the LLM call changes (`chunk.id` transition — each round of a multi-round
  tool loop gets its own part),
- a second `reasoning` block appears in the same chunk (OpenAI multi-summary
  explode — each summary is its own part),
- `finalize()` runs (natural finish and the error path both close the open
  part, so the wire always carries a complete `start/delta*/end` — except on
  abort, which is wire-silent by design).

Part `id`s (`reasoning-{n}`) are **unique across the whole turn**, not per
LLM call/step: the AI SDK resets its active-reasoning map on `finish-step`
and would otherwise allow id reuse across steps, colliding React keys and
timer refs on the frontend.

Persistence runs in parallel via `ReasoningTraceCallback.on_llm_end` writing the joined reasoning to `metadata.reasoning` on the current chat_model generation span.

## `metadata.reasoning` Value Contract

`ReasoningTraceCallback` writes `metadata.reasoning` on every chat-model GENERATION (always-write-key on the completed path). The value is one of five shapes:

| State                              | Condition                                                            | Value                                                          |
| ---------------------------------- | -------------------------------------------------------------------- | -------------------------------------------------------------- |
| Reasoning text                     | capability ∈ {`"on"`, `"off"`} AND `content_blocks` has reasoning     | `"\n".join(reasoning_block["reasoning"], ...)`                |
| No reasoning emitted               | capability ∈ {`"on"`, `"off"`} AND no reasoning blocks                | `""`                                                          |
| Unsupported model                  | `capability == "unsupported"`                                        | `"<unsupported>"` sentinel                                    |
| Oversize payload                   | joined UTF-8 length > 500_000 bytes                                  | first 500KB + `... [truncated, original {N} bytes]` suffix    |
| Extraction failure                 | `_compute_reasoning_value` raised                                    | `""` — defensive fallback so the always-write-key contract holds |

On the **abort path** (`asyncio.CancelledError` through `astream_run`),
`on_llm_end` never fires, so `metadata.reasoning` may be absent on the
in-flight GENERATION. `Orchestrator._handle_abort_cleanup` stamps
`metadata.status="aborted"` on the root chain; that is the only abort-trace
marker. (The former per-generation `reasoning_tail_aborted` write moves to
DEV-107 with F7's trace-level reasoning.) `backend/scripts/validation/verify_langfuse_trace.py` enforces these shapes.

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

Used by BDD verification to drive deterministic scenarios. **Never set these in production.**

| Flag | Effect |
|------|--------|
| `FORCE_LLM_FAIL=1` | `Orchestrator.astream_run` raises before `agent.astream` (mid-stream error path). |
