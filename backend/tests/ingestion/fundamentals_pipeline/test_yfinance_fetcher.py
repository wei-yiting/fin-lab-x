from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from typing import Any

import pandas as pd
import pytest

from backend.ingestion.fundamentals_pipeline.errors import DataValidationError
from backend.ingestion.fundamentals_pipeline.yfinance_fetcher import (
    build_company_row,
    build_market_valuation_row,
    ingest_ticker,
)

AS_OF = date(2026, 10, 27)


def _epoch(d: date) -> int:
    return int(datetime(d.year, d.month, d.day, tzinfo=UTC).timestamp())


def _frame(rows: dict[str, list[Any]], periods: list[str]) -> pd.DataFrame:
    return pd.DataFrame(rows, index=pd.to_datetime(periods)).T


@dataclass
class FakeTicker:
    info: dict[str, Any]
    quarterly_income_stmt: pd.DataFrame = field(default_factory=pd.DataFrame)
    quarterly_balance_sheet: pd.DataFrame = field(default_factory=pd.DataFrame)
    quarterly_cashflow: pd.DataFrame = field(default_factory=pd.DataFrame)
    income_stmt: pd.DataFrame = field(default_factory=pd.DataFrame)
    balance_sheet: pd.DataFrame = field(default_factory=pd.DataFrame)
    cashflow: pd.DataFrame = field(default_factory=pd.DataFrame)


def _apple_like() -> FakeTicker:
    quarters = ["2026-06-30", "2026-03-31", "2025-12-31"]
    return FakeTicker(
        info={
            "longName": "Apple Inc.",
            "sector": "Technology",
            "industry": "Consumer Electronics",
            "lastFiscalYearEnd": _epoch(date(2025, 9, 27)),
            "marketCap": 5.0e12,
            "forwardPE": 35.9,
            "trailingPE": "Infinity",
            "dividendYield": 0.31,
            "heldPercentInstitutions": 0.66,
        },
        quarterly_income_stmt=_frame(
            {
                "Total Revenue": [94.0e9, 95.0e9, 124.0e9],
                "Gross Profit": [43.0e9, 45.0e9, 58.0e9],
                "Diluted EPS": [1.57, 1.65, 2.40],
                "Interest Income Non Operating": [1.0e8, None, None],
            },
            quarters,
        ),
        quarterly_balance_sheet=_frame(
            {
                "Total Assets": [331.0e9, 340.0e9, float("nan")],
                "Stockholders Equity": [66.0e9, 70.0e9, float("nan")],
            },
            quarters,
        ),
        quarterly_cashflow=_frame(
            {"Free Cash Flow": [24.0e9, 20.0e9, 27.0e9]}, quarters
        ),
        income_stmt=_frame(
            {"Total Revenue": [416.0e9, 391.0e9]}, ["2025-09-30", "2024-09-30"]
        ),
    )


def test_ingest_ticker_writes_all_four_tables(tmp_duckdb):
    written = ingest_ticker(tmp_duckdb, "AAPL", _apple_like(), AS_OF)

    assert written == {
        "companies": 1,
        "market_valuations": 1,
        "quarterly_financials": 3,
        "annual_financials": 2,
    }
    rows = tmp_duckdb.execute(
        "SELECT fiscal_year, fiscal_quarter, period_end, total_revenue_usd,"
        " total_assets_usd, diluted_eps, interest_income_usd"
        " FROM quarterly_financials ORDER BY period_end"
    ).fetchall()
    assert rows == [
        (2026, 1, date(2025, 12, 31), 124_000_000_000, None, 2.40, None),
        (2026, 2, date(2026, 3, 31), 95_000_000_000, 340_000_000_000, 1.65, None),
        (
            2026,
            3,
            date(2026, 6, 30),
            94_000_000_000,
            331_000_000_000,
            1.57,
            100_000_000,
        ),
    ]
    annual = tmp_duckdb.execute(
        "SELECT fiscal_year, total_revenue_usd FROM annual_financials ORDER BY 1"
    ).fetchall()
    assert annual == [(2024, 391_000_000_000), (2025, 416_000_000_000)]


def test_sec_only_columns_stay_null(tmp_duckdb):
    ingest_ticker(tmp_duckdb, "AAPL", _apple_like(), AS_OF)
    assert tmp_duckdb.execute(
        "SELECT count(*) FROM quarterly_financials"
        " WHERE product_revenue_usd IS NOT NULL OR current_rpo_usd IS NOT NULL"
    ).fetchone() == (0,)


def test_ingest_ticker_records_success_audit_row(tmp_duckdb):
    ingest_ticker(tmp_duckdb, "AAPL", _apple_like(), AS_OF)
    assert tmp_duckdb.execute(
        "SELECT pipeline, ticker, status, rows_written_total FROM ingestion_runs"
    ).fetchall() == [("yfinance", "AAPL", "success", 7)]


def test_ingest_ticker_records_error_audit_row_and_reraises(tmp_duckdb):
    with pytest.raises(DataValidationError):
        ingest_ticker(tmp_duckdb, "XXXX", FakeTicker(info={}), AS_OF)
    assert tmp_duckdb.execute(
        "SELECT ticker, status, error_class FROM ingestion_runs"
    ).fetchall() == [("XXXX", "error", "DataValidationError")]


def test_all_empty_period_is_skipped(tmp_duckdb):
    source = _apple_like()
    source.quarterly_income_stmt = _frame(
        {"Total Revenue": [94.0e9, float("nan")]}, ["2026-06-30", "2025-03-31"]
    )
    source.quarterly_balance_sheet = pd.DataFrame()
    source.quarterly_cashflow = pd.DataFrame()
    written = ingest_ticker(tmp_duckdb, "AAPL", source, AS_OF)
    assert written["quarterly_financials"] == 1


def test_company_row_snaps_52_53_week_fiscal_year_end():
    row = build_company_row(
        "COST", {"longName": "Costco", "lastFiscalYearEnd": _epoch(date(2024, 9, 1))}
    )
    assert (row.fy_end_month, row.fy_end_day) == (8, 31)


def test_market_valuation_quirks():
    row = build_market_valuation_row("AAPL", _apple_like().info, AS_OF)
    assert row.market_cap_usd == 5_000_000_000_000
    assert row.trailing_price_to_earnings is None  # "Infinity" → NULL
    assert row.dividend_yield_pct == 0.31  # already percent in yfinance
    assert row.held_pct_institutions == pytest.approx(66.0)  # fraction → percent
