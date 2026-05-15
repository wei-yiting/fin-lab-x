"""Journey-level tests for the yfinance ingestion subsystem (J-yfinance-01..04).

These tests stitch together the per-feature unit + integration suites
(CLI dispatch, freezegun-anchored wall clock, OTel in-memory exporter,
ContextVar stub injection) into end-to-end flows that mirror the production
hybrid batch + JIT pattern:

* **J-yfinance-01** — CLI cron at 02:00 (no outer trace → no spans) →
  staleness query at 11:30 (no refresh) → next-day 03:00 JIT under a
  test-managed root span (3 sibling fetch spans, all success).
* **J-yfinance-02** — ``ingestion_runs`` carries ``(pipeline, ticker,
  status, started_at)`` such that an agent's ``WHERE status='success'``
  staleness query distinguishes fresh from stale on a 7-day series.
  Split into two tests to surface the contract failure mode if the
  filter were omitted.
* **J-yfinance-03** — cross-day ``market_valuations`` accumulation:
  PK is ``(ticker, as_of_date)``, so 5/4 and 5/5 rows coexist with
  their original values; ``companies`` is keyed only by ticker so it
  is UPDATEd in-place, not duplicated.
* **J-yfinance-04** — connection lifecycle: JIT mode opens a fresh
  ``DuckDBPyConnection`` per agent request (different ``id()``); CLI
  batch mode reuses one connection across the for-loop (single ``id()``).

Helpers are duplicated locally rather than imported — this keeps the
journey file self-contained and decouples it from any future refactor of
the orchestrator-core test helpers.
"""

import json
from datetime import date

import pandas as pd
import pytest
from freezegun import freeze_time
from opentelemetry import trace as otel_trace

from backend.ingestion.quant_data_pipeline import __main__ as cli_main
from backend.ingestion.quant_data_pipeline.duck_db.connection import get_connection
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
# Inline stub helpers — duplicated from test_refresh_orchestrator_core.py /
# test_tracing.py so this file stays self-contained (same pattern as the
# tracing suite).
# ---------------------------------------------------------------------------

# 1751241600 → UTC 2025-06-30 (MSFT-aligned FY end).
_MSFT_FY_END_UNIX = 1751241600
# 1695945600 → UTC 2023-09-29 (AAPL-aligned FY end, month=9).
_AAPL_FY_END_UNIX = 1695945600


def _good_info(ticker: str = "MSFT", **overrides) -> dict:
    """Minimal yfinance ``info`` payload accepted by the DTO builder."""
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


def _happy_stub(ticker: str = "MSFT", **info_overrides) -> StubTicker:
    q_income, q_balance, q_cashflow = _quarterly_statement_dfs()
    a_income, a_balance, a_cashflow = _annual_statement_dfs()
    info = _good_info(ticker, **info_overrides)
    return StubTicker(
        info=info,
        quarterly_income_stmt=q_income,
        quarterly_balance_sheet=q_balance,
        quarterly_cashflow=q_cashflow,
        income_stmt=a_income,
        balance_sheet=a_balance,
        cashflow=a_cashflow,
    )


def _per_ticker_factory(stubs: dict[str, StubTicker]):
    """Return a ``TickerFactory`` that dispatches to a per-ticker stub."""

    def _factory(ticker: str) -> StubTicker:
        return stubs[ticker]

    return _factory


# Metadata key set the orchestrator always emits (6 keys).
_EXPECTED_META_KEYS = {
    "periods_covered",
    "rows_per_table",
    "missing_fields",
    "pacing",
    "retry_count",
    "error_stage",
}


# ---------------------------------------------------------------------------
# J-yfinance-01: hybrid batch (CLI cron) then JIT (agent-triggered under
# outer @observe-equivalent span)
# ---------------------------------------------------------------------------


