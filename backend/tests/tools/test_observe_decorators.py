"""Tests to verify @observe() decorator is NOT applied on tool functions.

CallbackHandler auto-traces via LangGraph, so @observe() is unnecessary
and would interfere with streaming.
"""

from backend.agent_engine.tools.financial import (
    tavily_financial_search,
    yfinance_get_available_fields,
    yfinance_stock_quote,
)
from backend.agent_engine.tools.sec import sec_official_docs_retriever


ALL_TOOLS = [
    yfinance_stock_quote,
    yfinance_get_available_fields,
    tavily_financial_search,
    sec_official_docs_retriever,
]


def test_tools_do_not_use_observe_decorator():
    """Verify all tool functions do NOT have @observe() decorator.

    CallbackHandler auto-traces via LangGraph, so @observe() is removed.
    We check that the inner function does NOT have __wrapped__ (which
    @observe sets via functools.wraps).
    """
    for tool_func in ALL_TOOLS:
        inner = getattr(tool_func, "func", tool_func)
        assert not hasattr(inner, "__wrapped__"), (
            f"{tool_func.name} still has @observe() decorator"
        )


def test_tool_schema_intact_without_observe():
    """Verify tool schema is intact after removing @observe()."""
    expected_tools = {
        "yfinance_stock_quote": "YFinanceStockQuoteInput",
        "yfinance_get_available_fields": "YFinanceGetAvailableFieldsInput",
        "tavily_financial_search": "TavilyFinancialSearchInput",
        "sec_official_docs_retriever": "SecOfficialDocsRetrieverInput",
    }

    for tool_func in ALL_TOOLS:
        assert hasattr(tool_func, "name"), (
            f"Tool {tool_func} is missing .name attribute"
        )
        assert tool_func.name in expected_tools, (
            f"Unexpected tool name: {tool_func.name}"
        )
        assert hasattr(tool_func, "description"), (
            f"Tool {tool_func.name} is missing .description"
        )
        assert hasattr(tool_func, "args_schema"), (
            f"Tool {tool_func.name} is missing .args_schema"
        )
        args_schema = tool_func.args_schema
        assert isinstance(args_schema, type), (
            f"Tool {tool_func.name} has unexpected args_schema type: "
            f"{type(args_schema).__name__}"
        )
        assert args_schema.__name__ == expected_tools[tool_func.name], (
            f"Tool {tool_func.name} has wrong args_schema: "
            f"{args_schema.__name__} != {expected_tools[tool_func.name]}"
        )
