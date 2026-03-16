"""Tests for Langfuse CallbackHandler injection in Orchestrator."""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from langchain_core.messages import AIMessage, HumanMessage

from backend.agent_engine.agents.base import Orchestrator
from backend.agent_engine.agents.config_loader import VersionConfig, ModelConfig


def _make_config() -> VersionConfig:
    """Create minimal test config."""
    return VersionConfig(
        version="0.1.0",
        name="v1_baseline",
        description="Test version",
        tools=[],
        model=ModelConfig(name="gpt-4o-mini", temperature=0.0),
    )


def _mock_agent_response() -> dict:
    """Standard agent response for tests."""
    return {
        "messages": [
            HumanMessage(content="test"),
            AIMessage(content="Test response"),
        ]
    }


def _create_orchestrator(config: VersionConfig) -> Orchestrator:
    """Create orchestrator with all external deps mocked."""
    with (
        patch("backend.agent_engine.agents.base.get_tools_by_names") as mock_get_tools,
        patch("backend.agent_engine.agents.base.create_agent") as mock_create,
        patch("backend.agent_engine.agents.base.init_chat_model"),
        patch("backend.agent_engine.agents.base.ToolCallLimitMiddleware"),
    ):
        mock_get_tools.return_value = []
        mock_agent = MagicMock()
        mock_create.return_value = mock_agent
        orch = Orchestrator(config)
        return orch


class TestRunInjectsLangfuseCallback:
    def test_run_injects_langfuse_callback(self):
        config = _make_config()
        orch = _create_orchestrator(config)
        orch.agent.invoke.return_value = _mock_agent_response()

        with patch(
            "backend.agent_engine.agents.base.CallbackHandler"
        ) as mock_handler_cls:
            mock_handler = MagicMock()
            mock_handler_cls.return_value = mock_handler

            orch.run("test prompt")

            mock_handler_cls.assert_called_once()
            call_args = orch.agent.invoke.call_args
            config_arg = call_args[1].get("config")
            assert config_arg is not None, "agent.invoke was not called with config="
            assert "callbacks" in config_arg
            assert mock_handler in config_arg["callbacks"]

    def test_run_without_session_id(self):
        config = _make_config()
        orch = _create_orchestrator(config)
        orch.agent.invoke.return_value = _mock_agent_response()

        with patch(
            "backend.agent_engine.agents.base.CallbackHandler"
        ) as mock_handler_cls:
            mock_handler_cls.return_value = MagicMock()

            result = orch.run("test prompt")

            assert result["response"] == "Test response"
            call_args = orch.agent.invoke.call_args
            config_arg = call_args[1].get("config")
            assert config_arg["metadata"] == {}


class TestArunInjectsLangfuseCallback:
    @pytest.mark.asyncio
    async def test_arun_injects_langfuse_callback(self):
        config = _make_config()
        orch = _create_orchestrator(config)
        orch.agent.ainvoke = AsyncMock(return_value=_mock_agent_response())

        with patch(
            "backend.agent_engine.agents.base.CallbackHandler"
        ) as mock_handler_cls:
            mock_handler = MagicMock()
            mock_handler_cls.return_value = mock_handler

            await orch.arun("test prompt")

            mock_handler_cls.assert_called_once()
            call_args = orch.agent.ainvoke.call_args
            config_arg = call_args[1].get("config")
            assert config_arg is not None
            assert "callbacks" in config_arg
            assert mock_handler in config_arg["callbacks"]

    @pytest.mark.asyncio
    async def test_arun_passes_session_id_via_metadata(self):
        config = _make_config()
        orch = _create_orchestrator(config)
        orch.agent.ainvoke = AsyncMock(return_value=_mock_agent_response())

        with patch(
            "backend.agent_engine.agents.base.CallbackHandler"
        ) as mock_handler_cls:
            mock_handler_cls.return_value = MagicMock()

            await orch.arun("test prompt", session_id="sess-123")

            call_args = orch.agent.ainvoke.call_args
            config_arg = call_args[1].get("config")
            assert config_arg["metadata"]["langfuse_session_id"] == "sess-123"
