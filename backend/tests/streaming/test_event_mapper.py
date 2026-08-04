"""Tests for StreamEventMapper — LangGraph v2 chunk → domain event translation."""

from langchain_core.messages import AIMessage, AIMessageChunk, ToolMessage

from backend.agent_engine.streaming.domain_events_schema import (
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
        events = mapper.process_chunk(
            make_messages_chunk_text("Let me check", msg_id="msg-1")
        )
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
            make_updates_agent(
                [{"id": "tc-1", "name": "poc_add", "args": {"a": 1, "b": 2}}]
            )
        )
        assert (
            ToolCall(tool_call_id="tc-1", tool_name="poc_add", args={"a": 1, "b": 2})
            in events
        )

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


def make_messages_chunk_multi_reasoning(
    texts: list[str],
    msg_id: str = "msg-1",
) -> dict:
    msg = AIMessageChunk(
        content=[{"type": "reasoning", "reasoning": t} for t in texts],
        id=msg_id,
    )
    return {"type": "messages", "data": (msg, {"langgraph_node": "agent"})}


class TestReasoningNativeParts:
    """F5: one provider reasoning block = one native part (start/delta*/end)."""

    def test_single_reasoning_chunk_opens_part_and_streams_delta(self):
        mapper = StreamEventMapper(session_id=SESSION_ID)

        events = mapper.process_chunk(
            make_messages_chunk_reasoning("理解問題。", msg_id="msg-A")
        )

        assert events == [
            MessageStart(message_id="msg-A", session_id=SESSION_ID),
            ReasoningStart(reasoning_id="reasoning-0"),
            ReasoningDelta(reasoning_id="reasoning-0", delta="理解問題。"),
        ]

    def test_raw_passthrough_no_buffering(self):
        """S-parts-02: mid-word fragments and `\\n\\n` pass through verbatim,
        one ReasoningDelta per provider delta — no sentence buffering."""
        mapper = StreamEventMapper(session_id=SESSION_ID)

        mapper.process_chunk(make_messages_chunk_reasoning("10-K li", msg_id="msg-A"))
        events = mapper.process_chunk(
            make_messages_chunk_reasoning("sts\n\nrisks", msg_id="msg-A")
        )

        deltas = [e for e in events if isinstance(e, ReasoningDelta)]
        assert deltas == [
            ReasoningDelta(reasoning_id="reasoning-0", delta="sts\n\nrisks")
        ]

    def test_empty_delta_not_emitted(self):
        """A zero-length reasoning block opens the part but emits no delta —
        the frontend suppresses zero-delta chips (S-chip-08)."""
        mapper = StreamEventMapper(session_id=SESSION_ID)

        events = mapper.process_chunk(make_messages_chunk_reasoning("", msg_id="msg-A"))

        assert ReasoningStart(reasoning_id="reasoning-0") in events
        assert not [e for e in events if isinstance(e, ReasoningDelta)]


