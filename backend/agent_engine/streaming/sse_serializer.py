"""SSE Serializer — converts domain events to AI SDK UIMessage Stream Protocol v1 wire format.

Uses functools.singledispatch so each event type registers independently.
Wire format: ``data: {json}\n\n``
"""

from __future__ import annotations

import functools
import json
import logging
import os

from backend.agent_engine.streaming.domain_events_schema import (
    Finish,
    MessageStart,
    ReasoningStatus,
    StreamError,
    TextDelta,
    TextEnd,
    TextStart,
    ToolCall,
    ToolError,
    ToolProgress,
    ToolResult,
)

logger = logging.getLogger(__name__)


def _sse(payload: dict) -> str:
    return f"data: {json.dumps(payload)}\n\n"


# D39.c: reasoning events must always carry transient=True. ToolProgress predates this contract and is intentionally not guarded.
def _assert_reasoning_transient(payload: dict) -> None:
    if not (
        payload.get("type", "").startswith("data-reasoning-")
        and payload.get("transient") is True
    ):
        msg = "reasoning SSE event missing transient=True flag"
        if os.environ.get("APP_ENV", "").lower() == "production":
            logger.warning(msg, extra={"payload_type": payload.get("type")})
        else:
            raise AssertionError(msg)


@functools.singledispatch
def serialize_event(event) -> str:
    raise TypeError(f"Unhandled event type: {type(event).__name__}")


@serialize_event.register
def _(event: MessageStart) -> str:
    return _sse(
        {
            "type": "start",
            "messageId": event.message_id,
            "messageMetadata": {"sessionId": event.session_id},
        }
    )


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
    return _sse(
        {
            "type": "tool-input-available",
            "toolCallId": event.tool_call_id,
            "toolName": event.tool_name,
            "input": event.args,
        }
    )


@serialize_event.register
def _(event: ToolResult) -> str:
    return _sse(
        {
            "type": "tool-output-available",
            "toolCallId": event.tool_call_id,
            "output": event.result,
        }
    )


@serialize_event.register
def _(event: ToolError) -> str:
    return _sse(
        {
            "type": "tool-output-error",
            "toolCallId": event.tool_call_id,
            "errorText": event.error,
        }
    )


@serialize_event.register
def _(event: ToolProgress) -> str:
    return _sse(
        {
            "type": "data-tool-progress",
            "id": event.tool_call_id,
            "data": event.data,
            "transient": True,
        }
    )


@serialize_event.register
def _(event: ReasoningStatus) -> str:
    payload = {
        "type": "data-reasoning-status",
        "id": event.reasoning_id,
        "data": {"text": event.text},
        "transient": True,
    }
    # DEV-ONLY: FORCE_REASONING_NON_TRANSIENT strips the transient flag so
    # the wire emits a malformed payload. In APP_ENV=production the helper
    # downgrades to a warning, letting Playwright assert that the frontend
    # filter discards non-transient data-reasoning-status events
    # (S-chan-03). In dev/CI the helper raises so accidental flag-on
    # tests fail loudly. Production must NOT set FORCE_REASONING_NON_TRANSIENT.
    if os.environ.get("FORCE_REASONING_NON_TRANSIENT"):
        payload.pop("transient", None)
    _assert_reasoning_transient(payload)
    return _sse(payload)


@serialize_event.register
def _(event: StreamError) -> str:
    return _sse({"type": "error", "errorText": event.error_text})


@serialize_event.register
def _(event: Finish) -> str:
    return _sse(
        {
            "type": "finish",
            "finishReason": event.finish_reason,
            "messageMetadata": {
                "usage": {
                    "totalTokens": event.usage.input_tokens + event.usage.output_tokens,
                },
            },
        }
    )
