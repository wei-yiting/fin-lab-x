"""Behavioural integration tests for ``metadata['missing_fields']`` semantics.

Covers BDD scenarios:

* S-yfinance-18 — cross-source dedup: a destination column missing from both
  the info dict AND the quarterly + annual statements still appears at most
  once in ``missing_fields`` because the orchestrator wraps the four
  per-stage lists in ``set(...)`` before sorting.
* S-yfinance-19 — per-stage dedup: one quarterly column missing across
  multiple period columns appears exactly once because
  ``_build_statement_rows`` uses a ``set`` internally; periods skipped via
  the Total Revenue NaN gate contribute nothing to the missing set.
* S-yfinance-20 — cross-stage partial coverage: a column resolved from the
  ``DEFERRED_REVENUE_FALLBACK`` chain in annual but exhausted in quarterly
  appears in ``missing_fields`` (since it is missing in ≥1 stage) yet the
  annual row still carries the non-NULL value.

Helpers are inlined per-test to keep the per-scenario data shape obvious;
each scenario tweaks a different axis of the missing-list machinery.
"""

import json
from datetime import date

import pandas as pd

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

# 1735603200 → UTC 2024-12-31 (calendar-year FYE → fy_end_month=12). Lets
# quarterly period_end Mar/Jun/Sep/Dec normalize cleanly to Q1/Q2/Q3/Q4.
_CY_FY_END_UNIX = 1735603200


def _good_info(ticker: str, **overrides) -> dict:
    """Return a fully-populated info dict for a calendar-year FYE ticker."""
    base = {
        "longName": f"{ticker} Inc.",
        "sector": "Financials",
        "industry": "Banks",
        "lastFiscalYearEnd": _CY_FY_END_UNIX,
        "marketCap": 600_000_000_000,
        "enterpriseValue": 650_000_000_000,
        "trailingPE": 12.0,
        "forwardPE": 11.0,
        "priceToBook": 1.8,
        "priceToSalesTrailing12Months": 3.5,
        "enterpriseToEbitda": 15.0,
        "trailingPegRatio": 1.4,
        "dividendYield": 2.5,
        "beta": 1.1,
        "heldPercentInstitutions": 0.72,
    }
    base.update(overrides)
    return base


