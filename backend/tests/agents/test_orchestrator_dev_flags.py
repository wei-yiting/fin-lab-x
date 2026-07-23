"""Dev-only env flag handlers in Orchestrator.

FORCE_LLM_FAIL=1 raises in astream_run BEFORE the agent.astream call,
exercising the existing exception handler that converts the failure
into ``StreamError + Finish(error)``. Drives S-stream-04 (mid-stream
failure mid-row) by simulating a deterministic provider failure.

Production must NOT set FORCE_LLM_FAIL.
"""

from __future__ import annotations

import asyncio
from typing import Any
from unittest.mock import MagicMock, patch

from backend.agent_engine.agents.base import Orchestrator
from backend.agent_engine.agents.config_loader import (
    ModelConfig,
    WorkflowProfileConfig,
)
from backend.agent_engine.streaming.domain_events_schema import (
    Finish,
    StreamError,
)


def _create_orchestrator() -> Orchestrator:
    config = WorkflowProfileConfig(
        version="0.1.0",
        name="baseline",
        description="Test version",
        tools=[],
        model=ModelConfig(name="gpt-4o-mini", reasoning="off"),
    )
    with (
        patch("backend.agent_engine.agents.base.get_tools_by_names") as mock_get_tools,
        patch("backend.agent_engine.agents.base.create_agent") as mock_create,
        patch("backend.agent_engine.agents.base.init_chat_model"),
        patch("backend.agent_engine.agents.base.RunBudgetMiddleware"),
        patch("backend.agent_engine.agents.base.handle_tool_errors", new=MagicMock()),
    ):
        mock_get_tools.return_value = []
        mock_create.return_value = MagicMock()
        return Orchestrator(config, checkpointer=MagicMock())


async def _collect(astream_gen: Any) -> list:
    return [event async for event in astream_gen]


class TestForceLlmFailDevFlag:
    def test_force_llm_fail_raises_when_env_set_and_yields_stream_error(
        self, monkeypatch
    ):
        monkeypatch.setenv("FORCE_LLM_FAIL", "1")
        orch = _create_orchestrator()

        # Counter so we can assert agent.astream was never iterated.
        call_count: dict[str, int] = {"astream_iterations": 0}

        async def _fake_astream(*args, **kwargs):
            call_count["astream_iterations"] += 1
            if False:  # pragma: no cover
                yield

        with patch(
            "langfuse.get_client", return_value=MagicMock()
        ), patch.object(orch.agent, "astream", _fake_astream):
            events = asyncio.run(
                _collect(orch.astream_run(message="hi", session_id="sess-x"))
            )

        # FORCE_LLM_FAIL must short-circuit BEFORE astream iteration.
        assert call_count["astream_iterations"] == 0, (
            "agent.astream must not be iterated when FORCE_LLM_FAIL=1"
        )
        # The except-Exception path in astream_run converts the simulated
        # provider failure into StreamError + Finish(error).
        stream_errors = [e for e in events if isinstance(e, StreamError)]
        assert stream_errors, "expected a StreamError event"
        assert "FORCE_LLM_FAIL" in stream_errors[0].error_text
        assert any(
            isinstance(e, Finish) and e.finish_reason == "error" for e in events
        )

    def test_unset_does_not_short_circuit(self, monkeypatch):
        monkeypatch.delenv("FORCE_LLM_FAIL", raising=False)
        orch = _create_orchestrator()

        called: dict[str, bool] = {"astream": False}

        async def _fake_astream(*args, **kwargs):
            called["astream"] = True
            if False:
                yield  # never reached, but keeps this an async generator

        with patch(
            "langfuse.get_client", return_value=MagicMock()
        ), patch.object(orch.agent, "astream", _fake_astream):
            asyncio.run(_collect(orch.astream_run(message="hi", session_id="sess-x")))

        assert called["astream"] is True
