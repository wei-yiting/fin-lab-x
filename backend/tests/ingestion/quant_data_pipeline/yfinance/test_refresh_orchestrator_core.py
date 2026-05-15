"""Unit tests for the yfinance ``refresh_yfinance_ticker`` orchestrator.

Tests exercise the full stage 1/2/3 sequence against the foundation
``tmp_duckdb`` fixture (auto-discovered from the parent conftest) and the
``use_ticker_factory_for_test`` ContextVar seam for happy-path stubs.
Retry tests bypass the ContextVar seam and ``monkeypatch.setattr`` the
``yfinance_client`` module-level function directly — the orchestrator
references the function via the module (``yfinance_client.fetch_quarterly_statements``),
so the patch lands at the resolution site.

``constants.RETRY_BASE_DELAY_SECONDS`` is monkeypatched to 0.0 in every
retry-exercising test so the suite never sleeps real time.
"""

import json
from datetime import date

import pandas as pd
import pytest

from backend.ingestion.quant_data_pipeline.yfinance import (
    constants,
    yfinance_client,
)
from backend.ingestion.quant_data_pipeline.yfinance.refresh_orchestrator import (
    refresh_yfinance_ticker,
)
from backend.ingestion.quant_data_pipeline.yfinance.yfinance_pipeline_errors import (
    YFinanceEmptyResponseError,
    YFinanceRateLimitError,
)
from backend.tests.ingestion.quant_data_pipeline.yfinance.stubs import (
    StubTicker,
    make_stub_factory,
)


# ---------------------------------------------------------------------------
# Local fixture helpers (kept in this file — not in shared stubs.py)
# ---------------------------------------------------------------------------
# MSFT-aligned fiscal calendar: 1751241600 → UTC 2025-06-30, so fy_end_month=6.


_MSFT_FY_END_UNIX = 1751241600
# 1735603200 → UTC 2024-12-31 (calendar-year FYE).
_CY_FY_END_UNIX = 1735603200
# 1769299200 → UTC 2026-01-25 (NVDA-style FYE).
_NVDA_FY_END_UNIX = 1769299200


def _good_info(ticker: str = "MSFT", **overrides) -> dict:
    """Return a fully-populated yfinance ``info`` dict the DTO builder accepts."""
    base = {
        "longName": f"{ticker} Inc.",
        "sector": "Technology",
        "industry": "Software",
        "lastFiscalYearEnd": _MSFT_FY_END_UNIX,
        "marketCap": 3_400_000_000_000,
        "enterpriseValue": 3_500_000_000_000,
        "trailingPE": 35.0,
        "forwardPE": 32.0,
        "priceToBook": 14.0,
        "priceToSalesTrailing12Months": 13.0,
        "enterpriseToEbitda": 25.0,
        "trailingPegRatio": 2.2,
        "dividendYield": 0.46,
        "beta": 0.9,
        "heldPercentInstitutions": 0.7598,
    }
    base.update(overrides)
    return base


