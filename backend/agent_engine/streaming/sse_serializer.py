"""SSE Serializer — converts domain events to AI SDK UIMessage Stream Protocol v1 wire format.

Uses functools.singledispatch so each event type registers independently.
Wire format: ``data: {json}\n\n``
"""

from __future__ import annotations

import functools
import json

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
)


def _sse(payload: dict) -> str:
    return f"data: {json.dumps(payload)}\n\n"


@functools.singledispatch
def serialize_event(event) -> str:
    raise TypeError(f"Unhandled event type: {type(event).__name__}")


@serialize_event.register
def _(event: MessageStart) -> str:
    return _sse({
        "type": "start",
        "messageId": event.message_id,
        "messageMetadata": {"sessionId": event.session_id},
    })


@serialize_event.register
def _(event: TextStart) -> str:
    return _sse({"type": "text-start", "id": event.text_id})


@serialize_event.register
def _(event: TextDelta) -> str:
    return _sse({"type": "text-delta", "id": event.text_id, "delta": event.delta})


@serialize_event.register
def _(event: TextEnd) -> str:
    return _sse({"type": "text-end", "id": event.text_id})


@serialize_event.register
def _(event: ToolCall) -> str:
    return _sse({
        "type": "tool-input-available",
        "toolCallId": event.tool_call_id,
        "toolName": event.tool_name,
        "input": event.args,
    })


@serialize_event.register
def _(event: ToolResult) -> str:
    return _sse({
        "type": "tool-output-available",
        "toolCallId": event.tool_call_id,
        "output": event.result,
    })


@serialize_event.register
def _(event: ToolError) -> str:
    return _sse({
        "type": "tool-output-error",
        "toolCallId": event.tool_call_id,
        "errorText": event.error,
    })


@serialize_event.register
def _(event: ToolProgress) -> str:
    return _sse({
        "type": "data-tool-progress",
        "id": event.tool_call_id,
        "data": event.data,
        "transient": True,
    })


@serialize_event.register
def _(event: StreamError) -> str:
    return _sse({"type": "error", "errorText": event.error_text})


@serialize_event.register
def _(event: Finish) -> str:
    return _sse({
        "type": "finish",
        "finishReason": event.finish_reason,
        "messageMetadata": {
            "usage": {
                "totalTokens": event.usage.input_tokens + event.usage.output_tokens,
            },
        },
    })
