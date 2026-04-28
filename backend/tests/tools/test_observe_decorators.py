"""Allow-list assertions for @observe() usage on tool functions.

Convention: tools that need CallbackHandler auto-tracing via LangGraph
do NOT use @observe (it would interfere with streaming). SEC filing tools
that go through edgartools + blocking I/O benefit from explicit
@observe spans, so they are on the allow-list.
"""

from backend.agent_engine.tools.financial import (
    tavily_financial_search,
    yfinance_get_available_fields,
    yfinance_stock_quote,
)
from backend.agent_engine.tools.sec_filing import sec_filing_downloader
from backend.agent_engine.tools.sec_filing_tools import (
    sec_filing_get_section,
    sec_filing_list_sections,
)


TOOLS_WITHOUT_OBSERVE = [
    yfinance_stock_quote,
    yfinance_get_available_fields,
    tavily_financial_search,
]

TOOLS_WITH_OBSERVE = [
    sec_filing_list_sections,
    sec_filing_get_section,
    sec_filing_downloader,
]


def test_legacy_tools_have_no_observe():
    """Tools that rely on CallbackHandler auto-tracing must not wrap
    @observe — it would double-trace and break streaming."""
    for tool_func in TOOLS_WITHOUT_OBSERVE:
        inner = getattr(tool_func, "func", tool_func)
        assert not hasattr(inner, "__wrapped__"), (
            f"{tool_func.name} unexpectedly has @observe() decorator"
        )


def test_new_sec_tools_have_observe():
    """SEC tools use explicit @observe spans for richer tracing of the
    edgartools blocking path. Verify the decorator is applied (wrapper
    sets __wrapped__) and the tool name is aligned."""
    expected_names = {
        "sec_filing_list_sections",
        "sec_filing_get_section",
        "sec_filing_downloader",
    }
    actual_names = set()
    for tool_func in TOOLS_WITH_OBSERVE:
        inner = getattr(tool_func, "func", tool_func)
        assert hasattr(inner, "__wrapped__"), (
            f"{tool_func.name} is missing @observe() decorator"
        )
        actual_names.add(tool_func.name)
    assert actual_names == expected_names


def test_all_tools_have_valid_schema():
    """Every registered tool — with or without @observe — must still
    expose name / description / args_schema so LangChain can bind it."""
    expected_schemas = {
        "yfinance_stock_quote": "YFinanceStockQuoteInput",
        "yfinance_get_available_fields": "YFinanceGetAvailableFieldsInput",
        "tavily_financial_search": "TavilyFinancialSearchInput",
        "sec_filing_list_sections": "SecFilingListSectionsInput",
        "sec_filing_get_section": "SecFilingGetSectionInput",
        "sec_filing_downloader": "SecFilingDownloaderInput",
    }

    for tool_func in TOOLS_WITHOUT_OBSERVE + TOOLS_WITH_OBSERVE:
        assert hasattr(tool_func, "name")
        assert hasattr(tool_func, "description")
        assert hasattr(tool_func, "args_schema")
        args_schema = tool_func.args_schema
        assert isinstance(args_schema, type)
        assert args_schema.__name__ == expected_schemas[tool_func.name], (
            f"Tool {tool_func.name} schema mismatch: "
            f"{args_schema.__name__} != {expected_schemas[tool_func.name]}"
        )
