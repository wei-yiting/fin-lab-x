"""Domain event value objects — shared contract between StreamEventMapper and SSE Serializer.

All events are frozen dataclasses (immutable value objects) with structural equality.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class MessageStart:
    message_id: str
    session_id: str


@dataclass(frozen=True)
class TextStart:
    text_id: str


@dataclass(frozen=True)
class TextDelta:
    text_id: str
    delta: str


@dataclass(frozen=True)
class TextEnd:
    text_id: str


@dataclass(frozen=True)
class ToolCall:
    tool_call_id: str
    tool_name: str
    args: dict


@dataclass(frozen=True)
class ToolResult:
    tool_call_id: str
    result: str


@dataclass(frozen=True)
class ToolError:
    tool_call_id: str
    error: str


@dataclass(frozen=True)
class ToolProgress:
    tool_call_id: str
    data: dict


@dataclass(frozen=True)
class StreamError:
    error_text: str


@dataclass(frozen=True)
class Usage:
    input_tokens: int = 0
    output_tokens: int = 0


@dataclass(frozen=True)
class Finish:
    finish_reason: str
    usage: Usage = field(default_factory=Usage)


DomainEvent = (
    MessageStart
    | TextStart
    | TextDelta
    | TextEnd
    | ToolCall
    | ToolResult
    | ToolError
    | ToolProgress
    | StreamError
    | Finish
)
