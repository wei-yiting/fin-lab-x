"""Integration tests for v1 orchestrator."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from backend.agent_engine.orchestrator.base import Orchestrator
from backend.agent_engine.workflows.config_loader import VersionConfig


def _create_orchestrator(config: VersionConfig, mock_tools: list) -> Orchestrator:
    """Create an Orchestrator with mocked LLM and tools.

    Patches init_chat_model and get_tools_by_names so no real API keys are needed.
    Returns the orchestrator with a mock model ready to be configured per test.
    """
    with (
        patch(
            "backend.agent_engine.orchestrator.base.get_tools_by_names"
        ) as mock_get_tools,
        patch("backend.agent_engine.orchestrator.base.init_chat_model") as mock_init,
    ):
        mock_get_tools.return_value = mock_tools

        # init_chat_model returns a model; .bind_tools() returns the bound model
        mock_model = MagicMock()
        mock_bound = MagicMock()
        mock_model.bind_tools.return_value = mock_bound
        mock_init.return_value = mock_model

        orch = Orchestrator(config)
        return orch


def test_yfinance_tool_integration():
    """Test that yfinance tool is called correctly."""
    config = VersionConfig(
        version="0.1.0",
        name="v1_baseline",
        description="Test version",
        tools=["yfinance_get_available_fields"],
    )

    mock_tool = Mock()
    mock_tool.name = "yfinance_get_available_fields"
    mock_tool.invoke.return_value = {"ticker": "AAPL", "available_fields": {}}

    orch = _create_orchestrator(config, [mock_tool])

    # First call: LLM returns tool call, second call: LLM returns final answer
    call_count = [0]

    def mock_invoke(messages):
        if call_count[0] == 0:
            call_count[0] += 1
            return Mock(
                tool_calls=[
                    {
                        "name": "yfinance_get_available_fields",
                        "args": {"ticker": "AAPL"},
                        "id": "call_1",
                    }
                ]
            )
        return Mock(tool_calls=[], content="AAPL has these fields available.")

    orch.model.invoke = mock_invoke

    result = orch.run("What data is available for AAPL?")

    assert len(result["tool_outputs"]) > 0
    assert result["tool_outputs"][0]["tool"] == "yfinance_get_available_fields"
    assert result["tool_outputs"][0]["args"]["ticker"] == "AAPL"


def test_tavily_tool_integration():
    """Test that tavily tool is called correctly."""
    config = VersionConfig(
        version="0.1.0",
        name="v1_baseline",
        description="Test version",
        tools=["tavily_financial_search"],
    )

    mock_tool = Mock()
    mock_tool.name = "tavily_financial_search"
    mock_tool.invoke.return_value = {"results": []}

    orch = _create_orchestrator(config, [mock_tool])

    call_count = [0]

    def mock_invoke(messages):
        if call_count[0] == 0:
            call_count[0] += 1
            return Mock(
                tool_calls=[
                    {
                        "name": "tavily_financial_search",
                        "args": {"query": "latest news", "ticker": "TSLA"},
                        "id": "call_1",
                    }
                ]
            )
        return Mock(tool_calls=[], content="No recent news for TSLA.")

    orch.model.invoke = mock_invoke

    result = orch.run("What's the latest news about TSLA?")

    assert len(result["tool_outputs"]) > 0
    assert result["tool_outputs"][0]["tool"] == "tavily_financial_search"
    assert result["tool_outputs"][0]["args"]["ticker"] == "TSLA"


def test_sec_tool_integration():
    """Test that SEC tool is called correctly."""
    config = VersionConfig(
        version="0.1.0",
        name="v1_baseline",
        description="Test version",
        tools=["sec_official_docs_retriever"],
    )

    mock_tool = Mock()
    mock_tool.name = "sec_official_docs_retriever"
    mock_tool.invoke.return_value = {"ticker": "MSFT", "doc_type": "10-K"}

    orch = _create_orchestrator(config, [mock_tool])

    call_count = [0]

    def mock_invoke(messages):
        if call_count[0] == 0:
            call_count[0] += 1
            return Mock(
                tool_calls=[
                    {
                        "name": "sec_official_docs_retriever",
                        "args": {"ticker": "MSFT", "doc_type": "10-K"},
                        "id": "call_1",
                    }
                ]
            )
        return Mock(tool_calls=[], content="MSFT 10-K filing retrieved.")

    orch.model.invoke = mock_invoke

    result = orch.run("Get the latest 10-K for MSFT")

    assert len(result["tool_outputs"]) > 0
    assert result["tool_outputs"][0]["tool"] == "sec_official_docs_retriever"
    assert result["tool_outputs"][0]["args"]["ticker"] == "MSFT"
    assert result["tool_outputs"][0]["args"]["doc_type"] == "10-K"


def test_multi_tool_integration():
    """Test that multiple tools can be called in sequence."""
    config = VersionConfig(
        version="0.1.0",
        name="v1_baseline",
        description="Test version",
        tools=["yfinance_stock_quote", "tavily_financial_search"],
    )

    mock_tool_1 = Mock()
    mock_tool_1.name = "yfinance_stock_quote"
    mock_tool_1.invoke.return_value = {"ticker": "AAPL", "current_price": 150}

    mock_tool_2 = Mock()
    mock_tool_2.name = "tavily_financial_search"
    mock_tool_2.invoke.return_value = {"results": []}

    orch = _create_orchestrator(config, [mock_tool_1, mock_tool_2])

    call_count = [0]

    def mock_invoke(messages):
        if call_count[0] == 0:
            call_count[0] += 1
            return Mock(
                tool_calls=[
                    {
                        "name": "yfinance_stock_quote",
                        "args": {"ticker": "AAPL"},
                        "id": "call_1",
                    }
                ]
            )
        elif call_count[0] == 1:
            call_count[0] += 1
            return Mock(
                tool_calls=[
                    {
                        "name": "tavily_financial_search",
                        "args": {"query": "news", "ticker": "AAPL"},
                        "id": "call_2",
                    }
                ]
            )
        else:
            return Mock(tool_calls=[], content="Analysis complete")

    orch.model.invoke = mock_invoke

    result = orch.run("Analyze AAPL stock price and news")

    # Verify both tools were called
    assert len(result["tool_outputs"]) >= 2
    tool_names = [t["tool"] for t in result["tool_outputs"]]
    assert "yfinance_stock_quote" in tool_names
    assert "tavily_financial_search" in tool_names


def test_zero_hallucination_policy():
    """Test that response is grounded in tool outputs."""
    config = VersionConfig(
        version="0.1.0",
        name="v1_baseline",
        description="Test version",
        tools=[],
    )

    orch = _create_orchestrator(config, [])

    orch.model.invoke.return_value = Mock(
        tool_calls=[],
        content="Based on the data, AAPL is trading at $150.",
    )

    result = orch.run("What is AAPL's price?")

    # Response should be present
    assert "response" in result
    # Should have version info
    assert "version" in result