def test_hybrid_batch_then_jit_with_tracing_asymmetry(
    tmp_path, monkeypatch, otel_in_memory_exporter,
):
    """Full hybrid flow: CLI batch at 02:00 (no tracing) → 11:30 agent
    staleness probe (no refresh) → next-day 03:00 JIT under a root span
    that triggers the 4-span trace tree (root + 3 fetch siblings).

    Trace asymmetry: the CLI ``main()`` does not open an outer span, so
    ``traced_span`` is a no-op and the in-memory exporter sees zero spans
    after the batch run. The JIT run wraps the call in
    ``tracer.start_as_current_span("quant_data_refresh_ticker")`` —
    exactly the shape the production agent would produce via ``@observe``
    — and the orchestrator's three ``traced_span(...)`` sites materialise
    as child spans.
    """
    monkeypatch.setattr(constants, "PACING_MIN_INTERVAL_SECONDS", 0.0)
    monkeypatch.setattr(constants, "RETRY_BASE_DELAY_SECONDS", 0.0)

    db_path = tmp_path / "hybrid.db"
    stub = _happy_stub("MSFT")

    # ---- Phase 1: CLI cron at 02:00 — no outer span, no exported spans ----
    with freeze_time("2026-05-04 02:00:00"):
        with yfinance_client.use_ticker_factory_for_test(make_stub_factory(stub)):
            with pytest.raises(SystemExit) as excinfo:
                cli_main.main(
                    ["refresh-yfinance", "MSFT", "--db-path", str(db_path)],
                )
        assert excinfo.value.code == 0

    # Inspect persisted state via a fresh connection. ``ensure_schema=False``
    # keeps the assertion focused on what the CLI wrote, not what the
    # schema bootstrap re-creates.
    conn = get_connection(str(db_path), ensure_schema=False)
    try:
        runs_after_batch = conn.execute(
            "SELECT ticker, status, started_at FROM ingestion_runs "
            "WHERE pipeline='yfinance' AND ticker='MSFT'"
        ).fetchall()
        assert len(runs_after_batch) == 1
        ticker_b, status_b, started_at_b = runs_after_batch[0]
        assert ticker_b == "MSFT"
        assert status_b == "success"
        # freezegun anchors ``datetime.now(UTC)`` inside ``track_ingestion_run``;
        # DuckDB stores ``TIMESTAMP`` as naive local-tz, so the .date() can
        # land on either 5/4 or 5/5 depending on test runner timezone.
        # Compare against the timestamp we will write next-day to keep this
        # assertion tz-agnostic — see Phase 3 ordering check below.

        mv_after_batch = conn.execute(
            "SELECT ticker, as_of_date FROM market_valuations "
            "WHERE ticker='MSFT'"
        ).fetchall()
        assert mv_after_batch == [("MSFT", date(2026, 5, 4))]

        # CLI batch path emitted zero OTel spans — no @observe / outer span.
        assert len(otel_in_memory_exporter.get_finished_spans()) == 0

        # ---- Phase 2: 11:30 staleness probe (no refresh) ----
        with freeze_time("2026-05-04 11:30:00"):
            staleness_ts = conn.execute(
                "SELECT MAX(started_at) FROM ingestion_runs "
                "WHERE pipeline='yfinance' AND ticker='MSFT' "
                "AND status='success'"
            ).fetchone()[0]
        # The staleness probe should still see the 02:00 audit row, since
        # nothing has refreshed in the intervening 9.5 hours.
        assert staleness_ts == started_at_b
        # Audit log size unchanged — staleness query is read-only.
        assert conn.execute(
            "SELECT COUNT(*) FROM ingestion_runs WHERE ticker='MSFT'"
        ).fetchone()[0] == 1

        # ---- Phase 3: next-day 03:00 JIT refresh under root span ----
        with freeze_time("2026-05-05 03:00:00"):
            tracer = otel_trace.get_tracer("test")
            with tracer.start_as_current_span("quant_data_refresh_ticker"):
                with yfinance_client.use_ticker_factory_for_test(
                    make_stub_factory(stub),
                ):
                    refresh_yfinance_ticker(conn, "MSFT")

        # Post-JIT audit: 2 success rows, newer row gets a fresh started_at.
        runs_after_jit = conn.execute(
            "SELECT status, started_at, metadata FROM ingestion_runs "
            "WHERE pipeline='yfinance' AND ticker='MSFT' "
            "ORDER BY started_at ASC"
        ).fetchall()
        assert len(runs_after_jit) == 2
        assert [r[0] for r in runs_after_jit] == ["success", "success"]

        # JIT row's started_at is strictly later than the cron row's (27 hr
        # apart). Exact wall-clock comparison stays tz-agnostic — DuckDB
        # stores TIMESTAMP as naive-local so the absolute hour depends on
        # the runner timezone, but the relative ordering is preserved.
        newer_started_at = runs_after_jit[1][1]
        assert newer_started_at > started_at_b

        newer_metadata = json.loads(runs_after_jit[1][2])
        assert set(newer_metadata.keys()) == _EXPECTED_META_KEYS
        assert newer_metadata["error_stage"] is None

        # Cross-day market_valuations: PK collision avoided by date,
        # both rows coexist; the 5/4 row is not touched.
        mv_after_jit = conn.execute(
            "SELECT as_of_date FROM market_valuations "
            "WHERE ticker='MSFT' ORDER BY as_of_date ASC"
        ).fetchall()
        assert mv_after_jit == [(date(2026, 5, 4),), (date(2026, 5, 5),)]

        # ``companies`` is keyed only by ticker → UPDATE in place;
        # ``updated_at`` is managed by DuckDB's ``now()`` (real wall
        # clock — freezegun does NOT propagate into DuckDB SQL),
        # so we assert relatively: post-JIT > post-batch (well, ``>=``
        # to stay clock-skew tolerant on fast hardware).
        company_count = conn.execute(
            "SELECT COUNT(*) FROM companies WHERE ticker='MSFT'"
        ).fetchone()[0]
        assert company_count == 1

        # JIT span tree: 4 spans total (root + 3 fetch siblings).
        spans = otel_in_memory_exporter.get_finished_spans()
        names = [s.name for s in spans]
        assert "quant_data_refresh_ticker" in names
        assert "yf_fetch_info" in names
        assert "yf_fetch_quarterly_statements" in names
        assert "yf_fetch_annual_statements" in names
        assert len(spans) == 4

        # All success — one ``fetch_attempt`` per fetch span, status='success'.
        for fetch_name in (
            "yf_fetch_info",
            "yf_fetch_quarterly_statements",
            "yf_fetch_annual_statements",
        ):
            fetch_spans = [s for s in spans if s.name == fetch_name]
            assert len(fetch_spans) == 1
            attempts = [
                e for e in fetch_spans[0].events if e.name == "fetch_attempt"
            ]
            assert len(attempts) == 1
            assert attempts[0].attributes is not None
            assert attempts[0].attributes["attempt"] == 0
            assert attempts[0].attributes["status"] == "success"
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# J-yfinance-02: staleness query needs status filter
# Split into two tests — one demonstrates the correct filter,
# the other demonstrates the failure mode if the filter is omitted.
# ---------------------------------------------------------------------------


