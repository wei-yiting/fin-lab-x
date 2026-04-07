"""StreamEventMapper — stateful translator from LangGraph astream(version='v2') chunks to domain events.

Handles TextStart/TextEnd pairing, MessageStart/Finish framing,
and tool call lifecycle assembly across stream modes.
"""

from __future__ import annotations

from langchain_core.messages import AIMessage, ToolMessage

from backend.agent_engine.streaming.domain_events_schema import (
    DomainEvent,
    Finish,
    MessageStart,
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
    def __init__(self, session_id: str) -> None:
        self._session_id = session_id
        self._message_started = False
        self._text_block_open = False
        self._current_text_id: str | None = None
        self._pending_tool_calls: dict[str, str] = {}
        self._text_id_counter = 0
        self._total_input_tokens = 0
        self._total_output_tokens = 0

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

        if not self._message_started:
            events.append(MessageStart(message_id=msg_chunk.id, session_id=self._session_id))
            self._message_started = True

        if msg_chunk.content:
            if not self._text_block_open:
                self._current_text_id = self._next_text_id()
                events.append(TextStart(text_id=self._current_text_id))
                self._text_block_open = True
            events.append(TextDelta(text_id=self._current_text_id, delta=msg_chunk.content))

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
            self._total_output_tokens += msg_chunk.usage_metadata.get("output_tokens", 0)

        return events

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
                        events.append(ToolCall(
                            tool_call_id=tc["id"],
                            tool_name=tc["name"],
                            args=tc.get("args", {}),
                        ))

                if isinstance(msg, ToolMessage):
                    if msg.status == "error":
                        events.append(ToolError(tool_call_id=msg.tool_call_id, error=msg.content))
                    else:
                        events.append(ToolResult(tool_call_id=msg.tool_call_id, result=msg.content))
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
        events: list[DomainEvent] = []
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
