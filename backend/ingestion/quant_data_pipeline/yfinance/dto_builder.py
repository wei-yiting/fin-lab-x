"""Pure transforms from yfinance API responses to foundation row models.

This module is intentionally a pure-function layer: no I/O, no DuckDB, no
yfinance client imports. The orchestrator pulls raw data via
``yfinance_client`` and feeds it here; the dto_builder produces row models
that the upsert layer can persist.

The info-dict half (``build_company_row`` / ``build_market_valuation_row``)
and the DataFrame-driven half (``build_quarterly_rows`` /
``build_annual_rows``) both live here so the orchestrator has one import
surface for all pure DTO construction.
"""

import math
from datetime import date, datetime, timezone
from typing import Any

import pandas as pd

from backend.ingestion.quant_data_pipeline.calendar_to_fiscal_period import (
    normalize_fiscal_period,
)
from backend.ingestion.quant_data_pipeline.duck_db.row_models import (
    CompanyRow,
    MarketValuationRow,
    YFinanceAnnualRow,
    YFinanceQuarterlyRow,
)
from backend.ingestion.quant_data_pipeline.yfinance.field_mappings import (
    BALANCE_LINE_TO_FIELD,
    CASHFLOW_LINE_TO_FIELD,
    DEFERRED_REVENUE_FALLBACK,
    INCOME_LINE_TO_FIELD,
    INFO_TO_MARKET_VALUATION_FIELD,
)
from backend.ingestion.quant_data_pipeline.yfinance.yfinance_pipeline_errors import (
    YFinanceEmptyResponseError,
)

# Destination columns whose row_model type is ``float | None`` rather than
# ``int | None``. Verified against ``row_models.py``: only ``diluted_eps``
# qualifies on the statement DTOs. Add to this set if more float-typed
# columns are introduced downstream.
_FLOAT_COLUMNS: frozenset[str] = frozenset({"diluted_eps"})

# Required line item that gates whether a period column is materialized into
# a row at all. NaN → entire period skipped (and contributes nothing to the
# missing list — that is the S-yfinance-19 per-period filter rule).
_REQUIRED_INCOME_LINE: str = "Total Revenue"
_REQUIRED_DEST_COLUMN: str = "total_revenue_usd"


def _is_missing(value: Any) -> bool:
    """True if value is None or float NaN.

    Yahoo represents missing fields as None most of the time, but occasionally
    float('nan') leaks through; both are treated identically. Empty string is
    NOT treated as missing here — that is a longName-specific concern handled
    inline in ``build_company_row``.
    """
    if value is None:
        return True
    if isinstance(value, float) and math.isnan(value):
        return True
    return False


def _parse_fy_end_unix(raw: int) -> tuple[int, int]:
    """Convert Unix timestamp (seconds, UTC) → (fy_end_month, fy_end_day).

    Caller is responsible for validating that ``raw`` is a positive non-None
    integer (see ``build_company_row``'s anomaly branches).
    """
    d = datetime.fromtimestamp(raw, tz=timezone.utc).date()
    return d.month, d.day


def build_company_row(info: dict, ticker: str) -> tuple[CompanyRow, list[str]]:
    """Build ``CompanyRow`` from yfinance ``info`` dict.

    ``ticker`` is passed in by the orchestrator already normalized
    (``.strip().upper()``); this function does NOT re-normalize.

    Raises ``YFinanceEmptyResponseError`` when ``lastFiscalYearEnd`` is
    missing / None / zero / negative, or when ``longName`` is missing / None
    / empty. Optional fields (``sector`` / ``industry``) missing are
    collected into the returned list rather than raising.
    """
    if "lastFiscalYearEnd" not in info:
        raise YFinanceEmptyResponseError(
            "lastFiscalYearEnd missing from yfinance info dict"
        )
    raw_fy_end = info["lastFiscalYearEnd"]
    if raw_fy_end is None:
        raise YFinanceEmptyResponseError("lastFiscalYearEnd is None")
    if raw_fy_end == 0:
        raise YFinanceEmptyResponseError("lastFiscalYearEnd is epoch (0)")
    if raw_fy_end < 0:
        raise YFinanceEmptyResponseError(
            f"lastFiscalYearEnd is negative ({raw_fy_end})"
        )

    fy_end_month, fy_end_day = _parse_fy_end_unix(raw_fy_end)

    long_name = info.get("longName")
    if long_name is None or long_name == "":
        raise YFinanceEmptyResponseError("longName missing or empty in yfinance info")

    missing: list[str] = []

    sector = info.get("sector")
    if sector is None or sector == "":
        sector = None
        missing.append("sector")

    industry = info.get("industry")
    if industry is None or industry == "":
        industry = None
        missing.append("industry")

    row = CompanyRow(
        ticker=ticker,
        company_name=long_name,
        sector=sector,
        industry=industry,
        fy_end_month=fy_end_month,
        fy_end_day=fy_end_day,
    )
    return row, missing


