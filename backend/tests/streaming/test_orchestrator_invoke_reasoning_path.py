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
from backend.agent_engine.streaming.reasoning_trace_callback import (
    ReasoningTraceCallback,
)


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


class TestInvokeBuildsCallbacksWithReasoningFirst:
    def test_build_langfuse_config_invoke_orders_reasoning_before_handler(self):
        orch = _create_orchestrator(_make_config(reasoning="on"))

        with (
            patch("backend.agent_engine.agents.base.CallbackHandler") as mock_handler_cls,
            patch(
                "backend.agent_engine.streaming.reasoning_trace_callback.get_client",
                return_value=MagicMock(),
            ),
        ):
            mock_handler = MagicMock(spec=CallbackHandler)
            mock_handler_cls.return_value = mock_handler

            config, _propagation = orch._build_langfuse_config(
                mode="invoke", request_id="req-1"
            )

        callbacks = config["callbacks"]
        assert len(callbacks) == 2
        assert isinstance(callbacks[0], ReasoningTraceCallback)
        assert callbacks[1] is mock_handler

    def test_build_langfuse_config_propagates_capability_to_callback(self):
        orch = _create_orchestrator(_make_config(reasoning="unsupported"))

        with (
            patch("backend.agent_engine.agents.base.CallbackHandler"),
            patch(
                "backend.agent_engine.streaming.reasoning_trace_callback.get_client",
                return_value=MagicMock(),
            ),
        ):
            config, _ = orch._build_langfuse_config(
                mode="invoke", request_id="req-1"
            )

        rc = cast(ReasoningTraceCallback, config["callbacks"][0])
        assert rc._capability == "unsupported"


class TestReasoningCallbackFiresOnInvokeChain:
    """Mapper-free unit test: simulate the LangChain on_llm_end dispatch the
    invoke path would trigger when the LLM call ends, and assert the cached
    Langfuse client receives the metadata write."""

    def test_on_llm_end_writes_reasoning_metadata(self):
        orch = _create_orchestrator(_make_config(reasoning="on"))

        fake_client = MagicMock()
        with (
            patch("backend.agent_engine.agents.base.CallbackHandler"),
            patch(
                "backend.agent_engine.streaming.reasoning_trace_callback.get_client",
                return_value=fake_client,
            ),
            patch(
                "backend.agent_engine.agents.base.propagate_attributes",
                return_value=nullcontext(),
            ),
        ):
            config, _ = orch._build_langfuse_config(
                mode="invoke", request_id="req-1"
            )
            rc = cast(ReasoningTraceCallback, config["callbacks"][0])

            msg = AIMessage(
                content=[
                    {"type": "reasoning", "reasoning": "the chain of thought"},
                    {"type": "text", "text": "final answer"},
                ]
            )
            response = LLMResult(generations=[[ChatGeneration(message=msg)]])
            rc.on_llm_end(response, run_id=uuid4(), parent_run_id=None)

        fake_client.update_current_generation.assert_called_once_with(
            metadata={"reasoning": "the chain of thought"},
        )
