"""Tests for domain event value objects — frozen immutability, construction, equality."""

import pytest

from backend.agent_engine.streaming.domain_events_schema import (
    DomainEvent,
    Finish,
    MessageStart,
    StreamError,
    TextDelta,
    TextEnd,
    TextStart,
    ToolCall,
    ToolError,
    ToolProgress,
    ToolResult,
    Usage,
)


class TestFrozenImmutability:
    """All domain events must be frozen dataclasses — mutation raises FrozenInstanceError."""

    def test_message_start_is_frozen(self):
        evt = MessageStart(message_id="m1", session_id="s1")
        with pytest.raises(AttributeError):
            evt.message_id = "m2"  # type: ignore[misc]

    def test_text_delta_is_frozen(self):
        evt = TextDelta(text_id="t1", delta="hello")
        with pytest.raises(AttributeError):
            evt.delta = "world"  # type: ignore[misc]

    def test_tool_call_is_frozen(self):
        evt = ToolCall(tool_call_id="tc1", tool_name="yfinance", args={"ticker": "AAPL"})
        with pytest.raises(AttributeError):
            evt.tool_name = "other"  # type: ignore[misc]

    def test_usage_is_frozen(self):
        u = Usage(input_tokens=10, output_tokens=20)
        with pytest.raises(AttributeError):
            u.input_tokens = 99  # type: ignore[misc]

    def test_finish_is_frozen(self):
        f = Finish(finish_reason="stop")
        with pytest.raises(AttributeError):
            f.finish_reason = "error"  # type: ignore[misc]


class TestConstruction:
    """Verify correct field assignment for every event type."""

    def test_message_start(self):
        evt = MessageStart(message_id="m1", session_id="s1")
        assert evt.message_id == "m1"
        assert evt.session_id == "s1"

    def test_text_start(self):
        evt = TextStart(text_id="t1")
        assert evt.text_id == "t1"

    def test_text_delta(self):
        evt = TextDelta(text_id="t1", delta="chunk")
        assert evt.text_id == "t1"
        assert evt.delta == "chunk"

    def test_text_end(self):
        evt = TextEnd(text_id="t1")
        assert evt.text_id == "t1"

    def test_tool_call(self):
        evt = ToolCall(tool_call_id="tc1", tool_name="yfinance", args={"ticker": "AAPL"})
        assert evt.tool_call_id == "tc1"
        assert evt.tool_name == "yfinance"
        assert evt.args == {"ticker": "AAPL"}

    def test_tool_result(self):
        evt = ToolResult(tool_call_id="tc1", result="price=150.0")
        assert evt.tool_call_id == "tc1"
        assert evt.result == "price=150.0"

    def test_tool_error(self):
        evt = ToolError(tool_call_id="tc1", error="timeout")
        assert evt.tool_call_id == "tc1"
        assert evt.error == "timeout"

    def test_tool_progress(self):
        evt = ToolProgress(tool_call_id="tc1", data={"step": 1})
        assert evt.tool_call_id == "tc1"
        assert evt.data == {"step": 1}

    def test_stream_error(self):
        evt = StreamError(error_text="connection lost")
        assert evt.error_text == "connection lost"

    def test_usage_defaults(self):
        u = Usage()
        assert u.input_tokens == 0
        assert u.output_tokens == 0

    def test_usage_explicit(self):
        u = Usage(input_tokens=100, output_tokens=50)
        assert u.input_tokens == 100
        assert u.output_tokens == 50

    def test_finish_with_default_usage(self):
        f = Finish(finish_reason="stop")
        assert f.finish_reason == "stop"
        assert f.usage.input_tokens == 0
        assert f.usage.output_tokens == 0

    def test_finish_with_explicit_usage(self):
        u = Usage(input_tokens=10, output_tokens=20)
        f = Finish(finish_reason="stop", usage=u)
        assert f.usage is u


class TestEquality:
    """Frozen dataclasses support structural equality by default."""

    def test_same_values_are_equal(self):
        a = TextDelta(text_id="t1", delta="hi")
        b = TextDelta(text_id="t1", delta="hi")
        assert a == b

    def test_different_values_are_not_equal(self):
        a = TextDelta(text_id="t1", delta="hi")
        b = TextDelta(text_id="t1", delta="bye")
        assert a != b

    def test_different_types_are_not_equal(self):
        a = TextStart(text_id="t1")
        b = TextEnd(text_id="t1")
        assert a != b

    def test_usage_equality(self):
        assert Usage(input_tokens=1, output_tokens=2) == Usage(
            input_tokens=1, output_tokens=2
        )

    def test_finish_equality_with_usage(self):
        u = Usage(input_tokens=5, output_tokens=10)
        assert Finish(finish_reason="stop", usage=u) == Finish(
            finish_reason="stop", usage=Usage(input_tokens=5, output_tokens=10)
        )


class TestDomainEventUnion:
    """DomainEvent union type should accept all event types."""

    @pytest.mark.parametrize(
        "event",
        [
            MessageStart(message_id="m1", session_id="s1"),
            TextStart(text_id="t1"),
            TextDelta(text_id="t1", delta="x"),
            TextEnd(text_id="t1"),
            ToolCall(tool_call_id="tc1", tool_name="fn", args={}),
            ToolResult(tool_call_id="tc1", result="ok"),
            ToolError(tool_call_id="tc1", error="fail"),
            ToolProgress(tool_call_id="tc1", data={}),
            StreamError(error_text="err"),
            Finish(finish_reason="stop"),
        ],
    )
    def test_isinstance_check(self, event: DomainEvent):
        event_types = (
            MessageStart,
            TextStart,
            TextDelta,
            TextEnd,
            ToolCall,
            ToolResult,
            ToolError,
            ToolProgress,
            StreamError,
            Finish,
        )
        assert isinstance(event, event_types)
