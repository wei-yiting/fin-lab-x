from __future__ import annotations

import os
import re
from typing import Any, Literal

from langchain_core.tools import tool
from pydantic import BaseModel, Field

TRUSTED_NEWS_DOMAINS = [
    "reuters.com",
    "bloomberg.com",
    "cnbc.com",
]

MAX_SECTION_CHARS = 4000


class TavilyFinancialSearchInput(BaseModel):
    query: str = Field(
        ..., description="The specific financial event, news, or qualitative question."
    )
    ticker: str = Field(..., description="The target company's ticker symbol.")


class YFinanceStockQuoteInput(BaseModel):
    ticker: str = Field(..., description="The exact stock ticker symbol, e.g., 'AAPL'.")


class SecOfficialDocsRetrieverInput(BaseModel):
    ticker: str = Field(..., description="The exact stock ticker symbol, e.g., 'TSLA'.")
    doc_type: Literal["10-K", "10-Q"] = Field(
        "10-K",
        description="The type of document to retrieve. Defaults to 10-K if omitted.",
    )


def _normalize_ticker(ticker: str) -> str:
    return ticker.strip().upper()


def _extract_section(
    text: str, start_markers: list[str], end_markers: list[str]
) -> str | None:
    lower_text = text.lower()
    start_index = -1
    for marker in start_markers:
        idx = lower_text.find(marker.lower())
        if idx != -1 and (start_index == -1 or idx < start_index):
            start_index = idx

    if start_index == -1:
        return None

    end_index = -1
    for marker in end_markers:
        idx = lower_text.find(marker.lower(), start_index + 1)
        if idx != -1 and (end_index == -1 or idx < end_index):
            end_index = idx

    extracted = text[start_index : end_index if end_index != -1 else None].strip()
    if len(extracted) > MAX_SECTION_CHARS:
        extracted = extracted[:MAX_SECTION_CHARS].rstrip() + "..."
    return extracted


@tool("yfinance_stock_quote", args_schema=YFinanceStockQuoteInput)
def yfinance_stock_quote(ticker: str) -> dict[str, Any] | str:
    """
    Retrieve real-time quantitative stock metrics using yfinance.
    """
    try:
        import yfinance as yf

        normalized_ticker = _normalize_ticker(ticker)
        info = yf.Ticker(normalized_ticker).info
        return {
            "ticker": normalized_ticker,
            "currentPrice": info.get("currentPrice"),
            "fiftyTwoWeekHigh": info.get("fiftyTwoWeekHigh"),
            "fiftyTwoWeekLow": info.get("fiftyTwoWeekLow"),
            "forwardPE": info.get("forwardPE"),
            "trailingPE": info.get("trailingPE"),
        }
    except Exception as exc:
        return f"Error: Could not retrieve data from yfinance: {exc}"


@tool("tavily_financial_search", args_schema=TavilyFinancialSearchInput)
def tavily_financial_search(query: str, ticker: str) -> dict[str, Any] | str:
    """
    Search trusted financial news domains for event-driven queries.
    """
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        return "Error: TAVILY_API_KEY is not set."

    try:
        from tavily import TavilyClient

        normalized_ticker = _normalize_ticker(ticker)
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
    except Exception as exc:
        return f"Error: Could not retrieve data from Tavily: {exc}"


@tool("sec_official_docs_retriever", args_schema=SecOfficialDocsRetrieverInput)
def sec_official_docs_retriever(
    ticker: str, doc_type: str = "10-K"
) -> dict[str, Any] | str:
    """
    Retrieve official SEC filing text sections using edgartools.
    """
    identity = os.getenv("EDGAR_IDENTITY")
    if not identity:
        return "Error: EDGAR_IDENTITY is not set."

    try:
        from edgar import Company, set_identity

        set_identity(identity)
        normalized_ticker = _normalize_ticker(ticker)
        filings = Company(normalized_ticker).get_filings(form=doc_type)
        filing = filings.latest()
        if not filing:
            return f"Error: No {doc_type} filing found for {normalized_ticker}."

        text = filing.text()
        cleaned_text = re.sub(r"\s+", " ", text)
        risk_factors = _extract_section(
            cleaned_text,
            ["Item 1A", "Item 1A."],
            ["Item 1B", "Item 2", "Item 3"],
        )
        mdna = _extract_section(
            cleaned_text,
            ["Item 7", "Item 7."],
            ["Item 7A", "Item 8", "Item 9"],
        )

        return {
            "ticker": normalized_ticker,
            "doc_type": doc_type,
            "filing_date": getattr(filing, "filing_date", None),
            "risk_factors": risk_factors,
            "mdna": mdna,
            "raw_excerpt": cleaned_text[:MAX_SECTION_CHARS].rstrip() + "...",
        }
    except Exception as exc:
        return f"Error: Could not retrieve SEC filing data: {exc}"


V1_BASELINE_TOOLS = [
    yfinance_stock_quote,
    tavily_financial_search,
    sec_official_docs_retriever,
]
