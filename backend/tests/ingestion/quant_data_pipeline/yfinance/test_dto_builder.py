"""Unit tests for ``dto_builder`` info-side builders.

These tests cover ``build_company_row`` and ``build_market_valuation_row`` —
the two pure transforms from yfinance ``info`` dict to foundation row models.
Statement-side builders (quarterly / annual) are covered by Task 5.
"""

from datetime import date

import pytest

from backend.ingestion.quant_data_pipeline.yfinance.dto_builder import (
    build_company_row,
    build_market_valuation_row,
)
from backend.ingestion.quant_data_pipeline.yfinance.yfinance_pipeline_errors import (
    YFinanceEmptyResponseError,
)


# ---------------------------------------------------------------------------
# build_company_row
# ---------------------------------------------------------------------------
# 1751241600 → UTC 2025-06-30 (MSFT FY end).
# 1769299200 → UTC 2026-01-25 (NVDA FY end — S-yfinance-15 mock half).

_MSFT_FY_END_UNIX = 1751241600
_NVDA_FY_END_UNIX = 1769299200


def test_build_company_row_happy_path():
    info = {
        "longName": "Microsoft Corporation",
        "sector": "Technology",
        "industry": "Software",
        "lastFiscalYearEnd": _MSFT_FY_END_UNIX,
    }
    row, missing = build_company_row(info, ticker="MSFT")

    assert row.ticker == "MSFT"
    assert row.company_name == "Microsoft Corporation"
    assert row.sector == "Technology"
    assert row.industry == "Software"
    assert row.fy_end_month == 6
    assert row.fy_end_day == 30
    assert missing == []


def test_build_company_row_nvda_fy_end_day_25():
    info = {
        "longName": "NVIDIA Corporation",
        "sector": "Technology",
        "industry": "Semiconductors",
        "lastFiscalYearEnd": _NVDA_FY_END_UNIX,
    }
    row, _missing = build_company_row(info, ticker="NVDA")

    assert row.fy_end_month == 1
    assert row.fy_end_day == 25


def test_build_company_row_raises_on_missing_lastFiscalYearEnd():
    info = {"longName": "Foo"}
    with pytest.raises(YFinanceEmptyResponseError) as exc_info:
        build_company_row(info, ticker="FOO")
    msg = str(exc_info.value)
    assert "lastFiscalYearEnd" in msg
    assert "missing" in msg


def test_build_company_row_raises_on_none_lastFiscalYearEnd():
    info = {"longName": "Foo", "lastFiscalYearEnd": None}
    with pytest.raises(YFinanceEmptyResponseError) as exc_info:
        build_company_row(info, ticker="FOO")
    msg = str(exc_info.value)
    assert "lastFiscalYearEnd" in msg
    assert "None" in msg


def test_build_company_row_raises_on_zero_lastFiscalYearEnd():
    info = {"longName": "Foo", "lastFiscalYearEnd": 0}
    with pytest.raises(YFinanceEmptyResponseError) as exc_info:
        build_company_row(info, ticker="FOO")
    msg = str(exc_info.value)
    assert "lastFiscalYearEnd" in msg
    assert "epoch" in msg


def test_build_company_row_raises_on_negative_lastFiscalYearEnd():
    info = {"longName": "Foo", "lastFiscalYearEnd": -1}
    with pytest.raises(YFinanceEmptyResponseError) as exc_info:
        build_company_row(info, ticker="FOO")
    msg = str(exc_info.value)
    assert "lastFiscalYearEnd" in msg
    assert "negative" in msg


def test_build_company_row_raises_on_missing_longName():
    info = {"lastFiscalYearEnd": _MSFT_FY_END_UNIX}
    with pytest.raises(YFinanceEmptyResponseError) as exc_info:
        build_company_row(info, ticker="FOO")
    assert "longName" in str(exc_info.value)


def test_build_company_row_treats_empty_longName_as_missing():
    info = {"longName": "", "lastFiscalYearEnd": _MSFT_FY_END_UNIX}
    with pytest.raises(YFinanceEmptyResponseError) as exc_info:
        build_company_row(info, ticker="FOO")
    assert "longName" in str(exc_info.value)


def test_build_company_row_collects_missing_optional_industry():
    info = {
        "longName": "Foo Inc",
        "sector": "Technology",
        "lastFiscalYearEnd": _MSFT_FY_END_UNIX,
    }
    row, missing = build_company_row(info, ticker="FOO")

    assert row.industry is None
    assert "industry" in missing


