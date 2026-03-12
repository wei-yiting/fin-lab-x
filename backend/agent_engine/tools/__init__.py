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

    from backend.agent_engine.tools.financial import (
        tavily_financial_search,
        yfinance_get_available_fields,
        yfinance_stock_quote,
    )
    from backend.agent_engine.tools.sec import sec_official_docs_retriever

    register_tool("yfinance_stock_quote", yfinance_stock_quote)
    register_tool("yfinance_get_available_fields", yfinance_get_available_fields)
    register_tool("tavily_financial_search", tavily_financial_search)
    register_tool("sec_official_docs_retriever", sec_official_docs_retriever)

    _tools_registered = True


# Auto-register on import for backward compatibility.
setup_tools()
