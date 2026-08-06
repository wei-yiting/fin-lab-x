"""StreamEventMapper — stateful translator from LangGraph astream(version='v2') chunks to domain events.

Handles TextStart/TextEnd pairing, MessageStart/Finish framing,
tool call lifecycle assembly, and native reasoning part dispatch
across stream modes.
"""

from __future__ import annotations

from langchain_core.messages import AIMessage, ToolMessage

from backend.agent_engine.streaming.domain_events_schema import (
    DomainEvent,
    Finish,
    MessageStart,
    ReasoningDelta,
    ReasoningEnd,
    ReasoningStart,
    TextDelta,
    TextEnd,
    TextStart,
    ToolCall,
    ToolError,
    ToolProgress,
    ToolResult,
    Usage,
)


class StreamEventMapper:
    """Per-request stateful translator (D33).

    One instance per chat HTTP request — never share across requests or
    sessions. Multi-tab concurrent streaming relies on this isolation;
    request-scoped state (reasoning part id counter, text_id counter,
    pending tool calls) would corrupt across concurrent streams if the
    mapper were per-session.

    Reasoning contract (F5): one provider reasoning block = one native
    reasoning part (ReasoningStart / ReasoningDelta* / ReasoningEnd).
    Provider deltas pass through verbatim — no buffering, no sentence
    segmentation, no separator joining. Part ids are unique across the
    whole turn (not per LLM call/step): the AI SDK resets its active
    reasoning map on finish-step and allows id reuse across steps, which
    would collide React keys / timer refs on the frontend.
    """

    def __init__(self, session_id: str) -> None:
        self._session_id = session_id
        self._message_started = False
        self._text_block_open = False
        self._current_text_id: str | None = None
        self._pending_tool_calls: dict[str, str] = {}
        self._text_id_counter = 0
        self._total_input_tokens = 0
        self._total_output_tokens = 0
        # Reasoning part state — turn-unique id counter + currently open part.
        self._current_llm_call_id: str | None = None
        self._open_reasoning_id: str | None = None
        self._reasoning_id_counter = 0
        # Idempotent finalize — invoked from both the natural-end and the
        # error cleanup paths.
        self._finalized = False

    def _next_text_id(self) -> str:
        # Within a single assistant turn we can emit multiple text blocks
        # separated by tool calls (text-0 → tool call → text-1 → finish).
        # Per AI SDK UIMessage protocol, each block's text-start/text-delta/
        # text-end must share an id, and sibling blocks must have different
        # ids so the client can keep them apart. A counter keeps IDs
        # deterministic for unit tests; uuid would work too but adds noise.
        text_id = f"text-{self._text_id_counter}"
        self._text_id_counter += 1
        return text_id

    def process_chunk(self, chunk: dict) -> list[DomainEvent]:
        chunk_type = chunk.get("type")
        if chunk_type == "messages":
            return self._handle_messages(chunk)
        if chunk_type == "updates":
            return self._handle_updates(chunk)
        if chunk_type == "custom":
            return self._handle_custom(chunk)
        return []

    def _handle_messages(self, chunk: dict) -> list[DomainEvent]:
        events: list[DomainEvent] = []
        msg_chunk, _metadata = chunk["data"]

        if isinstance(msg_chunk, ToolMessage):
            return events

        # chunk.id transitions are LLM-call boundaries — close any open
        # reasoning part so each round of a multi-round tool loop gets its
        # own part. id=None is treated as continuation (some providers emit
        # None on intermediate chunks).
        if msg_chunk.id is not None and msg_chunk.id != self._current_llm_call_id:
            self._close_reasoning_part(events)
            self._current_llm_call_id = msg_chunk.id

        if not self._message_started:
            events.append(
                MessageStart(message_id=msg_chunk.id, session_id=self._session_id)
            )
            self._message_started = True

        # Single ordered dispatch over the pinned langchain-core
        # provider-normalized accessor (code-review round 6/M-1.1): every
        # supported provider's tool call already surfaces in
        # `content_blocks` — OpenAI/Anthropic as `tool_call_chunk`, Gemini as
        # `tool_call` — so no separate pass over the raw `tool_call_chunks`
        # attribute is needed. Trusting one accessor also avoids the
        # ordering hazard the old two-route shape had (a `tool_call_chunk →
        # reasoning` chunk could have its new part wrongly closed by a
        # post-loop fallback).
        blocks = list(msg_chunk.content_blocks)

        prev_block_type: str | None = None
        for block in blocks:
            block_type = block.get("type")
            if block_type == "reasoning":
                # A reasoning block directly following another reasoning
                # block in the same chunk is a distinct provider block
                # (OpenAI multi-summary explode) → its own part.
                self._handle_reasoning_block(
                    block, events, force_new_part=(prev_block_type == "reasoning")
                )
            elif block_type == "text":
                self._handle_text_block(block, events)
            elif block_type in ("tool_call", "tool_call_chunk"):
                self._handle_tool_call_started(block, events)
            prev_block_type = block_type

        # LangChain does not auto-aggregate usage_metadata across streaming
        # chunks — the official pattern is to concatenate AIMessageChunks
        # with `+` and read .usage_metadata at the end. We don't need the
        # full concatenated message (TextDeltas are already flushed), so we
        # sum the two numeric fields directly. This works whether the
        # provider emits usage on every chunk (Anthropic-style deltas) or
        # only on the final chunk (OpenAI-style cumulative) — both sum to
        # the correct total.
        if getattr(msg_chunk, "usage_metadata", None):
            self._total_input_tokens += msg_chunk.usage_metadata.get("input_tokens", 0)
            self._total_output_tokens += msg_chunk.usage_metadata.get(
                "output_tokens", 0
            )

        return events

    def _handle_reasoning_block(
        self,
        block: dict,
        events: list[DomainEvent],
        force_new_part: bool = False,
    ) -> None:
        if force_new_part:
            self._close_reasoning_part(events)
        if self._open_reasoning_id is None:
            self._open_reasoning_id = f"reasoning-{self._reasoning_id_counter}"
            self._reasoning_id_counter += 1
            events.append(ReasoningStart(reasoning_id=self._open_reasoning_id))
        delta = block.get("reasoning", "")
        if delta:
            events.append(
                ReasoningDelta(reasoning_id=self._open_reasoning_id, delta=delta)
            )

    def _close_reasoning_part(self, events: list[DomainEvent]) -> None:
        if self._open_reasoning_id is not None:
            events.append(ReasoningEnd(reasoning_id=self._open_reasoning_id))
            self._open_reasoning_id = None

    def _handle_text_block(self, block: dict, events: list[DomainEvent]) -> None:
        # The provider moved on to answer text — the current reasoning
        # part (if any) is complete.
        self._close_reasoning_part(events)
        text = block.get("text", "")
        if not text:
            return
        if not self._text_block_open:
            self._current_text_id = self._next_text_id()
            events.append(TextStart(text_id=self._current_text_id))
            self._text_block_open = True
        events.append(TextDelta(text_id=self._current_text_id, delta=text))

    def _handle_tool_call_started(self, block: dict, events: list[DomainEvent]) -> None:
        # Tool args arriving means this round's reasoning block is over —
        # close the open part so the chip collapses at tool-start, matching
        # the `Thought for Xs` freeze point (DEV-109 ruling 2026-08-04,
        # supersedes the DEV-106 §B keep-open allowance: content_blocks give
        # the mapper no other end-of-block signal, which left every chip
        # open through the whole tool execution on the default provider).
        # Arrival order is preserved — the tool card renders below the
        # now-collapsed chip. Handles both normalized tool block types
        # (`tool_call_chunk`: OpenAI/Anthropic; `tool_call`: Gemini).
        self._close_reasoning_part(events)
        if self._text_block_open:
            events.append(TextEnd(text_id=self._current_text_id))
            self._text_block_open = False
        tc_id = block.get("id")
        tc_name = block.get("name")
        if tc_id and tc_name and tc_id not in self._pending_tool_calls:
            self._pending_tool_calls[tc_id] = tc_name

    def _handle_updates(self, chunk: dict) -> list[DomainEvent]:
        events: list[DomainEvent] = []
        data = chunk["data"]
        if not isinstance(data, dict):
            return events
        for _node_name, update in data.items():
            if not isinstance(update, dict):
                continue
            messages = update.get("messages", [])
            for msg in messages:
                if isinstance(msg, AIMessage) and msg.tool_calls:
                    for tc in msg.tool_calls:
                        events.append(
                            ToolCall(
                                tool_call_id=tc["id"],
                                tool_name=tc["name"],
                                args=tc.get("args", {}),
                            )
                        )

                if isinstance(msg, ToolMessage):
                    if msg.status == "error":
                        events.append(
                            ToolError(tool_call_id=msg.tool_call_id, error=msg.content)
                        )
                    else:
                        events.append(
                            ToolResult(
                                tool_call_id=msg.tool_call_id, result=msg.content
                            )
                        )
                    self._pending_tool_calls.pop(msg.tool_call_id, None)
        return events

    def _handle_custom(self, chunk: dict) -> list[DomainEvent]:
        data = chunk["data"]
        if not isinstance(data, dict):
            return []
        tool_call_id = data.get("toolCallId")
        if tool_call_id and tool_call_id in self._pending_tool_calls:
            return [ToolProgress(tool_call_id=tool_call_id, data=data)]
        return []

    def finalize(self) -> list[DomainEvent]:
        if self._finalized:
            return []
        self._finalized = True
        events: list[DomainEvent] = []
        # Reasoning may be the last content of the last LLM call — close the
        # open part so the wire always carries a complete start/delta*/end
        # sequence on natural finish and on the error path (the error path
        # replays finalize() minus Finish, giving reasoning-end → error →
        # finish per S-parts-04).
        self._close_reasoning_part(events)
        if self._text_block_open:
            events.append(TextEnd(text_id=self._current_text_id))
            self._text_block_open = False
        events.append(
            Finish(
                finish_reason="stop",
                usage=Usage(
                    input_tokens=self._total_input_tokens,
                    output_tokens=self._total_output_tokens,
                ),
            )
        )
        return events