def _quarterly_statement_dfs(
    period_ends: list[date] | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Build (income, balance, cashflow) DataFrames with every line item populated."""
    if period_ends is None:
        period_ends = [
            date(2024, 9, 30),
            date(2024, 12, 31),
            date(2025, 3, 31),
            date(2025, 6, 30),
        ]
    income = pd.DataFrame.from_dict(
        {
            "Total Revenue": {p: 50_000_000_000 + i * 1_000_000_000 for i, p in enumerate(period_ends)},
            "Cost Of Revenue": {p: 20_000_000_000 for p in period_ends},
            "Gross Profit": {p: 30_000_000_000 for p in period_ends},
            "Net Income": {p: 12_000_000_000 for p in period_ends},
            "Interest Income": {p: 200_000_000 for p in period_ends},
            "Diluted EPS": {p: 1.61 for p in period_ends},
            "Diluted Average Shares": {p: 7_450_000_000 for p in period_ends},
        },
        orient="index",
    )
    balance = pd.DataFrame.from_dict(
        {
            "Total Assets": {p: 510_000_000_000 for p in period_ends},
            "Stockholders Equity": {p: 245_000_000_000 for p in period_ends},
            "Goodwill": {p: 65_000_000_000 for p in period_ends},
        },
        orient="index",
    )
    cashflow = pd.DataFrame.from_dict(
        {
            "Operating Cash Flow": {p: 25_000_000_000 for p in period_ends},
            "Capital Expenditure": {p: -7_000_000_000 for p in period_ends},
            "Free Cash Flow": {p: 18_000_000_000 for p in period_ends},
        },
        orient="index",
    )
    return income, balance, cashflow


def _annual_statement_dfs(
    period_ends: list[date] | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Annual-cadence (income, balance, cashflow) DataFrames."""
    if period_ends is None:
        period_ends = [
            date(2023, 6, 30),
            date(2024, 6, 30),
            date(2025, 6, 30),
        ]
    income = pd.DataFrame.from_dict(
        {
            "Total Revenue": {p: 240_000_000_000 + i * 10_000_000_000 for i, p in enumerate(period_ends)},
            "Net Income": {p: 80_000_000_000 for p in period_ends},
            "Diluted EPS": {p: 11.5 for p in period_ends},
        },
        orient="index",
    )
    balance = pd.DataFrame.from_dict(
        {
            "Total Assets": {p: 510_000_000_000 for p in period_ends},
            "Stockholders Equity": {p: 245_000_000_000 for p in period_ends},
        },
        orient="index",
    )
    cashflow = pd.DataFrame.from_dict(
        {
            "Operating Cash Flow": {p: 110_000_000_000 for p in period_ends},
            "Free Cash Flow": {p: 80_000_000_000 for p in period_ends},
        },
        orient="index",
    )
    return income, balance, cashflow


def _happy_stub(ticker: str = "MSFT") -> StubTicker:
    """A StubTicker pre-filled with everything ``refresh_yfinance_ticker`` needs."""
    q_income, q_balance, q_cashflow = _quarterly_statement_dfs()
    a_income, a_balance, a_cashflow = _annual_statement_dfs()
    return StubTicker(
        info=_good_info(ticker),
        quarterly_income_stmt=q_income,
        quarterly_balance_sheet=q_balance,
        quarterly_cashflow=q_cashflow,
        income_stmt=a_income,
        balance_sheet=a_balance,
        cashflow=a_cashflow,
    )


def _make_flaky(attempts_to_fail: int, success_value):
    """Return a stub fn that raises ``YFinanceRateLimitError`` for the first N calls.

    On call N+1 (and beyond) it returns ``success_value``. Used to drive the
    retry loop in ``_retry_with_counter`` without hitting yfinance.
    """
    state = {"calls": 0}

    def f(_ticker: str):
        state["calls"] += 1
        if state["calls"] <= attempts_to_fail:
            raise YFinanceRateLimitError(f"transient {state['calls']}")
        return success_value

    return f


# Standard metadata key set the orchestrator always emits.
_EXPECTED_META_KEYS = {
    "periods_covered",
    "rows_per_table",
    "missing_fields",
    "pacing",
    "retry_count",
    "error_stage",
}


# ---------------------------------------------------------------------------
# 1. Happy path: 6-key metadata + error_stage cleared
# ---------------------------------------------------------------------------


def test_success_returns_report_with_5_plus_1_keys(tmp_duckdb, monkeypatch):
    monkeypatch.setattr(constants, "PACING_MIN_INTERVAL_SECONDS", 0.0)
    stub = _happy_stub("MSFT")
    with yfinance_client.use_ticker_factory_for_test(make_stub_factory(stub)):
        report = refresh_yfinance_ticker(tmp_duckdb, "MSFT")

    assert set(report.metadata.keys()) == _EXPECTED_META_KEYS
    assert report.metadata["error_stage"] is None
    assert report.rows_written_total > 0


# ---------------------------------------------------------------------------
# 2. Success audit row + JSON-deserialisable metadata
# ---------------------------------------------------------------------------


def test_success_audit_row_status_success(tmp_duckdb, monkeypatch):
    monkeypatch.setattr(constants, "PACING_MIN_INTERVAL_SECONDS", 0.0)
    stub = _happy_stub("MSFT")
    with yfinance_client.use_ticker_factory_for_test(make_stub_factory(stub)):
        refresh_yfinance_ticker(tmp_duckdb, "MSFT")

    row = tmp_duckdb.execute(
        "SELECT status, rows_written_total, error_class, metadata "
        "FROM ingestion_runs WHERE ticker = 'MSFT'"
    ).fetchone()
    assert row is not None
    status, n_rows, err_class, meta_json = row
    assert status == "success"
    assert n_rows > 0
    assert err_class is None

    parsed = json.loads(meta_json)
    assert isinstance(parsed, dict)
    assert set(parsed.keys()) == _EXPECTED_META_KEYS


# ---------------------------------------------------------------------------
# 3. Ticker normalize: strip + upper applied everywhere
# ---------------------------------------------------------------------------


def test_ticker_normalize_strip_upper_in_all_sites(tmp_duckdb, monkeypatch):
    monkeypatch.setattr(constants, "PACING_MIN_INTERVAL_SECONDS", 0.0)
    stub = _happy_stub("MSFT")
    with yfinance_client.use_ticker_factory_for_test(make_stub_factory(stub)):
        refresh_yfinance_ticker(tmp_duckdb, "  msft  ")

    sites = [
        ("ingestion_runs", "SELECT DISTINCT ticker FROM ingestion_runs"),
        ("companies", "SELECT DISTINCT ticker FROM companies"),
        ("market_valuations", "SELECT DISTINCT ticker FROM market_valuations"),
        ("quarterly_financials", "SELECT DISTINCT ticker FROM quarterly_financials"),
        ("annual_financials", "SELECT DISTINCT ticker FROM annual_financials"),
    ]
    for table, sql in sites:
        rows = tmp_duckdb.execute(sql).fetchall()
        assert rows, f"no rows in {table}"
        # Both positive (only MSFT exists) AND negative (no padded / lowercase
        # variant leaked) are verified by this single equality assertion.
        assert rows == [("MSFT",)], f"{table} contained unexpected ticker(s): {rows}"


# ---------------------------------------------------------------------------
# 4. Failure path: caller exception has no partial-report attribute
# ---------------------------------------------------------------------------


def test_failure_caller_has_no_partial_report_attribute(tmp_duckdb, monkeypatch):
    monkeypatch.setattr(constants, "PACING_MIN_INTERVAL_SECONDS", 0.0)
    monkeypatch.setattr(constants, "RETRY_BASE_DELAY_SECONDS", 0.0)

    stub = _happy_stub("MSFT")
    monkeypatch.setattr(
        yfinance_client,
        "fetch_quarterly_statements",
        _make_flaky(constants.RETRY_MAX_ATTEMPTS + 5, None),
    )
    with yfinance_client.use_ticker_factory_for_test(make_stub_factory(stub)):
        with pytest.raises(YFinanceRateLimitError) as exc_info:
            refresh_yfinance_ticker(tmp_duckdb, "MSFT")

    e = exc_info.value
    assert not hasattr(e, "report")
    assert not hasattr(e, "partial")
    assert not hasattr(e, "rows_written")


# ---------------------------------------------------------------------------
# 5. Failure path: audit row committed before raise
# ---------------------------------------------------------------------------


def test_failure_audit_row_committed_before_raise(tmp_duckdb, monkeypatch):
    monkeypatch.setattr(constants, "PACING_MIN_INTERVAL_SECONDS", 0.0)
    monkeypatch.setattr(constants, "RETRY_BASE_DELAY_SECONDS", 0.0)

    stub = _happy_stub("MSFT")
    # Quarterly fetch returns empty DataFrames → ``build_quarterly_rows``
    # raises ``YFinanceEmptyResponseError``.
    monkeypatch.setattr(
        yfinance_client,
        "fetch_quarterly_statements",
        lambda _t: (pd.DataFrame(), pd.DataFrame(), pd.DataFrame()),
    )
    with yfinance_client.use_ticker_factory_for_test(make_stub_factory(stub)):
        with pytest.raises(YFinanceEmptyResponseError):
            refresh_yfinance_ticker(tmp_duckdb, "MSFT")

    row = tmp_duckdb.execute(
        "SELECT status, error_class FROM ingestion_runs WHERE ticker = 'MSFT'"
    ).fetchone()
    assert row is not None
    assert row == ("error", "YFinanceEmptyResponseError")


# ---------------------------------------------------------------------------
# 6. Partial-success error path: 6 keys + partial rows_per_table
# ---------------------------------------------------------------------------


def test_error_path_metadata_5_plus_1_keys_with_partial_rows_per_table(
    tmp_duckdb, monkeypatch,
):
    monkeypatch.setattr(constants, "PACING_MIN_INTERVAL_SECONDS", 0.0)
    monkeypatch.setattr(constants, "RETRY_BASE_DELAY_SECONDS", 0.0)

    stub = _happy_stub("MSFT")
    # info + quarterly succeed (default stub); annual fetch is patched to fail
    # on every attempt.
    monkeypatch.setattr(
        yfinance_client,
        "fetch_annual_statements",
        _make_flaky(constants.RETRY_MAX_ATTEMPTS + 5, None),
    )
    with yfinance_client.use_ticker_factory_for_test(make_stub_factory(stub)):
        with pytest.raises(YFinanceRateLimitError):
            refresh_yfinance_ticker(tmp_duckdb, "MSFT")

    row = tmp_duckdb.execute(
        "SELECT metadata FROM ingestion_runs WHERE ticker = 'MSFT'"
    ).fetchone()
    assert row is not None
    parsed = json.loads(row[0])

    assert set(parsed.keys()) == _EXPECTED_META_KEYS
    assert set(parsed["rows_per_table"].keys()) == {
        "companies",
        "market_valuations",
        "quarterly_financials",
    }
    assert parsed["retry_count"] == constants.RETRY_MAX_ATTEMPTS - 1
    assert parsed["error_stage"] == "annual"


# ---------------------------------------------------------------------------
# 7. lastFiscalYearEnd anomaly variants all converge to one error
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "fy_end_value",
    [None, 0, -1, "missing"],
)
def test_lastFiscalYearEnd_4_variants_unified_error(
    tmp_duckdb, monkeypatch, fy_end_value,
):
    monkeypatch.setattr(constants, "PACING_MIN_INTERVAL_SECONDS", 0.0)

    info = _good_info("MSFT")
    if fy_end_value == "missing":
        info.pop("lastFiscalYearEnd")
    else:
        info["lastFiscalYearEnd"] = fy_end_value

    stub = _happy_stub("MSFT")
    stub.info = info

    with yfinance_client.use_ticker_factory_for_test(make_stub_factory(stub)):
        with pytest.raises(YFinanceEmptyResponseError):
            refresh_yfinance_ticker(tmp_duckdb, "MSFT")

    row = tmp_duckdb.execute(
        "SELECT error_class, metadata FROM ingestion_runs WHERE ticker = 'MSFT'"
    ).fetchone()
    assert row is not None
    err_class, meta_json = row
    assert err_class == "YFinanceEmptyResponseError"
    parsed = json.loads(meta_json)
    assert parsed["error_stage"] == "normalize"


