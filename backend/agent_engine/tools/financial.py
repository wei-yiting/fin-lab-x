"""Financial data tools for FinLab-X."""

from typing import Annotated, Any

from langchain_core.tools import InjectedToolCallId
from langgraph.config import get_stream_writer
from pydantic import BaseModel, Field
from langchain.tools import tool


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
