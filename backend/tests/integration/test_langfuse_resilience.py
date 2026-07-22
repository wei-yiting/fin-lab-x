"""Langfuse observability resilience tests.

Covers BDD scenarios:
- S-obs-07: Langfuse outage during a stream does not stall the user
- S-obs-15: Exception in the Langfuse handler does not kill the stream
- J-obs-03: Dual-handler eval run survives Langfuse degradation (architectural
  invariant shared with S-obs-07 — verified here at the Orchestrator layer)

The architectural guarantee under test: Orchestrator.astream_run passes the
Langfuse CallbackHandler through to LangChain's callback manager but does not
`await` on it. LangChain's callback manager catches handler exceptions. The
Langfuse SDK ingests spans on a background schedule so endpoint failures surface
only as SDK-level warnings, never as user-facing errors or request latency.
"""

from contextlib import nullcontext
from typing import Any, cast
from unittest.mock import patch, MagicMock

import pytest
from langchain_core.messages import AIMessageChunk

from backend.agent_engine.streaming.domain_events_schema import (
    Finish,
    MessageStart,
    TextDelta,
    TextEnd,
    TextStart,
)
from backend.agent_engine.streaming.reasoning_trace_callback import (
    ReasoningTraceCallback,
)

# Reuse orchestrator builders from the existing langfuse test module
from backend.tests.agents.test_orchestrator_langfuse import (
    _create_orchestrator,
    _make_config,
)


def _assert_complete_stream(events):
    """Every stream must open with MessageStart and close with Finish."""
    assert events, "stream yielded no events"
    assert isinstance(events[0], MessageStart), f"first event was {type(events[0]).__name__}"
    assert isinstance(events[-1], Finish), f"last event was {type(events[-1]).__name__}"


async def _drain(astream_gen):
    return [event async for event in astream_gen]


class BrokenHandler:
    """Handler whose every callback method raises — simulates SDK bugs or
    corrupt handler state. LangChain's callback manager catches these."""

    def __getattr__(self, name):
        def _raise(*args, **kwargs):
            raise RuntimeError(f"simulated handler failure in {name}")

        return _raise


@pytest.mark.asyncio
class TestLangfuseHandlerExceptionIsolation:
    """S-obs-15: handler failure must not cascade into the stream."""

    async def test_broken_handler_does_not_prevent_domain_events(self):
        config = _make_config()
        orch = _create_orchestrator(config)
        agent = cast(Any, orch.agent)

        async def mock_astream(*args, **kwargs):
            yield {
                "type": "messages",
                "data": (
                    AIMessageChunk(content="Hi", id="m-1"),
                    {"langgraph_node": "agent"},
                ),
            }
            yield {
                "type": "messages",
                "data": (
                    AIMessageChunk(content=" there", id="m-1"),
                    {"langgraph_node": "agent"},
                ),
            }

        agent.astream = mock_astream

        with (
            patch(
                "backend.agent_engine.agents.base.CallbackHandler",
                return_value=BrokenHandler(),
            ),
            patch(
                "backend.agent_engine.agents.base.propagate_attributes",
                return_value=nullcontext(),
            ),
        ):
            events = await _drain(orch.astream_run(message="hi", session_id="s-h1"))

        _assert_complete_stream(events)
        text_deltas = [e for e in events if isinstance(e, TextDelta)]
        assert [d.delta for d in text_deltas] == ["Hi", " there"]
        assert any(isinstance(e, TextStart) for e in events)
        assert any(isinstance(e, TextEnd) for e in events)


@pytest.mark.asyncio
class TestLangfuseEndpointOutageResilience:
    """S-obs-07 / J-obs-03: unreachable Langfuse endpoint is silent.

    The Langfuse SDK flushes spans asynchronously; the handler's observable
    side effect during a request is only its LangChain callback methods.
    Simulating endpoint failure is equivalent to simulating handler-method
    failure (covered above) plus verifying the handler is instantiated
    and attached to the config regardless.
    """

    async def test_handler_still_attached_when_flush_raises(self):
        """Even if the handler's flush raises, it is still instantiated and
        passed to the agent config — so spans are captured, only the ingest
        fails silently (SDK design)."""
        config = _make_config()
        orch = _create_orchestrator(config)
        agent = cast(Any, orch.agent)

        captured_kwargs: dict = {}

        async def mock_astream(*args, **kwargs):
            captured_kwargs.update(kwargs)
            yield {
                "type": "messages",
                "data": (
                    AIMessageChunk(content="ok", id="m-1"),
                    {"langgraph_node": "agent"},
                ),
            }

        agent.astream = mock_astream

        flushing_handler = MagicMock()
        flushing_handler.flush.side_effect = RuntimeError("Langfuse unreachable")

        with (
            patch(
                "backend.agent_engine.agents.base.CallbackHandler",
                return_value=flushing_handler,
            ),
            patch(
                "backend.agent_engine.agents.base.propagate_attributes",
                return_value=nullcontext(),
            ),
        ):
            events = await _drain(orch.astream_run(message="hi", session_id="s-o1"))

        _assert_complete_stream(events)
        callbacks = captured_kwargs.get("config", {}).get("callbacks", [])
        assert flushing_handler in callbacks, (
            "handler must be attached to config so spans are captured even when "
            "endpoint ingestion fails"
        )


@pytest.mark.asyncio
class TestDualHandlerResilience:
    """J-obs-03: a broken Langfuse handler must not gate out the sibling
    callback the Orchestrator wires alongside it (the ReasoningTraceCallback —
    same coexistence shape an eval-time Braintrust handler would have)."""

    async def test_real_config_keeps_sibling_callback_when_langfuse_handler_broken(
        self,
    ):
        """Drive the REAL ``_build_langfuse_config`` (not a patched stand-in):
        when the Langfuse handler class produces a broken handler, the actual
        callbacks list the Orchestrator hands to ``astream`` must still contain
        BOTH the broken handler AND the sibling ReasoningTraceCallback, and the
        stream must complete with full domain events. The earlier version of
        this test patched the builder and asserted a call its own mock made —
        it passed even if the real dual-handler wiring were broken. This drives
        the real wiring instead, so dropping a callback on handler trouble fails
        the test."""
        config = _make_config()
        orch = _create_orchestrator(config)
        agent = cast(Any, orch.agent)

        captured_kwargs: dict = {}

        async def mock_astream(*args, **kwargs):
            captured_kwargs.update(kwargs)
            yield {
                "type": "messages",
                "data": (
                    AIMessageChunk(content="done", id="m-1"),
                    {"langgraph_node": "agent"},
                ),
            }

        agent.astream = mock_astream

        broken = BrokenHandler()
        with (
            patch(
                "backend.agent_engine.agents.base.CallbackHandler",
                return_value=broken,
            ),
            patch(
                "backend.agent_engine.agents.base.propagate_attributes",
                return_value=nullcontext(),
            ),
        ):
            events = await _drain(orch.astream_run(message="hi", session_id="s-d1"))

        _assert_complete_stream(events)
        callbacks = captured_kwargs.get("config", {}).get("callbacks", [])
        # The broken Langfuse handler is present in the real callbacks list...
        assert broken in callbacks, "Langfuse handler must still be attached"
        # ...and it did NOT gate out the sibling reasoning callback.
        assert any(isinstance(c, ReasoningTraceCallback) for c in callbacks), (
            "dual-handler invariant: a broken Langfuse handler must not remove "
            "the sibling ReasoningTraceCallback from the dispatched callbacks"
        )