# ---------------------------------------------------------------------------
# 8. retry_count == max_attempts - 1 when every attempt fails
# ---------------------------------------------------------------------------


def test_retry_count_all_fail_equals_max_minus_one(tmp_duckdb, monkeypatch):
    monkeypatch.setattr(constants, "PACING_MIN_INTERVAL_SECONDS", 0.0)
    monkeypatch.setattr(constants, "RETRY_BASE_DELAY_SECONDS", 0.0)

    stub = _happy_stub("MSFT")
    monkeypatch.setattr(
        yfinance_client,
        "fetch_quarterly_statements",
        _make_flaky(constants.RETRY_MAX_ATTEMPTS + 5, None),
    )
    with yfinance_client.use_ticker_factory_for_test(make_stub_factory(stub)):
        with pytest.raises(YFinanceRateLimitError):
            refresh_yfinance_ticker(tmp_duckdb, "MSFT")

    row = tmp_duckdb.execute(
        "SELECT status, metadata FROM ingestion_runs WHERE ticker = 'MSFT'"
    ).fetchone()
    assert row is not None
    status, meta_json = row
    assert status == "error"
    parsed = json.loads(meta_json)
    assert parsed["retry_count"] == constants.RETRY_MAX_ATTEMPTS - 1


# ---------------------------------------------------------------------------
# 9. Success on third attempt → retry_count == 2
# ---------------------------------------------------------------------------


