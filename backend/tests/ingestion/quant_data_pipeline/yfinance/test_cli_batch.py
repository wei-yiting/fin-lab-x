"""CLI batch isolation + exit code tests for ``refresh-yfinance``.

Two layers of coverage:

* ``TestBatchIsolation`` — the for-loop logic *only*. Runs
  ``refresh_yfinance_ticker`` in a local loop with the same
  ``except QuantPipelineError: continue`` contract used by
  ``__main__._refresh_yfinance`` to prove per-ticker failures do not
  poison the shared DuckDB connection for subsequent tickers.

* ``TestExitCode`` — full ``__main__.main(argv)`` invocations using
  ``pytest.raises(SystemExit)`` (the so-called *Option C* harness from
  the design plan). Each test points ``--db-path`` at a ``tmp_path``-
  scoped DuckDB file and re-opens it with ``ensure_schema=False`` after
  ``main`` returns to inspect the persisted audit rows.

Per-ticker stub injection uses ``yfinance_client.use_ticker_factory_for_test``,
a ``ContextVar``-based seam. The ContextVar is process-local and is read
inside ``main`` (no fork), so a single ``with`` block around the
``main(argv)`` call cleanly scopes the override.
"""

import json

import pytest

from backend.ingestion.quant_data_pipeline import __main__ as cli_main
from backend.ingestion.quant_data_pipeline.duck_db.connection import get_connection
from backend.ingestion.quant_data_pipeline.quant_pipeline_errors import (
    QuantPipelineError,
)
from backend.ingestion.quant_data_pipeline.yfinance import (
    constants,
    refresh_yfinance_ticker,
    yfinance_client,
)
from backend.ingestion.quant_data_pipeline.yfinance.yfinance_pipeline_errors import (
    YFinanceRateLimitError,
    YFinanceTickerNotFoundError,
)
from backend.tests.ingestion.quant_data_pipeline.yfinance.stubs import StubTicker
from backend.tests.ingestion.quant_data_pipeline.yfinance.test_refresh_orchestrator_core import (
    _happy_stub,
)


def _per_ticker_factory(stubs: dict[str, StubTicker]):
    """Return a ``TickerFactory`` that dispatches to a per-ticker stub.

    Raises ``KeyError`` if the ticker is not in the map — that's intentional;
    every test below registers exactly the tickers it expects to drive.
    """

    def _factory(ticker: str) -> StubTicker:
        return stubs[ticker]

    return _factory


def _jpm_quarterly_empty_stub() -> StubTicker:
    """JPM stub whose quarterly Total Revenue row is all-NaN.

    Forces ``build_quarterly_rows`` to raise ``YFinanceEmptyResponseError``
    at the ``error_stage='quarterly'`` boundary while ``info`` (Stage 1)
    still upserts ``companies`` + ``market_valuations``.
    """
    stub = _happy_stub("JPM")
    # Wipe every value in the quarterly_income_stmt — Total Revenue all-NaN
    # is sufficient (the DTO builder skips rows without Total Revenue), but
    # zeroing the whole frame keeps the intent obvious.
    for col in stub.quarterly_income_stmt.columns:
        stub.quarterly_income_stmt[col] = float("nan")
    return stub


