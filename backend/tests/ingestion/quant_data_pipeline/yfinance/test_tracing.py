"""Caller-aware tracing verification for ``refresh_yfinance_ticker``.

These two tests pin the contract that the OTel span fan-out is opt-in via an
outer trace:

* When the caller has opened a root span (here: a test-managed
  ``tracer.start_as_current_span("quant_data_refresh_ticker")``), each
  ``traced_span(...)`` site inside the orchestrator materialises as a child
  span on the global ``TracerProvider`` and per-attempt retry events nest
  under it as ``add_event("fetch_attempt", ...)`` records.

* When no outer span exists, ``traced_span(...)`` falls into its no-op
  branch and nothing reaches the in-memory exporter — even though the
  orchestrator still invokes ``traced_span`` three times and the refresh
  succeeds end-to-end.
"""

from datetime import date

import pandas as pd
import pytest
from opentelemetry import trace as otel_trace

from backend.ingestion.quant_data_pipeline.yfinance import (
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
# Inline stub helpers — kept lean; intentionally duplicated from the
# orchestrator-core tests so this file stays self-contained.
# ---------------------------------------------------------------------------

# 1751241600 → UTC 2025-06-30, the MSFT-aligned fiscal-year end.
_MSFT_FY_END_UNIX = 1751241600


def _good_info(ticker: str = "MSFT") -> dict:
    """Minimal yfinance ``info`` payload accepted by the DTO builder."""
    return {
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


def _quarterly_statement_dfs() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    period_ends = [
        date(2024, 9, 30),
        date(2024, 12, 31),
        date(2025, 3, 31),
        date(2025, 6, 30),
    ]
    income = pd.DataFrame.from_dict(
        {
            "Total Revenue": {p: 50_000_000_000 for p in period_ends},
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


def _annual_statement_dfs() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    period_ends = [
        date(2023, 6, 30),
        date(2024, 6, 30),
        date(2025, 6, 30),
    ]
    income = pd.DataFrame.from_dict(
        {
            "Total Revenue": {p: 240_000_000_000 for p in period_ends},
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


def _raise_rate_limit(_ticker: str):
    """Quarterly fetch stub that always raises ``YFinanceRateLimitError``."""
    raise YFinanceRateLimitError("boom")


# ---------------------------------------------------------------------------
# S-yfinance-16: outer span active → spans + nested retry events emitted
# ---------------------------------------------------------------------------


def test_failed_fetch_emits_outer_span_with_nested_retry_events(
    tmp_duckdb, monkeypatch, otel_in_memory_exporter,
):
    """Quarterly stage raises after 3 attempts; the resulting trace tree is:

    ``quant_data_refresh_ticker`` (root, test-owned)
        ``yf_fetch_info``                 — 1 success event
        ``yf_fetch_quarterly_statements`` — 3 error events

    ``yf_fetch_annual_statements`` MUST NOT appear because Stage 3 never runs.
    Each retry surfaces as a nested event on the *same* outer fetch span, not
    as three separate spans — the orchestrator opens one ``traced_span`` per
    fetch site and ``add_event`` is called per attempt inside it.
    """
    monkeypatch.setattr(constants, "RETRY_BASE_DELAY_SECONDS", 0.0)
    monkeypatch.setattr(constants, "PACING_MIN_INTERVAL_SECONDS", 0.0)

    stub = _happy_stub("MSFT")
    monkeypatch.setattr(
        yfinance_client, "fetch_quarterly_statements", _raise_rate_limit,
    )

    tracer = otel_trace.get_tracer("test")
    with tracer.start_as_current_span("quant_data_refresh_ticker"):
        with yfinance_client.use_ticker_factory_for_test(make_stub_factory(stub)):
            with pytest.raises(YFinanceRateLimitError):
                refresh_yfinance_ticker(tmp_duckdb, "MSFT")

    spans = otel_in_memory_exporter.get_finished_spans()
    names = [s.name for s in spans]

    # Span fan-out: outer root + 2 fetch sites (annual was never reached).
    assert "quant_data_refresh_ticker" in names
    assert "yf_fetch_info" in names
    assert "yf_fetch_quarterly_statements" in names
    assert "yf_fetch_annual_statements" not in names

    # Exactly one span per fetch site — retries are events, not spans.
    quarterly_spans = [s for s in spans if s.name == "yf_fetch_quarterly_statements"]
    assert len(quarterly_spans) == 1
    info_spans = [s for s in spans if s.name == "yf_fetch_info"]
    assert len(info_spans) == 1

    # Quarterly: 3 ``fetch_attempt`` events, all error, in increasing order.
    # The OTel SDK also records an auto-generated ``exception`` event when the
    # ``with`` block exits via the unhandled raise — filter to the per-attempt
    # events the orchestrator owns.
    quarterly_attempts = [
        e for e in quarterly_spans[0].events if e.name == "fetch_attempt"
    ]
    assert len(quarterly_attempts) == constants.RETRY_MAX_ATTEMPTS == 3
    for expected_attempt, event in enumerate(quarterly_attempts):
        assert event.attributes is not None
        assert event.attributes["attempt"] == expected_attempt
        assert event.attributes["status"] == "error"
        assert event.attributes["error_class"] == "YFinanceRateLimitError"

    # Info: succeeded on first attempt — one ``fetch_attempt`` event only.
    info_attempts = [
        e for e in info_spans[0].events if e.name == "fetch_attempt"
    ]
    assert len(info_attempts) == 1
    assert info_attempts[0].attributes is not None
    assert info_attempts[0].attributes["attempt"] == 0
    assert info_attempts[0].attributes["status"] == "success"


# ---------------------------------------------------------------------------
# S-yfinance-17: no outer span → no spans emitted; business path still works
# ---------------------------------------------------------------------------


def test_no_outer_span_emits_no_spans(
    tmp_duckdb, monkeypatch, otel_in_memory_exporter,
):
    """Without an outer ``@observe``/test root span, ``traced_span`` returns
    its no-op object — even though the orchestrator calls it three times
    (info, quarterly, annual), zero spans flush to the in-memory exporter.

    The refresh itself must still succeed end-to-end and persist an
    ``ingestion_runs`` audit row with ``status='success'``.
    """
    monkeypatch.setattr(constants, "PACING_MIN_INTERVAL_SECONDS", 0.0)
    stub = _happy_stub("MSFT")

    with yfinance_client.use_ticker_factory_for_test(make_stub_factory(stub)):
        report = refresh_yfinance_ticker(tmp_duckdb, "MSFT")

    # The exporter is wired to a real provider but no span was ever opened.
    # ``get_finished_spans()`` returns a tuple — compare via length to stay
    # agnostic of the concrete container type.
    assert len(otel_in_memory_exporter.get_finished_spans()) == 0

    # Business outcome is preserved.
    assert report.rows_written_total > 0
    row = tmp_duckdb.execute(
        "SELECT status FROM ingestion_runs WHERE ticker = 'MSFT'"
    ).fetchone()
    assert row is not None
    assert row[0] == "success"
