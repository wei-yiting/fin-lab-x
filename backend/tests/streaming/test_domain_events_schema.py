"""Tests for domain event value objects.

These are frozen dataclasses; we deliberately do NOT re-test stdlib-generated
behavior (per-field construction / __eq__ for every type). We keep only:
- one representative ``frozen=True`` guard,
- one representative structural-equality guard,
- the defaults WE chose (Usage zero-init, Finish's zero-Usage factory), and
- a union-membership guard that fails if a new event type is added to the
  module but forgotten in the ``DomainEvent`` union.
"""

from typing import get_args

import pytest

from backend.agent_engine.streaming.domain_events_schema import (
    DomainEvent,
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
    Usage,
)

_ALL_EVENTS = [
    MessageStart,
    TextStart,
    TextDelta,
    TextEnd,
    ToolCall,
    ToolResult,
    ToolError,
    ToolProgress,
    ReasoningStatus,
    StreamError,
    Finish,
]


def test_events_are_frozen():
    """Representative guard that domain events are frozen=True (applied
    uniformly by the dataclass decorator) — mutation must raise."""
    evt = TextDelta(text_id="t1", delta="hello")
    with pytest.raises(AttributeError):
        evt.delta = "world"  # type: ignore[misc]


def test_events_support_structural_equality():
    """Representative guard that events are value objects (structural __eq__)."""
    assert TextDelta(text_id="t1", delta="hi") == TextDelta(text_id="t1", delta="hi")
    assert TextDelta(text_id="t1", delta="hi") != TextDelta(text_id="t1", delta="bye")
    # Different types sharing a field value never compare equal.
    assert TextStart(text_id="t1") != TextEnd(text_id="t1")


def test_usage_defaults_to_zero():
    """Our chosen default: an omitted Usage is zero in/out tokens."""
    u = Usage()
    assert (u.input_tokens, u.output_tokens) == (0, 0)


def test_finish_defaults_to_zero_usage():
    """Our chosen default_factory: Finish without usage carries a zero Usage."""
    f = Finish(finish_reason="stop")
    assert f.usage == Usage(input_tokens=0, output_tokens=0)


def test_every_event_type_is_in_domain_event_union():
    """Guard against adding a new event class but forgetting to register it in
    the DomainEvent union (which would silently break exhaustive handling)."""
    union_members = set(get_args(DomainEvent))
    for event_cls in _ALL_EVENTS:
        assert event_cls in union_members, (
            f"{event_cls.__name__} is missing from the DomainEvent union"
        )
