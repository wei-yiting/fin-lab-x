# Streaming Pipeline

Three-layer architecture that transforms LangGraph agent output into SSE wire format.

## Layers

| Layer | File | Responsibility |
|-------|------|----------------|
| Domain Events | `domain_events_schema.py` | Frozen dataclass value objects defining the shared contract between mapper and serializer. |
| Event Mapper | `event_mapper.py` | Stateful translator: LangGraph `astream()` chunks → domain events. Handles text block pairing, message framing, tool call lifecycle, and native reasoning part dispatch. Per-request scope — never share across requests. |
| SSE Serializer | `sse_serializer.py` | Stateless: domain events → AI SDK UIMessage Stream Protocol v1 wire format (`data: {json}\n\n`). Uses `singledispatch`. |

Additional module:
- `tool_error_sanitizer.py` — strips secrets, paths, and stack traces from error messages before they reach the client.

## Reasoning Pipeline (native parts)

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

- a `text` block arrives (provider moved on to answer text),
- a same-round tool call arrives — either normalized `content_blocks` shape
  (`tool_call_chunk`: OpenAI/Anthropic; `tool_call`: Gemini) closes the part
  the moment tool-call args appear (an earlier design kept the chip open
  until the next LLM call, but the overlap with tool execution turned out
  to happen every round rather than being a rare edge case),
- the LLM call changes (`chunk.id` transition — each round of a multi-round
  tool loop gets its own part),
- a second `reasoning` block appears in the same chunk (OpenAI multi-summary
  explode — each summary is its own part),
- `finalize()` runs (natural finish and the error path both close the open
  part, so the wire always carries a complete `start/delta*/end` — except on
  abort, which is wire-silent by design).

Arrival order is preserved in all cases — the tool card still renders below
the now-collapsed chip.

Part `id`s (`reasoning-{n}`) are **unique across the whole turn**, not per
LLM call/step: the AI SDK resets its active-reasoning map on `finish-step`
and would otherwise allow id reuse across steps, colliding React keys and
timer refs on the frontend.

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
