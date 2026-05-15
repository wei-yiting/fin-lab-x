"""Behavioural integration tests for the yfinance ingestion entrypoint.

Covers BDD scenarios:

* S-yfinance-10 — idempotent re-run uses the NEW fetched value, never the
  leftover DB state from a previously failed run.
* S-yfinance-11 — a restated period overwrites the same PK row; the audit
  log retains both run rows (no history on the data side).
* S-yfinance-12 — yfinance's upsert only writes the ``YFINANCE_OWNED_COLUMNS``
  set (driven by ``YFinanceQuarterlyRow`` fields), so SEC-only columns
  pre-existing on the same PK row survive untouched.

The helpers (``_good_info_aapl`` / ``_quarterly_dfs_for_aapl`` /
``_annual_dfs_for_aapl``) are deliberately duplicated locally rather than
shared via ``stubs.py`` to keep the AAPL-specific fixtures isolated to this
file — the parameters they encode (FY-end month 9, period-end Sep 30, 2024)
are load-bearing for the scenarios below and would obscure the more generic
MSFT-flavoured helpers in ``test_refresh_orchestrator_core.py`` if merged.
"""

from datetime import date, datetime, timezone

import pandas as pd

from backend.ingestion.quant_data_pipeline.calendar_to_fiscal_period import (
    normalize_fiscal_period,
)
from backend.ingestion.quant_data_pipeline.yfinance import (
    YFINANCE_OWNED_COLUMNS,
    constants,
    yfinance_client,
)
from backend.ingestion.quant_data_pipeline.yfinance.refresh_orchestrator import (
    refresh_yfinance_ticker,
)
from backend.ingestion.quant_data_pipeline.yfinance.yfinance_pipeline_errors import (
    YFinanceRateLimitError,
)
from backend.tests.ingestion.quant_data_pipeline.yfinance.stubs import (
    StubTicker,
    make_stub_factory,
)

# ---------------------------------------------------------------------------
# AAPL-flavoured fixture helpers
# ---------------------------------------------------------------------------
# Verified via datetime.fromtimestamp(unix, tz=timezone.utc).date():
#   1695945600 → 2023-09-29 UTC  (fy_end_month=9, fy_end_day=29)
#   1696032000 → 2023-09-30 UTC  (fy_end_month=9, fy_end_day=30)
_AAPL_FY_END_UNIX_DAY_29 = 1695945600
_AAPL_FY_END_UNIX_DAY_30 = 1696032000


def _good_info_aapl(fy_end_unix: int) -> dict:
    """Return a fully-populated yfinance ``info`` dict for AAPL."""
    return {
        "longName": "Apple Inc.",
        "sector": "Technology",
        "industry": "Consumer Electronics",
        "lastFiscalYearEnd": fy_end_unix,
        "marketCap": 3_400_000_000_000,
        "enterpriseValue": 3_500_000_000_000,
        "trailingPE": 30.0,
        "forwardPE": 27.0,
        "priceToBook": 50.0,
        "priceToSalesTrailing12Months": 9.0,
        "enterpriseToEbitda": 22.0,
        "trailingPegRatio": 2.0,
        "dividendYield": 0.46,
        "beta": 1.2,
        "heldPercentInstitutions": 0.61,
    }


