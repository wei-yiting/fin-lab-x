"""Behaviour of the semantic-layer views and the period_metrics macro (ADR-0023)."""

from datetime import date
from typing import Any

import pytest

from backend.ingestion.fundamentals_pipeline.duck_db.row_models import (
    CompanyRow,
    YFinanceAnnualRow,
    YFinanceQuarterlyRow,
)
from backend.ingestion.fundamentals_pipeline.duck_db.upsert import upsert_rows


def _quarter(ticker: str, fy: int, fq: int, end: date, **values: Any):
    return YFinanceQuarterlyRow(
        ticker=ticker, fiscal_year=fy, fiscal_quarter=fq, period_end=end, **values
    )


def _insert(conn, *rows: YFinanceQuarterlyRow, fye_month: int = 12) -> None:
    companies = [
        CompanyRow(ticker=t, company_name=t, fy_end_month=fye_month, fy_end_day=28)
        for t in sorted({r.ticker for r in rows})
    ]
    upsert_rows(conn, "companies", ["ticker"], companies)
    upsert_rows(
        conn, "quarterly_financials", ["ticker", "fiscal_year", "fiscal_quarter"], rows
    )


def test_quarterly_ratios(tmp_duckdb):
    _insert(
        tmp_duckdb,
        _quarter(
            "AAA", 2026, 1, date(2026, 3, 31),
            total_revenue_usd=200, gross_profit_usd=90, operating_income_usd=50,
            net_income_usd=30, free_cash_flow_usd=40, research_and_development_usd=20,
            total_debt_usd=300, stockholders_equity_usd=150,
            current_assets_usd=120, current_liabilities_usd=80,
        ),
    )  # fmt: skip
    row = tmp_duckdb.execute(
        "SELECT gross_margin_pct, operating_margin_pct, net_margin_pct, fcf_margin_pct,"
        " rd_to_revenue_pct, debt_to_equity, current_ratio FROM quarterly_metrics"
    ).fetchone()
    assert row == pytest.approx((45.0, 25.0, 15.0, 20.0, 10.0, 2.0, 1.5))


def test_ratio_is_null_when_part_missing_or_denominator_zero(tmp_duckdb):
    _insert(
        tmp_duckdb,
        _quarter("BANK", 2026, 1, date(2026, 3, 31), total_revenue_usd=100),
        _quarter("ZERO", 2026, 1, date(2026, 3, 31), total_revenue_usd=0,
                 gross_profit_usd=0),
    )  # fmt: skip
    assert tmp_duckdb.execute(
        "SELECT ticker, gross_margin_pct FROM quarterly_metrics ORDER BY ticker"
    ).fetchall() == [("BANK", None), ("ZERO", None)]


@pytest.mark.parametrize(
    "fye_month, fiscal_year, fiscal_quarter, period_end, expected",
    [
        pytest.param(12, 2026, 1, date(2026, 3, 31), (2026, 1), id="calendar-FYE"),
        pytest.param(9, 2026, 3, date(2026, 6, 30), (2026, 2), id="AAPL-FY-Q3-Apr-Jun"),
        pytest.param(1, 2027, 1, date(2026, 4, 30), (2026, 1), id="NVDA-Feb-Apr"),
        pytest.param(1, 2026, 4, date(2026, 1, 31), (2025, 4), id="Nov-Jan-prior-year"),
        pytest.param(6, 2027, 1, date(2026, 9, 30), (2026, 3), id="MSFT-FY27-Q1"),
        pytest.param(8, 2024, 4, date(2024, 9, 1), (2024, 3), id="COST-5253wk-drift"),
    ],
)
def test_calendar_quarter_by_middle_month(
    tmp_duckdb, fye_month, fiscal_year, fiscal_quarter, period_end, expected
):
    _insert(
        tmp_duckdb,
        _quarter("AAA", fiscal_year, fiscal_quarter, period_end, total_revenue_usd=1),
        fye_month=fye_month,
    )
    assert (
        tmp_duckdb.execute(
            "SELECT calendar_year, calendar_quarter FROM quarterly_metrics"
        ).fetchone()
        == expected
    )


