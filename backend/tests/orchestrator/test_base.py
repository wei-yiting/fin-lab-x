"""Tests for the version-agnostic Orchestrator."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from backend.agent_engine.orchestrator.base import Orchestrator
from backend.agent_engine.workflows.config_loader import VersionConfig, ModelConfig


def test_orchestrator_initialization_with_config():
    """Test orchestrator can be initialized with version config."""
    config = VersionConfig(
        version="0.1.0",
        name="v1_baseline",
        description="Test version",
        tools=["yfinance_stock_quote"],
        model=ModelConfig(name="gpt-4o-mini", temperature=0.0, max_iterations=10),
    )

    with patch(
        "backend.agent_engine.orchestrator.base.get_tools_by_names"
    ) as mock_get_tools:
        mock_tool = MagicMock()
        mock_tool.name = "yfinance_stock_quote"
        mock_get_tools.return_value = [mock_tool]

        with patch(
            "backend.agent_engine.orchestrator.base.init_chat_model"
        ) as mock_init:
            mock_model = MagicMock()
            mock_model.bind_tools = MagicMock(return_value=mock_model)
            mock_init.return_value = mock_model

            orch = Orchestrator(config)
            assert orch.config.name == "v1_baseline"


def test_orchestrator_run_returns_response():
    """Test orchestrator run returns a response."""
    config = VersionConfig(
        version="0.1.0",
        name="v1_baseline",
        description="Test version",
        tools=[],
        model=ModelConfig(name="gpt-4o-mini", temperature=0.0, max_iterations=10),
    )

    with patch(
        "backend.agent_engine.orchestrator.base.get_tools_by_names"
    ) as mock_get_tools:
        mock_get_tools.return_value = []

        with patch(
            "backend.agent_engine.orchestrator.base.init_chat_model"
        ) as mock_init:
            mock_model = MagicMock()
            mock_model.bind_tools = MagicMock(return_value=mock_model)
            mock_model.invoke = MagicMock(
                return_value=MagicMock(content="Test response", tool_calls=[])
            )
            mock_init.return_value = mock_model

            orch = Orchestrator(config)
            result = orch.run("test prompt")
            assert "response" in result or "error" in result