def test_retry_count_success_on_third_attempt_equals_two(tmp_duckdb, monkeypatch):
    monkeypatch.setattr(constants, "PACING_MIN_INTERVAL_SECONDS", 0.0)
    monkeypatch.setattr(constants, "RETRY_BASE_DELAY_SECONDS", 0.0)

    stub = _happy_stub("MSFT")
    q_dfs = _quarterly_statement_dfs()
    # Two failures then success — the wrapper retries 2× and the third call returns.
    monkeypatch.setattr(
        yfinance_client, "fetch_quarterly_statements", _make_flaky(2, q_dfs),
    )
    with yfinance_client.use_ticker_factory_for_test(make_stub_factory(stub)):
        report = refresh_yfinance_ticker(tmp_duckdb, "MSFT")

    assert report.metadata["retry_count"] == 2

    row = tmp_duckdb.execute(
        "SELECT status, metadata FROM ingestion_runs WHERE ticker = 'MSFT'"
    ).fetchone()
    assert row is not None
    status, meta_json = row
    assert status == "success"
    parsed = json.loads(meta_json)
    assert parsed["retry_count"] == 2


# ---------------------------------------------------------------------------
# 10. Pacing: 1 retry in info → 8 calls total
# ---------------------------------------------------------------------------


def test_pacing_calls_eight_with_one_retry_in_info(tmp_duckdb, monkeypatch):
    monkeypatch.setattr(constants, "PACING_MIN_INTERVAL_SECONDS", 0.001)
    monkeypatch.setattr(constants, "RETRY_BASE_DELAY_SECONDS", 0.0)

    # info fails once, succeeds on attempt 1. The stub-backed fetch_info path
    # is the one that touches yfinance_client._pace, so we route the failing
    # attempt through the same pacing-aware function.
    happy_info = _good_info("MSFT")
    state = {"calls": 0}

    def flaky_fetch_info(_ticker: str) -> dict:
        # Tick the pacing counter so test 10 measures the real call count.
        yfinance_client._pace()
        state["calls"] += 1
        if state["calls"] == 1:
            raise YFinanceRateLimitError("first attempt 429")
        return happy_info

    monkeypatch.setattr(yfinance_client, "fetch_info", flaky_fetch_info)

    # Use the ticker factory for the quarterly / annual paths which still
    # call _pace() inside fetch_quarterly_statements / fetch_annual_statements.
    stub = _happy_stub("MSFT")
    with yfinance_client.use_ticker_factory_for_test(make_stub_factory(stub)):
        report = refresh_yfinance_ticker(tmp_duckdb, "MSFT")

    # Calls accounted: 1 failed info + 1 success info + 3 quarterly + 3 annual = 8.
    assert report.metadata["pacing"]["calls"] == 8
    assert report.metadata["retry_count"] == 1


