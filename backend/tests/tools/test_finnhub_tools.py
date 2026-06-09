"""Tests for Finnhub financial tools."""

import json
import os
from unittest.mock import MagicMock, patch

import pytest

from backend.agent_engine.tools.finnhub_client import (
    BASIC_FINANCIALS_CATALOG,
    fetch_basic_financials,
    fetch_quote,
)
from backend.agent_engine.tools.finnhub_tools import (
    finnhub_company_basic_financials,
    finnhub_get_available_fields,
    finnhub_stock_quote,
)

_SEAM = "backend.agent_engine.tools.finnhub_client.get_finnhub_client"


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


def _mock_client(quote=None, basic_financials=None) -> MagicMock:
    """Build a MagicMock Finnhub client with canned return values."""
    client = MagicMock()
    if quote is not None:
        client.quote.return_value = quote
    if basic_financials is not None:
        client.company_basic_financials.return_value = basic_financials
    return client


def test_finnhub_stock_quote_happy_path():
    quote = {
        "c": 190.5,
        "o": 188.0,
        "pc": 187.0,
        "d": 3.5,
        "dp": 1.87,
        "h": 191.0,
        "l": 186.5,
        "t": 1700000000,
    }
    with patch(_SEAM, return_value=_mock_client(quote=quote)):
        result = _tool_call(finnhub_stock_quote, {"ticker": "aapl"})

    assert result["ticker"] == "AAPL"
    assert result["currentPrice"] == 190.5
    assert result["open"] == 188.0
    assert result["previousClose"] == 187.0
    assert result["change"] == 3.5
    assert result["percentChange"] == 1.87
    assert result["dayHigh"] == 191.0
    assert result["dayLow"] == 186.5


def test_finnhub_stock_quote_invalid_ticker_all_zero_raises():
    all_zero = {"c": 0, "o": 0, "pc": 0, "d": 0, "dp": 0, "h": 0, "l": 0, "t": 0}
    with patch(_SEAM, return_value=_mock_client(quote=all_zero)):
        with pytest.raises(ValueError, match="invalid"):
            _tool_call(finnhub_stock_quote, {"ticker": "ZZZZ"})


def test_finnhub_company_basic_financials_happy_present_only():
    metric = {
        "52WeekHigh": 200.0,
        "52WeekLow": 150.0,
        "peTTM": 28.4,
        "beta": 1.2,
        "roeTTM": None,  # present but None -> excluded
    }
    with patch(_SEAM, return_value=_mock_client(basic_financials={"metric": metric})):
        result = _tool_call(finnhub_company_basic_financials, {"ticker": "aapl"})

    assert result["ticker"] == "AAPL"
    assert result["fiftyTwoWeekHigh"] == 200.0
    assert result["fiftyTwoWeekLow"] == 150.0
    assert result["peTTM"] == 28.4
    assert result["beta"] == 1.2
    # None-valued metric is excluded
    assert "roeTTM" not in result
    # Catalog fields absent from the API payload are excluded
    assert "marketCap" not in result
    assert "psTTM" not in result


def test_finnhub_company_basic_financials_empty_metric_raises():
    with patch(_SEAM, return_value=_mock_client(basic_financials={"metric": {}})):
        with pytest.raises(ValueError, match="basic financials"):
            _tool_call(finnhub_company_basic_financials, {"ticker": "ZZZZ"})


def test_finnhub_get_available_fields_lists_present_fields():
    metric = {
        "peTTM": 28.4,
        "beta": 1.2,
    }
    with patch(_SEAM, return_value=_mock_client(basic_financials={"metric": metric})):
        result = _tool_call(finnhub_get_available_fields, {"ticker": "aapl"})

    assert result["ticker"] == "AAPL"
    assert result["total_fields"] == 2
    assert set(result["available_fields"].keys()) == {"peTTM", "beta"}
    assert result["available_fields"]["peTTM"]["available"] is True
    assert result["available_fields"]["peTTM"]["description"] == (
        "Trailing twelve-month P/E ratio"
    )
    assert result["available_fields"]["beta"]["description"] == "Beta coefficient"


def test_finnhub_stock_quote_missing_api_key_raises():
    with patch.dict(os.environ, {}, clear=True):
        with pytest.raises(ValueError, match="FINNHUB_API_KEY"):
            _tool_call(finnhub_stock_quote, {"ticker": "AAPL"})


def test_finnhub_ticker_normalization_uppercase():
    quote = {"c": 100.0, "pc": 99.0, "o": 99.5, "d": 1.0, "dp": 1.0, "h": 101.0, "l": 98.0}
    client = _mock_client(quote=quote)
    with patch(_SEAM, return_value=client):
        result = _tool_call(finnhub_stock_quote, {"ticker": "aapl"})

    assert result["ticker"] == "AAPL"
    client.quote.assert_called_once_with("AAPL")


def test_finnhub_tools_work_without_stream_writer():
    """Tools must tolerate non-streaming context where get_stream_writer() raises."""
    quote = {"c": 190.5, "pc": 187.0, "o": 188.0, "d": 3.5, "dp": 1.87, "h": 191.0, "l": 186.5}
    with patch(_SEAM, return_value=_mock_client(quote=quote)):
        result = _tool_call(finnhub_stock_quote, {"ticker": "AAPL"})

    assert result["ticker"] == "AAPL"
    assert result["currentPrice"] == 190.5


@pytest.mark.finnhub_integration
@pytest.mark.skipif(not os.getenv("FINNHUB_API_KEY"), reason="needs FINNHUB_API_KEY")
def test_live_quote_known_ticker():
    q = fetch_quote("AAPL")
    assert q["c"] and q["c"] > 0


@pytest.mark.finnhub_integration
@pytest.mark.skipif(not os.getenv("FINNHUB_API_KEY"), reason="needs FINNHUB_API_KEY")
def test_live_basic_financials_known_ticker():
    m = fetch_basic_financials("MSFT")
    assert "peTTM" in m or "52WeekHigh" in m


@pytest.mark.finnhub_integration
@pytest.mark.skipif(not os.getenv("FINNHUB_API_KEY"), reason="needs FINNHUB_API_KEY")
def test_live_catalog_metric_keys_resolve():
    """Guard the curated catalog spelling against the real free-tier response.

    The catalog's Finnhub metric keys are data-driven strings (literal slash in
    `totalDebt/totalEquityQuarterly`, leading digit in `10DayAverageTradingVolume`,
    mixed Quarterly/TTM suffixes) that no SDK or schema enumerates. A silent typo
    would be dropped by the present-only filter with no error — this test catches
    that drift for a large-cap where every field is expected to populate.
    """
    metric = fetch_basic_financials("AAPL")
    resolved = [
        out_key
        for out_key, spec in BASIC_FINANCIALS_CATALOG.items()
        if metric.get(spec.metric_key) is not None
    ]
    # All 19 resolved for AAPL when authored; allow minor day-to-day variance.
    assert len(resolved) >= 17, f"only {len(resolved)}/19 catalog keys resolved: {resolved}"


@pytest.mark.finnhub_integration
@pytest.mark.skipif(not os.getenv("FINNHUB_API_KEY"), reason="needs FINNHUB_API_KEY")
def test_live_invalid_ticker_raises():
    with pytest.raises(ValueError):
        fetch_quote("ZZZZINVALID")