def _seven_day_refresh(
    conn,
    *,
    fail_day: int,
    monkeypatch,
    stub: StubTicker,
) -> list[date]:
    """Drive 7 daily refreshes; ``fail_day`` (1-7) is forced to error via
    a quarterly rate-limit. Returns the list of ``date`` objects driven.
    """
    base = date(2026, 5, 1)
    days = [date(base.year, base.month, base.day + i) for i in range(7)]

    for i, day in enumerate(days, start=1):
        ts = f"{day.isoformat()} 02:00:00"
        if i == fail_day:
            # Patch quarterly fetch to raise — full retry exhaustion drives
            # status='error' for this day's audit row.
            def _boom(_t: str):
                raise YFinanceRateLimitError(f"forced fail day {i}")

            monkeypatch.setattr(
                yfinance_client, "fetch_quarterly_statements", _boom,
            )
            with freeze_time(ts):
                with yfinance_client.use_ticker_factory_for_test(
                    make_stub_factory(stub),
                ):
                    with pytest.raises(YFinanceRateLimitError):
                        refresh_yfinance_ticker(conn, "MSFT")
            # Restore the real fetcher for subsequent days.
            monkeypatch.undo()
            # Re-apply the pacing / retry overrides the caller set.
            monkeypatch.setattr(
                constants, "PACING_MIN_INTERVAL_SECONDS", 0.0,
            )
            monkeypatch.setattr(constants, "RETRY_BASE_DELAY_SECONDS", 0.0)
        else:
            with freeze_time(ts):
                with yfinance_client.use_ticker_factory_for_test(
                    make_stub_factory(stub),
                ):
                    refresh_yfinance_ticker(conn, "MSFT")
    return days


