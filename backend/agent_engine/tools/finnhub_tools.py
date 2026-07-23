"""Finnhub agent tools: real-time quote and curated fundamentals.

Two LangChain `@tool` functions backed by the `finnhub_client` domain core.
Each tool normalizes the ticker, emits an optional stream event when running in a
streaming context, and returns a plain dict. Errors bubble up as raised
exceptions (consistent with the SEC tools), handled by `_HandleToolErrors`.

There is deliberately no field-discovery tool: it would hit the same
`/stock/metric` endpoint as the fundamentals tool while returning strictly less
information, doubling the free-tier API cost of every fundamentals question.
The catalog is small enough to summarize in the tool description instead.
"""

from typing import Annotated, Any

from langchain.tools import tool
from langchain_core.tools import InjectedToolCallId
from langgraph.config import get_stream_writer
from pydantic import BaseModel, Field

from backend.agent_engine.tools.finnhub_client import (
    BASIC_FINANCIALS_CATALOG,
    fetch_basic_financials,
    fetch_quote,
)


class FinnhubStockQuoteInput(BaseModel):
    """Input schema for the Finnhub stock quote tool."""

    ticker: str = Field(..., description="Stock ticker symbol (e.g., AAPL, TSLA)")


@tool("finnhub_stock_quote", args_schema=FinnhubStockQuoteInput)
def finnhub_stock_quote(
    ticker: str,
    tool_call_id: Annotated[str, InjectedToolCallId],
) -> dict[str, Any]:
    """Retrieve real-time stock quote (price, open, prev close, change, day high/low) via Finnhub."""
    try:
        writer = get_stream_writer()
    except Exception:
        writer = None
    t = ticker.strip().upper()
    if writer:
        writer(
            {
                "status": "querying_stock",
                "message": f"Querying {t}...",
                "toolName": "finnhub_stock_quote",
                "toolCallId": tool_call_id,
            }
        )
    q = fetch_quote(t)
    return {
        "ticker": t,
        "currentPrice": q.get("c"),
        "open": q.get("o"),
        "previousClose": q.get("pc"),
        "change": q.get("d"),
        "percentChange": q.get("dp"),
        "dayHigh": q.get("h"),
        "dayLow": q.get("l"),
    }


class FinnhubCompanyBasicFinancialsInput(BaseModel):
    """Input schema for the Finnhub company basic financials tool."""

    ticker: str = Field(..., description="Stock ticker symbol (e.g., AAPL, TSLA)")


@tool(
    "finnhub_company_basic_financials",
    args_schema=FinnhubCompanyBasicFinancialsInput,
)
def finnhub_company_basic_financials(
    ticker: str,
    tool_call_id: Annotated[str, InjectedToolCallId],
) -> dict[str, Any]:
    """Retrieve curated company fundamentals for a ticker via Finnhub.

    Covers valuation (trailing/forward P/E, P/S, P/B, market cap, enterprise
    value), 52-week high/low, profitability (gross/operating/net margins, EPS,
    ROE, ROA), leverage and liquidity (debt-to-equity, current/quick ratio),
    growth (revenue and EPS TTM YoY), dividend yield, beta, and average volume.
    Returns only the fields Finnhub actually has for this ticker.
    """
    try:
        writer = get_stream_writer()
    except Exception:
        writer = None
    t = ticker.strip().upper()
    if writer:
        writer(
            {
                "status": "querying_financials",
                "message": f"Querying financials for {t}...",
                "toolName": "finnhub_company_basic_financials",
                "toolCallId": tool_call_id,
            }
        )
    metric = fetch_basic_financials(t)
    out: dict[str, Any] = {"ticker": t}
    for out_key, spec in BASIC_FINANCIALS_CATALOG.items():
        if spec.metric_key in metric and metric[spec.metric_key] is not None:
            out[out_key] = metric[spec.metric_key]
    return out
