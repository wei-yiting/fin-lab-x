"""Integration tests for v1 orchestrator.

Tests mock create_agent at the Orchestrator level, simulating the agent's
message history output to verify _extract_result correctly parses responses
and tool outputs.
"""

from typing import Any
from unittest.mock import Mock, patch, MagicMock

import pytest
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
        patch("backend.agent_engine.agents.base.RunBudgetMiddleware"),
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


@pytest.mark.parametrize(
    "tool_name, args",
    [
        ("yfinance_get_available_fields", {"ticker": "AAPL"}),
        ("tavily_financial_search", {"query": "latest news", "ticker": "TSLA"}),
        ("sec_filing_list_sections", {"ticker": "MSFT", "doc_type": "10-K"}),
    ],
    ids=["yfinance", "tavily", "sec"],
)
def test_single_tool_output_is_extracted(tool_name, args):
    """A single tool call yields a single tool_output carrying the tool name
    and the echoed args. yfinance / tavily / sec are the same extraction
    equivalence class — only the tool name and args strings differ — so they
    share one parametrized test. Multi-tool sequencing is covered separately by
    test_multi_tool_integration."""
    config = VersionConfig(
        version="0.1.0",
        name="v1_baseline",
        description="Test version",
        tools=[tool_name],
    )

    mock_tool = Mock()
    mock_tool.name = tool_name

    orch = _create_orchestrator(config, [mock_tool])

    orch.agent.invoke.return_value = {
        "messages": [
            HumanMessage(content="q"),
            AIMessage(
                content="",
                tool_calls=[{"name": tool_name, "args": args, "id": "call_1"}],
            ),
            ToolMessage(content="{}", tool_call_id="call_1", name=tool_name),
            AIMessage(content="done"),
        ]
    }

    result = orch.run("q")

    assert len(result["tool_outputs"]) > 0
    output = result["tool_outputs"][0]
    assert output["tool"] == tool_name
    assert output["args"] == args


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
    assert config.model.name == "openai:gpt-5-mini"
    assert config.model.reasoning == "on"


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