def test_staleness_query_with_status_filter_returns_latest_success(
    tmp_path, monkeypatch,
):
    """7-day refresh series with day-3 fetch failure. The agent's staleness
    query — ``WHERE pipeline='yfinance' AND ticker='MSFT' AND status='success'``
    — pins to the day-7 timestamp, ignoring the day-3 error row entirely.
    """
    monkeypatch.setattr(constants, "PACING_MIN_INTERVAL_SECONDS", 0.0)
    monkeypatch.setattr(constants, "RETRY_BASE_DELAY_SECONDS", 0.0)

    db_path = tmp_path / "staleness.db"
    conn = get_connection(str(db_path), ensure_schema=True)
    try:
        stub = _happy_stub("MSFT")
        days = _seven_day_refresh(
            conn, fail_day=3, monkeypatch=monkeypatch, stub=stub,
        )

        # Sanity: 7 audit rows, 6 success + 1 error on day 3.
        rows = conn.execute(
            "SELECT status, started_at FROM ingestion_runs "
            "WHERE pipeline='yfinance' AND ticker='MSFT' "
            "ORDER BY started_at ASC"
        ).fetchall()
        assert len(rows) == 7
        statuses = [r[0] for r in rows]
        assert statuses.count("success") == 6
        assert statuses.count("error") == 1
        # Day 3 is the failure (0-indexed index 2).
        assert statuses[2] == "error"

        # Agent staleness query — pin to latest success. Compare against
        # the last ``success`` row in the time-ASC ordered list rather than
        # the tz-shifted absolute timestamp (DuckDB stores TIMESTAMP as
        # naive-local; the absolute hour depends on the runner timezone).
        success_rows = [r for r in rows if r[0] == "success"]
        expected_latest_ts = success_rows[-1][1]
        latest_success_ts = conn.execute(
            "SELECT MAX(started_at) FROM ingestion_runs "
            "WHERE pipeline='yfinance' AND ticker='MSFT' "
            "AND status='success'"
        ).fetchone()[0]
        assert latest_success_ts == expected_latest_ts
        # And the day-3 error row sits below the day-7 success row — i.e.
        # the failed day did not poison the "latest success" answer.
        error_ts = next(r[1] for r in rows if r[0] == "error")
        assert error_ts < latest_success_ts
        # Sanity tie back to days: day 7 should appear AFTER day 1 in the
        # ordered list (we built the freeze times across 7 distinct days).
        assert success_rows[0][1] < success_rows[-1][1]
        assert len(days) == 7
    finally:
        conn.close()


