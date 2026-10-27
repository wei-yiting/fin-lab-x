"""yfinance → DuckDB fetcher for the fundamentals path (local batch ingest only).

Writes the yfinance-owned tables — ``companies``, ``market_valuations``,
``quarterly_financials``, ``annual_financials`` — and leaves SEC-sourced columns
untouched (NULL). There is deliberately no retry and no JIT: this runs once from a
developer machine; yfinance rate-limits cloud IPs, which is why on-demand ingestion
waits for the Finnhub migration (DEV-69 / DEV-228).
"""

import math
from datetime import UTC, date, datetime
from typing import Any, Protocol

import pandas as pd
import yfinance as yf
from duckdb import DuckDBPyConnection

from backend.ingestion.fundamentals_pipeline.calendar_to_fiscal_period import (
    normalize_fiscal_period,
    snap_period_end,
)
from backend.ingestion.fundamentals_pipeline.duck_db.row_models import (
    CompanyRow,
    MarketValuationRow,
    YFinanceAnnualRow,
    YFinanceQuarterlyRow,
)
from backend.ingestion.fundamentals_pipeline.duck_db.upsert import upsert_rows
from backend.ingestion.fundamentals_pipeline.errors import DataValidationError
from backend.ingestion.fundamentals_pipeline.ingestion_run_tracker import (
    track_ingestion_run,
)

PIPELINE_NAME = "yfinance"

# Store keeps the SEC-style class-share ticker; Yahoo uses a dash.
_YF_SYMBOL_OVERRIDES = {"BRK.B": "BRK-B"}

# DDL column → yfinance line items, first non-null wins. Fallbacks cover label
# variants across industries (e.g. banks report interest income without the
# "Non Operating" suffix).
INCOME_FIELDS: dict[str, tuple[str, ...]] = {
    "total_revenue_usd": ("Total Revenue",),
    "cost_of_revenue_usd": ("Cost Of Revenue",),
    "gross_profit_usd": ("Gross Profit",),
    "research_and_development_usd": ("Research And Development",),
    "selling_general_admin_usd": ("Selling General And Administration",),
    "operating_income_usd": ("Operating Income",),
    "ebit_usd": ("EBIT",),
    "net_income_usd": ("Net Income",),
    "interest_income_usd": ("Interest Income", "Interest Income Non Operating"),
    "interest_expense_usd": ("Interest Expense", "Interest Expense Non Operating"),
    "tax_provision_usd": ("Tax Provision",),
    "ebitda_usd": ("EBITDA",),
    "diluted_eps": ("Diluted EPS",),
    "diluted_avg_shares": ("Diluted Average Shares",),
}
BALANCE_FIELDS: dict[str, tuple[str, ...]] = {
    "total_assets_usd": ("Total Assets",),
    "goodwill_usd": ("Goodwill",),
    "net_ppe_usd": ("Net PPE",),
    "total_debt_usd": ("Total Debt",),
    "long_term_debt_usd": ("Long Term Debt",),
    "net_debt_usd": ("Net Debt",),
    "cash_and_equivalents_usd": ("Cash And Cash Equivalents",),
    "stockholders_equity_usd": ("Stockholders Equity",),
    "current_assets_usd": ("Current Assets",),
    "current_liabilities_usd": ("Current Liabilities",),
    "accounts_receivable_usd": ("Accounts Receivable",),
    "inventory_usd": ("Inventory",),
    "deferred_revenue_usd": ("Current Deferred Revenue",),
}
CASHFLOW_FIELDS: dict[str, tuple[str, ...]] = {
    "operating_cash_flow_usd": ("Operating Cash Flow",),
    "capital_expenditure_usd": ("Capital Expenditure",),
    "free_cash_flow_usd": ("Free Cash Flow",),
    "depreciation_amortization_usd": (
        "Depreciation And Amortization",
        "Depreciation Amortization Depletion",
    ),
    "stock_buyback_usd": ("Repurchase Of Capital Stock",),
    "dividends_paid_usd": ("Common Stock Dividend Paid", "Cash Dividends Paid"),
    "stock_based_compensation_usd": ("Stock Based Compensation",),
}
_FLOAT_COLUMNS = {"diluted_eps"}

# yfinance emits columns for periods not yet fully reported (a few stray line items,
# no revenue). Revenue marks a reported period; anything without it is dropped so it
# can never become a company's "latest reported quarter".


class TickerSource(Protocol):
    """The slice of ``yfinance.Ticker`` this fetcher reads (test seam)."""

    @property
    def info(self) -> dict[str, Any]: ...
    @property
    def quarterly_income_stmt(self) -> pd.DataFrame: ...
    @property
    def quarterly_balance_sheet(self) -> pd.DataFrame: ...
    @property
    def quarterly_cashflow(self) -> pd.DataFrame: ...
    @property
    def income_stmt(self) -> pd.DataFrame: ...
    @property
    def balance_sheet(self) -> pd.DataFrame: ...
    @property
    def cashflow(self) -> pd.DataFrame: ...


def open_ticker(ticker: str) -> TickerSource:
    return yf.Ticker(_YF_SYMBOL_OVERRIDES.get(ticker, ticker))


def _finite_float(value: Any) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def _finite_int(value: Any) -> int | None:
    number = _finite_float(value)
    return None if number is None else int(round(number))


def build_company_row(ticker: str, info: dict[str, Any]) -> CompanyRow:
    name = info.get("longName") or info.get("shortName")
    fye_epoch = info.get("lastFiscalYearEnd")
    if not name or fye_epoch is None:
        raise DataValidationError(
            f"{ticker}: yfinance info lacks company name or lastFiscalYearEnd"
        )
    fye = snap_period_end(datetime.fromtimestamp(fye_epoch, UTC).date())
    return CompanyRow(
        ticker=ticker,
        company_name=name,
        sector=info.get("sector"),
        industry=info.get("industry"),
        fy_end_month=fye.month,
        fy_end_day=fye.day,
    )