# ---------------------------------------------------------------------------
# 11. Pacing: no retry → 7 calls baseline
# ---------------------------------------------------------------------------


def test_pacing_calls_seven_with_no_retry_baseline(tmp_duckdb, monkeypatch):
    monkeypatch.setattr(constants, "PACING_MIN_INTERVAL_SECONDS", 0.001)
    monkeypatch.setattr(constants, "RETRY_BASE_DELAY_SECONDS", 0.0)

    stub = _happy_stub("MSFT")
    with yfinance_client.use_ticker_factory_for_test(make_stub_factory(stub)):
        report = refresh_yfinance_ticker(tmp_duckdb, "MSFT")

    assert report.metadata["pacing"]["calls"] == 7
    assert report.metadata["retry_count"] == 0


# ---------------------------------------------------------------------------
# 12. periods_covered["quarterly"] uses normalize_fiscal_period format
# ---------------------------------------------------------------------------


def test_periods_covered_quarterly_uses_normalize_fiscal_period_format(
    tmp_duckdb, monkeypatch,
):
    monkeypatch.setattr(constants, "PACING_MIN_INTERVAL_SECONDS", 0.0)

    # Calendar-year FYE: fy_end_month=12. Periods 2024-Q1..Q4; skip Q2.
    period_ends_calendar = [
        date(2024, 3, 31),
        date(2024, 6, 30),  # Q2 → forced NaN via Total Revenue.
        date(2024, 9, 30),
        date(2024, 12, 31),
    ]
    q_income, q_balance, q_cashflow = _quarterly_statement_dfs(period_ends_calendar)
    # Force Q2 (index 1) Total Revenue NaN.
    q_income.loc["Total Revenue", date(2024, 6, 30)] = float("nan")

    a_income, a_balance, a_cashflow = _annual_statement_dfs(
        [date(2022, 12, 31), date(2023, 12, 31), date(2024, 12, 31)],
    )
    stub = StubTicker(
        info=_good_info("CY", lastFiscalYearEnd=_CY_FY_END_UNIX),
        quarterly_income_stmt=q_income,
        quarterly_balance_sheet=q_balance,
        quarterly_cashflow=q_cashflow,
        income_stmt=a_income,
        balance_sheet=a_balance,
        cashflow=a_cashflow,
    )
    with yfinance_client.use_ticker_factory_for_test(make_stub_factory(stub)):
        report = refresh_yfinance_ticker(tmp_duckdb, "CY")

    assert report.metadata["periods_covered"]["quarterly"] == [
        "2024Q1",
        "2024Q3",
        "2024Q4",
    ]


