"""DST same-calendar-day pacing scenario for the yfinance orchestrator.

Covers BDD scenario S-yfinance-09: two ``refresh_yfinance_ticker`` calls on
the SAME LA calendar day (2026-03-08, the DST spring-forward day) but spanning
the 02:00→03:00 jump produce:

* 2 ``ingestion_runs`` rows whose ``started_at`` converts to LA-local date
  2026-03-08 (audit retains per-run history)
* 1 ``market_valuations`` row (PK ``(ticker, as_of_date)`` collapses because
  both runs see ``date.today() == 2026-03-08``)
* Each run's ``metadata.pacing.calls == 7`` (baseline: 1 info + 3 quarterly +
  3 annual, no retry)

The test exposes the asymmetry S-yfinance-09 locks down: audit count is
keyed by LA-local DATE of ``started_at`` (2 rows), but ``market_valuations``
collapses on the same ``as_of_date`` (1 row). The two cardinalities are
**both correct** for their respective grains.

Implementation notes
--------------------
* ``os.environ["TZ"]`` + ``time.tzset()`` sets process tz to ``America/
  Los_Angeles``. ``time.tzset`` is POSIX-only — Windows runs skip the test.
* The ``tmp_duckdb`` fixture opens the connection BEFORE this test body runs,
  so its DuckDB session TimeZone reflects whatever the dev/CI host tz was at
  connection time — not LA. We explicitly ``SET TimeZone='America/
  Los_Angeles'`` on the connection so naive ``TIMESTAMP`` inserts are
  interpreted in LA and the ``AT TIME ZONE 'America/Los_Angeles'`` audit
  query returns LA-local dates regardless of host.
* ``freezegun.freeze_time`` fixes the wall clock; ``datetime.now(UTC)``
  returns the frozen UTC, which is what ``track_ingestion_run`` writes into
  ``ingestion_runs.started_at``.
* ``date.today()`` under freezegun returns the frozen UTC date, NOT the LA
  local date — verified on macOS that even with ``TZ=America/Los_Angeles``
  and ``time.tzset()``, freezegun's ``date.today`` mock honours UTC. Run B's
  UTC date (2026-03-09) differs from its LA-local date (2026-03-08), so we
  monkeypatch ``refresh_orchestrator.date`` to a fixed stub returning
  ``date(2026, 3, 8)`` for both runs. This matches the production behaviour
  on a real LA host where ``date.today()`` returns LA-local 2026-03-08 at
  both LA 01:30 and LA 23:30.
"""

import json
import os
import sys
import time
from datetime import date

import pandas as pd
import pytest
from freezegun import freeze_time

from backend.ingestion.quant_data_pipeline.yfinance import (
    constants,
    refresh_orchestrator,
    yfinance_client,
)
from backend.ingestion.quant_data_pipeline.yfinance.refresh_orchestrator import (
    refresh_yfinance_ticker,
)
from backend.tests.ingestion.quant_data_pipeline.yfinance.stubs import (
    StubTicker,
    make_stub_factory,
)

# 1695945600 → 2023-09-29 UTC, matches AAPL's FY-end month 9 so the orchestrator's
# normalize_fiscal_period landing for period_end 2024-09-30 is self-consistent.
# Exact value is not load-bearing for this test (we assert audit/MV cardinality
# only), but a valid fy_end keeps both runs succeeding through every stage.
_AAPL_FY_END_UNIX = 1695945600


