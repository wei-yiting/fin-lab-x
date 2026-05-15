"""yfinance I/O layer for the ingestion subsystem.

Holds the only references to ``yf.Ticker`` and ``yfinance.exceptions`` in
the subsystem. Pacing counters accumulate for the lifetime of the process;
tests use ``reset_pacing_stats()`` to clear them per-test via fixture.

The ``ContextVar`` test seam (``_ticker_factory_override`` +
``use_ticker_factory_for_test``) lets unit tests inject stub Ticker objects
without monkeypatching ``yfinance.Ticker`` globally — this keeps the
subsystem's ``yfinance`` dependency to this one module.
"""

import time
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from typing import NoReturn, Protocol

import pandas as pd
import yfinance as yf
from yfinance import exceptions as yf_exceptions

from backend.ingestion.quant_data_pipeline.quant_pipeline_errors import (
    TransientError,
)

from . import constants  # module import so monkeypatch.setattr(constants, ...) flows through
from .yfinance_pipeline_errors import (
    YFinanceEmptyResponseError,
    YFinanceRateLimitError,
    YFinanceTickerNotFoundError,
)

# Apply yfinance's built-in retry knob once at import time. Foundation retry
# wrapping in refresh_orchestrator (Task 7) layers on top of this.
yf.config.network.retries = constants.YF_NETWORK_RETRIES

# Module-level pacing state. Process-lifetime; test fixture resets per-test.
_last_call_ts: float | None = None
_pace_call_count: int = 0
_pace_total_sleep_seconds: float = 0.0


class TickerLike(Protocol):
    info: dict
    quarterly_income_stmt: pd.DataFrame
    quarterly_balance_sheet: pd.DataFrame
    quarterly_cashflow: pd.DataFrame
    income_stmt: pd.DataFrame
    balance_sheet: pd.DataFrame
    cashflow: pd.DataFrame


TickerFactory = Callable[[str], TickerLike]


_ticker_factory_override: ContextVar[TickerFactory | None] = ContextVar(
    "yfinance_ticker_factory_override", default=None
)


def _make_ticker(ticker: str) -> TickerLike:
    """Return a Ticker-like object for ``ticker``.

    If a test factory override is active, use it; otherwise construct a real
    ``yf.Ticker``. No ``session=`` kwarg — yfinance 1.x uses curl_cffi
    internally and the ``session=`` parameter is incompatible.
    """
    override = _ticker_factory_override.get()
    if override is not None:
        return override(ticker)
    return yf.Ticker(ticker)  # type: ignore[return-value]


@contextmanager
def use_ticker_factory_for_test(factory: TickerFactory) -> Iterator[None]:
    """TEST-ONLY: override the Ticker factory within this scope.

    Automatically restored on exit (including via exception) by the
    ``ContextVar`` token's reset semantics.
    """
    token = _ticker_factory_override.set(factory)
    try:
        yield
    finally:
        _ticker_factory_override.reset(token)


def _pace() -> None:
    """Enforce a minimum interval between outbound calls.

    Reads ``constants.PACING_MIN_INTERVAL_SECONDS`` at CALL time (not at
    import / definition time) so tests can monkeypatch the module attribute.
    """
    global _last_call_ts, _pace_call_count, _pace_total_sleep_seconds

    min_interval = constants.PACING_MIN_INTERVAL_SECONDS
    now = time.monotonic()
    if _last_call_ts is not None:
        delta = now - _last_call_ts
        if delta < min_interval:
            sleep_for = min_interval - delta
            time.sleep(sleep_for)
            _pace_total_sleep_seconds += sleep_for
    _pace_call_count += 1
    _last_call_ts = time.monotonic()


def get_pacing_stats() -> tuple[int, float]:
    """Return a snapshot of ``(call_count, total_sleep_seconds)``.

    Caller computes deltas across snapshots — this function never resets.
    """
    return _pace_call_count, _pace_total_sleep_seconds