def build_market_valuation_row(
    info: dict, ticker: str, today: date,
) -> tuple[MarketValuationRow, list[str]]:
    """Build ``MarketValuationRow`` from yfinance ``info`` dict + ETL run date.

    ``today`` is passed by the caller (orchestrator) to keep this function
    deterministic and freezegun-friendly. All valuation fields are nullable;
    each missing source key (absent / None / NaN) becomes a None destination
    and appends the destination column name to the returned list.
    """
    missing: list[str] = []
    values: dict[str, Any] = {}

    for source_key, (dest_column, converter) in INFO_TO_MARKET_VALUATION_FIELD.items():
        raw = info.get(source_key)
        if source_key not in info or _is_missing(raw):
            values[dest_column] = None
            missing.append(dest_column)
            continue
        values[dest_column] = converter(raw) if converter is not None else raw

    row = MarketValuationRow(
        ticker=ticker,
        as_of_date=today,
        **values,
    )
    return row, missing


# ---------------------------------------------------------------------------
# Statement-side builders
# ---------------------------------------------------------------------------


def _coerce_numeric(dest_column: str, value: Any) -> int | float | None:
    """Coerce a yfinance numeric cell to the row_model's column type.

    ``diluted_eps`` is the only float-typed statement column; everything else
    is ``int | None`` and goes through ``int(round(...))``. Missing values
    (None / NaN) return None — the caller decides whether to record the dest
    column in the per-stage missing set.
    """
    if _is_missing(value):
        return None
    if dest_column in _FLOAT_COLUMNS:
        return float(value)
    return int(round(float(value)))


def _value_for(df: pd.DataFrame, line_item: str, period_col: Any) -> Any:
    """Return ``df.at[line_item, period_col]`` defensively.

    Missing line (not in index) or missing column → None. Catches KeyError so
    a balance / cashflow DataFrame missing the period column an income
    DataFrame had still resolves cleanly to None (the caller treats that as
    "this period missing this field").
    """
    if line_item not in df.index:
        return None
    try:
        return df.at[line_item, period_col]
    except KeyError:
        return None


def _periods_sorted_ascending(df: pd.DataFrame) -> list[Any]:
    """Return the income DataFrame's period columns in ascending order.

    Drops NaT / null timestamps before sorting so a malformed yfinance column
    (rare but observed) can't poison the iteration.
    """
    columns = [c for c in df.columns if not pd.isna(c)]
    return sorted(columns)


def _period_col_to_date(period_col: Any) -> date | None:
    """Convert a yfinance period column label to a ``datetime.date``.

    yfinance ships period_end as a ``pandas.Timestamp`` for these tables.
    Returns None if the value can't be coerced (caller skips the period).
    """
    if pd.isna(period_col):
        return None
    try:
        ts = pd.Timestamp(period_col)
    except (TypeError, ValueError):
        return None
    if pd.isna(ts):
        return None
    # NaT is filtered above; .date() returns a real datetime.date here. The
    # ``isinstance`` guard pins the return type for pyright since pandas
    # types it as ``date | NaTType``.
    result = ts.date()
    if not isinstance(result, date):
        return None
    return result


