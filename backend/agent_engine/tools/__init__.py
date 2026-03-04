"""FinLab-X tools package."""

from backend.agent_engine.tools.financial import (
    yfinance_stock_quote,
    yfinance_get_available_fields,
    tavily_financial_search,
)
from backend.agent_engine.tools.sec import sec_official_docs_retriever
from backend.agent_engine.agents.specialized.registry import register_tool

# Register all tools
register_tool("yfinance_stock_quote", yfinance_stock_quote)
register_tool("yfinance_get_available_fields", yfinance_get_available_fields)
register_tool("tavily_financial_search", tavily_financial_search)
register_tool("sec_official_docs_retriever", sec_official_docs_retriever)

V1_TOOLS = [
    yfinance_stock_quote,
    yfinance_get_available_fields,
    tavily_financial_search,
    sec_official_docs_retriever,
]

__all__ = [
    "yfinance_stock_quote",
    "yfinance_get_available_fields",
    "tavily_financial_search",
    "sec_official_docs_retriever",
    "V1_TOOLS",
]