class TestBatchIsolation:
    """For-loop tests that bypass ``main()`` and exercise the isolation
    contract directly: ``except QuantPipelineError: continue`` must leave
    the shared DuckDB connection writable for the next ticker."""

    def test_three_ticker_loop_jpm_fails_others_succeed(
        self, tmp_duckdb, monkeypatch,
    ):
        monkeypatch.setattr(constants, "PACING_MIN_INTERVAL_SECONDS", 0.0)
        monkeypatch.setattr(constants, "RETRY_BASE_DELAY_SECONDS", 0.0)

        stubs = {
            "MSFT": _happy_stub("MSFT"),
            "JPM": _jpm_quarterly_empty_stub(),
            "AAPL": _happy_stub("AAPL"),
        }
        tickers = ["MSFT", "JPM", "AAPL"]
        with yfinance_client.use_ticker_factory_for_test(_per_ticker_factory(stubs)):
            for ticker in tickers:
                try:
                    refresh_yfinance_ticker(tmp_duckdb, ticker)
                except QuantPipelineError:
                    continue

        audit_rows = tmp_duckdb.execute(
            "SELECT ticker, status, error_class, metadata "
            "FROM ingestion_runs ORDER BY ticker"
        ).fetchall()
        # Audit rows ordered alphabetically: AAPL, JPM, MSFT.
        by_ticker = {row[0]: row for row in audit_rows}
        assert set(by_ticker) == {"MSFT", "JPM", "AAPL"}

        assert by_ticker["MSFT"][1] == "success"
        assert by_ticker["AAPL"][1] == "success"

        jpm_ticker, jpm_status, jpm_err_class, jpm_meta_json = by_ticker["JPM"]
        assert jpm_status == "error"
        assert jpm_err_class == "YFinanceEmptyResponseError"

        parsed = json.loads(jpm_meta_json)
        assert parsed["error_stage"] == "quarterly"
        assert set(parsed["rows_per_table"].keys()) == {
            "companies",
            "market_valuations",
        }

        # Verify MSFT and AAPL have rows in all 4 yfinance-owned tables.
        for ticker in ("MSFT", "AAPL"):
            for table in (
                "companies",
                "market_valuations",
                "quarterly_financials",
                "annual_financials",
            ):
                count = tmp_duckdb.execute(
                    f"SELECT count(*) FROM {table} WHERE ticker = ?", [ticker],
                ).fetchone()[0]
                assert count > 0, f"{ticker} missing rows in {table}"

    def test_conn_remains_writable_after_ticker_failure(
        self, tmp_duckdb, monkeypatch,
    ):
        monkeypatch.setattr(constants, "PACING_MIN_INTERVAL_SECONDS", 0.0)
        monkeypatch.setattr(constants, "RETRY_BASE_DELAY_SECONDS", 0.0)

        stubs = {
            "JPM": _jpm_quarterly_empty_stub(),
            "AAPL": _happy_stub("AAPL"),
        }
        with yfinance_client.use_ticker_factory_for_test(_per_ticker_factory(stubs)):
            with pytest.raises(QuantPipelineError):
                refresh_yfinance_ticker(tmp_duckdb, "JPM")
            # Immediately reuse the same conn for AAPL — no dangling
            # transaction state should block the upserts.
            refresh_yfinance_ticker(tmp_duckdb, "AAPL")

        aapl_row = tmp_duckdb.execute(
            "SELECT status FROM ingestion_runs WHERE ticker = 'AAPL'"
        ).fetchone()
        assert aapl_row == ("success",)
        # AAPL writes landed in every owned table.
        for table in (
            "companies",
            "market_valuations",
            "quarterly_financials",
            "annual_financials",
        ):
            count = tmp_duckdb.execute(
                f"SELECT count(*) FROM {table} WHERE ticker = 'AAPL'",
            ).fetchone()[0]
            assert count > 0, f"AAPL missing rows in {table}"