def _quarterly_dfs(
    period_ends: list[date],
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Single helper for all 3 scenarios — every line item populated for every
    period. Tests drop / NaN specific cells after construction."""
    income = pd.DataFrame.from_dict(
        {
            "Total Revenue": {p: 40_000_000_000 for p in period_ends},
            "Cost Of Revenue": {p: 15_000_000_000 for p in period_ends},
            "Gross Profit": {p: 25_000_000_000 for p in period_ends},
            "Net Income": {p: 12_000_000_000 for p in period_ends},
            "Interest Income": {p: 200_000_000 for p in period_ends},
            "Diluted EPS": {p: 4.0 for p in period_ends},
            "Diluted Average Shares": {p: 3_000_000_000 for p in period_ends},
        },
        orient="index",
    )
    balance = pd.DataFrame.from_dict(
        {
            "Total Assets": {p: 3_700_000_000_000 for p in period_ends},
            "Stockholders Equity": {p: 320_000_000_000 for p in period_ends},
            "Deferred Revenue": {p: 5_000_000_000 for p in period_ends},
        },
        orient="index",
    )
    cashflow = pd.DataFrame.from_dict(
        {
            "Operating Cash Flow": {p: 40_000_000_000 for p in period_ends},
            "Free Cash Flow": {p: 35_000_000_000 for p in period_ends},
        },
        orient="index",
    )
    return income, balance, cashflow


def _annual_dfs(
    period_ends: list[date],
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Annual-cadence counterpart with the same shape — each test mutates
    specific cells / drops specific rows for the scenario it owns."""
    income = pd.DataFrame.from_dict(
        {
            "Total Revenue": {p: 160_000_000_000 for p in period_ends},
            "Net Income": {p: 48_000_000_000 for p in period_ends},
            "Interest Income": {p: 800_000_000 for p in period_ends},
            "Diluted EPS": {p: 16.0 for p in period_ends},
        },
        orient="index",
    )
    balance = pd.DataFrame.from_dict(
        {
            "Total Assets": {p: 3_700_000_000_000 for p in period_ends},
            "Stockholders Equity": {p: 320_000_000_000 for p in period_ends},
            "Deferred Revenue": {p: 5_000_000_000 for p in period_ends},
        },
        orient="index",
    )
    cashflow = pd.DataFrame.from_dict(
        {
            "Operating Cash Flow": {p: 160_000_000_000 for p in period_ends},
            "Free Cash Flow": {p: 140_000_000_000 for p in period_ends},
        },
        orient="index",
    )
    return income, balance, cashflow


# ---------------------------------------------------------------------------
# Test 1 — S-yfinance-18 cross-source dedup
# ---------------------------------------------------------------------------


def test_cross_source_dedup_appears_once(tmp_duckdb, monkeypatch):
    """``interest_income_usd`` missing in BOTH quarterly + annual statements
    plus ``dividendYield`` absent in info — the outer ``set(...)`` collapse
    keeps interest_income_usd to exactly one occurrence, and the final list
    is sorted."""
    monkeypatch.setattr(constants, "PACING_MIN_INTERVAL_SECONDS", 0.0)

    quarterly_period_ends = [date(2025, 3, 31), date(2025, 6, 30)]
    annual_period_ends = [date(2024, 12, 31), date(2023, 12, 31)]

    q_income, q_balance, q_cashflow = _quarterly_dfs(quarterly_period_ends)
    a_income, a_balance, a_cashflow = _annual_dfs(annual_period_ends)

    # Drop Interest Income from BOTH statement sources.
    q_income = q_income.drop(index="Interest Income")
    a_income = a_income.drop(index="Interest Income")

    info = _good_info("WEIRD")
    # Omit dividendYield → build_market_valuation_row emits "dividend_yield_pct".
    info.pop("dividendYield")

    stub = StubTicker(
        info=info,
        quarterly_income_stmt=q_income,
        quarterly_balance_sheet=q_balance,
        quarterly_cashflow=q_cashflow,
        income_stmt=a_income,
        balance_sheet=a_balance,
        cashflow=a_cashflow,
    )

    with yfinance_client.use_ticker_factory_for_test(make_stub_factory(stub)):
        report = refresh_yfinance_ticker(tmp_duckdb, "WEIRD")

    missing = report.metadata["missing_fields"]
    assert isinstance(missing, list)
    assert all(isinstance(item, str) for item in missing)

    # Cross-source dedup: appears in both quarterly + annual lists, surfaces
    # in the merged set exactly once.
    assert missing.count("interest_income_usd") == 1
    # Info-side gap also flows through.
    assert "dividend_yield_pct" in missing
    # Final list is sorted (orchestrator wraps the union in sorted(...)).
    assert missing == sorted(missing)


# ---------------------------------------------------------------------------
# Test 2 — S-yfinance-19 per-stage dedup with one skipped period
# ---------------------------------------------------------------------------


def test_per_stage_dedup_one_field_missing_in_multiple_periods(
    tmp_duckdb, monkeypatch,
):
    """Four quarterly periods. 2025-Q1 has Total Revenue=NaN (whole period
    skipped). 2024-Q4 + 2025-Q3 both have Interest Income=NaN. 2025-Q2 has
    valid Interest Income. Per-stage dedup → ``interest_income_usd`` shows
    up exactly once in ``missing_fields`` even though it is missing in 2
    materialized periods; the skipped Q1 contributes nothing."""
    monkeypatch.setattr(constants, "PACING_MIN_INTERVAL_SECONDS", 0.0)

    quarterly_period_ends = [
        date(2024, 12, 31),  # FY2024 Q4
        date(2025, 3, 31),   # FY2025 Q1 — gets SKIPPED via NaN Total Revenue
        date(2025, 6, 30),   # FY2025 Q2
        date(2025, 9, 30),   # FY2025 Q3
    ]
    annual_period_ends = [date(2023, 12, 31), date(2024, 12, 31)]

    q_income, q_balance, q_cashflow = _quarterly_dfs(quarterly_period_ends)
    a_income, a_balance, a_cashflow = _annual_dfs(annual_period_ends)

    # Skip 2025-Q1 entirely.
    q_income.loc["Total Revenue", date(2025, 3, 31)] = float("nan")
    # Two materialized periods missing Interest Income, one has it valid.
    q_income.loc["Interest Income", date(2024, 12, 31)] = float("nan")
    q_income.loc["Interest Income", date(2025, 9, 30)] = float("nan")
    # 2025-Q2 keeps its 200_000_000 valid value.

    stub = StubTicker(
        info=_good_info("JPM"),
        quarterly_income_stmt=q_income,
        quarterly_balance_sheet=q_balance,
        quarterly_cashflow=q_cashflow,
        income_stmt=a_income,
        balance_sheet=a_balance,
        cashflow=a_cashflow,
    )

    with yfinance_client.use_ticker_factory_for_test(make_stub_factory(stub)):
        report = refresh_yfinance_ticker(tmp_duckdb, "JPM")

    # 1. Three quarterly rows persisted (2025-Q1 skipped).
    quarterly_count = tmp_duckdb.execute(
        "SELECT COUNT(*) FROM quarterly_financials WHERE ticker = 'JPM'"
    ).fetchone()[0]
    assert quarterly_count == 3

    persisted_periods = tmp_duckdb.execute(
        "SELECT fiscal_year, fiscal_quarter, interest_income_usd "
        "FROM quarterly_financials WHERE ticker = 'JPM' "
        "ORDER BY fiscal_year, fiscal_quarter"
    ).fetchall()
    # (2024, 4) interest_income_usd IS NULL
    # (2025, 2) interest_income_usd = 200_000_000
    # (2025, 3) interest_income_usd IS NULL
    assert persisted_periods == [
        (2024, 4, None),
        (2025, 2, 200_000_000),
        (2025, 3, None),
    ]

    # 2. Per-stage dedup — exactly one occurrence regardless of how many
    # periods left it NULL.
    missing = report.metadata["missing_fields"]
    assert missing.count("interest_income_usd") == 1

    # 3. The skipped 2025-Q1 contributed nothing — every column that ONLY
    # came from that period (none by design, but the invariant still holds)
    # would not appear here. Cross-reference against the persisted rows:
    # any column present in missing_fields and NOT NULL in every persisted
    # row would be a contradiction.
    null_counts = tmp_duckdb.execute(
        "SELECT COUNT(*) FROM quarterly_financials WHERE ticker = 'JPM' "
        "AND interest_income_usd IS NULL"
    ).fetchone()[0]
    assert null_counts == 2


# ---------------------------------------------------------------------------
# Test 3 — S-yfinance-20 cross-stage partial coverage
# ---------------------------------------------------------------------------


def test_cross_stage_partial_coverage_quarterly_only_missing(
    tmp_duckdb, monkeypatch,
):
    """Quarterly balance sheet exhausts the DEFERRED_REVENUE_FALLBACK chain
    (neither "Deferred Revenue" nor "Current Deferred Revenue" present);
    annual balance sheet hits the fallback ("Current Deferred Revenue") with
    a valid value. The merged ``missing_fields`` includes
    ``deferred_revenue_usd`` (because quarterly's per-stage list does), yet
    the annual rows carry the non-NULL value from the fallback hit. Locks
    the semantic: "missing_fields" means "missing in ≥1 stage", not
    "missing everywhere"."""
    monkeypatch.setattr(constants, "PACING_MIN_INTERVAL_SECONDS", 0.0)

    quarterly_period_ends = [date(2024, 12, 31), date(2025, 3, 31)]
    annual_period_ends = [date(2023, 12, 31), date(2024, 12, 31)]

    q_income, q_balance, q_cashflow = _quarterly_dfs(quarterly_period_ends)
    a_income, a_balance, a_cashflow = _annual_dfs(annual_period_ends)

    # Quarterly: exhaust the fallback chain entirely — both candidate rows
    # absent (Deferred Revenue is in q_balance by default; Current Deferred
    # Revenue was never added).
    q_balance = q_balance.drop(index="Deferred Revenue")
    assert "Current Deferred Revenue" not in q_balance.index

    # Annual: rename "Deferred Revenue" → "Current Deferred Revenue" to
    # ensure the fallback resolver walks past the primary key and hits the
    # secondary one.
    a_balance = a_balance.rename(index={"Deferred Revenue": "Current Deferred Revenue"})
    assert "Deferred Revenue" not in a_balance.index
    assert "Current Deferred Revenue" in a_balance.index

    stub = StubTicker(
        info=_good_info("AAPL"),
        quarterly_income_stmt=q_income,
        quarterly_balance_sheet=q_balance,
        quarterly_cashflow=q_cashflow,
        income_stmt=a_income,
        balance_sheet=a_balance,
        cashflow=a_cashflow,
    )

    with yfinance_client.use_ticker_factory_for_test(make_stub_factory(stub)):
        report = refresh_yfinance_ticker(tmp_duckdb, "AAPL")

    # 1. Field appears in missing_fields (from quarterly's list only).
    missing = report.metadata["missing_fields"]
    assert "deferred_revenue_usd" in missing
    assert missing.count("deferred_revenue_usd") == 1

    # 2. Quarterly rows: deferred_revenue_usd IS NULL for every period (the
    # fallback chain was exhausted).
    quarterly_deferred = tmp_duckdb.execute(
        "SELECT deferred_revenue_usd FROM quarterly_financials "
        "WHERE ticker = 'AAPL'"
    ).fetchall()
    assert len(quarterly_deferred) == 2
    assert all(value is None for (value,) in quarterly_deferred)

    # 3. Annual rows: deferred_revenue_usd non-NULL (fallback hit) — values
    # match the stub's "Current Deferred Revenue" cell.
    annual_deferred = tmp_duckdb.execute(
        "SELECT deferred_revenue_usd FROM annual_financials WHERE ticker = 'AAPL'"
    ).fetchall()
    assert len(annual_deferred) == 2
    assert all(value == 5_000_000_000 for (value,) in annual_deferred)

    # 4. Audit row's metadata matches the in-memory report.
    audit_meta_json = tmp_duckdb.execute(
        "SELECT metadata FROM ingestion_runs WHERE ticker = 'AAPL'"
    ).fetchone()[0]
    audit_missing = json.loads(audit_meta_json)["missing_fields"]
    assert "deferred_revenue_usd" in audit_missing
    assert audit_missing.count("deferred_revenue_usd") == 1