def test_window_over_period_end_with_calendar_columns(tmp_duckdb):
    """Regression: DuckDB 1.5.2 INTERNAL binder error when a calendar column was
    computed from period_end and the query ordered a window by period_end."""
    _two_quarters(tmp_duckdb)
    rows = tmp_duckdb.execute(
        "SELECT ticker, period_end, calendar_year, calendar_quarter"
        " FROM quarterly_metrics WHERE ticker = 'AAA'"
        " QUALIFY row_number() OVER (PARTITION BY ticker ORDER BY period_end DESC) = 1"
    ).fetchall()
    assert rows == [("AAA", date(2026, 6, 30), 2026, 2)]


def _two_quarters(conn) -> None:
    _insert(
        conn,
        _quarter("AAA", 2026, 1, date(2026, 3, 31), total_revenue_usd=100,
                 gross_profit_usd=10, total_assets_usd=1000),
        _quarter("AAA", 2026, 2, date(2026, 6, 30), total_revenue_usd=300,
                 gross_profit_usd=90, total_assets_usd=1200),
    )  # fmt: skip


def test_period_metrics_sums_flows_takes_last_stock_and_recomputes_ratio(tmp_duckdb):
    _two_quarters(tmp_duckdb)
    row = tmp_duckdb.execute(
        "SELECT total_revenue_usd, gross_profit_usd, total_assets_usd, gross_margin_pct,"
        " quarters_covered, quarters_expected, first_period_end, last_period_end"
        " FROM period_metrics(2026, 1, 2)"
    ).fetchone()
    # Averaging the quarterly margins (10% and 30%) would give 20%; summed parts give 25%.
    assert row == (
        400,
        100,
        1200,
        pytest.approx(25.0),
        2,
        2,
        date(2026, 3, 31),
        date(2026, 6, 30),
    )


def test_period_metrics_partial_window_has_coverage_but_no_amounts(tmp_duckdb):
    _two_quarters(tmp_duckdb)
    assert tmp_duckdb.execute(
        "SELECT quarters_covered, quarters_expected, total_revenue_usd,"
        " total_assets_usd, gross_margin_pct FROM period_metrics(2026, 1, 3)"
    ).fetchone() == (2, 3, None, None, None)


def test_period_metrics_flow_is_null_unless_every_quarter_reports_it(tmp_duckdb):
    _insert(
        tmp_duckdb,
        _quarter("AAA", 2026, 1, date(2026, 3, 31), total_revenue_usd=100,
                 net_income_usd=5),
        _quarter("AAA", 2026, 2, date(2026, 6, 30), total_revenue_usd=100),
    )  # fmt: skip
    assert tmp_duckdb.execute(
        "SELECT total_revenue_usd, net_income_usd, net_margin_pct"
        " FROM period_metrics(2026, 1, 2)"
    ).fetchone() == (200, None, None)


def test_annual_metrics_ratios(tmp_duckdb):
    upsert_rows(
        tmp_duckdb,
        "annual_financials",
        ["ticker", "fiscal_year"],
        [
            YFinanceAnnualRow(
                ticker="AAA", fiscal_year=2025, period_end=date(2025, 12, 31),
                total_revenue_usd=1000, net_income_usd=250,
            )
        ],
    )  # fmt: skip
    assert tmp_duckdb.execute(
        "SELECT fiscal_year, net_margin_pct FROM annual_metrics"
    ).fetchone() == (2025, pytest.approx(25.0))


def test_derived_columns_and_macro_carry_comments(tmp_duckdb):
    uncommented = tmp_duckdb.execute(
        "SELECT table_name, column_name FROM duckdb_columns()"
        " WHERE table_name IN ('quarterly_metrics', 'annual_metrics')"
        " AND (column_name LIKE '%\\_pct' ESCAPE '\\'"
        "      OR column_name IN ('debt_to_equity', 'current_ratio',"
        "                         'calendar_year', 'calendar_quarter'))"
        " AND comment IS NULL"
    ).fetchall()
    assert uncommented == []
    assert tmp_duckdb.execute(
        "SELECT comment IS NOT NULL FROM duckdb_functions()"
        " WHERE function_name = 'period_metrics'"
    ).fetchone() == (True,)
