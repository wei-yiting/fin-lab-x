"""Tests for StreamEventMapper — LangGraph v2 chunk → domain event translation."""

from langchain_core.messages import AIMessage, AIMessageChunk, ToolMessage

from backend.agent_engine.streaming.domain_events_schema import (
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
from backend.agent_engine.streaming.event_mapper import StreamEventMapper

SESSION_ID = "sess-001"


def make_messages_chunk_text(content: str, msg_id: str = "msg-1") -> dict:
    msg = AIMessageChunk(content=content, id=msg_id)
    return {"type": "messages", "data": (msg, {"langgraph_node": "agent"})}


def make_messages_chunk_tool_call(
    tool_call_id: str,
    tool_name: str,
    msg_id: str = "msg-1",
) -> dict:
    msg = AIMessageChunk(
        content="",
        id=msg_id,
        tool_call_chunks=[{"id": tool_call_id, "name": tool_name, "args": "{}"}],
    )
    return {"type": "messages", "data": (msg, {"langgraph_node": "agent"})}


def make_messages_chunk_usage(
    input_tokens: int,
    output_tokens: int,
    msg_id: str = "msg-1",
) -> dict:
    msg = AIMessageChunk(
        content="",
        id=msg_id,
        usage_metadata={
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": input_tokens + output_tokens,
        },
    )
    return {"type": "messages", "data": (msg, {"langgraph_node": "agent"})}


def make_updates_agent(tool_calls: list[dict], msg_id: str = "msg-1") -> dict:
    ai_msg = AIMessage(content="", id=msg_id, tool_calls=tool_calls)
    return {"type": "updates", "data": {"agent": {"messages": [ai_msg]}}}


def make_updates_tool_result(
    tool_call_id: str,
    content: str,
    tool_name: str = "poc_add",
) -> dict:
    tool_msg = ToolMessage(content=content, tool_call_id=tool_call_id, name=tool_name)
    return {"type": "updates", "data": {"tools": {"messages": [tool_msg]}}}


def make_updates_tool_error(
    tool_call_id: str,
    content: str,
    tool_name: str = "poc_add",
) -> dict:
    tool_msg = ToolMessage(
        content=content,
        tool_call_id=tool_call_id,
        name=tool_name,
        status="error",
    )
    return {"type": "updates", "data": {"tools": {"messages": [tool_msg]}}}


def make_custom_chunk(tool_call_id: str, extra: dict | None = None) -> dict:
    data = {"toolCallId": tool_call_id, "status": "querying", "message": "Fetching..."}
    if extra:
        data.update(extra)
    return {"type": "custom", "data": data}


class TestTextOnlyHappyPath:
    """messages chunks with content → MessageStart + TextStart + TextDelta* + TextEnd + Finish."""

    def test_text_only_stream(self):
        mapper = StreamEventMapper(session_id=SESSION_ID)

        events = mapper.process_chunk(make_messages_chunk_text("Hello", msg_id="msg-1"))
        assert events == [
            MessageStart(message_id="msg-1", session_id=SESSION_ID),
            TextStart(text_id="text-0"),
            TextDelta(text_id="text-0", delta="Hello"),
        ]

        events = mapper.process_chunk(make_messages_chunk_text(" world"))
        assert events == [TextDelta(text_id="text-0", delta=" world")]

        events = mapper.finalize()
        assert events == [
            TextEnd(text_id="text-0"),
            Finish(finish_reason="stop", usage=Usage()),
        ]


class TestToolCallHappyPath:
    """text → tool_call_chunks → agent update → tool update → more text → finish."""

    def test_full_tool_call_lifecycle(self):
        mapper = StreamEventMapper(session_id=SESSION_ID)

        # Text before tool call
        events = mapper.process_chunk(make_messages_chunk_text("Let me check", msg_id="msg-1"))
        assert MessageStart(message_id="msg-1", session_id=SESSION_ID) in events
        assert TextStart(text_id="text-0") in events
        assert TextDelta(text_id="text-0", delta="Let me check") in events

        # Tool call chunk — should auto-close text block (no ToolCall emitted yet)
        events = mapper.process_chunk(
            make_messages_chunk_tool_call("tc-1", "poc_add", msg_id="msg-1")
        )
        assert TextEnd(text_id="text-0") in events
        assert not any(isinstance(e, ToolCall) for e in events)

        # Agent update — ToolCall emitted with complete name + args
        events = mapper.process_chunk(
            make_updates_agent([{"id": "tc-1", "name": "poc_add", "args": {"a": 1, "b": 2}}])
        )
        assert ToolCall(tool_call_id="tc-1", tool_name="poc_add", args={"a": 1, "b": 2}) in events

        # Tool result
        events = mapper.process_chunk(make_updates_tool_result("tc-1", "3"))
        assert ToolResult(tool_call_id="tc-1", result="3") in events

        # More text after tool
        events = mapper.process_chunk(make_messages_chunk_text("The result is 3"))
        assert TextStart(text_id="text-1") in events
        assert TextDelta(text_id="text-1", delta="The result is 3") in events

        # Finalize
        events = mapper.finalize()
        assert TextEnd(text_id="text-1") in events
        assert any(isinstance(e, Finish) for e in events)


class TestToolError:
    """tool update with ToolMessage(status="error") → ToolError."""

    def test_tool_error_emitted(self):
        mapper = StreamEventMapper(session_id=SESSION_ID)

        mapper.process_chunk(make_messages_chunk_text("Checking", msg_id="msg-1"))
        mapper.process_chunk(make_messages_chunk_tool_call("tc-1", "poc_add"))
        mapper.process_chunk(
            make_updates_agent([{"id": "tc-1", "name": "poc_add", "args": {}}])
        )

        events = mapper.process_chunk(make_updates_tool_error("tc-1", "API timeout"))
        assert ToolError(tool_call_id="tc-1", error="API timeout") in events


class TestToolProgressCustomChunk:
    """custom chunk → ToolProgress when tool_call_id is pending."""

    def test_progress_for_pending_tool(self):
        mapper = StreamEventMapper(session_id=SESSION_ID)

        mapper.process_chunk(make_messages_chunk_text("x", msg_id="msg-1"))
        mapper.process_chunk(make_messages_chunk_tool_call("tc-1", "poc_add"))

        events = mapper.process_chunk(make_custom_chunk("tc-1"))
        assert len(events) == 1
        assert isinstance(events[0], ToolProgress)
        assert events[0].tool_call_id == "tc-1"

    def test_progress_ignored_for_unknown_tool(self):
        mapper = StreamEventMapper(session_id=SESSION_ID)
        events = mapper.process_chunk(make_custom_chunk("tc-unknown"))
        assert events == []


class TestMultipleTextBlocks:
    """text → tool → text produces two TextStart/TextEnd pairs."""

    def test_two_text_blocks(self):
        mapper = StreamEventMapper(session_id=SESSION_ID)

        mapper.process_chunk(make_messages_chunk_text("block1", msg_id="msg-1"))
        mapper.process_chunk(make_messages_chunk_tool_call("tc-1", "poc_add"))
        mapper.process_chunk(
            make_updates_agent([{"id": "tc-1", "name": "poc_add", "args": {}}])
        )
        mapper.process_chunk(make_updates_tool_result("tc-1", "ok"))

        # Second text block
        events = mapper.process_chunk(make_messages_chunk_text("block2"))
        assert TextStart(text_id="text-1") in events
        assert TextDelta(text_id="text-1", delta="block2") in events

        all_events = mapper.finalize()
        assert TextEnd(text_id="text-1") in all_events


class TestMessageStartEmittedOnce:
    """MessageStart should only appear on the first messages chunk."""

    def test_message_start_once(self):
        mapper = StreamEventMapper(session_id=SESSION_ID)

        events1 = mapper.process_chunk(make_messages_chunk_text("a", msg_id="msg-1"))
        events2 = mapper.process_chunk(make_messages_chunk_text("b"))

        message_starts = [e for e in events1 + events2 if isinstance(e, MessageStart)]
        assert len(message_starts) == 1


class TestTextBlockAutoCloseOnToolCall:
    """An open text block is closed when a tool call chunk arrives."""

    def test_auto_close(self):
        mapper = StreamEventMapper(session_id=SESSION_ID)

        mapper.process_chunk(make_messages_chunk_text("thinking", msg_id="msg-1"))
        events = mapper.process_chunk(make_messages_chunk_tool_call("tc-1", "fn"))

        assert TextEnd(text_id="text-0") in events
        assert not any(isinstance(e, ToolCall) for e in events)


class TestFinalizeClosesOpenTextBlock:
    """finalize() must emit TextEnd if a text block is still open."""

    def test_finalize_closes_text(self):
        mapper = StreamEventMapper(session_id=SESSION_ID)
        mapper.process_chunk(make_messages_chunk_text("open", msg_id="msg-1"))

        events = mapper.finalize()
        assert TextEnd(text_id="text-0") in events
        assert any(isinstance(e, Finish) for e in events)

    def test_finalize_without_open_text(self):
        mapper = StreamEventMapper(session_id=SESSION_ID)
        mapper.process_chunk(make_messages_chunk_text("done", msg_id="msg-1"))
        mapper.process_chunk(make_messages_chunk_tool_call("tc-1", "fn"))
        # text block already closed by tool call

        events = mapper.finalize()
        text_ends = [e for e in events if isinstance(e, TextEnd)]
        assert len(text_ends) == 0


class TestUsageAccumulation:
    """usage_metadata from multiple chunks should accumulate."""

    def test_usage_summed_in_finish(self):
        mapper = StreamEventMapper(session_id=SESSION_ID)

        mapper.process_chunk(make_messages_chunk_text("hi", msg_id="msg-1"))
        mapper.process_chunk(make_messages_chunk_usage(10, 20))
        mapper.process_chunk(make_messages_chunk_usage(5, 15))

        events = mapper.finalize()
        finish = next(e for e in events if isinstance(e, Finish))
        assert finish.usage == Usage(input_tokens=15, output_tokens=35)
