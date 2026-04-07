"""Integration tests for v1 orchestrator.

Tests mock create_agent at the Orchestrator level, simulating the agent's
message history output to verify _extract_result correctly parses responses
and tool outputs.
"""

from typing import Any
from unittest.mock import Mock, patch, MagicMock
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from backend.agent_engine.agents.base import Orchestrator
from backend.agent_engine.agents.config_loader import VersionConfig, VersionConfigLoader
from backend.agent_engine.tools.registry import get_tools_by_names


def _create_orchestrator(config: VersionConfig, mock_tools: list) -> Any:
    """Create an Orchestrator with mocked create_agent and tool registry.

    Patches create_agent, init_chat_model, and get_tools_by_names so no real
    API keys are needed. Returns the orchestrator with a mock agent ready to
    be configured per test.
    """
    with (
        patch("backend.agent_engine.agents.base.get_tools_by_names") as mock_get_tools,
        patch("backend.agent_engine.agents.base.create_agent") as mock_create,
        patch("backend.agent_engine.agents.base.init_chat_model") as mock_init,
        patch("backend.agent_engine.agents.base.ToolCallLimitMiddleware"),
        patch("backend.agent_engine.agents.base.handle_tool_errors", new=MagicMock()),
    ):
        mock_get_tools.return_value = mock_tools
        mock_agent = MagicMock()
        mock_create.return_value = mock_agent
        mock_init.return_value = MagicMock()

        orch = Orchestrator(config, checkpointer=MagicMock())
        return orch


def _create_orchestrator_with_mocked_llm(config: VersionConfig) -> Orchestrator:
    with (
        patch("backend.agent_engine.agents.base.create_agent") as mock_create,
        patch("backend.agent_engine.agents.base.init_chat_model") as mock_init,
        patch("backend.agent_engine.agents.base.handle_tool_errors", new=MagicMock()),
    ):
        mock_agent = MagicMock()
        mock_create.return_value = mock_agent
        mock_init.return_value = MagicMock()

        orch = Orchestrator(config, checkpointer=MagicMock())
        return orch


def test_yfinance_tool_integration():
    """Test that yfinance tool output is correctly extracted."""
    config = VersionConfig(
        version="0.1.0",
        name="v1_baseline",
        description="Test version",
        tools=["yfinance_get_available_fields"],
    )

    mock_tool = Mock()
    mock_tool.name = "yfinance_get_available_fields"

    orch = _create_orchestrator(config, [mock_tool])

    # Simulate agent returning message history with tool call + result
    orch.agent.invoke.return_value = {
        "messages": [
            HumanMessage(content="What data is available for AAPL?"),
            AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": "yfinance_get_available_fields",
                        "args": {"ticker": "AAPL"},
                        "id": "call_1",
                    }
                ],
            ),
            ToolMessage(
                content='{"ticker": "AAPL", "available_fields": {}}',
                tool_call_id="call_1",
                name="yfinance_get_available_fields",
            ),
            AIMessage(content="AAPL has these fields available."),
        ]
    }

    result = orch.run("What data is available for AAPL?")

    assert len(result["tool_outputs"]) > 0
    assert result["tool_outputs"][0]["tool"] == "yfinance_get_available_fields"
    assert result["tool_outputs"][0]["args"]["ticker"] == "AAPL"


def test_tavily_tool_integration():
    """Test that tavily tool output is correctly extracted."""
    config = VersionConfig(
        version="0.1.0",
        name="v1_baseline",
        description="Test version",
        tools=["tavily_financial_search"],
    )

    mock_tool = Mock()
    mock_tool.name = "tavily_financial_search"

    orch = _create_orchestrator(config, [mock_tool])

    orch.agent.invoke.return_value = {
        "messages": [
            HumanMessage(content="What's the latest news about TSLA?"),
            AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": "tavily_financial_search",
                        "args": {"query": "latest news", "ticker": "TSLA"},
                        "id": "call_1",
                    }
                ],
            ),
            ToolMessage(
                content='{"results": []}',
                tool_call_id="call_1",
                name="tavily_financial_search",
            ),
            AIMessage(content="No recent news for TSLA."),
        ]
    }

    result = orch.run("What's the latest news about TSLA?")

    assert len(result["tool_outputs"]) > 0
    assert result["tool_outputs"][0]["tool"] == "tavily_financial_search"
    assert result["tool_outputs"][0]["args"]["ticker"] == "TSLA"


def test_sec_tool_integration():
    """Test that SEC tool output is correctly extracted."""
    config = VersionConfig(
        version="0.1.0",
        name="v1_baseline",
        description="Test version",
        tools=["sec_official_docs_retriever"],
    )

    mock_tool = Mock()
    mock_tool.name = "sec_official_docs_retriever"

    orch = _create_orchestrator(config, [mock_tool])

    orch.agent.invoke.return_value = {
        "messages": [
            HumanMessage(content="Get the latest 10-K for MSFT"),
            AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": "sec_official_docs_retriever",
                        "args": {"ticker": "MSFT", "doc_type": "10-K"},
                        "id": "call_1",
                    }
                ],
            ),
            ToolMessage(
                content='{"ticker": "MSFT", "doc_type": "10-K"}',
                tool_call_id="call_1",
                name="sec_official_docs_retriever",
            ),
            AIMessage(content="MSFT 10-K filing retrieved."),
        ]
    }

    result = orch.run("Get the latest 10-K for MSFT")

    assert len(result["tool_outputs"]) > 0
    assert result["tool_outputs"][0]["tool"] == "sec_official_docs_retriever"
    assert result["tool_outputs"][0]["args"]["ticker"] == "MSFT"
    assert result["tool_outputs"][0]["args"]["doc_type"] == "10-K"