def test_build_company_row_collects_missing_optional_sector():
    info = {
        "longName": "Foo Inc",
        "industry": "Software",
        "lastFiscalYearEnd": _MSFT_FY_END_UNIX,
    }
    row, missing = build_company_row(info, ticker="FOO")

    assert row.sector is None
    assert "sector" in missing


# ---------------------------------------------------------------------------
# build_market_valuation_row
# ---------------------------------------------------------------------------


def _full_market_valuation_info() -> dict:
    """All 11 mapping keys populated with plausible values."""
    return {
        "marketCap": 3_000_000_000_000,
        "enterpriseValue": 3_100_000_000_000,
        "trailingPE": 35.5,
        "forwardPE": 30.1,
        "priceToBook": 12.3,
        "priceToSalesTrailing12Months": 11.2,
        "enterpriseToEbitda": 22.7,
        "trailingPegRatio": 2.4,
        "dividendYield": 0.74,
        "beta": 1.05,
        "heldPercentInstitutions": 0.7598,
    }


def test_build_market_valuation_row_uses_today_param():
    info = _full_market_valuation_info()
    row, _missing = build_market_valuation_row(
        info, ticker="MSFT", today=date(2026, 5, 4)
    )
    assert row.as_of_date == date(2026, 5, 4)


def test_build_market_valuation_row_happy_path_all_fields_present():
    info = _full_market_valuation_info()
    row, missing = build_market_valuation_row(
        info, ticker="MSFT", today=date(2026, 5, 4)
    )

    assert row.ticker == "MSFT"
    assert row.market_cap_usd == 3_000_000_000_000
    assert row.enterprise_value_usd == 3_100_000_000_000
    assert row.trailing_price_to_earnings == pytest.approx(35.5)
    assert row.forward_price_to_earnings == pytest.approx(30.1)
    assert row.price_to_book_ratio == pytest.approx(12.3)
    assert row.price_to_sales_trailing_12m == pytest.approx(11.2)
    assert row.ev_to_ebitda_ratio == pytest.approx(22.7)
    assert row.trailing_peg_ratio == pytest.approx(2.4)
    assert row.dividend_yield_pct == pytest.approx(0.74)
    assert row.beta == pytest.approx(1.05)
    assert row.held_pct_institutions == pytest.approx(75.98)
    assert missing == []


def test_build_market_valuation_row_held_pct_x100():
    info = {"heldPercentInstitutions": 0.7598}
    row, _missing = build_market_valuation_row(
        info, ticker="MSFT", today=date(2026, 5, 4)
    )
    assert row.held_pct_institutions == pytest.approx(75.98)


def test_build_market_valuation_row_held_pct_drift_value():
    info = {"heldPercentInstitutions": 75.98}
    row, _missing = build_market_valuation_row(
        info, ticker="MSFT", today=date(2026, 5, 4)
    )
    assert row.held_pct_institutions == pytest.approx(7598.0)


def test_build_market_valuation_row_dividend_yield_no_conversion():
    info = {"dividendYield": 2.61}
    row, _missing = build_market_valuation_row(
        info, ticker="MSFT", today=date(2026, 5, 4)
    )
    assert row.dividend_yield_pct == pytest.approx(2.61)


def test_build_market_valuation_row_collects_missing_marketCap_when_key_absent():
    info = _full_market_valuation_info()
    del info["marketCap"]
    row, missing = build_market_valuation_row(
        info, ticker="MSFT", today=date(2026, 5, 4)
    )

    assert row.market_cap_usd is None
    assert "market_cap_usd" in missing


def test_build_market_valuation_row_treats_none_as_missing():
    info = _full_market_valuation_info()
    info["marketCap"] = None
    row, missing = build_market_valuation_row(
        info, ticker="MSFT", today=date(2026, 5, 4)
    )

    assert row.market_cap_usd is None
    assert "market_cap_usd" in missing


def test_build_market_valuation_row_treats_nan_as_missing():
    info = _full_market_valuation_info()
    info["marketCap"] = float("nan")
    row, missing = build_market_valuation_row(
        info, ticker="MSFT", today=date(2026, 5, 4)
    )

    assert row.market_cap_usd is None
    assert "market_cap_usd" in missing
