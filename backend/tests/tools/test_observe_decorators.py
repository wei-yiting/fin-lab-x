"""Tests to verify @observe() decorator is applied on all tool functions."""

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


def test_tools_use_observe_decorator():
    """Verify all tool functions are decorated with @observe().

    Langfuse's @observe() wraps functions and sets internal attributes.
    We check that the wrapper chain includes the observe layer by verifying
    the function's __wrapped__ attribute exists (set by functools.wraps
    inside @observe).
    """
    for tool_func in ALL_TOOLS:
        # LangChain @tool creates a StructuredTool with a .func attribute
        inner = getattr(tool_func, "func", tool_func)
        # Fragile assertion: depends on @observe using functools.wraps internally.
        assert hasattr(inner, "__wrapped__"), (
            f"{tool_func.name} is missing @observe() decorator — "
            f"no __wrapped__ attribute found on inner function"
        )


def test_observe_decorator_does_not_break_tool_schema():
    """Verify @observe() doesn't interfere with LangChain tool schema."""
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
        assert tool_func.args_schema.__name__ == expected_tools[tool_func.name], (
            f"Tool {tool_func.name} has wrong args_schema: "
            f"{tool_func.args_schema.__name__} != {expected_tools[tool_func.name]}"
        )
