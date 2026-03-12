"""Financial data tools for FinLab-X."""

from typing import Any
import yfinance as yf
from pydantic import BaseModel, Field
from langchain.tools import tool

from backend.agent_engine.observability.langsmith_tracer import trace_step


class YFinanceStockQuoteInput(BaseModel):
    """Input schema for yfinance stock quote tool."""

    ticker: str = Field(..., description="Stock ticker symbol (e.g., AAPL, TSLA)")


@tool("yfinance_stock_quote", args_schema=YFinanceStockQuoteInput)
@trace_step(step_name="yfinance_stock_quote", tags=["tool:yfinance", "version:0.1.0"])
def yfinance_stock_quote(ticker: str) -> dict[str, Any]:
    """Retrieve real-time quantitative stock metrics using yfinance."""
    try:
        normalized_ticker = ticker.strip().upper()
        info = yf.Ticker(normalized_ticker).info
        return {
            "ticker": normalized_ticker,
            "currentPrice": info.get("currentPrice"),
            "fiftyTwoWeekHigh": info.get("fiftyTwoWeekHigh"),
            "fiftyTwoWeekLow": info.get("fiftyTwoWeekLow"),
            "forwardPE": info.get("forwardPE"),
            "trailingPE": info.get("trailingPE"),
        }
    except (KeyError, ValueError, ConnectionError, TimeoutError) as exc:
        return {
            "error": True,
            "message": f"Could not retrieve data from yfinance: {exc}",
        }


class YFinanceGetAvailableFieldsInput(BaseModel):
    """Input schema for yfinance get available fields tool."""

    ticker: str = Field(
        ..., description="Stock ticker symbol to query available fields"
    )


@tool("yfinance_get_available_fields", args_schema=YFinanceGetAvailableFieldsInput)
@trace_step(
    step_name="yfinance_get_available_fields", tags=["tool:yfinance", "version:0.1.0"]
)
def yfinance_get_available_fields(ticker: str) -> dict[str, Any]:
    """Get all available data fields for a stock ticker with descriptions.

    Use this tool first to discover what data is available, then use
    yfinance_stock_quote with specific fields.

    Only returns curated fields with known descriptions to avoid wasting
    LLM tokens on unrecognized yfinance fields.
    """
    try:
        normalized_ticker = ticker.strip().upper()
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
    except (KeyError, ValueError, ConnectionError, TimeoutError) as exc:
        return {"error": True, "message": f"Could not fetch available fields: {exc}"}


TRUSTED_NEWS_DOMAINS = [
    "reuters.com",
    "bloomberg.com",
    "cnbc.com",
]


class TavilyFinancialSearchInput(BaseModel):
    """Input schema for Tavily financial search tool."""

    query: str = Field(..., description="Financial news search query")
    ticker: str = Field(..., description="Stock ticker to focus search on")


@tool("tavily_financial_search", args_schema=TavilyFinancialSearchInput)
@trace_step(step_name="tavily_financial_search", tags=["tool:tavily", "version:0.1.0"])
def tavily_financial_search(query: str, ticker: str) -> dict[str, Any]:
    """Search trusted financial news domains for event-driven queries."""
    import os

    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        return {"error": True, "message": "TAVILY_API_KEY is not set."}

    try:
        from tavily import TavilyClient

        normalized_ticker = ticker.strip().upper()
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
    except (KeyError, ValueError, ConnectionError, TimeoutError) as exc:
        return {"error": True, "message": f"Could not retrieve data from Tavily: {exc}"}
