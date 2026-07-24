"""Finnhub domain core: client seam, fetch functions, and field catalog.

Pure domain layer with no LangChain dependency. `get_finnhub_client` is the
patch seam for tests; the fetch functions encode Finnhub's free-tier quirk that
invalid tickers do not raise (quote returns all-zero values, basic financials
returns an empty metric map) and translate those into `ValueError`.
"""

import os
from typing import Any, NamedTuple

import finnhub


class FieldSpec(NamedTuple):
    metric_key: str
    description: str


# output key -> (Finnhub `metric` key, neutral English description)
# Unit conventions (verified against live free-tier responses): ratio/margin/yield
# values are percentages (47.86 means 47.86%), unlike the response's `series`
# section which uses fractions; monetary aggregates (marketCapitalization,
# enterpriseValue) are millions of the issuer's reporting currency, not USD.
BASIC_FINANCIALS_CATALOG: dict[str, FieldSpec] = {
    "fiftyTwoWeekHigh": FieldSpec("52WeekHigh", "52-week high price"),
    "fiftyTwoWeekLow": FieldSpec("52WeekLow", "52-week low price"),
    "peTTM": FieldSpec("peTTM", "Trailing twelve-month P/E ratio"),
    "forwardPE": FieldSpec("forwardPE", "Forward P/E ratio"),
    "psTTM": FieldSpec("psTTM", "Trailing twelve-month price-to-sales"),
    "pb": FieldSpec("pbQuarterly", "Price-to-book ratio"),
    "marketCap": FieldSpec(
        "marketCapitalization", "Market capitalization (millions of reporting currency)"
    ),
    "enterpriseValue": FieldSpec(
        "enterpriseValue", "Enterprise value (millions of reporting currency)"
    ),
    "beta": FieldSpec("beta", "Beta coefficient"),
    "epsTTM": FieldSpec("epsTTM", "Earnings per share (TTM)"),
    "roeTTM": FieldSpec("roeTTM", "Return on equity (TTM)"),
    "roaTTM": FieldSpec("roaTTM", "Return on assets (TTM)"),
    "grossMarginTTM": FieldSpec("grossMarginTTM", "Gross margin (TTM)"),
    "netProfitMarginTTM": FieldSpec("netProfitMarginTTM", "Net profit margin (TTM)"),
    "operatingMarginTTM": FieldSpec("operatingMarginTTM", "Operating margin (TTM)"),
    "currentRatio": FieldSpec("currentRatioQuarterly", "Current ratio"),
    "quickRatio": FieldSpec("quickRatioQuarterly", "Quick ratio"),
    "debtToEquity": FieldSpec("totalDebt/totalEquityQuarterly", "Debt-to-equity ratio"),
    "dividendYield": FieldSpec(
        "dividendYieldIndicatedAnnual", "Indicated annual dividend yield"
    ),
    "revenueGrowthTTMYoy": FieldSpec("revenueGrowthTTMYoy", "Revenue growth (TTM YoY)"),
    "epsGrowthTTMYoy": FieldSpec("epsGrowthTTMYoy", "EPS growth (TTM YoY)"),
    "tenDayAvgVolume": FieldSpec(
        "10DayAverageTradingVolume", "10-day average trading volume"
    ),
}


def get_finnhub_client() -> finnhub.Client:
    api_key = os.getenv("FINNHUB_API_KEY")
    if not api_key:
        raise ValueError("FINNHUB_API_KEY is not set.")
    return finnhub.Client(api_key=api_key)


def fetch_quote(symbol: str) -> dict[str, Any]:
    data = get_finnhub_client().quote(symbol)
    # Finnhub's free tier returns an all-zero payload (not an error) for unknown
    # tickers. Require BOTH current and previous-close to be 0/None: checking `c`
    # alone would false-positive a legitimately-zero pre-market price.
    if not data or (data.get("c") in (0, None) and data.get("pc") in (0, None)):
        raise ValueError(
            f"No quote data for ticker '{symbol}'. The symbol may be invalid, "
            f"delisted, or not covered by Finnhub free tier."
        )
    return data


def fetch_basic_financials(symbol: str) -> dict[str, Any]:
    data = get_finnhub_client().company_basic_financials(symbol, "all")
    metric = (data or {}).get("metric") or {}
    if not metric:
        raise ValueError(
            f"No basic financials for ticker '{symbol}'. The symbol may be "
            f"invalid or not covered by Finnhub free tier."
        )
    return metric
