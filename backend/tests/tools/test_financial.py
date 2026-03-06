"""Tests for financial tools."""

from backend.agent_engine.tools.financial import (
    yfinance_stock_quote,
    yfinance_get_available_fields,
    tavily_financial_search,
)


def test_yfinance_tool_exists():
    """Test yfinance tool can be imported."""
    assert yfinance_stock_quote is not None
    assert hasattr(yfinance_stock_quote, "invoke")


def test_yfinance_get_available_fields_exists():
    """Test yfinance_get_available_fields tool exists."""
    assert yfinance_get_available_fields is not None
    assert hasattr(yfinance_get_available_fields, "invoke")


def test_tavily_tool_exists():
    """Test tavily tool can be imported."""
    assert tavily_financial_search is not None
    assert hasattr(tavily_financial_search, "invoke")