def reset_pacing_stats() -> None:
    """TEST-ONLY: clear module-level pacing counters."""
    global _last_call_ts, _pace_call_count, _pace_total_sleep_seconds
    _last_call_ts = None
    _pace_call_count = 0
    _pace_total_sleep_seconds = 0.0


def _classify(exc: Exception) -> NoReturn:
    """Translate yfinance / network errors into subsystem error classes.

    Order matters: ``YFPricesMissingError`` is a subclass of
    ``YFTickerMissingError`` in yfinance 1.2.x, so it must be checked first
    to keep its empty-response semantics. ``YFTzMissingError`` is also a
    subclass of ``YFTickerMissingError`` but both map to ticker-not-found,
    so order between them is moot.

    Unknown exceptions are re-raised unchanged so genuine bugs aren't masked.
    Uses ``getattr`` guards on ``yf_exceptions`` so the module still imports
    if a yfinance patch release renames or drops one of the YF* classes.
    """
    rate_limit_cls = getattr(yf_exceptions, "YFRateLimitError", None)
    prices_missing_cls = getattr(yf_exceptions, "YFPricesMissingError", None)
    tz_missing_cls = getattr(yf_exceptions, "YFTzMissingError", None)
    ticker_missing_cls = getattr(yf_exceptions, "YFTickerMissingError", None)
    yf_data_cls = getattr(yf_exceptions, "YFDataException", None)
    yf_base_cls = getattr(yf_exceptions, "YFException", None)

    if rate_limit_cls is not None and isinstance(exc, rate_limit_cls):
        raise YFinanceRateLimitError(str(exc)) from exc
    if prices_missing_cls is not None and isinstance(exc, prices_missing_cls):
        raise YFinanceEmptyResponseError(str(exc)) from exc
    if tz_missing_cls is not None and isinstance(exc, tz_missing_cls):
        raise YFinanceTickerNotFoundError(str(exc)) from exc
    if ticker_missing_cls is not None and isinstance(exc, ticker_missing_cls):
        raise YFinanceTickerNotFoundError(str(exc)) from exc
    if yf_data_cls is not None and isinstance(exc, yf_data_cls):
        raise YFinanceEmptyResponseError(str(exc)) from exc
    if yf_base_cls is not None and isinstance(exc, yf_base_cls):
        raise YFinanceEmptyResponseError(str(exc)) from exc
    if isinstance(exc, (TimeoutError, ConnectionError, OSError)):
        raise TransientError(str(exc)) from exc
    raise exc


def fetch_info(ticker: str) -> dict:
    """Fetch the ``Ticker.info`` dict for ``ticker``.

    One paced HTTP call. Any exception is routed through ``_classify`` and
    re-raised as a subsystem error class (or unchanged for unknown types).
    """
    _pace()
    try:
        return _make_ticker(ticker).info
    except Exception as exc:
        _classify(exc)


def fetch_quarterly_statements(
    ticker: str,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Fetch ``(income, balance, cashflow)`` quarterly DataFrames.

    Three paced calls (one per attribute access). Order: income → balance →
    cashflow. Any exception is ``_classify``'d.
    """
    try:
        ticker_obj = _make_ticker(ticker)
        _pace()
        income = ticker_obj.quarterly_income_stmt
        _pace()
        balance = ticker_obj.quarterly_balance_sheet
        _pace()
        cashflow = ticker_obj.quarterly_cashflow
    except Exception as exc:
        _classify(exc)
    return income, balance, cashflow


def fetch_annual_statements(
    ticker: str,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Fetch ``(income, balance, cashflow)`` annual DataFrames.

    Three paced calls (one per attribute access). Order: income → balance →
    cashflow. Any exception is ``_classify``'d.
    """
    try:
        ticker_obj = _make_ticker(ticker)
        _pace()
        income = ticker_obj.income_stmt
        _pace()
        balance = ticker_obj.balance_sheet
        _pace()
        cashflow = ticker_obj.cashflow
    except Exception as exc:
        _classify(exc)
    return income, balance, cashflow
