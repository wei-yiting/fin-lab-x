"""Tests for the version-agnostic Orchestrator."""

from unittest.mock import patch, MagicMock
from langchain_core.messages import AIMessage, HumanMessage
from backend.agent_engine.agents.base import Orchestrator
from backend.agent_engine.agents.config_loader import VersionConfig, ModelConfig


def _create_orchestrator(config: VersionConfig, mock_tools: list) -> Orchestrator:
    """Create an Orchestrator with mocked create_agent and tool registry."""
    with (
        patch(
            "backend.agent_engine.agents.base.get_tools_by_names"
        ) as mock_get_tools,
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
    """Test orchestrator can be initialized with version config."""
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
    """Test orchestrator run returns a response."""
    config = VersionConfig(
        version="0.1.0",
        name="v1_baseline",
        description="Test version",
        tools=[],
        model=ModelConfig(name="gpt-4o-mini", temperature=0.0),
    )

    orch = _create_orchestrator(config, [])

    # Mock agent.invoke to return a message list with a final AI response
    orch.agent.invoke.return_value = {
        "messages": [
            HumanMessage(content="test prompt"),
            AIMessage(content="Test response"),
        ]
    }

    result = orch.run("test prompt")
    assert "response" in result
    assert result["response"] == "Test response"
    assert result["version"] == "0.1.0"
    assert result["model"] == "gpt-4o-mini"
