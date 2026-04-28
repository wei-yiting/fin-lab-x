"""Single-flight de-dupe test for fetch_filing_obj.

Covers the race that LangGraph's parallel tool-call planning produces:
two ``sec_filing_list_sections`` calls for the same filing fired together
must collapse into one underlying SEC EDGAR fetch."""

from __future__ import annotations

import threading
import time
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch

import pytest

from backend.common import sec_core
from backend.common.sec_core import FilingType, RateLimitError, fetch_filing_obj


@pytest.fixture(autouse=True)
def _reset_inflight():
    sec_core._inflight.clear()
    yield
    sec_core._inflight.clear()


def test_parallel_calls_share_one_underlying_fetch():
    """8 threads racing on the same key → underlying fetch runs once."""
    call_count = 0
    sentinel = object()

    def slow_fetch(ticker_upper, filing_type, fiscal_year):
        nonlocal call_count
        call_count += 1
        # Hold the slot so all 8 threads observe an in-flight Future
        time.sleep(0.5)
        return sentinel

    with patch.object(sec_core, "_fetch_filing_obj_cached", side_effect=slow_fetch):
        with ThreadPoolExecutor(max_workers=8) as pool:
            futures = [
                pool.submit(fetch_filing_obj, "AAPL", FilingType.TEN_K, 2025)
                for _ in range(8)
            ]
            results = [f.result(timeout=5) for f in futures]

    assert call_count == 1, "underlying fetch must collapse to a single call"
    assert all(r is sentinel for r in results)


def test_winner_exception_propagates_to_all_waiters():
    """If the race winner raises, every waiter must see the same exception."""
    raised = RateLimitError("AAPL", retry_after=600)

    def failing_fetch(ticker_upper, filing_type, fiscal_year):
        time.sleep(0.3)
        raise raised

    with patch.object(sec_core, "_fetch_filing_obj_cached", side_effect=failing_fetch):
        with ThreadPoolExecutor(max_workers=4) as pool:
            futures = [
                pool.submit(fetch_filing_obj, "AAPL", FilingType.TEN_K, 2025)
                for _ in range(4)
            ]
            errors = []
            for f in futures:
                with pytest.raises(RateLimitError) as exc_info:
                    f.result(timeout=5)
                errors.append(exc_info.value)

    assert all(e is raised for e in errors), (
        "every waiter must see the winner's actual exception, not a copy"
    )


def test_inflight_slot_freed_after_success():
    """The (ticker, type, fy) slot must be empty after the call returns,
    so a later call doesn't deadlock on a stale Future."""
    with patch.object(sec_core, "_fetch_filing_obj_cached", return_value=object()):
        fetch_filing_obj("AAPL", FilingType.TEN_K, 2025)
    assert ("AAPL", FilingType.TEN_K, 2025) not in sec_core._inflight


def test_inflight_slot_freed_after_failure():
    """Same invariant on the exception path."""

    def boom(ticker_upper, filing_type, fiscal_year):
        raise RuntimeError("boom")

    with patch.object(sec_core, "_fetch_filing_obj_cached", side_effect=boom):
        with pytest.raises(RuntimeError):
            fetch_filing_obj("AAPL", FilingType.TEN_K, 2025)
    assert ("AAPL", FilingType.TEN_K, 2025) not in sec_core._inflight


def test_different_keys_do_not_block_each_other():
    """A long-running fetch for AAPL must not stall a fetch for MSFT."""
    started = threading.Event()
    release = threading.Event()

    def fetch(ticker_upper, filing_type, fiscal_year):
        if ticker_upper == "AAPL":
            started.set()
            release.wait(timeout=5)
        return ticker_upper

    with patch.object(sec_core, "_fetch_filing_obj_cached", side_effect=fetch):
        with ThreadPoolExecutor(max_workers=2) as pool:
            f_aapl = pool.submit(fetch_filing_obj, "AAPL", FilingType.TEN_K, 2025)
            assert started.wait(timeout=2), "AAPL fetch should start first"
            f_msft = pool.submit(fetch_filing_obj, "MSFT", FilingType.TEN_K, 2025)
            assert f_msft.result(timeout=2) == "MSFT", (
                "MSFT (different key) must not be blocked by AAPL's in-flight fetch"
            )
            release.set()
            assert f_aapl.result(timeout=2) == "AAPL"
