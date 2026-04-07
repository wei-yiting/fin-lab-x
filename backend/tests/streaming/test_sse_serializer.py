"""Tests for SSE serializer — singledispatch conversion of domain events to wire format."""

import json

import pytest

from backend.agent_engine.streaming.domain_events_schema import (
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
from backend.agent_engine.streaming.sse_serializer import serialize_event


def _parse_sse(raw: str) -> dict:
    """Strip SSE framing and parse the JSON payload."""
    assert raw.startswith("data: "), f"Missing 'data: ' prefix: {raw!r}"
    assert raw.endswith("\n\n"), f"Missing trailing double newline: {raw!r}"
    return json.loads(raw.removeprefix("data: ").removesuffix("\n\n"))


class TestMessageStart:
    def test_wire_format(self):
        evt = MessageStart(message_id="msg-1", session_id="sess-1")
        payload = _parse_sse(serialize_event(evt))
        assert payload == {
            "type": "start",
            "messageId": "msg-1",
            "messageMetadata": {"sessionId": "sess-1"},
        }


class TestTextStart:
    def test_wire_format(self):
        evt = TextStart(text_id="txt-1")
        payload = _parse_sse(serialize_event(evt))
        assert payload == {"type": "text-start", "id": "txt-1"}


class TestTextDelta:
    def test_wire_format(self):
        evt = TextDelta(text_id="txt-1", delta="hello")
        payload = _parse_sse(serialize_event(evt))
        assert payload == {"type": "text-delta", "id": "txt-1", "delta": "hello"}


class TestTextEnd:
    def test_wire_format(self):
        evt = TextEnd(text_id="txt-1")
        payload = _parse_sse(serialize_event(evt))
        assert payload == {"type": "text-end", "id": "txt-1"}


class TestToolCall:
    def test_wire_format(self):
        evt = ToolCall(tool_call_id="tc-1", tool_name="yfinance", args={"ticker": "AAPL"})
        payload = _parse_sse(serialize_event(evt))
        assert payload == {
            "type": "tool-input-available",
            "toolCallId": "tc-1",
            "toolName": "yfinance",
            "input": {"ticker": "AAPL"},
        }

    def test_empty_args(self):
        evt = ToolCall(tool_call_id="tc-1", tool_name="fn", args={})
        payload = _parse_sse(serialize_event(evt))
        assert payload["input"] == {}


class TestToolResult:
    def test_wire_format(self):
        evt = ToolResult(tool_call_id="tc-1", result="price=150.0")
        payload = _parse_sse(serialize_event(evt))
        assert payload == {
            "type": "tool-output-available",
            "toolCallId": "tc-1",
            "output": "price=150.0",
        }


class TestToolError:
    def test_wire_type_is_tool_output_error(self):
        evt = ToolError(tool_call_id="tc-1", error="timeout")
        payload = _parse_sse(serialize_event(evt))
        assert payload["type"] == "tool-output-error"

    def test_wire_format(self):
        evt = ToolError(tool_call_id="tc-1", error="timeout")
        payload = _parse_sse(serialize_event(evt))
        assert payload == {
            "type": "tool-output-error",
            "toolCallId": "tc-1",
            "errorText": "timeout",
        }


class TestToolProgress:
    def test_wire_format(self):
        evt = ToolProgress(tool_call_id="tc-1", data={"step": 1})
        payload = _parse_sse(serialize_event(evt))
        assert payload == {
            "type": "data-tool-progress",
            "id": "tc-1",
            "data": {"step": 1},
            "transient": True,
        }

    def test_transient_is_true(self):
        evt = ToolProgress(tool_call_id="tc-1", data={})
        payload = _parse_sse(serialize_event(evt))
        assert payload["transient"] is True


class TestStreamError:
    def test_wire_format(self):
        evt = StreamError(error_text="connection lost")
        payload = _parse_sse(serialize_event(evt))
        assert payload == {"type": "error", "errorText": "connection lost"}


class TestFinish:
    def test_wire_format_with_default_usage(self):
        evt = Finish(finish_reason="stop")
        payload = _parse_sse(serialize_event(evt))
        assert payload == {
            "type": "finish",
            "finishReason": "stop",
            "messageMetadata": {"usage": {"totalTokens": 0}},
        }

    def test_wire_format_with_explicit_usage(self):
        evt = Finish(finish_reason="stop", usage=Usage(input_tokens=100, output_tokens=50))
        payload = _parse_sse(serialize_event(evt))
        assert payload["messageMetadata"]["usage"] == {"totalTokens": 150}


class TestCamelCaseKeys:
    """All wire-format keys must be camelCase, never snake_case."""

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
    def test_no_snake_case_keys(self, event):
        payload = _parse_sse(serialize_event(event))
        for key in payload:
            assert "_" not in key, f"Snake-case key found: {key}"


class TestUnknownEventType:
    def test_raises_type_error(self):
        with pytest.raises(TypeError, match="Unhandled event type"):
            serialize_event("not an event")


class TestJsonSpecialCharacters:
    def test_quotes_in_delta(self):
        evt = TextDelta(text_id="t1", delta='He said "hello"')
        raw = serialize_event(evt)
        payload = _parse_sse(raw)
        assert payload["delta"] == 'He said "hello"'

    def test_newlines_in_error(self):
        evt = StreamError(error_text="line1\nline2")
        raw = serialize_event(evt)
        payload = _parse_sse(raw)
        assert payload["errorText"] == "line1\nline2"

    def test_backslash_in_result(self):
        evt = ToolResult(tool_call_id="tc1", result="path\\to\\file")
        raw = serialize_event(evt)
        payload = _parse_sse(raw)
        assert payload["output"] == "path\\to\\file"
