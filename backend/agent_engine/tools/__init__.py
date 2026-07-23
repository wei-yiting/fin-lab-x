"""FinLab-X tools package.

Provides explicit tool registration via setup_tools(). Called automatically
on import for backward compatibility, but can also be invoked directly.
"""

from backend.agent_engine.tools.registry import register_tool

_tools_registered = False


def setup_tools() -> None:
    """Register all tools in the global registry. Idempotent."""
    global _tools_registered
    if _tools_registered:
        return

    from backend.agent_engine.tools.news_search import tavily_financial_search
    from backend.agent_engine.tools.finnhub_tools import (
        finnhub_company_basic_financials,
        finnhub_stock_quote,
    )
    from backend.agent_engine.tools.sec_filing import sec_filing_downloader
    from backend.agent_engine.tools.sec_filing_tools import (
        sec_filing_get_section,
        sec_filing_list_sections,
    )

    register_tool("finnhub_stock_quote", finnhub_stock_quote)
    register_tool(
        "finnhub_company_basic_financials", finnhub_company_basic_financials
    )
    register_tool("tavily_financial_search", tavily_financial_search)
    register_tool("sec_filing_list_sections", sec_filing_list_sections)
    register_tool("sec_filing_get_section", sec_filing_get_section)
    register_tool("sec_filing_downloader", sec_filing_downloader)

    _tools_registered = True


# Auto-register on import for backward compatibility.
setup_tools()
