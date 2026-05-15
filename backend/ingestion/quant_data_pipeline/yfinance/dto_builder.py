"""Pure transforms from yfinance API responses to foundation row models.

This module is intentionally a pure-function layer: no I/O, no DuckDB, no
yfinance client imports. The orchestrator pulls raw data via
``yfinance_client`` and feeds it here; the dto_builder produces row models
that the upsert layer can persist.

Task 4 fills the info-dict half (``build_company_row`` /
``build_market_valuation_row``). Task 5 will append DataFrame-driven builders
for quarterly and annual statements to the same module.
"""

import math
from datetime import date, datetime, timezone
from typing import Any

from backend.ingestion.quant_data_pipeline.duck_db.row_models import (
    CompanyRow,
    MarketValuationRow,
)
from backend.ingestion.quant_data_pipeline.yfinance.field_mappings import (
    INFO_TO_MARKET_VALUATION_FIELD,
)
from backend.ingestion.quant_data_pipeline.yfinance.yfinance_pipeline_errors import (
    YFinanceEmptyResponseError,
)


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
