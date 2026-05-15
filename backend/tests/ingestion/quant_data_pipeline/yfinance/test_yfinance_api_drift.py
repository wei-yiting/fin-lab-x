"""Live yfinance HTTP smoke tests for production drift detection.

These are SKIPPED in default CI runs (filtered by ``addopts``). Run manually with:

    uv run pytest -m live_yfinance backend/tests/ingestion/quant_data_pipeline/yfinance/

Hits real yfinance API; rate-limited; flaky if Yahoo throttles. Expected
runtime ~30-60s for 5 tickers.
"""

import time

import pytest

from backend.ingestion.quant_data_pipeline.yfinance import refresh_yfinance_ticker

PRODUCTION_TICKERS = ["MSFT", "NVDA", "KO", "AAPL", "JPM"]


@pytest.mark.live_yfinance
@pytest.mark.parametrize("ticker", PRODUCTION_TICKERS)
def test_held_pct_drift(tmp_duckdb, ticker):
    """Sanity-check that held_pct_institutions for each ticker falls in [0, 100].

    If the assertion fails for any ticker, yfinance has changed its unit
    convention (e.g. now returns a percent already, making our ×100
    converter wrong). Bubble up as a drift incident.
    """
    refresh_yfinance_ticker(tmp_duckdb, ticker)
    row = tmp_duckdb.execute(
        "SELECT held_pct_institutions FROM market_valuations WHERE ticker = ? "
        "ORDER BY as_of_date DESC LIMIT 1",
        [ticker],
    ).fetchone()
    assert row is not None, f"market_valuations row for {ticker} missing"
    held_pct = row[0]
    # held_pct may be None if yfinance does not report it for this ticker
    if held_pct is not None:
        assert 0 <= held_pct <= 100, (
            f"held_pct_institutions for {ticker} = {held_pct} is outside [0, 100] "
            "— yfinance unit drift detected"
        )
    # 1-second between tickers when parametrized to avoid rate-limit hits
    time.sleep(1)


@pytest.mark.live_yfinance
def test_nvda_fy_end_day(tmp_duckdb):
    """NVDA's lastFiscalYearEnd Unix timestamp is sensitive: real yfinance
    must report it as a date with day=25 (NVDA's non-month-end FY closes
    on the last Friday of January). If this assertion fails, NVDA changed
    their fiscal calendar OR yfinance changed how lastFiscalYearEnd is
    populated.
    """
    refresh_yfinance_ticker(tmp_duckdb, "NVDA")
    row = tmp_duckdb.execute(
        "SELECT fy_end_month, fy_end_day FROM companies WHERE ticker = 'NVDA'"
    ).fetchone()
    assert row is not None
    fy_end_month, fy_end_day = row
    assert fy_end_month == 1, f"NVDA fy_end_month should be 1, got {fy_end_month}"
    assert fy_end_day == 25, f"NVDA fy_end_day should be 25, got {fy_end_day}"