def test_multi_tool_integration():
    """Test that multiple tools called in sequence are all extracted."""
    config = VersionConfig(
        version="0.1.0",
        name="v1_baseline",
        description="Test version",
        tools=["yfinance_stock_quote", "tavily_financial_search"],
    )

    mock_tool_1 = Mock()
    mock_tool_1.name = "yfinance_stock_quote"
    mock_tool_2 = Mock()
    mock_tool_2.name = "tavily_financial_search"

    orch = _create_orchestrator(config, [mock_tool_1, mock_tool_2])

    # Simulate agent calling two tools in sequence
    orch.agent.invoke.return_value = {
        "messages": [
            HumanMessage(content="Analyze AAPL stock price and news"),
            AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": "yfinance_stock_quote",
                        "args": {"ticker": "AAPL"},
                        "id": "call_1",
                    }
                ],
            ),
            ToolMessage(
                content='{"ticker": "AAPL", "current_price": 150}',
                tool_call_id="call_1",
                name="yfinance_stock_quote",
            ),
            AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": "tavily_financial_search",
                        "args": {"query": "news", "ticker": "AAPL"},
                        "id": "call_2",
                    }
                ],
            ),
            ToolMessage(
                content='{"results": []}',
                tool_call_id="call_2",
                name="tavily_financial_search",
            ),
            AIMessage(content="Analysis complete"),
        ]
    }

    result = orch.run("Analyze AAPL stock price and news")

    # Verify both tools were extracted
    assert len(result["tool_outputs"]) >= 2
    tool_names = [t["tool"] for t in result["tool_outputs"]]
    assert "yfinance_stock_quote" in tool_names
    assert "tavily_financial_search" in tool_names


def test_zero_hallucination_policy():
    """Test that response without tool calls is correctly extracted."""
    config = VersionConfig(
        version="0.1.0",
        name="v1_baseline",
        description="Test version",
        tools=[],
    )

    orch = _create_orchestrator(config, [])

    orch.agent.invoke.return_value = {
        "messages": [
            HumanMessage(content="What is AAPL's price?"),
            AIMessage(content="Based on the data, AAPL is trading at $150."),
        ]
    }

    result = orch.run("What is AAPL's price?")

    # Response should be present
    assert "response" in result
    assert result["response"] == "Based on the data, AAPL is trading at $150."
    # Should have version info
    assert "version" in result


def test_config_loading_from_yaml():
    config = VersionConfigLoader("v1_baseline").load()

    assert config.version == "0.1.0"
    assert config.name == "v1_baseline"
    assert "yfinance_stock_quote" in config.tools
    assert "tavily_financial_search" in config.tools
    assert config.model.name == "gpt-4o-mini"


def test_system_prompt_loaded_from_file():
    config = VersionConfigLoader("v1_baseline").load()

    assert config.system_prompt is not None
    assert "ZERO HALLUCINATION" in config.system_prompt
    assert "CITATION" in config.system_prompt


def test_tool_registry_has_tools():
    tools = get_tools_by_names(
        [
            "yfinance_stock_quote",
            "tavily_financial_search",
        ]
    )

    assert len(tools) == 2


def test_orchestrator_uses_config_system_prompt():
    config = VersionConfig(
        version="0.1.0",
        name="v1_baseline",
        description="Test version",
        tools=[],
        system_prompt="Custom test prompt",
    )

    orch = _create_orchestrator_with_mocked_llm(config)

    assert orch.system_prompt == "Custom test prompt"
    assert "FinLab-X" not in orch.system_prompt


def test_orchestrator_falls_back_to_default_prompt():
    config = VersionConfig(
        version="0.1.0",
        name="v1_baseline",
        description="Test version",
        tools=[],
        system_prompt=None,
    )

    orch = _create_orchestrator_with_mocked_llm(config)

    assert "FinLab-X" in orch.system_prompt


def test_extract_result_empty_messages():
    config = VersionConfig(
        version="0.1.0",
        name="v1_baseline",
        description="Test version",
        tools=[],
    )

    orch = _create_orchestrator(config, [])
    result = orch._extract_result({"messages": []})

    assert result["response"] == ""
    assert result["tool_outputs"] == []


def test_extract_result_no_final_ai_message():
    config = VersionConfig(
        version="0.1.0",
        name="v1_baseline",
        description="Test version",
        tools=["yfinance_stock_quote"],
    )

    mock_tool = Mock()
    mock_tool.name = "yfinance_stock_quote"

    orch = _create_orchestrator(config, [mock_tool])

    result = orch._extract_result(
        {
            "messages": [
                AIMessage(
                    content="",
                    tool_calls=[
                        {
                            "name": "yfinance_stock_quote",
                            "args": {"ticker": "AAPL"},
                            "id": "call_1",
                        }
                    ],
                ),
                ToolMessage(
                    content='{"ticker": "AAPL", "price": 150}',
                    tool_call_id="call_1",
                    name="yfinance_stock_quote",
                ),
            ]
        }
    )

    assert result["response"] == ""
