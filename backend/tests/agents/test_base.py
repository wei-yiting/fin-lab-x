"""Tests for the version-agnostic Orchestrator."""

from typing import Any, cast
from unittest.mock import patch, MagicMock
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from backend.agent_engine.agents.base import Orchestrator, _DEFAULT_SYSTEM_PROMPT
from backend.agent_engine.agents.config_loader import VersionConfig, ModelConfig


def _create_orchestrator(config: VersionConfig, mock_tools: list) -> Orchestrator:
    with (
        patch("backend.agent_engine.agents.base.get_tools_by_names") as mock_get_tools,
        patch("backend.agent_engine.agents.base.create_agent") as mock_create,
        patch("backend.agent_engine.agents.base.init_chat_model") as mock_init,
        patch("backend.agent_engine.agents.base.ToolCallLimitMiddleware"),
    ):
        mock_get_tools.return_value = mock_tools
        mock_agent = MagicMock()
        mock_create.return_value = mock_agent
        mock_init.return_value = MagicMock()

        orch = Orchestrator(config)
        return orch


def test_orchestrator_initialization_with_config():
    config = VersionConfig(
        version="0.1.0",
        name="v1_baseline",
        description="Test version",
        tools=["yfinance_stock_quote"],
        model=ModelConfig(name="gpt-4o-mini", temperature=0.0),
    )

    mock_tool = MagicMock()
    mock_tool.name = "yfinance_stock_quote"

    orch = _create_orchestrator(config, [mock_tool])
    assert orch.config.name == "v1_baseline"
    assert len(orch.tools) == 1


def test_orchestrator_run_returns_response():
    config = VersionConfig(
        version="0.1.0",
        name="v1_baseline",
        description="Test version",
        tools=[],
        model=ModelConfig(name="gpt-4o-mini", temperature=0.0),
    )

    orch = _create_orchestrator(config, [])

    cast(Any, orch.agent.invoke).return_value = {
        "messages": [
            HumanMessage(content="test prompt"),
            AIMessage(content="Test response"),
        ]
    }

    result = orch.run("test prompt")
    assert result["response"] == "Test response"
    assert result["version"] == "0.1.0"
    assert result["model"] == "gpt-4o-mini"


def test_orchestrator_uses_config_system_prompt():
    custom_prompt = "You are a custom financial assistant."
    config = VersionConfig(
        version="0.1.0",
        name="v1_baseline",
        description="Test version",
        tools=[],
        system_prompt=custom_prompt,
    )

    orch = _create_orchestrator(config, [])
    assert orch.system_prompt == custom_prompt


def test_orchestrator_falls_back_to_default_prompt():
    config = VersionConfig(
        version="0.1.0",
        name="v1_baseline",
        description="Test version",
        tools=[],
        system_prompt=None,
    )

    orch = _create_orchestrator(config, [])
    assert orch.system_prompt == _DEFAULT_SYSTEM_PROMPT


def test_orchestrator_result_has_typed_structure():
    config = VersionConfig(
        version="0.1.0",
        name="v1_baseline",
        description="Test version",
        tools=[],
    )
    orch = _create_orchestrator(config, [])

    cast(Any, orch.agent.invoke).return_value = {
        "messages": [
            HumanMessage(content="test"),
            AIMessage(
                content="",
                tool_calls=[{"name": "test_tool", "args": {"x": 1}, "id": "c1"}],
            ),
            ToolMessage(content="result_data", tool_call_id="c1", name="test_tool"),
            AIMessage(content="Final answer"),
        ]
    }

    result = orch.run("test")
    assert result["response"] == "Final answer"
    assert len(result["tool_outputs"]) == 1
    assert result["tool_outputs"][0]["tool"] == "test_tool"
    assert result["tool_outputs"][0]["args"] == {"x": 1}
    assert result["tool_outputs"][0]["result"] == "result_data"