# ---------------------------------------------------------------------------
# 13. Quarterly normalize uses company.fy_end_month built in Stage 1
# ---------------------------------------------------------------------------


def test_company_must_be_built_before_quarterly_uses_fy_end_month(
    tmp_duckdb, monkeypatch,
):
    monkeypatch.setattr(constants, "PACING_MIN_INTERVAL_SECONDS", 0.0)

    nvda_period = date(2025, 10, 26)
    q_income, q_balance, q_cashflow = _quarterly_statement_dfs([nvda_period])
    a_income, a_balance, a_cashflow = _annual_statement_dfs(
        [date(2024, 1, 28), date(2025, 1, 26)],
    )
    stub = StubTicker(
        info=_good_info("NVDA", lastFiscalYearEnd=_NVDA_FY_END_UNIX),
        quarterly_income_stmt=q_income,
        quarterly_balance_sheet=q_balance,
        quarterly_cashflow=q_cashflow,
        income_stmt=a_income,
        balance_sheet=a_balance,
        cashflow=a_cashflow,
    )
    with yfinance_client.use_ticker_factory_for_test(make_stub_factory(stub)):
        refresh_yfinance_ticker(tmp_duckdb, "NVDA")

    row = tmp_duckdb.execute(
        "SELECT fiscal_year, fiscal_quarter FROM quarterly_financials "
        "WHERE ticker = 'NVDA'"
    ).fetchone()
    assert row == (2026, 3)