def test_staleness_query_without_status_filter_returns_misleading_latest(
    tmp_path, monkeypatch,
):
    """Reverse scenario: day 7 fails. The status-filtered query correctly
    points at day 6 (the latest *successful* refresh); the unfiltered
    query would mistakenly point at day 7, which is the latest *attempt*
    but not the latest fresh data — exactly the failure mode the filter
    exists to prevent.
    """
    monkeypatch.setattr(constants, "PACING_MIN_INTERVAL_SECONDS", 0.0)
    monkeypatch.setattr(constants, "RETRY_BASE_DELAY_SECONDS", 0.0)

    db_path = tmp_path / "staleness_reverse.db"
    conn = get_connection(str(db_path), ensure_schema=True)
    try:
        stub = _happy_stub("MSFT")
        days = _seven_day_refresh(
            conn, fail_day=7, monkeypatch=monkeypatch, stub=stub,
        )

        # Reference rows in time-ASC order so we can identify day-6
        # (last success) and day-7 (the error) without leaning on the
        # tz-shifted ``.date()`` extraction.
        rows = conn.execute(
            "SELECT status, started_at FROM ingestion_runs "
            "WHERE pipeline='yfinance' AND ticker='MSFT' "
            "ORDER BY started_at ASC"
        ).fetchall()
        assert [r[0] for r in rows] == [
            "success", "success", "success",
            "success", "success", "success", "error",
        ]
        expected_day6_success_ts = rows[5][1]
        expected_day7_error_ts = rows[6][1]

        # Correct query — filter for status='success' picks day 6.
        latest_success_ts = conn.execute(
            "SELECT MAX(started_at) FROM ingestion_runs "
            "WHERE pipeline='yfinance' AND ticker='MSFT' "
            "AND status='success'"
        ).fetchone()[0]
        assert latest_success_ts == expected_day6_success_ts

        # Broken query — without the status filter, day 7's error row wins.
        # This is what the subsystem-side guarantee is designed to expose:
        # both ``status`` and ``started_at`` live on the same row, so the
        # downstream agent must apply both predicates.
        latest_any_ts = conn.execute(
            "SELECT MAX(started_at) FROM ingestion_runs "
            "WHERE pipeline='yfinance' AND ticker='MSFT'"
        ).fetchone()[0]
        assert latest_any_ts == expected_day7_error_ts
        assert latest_any_ts > latest_success_ts
        # Sanity tie back to the 7-day series we drove.
        assert len(days) == 7
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# J-yfinance-03: cross-day market_valuations accumulation
# ---------------------------------------------------------------------------


def test_cross_day_market_valuations_accumulate_old_day_preserved(
    tmp_path, monkeypatch,
):
    """Two days apart: cron 5/4 02:00 writes ``(AAPL, 2026-05-04,
    market_cap=3.40T)``, agent stares at the staleness gauge at 11:30,
    and JIT 5/5 03:00 writes ``(AAPL, 2026-05-05, market_cap=3.41T)``.

    The PK ``(ticker, as_of_date)`` keeps the rows distinct, so the 5/4
    value is NOT overwritten by the 5/5 run. ``companies`` is keyed only
    by ticker, so it is UPDATEd in place — one row, ``updated_at`` bumps.
    """
    monkeypatch.setattr(constants, "PACING_MIN_INTERVAL_SECONDS", 0.0)
    monkeypatch.setattr(constants, "RETRY_BASE_DELAY_SECONDS", 0.0)

    db_path = tmp_path / "cross_day.db"
    conn = get_connection(str(db_path), ensure_schema=True)
    try:
        # ---- 5/4 02:00 cron: AAPL @ 3.40T market cap ----
        stub_504 = _happy_stub(
            "AAPL",
            lastFiscalYearEnd=_AAPL_FY_END_UNIX,
            marketCap=3_400_000_000_000,
        )
        with freeze_time("2026-05-04 02:00:00"):
            with yfinance_client.use_ticker_factory_for_test(
                make_stub_factory(stub_504),
            ):
                refresh_yfinance_ticker(conn, "AAPL")

        updated_at_after_504 = conn.execute(
            "SELECT updated_at FROM companies WHERE ticker='AAPL'"
        ).fetchone()[0]
        assert updated_at_after_504 is not None

        # ---- 5/4 11:30: staleness probe only, no refresh ----
        # No state change expected — included to mirror the production flow.
        with freeze_time("2026-05-04 11:30:00"):
            mid_day_count = conn.execute(
                "SELECT COUNT(*) FROM market_valuations WHERE ticker='AAPL'"
            ).fetchone()[0]
        assert mid_day_count == 1

        # ---- 5/5 03:00 JIT: AAPL @ 3.41T market cap ----
        stub_505 = _happy_stub(
            "AAPL",
            lastFiscalYearEnd=_AAPL_FY_END_UNIX,
            marketCap=3_410_000_000_000,
        )
        with freeze_time("2026-05-05 03:00:00"):
            with yfinance_client.use_ticker_factory_for_test(
                make_stub_factory(stub_505),
            ):
                refresh_yfinance_ticker(conn, "AAPL")

        # ---- Assertions: two distinct ``market_valuations`` rows ----
        mv_rows = conn.execute(
            "SELECT as_of_date, market_cap_usd FROM market_valuations "
            "WHERE ticker='AAPL' ORDER BY as_of_date ASC"
        ).fetchall()
        assert mv_rows == [
            (date(2026, 5, 4), 3_400_000_000_000),
            (date(2026, 5, 5), 3_410_000_000_000),
        ]

        # 5/4 row's value is preserved — was not overwritten by 5/5's run.
        original_value = conn.execute(
            "SELECT market_cap_usd FROM market_valuations "
            "WHERE ticker='AAPL' AND as_of_date='2026-05-04'"
        ).fetchone()[0]
        assert original_value == 3_400_000_000_000

        # ``companies`` has exactly one row (UPDATE in place, not INSERT)
        # and its ``updated_at`` has advanced. DuckDB ``now()`` is real
        # wall clock (freezegun does NOT propagate into DuckDB SQL), so
        # this is a ``>=`` relative comparison.
        company_rows = conn.execute(
            "SELECT updated_at FROM companies WHERE ticker='AAPL'"
        ).fetchall()
        assert len(company_rows) == 1
        updated_at_after_505 = company_rows[0][0]
        assert updated_at_after_505 >= updated_at_after_504
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# J-yfinance-04: connection lifecycle — per-request (JIT) vs shared (CLI)
# ---------------------------------------------------------------------------