def build_market_valuation_row(
    ticker: str, info: dict[str, Any], as_of: date
) -> MarketValuationRow:
    held = _finite_float(info.get("heldPercentInstitutions"))
    return MarketValuationRow(
        ticker=ticker,
        as_of_date=as_of,
        market_cap_usd=_finite_int(info.get("marketCap")),
        enterprise_value_usd=_finite_int(info.get("enterpriseValue")),
        trailing_price_to_earnings=_finite_float(info.get("trailingPE")),
        forward_price_to_earnings=_finite_float(info.get("forwardPE")),
        price_to_book_ratio=_finite_float(info.get("priceToBook")),
        price_to_sales_trailing_12m=_finite_float(
            info.get("priceToSalesTrailing12Months")
        ),
        ev_to_ebitda_ratio=_finite_float(info.get("enterpriseToEbitda")),
        trailing_peg_ratio=_finite_float(info.get("trailingPegRatio")),
        # yfinance >= 1.x already reports dividendYield in percent (AAPL 0.31 = 0.31%).
        dividend_yield_pct=_finite_float(info.get("dividendYield")),
        beta=_finite_float(info.get("beta")),
        held_pct_institutions=None if held is None else held * 100,
    )


def _extract_period_values(
    frames: list[tuple[pd.DataFrame, dict[str, tuple[str, ...]]]],
) -> dict[date, dict[str, Any]]:
    by_period: dict[date, dict[str, Any]] = {}
    for frame, fields in frames:
        if frame is None or frame.empty:
            continue
        for column in frame.columns:
            period_end = pd.Timestamp(column).date()
            values = by_period.setdefault(period_end, {})
            for ddl_column, labels in fields.items():
                for label in labels:
                    if label not in frame.index:
                        continue
                    raw = frame.at[label, column]
                    parsed = (
                        _finite_float(raw)
                        if ddl_column in _FLOAT_COLUMNS
                        else _finite_int(raw)
                    )
                    if parsed is not None:
                        values[ddl_column] = parsed
                        break
    return by_period


def build_quarterly_rows(
    ticker: str,
    fy_end_month: int,
    income: pd.DataFrame,
    balance: pd.DataFrame,
    cashflow: pd.DataFrame,
) -> list[YFinanceQuarterlyRow]:
    by_period = _extract_period_values(
        [
            (income, INCOME_FIELDS),
            (balance, BALANCE_FIELDS),
            (cashflow, CASHFLOW_FIELDS),
        ]
    )
    rows: dict[tuple[int, int], YFinanceQuarterlyRow] = {}
    for period_end in sorted(by_period):
        values = by_period[period_end]
        if values.get("total_revenue_usd") is None:
            continue
        fiscal_year, fiscal_quarter = normalize_fiscal_period(period_end, fy_end_month)
        rows[(fiscal_year, fiscal_quarter)] = YFinanceQuarterlyRow(
            ticker=ticker,
            fiscal_year=fiscal_year,
            fiscal_quarter=fiscal_quarter,
            period_end=period_end,
            **values,
        )
    return list(rows.values())


def build_annual_rows(
    ticker: str,
    fy_end_month: int,
    income: pd.DataFrame,
    balance: pd.DataFrame,
    cashflow: pd.DataFrame,
) -> list[YFinanceAnnualRow]:
    by_period = _extract_period_values(
        [
            (income, INCOME_FIELDS),
            (balance, BALANCE_FIELDS),
            (cashflow, CASHFLOW_FIELDS),
        ]
    )
    rows: dict[int, YFinanceAnnualRow] = {}
    for period_end in sorted(by_period):
        values = by_period[period_end]
        if values.get("total_revenue_usd") is None:
            continue
        fiscal_year, _ = normalize_fiscal_period(period_end, fy_end_month)
        rows[fiscal_year] = YFinanceAnnualRow(
            ticker=ticker, fiscal_year=fiscal_year, period_end=period_end, **values
        )
    return list(rows.values())


def ingest_ticker(
    conn: DuckDBPyConnection, ticker: str, source: TickerSource, as_of: date
) -> dict[str, int]:
    """Fetch one ticker from ``source`` and upsert all four tables.

    Returns rows written per table; one ``ingestion_runs`` audit row is written
    whether this succeeds or raises.
    """
    written: dict[str, int] = {}
    with track_ingestion_run(conn, PIPELINE_NAME, ticker) as report:

        def write(table: str, pk: list[str], rows: list[Any]) -> None:
            written[table] = upsert_rows(conn, table, pk, rows)
            report.rows_written_total += written[table]

        info = source.info
        company = build_company_row(ticker, info)
        write("companies", ["ticker"], [company])
        write(
            "market_valuations",
            ["ticker", "as_of_date"],
            [build_market_valuation_row(ticker, info, as_of)],
        )
        quarterly = build_quarterly_rows(
            ticker,
            company.fy_end_month,
            source.quarterly_income_stmt,
            source.quarterly_balance_sheet,
            source.quarterly_cashflow,
        )
        write(
            "quarterly_financials",
            ["ticker", "fiscal_year", "fiscal_quarter"],
            quarterly,
        )
        annual = build_annual_rows(
            ticker,
            company.fy_end_month,
            source.income_stmt,
            source.balance_sheet,
            source.cashflow,
        )
        write("annual_financials", ["ticker", "fiscal_year"], annual)
        report.metadata = {
            "rows_per_table": written,
            "periods_covered": [str(r.period_end) for r in quarterly],
        }
    return written
