"""StreamEventMapper — stateful translator from LangGraph astream(version='v2') chunks to domain events.

Handles TextStart/TextEnd pairing, MessageStart/Finish framing,
tool call lifecycle assembly, and reasoning sentence dispatch
across stream modes.
"""

from __future__ import annotations

import os

from langchain_core.messages import AIMessage, ToolMessage

from backend.agent_engine.streaming.domain_events_schema import (
    DomainEvent,
    Finish,
    MessageStart,
    ReasoningStatus,
    TextDelta,
    TextEnd,
    TextStart,
    ToolCall,
    ToolError,
    ToolProgress,
    ToolResult,
    Usage,
)
from backend.agent_engine.streaming.reasoning_segmenter import ReasoningSegmenter


class StreamEventMapper:
    """Per-request stateful translator (D33).

    One instance per chat HTTP request — never share across requests or
    sessions. Multi-tab concurrent streaming relies on this isolation;
    request-scoped state (segmenter buffer, reasoning_id counter, text_id
    counter, pending tool calls) would corrupt across concurrent streams
    if the mapper were per-session.
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
        # Reasoning state — D26/D27/D28/D34
        self._segmenter = ReasoningSegmenter()
        self._current_llm_call_id: str | None = None
        self._current_reasoning_id: str | None = None
        self._reasoning_id_counter = 0
        # Idempotent finalize — Task 6's ReasoningTraceCallback may invoke
        # finalize() from multiple cleanup paths (natural / abort / error).
        self._finalized = False
        # DEV-ONLY: tracks whether the EMIT_DELAYED_REASONING flag has already
        # released its single allowed reasoning chunk for this mapper instance.
        # Production must NOT set EMIT_DELAYED_REASONING.
        self._delayed_reasoning_emitted = False

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

        # D27.1: chunk.id transitions are LLM-call boundaries — flush any
        # buffered reasoning tail under the prior reasoning_id, reset
        # segmenter, and arm a new reasoning_id for the next reasoning
        # block. id=None is treated as continuation (some providers emit
        # None on intermediate chunks).
        if msg_chunk.id is not None and msg_chunk.id != self._current_llm_call_id:
            self._flush_segmenter_into(events)
            self._segmenter.reset()
            self._current_llm_call_id = msg_chunk.id
            self._current_reasoning_id = None

        if not self._message_started:
            events.append(
                MessageStart(message_id=msg_chunk.id, session_id=self._session_id)
            )
            self._message_started = True

        # Iterate the LangChain v1 normalized content_blocks (D1). The lazy
        # property handles all three providers' raw shapes (string content,
        # list of blocks with text/reasoning/tool_call_chunk types).
        blocks = self._apply_dev_flag_block_filters(msg_chunk.content_blocks)
        prev_block_type: str | None = None
        for block in blocks:
            block_type = block.get("type")
            if block_type == "reasoning":
                self._handle_reasoning_block(
                    block, events, prepend_separator=(prev_block_type == "reasoning")
                )
            elif block_type == "text":
                self._handle_text_block(block, events)
            elif block_type == "tool_call_chunk":
                self._handle_tool_call_chunk_block(block, events)
            prev_block_type = block_type

        # Backup path — a few providers' content_blocks may not surface
        # tool_call_chunks; the legacy attribute keeps the tool path alive
        # in that case. Safe to run unconditionally because
        # _pending_tool_calls is a set-like dict (no duplicates).
        if getattr(msg_chunk, "tool_call_chunks", None):
            if self._text_block_open:
                events.append(TextEnd(text_id=self._current_text_id))
                self._text_block_open = False
            for tc in msg_chunk.tool_call_chunks:
                tc_id = tc.get("id")
                tc_name = tc.get("name")
                if tc_id and tc_name and tc_id not in self._pending_tool_calls:
                    self._pending_tool_calls[tc_id] = tc_name

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
        prepend_separator: bool = False,
    ) -> None:
        # DEV-ONLY: EMIT_DELAYED_REASONING releases ONE reasoning chunk total
        # then drops the rest. The natural stream's silence between that lone
        # emission and finish exceeds the frontend STALLED_THRESHOLD_MS and
        # flips ``stalled=true`` — the Playwright spec asserts that visual
        # state. A real per-chunk sleep is impossible here (sync path) and
        # anyway not needed: the observable contract is a single reasoning
        # chunk followed by silence, which this branch produces directly.
        # Production must NOT set EMIT_DELAYED_REASONING.
        if os.environ.get("EMIT_DELAYED_REASONING"):
            if self._delayed_reasoning_emitted:
                return
            self._delayed_reasoning_emitted = True

        # Lazy-mount reasoning_id at the first reasoning block of an LLM
        # call; same id is reused for every reasoning block within the
        # same chunk.id (D27.2 — frontend setText updates a single
        # reasoning indicator).
        if self._current_reasoning_id is None:
            self._current_reasoning_id = f"reasoning-{self._reasoning_id_counter}"
            self._reasoning_id_counter += 1
        # D12: consecutive reasoning blocks within one chunk get a `\n`
        # separator so different summaries (e.g. OpenAI multi-summary
        # explode) don't fuse. `\n` is itself an immediate terminator,
        # so the prior block's buffered content emits as a complete
        # ReasoningStatus before this block's text feeds.
        delta = ("\n" if prepend_separator else "") + block.get("reasoning", "")
        for sentence in self._segmenter.feed(delta):
            events.append(
                ReasoningStatus(reasoning_id=self._current_reasoning_id, text=sentence)
            )

    @staticmethod
    def _apply_dev_flag_block_filters(blocks: list[dict]) -> list[dict]:
        """DEV-ONLY filters that mutate the per-chunk block stream.

        Two flags are honored:

        - ``STUB_REASONING_ONLY`` — drop ``text`` and ``tool_call_chunk``
          blocks so the resulting stream is reasoning-only. Drives
          S-trace-05 (trace tail emits reasoning even when no text/tool
          blocks reach the wire).
        - ``STUB_CONTENT_BLOCKS_NO_REASONING=<provider>`` — drop
          ``reasoning`` blocks to simulate a regression where the
          LangChain v1 content_blocks normalizer stops surfacing
          reasoning for that provider. Drives S-trace-09. The value is
          treated as a non-empty truthy switch; the per-provider scope
          is documented but not enforced here because the mapper has no
          provider context — Playwright sets the flag only when the
          backend is configured for the matching provider.

        Production must NOT set either flag.
        """
        if os.environ.get("STUB_REASONING_ONLY"):
            return [b for b in blocks if b.get("type") == "reasoning"]
        if os.environ.get("STUB_CONTENT_BLOCKS_NO_REASONING"):
            return [b for b in blocks if b.get("type") != "reasoning"]
        return list(blocks)

    def _handle_text_block(self, block: dict, events: list[DomainEvent]) -> None:
        # D28 hold-and-flush: any buffered reasoning tail must reach the
        # wire BEFORE TextStart so the frontend can clear the reasoning
        # indicator on text-start without losing the last visible sentence.
        self._flush_segmenter_into(events)
        text = block.get("text", "")
        if not text:
            return
        if not self._text_block_open:
            self._current_text_id = self._next_text_id()
            events.append(TextStart(text_id=self._current_text_id))
            self._text_block_open = True
        events.append(TextDelta(text_id=self._current_text_id, delta=text))

    def _handle_tool_call_chunk_block(
        self, block: dict, events: list[DomainEvent]
    ) -> None:
        # D28 hold-and-flush — same rationale as _handle_text_block.
        self._flush_segmenter_into(events)
        if self._text_block_open:
            events.append(TextEnd(text_id=self._current_text_id))
            self._text_block_open = False
        tc_id = block.get("id")
        tc_name = block.get("name")
        if tc_id and tc_name and tc_id not in self._pending_tool_calls:
            self._pending_tool_calls[tc_id] = tc_name

    def _flush_segmenter_into(self, events: list[DomainEvent]) -> None:
        tail = self._segmenter.flush()
        if tail and self._current_reasoning_id is not None:
            events.append(
                ReasoningStatus(reasoning_id=self._current_reasoning_id, text=tail)
            )

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
        # D34: reasoning may be the last block of the last LLM call with no
        # terminator and no following text/tool. flush() here closes that
        # gap so the buffer is never lost.
        self._flush_segmenter_into(events)
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
        # DEV-ONLY: EMIT_LATE_REASONING injects a synthetic ReasoningStatus
        # AFTER Finish. The frontend's ``finishedRef`` (latched on the
        # ``finish`` SSE event) MUST drop this, leaving the indicator
        # cleared. Drives S-rsn-12 (post-finish reasoning event leakage).
        # Production must NOT set EMIT_LATE_REASONING.
        if os.environ.get("EMIT_LATE_REASONING"):
            events.append(
                ReasoningStatus(
                    reasoning_id="reasoning-late",
                    text="late thought after finish",
                )
            )
        return events