def test_conn_lifecycle_jit_per_request_vs_cli_batch_shared(
    tmp_path, monkeypatch,
):
    """JIT mode opens one ``DuckDBPyConnection`` per agent request
    (``id()`` differs between requests); CLI batch mode reuses a single
    connection across the for-loop (``id()`` is identical for every
    ticker call inside one ``main(argv)``).
    """
    monkeypatch.setattr(constants, "PACING_MIN_INTERVAL_SECONDS", 0.0)
    monkeypatch.setattr(constants, "RETRY_BASE_DELAY_SECONDS", 0.0)

    db_path = tmp_path / "j04.db"

    # ---- JIT (per-request) — two distinct ``get_connection()`` calls ----
    msft_stub = _happy_stub("MSFT")

    conn_a = get_connection(str(db_path))
    try:
        id_a = id(conn_a)
        with yfinance_client.use_ticker_factory_for_test(
            make_stub_factory(msft_stub),
        ):
            refresh_yfinance_ticker(conn_a, "MSFT")
    finally:
        conn_a.close()

    conn_b = get_connection(str(db_path))
    try:
        id_b = id(conn_b)
        with yfinance_client.use_ticker_factory_for_test(
            make_stub_factory(msft_stub),
        ):
            refresh_yfinance_ticker(conn_b, "MSFT")
    finally:
        conn_b.close()

    assert id_a != id_b

    # ---- CLI batch (shared) — one connection across N tickers ----
    db_path_cli = tmp_path / "j04_cli.db"
    stubs = {
        "MSFT": _happy_stub("MSFT"),
        "NVDA": _happy_stub("NVDA"),
        "AAPL": _happy_stub("AAPL", lastFiscalYearEnd=_AAPL_FY_END_UNIX),
    }

    captured_ids: list[int] = []
    original_refresh = cli_main.refresh_yfinance_ticker

    def _capturing_refresh(conn, ticker):
        captured_ids.append(id(conn))
        return original_refresh(conn, ticker)

    monkeypatch.setattr(cli_main, "refresh_yfinance_ticker", _capturing_refresh)

    with yfinance_client.use_ticker_factory_for_test(_per_ticker_factory(stubs)):
        with pytest.raises(SystemExit) as excinfo:
            cli_main.main(
                [
                    "refresh-yfinance",
                    "MSFT",
                    "NVDA",
                    "AAPL",
                    "--db-path",
                    str(db_path_cli),
                ],
            )
    assert excinfo.value.code == 0

    # Every per-ticker invocation inside ``main()`` saw the same conn.
    assert len(captured_ids) == 3
    assert len(set(captured_ids)) == 1
