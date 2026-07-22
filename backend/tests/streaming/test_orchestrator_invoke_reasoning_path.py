"""Task 6 / S-stream-05 — invoke path also produces reasoning trace metadata.

The invoke endpoints (run / arun) must wire ReasoningTraceCallback ahead of
the Langfuse handler exactly like astream_run does. This test exercises the
public _build_langfuse_config(mode="invoke") path and then drives the
callback's on_llm_end directly to confirm the metadata write would fire if
the chain were live.
"""

from __future__ import annotations

from contextlib import nullcontext
from typing import cast
from unittest.mock import MagicMock, patch
from uuid import uuid4

from langchain_core.messages import AIMessage
from langchain_core.outputs import ChatGeneration, LLMResult
from langfuse.langchain import CallbackHandler

from backend.agent_engine.agents.base import Orchestrator
from backend.agent_engine.agents.config_loader import ModelConfig, VersionConfig
from backend.agent_engine.streaming import reasoning_trace_callback as rtc_module
from backend.agent_engine.streaming.reasoning_trace_callback import (
    ReasoningTraceCallback,
)


class _FakeGeneration:
    """Stand-in for ``LangfuseGeneration`` exposing only the ``update`` API the
    callback uses. The real class needs a live trace context to instantiate."""

    def __init__(self) -> None:
        self.updates: list[dict] = []

    def update(self, *, metadata: dict) -> None:
        self.updates.append(metadata)


def _make_config(reasoning: str = "on") -> VersionConfig:
    return VersionConfig(
        version="0.1.0",
        name="v1_baseline",
        description="Test version",
        tools=[],
        model=ModelConfig(name="gpt-4o-mini", reasoning=reasoning),
    )


def _create_orchestrator(config: VersionConfig) -> Orchestrator:
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


class TestInvokeBuildsCallbacksWithReasoning:
    def test_build_langfuse_config_invoke_wires_handler_into_reasoning_callback(self):
        """The invoke path must hand the Langfuse handler to the
        ReasoningTraceCallback so on_llm_end can resolve the in-flight
        GENERATION via ``handler._runs[run_id]`` (the production write path).

        We assert membership + the handler wiring, NOT list position: the
        ``_build_langfuse_config`` docstring states ordering is no longer
        load-bearing once lookup-by-run_id is in play, so pinning index 0/1
        would block a harmless reorder without protecting any behavior.
        """
        orch = _create_orchestrator(_make_config(reasoning="on"))

        with (
            patch(
                "backend.agent_engine.agents.base.CallbackHandler"
            ) as mock_handler_cls,
            patch(
                "backend.agent_engine.streaming.reasoning_trace_callback.get_client",
                return_value=MagicMock(),
            ),
        ):
            mock_handler = MagicMock(spec=CallbackHandler)
            mock_handler_cls.return_value = mock_handler

            config, _propagation, handler = orch._build_langfuse_config(
                mode="invoke", request_id="req-1"
            )

        callbacks = config["callbacks"]
        reasoning_callbacks = [
            c for c in callbacks if isinstance(c, ReasoningTraceCallback)
        ]
        assert len(reasoning_callbacks) == 1
        assert handler in callbacks
        # Load-bearing wiring: the callback holds the same handler reference,
        # which is what lets it look up the GENERATION by run_id.
        assert reasoning_callbacks[0]._handler is handler is mock_handler

    def test_build_langfuse_config_propagates_capability_to_callback(self):
        orch = _create_orchestrator(_make_config(reasoning="unsupported"))

        with (
            patch("backend.agent_engine.agents.base.CallbackHandler"),
            patch(
                "backend.agent_engine.streaming.reasoning_trace_callback.get_client",
                return_value=MagicMock(),
            ),
        ):
            config, _, _h = orch._build_langfuse_config(
                mode="invoke", request_id="req-1"
            )

        rc = cast(ReasoningTraceCallback, config["callbacks"][0])
        assert rc._capability == "unsupported"


class TestReasoningCallbackFiresOnInvokeChain:
    """Mapper-free integration test: drive the LangChain on_llm_end dispatch the
    invoke path triggers when the LLM call ends, and assert the callback built
    by ``_build_langfuse_config`` writes via the PRODUCTION run_id-lookup path
    (``generation.update``), not the OTel current-generation fallback.
    """

    def test_on_llm_end_writes_reasoning_via_production_run_lookup(self):
        orch = _create_orchestrator(_make_config(reasoning="on"))

        run_id = uuid4()
        generation = _FakeGeneration()
        fake_client = MagicMock()
        with (
            patch(
                "backend.agent_engine.agents.base.CallbackHandler"
            ) as mock_handler_cls,
            patch(
                "backend.agent_engine.streaming.reasoning_trace_callback.get_client",
                return_value=fake_client,
            ),
            patch(
                "backend.agent_engine.agents.base.propagate_attributes",
                return_value=nullcontext(),
            ),
            patch.object(rtc_module, "LangfuseGeneration", _FakeGeneration),
        ):
            # Seed the handler's _runs map exactly as Langfuse does during
            # on_chat_model_start: run_id -> in-flight GENERATION.
            mock_handler = MagicMock()
            mock_handler._runs = {run_id: generation}
            mock_handler_cls.return_value = mock_handler

            config, _, _h = orch._build_langfuse_config(
                mode="invoke", request_id="req-1"
            )
            rc = next(
                c
                for c in config["callbacks"]
                if isinstance(c, ReasoningTraceCallback)
            )

            msg = AIMessage(
                content=[
                    {"type": "reasoning", "reasoning": "the chain of thought"},
                    {"type": "text", "text": "final answer"},
                ]
            )
            response = LLMResult(generations=[[ChatGeneration(message=msg)]])
            rc.on_llm_end(response, run_id=run_id, parent_run_id=None)

        # Production path: written through the looked-up generation, and the
        # OTel current-generation fallback was NOT used.
        assert generation.updates == [{"reasoning": "the chain of thought"}]
        fake_client.update_current_generation.assert_not_called()
