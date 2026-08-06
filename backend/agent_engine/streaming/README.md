# Streaming Pipeline

Three-layer architecture that transforms LangGraph agent output into SSE wire format.

## Layers

| Layer | File | Responsibility |
|-------|------|----------------|
| Domain Events | `domain_events_schema.py` | Frozen dataclass value objects defining the shared contract between mapper and serializer. |
| Event Mapper | `event_mapper.py` | Stateful translator: LangGraph `astream()` chunks → domain events. Handles text block pairing, message framing, tool call lifecycle, and native reasoning part dispatch. Per-request scope (D33) — never share across requests. |
| Reasoning Transcript Accumulator | `reasoning_transcript_accumulator.py` | Observes reasoning domain events and renders the trace-level transcript (`=== segment N ===` markers, aborted marker, size cap) that `Orchestrator.astream_run` writes once to the root span metadata at conversation end (ADR-0011). Platform-agnostic. |
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

- a `text` block arrives (provider moved on to answer text),
- a same-round tool call arrives — either normalized `content_blocks` shape
  (`tool_call_chunk`: OpenAI/Anthropic; `tool_call`: Gemini) closes the part
  the moment tool-call args appear (DEV-109 ruling 9, ADR-0012; supersedes
  ADR-0008's "keep chip open" allowance — the overlap turned out to happen
  every round, not rarely),
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

Persistence is trace-level (F7 / ADR-0011): `ReasoningTranscriptAccumulator`
observes the same domain events and `Orchestrator.astream_run` writes the full
transcript once to the metadata of the root span it owns when the conversation
ends.

## `metadata.reasoning` Value Contract

The root span's `metadata.reasoning` is written once per conversation
(always-write-key). Single key; all structure lives inside the value:

| State                | Condition                                             | Value                                                       |
| -------------------- | ----------------------------------------------------- | ----------------------------------------------------------- |
| Reasoning transcript | capability ∈ {`"on"`, `"off"`} AND segments streamed  | `=== segment N ===`-delimited full text (one segment = one reasoning part = one frontend chip). Only text-bearing segments are rendered — zero-delta provider reasoning blocks are dropped and the kept segments are renumbered 1..K |
| No reasoning emitted | capability ∈ {`"on"`, `"off"`} AND no segments        | `""`                                                        |
| Unsupported model    | `capability == "unsupported"`                         | `"<unsupported>"` sentinel                                  |
| Oversize payload     | rendered value UTF-8 length > 500_000 bytes           | head kept, tail truncated so the FINAL value — including the `... [truncated, original {N} bytes]` note and the aborted marker when present — fits in 500KB |

On the **abort path** — `asyncio.CancelledError` or `GeneratorExit` through
`astream_run` (a client disconnect delivers one or the other depending on
whether the generator is suspended at an `await` or a `yield`; both are
`BaseException`, listed ahead of the generic `except` so neither collapses
into the `StreamError` path) — `_handle_abort_cleanup` performs one update on
the root span writing both the
reasoning tail — with a trailing `=== aborted ===` marker only when a segment
was cut mid-flight — and `metadata.status="aborted"` (the conversation-level
abort flag; the marker owns transcript integrity, the status key owns the
conversation outcome). `backend/scripts/validation/verify_langfuse_trace.py`
enforces these shapes.

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
