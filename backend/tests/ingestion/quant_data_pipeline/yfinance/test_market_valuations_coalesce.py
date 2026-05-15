"""Behavioural integration test for same-day ``market_valuations`` COALESCE.

Covers BDD scenario S-yfinance-13: two ``refresh_yfinance_ticker`` calls on
the same calendar day collapse to one ``market_valuations`` PK row; columns
where Run B fetched ``None`` preserve Run A's value (orchestrator passes
``MARKET_VALUATIONS_COALESCE_COLS`` so the upsert's
``SET col = COALESCE(EXCLUDED.col, table.col)`` retains the prior value),
while columns where both runs fetched non-``None`` values let Run B's value
win (EXCLUDED, the newer value). Run B's audit row records the missing
field in ``metadata.missing_fields``.

Helpers are duplicated locally rather than imported from
``test_refresh_orchestrator_core.py`` — the same-day COALESCE scenario
needs a tiny single-period stub, not the multi-period MSFT helpers.
"""

import json
from datetime import date

import pandas as pd
import pytest
from freezegun import freeze_time

from backend.ingestion.quant_data_pipeline.yfinance import (
    constants,
    yfinance_client,
)
from backend.ingestion.quant_data_pipeline.yfinance.refresh_orchestrator import (
    refresh_yfinance_ticker,
)
from backend.tests.ingestion.quant_data_pipeline.yfinance.stubs import (
    StubTicker,
    make_stub_factory,
)

# 1695945600 → 2023-09-29 UTC. Matches AAPL's FY-end month 9 so quarterly /
# annual period_end Sep 30, 2024 normalises to (fiscal_year=2024,
# fiscal_quarter=4); the exact mapping is not load-bearing for this test —
# we only assert market_valuations behaviour — but a self-consistent FY end
# keeps the orchestrator's stage 2 + stage 3 happy so both runs succeed.
_AAPL_FY_END_UNIX = 1695945600


def _info(market_cap: int | None, dividend_yield: float) -> dict:
    """Return a fully-populated yfinance info dict, with overridable
    ``marketCap`` and ``dividendYield`` for the COALESCE scenario."""
    return {
        "longName": "Apple Inc.",
        "sector": "Technology",
        "industry": "Consumer Electronics",
        "lastFiscalYearEnd": _AAPL_FY_END_UNIX,
        "marketCap": market_cap,
        "enterpriseValue": 3_500_000_000_000,
        "trailingPE": 30.0,
        "forwardPE": 27.0,
        "priceToBook": 50.0,
        "priceToSalesTrailing12Months": 9.0,
        "enterpriseToEbitda": 22.0,
        "trailingPegRatio": 2.0,
        "dividendYield": dividend_yield,
        "beta": 1.2,
        "heldPercentInstitutions": 0.61,
    }


def _statement_dfs() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Single-period statement triple — same shape for quarterly + annual."""
    period_end = date(2024, 9, 30)
    income = pd.DataFrame.from_dict(
        {
            "Total Revenue": {period_end: 89_000_000_000},
            "Net Income": {period_end: 20_000_000_000},
            "Diluted EPS": {period_end: 1.5},
            "Diluted Average Shares": {period_end: 15_000_000_000},
        },
        orient="index",
    )
    balance = pd.DataFrame.from_dict(
        {
            "Total Assets": {period_end: 350_000_000_000},
            "Stockholders Equity": {period_end: 65_000_000_000},
        },
        orient="index",
    )
    cashflow = pd.DataFrame.from_dict(
        {
            "Operating Cash Flow": {period_end: 30_000_000_000},
            "Free Cash Flow": {period_end: 27_000_000_000},
        },
        orient="index",
    )
    return income, balance, cashflow


def _stub(market_cap: int | None, dividend_yield: float) -> StubTicker:
    income, balance, cashflow = _statement_dfs()
    return StubTicker(
        info=_info(market_cap, dividend_yield),
        quarterly_income_stmt=income,
        quarterly_balance_sheet=balance,
        quarterly_cashflow=cashflow,
        income_stmt=income,
        balance_sheet=balance,
        cashflow=cashflow,
    )


def test_same_day_market_cap_coalesce_preserves_prior_value_dividend_yield_overrides(
    tmp_duckdb, monkeypatch,
):
    monkeypatch.setattr(constants, "PACING_MIN_INTERVAL_SECONDS", 0.0)

    # ---- Run A: market_cap=3.4T, dividend_yield=0.46, all fields populated ----
    stub_a = _stub(market_cap=3_400_000_000_000, dividend_yield=0.46)
    with freeze_time("2026-05-04 09:00:00"):
        with yfinance_client.use_ticker_factory_for_test(make_stub_factory(stub_a)):
            refresh_yfinance_ticker(tmp_duckdb, "AAPL")

    # ---- Run B: yfinance returns marketCap=None (hiccup) + new dividendYield ----
    stub_b = _stub(market_cap=None, dividend_yield=0.47)
    with freeze_time("2026-05-04 14:30:00"):
        with yfinance_client.use_ticker_factory_for_test(make_stub_factory(stub_b)):
            refresh_yfinance_ticker(tmp_duckdb, "AAPL")

    # 1. PK collapses — exactly one market_valuations row for the day.
    mv_count = tmp_duckdb.execute(
        "SELECT COUNT(*) FROM market_valuations "
        "WHERE ticker='AAPL' AND as_of_date='2026-05-04'"
    ).fetchone()[0]
    assert mv_count == 1

    # 2. market_cap_usd preserved from Run A (COALESCE skipped Run B's None);
    #    dividend_yield_pct overridden by Run B (both runs non-None, EXCLUDED wins).
    row = tmp_duckdb.execute(
        "SELECT market_cap_usd, dividend_yield_pct FROM market_valuations "
        "WHERE ticker='AAPL' AND as_of_date='2026-05-04'"
    ).fetchone()
    assert row is not None
    assert row[0] == 3_400_000_000_000
    assert row[1] == pytest.approx(0.47)

    # 3. Run B's audit row records ``market_cap_usd`` in missing_fields.
    metadata_json = tmp_duckdb.execute(
        "SELECT metadata FROM ingestion_runs "
        "WHERE pipeline='yfinance' AND ticker='AAPL' "
        "ORDER BY started_at DESC LIMIT 1"
    ).fetchone()[0]
    metadata = json.loads(metadata_json)
    assert "market_cap_usd" in metadata["missing_fields"]

    # 4. Both audit rows present and successful.
    audit_rows = tmp_duckdb.execute(
        "SELECT status FROM ingestion_runs "
        "WHERE pipeline='yfinance' AND ticker='AAPL' "
        "ORDER BY started_at ASC"
    ).fetchall()
    assert audit_rows == [("success",), ("success",)]
