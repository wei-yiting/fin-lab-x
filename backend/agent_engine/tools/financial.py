"""Financial data tools for FinLab-X."""

from typing import Annotated, Any

import yfinance as yf
from langchain_core.tools import InjectedToolCallId
from langgraph.config import get_stream_writer
from pydantic import BaseModel, Field
from langchain.tools import tool


class YFinanceStockQuoteInput(BaseModel):
    """Input schema for yfinance stock quote tool."""

    ticker: str = Field(..., description="Stock ticker symbol (e.g., AAPL, TSLA)")


@tool("yfinance_stock_quote", args_schema=YFinanceStockQuoteInput)
def yfinance_stock_quote(
    ticker: str,
    tool_call_id: Annotated[str, InjectedToolCallId],
) -> dict[str, Any]:
    """Retrieve real-time quantitative stock metrics using yfinance."""
    try:
        writer = get_stream_writer()
    except Exception:
        writer = None

    normalized_ticker = ticker.strip().upper()
    if writer:
        writer({"status": "querying_stock", "message": f"Querying {normalized_ticker}...", "toolName": "yfinance_stock_quote", "toolCallId": tool_call_id})

    info = yf.Ticker(normalized_ticker).info
    return {
        "ticker": normalized_ticker,
        "currentPrice": info.get("currentPrice"),
        "fiftyTwoWeekHigh": info.get("fiftyTwoWeekHigh"),
        "fiftyTwoWeekLow": info.get("fiftyTwoWeekLow"),
        "forwardPE": info.get("forwardPE"),
        "trailingPE": info.get("trailingPE"),
    }


class YFinanceGetAvailableFieldsInput(BaseModel):
    """Input schema for yfinance get available fields tool."""

    ticker: str = Field(
        ..., description="Stock ticker symbol to query available fields"
    )


@tool("yfinance_get_available_fields", args_schema=YFinanceGetAvailableFieldsInput)
def yfinance_get_available_fields(
    ticker: str,
    tool_call_id: Annotated[str, InjectedToolCallId],
) -> dict[str, Any]:
    """Get all available data fields for a stock ticker with descriptions.

    Use this tool first to discover what data is available, then use
    yfinance_stock_quote with specific fields.

    Only returns curated fields with known descriptions to avoid wasting
    LLM tokens on unrecognized yfinance fields.
    """
    try:
        writer = get_stream_writer()
    except Exception:
        writer = None

    normalized_ticker = ticker.strip().upper()
    if writer:
        writer({"status": "querying_fields", "message": f"Discovering fields for {normalized_ticker}...", "toolName": "yfinance_get_available_fields", "toolCallId": tool_call_id})

    info = yf.Ticker(normalized_ticker).info

    field_descriptions = {
        "currentPrice": "Current stock price",
        "fiftyTwoWeekHigh": "52-week high price",
        "fiftyTwoWeekLow": "52-week low price",
        "forwardPE": "Forward P/E ratio",
        "trailingPE": "Trailing P/E ratio",
        "marketCap": "Market capitalization",
        "revenueGrowth": "Revenue growth rate",
        "earningsGrowth": "Earnings growth rate",
        "dividendYield": "Dividend yield",
        "beta": "Beta coefficient",
        "avgVolume": "Average trading volume",
        "profitMargin": "Profit margin",
        "operatingMargin": "Operating margin",
        "returnOnEquity": "Return on equity (ROE)",
        "returnOnAssets": "Return on assets (ROA)",
        "debtToEquity": "Debt-to-equity ratio",
        "currentRatio": "Current ratio",
        "quickRatio": "Quick ratio",
        "priceToBook": "Price-to-book ratio",
        "priceToSales": "Price-to-sales ratio",
        "enterpriseValue": "Enterprise value",
        "ebitda": "EBITDA",
        "totalRevenue": "Total revenue",
        "netIncome": "Net income",
        "freeCashflow": "Free cash flow",
        "operatingCashflow": "Operating cash flow",
    }

    available_fields = {}
    for field, description in field_descriptions.items():
        if field in info:
            available_fields[field] = {
                "description": description,
                "available": True,
            }

    return {
        "ticker": normalized_ticker,
        "available_fields": available_fields,
        "total_fields": len(available_fields),
    }


TRUSTED_NEWS_DOMAINS = [
    "reuters.com",
    "bloomberg.com",
    "cnbc.com",
]


class TavilyFinancialSearchInput(BaseModel):
    """Input schema for Tavily financial search tool."""

    query: str = Field(..., description="Financial news search query (MUST be in English)")
    ticker: str = Field(..., description="Stock ticker to focus search on")


@tool("tavily_financial_search", args_schema=TavilyFinancialSearchInput)
def tavily_financial_search(
    query: str,
    ticker: str,
    tool_call_id: Annotated[str, InjectedToolCallId],
) -> dict[str, Any]:
    """Search trusted financial news domains for event-driven queries."""
    import os

    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        raise ValueError("TAVILY_API_KEY is not set.")

    try:
        writer = get_stream_writer()
    except Exception:
        writer = None

    from tavily import TavilyClient

    normalized_ticker = ticker.strip().upper()
    if writer:
        writer({"status": "searching_news", "message": f"Searching news for {normalized_ticker}...", "toolName": "tavily_financial_search", "toolCallId": tool_call_id})

    client = TavilyClient(api_key=api_key)
    full_query = f"{normalized_ticker} {query}".strip()
    response = client.search(
        query=full_query,
        include_domains=TRUSTED_NEWS_DOMAINS,
        max_results=5,
    )
    results = []
    for item in response.get("results", []):
        results.append(
            {
                "title": item.get("title"),
                "url": item.get("url"),
                "content": item.get("content"),
                "published_date": item.get("published_date"),
            }
        )
    return {"query": full_query, "results": results}