def _resolve_deferred_revenue(
    balance_df: pd.DataFrame, period_col: Any,
) -> Any:
    """Walk ``DEFERRED_REVENUE_FALLBACK`` for the first non-missing cell.

    Returns the raw (uncoerced) cell value, or None if every fallback line
    is missing. Caller decides whether to record the dest column as missing.
    """
    for line in DEFERRED_REVENUE_FALLBACK:
        raw = _value_for(balance_df, line, period_col)
        if not _is_missing(raw):
            return raw
    return None


def _build_statement_rows(
    dfs: tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame],
    company: CompanyRow,
    *,
    row_cls: type,
    include_fiscal_quarter: bool,
) -> tuple[list, list[str]]:
    """Shared implementation for quarterly + annual row construction.

    Iteration is outer = period column (driven by the income DataFrame),
    inner = line items per statement. A period whose Total Revenue is NaN
    is skipped entirely and contributes nothing to ``missing`` — only
    materialized rows can add to that set.
    """
    income_df, balance_df, cashflow_df = dfs
    missing: set[str] = set()
    rows: list = []

    for period_col in _periods_sorted_ascending(income_df):
        period_end = _period_col_to_date(period_col)
        if period_end is None:
            continue

        raw_revenue = _value_for(income_df, _REQUIRED_INCOME_LINE, period_col)
        if _is_missing(raw_revenue):
            continue

        fiscal_year, fiscal_quarter = normalize_fiscal_period(
            period_end, company.fy_end_month
        )

        row_kwargs: dict[str, Any] = {
            "ticker": company.ticker,
            "fiscal_year": fiscal_year,
            "period_start": None,
            "period_end": period_end,
        }
        if include_fiscal_quarter:
            row_kwargs["fiscal_quarter"] = fiscal_quarter

        for mapping, df in (
            (INCOME_LINE_TO_FIELD, income_df),
            (BALANCE_LINE_TO_FIELD, balance_df),
            (CASHFLOW_LINE_TO_FIELD, cashflow_df),
        ):
            for line_item, dest_column in mapping.items():
                raw = _value_for(df, line_item, period_col)
                coerced = _coerce_numeric(dest_column, raw)
                row_kwargs[dest_column] = coerced
                if coerced is None:
                    missing.add(dest_column)

        deferred_raw = _resolve_deferred_revenue(balance_df, period_col)
        deferred_coerced = _coerce_numeric("deferred_revenue_usd", deferred_raw)
        row_kwargs["deferred_revenue_usd"] = deferred_coerced
        if deferred_coerced is None:
            missing.add("deferred_revenue_usd")

        rows.append(row_cls(**row_kwargs))

    if not rows:
        raise YFinanceEmptyResponseError(
            f"All periods missing required field '{_REQUIRED_DEST_COLUMN}' "
            f"for ticker {company.ticker}"
        )

    return rows, sorted(missing)


def build_quarterly_rows(
    dfs: tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame],
    company: CompanyRow,
) -> tuple[list[YFinanceQuarterlyRow], list[str]]:
    """Build per-period ``YFinanceQuarterlyRow`` list + missing-columns list.

    Periods with NaN ``Total Revenue`` are skipped entirely. Raises
    ``YFinanceEmptyResponseError`` when every period is skipped.
    """
    rows, missing = _build_statement_rows(
        dfs,
        company,
        row_cls=YFinanceQuarterlyRow,
        include_fiscal_quarter=True,
    )
    return rows, missing


def build_annual_rows(
    dfs: tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame],
    company: CompanyRow,
) -> tuple[list[YFinanceAnnualRow], list[str]]:
    """Build per-period ``YFinanceAnnualRow`` list + missing-columns list.

    Same NaN-filter / fallback / sign-preservation behavior as
    ``build_quarterly_rows``; only difference is the row class has no
    ``fiscal_quarter`` field.
    """
    rows, missing = _build_statement_rows(
        dfs,
        company,
        row_cls=YFinanceAnnualRow,
        include_fiscal_quarter=False,
    )
    return rows, missing