class TestExitCode:
    """In-process invocations of ``__main__.main(argv)`` using
    ``pytest.raises(SystemExit)`` to capture exit codes (Option C in the
    design plan)."""

    def test_cli_all_fail_exits_non_zero(self, tmp_path, monkeypatch):
        monkeypatch.setattr(constants, "PACING_MIN_INTERVAL_SECONDS", 0.0)
        monkeypatch.setattr(constants, "RETRY_BASE_DELAY_SECONDS", 0.0)

        def always_429(_ticker: str) -> dict:
            raise YFinanceRateLimitError("synthetic 429")

        monkeypatch.setattr(yfinance_client, "fetch_info", always_429)

        db_path = tmp_path / "x.db"
        with pytest.raises(SystemExit) as excinfo:
            cli_main.main(
                [
                    "refresh-yfinance",
                    "MSFT",
                    "JPM",
                    "AAPL",
                    "--db-path",
                    str(db_path),
                ],
            )
        assert excinfo.value.code != 0

        conn = get_connection(str(db_path), ensure_schema=False)
        try:
            rows = conn.execute(
                "SELECT ticker, status FROM ingestion_runs ORDER BY ticker"
            ).fetchall()
        finally:
            conn.close()
        assert len(rows) == 3
        assert all(status == "error" for _, status in rows)

    def test_cli_partial_fail_exits_zero(self, tmp_path, monkeypatch):
        monkeypatch.setattr(constants, "PACING_MIN_INTERVAL_SECONDS", 0.0)
        monkeypatch.setattr(constants, "RETRY_BASE_DELAY_SECONDS", 0.0)

        stubs = {
            "MSFT": _happy_stub("MSFT"),
            "NVDA": _happy_stub("NVDA"),
        }
        original_fetch_info = yfinance_client.fetch_info

        def selective_fetch_info(ticker: str) -> dict:
            ticker = ticker.strip().upper()
            if ticker == "FAKE1":
                raise YFinanceTickerNotFoundError("ticker not found")
            return original_fetch_info(ticker)

        monkeypatch.setattr(yfinance_client, "fetch_info", selective_fetch_info)

        db_path = tmp_path / "x.db"
        with yfinance_client.use_ticker_factory_for_test(_per_ticker_factory(stubs)):
            with pytest.raises(SystemExit) as excinfo:
                cli_main.main(
                    [
                        "refresh-yfinance",
                        "MSFT",
                        "FAKE1",
                        "NVDA",
                        "--db-path",
                        str(db_path),
                    ],
                )
        assert excinfo.value.code == 0

        conn = get_connection(str(db_path), ensure_schema=False)
        try:
            rows = conn.execute(
                "SELECT ticker, status FROM ingestion_runs ORDER BY ticker"
            ).fetchall()
        finally:
            conn.close()
        statuses = {ticker: status for ticker, status in rows}
        assert statuses == {"MSFT": "success", "FAKE1": "error", "NVDA": "success"}

    def test_cli_all_success_exits_zero(self, tmp_path, monkeypatch):
        monkeypatch.setattr(constants, "PACING_MIN_INTERVAL_SECONDS", 0.0)

        stubs = {
            "MSFT": _happy_stub("MSFT"),
            "NVDA": _happy_stub("NVDA"),
            "AAPL": _happy_stub("AAPL"),
        }
        db_path = tmp_path / "x.db"
        with yfinance_client.use_ticker_factory_for_test(_per_ticker_factory(stubs)):
            with pytest.raises(SystemExit) as excinfo:
                cli_main.main(
                    [
                        "refresh-yfinance",
                        "MSFT",
                        "NVDA",
                        "AAPL",
                        "--db-path",
                        str(db_path),
                    ],
                )
        assert excinfo.value.code == 0

        conn = get_connection(str(db_path), ensure_schema=False)
        try:
            rows = conn.execute(
                "SELECT status FROM ingestion_runs"
            ).fetchall()
        finally:
            conn.close()
        assert len(rows) == 3
        assert all(status == "success" for (status,) in rows)

    def test_cli_uses_universe_when_no_explicit_tickers(
        self, tmp_path, monkeypatch,
    ):
        monkeypatch.setattr(constants, "PACING_MIN_INTERVAL_SECONDS", 0.0)

        universe_path = tmp_path / "universe.yaml"
        universe_path.write_text("tickers:\n  - MSFT\n")

        stubs = {"MSFT": _happy_stub("MSFT")}
        db_path = tmp_path / "x.db"
        with yfinance_client.use_ticker_factory_for_test(_per_ticker_factory(stubs)):
            with pytest.raises(SystemExit) as excinfo:
                cli_main.main(
                    [
                        "refresh-yfinance",
                        "--db-path",
                        str(db_path),
                        "--universe-path",
                        str(universe_path),
                    ],
                )
        assert excinfo.value.code == 0

        conn = get_connection(str(db_path), ensure_schema=False)
        try:
            rows = conn.execute(
                "SELECT ticker, status FROM ingestion_runs"
            ).fetchall()
        finally:
            conn.close()
        assert rows == [("MSFT", "success")]

    def test_cli_uses_explicit_tickers_when_provided(
        self, tmp_path, monkeypatch,
    ):
        monkeypatch.setattr(constants, "PACING_MIN_INTERVAL_SECONDS", 0.0)

        stubs = {"MSFT": _happy_stub("MSFT")}
        db_path = tmp_path / "x.db"
        with yfinance_client.use_ticker_factory_for_test(_per_ticker_factory(stubs)):
            with pytest.raises(SystemExit) as excinfo:
                cli_main.main(
                    ["refresh-yfinance", "MSFT", "--db-path", str(db_path)],
                )
        assert excinfo.value.code == 0

        conn = get_connection(str(db_path), ensure_schema=False)
        try:
            rows = conn.execute(
                "SELECT ticker, status FROM ingestion_runs"
            ).fetchall()
        finally:
            conn.close()
        assert rows == [("MSFT", "success")]
