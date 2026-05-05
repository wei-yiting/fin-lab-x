"""Tests for StreamEventMapper — LangGraph v2 chunk → domain event translation."""

from langchain_core.messages import AIMessage, AIMessageChunk, ToolMessage

from backend.agent_engine.streaming.domain_events_schema import (
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


def make_messages_chunk_reasoning(text: str, msg_id: str = "msg-1") -> dict:
    msg = AIMessageChunk(
        content=[{"type": "reasoning", "reasoning": text}],
        id=msg_id,
    )
    return {"type": "messages", "data": (msg, {"langgraph_node": "agent"})}


def make_messages_chunk_reasoning_then_text(
    reasoning: str,
    text: str,
    msg_id: str = "msg-1",
) -> dict:
    msg = AIMessageChunk(
        content=[
            {"type": "reasoning", "reasoning": reasoning},
            {"type": "text", "text": text},
        ],
        id=msg_id,
    )
    return {"type": "messages", "data": (msg, {"langgraph_node": "agent"})}


class TestReasoningHappyPath:
    """A reasoning block with a terminator emits ReasoningStatus immediately."""

    def test_single_reasoning_sentence(self):
        mapper = StreamEventMapper(session_id=SESSION_ID)

        events = mapper.process_chunk(
            make_messages_chunk_reasoning("理解問題。", msg_id="msg-A")
        )

        assert events == [
            MessageStart(message_id="msg-A", session_id=SESSION_ID),
            ReasoningStatus(reasoning_id="reasoning-0", text="理解問題。"),
        ]


class TestReasoningHoldAndFlushOrdering:
    """D28: reasoning sentences must emit BEFORE TextStart in the same chunk."""

    def test_reasoning_then_text_in_same_chunk(self):
        mapper = StreamEventMapper(session_id=SESSION_ID)

        events = mapper.process_chunk(
            make_messages_chunk_reasoning_then_text(
                reasoning="分析中。",
                text="answer",
                msg_id="msg-A",
            )
        )

        types_in_order = [type(e).__name__ for e in events]
        assert types_in_order == [
            "MessageStart",
            "ReasoningStatus",
            "TextStart",
            "TextDelta",
        ]
        rs = next(e for e in events if isinstance(e, ReasoningStatus))
        assert rs.text == "分析中。"

    def test_reasoning_tail_flushed_before_tool_call(self):
        # Buffer a reasoning fragment with no terminator, then receive a
        # tool_call_chunk in the next chunk — the buffered fragment must
        # be flushed as ReasoningStatus before the text block closes.
        mapper = StreamEventMapper(session_id=SESSION_ID)
        mapper.process_chunk(make_messages_chunk_reasoning("partial-thought", msg_id="msg-A"))

        events = mapper.process_chunk(
            make_messages_chunk_tool_call("tc-1", "poc_add", msg_id="msg-A")
        )

        rs_events = [e for e in events if isinstance(e, ReasoningStatus)]
        assert len(rs_events) == 1
        assert rs_events[0].text == "partial-thought"


class TestChunkIdBoundary:
    """D27.1: chunk.id transitions trigger segmenter flush + reset."""

    def test_same_id_continuation_no_flush(self):
        mapper = StreamEventMapper(session_id=SESSION_ID)

        # Buffer "step 1" (no terminator) under msg-A
        mapper.process_chunk(make_messages_chunk_reasoning("step 1", msg_id="msg-A"))
        # Same chunk.id arrives — must NOT trigger flush
        events = mapper.process_chunk(make_messages_chunk_reasoning(" continues", msg_id="msg-A"))

        rs_events = [e for e in events if isinstance(e, ReasoningStatus)]
        assert rs_events == []

    def test_none_id_treated_as_continuation(self):
        mapper = StreamEventMapper(session_id=SESSION_ID)

        mapper.process_chunk(make_messages_chunk_reasoning("partial", msg_id="msg-A"))
        # id=None is continuation per D27.1, no boundary flush
        events = mapper.process_chunk(make_messages_chunk_reasoning(" more", msg_id=None))

        rs_events = [e for e in events if isinstance(e, ReasoningStatus)]
        assert rs_events == []

    def test_different_id_triggers_flush_and_new_reasoning_id(self):
        mapper = StreamEventMapper(session_id=SESSION_ID)

        # Buffer "tail-A" with no terminator under msg-A
        mapper.process_chunk(make_messages_chunk_reasoning("tail-A", msg_id="msg-A"))
        # New chunk.id msg-B → boundary: flush buffered tail. The new reasoning
        # ends with `\n` (immediate terminator) so it emits in the same call.
        events = mapper.process_chunk(make_messages_chunk_reasoning("new B.\n", msg_id="msg-B"))

        rs_events = [e for e in events if isinstance(e, ReasoningStatus)]
        assert len(rs_events) == 2
        # First emit is the flushed tail under the OLD reasoning_id
        assert rs_events[0].text == "tail-A"
        assert rs_events[0].reasoning_id == "reasoning-0"
        # Second emit is the new sentence under the NEW reasoning_id
        assert rs_events[1].text == "new B."
        assert rs_events[1].reasoning_id == "reasoning-1"


class TestReasoningIdLifecycle:
    """D27.2: same chunk.id → same reasoning_id; new chunk.id → new reasoning_id."""

    def test_three_reasoning_blocks_same_call_share_id(self):
        mapper = StreamEventMapper(session_id=SESSION_ID)

        events = []
        events += mapper.process_chunk(make_messages_chunk_reasoning("first.\n", msg_id="msg-A"))
        events += mapper.process_chunk(make_messages_chunk_reasoning("second.\n", msg_id="msg-A"))
        events += mapper.process_chunk(make_messages_chunk_reasoning("third.\n", msg_id="msg-A"))

        rs_events = [e for e in events if isinstance(e, ReasoningStatus)]
        assert len(rs_events) == 3
        ids = {e.reasoning_id for e in rs_events}
        assert ids == {"reasoning-0"}

    def test_new_llm_call_gets_new_reasoning_id(self):
        mapper = StreamEventMapper(session_id=SESSION_ID)

        events_a = mapper.process_chunk(
            make_messages_chunk_reasoning("call-A.\n", msg_id="msg-A")
        )
        events_b = mapper.process_chunk(
            make_messages_chunk_reasoning("call-B.\n", msg_id="msg-B")
        )

        rs_a = [e for e in events_a if isinstance(e, ReasoningStatus)]
        rs_b = [e for e in events_b if isinstance(e, ReasoningStatus)]
        assert rs_a[0].reasoning_id == "reasoning-0"
        assert rs_b[0].reasoning_id == "reasoning-1"


class TestFinalizeReasoningTail:
    """D34: finalize() emits any buffered segmenter tail before Finish."""

    def test_finalize_flushes_reasoning_tail(self):
        mapper = StreamEventMapper(session_id=SESSION_ID)

        mapper.process_chunk(
            make_messages_chunk_reasoning("no terminator here", msg_id="msg-A")
        )
        events = mapper.finalize()

        types_in_order = [type(e).__name__ for e in events]
        # Tail flushed first, then Finish (no TextEnd because no text block opened)
        assert types_in_order == ["ReasoningStatus", "Finish"]
        rs = next(e for e in events if isinstance(e, ReasoningStatus))
        assert rs.text == "no terminator here"

    def test_finalize_no_segmenter_content_emits_only_finish(self):
        mapper = StreamEventMapper(session_id=SESSION_ID)
        mapper.process_chunk(make_messages_chunk_text("done.", msg_id="msg-A"))
        mapper.process_chunk(make_messages_chunk_tool_call("tc-1", "fn", msg_id="msg-A"))

        events = mapper.finalize()

        # Text block already closed by tool call; no buffered reasoning;
        # only Finish should remain.
        assert len(events) == 1
        assert isinstance(events[0], Finish)

    def test_finalize_called_twice_emits_only_one_finish(self):
        mapper = StreamEventMapper(session_id=SESSION_ID)
        mapper.process_chunk(make_messages_chunk_text("hi", msg_id="msg-A"))

        first = mapper.finalize()
        second = mapper.finalize()

        assert any(isinstance(e, Finish) for e in first)
        assert second == []