def _quarterly_dfs_for_aapl(
    period_end: date, total_revenue: int,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Single-period quarterly statement triple.

    Income carries every line item the DTO maps so the row materialises;
    balance / cashflow stay minimal but valid.
    """
    income = pd.DataFrame.from_dict(
        {
            "Total Revenue": {period_end: total_revenue},
            "Cost Of Revenue": {period_end: 50_000_000_000},
            "Gross Profit": {period_end: 39_000_000_000},
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
            "Capital Expenditure": {period_end: -3_000_000_000},
            "Free Cash Flow": {period_end: 27_000_000_000},
        },
        orient="index",
    )
    return income, balance, cashflow


def _annual_dfs_for_aapl(
    period_end: date, total_revenue: int,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Single-period annual statement triple (same shape as quarterly)."""
    income = pd.DataFrame.from_dict(
        {
            "Total Revenue": {period_end: total_revenue},
            "Net Income": {period_end: 95_000_000_000},
            "Diluted EPS": {period_end: 6.0},
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
            "Operating Cash Flow": {period_end: 110_000_000_000},
            "Free Cash Flow": {period_end: 95_000_000_000},
        },
        orient="index",
    )
    return income, balance, cashflow


def _aapl_stub(
    fy_end_unix: int,
    quarterly_period_end: date,
    quarterly_revenue: int,
    annual_period_end: date,
    annual_revenue: int,
) -> StubTicker:
    """A StubTicker pre-filled for a single-period AAPL run."""
    q_income, q_balance, q_cashflow = _quarterly_dfs_for_aapl(
        quarterly_period_end, quarterly_revenue,
    )
    a_income, a_balance, a_cashflow = _annual_dfs_for_aapl(
        annual_period_end, annual_revenue,
    )
    return StubTicker(
        info=_good_info_aapl(fy_end_unix),
        quarterly_income_stmt=q_income,
        quarterly_balance_sheet=q_balance,
        quarterly_cashflow=q_cashflow,
        income_stmt=a_income,
        balance_sheet=a_balance,
        cashflow=a_cashflow,
    )


# ---------------------------------------------------------------------------
# Test 1 — Module-level surface: YFINANCE_OWNED_COLUMNS shape + content
# ---------------------------------------------------------------------------
# S-yfinance-12 surface guard.


def test_module_level_owned_columns_is_frozenset():
    assert isinstance(YFINANCE_OWNED_COLUMNS, frozenset)
    assert "total_revenue_usd" in YFINANCE_OWNED_COLUMNS
    # SEC-only columns must NOT appear in the yfinance-owned set.
    for sec_col in (
        "product_revenue_usd",
        "service_revenue_usd",
        "current_rpo_usd",
        "noncurrent_rpo_usd",
        "total_lease_obligation_usd",
    ):
        assert sec_col not in YFINANCE_OWNED_COLUMNS


# ---------------------------------------------------------------------------
# Test 2 — Re-run uses NEW fetched value, not leftover DB state (S-yfinance-10)
# ---------------------------------------------------------------------------


def test_rerun_uses_new_fetched_value_not_leftover_db_state(tmp_duckdb, monkeypatch):
    monkeypatch.setattr(constants, "PACING_MIN_INTERVAL_SECONDS", 0.0)
    monkeypatch.setattr(constants, "RETRY_BASE_DELAY_SECONDS", 0.0)

    # Sanity-check the two timestamps yield different fy_end_day so the
    # assertion below has discriminating power.
    assert (
        datetime.fromtimestamp(_AAPL_FY_END_UNIX_DAY_29, tz=timezone.utc).date()
        == date(2023, 9, 29)
    )
    assert (
        datetime.fromtimestamp(_AAPL_FY_END_UNIX_DAY_30, tz=timezone.utc).date()
        == date(2023, 9, 30)
    )

    # ---- Run A: info + quarterly succeed; annual fails every attempt ----
    stub_a = _aapl_stub(
        fy_end_unix=_AAPL_FY_END_UNIX_DAY_29,
        quarterly_period_end=date(2024, 9, 30),
        quarterly_revenue=89_000_000_000,
        annual_period_end=date(2024, 9, 30),
        annual_revenue=380_000_000_000,
    )

    def _always_rate_limit(_ticker: str):
        raise YFinanceRateLimitError("simulated 429 on annual stage")

    monkeypatch.setattr(
        yfinance_client, "fetch_annual_statements", _always_rate_limit,
    )

    with yfinance_client.use_ticker_factory_for_test(make_stub_factory(stub_a)):
        try:
            refresh_yfinance_ticker(tmp_duckdb, "AAPL")
        except YFinanceRateLimitError:
            pass
        else:
            raise AssertionError("Run A should have raised YFinanceRateLimitError")

    # Pre-condition: Run A left fy_end_day=29 in companies.
    row_after_a = tmp_duckdb.execute(
        "SELECT fy_end_month, fy_end_day FROM companies WHERE ticker = 'AAPL'"
    ).fetchone()
    assert row_after_a == (9, 29)

    # ---- Run B: clear the annual-stage monkeypatch, all stages succeed ----
    monkeypatch.undo()
    monkeypatch.setattr(constants, "PACING_MIN_INTERVAL_SECONDS", 0.0)
    monkeypatch.setattr(constants, "RETRY_BASE_DELAY_SECONDS", 0.0)

    stub_b = _aapl_stub(
        fy_end_unix=_AAPL_FY_END_UNIX_DAY_30,
        quarterly_period_end=date(2024, 9, 30),
        quarterly_revenue=89_000_000_000,
        annual_period_end=date(2024, 9, 30),
        annual_revenue=380_000_000_000,
    )
    with yfinance_client.use_ticker_factory_for_test(make_stub_factory(stub_b)):
        refresh_yfinance_ticker(tmp_duckdb, "AAPL")

    # The whole point: Run B's NEW fy_end_day (30) wins over Run A's leftover (29).
    row_after_b = tmp_duckdb.execute(
        "SELECT fy_end_month, fy_end_day FROM companies WHERE ticker = 'AAPL'"
    ).fetchone()
    assert row_after_b == (9, 30)

    # Audit table retains both runs in started_at order: error → success.
    audit_rows = tmp_duckdb.execute(
        "SELECT status FROM ingestion_runs "
        "WHERE ticker = 'AAPL' ORDER BY started_at ASC"
    ).fetchall()
    assert audit_rows == [("error",), ("success",)]


# ---------------------------------------------------------------------------
# Test 3 — Restated period overwrites the same PK row, audit keeps both runs
# ---------------------------------------------------------------------------
# S-yfinance-11.


def test_restated_period_overwrites_same_pk_row_audit_retains_both_runs(
    tmp_duckdb, monkeypatch,
):
    monkeypatch.setattr(constants, "PACING_MIN_INTERVAL_SECONDS", 0.0)

    # AAPL FY end day 30 → fy_end_month=9. period_end Sep 30, 2024 with
    # fy_end_month=9 normalises to (fiscal_year=2024, fiscal_quarter=4) —
    # confirmed by normalize_fiscal_period(date(2024,9,30), 9) == (2024, 4).
    assert normalize_fiscal_period(date(2024, 9, 30), 9) == (2024, 4)

    quarterly_period_end = date(2024, 9, 30)
    annual_period_end = date(2024, 9, 30)

    # ---- Run A: revenue 89B ----
    stub_a = _aapl_stub(
        fy_end_unix=_AAPL_FY_END_UNIX_DAY_30,
        quarterly_period_end=quarterly_period_end,
        quarterly_revenue=89_000_000_000,
        annual_period_end=annual_period_end,
        annual_revenue=380_000_000_000,
    )
    with yfinance_client.use_ticker_factory_for_test(make_stub_factory(stub_a)):
        refresh_yfinance_ticker(tmp_duckdb, "AAPL")

    # ---- Run B: same PK (FY2024 Q4), restated revenue 90.5B ----
    stub_b = _aapl_stub(
        fy_end_unix=_AAPL_FY_END_UNIX_DAY_30,
        quarterly_period_end=quarterly_period_end,
        quarterly_revenue=90_500_000_000,
        annual_period_end=annual_period_end,
        annual_revenue=380_000_000_000,
    )
    with yfinance_client.use_ticker_factory_for_test(make_stub_factory(stub_b)):
        refresh_yfinance_ticker(tmp_duckdb, "AAPL")

    # Exactly one row for the PK, and the restated value wins.
    rows = tmp_duckdb.execute(
        "SELECT total_revenue_usd FROM quarterly_financials "
        "WHERE ticker = 'AAPL' AND fiscal_year = 2024 AND fiscal_quarter = 4"
    ).fetchall()
    assert len(rows) == 1
    assert rows[0][0] == 90_500_000_000

    # No surviving history of the pre-restatement value.
    stale = tmp_duckdb.execute(
        "SELECT COUNT(*) FROM quarterly_financials "
        "WHERE ticker = 'AAPL' AND total_revenue_usd = 89000000000"
    ).fetchone()
    assert stale is not None
    assert stale[0] == 0

    # Audit retains both runs.
    audit_rows = tmp_duckdb.execute(
        "SELECT status FROM ingestion_runs "
        "WHERE ticker = 'AAPL' ORDER BY started_at ASC"
    ).fetchall()
    assert audit_rows == [("success",), ("success",)]


# ---------------------------------------------------------------------------
# Test 4 — yfinance upsert preserves SEC-only columns (S-yfinance-12)
# ---------------------------------------------------------------------------


def test_yfinance_upsert_preserves_sec_only_columns(tmp_duckdb, monkeypatch):
    monkeypatch.setattr(constants, "PACING_MIN_INTERVAL_SECONDS", 0.0)

    # Pre-seed the row with SEC-only column values; updated_at gets its
    # default. period_end is NOT NULL per schema, so include it explicitly.
    tmp_duckdb.execute(
        "INSERT INTO quarterly_financials "
        "(ticker, fiscal_year, fiscal_quarter, period_end, "
        " product_revenue_usd, service_revenue_usd) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        ["AAPL", 2024, 4, "2024-09-30", 200_000_000_000, 85_000_000_000],
    )
    # Verify the seed actually landed before exercising the orchestrator.
    seed = tmp_duckdb.execute(
        "SELECT product_revenue_usd, service_revenue_usd FROM quarterly_financials "
        "WHERE ticker = 'AAPL' AND fiscal_year = 2024 AND fiscal_quarter = 4"
    ).fetchone()
    assert seed == (200_000_000_000, 85_000_000_000)

    # ---- yfinance run: writes total_revenue_usd=285B for FY2024 Q4 ----
    stub = _aapl_stub(
        fy_end_unix=_AAPL_FY_END_UNIX_DAY_30,
        quarterly_period_end=date(2024, 9, 30),
        quarterly_revenue=285_000_000_000,
        annual_period_end=date(2024, 9, 30),
        annual_revenue=385_000_000_000,
    )
    with yfinance_client.use_ticker_factory_for_test(make_stub_factory(stub)):
        refresh_yfinance_ticker(tmp_duckdb, "AAPL")

    row = tmp_duckdb.execute(
        "SELECT total_revenue_usd, product_revenue_usd, service_revenue_usd "
        "FROM quarterly_financials "
        "WHERE ticker = 'AAPL' AND fiscal_year = 2024 AND fiscal_quarter = 4"
    ).fetchone()
    assert row is not None
    total_revenue, product_revenue, service_revenue = row

    # yfinance wrote its own column.
    assert total_revenue == 285_000_000_000
    # SEC-only columns are NOT in YFINANCE_OWNED_COLUMNS, so the upsert's
    # DO UPDATE SET clause never references them and the seeded values survive.
    assert product_revenue == 200_000_000_000
    assert service_revenue == 85_000_000_000

    # Defensive: keep the YFINANCE_OWNED_COLUMNS invariant the test relies on
    # documented in the test body itself — a regression that adds SEC columns
    # to the yfinance DTO would surface here as well as in Test 1.
    assert "product_revenue_usd" not in YFINANCE_OWNED_COLUMNS
    assert "service_revenue_usd" not in YFINANCE_OWNED_COLUMNS