def _info() -> dict:
    return {
        "longName": "Apple Inc.",
        "sector": "Technology",
        "industry": "Consumer Electronics",
        "lastFiscalYearEnd": _AAPL_FY_END_UNIX,
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


def _statement_dfs() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
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


def _stub() -> StubTicker:
    income, balance, cashflow = _statement_dfs()
    return StubTicker(
        info=_info(),
        quarterly_income_stmt=income,
        quarterly_balance_sheet=balance,
        quarterly_cashflow=cashflow,
        income_stmt=income,
        balance_sheet=balance,
        cashflow=cashflow,
    )


class _FixedLADate:
    """``date``-shaped stub whose ``today()`` returns LA-local 2026-03-08.

    Mimics the production behaviour on a host whose system timezone is set to
    ``America/Los_Angeles``: at both LA 01:30 (UTC 09:30 same day) and LA
    23:30 (UTC 06:30 next day), ``date.today()`` returns 2026-03-08.
    """

    @staticmethod
    def today() -> date:
        return date(2026, 3, 8)


def test_dst_same_calendar_day_two_refreshes_collapse_mv_keep_separate_audit(
    tmp_duckdb, monkeypatch,
):
    if not hasattr(time, "tzset"):
        pytest.skip("DST test requires POSIX time.tzset()")
    if sys.platform == "win32":  # defensive: time.tzset missing on Windows
        pytest.skip("DST test requires POSIX time.tzset()")

    # Scope TZ env to this test: restore the prior value (or unset) on exit.
    prior_tz = os.environ.get("TZ")
    os.environ["TZ"] = "America/Los_Angeles"
    time.tzset()
    try:
        # The tmp_duckdb fixture opened the connection before TZ was changed,
        # so explicitly align its session TimeZone with America/Los_Angeles —
        # otherwise the AT TIME ZONE audit query below would compose two
        # mismatched tz semantics (host default at storage time, LA at read
        # time) and yield wrong dates.
        tmp_duckdb.execute("SET TimeZone='America/Los_Angeles'")

        # Drop the real 1.0s pacing gate — _pace() reads time.monotonic() which
        # freezegun does NOT mock by default, so a live PACING_MIN_INTERVAL_
        # SECONDS=1.0 would cost ~14s of real sleep across the 14 paced calls.
        monkeypatch.setattr(constants, "PACING_MIN_INTERVAL_SECONDS", 0.0)

        # Force the orchestrator's date.today() to LA-local 2026-03-08 for both
        # runs. freezegun's date.today() mock honours frozen UTC, so without
        # this patch Run B would write as_of_date=2026-03-09 and the MV PK
        # would not collapse.
        monkeypatch.setattr(refresh_orchestrator, "date", _FixedLADate)

        # ---- Run A: LA local 01:30 on 2026-03-08 = UTC 09:30 (PST, pre-DST) ----
        with freeze_time("2026-03-08 09:30:00"):
            with yfinance_client.use_ticker_factory_for_test(
                make_stub_factory(_stub())
            ):
                refresh_yfinance_ticker(tmp_duckdb, "AAPL")

        # ---- Run B: LA local 23:30 on 2026-03-08 = UTC 06:30 next day (PDT, post-DST) ----
        with freeze_time("2026-03-09 06:30:00"):
            with yfinance_client.use_ticker_factory_for_test(
                make_stub_factory(_stub())
            ):
                refresh_yfinance_ticker(tmp_duckdb, "AAPL")

        # Audit grain: 2 rows, both falling on LA-local DATE 2026-03-08
        # (UTC 09:30 of 03-08 → LA 01:30 of 03-08;
        #  UTC 06:30 of 03-09 → LA 23:30 of 03-08 PDT after the DST jump).
        audit_count = tmp_duckdb.execute(
            "SELECT COUNT(*) FROM ingestion_runs "
            "WHERE pipeline='yfinance' AND ticker='AAPL' "
            "  AND DATE(started_at AT TIME ZONE 'America/Los_Angeles') = '2026-03-08'"
        ).fetchone()
        assert audit_count is not None
        assert audit_count[0] == 2

        # MV grain: PK (ticker, as_of_date) collapses — both runs write as_of_date=2026-03-08.
        mv_count = tmp_duckdb.execute(
            "SELECT COUNT(*) FROM market_valuations "
            "WHERE ticker='AAPL' AND as_of_date='2026-03-08'"
        ).fetchone()
        assert mv_count is not None
        assert mv_count[0] == 1

        # Each audit row records the per-run paced call delta (calls_after -
        # calls_before captured by the orchestrator's finally block). Baseline
        # is 7: 1 fetch_info + 3 quarterly + 3 annual.
        rows = tmp_duckdb.execute(
            "SELECT metadata FROM ingestion_runs "
            "WHERE pipeline='yfinance' AND ticker='AAPL' "
            "ORDER BY started_at ASC"
        ).fetchall()
        assert len(rows) == 2
        for raw_metadata, in rows:
            metadata = (
                json.loads(raw_metadata)
                if isinstance(raw_metadata, str)
                else raw_metadata
            )
            assert metadata["pacing"]["calls"] == 7
            assert metadata["retry_count"] == 0

        # Defensive: confirm the two stored TIMESTAMPs land on the right
        # LA-local wall times either side of the DST jump. With the
        # connection's TimeZone set to America/Los_Angeles, DuckDB converts
        # tz-aware UTC inserts to LA-local naive wall time at storage:
        #   Run A: UTC 2026-03-08 09:30 → LA 2026-03-08 01:30 (PST)
        #   Run B: UTC 2026-03-09 06:30 → LA 2026-03-08 23:30 (PDT)
        # If a future DuckDB version changed storage semantics, this guard
        # would flag the regression before the audit-count assertion above.
        stored_ts = tmp_duckdb.execute(
            "SELECT started_at FROM ingestion_runs "
            "WHERE pipeline='yfinance' AND ticker='AAPL' "
            "ORDER BY started_at ASC"
        ).fetchall()
        assert [r[0].date() for r in stored_ts] == [
            date(2026, 3, 8),
            date(2026, 3, 8),
        ]
        assert stored_ts[0][0].hour == 1
        assert stored_ts[1][0].hour == 23

    finally:
        if prior_tz is None:
            os.environ.pop("TZ", None)
        else:
            os.environ["TZ"] = prior_tz
        time.tzset()
