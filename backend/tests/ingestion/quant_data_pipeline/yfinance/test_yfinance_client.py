"""Unit tests for the yfinance I/O client.

All tests use the ``use_ticker_factory_for_test`` ContextVar seam — no
monkeypatching of ``yfinance.Ticker`` globally. Pacing counters are reset by
the autouse fixture in ``conftest.py``.
"""

import pandas as pd
import pytest
from yfinance import exceptions as yf_exceptions

from backend.ingestion.quant_data_pipeline.quant_pipeline_errors import (
    TransientError,
)
from backend.ingestion.quant_data_pipeline.yfinance import (
    constants,
    yfinance_client,
)
from backend.ingestion.quant_data_pipeline.yfinance.yfinance_client import (
    _classify,
    _make_ticker,
    _ticker_factory_override,
    fetch_annual_statements,
    fetch_info,
    fetch_quarterly_statements,
    get_pacing_stats,
    use_ticker_factory_for_test,
)
from backend.ingestion.quant_data_pipeline.yfinance.yfinance_pipeline_errors import (
    YFinanceEmptyResponseError,
    YFinanceRateLimitError,
    YFinanceTickerNotFoundError,
)
from backend.tests.ingestion.quant_data_pipeline.yfinance.stubs import (
    StubTicker,
    make_stub_factory,
)


# ---------------------------------------------------------------------------
# ContextVar test seam
# ---------------------------------------------------------------------------


def test_use_ticker_factory_for_test_overrides_within_scope():
    stub = StubTicker(info={"longName": "Acme"})
    factory = make_stub_factory(stub)

    assert _ticker_factory_override.get() is None
    with use_ticker_factory_for_test(factory):
        assert _make_ticker("ANY") is stub
    assert _ticker_factory_override.get() is None


def test_use_ticker_factory_for_test_restores_on_exception():
    stub = StubTicker()
    factory = make_stub_factory(stub)

    with pytest.raises(RuntimeError, match="boom"):
        with use_ticker_factory_for_test(factory):
            raise RuntimeError("boom")

    assert _ticker_factory_override.get() is None


# ---------------------------------------------------------------------------
# Pacing
# ---------------------------------------------------------------------------


def test_pace_increments_call_count(monkeypatch):
    # Freeze time so no real sleep happens; just verify the counter ticks.
    monkeypatch.setattr(yfinance_client.time, "monotonic", lambda: 0.0)
    monkeypatch.setattr(yfinance_client.time, "sleep", lambda _s: None)

    yfinance_client._pace()
    yfinance_client._pace()
    yfinance_client._pace()

    calls, _sleep = get_pacing_stats()
    assert calls == 3


def test_pace_reads_constant_at_call_time(monkeypatch):
    # If the constant is read at call time, monkeypatching the module attribute
    # immediately before the call must take effect.
    sleep_calls: list[float] = []
    monkeypatch.setattr(yfinance_client.time, "sleep", sleep_calls.append)
    monkeypatch.setattr(constants, "PACING_MIN_INTERVAL_SECONDS", 0.0)

    yfinance_client._pace()
    yfinance_client._pace()

    assert sleep_calls == []


def test_pace_accumulates_sleep_seconds(monkeypatch):
    # Each _pace() reads monotonic twice: once at entry (delta calc), once at
    # exit (last_call_ts update). Sequence:
    #   call 1: now=0.0 (last_ts=None, no sleep), then update last_ts=0.0
    #   call 2: now=0.0 (delta=0, sleep 1.0),     then update last_ts=1.0
    tick = iter([0.0, 0.0, 0.0, 1.0])
    monkeypatch.setattr(yfinance_client.time, "monotonic", lambda: next(tick))
    monkeypatch.setattr(yfinance_client.time, "sleep", lambda _s: None)
    monkeypatch.setattr(constants, "PACING_MIN_INTERVAL_SECONDS", 1.0)

    yfinance_client._pace()
    yfinance_client._pace()

    _calls, total_sleep = get_pacing_stats()
    assert total_sleep == pytest.approx(1.0)


def test_get_pacing_stats_returns_snapshot(monkeypatch):
    # _pace() always increments the call counter, regardless of sleep.
    monkeypatch.setattr(yfinance_client.time, "monotonic", lambda: 0.0)
    monkeypatch.setattr(yfinance_client.time, "sleep", lambda _s: None)
    monkeypatch.setattr(constants, "PACING_MIN_INTERVAL_SECONDS", 0.0)

    yfinance_client._pace()
    yfinance_client._pace()

    calls, total_sleep = get_pacing_stats()
    assert calls == 2
    assert total_sleep >= 0.0