class TestReasoningPartBoundaries:
    """Part closes when the provider moves on: text, new LLM call, or
    finalize — NOT a same-round tool-call chunk (S-chip-06 overlap)."""

    def test_text_block_closes_open_reasoning_part(self):
        mapper = StreamEventMapper(session_id=SESSION_ID)

        events = mapper.process_chunk(
            make_messages_chunk_reasoning_then_text(
                reasoning="分析中",
                text="answer",
                msg_id="msg-A",
            )
        )

        types_in_order = [type(e).__name__ for e in events]
        assert types_in_order == [
            "MessageStart",
            "ReasoningStart",
            "ReasoningDelta",
            "ReasoningEnd",
            "TextStart",
            "TextDelta",
        ]

    def test_tool_call_chunk_closes_open_reasoning_part(self):
        """DEV-109 ruling (2026-08-04, supersedes DEV-106 §B keep-open): a

        tool-call-chunk arriving mid-round means the round's reasoning block
        is over — the mapper closes the open reasoning part so the chip
        collapses at tool-start. Arrival order is preserved (the tool card
        renders below the now-collapsed chip).
        """
        mapper = StreamEventMapper(session_id=SESSION_ID)
        mapper.process_chunk(
            make_messages_chunk_reasoning("partial-thought", msg_id="msg-A")
        )

        events = mapper.process_chunk(
            make_messages_chunk_tool_call("tc-1", "poc_add", msg_id="msg-A")
        )

        assert events == [ReasoningEnd(reasoning_id="reasoning-0")]

    def test_legacy_tool_call_chunks_attr_also_closes_open_reasoning_part(self):
        """DEV-109 round-5 regression: Gemini delivers tool calls ONLY via
        the legacy ``tool_call_chunks`` attribute (its content_blocks never
        surface a tool_call_chunk block), so the close-on-tool-start rule
        must fire on the backup route too — exactly once."""
        mapper = StreamEventMapper(session_id=SESSION_ID)
        mapper.process_chunk(
            make_messages_chunk_reasoning("gemini thought", msg_id="msg-A")
        )

        msg = AIMessageChunk(
            content=[],
            id="msg-A",
            tool_call_chunks=[{"id": "tc-g", "name": "poc_add", "args": "{}"}],
        )
        events = mapper.process_chunk(
            {"type": "messages", "data": (msg, {"langgraph_node": "agent"})}
        )

        assert events == [ReasoningEnd(reasoning_id="reasoning-0")]

    def test_new_llm_call_closes_part_and_opens_new_id(self):
        """S-parts-01: multi-round loop → one part per round, ids turn-unique."""
        mapper = StreamEventMapper(session_id=SESSION_ID)

        mapper.process_chunk(make_messages_chunk_reasoning("round-1", msg_id="msg-A"))
        events = mapper.process_chunk(
            make_messages_chunk_reasoning("round-2", msg_id="msg-B")
        )

        assert events == [
            ReasoningEnd(reasoning_id="reasoning-0"),
            ReasoningStart(reasoning_id="reasoning-1"),
            ReasoningDelta(reasoning_id="reasoning-1", delta="round-2"),
        ]

    def test_tool_call_chunk_then_new_llm_call_closes_part_exactly_once(self):
        """The tool-call-chunk closes the round's reasoning part (DEV-109

        ruling); the next round's LLM-call-id transition must NOT emit a
        second ReasoningEnd for the already-closed part — close exactly
        once, at tool-start.
        """
        mapper = StreamEventMapper(session_id=SESSION_ID)

        mapper.process_chunk(
            make_messages_chunk_reasoning("round-1 thought", msg_id="msg-A")
        )
        tool_chunk_events = mapper.process_chunk(
            make_messages_chunk_tool_call("tc-1", "poc_add", msg_id="msg-A")
        )
        assert tool_chunk_events == [ReasoningEnd(reasoning_id="reasoning-0")]

        next_round_events = mapper.process_chunk(
            make_messages_chunk_reasoning("round-2 thought", msg_id="msg-B")
        )

        assert next_round_events == [
            ReasoningStart(reasoning_id="reasoning-1"),
            ReasoningDelta(reasoning_id="reasoning-1", delta="round-2 thought"),
        ]

    def test_same_id_continuation_keeps_part_open(self):
        mapper = StreamEventMapper(session_id=SESSION_ID)

        mapper.process_chunk(make_messages_chunk_reasoning("step 1", msg_id="msg-A"))
        events = mapper.process_chunk(
            make_messages_chunk_reasoning(" continues", msg_id="msg-A")
        )

        assert events == [
            ReasoningDelta(reasoning_id="reasoning-0", delta=" continues")
        ]

    def test_none_id_treated_as_continuation(self):
        mapper = StreamEventMapper(session_id=SESSION_ID)

        mapper.process_chunk(make_messages_chunk_reasoning("partial", msg_id="msg-A"))
        events = mapper.process_chunk(
            make_messages_chunk_reasoning(" more", msg_id=None)
        )

        assert events == [ReasoningDelta(reasoning_id="reasoning-0", delta=" more")]

    def test_consecutive_reasoning_blocks_in_one_chunk_become_separate_parts(self):
        """D12 removal: multi-summary explode → one part per provider block,
        no `\\n` join."""
        mapper = StreamEventMapper(session_id=SESSION_ID)

        events = mapper.process_chunk(
            make_messages_chunk_multi_reasoning(
                ["Summary one.", "Summary two."], msg_id="msg-A"
            )
        )

        assert events == [
            MessageStart(message_id="msg-A", session_id=SESSION_ID),
            ReasoningStart(reasoning_id="reasoning-0"),
            ReasoningDelta(reasoning_id="reasoning-0", delta="Summary one."),
            ReasoningEnd(reasoning_id="reasoning-0"),
            ReasoningStart(reasoning_id="reasoning-1"),
            ReasoningDelta(reasoning_id="reasoning-1", delta="Summary two."),
        ]

    def test_reasoning_after_text_same_call_opens_new_part(self):
        """Anthropic interleave: reasoning → text → reasoning within one LLM
        call yields two distinct parts (turn-unique ids)."""
        mapper = StreamEventMapper(session_id=SESSION_ID)

        events = []
        events += mapper.process_chunk(
            make_messages_chunk_reasoning("step A", msg_id="msg-A")
        )
        events += mapper.process_chunk(make_messages_chunk_text("t1", msg_id="msg-A"))
        events += mapper.process_chunk(
            make_messages_chunk_reasoning("step B", msg_id="msg-A")
        )

        starts = [e for e in events if isinstance(e, ReasoningStart)]
        assert [s.reasoning_id for s in starts] == ["reasoning-0", "reasoning-1"]


class TestFinalizeReasoning:
    """finalize() closes any open reasoning part before Finish."""

    def test_finalize_closes_open_reasoning_part(self):
        mapper = StreamEventMapper(session_id=SESSION_ID)

        mapper.process_chunk(
            make_messages_chunk_reasoning("no terminator here", msg_id="msg-A")
        )
        events = mapper.finalize()

        types_in_order = [type(e).__name__ for e in events]
        assert types_in_order == ["ReasoningEnd", "Finish"]

    def test_finalize_no_open_part_emits_only_finish(self):
        mapper = StreamEventMapper(session_id=SESSION_ID)
        mapper.process_chunk(make_messages_chunk_text("done.", msg_id="msg-A"))
        mapper.process_chunk(
            make_messages_chunk_tool_call("tc-1", "fn", msg_id="msg-A")
        )

        events = mapper.finalize()

        # Text block already closed by tool call; no open reasoning part;
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
