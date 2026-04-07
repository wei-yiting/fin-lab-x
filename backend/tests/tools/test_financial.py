"""Tests for financial tools."""

import json
import os
import sys
from typing import Any, cast
from unittest.mock import MagicMock, patch

import pytest
from pydantic import ValidationError

from backend.agent_engine.tools.financial import (
    TRUSTED_NEWS_DOMAINS,
    tavily_financial_search,
    yfinance_get_available_fields,
    yfinance_stock_quote,
)


def _tool_call(tool_func, args: dict) -> dict:
    """Invoke a tool with a full ToolCall (required for InjectedToolCallId).

    Returns the parsed dict from the ToolMessage content.
    """
    msg = tool_func.invoke(
        {
            "args": args,
            "name": tool_func.name,
            "type": "tool_call",
            "id": "test-call-id",
        }
    )
    return json.loads(msg.content)


def test_yfinance_tool_exists():
    assert yfinance_stock_quote is not None
    assert hasattr(yfinance_stock_quote, "invoke")


def test_yfinance_get_available_fields_exists():
    assert yfinance_get_available_fields is not None
    assert hasattr(yfinance_get_available_fields, "invoke")


def test_tavily_tool_exists():
    assert tavily_financial_search is not None
    assert hasattr(tavily_financial_search, "invoke")


def test_yfinance_stock_quote_schema_validation():
    with pytest.raises((ValidationError, ValueError)):
        _tool_call(yfinance_stock_quote, {})


@patch("yfinance.Ticker")
def test_yfinance_stock_quote_returns_expected_fields(ticker_mock):
    info = {
        "currentPrice": 190.5,
        "fiftyTwoWeekHigh": 200.0,
        "fiftyTwoWeekLow": 150.0,
        "forwardPE": 25.1,
        "trailingPE": 28.4,
    }
    instance = MagicMock()
    instance.info = info
    ticker_mock.return_value = instance

    result = _tool_call(yfinance_stock_quote, {"ticker": "aapl"})

    assert result["ticker"] == "AAPL"
    assert result["currentPrice"] == 190.5
    assert result["fiftyTwoWeekHigh"] == 200.0
    assert result["fiftyTwoWeekLow"] == 150.0
    assert result["forwardPE"] == 25.1
    assert result["trailingPE"] == 28.4
    ticker_mock.assert_called_once_with("AAPL")


@patch("yfinance.Ticker")
def test_yfinance_stock_quote_handles_connection_error(ticker_mock):
    ticker_mock.side_effect = ConnectionError("network down")

    with pytest.raises(ConnectionError, match="network down"):
        _tool_call(yfinance_stock_quote, {"ticker": "AAPL"})


@patch("yfinance.Ticker")
def test_yfinance_get_available_fields_discovers_curated_fields(ticker_mock):
    info = {
        "symbol": "AAPL",
        "currentPrice": 101.0,
        "beta": 1.2,
        "customField": "value",
    }
    instance = MagicMock()
    instance.info = info
    ticker_mock.return_value = instance

    result = _tool_call(yfinance_get_available_fields, {"ticker": "aapl"})

    assert result["ticker"] == "AAPL"
    assert result["available_fields"]["currentPrice"]["description"] == (
        "Current stock price"
    )
    assert result["available_fields"]["beta"]["description"] == "Beta coefficient"
    assert "customField" not in result["available_fields"]
    assert result["total_fields"] == 2


@patch("yfinance.Ticker")
def test_ticker_normalization_uppercase(ticker_mock):
    instance = MagicMock()
    instance.info = {"symbol": "AAPL"}
    ticker_mock.return_value = instance

    result = _tool_call(yfinance_get_available_fields, {"ticker": "aapl"})

    assert result["ticker"] == "AAPL"
    ticker_mock.assert_called_once_with("AAPL")


@patch("yfinance.Ticker")
def test_yfinance_stock_quote_raises_on_invalid_ticker(ticker_mock):
    instance = MagicMock()
    instance.info = {"symbol": "BOGUS"}
    ticker_mock.return_value = instance

    with pytest.raises(ValueError, match="BOGUS"):
        _tool_call(yfinance_stock_quote, {"ticker": "bogus"})


@patch("yfinance.Ticker")
def test_yfinance_stock_quote_accepts_regular_market_price_fallback(ticker_mock):
    instance = MagicMock()
    instance.info = {"symbol": "AAPL", "regularMarketPrice": 185.0}
    ticker_mock.return_value = instance

    result = _tool_call(yfinance_stock_quote, {"ticker": "aapl"})

    assert result["ticker"] == "AAPL"
    assert result["currentPrice"] is None


@patch("yfinance.Ticker")
def test_yfinance_get_available_fields_raises_on_invalid_ticker(ticker_mock):
    instance = MagicMock()
    instance.info = {}
    ticker_mock.return_value = instance

    with pytest.raises(ValueError, match="BOGUS"):
        _tool_call(yfinance_get_available_fields, {"ticker": "bogus"})


def test_tavily_financial_search_missing_api_key():
    with patch.dict(os.environ, {}, clear=True):
        with pytest.raises(ValueError, match="TAVILY_API_KEY"):
            _tool_call(
                tavily_financial_search,
                {"query": "earnings", "ticker": "AAPL"},
            )


@patch("yfinance.Ticker")
def test_tools_work_without_stream_writer(ticker_mock):
    """Tools should work in non-streaming context where get_stream_writer() fails."""
    info = {"currentPrice": 190.5}
    instance = MagicMock()
    instance.info = info
    ticker_mock.return_value = instance

    result = _tool_call(yfinance_stock_quote, {"ticker": "AAPL"})

    assert result["ticker"] == "AAPL"
    assert result["currentPrice"] == 190.5


@patch.dict(os.environ, {"TAVILY_API_KEY": "test-key"}, clear=True)
@patch.dict("sys.modules", {"tavily": MagicMock()})
@patch("backend.agent_engine.tools.financial.TavilyClient", create=True)
def test_tavily_financial_search_results(tavily_client_mock):
    cast(Any, sys.modules["tavily"]).TavilyClient = tavily_client_mock
    tavily_client_mock.return_value.search.return_value = {
        "results": [
            {
                "title": "Title 1",
                "url": "https://example.com/1",
                "content": "Content 1",
                "published_date": "2024-01-01",
            },
            {
                "title": "Title 2",
                "url": "https://example.com/2",
                "content": "Content 2",
                "published_date": "2024-01-02",
            },
        ]
    }

    result = _tool_call(
        tavily_financial_search, {"query": "earnings", "ticker": "aapl"}
    )

    assert result["query"] == "AAPL earnings"
    assert len(result["results"]) == 2
    assert result["results"][0]["title"] == "Title 1"
    assert result["results"][1]["url"] == "https://example.com/2"
    tavily_client_mock.return_value.search.assert_called_once_with(
        query="AAPL earnings",
        include_domains=TRUSTED_NEWS_DOMAINS,
        max_results=5,
    )
