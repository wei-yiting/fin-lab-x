"""Unit tests for ``dto_builder``.

Covers both halves of the module: the info-side builders
(``build_company_row`` / ``build_market_valuation_row``) and the
statement-side builders (``build_quarterly_rows`` / ``build_annual_rows``).
"""

from datetime import date

import pandas as pd
import pytest

from backend.ingestion.quant_data_pipeline.duck_db.row_models import (
    CompanyRow,
    YFinanceAnnualRow,
    YFinanceQuarterlyRow,
)
from backend.ingestion.quant_data_pipeline.yfinance.dto_builder import (
    build_annual_rows,
    build_company_row,
    build_market_valuation_row,
    build_quarterly_rows,
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


# ---------------------------------------------------------------------------
# build_quarterly_rows / build_annual_rows shared fixtures
# ---------------------------------------------------------------------------


def _make_statement(
    line_items: dict[str, dict[pd.Timestamp, float]],
) -> pd.DataFrame:
    """Build a yfinance-shaped DataFrame from a ``{line: {period: value}}`` dict."""
    return pd.DataFrame.from_dict(line_items, orient="index")


def _msft_company() -> CompanyRow:
    return CompanyRow(
        ticker="MSFT",
        company_name="Microsoft Corporation",
        sector="Technology",
        industry="Software",
        fy_end_month=6,
        fy_end_day=30,
    )


# Four MSFT-aligned quarter ends: FY25Q2, FY25Q3, FY25Q4, FY26Q1 given
# fy_end_month=6.
_P1 = pd.Timestamp("2024-12-31")
_P2 = pd.Timestamp("2025-03-31")
_P3 = pd.Timestamp("2025-06-30")
_P4 = pd.Timestamp("2025-09-30")
_ALL_PERIODS = (_P1, _P2, _P3, _P4)


def _income_with_revenue_only(
    period_to_revenue: dict[pd.Timestamp, float],
) -> pd.DataFrame:
    """Minimal income statement with only Total Revenue populated."""
    return _make_statement({"Total Revenue": period_to_revenue})


def _empty_statement(periods: tuple[pd.Timestamp, ...]) -> pd.DataFrame:
    """Statement DataFrame with the right columns but no line items.

    Used as the balance / cashflow placeholder when a test only cares about
    income behavior — every dest column will be missing in the result.
    """
    return pd.DataFrame(columns=list(periods))


# ---------------------------------------------------------------------------
# 19. happy path: chronological rows
# ---------------------------------------------------------------------------


def test_build_quarterly_rows_happy_path_returns_chronological_rows():
    income = _make_statement(
        {
            "Total Revenue": {
                _P1: 60_000_000_000.0,
                _P2: 62_000_000_000.0,
                _P3: 64_000_000_000.0,
                _P4: 66_000_000_000.0,
            },
            "Net Income": {
                _P1: 20_000_000_000.0,
                _P2: 21_000_000_000.0,
                _P3: 22_000_000_000.0,
                _P4: 23_000_000_000.0,
            },
            "Diluted EPS": {
                _P1: 2.50,
                _P2: 2.65,
                _P3: 2.80,
                _P4: 2.95,
            },
        }
    )
    balance = _empty_statement(_ALL_PERIODS)
    cashflow = _empty_statement(_ALL_PERIODS)

    rows, _missing = build_quarterly_rows(
        (income, balance, cashflow), company=_msft_company()
    )

    assert [r.period_end for r in rows] == [
        date(2024, 12, 31),
        date(2025, 3, 31),
        date(2025, 6, 30),
        date(2025, 9, 30),
    ]
    # MSFT fy_end_month=6: 2024-12-31 → FY25Q2, 2025-03-31 → FY25Q3,
    # 2025-06-30 → FY25Q4, 2025-09-30 → FY26Q1.
    assert [(r.fiscal_year, r.fiscal_quarter) for r in rows] == [
        (2025, 2),
        (2025, 3),
        (2025, 4),
        (2026, 1),
    ]
    assert rows[0].total_revenue_usd == 60_000_000_000
    assert rows[0].diluted_eps == pytest.approx(2.50)


# ---------------------------------------------------------------------------
# 20. skip NaN period
# ---------------------------------------------------------------------------


def test_build_quarterly_rows_skips_nan_period():
    income = _income_with_revenue_only(
        {
            _P1: 60_000_000_000.0,
            _P2: float("nan"),
            _P3: 64_000_000_000.0,
            _P4: 66_000_000_000.0,
        }
    )
    balance = _empty_statement(_ALL_PERIODS)
    cashflow = _empty_statement(_ALL_PERIODS)

    rows, _missing = build_quarterly_rows(
        (income, balance, cashflow), company=_msft_company()
    )

    period_ends = {r.period_end for r in rows}
    assert len(rows) == 3
    assert date(2025, 3, 31) not in period_ends
    assert period_ends == {date(2024, 12, 31), date(2025, 6, 30), date(2025, 9, 30)}


# ---------------------------------------------------------------------------
# 21. all periods NaN → raise
# ---------------------------------------------------------------------------


def test_build_quarterly_rows_raises_when_all_periods_nan():
    income = _income_with_revenue_only(
        {p: float("nan") for p in _ALL_PERIODS}
    )
    balance = _empty_statement(_ALL_PERIODS)
    cashflow = _empty_statement(_ALL_PERIODS)

    with pytest.raises(YFinanceEmptyResponseError) as exc_info:
        build_quarterly_rows(
            (income, balance, cashflow), company=_msft_company()
        )
    msg = str(exc_info.value)
    assert "total_revenue_usd" in msg
    assert "MSFT" in msg


# ---------------------------------------------------------------------------
# 22. empty DataFrame → raise
# ---------------------------------------------------------------------------


def test_build_quarterly_rows_raises_when_dataframe_is_empty():
    income = pd.DataFrame()
    balance = pd.DataFrame()
    cashflow = pd.DataFrame()

    with pytest.raises(YFinanceEmptyResponseError) as exc_info:
        build_quarterly_rows(
            (income, balance, cashflow), company=_msft_company()
        )
    assert "total_revenue_usd" in str(exc_info.value)


# ---------------------------------------------------------------------------
# 23. per-stage missing dedup
# ---------------------------------------------------------------------------


def test_build_quarterly_rows_per_stage_missing_dedup_interest_income():
    income = _make_statement(
        {
            "Total Revenue": {
                _P1: 60_000_000_000.0,
                _P2: 62_000_000_000.0,
                _P3: 64_000_000_000.0,
                _P4: 66_000_000_000.0,
            },
            # Interest Income present for 2 of the 4 periods.
            "Interest Income": {
                _P1: 500_000_000.0,
                _P2: float("nan"),
                _P3: 520_000_000.0,
                _P4: float("nan"),
            },
        }
    )
    balance = _empty_statement(_ALL_PERIODS)
    cashflow = _empty_statement(_ALL_PERIODS)

    _rows, missing = build_quarterly_rows(
        (income, balance, cashflow), company=_msft_company()
    )

    assert missing.count("interest_income_usd") == 1


# ---------------------------------------------------------------------------
# 24. skipped period contributes nothing to missing
# ---------------------------------------------------------------------------


def test_build_quarterly_rows_skipped_period_does_not_contribute_missing():
    # P2's Total Revenue is NaN → P2 is skipped.
    # P2 has a unique balance-sheet line item ("Net Debt") that does NOT
    # appear for any other period. If the skipped-period contribution rule
    # is broken, "net_debt_usd" would still be in missing because P2 has
    # NaN there. Since we only have one fully-valid period (P3) where
    # Net Debt IS populated, "net_debt_usd" must NOT show up in missing.
    income = _income_with_revenue_only(
        {
            _P1: float("nan"),
            _P2: float("nan"),
            _P3: 64_000_000_000.0,
            _P4: float("nan"),
        }
    )
    balance = _make_statement(
        {
            "Net Debt": {_P3: 50_000_000_000.0},
        }
    )
    cashflow = _empty_statement((_P3,))

    rows, missing = build_quarterly_rows(
        (income, balance, cashflow), company=_msft_company()
    )

    assert len(rows) == 1
    assert rows[0].net_debt_usd == 50_000_000_000
    assert "net_debt_usd" not in missing


# ---------------------------------------------------------------------------
# 25. deferred revenue fallback chain
# ---------------------------------------------------------------------------


def test_build_quarterly_rows_deferred_revenue_uses_fallback():
    income = _income_with_revenue_only({_P3: 64_000_000_000.0})
    balance = _make_statement(
        {
            # Note: no "Deferred Revenue" row at all.
            "Current Deferred Revenue": {_P3: 12_345_000_000.0},
        }
    )
    cashflow = _empty_statement((_P3,))

    rows, missing = build_quarterly_rows(
        (income, balance, cashflow), company=_msft_company()
    )

    assert len(rows) == 1
    assert rows[0].deferred_revenue_usd == 12_345_000_000
    assert "deferred_revenue_usd" not in missing


# ---------------------------------------------------------------------------
# 26. deferred revenue both missing
# ---------------------------------------------------------------------------


def test_build_quarterly_rows_deferred_revenue_both_missing():
    income = _income_with_revenue_only({_P3: 64_000_000_000.0})
    balance = _empty_statement((_P3,))
    cashflow = _empty_statement((_P3,))

    rows, missing = build_quarterly_rows(
        (income, balance, cashflow), company=_msft_company()
    )

    assert rows[0].deferred_revenue_usd is None
    assert "deferred_revenue_usd" in missing


# ---------------------------------------------------------------------------
# 27. sign preservation for capex
# ---------------------------------------------------------------------------


def test_build_quarterly_rows_capex_preserves_negative_sign():
    income = _income_with_revenue_only({_P3: 64_000_000_000.0})
    balance = _empty_statement((_P3,))
    cashflow = _make_statement(
        {"Capital Expenditure": {_P3: -5_000_000_000.0}}
    )

    rows, _missing = build_quarterly_rows(
        (income, balance, cashflow), company=_msft_company()
    )

    assert rows[0].capital_expenditure_usd == -5_000_000_000


# ---------------------------------------------------------------------------
# 28. uses company.fy_end_month for normalize
# ---------------------------------------------------------------------------


def test_build_quarterly_rows_uses_company_fy_end_month_for_normalize():
    # NVDA-like: fy_end_month=1 → 2025-10-26 falls in FY26Q3.
    nvda = CompanyRow(
        ticker="NVDA",
        company_name="NVIDIA Corporation",
        sector="Technology",
        industry="Semiconductors",
        fy_end_month=1,
        fy_end_day=25,
    )
    period = pd.Timestamp("2025-10-26")
    income = _income_with_revenue_only({period: 35_000_000_000.0})
    balance = _empty_statement((period,))
    cashflow = _empty_statement((period,))

    rows, _missing = build_quarterly_rows((income, balance, cashflow), company=nvda)

    assert rows[0].fiscal_year == 2026
    assert rows[0].fiscal_quarter == 3


# ---------------------------------------------------------------------------
# 29. diluted_eps stays a float (not rounded)
# ---------------------------------------------------------------------------


def test_build_quarterly_rows_diluted_eps_is_float():
    income = _make_statement(
        {
            "Total Revenue": {_P3: 64_000_000_000.0},
            "Diluted EPS": {_P3: 3.42},
        }
    )
    balance = _empty_statement((_P3,))
    cashflow = _empty_statement((_P3,))

    rows, _missing = build_quarterly_rows(
        (income, balance, cashflow), company=_msft_company()
    )

    assert rows[0].diluted_eps == pytest.approx(3.42)
    assert isinstance(rows[0].diluted_eps, float)


# ---------------------------------------------------------------------------
# 30. int columns rounded
# ---------------------------------------------------------------------------


def test_build_quarterly_rows_int_fields_are_rounded():
    income = _make_statement(
        {"Total Revenue": {_P3: 89_123_456_789.5}}
    )
    balance = _empty_statement((_P3,))
    cashflow = _empty_statement((_P3,))

    rows, _missing = build_quarterly_rows(
        (income, balance, cashflow), company=_msft_company()
    )

    # 89_123_456_789.5 rounds to 89_123_456_790 under banker's rounding
    # (Python's built-in round): .5 → nearest even, and 790 is even.
    assert rows[0].total_revenue_usd == 89_123_456_790
    assert isinstance(rows[0].total_revenue_usd, int)


# ---------------------------------------------------------------------------
# 31. annual row has no fiscal_quarter
# ---------------------------------------------------------------------------


def test_build_annual_rows_drops_fiscal_quarter_field():
    # Annual periods: yfinance returns one row per FY end. Use MSFT FY24 / FY25.
    p_fy24 = pd.Timestamp("2024-06-30")
    p_fy25 = pd.Timestamp("2025-06-30")
    income = _income_with_revenue_only(
        {p_fy24: 245_000_000_000.0, p_fy25: 260_000_000_000.0}
    )
    balance = _empty_statement((p_fy24, p_fy25))
    cashflow = _empty_statement((p_fy24, p_fy25))

    rows, _missing = build_annual_rows(
        (income, balance, cashflow), company=_msft_company()
    )

    assert all(isinstance(r, YFinanceAnnualRow) for r in rows)
    assert not hasattr(rows[0], "fiscal_quarter")


# ---------------------------------------------------------------------------
# 32. annual normalize_period
# ---------------------------------------------------------------------------


def test_build_annual_rows_uses_annual_normalize_period():
    # fy_end_month=12 means calendar year == fiscal year.
    aapl_like = CompanyRow(
        ticker="ACME",
        company_name="Acme Corp",
        sector=None,
        industry=None,
        fy_end_month=12,
        fy_end_day=31,
    )
    period = pd.Timestamp("2024-12-31")
    income = _income_with_revenue_only({period: 100_000_000_000.0})
    balance = _empty_statement((period,))
    cashflow = _empty_statement((period,))

    rows, _missing = build_annual_rows(
        (income, balance, cashflow), company=aapl_like
    )

    assert rows[0].fiscal_year == 2024


# ---------------------------------------------------------------------------
# 33. annual: dedup + skip mirrors quarterly
# ---------------------------------------------------------------------------


def test_build_annual_rows_per_stage_dedup_and_skip_consistent_with_quarterly():
    p_fy23 = pd.Timestamp("2023-06-30")
    p_fy24 = pd.Timestamp("2024-06-30")
    p_fy25 = pd.Timestamp("2025-06-30")

    income = _make_statement(
        {
            "Total Revenue": {
                p_fy23: float("nan"),  # skipped
                p_fy24: 245_000_000_000.0,
                p_fy25: 260_000_000_000.0,
            },
            # Missing from both materialized years → recorded once.
            "Interest Income": {
                p_fy24: float("nan"),
                p_fy25: float("nan"),
            },
        }
    )
    balance = _empty_statement((p_fy23, p_fy24, p_fy25))
    cashflow = _empty_statement((p_fy23, p_fy24, p_fy25))

    rows, missing = build_annual_rows(
        (income, balance, cashflow), company=_msft_company()
    )

    assert len(rows) == 2
    assert all(isinstance(r, YFinanceAnnualRow) for r in rows)
    assert [r.period_end for r in rows] == [date(2024, 6, 30), date(2025, 6, 30)]
    assert missing.count("interest_income_usd") == 1
    # sorted() output is deduped + sorted
    assert missing == sorted(set(missing))


# ---------------------------------------------------------------------------
# Sanity: quarterly row instances are the right class
# ---------------------------------------------------------------------------


def test_build_quarterly_rows_returns_quarterly_row_instances():
    income = _income_with_revenue_only({_P3: 64_000_000_000.0})
    balance = _empty_statement((_P3,))
    cashflow = _empty_statement((_P3,))

    rows, _missing = build_quarterly_rows(
        (income, balance, cashflow), company=_msft_company()
    )

    assert all(isinstance(r, YFinanceQuarterlyRow) for r in rows)