# ---------------------------------------------------------------------------
# _classify
# ---------------------------------------------------------------------------
# Some yfinance error classes have non-trivial constructors. To keep the test
# robust across yfinance patch releases, we use FakeXxx subclasses with a
# zero-arg constructor for the cases that need it.


class _FakeRateLimit(yf_exceptions.YFRateLimitError):
    pass


class _FakeTickerMissing(yf_exceptions.YFTickerMissingError):
    def __init__(self) -> None:
        super().__init__("FAKE", "fake reason")


class _FakeTzMissing(yf_exceptions.YFTzMissingError):
    def __init__(self) -> None:
        super().__init__("FAKE")


class _FakePricesMissing(yf_exceptions.YFPricesMissingError):
    def __init__(self) -> None:
        super().__init__("FAKE", "1d")


def test_classify_rate_limit():
    with pytest.raises(YFinanceRateLimitError):
        _classify(_FakeRateLimit())


def test_classify_ticker_missing():
    with pytest.raises(YFinanceTickerNotFoundError):
        _classify(_FakeTickerMissing())


def test_classify_tz_missing_maps_to_ticker_not_found():
    with pytest.raises(YFinanceTickerNotFoundError):
        _classify(_FakeTzMissing())


def test_classify_prices_missing_maps_to_empty_response():
    with pytest.raises(YFinanceEmptyResponseError):
        _classify(_FakePricesMissing())


def test_classify_generic_yf_data_exception_maps_to_empty_response():
    with pytest.raises(YFinanceEmptyResponseError):
        _classify(yf_exceptions.YFDataException("oops"))


def test_classify_network_timeout():
    with pytest.raises(TransientError):
        _classify(TimeoutError("boom"))


def test_classify_connection_error():
    with pytest.raises(TransientError):
        _classify(ConnectionError("net down"))


def test_classify_unknown_exception_passes_through():
    sentinel = ValueError("not a yfinance error")
    with pytest.raises(ValueError, match="not a yfinance error"):
        _classify(sentinel)


# ---------------------------------------------------------------------------
# fetch_* functions
# ---------------------------------------------------------------------------


def test_fetch_info_uses_factory():
    stub = StubTicker(info={"longName": "Microsoft", "marketCap": 1_000})
    with use_ticker_factory_for_test(make_stub_factory(stub)):
        result = fetch_info("MSFT")

    assert result == {"longName": "Microsoft", "marketCap": 1_000}
    calls, _ = get_pacing_stats()
    assert calls == 1


def test_fetch_quarterly_statements_returns_three_dataframes():
    inc = pd.DataFrame({"a": [1]})
    bal = pd.DataFrame({"b": [2]})
    cf = pd.DataFrame({"c": [3]})
    stub = StubTicker(
        quarterly_income_stmt=inc,
        quarterly_balance_sheet=bal,
        quarterly_cashflow=cf,
    )

    with use_ticker_factory_for_test(make_stub_factory(stub)):
        got_inc, got_bal, got_cf = fetch_quarterly_statements("MSFT")

    pd.testing.assert_frame_equal(got_inc, inc)
    pd.testing.assert_frame_equal(got_bal, bal)
    pd.testing.assert_frame_equal(got_cf, cf)

    calls, _ = get_pacing_stats()
    assert calls == 3


def test_fetch_annual_statements_returns_three_dataframes():
    inc = pd.DataFrame({"a": [10]})
    bal = pd.DataFrame({"b": [20]})
    cf = pd.DataFrame({"c": [30]})
    stub = StubTicker(income_stmt=inc, balance_sheet=bal, cashflow=cf)

    with use_ticker_factory_for_test(make_stub_factory(stub)):
        got_inc, got_bal, got_cf = fetch_annual_statements("MSFT")

    pd.testing.assert_frame_equal(got_inc, inc)
    pd.testing.assert_frame_equal(got_bal, bal)
    pd.testing.assert_frame_equal(got_cf, cf)

    calls, _ = get_pacing_stats()
    assert calls == 3


def test_fetch_info_classifies_rate_limit_error():
    stub = StubTicker(raise_on_attrs={"info": _FakeRateLimit()})
    with use_ticker_factory_for_test(make_stub_factory(stub)):
        with pytest.raises(YFinanceRateLimitError):
            fetch_info("MSFT")


def test_fetch_quarterly_classifies_ticker_missing():
    stub = StubTicker(
        raise_on_attrs={"quarterly_income_stmt": _FakeTickerMissing()},
    )
    with use_ticker_factory_for_test(make_stub_factory(stub)):
        with pytest.raises(YFinanceTickerNotFoundError):
            fetch_quarterly_statements("NOPE")
