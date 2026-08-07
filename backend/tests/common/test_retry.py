import pytest
from tenacity import wait_none

from backend.common.errors import TickerNotFoundError, TransientError
from backend.common.retry import retry_transient


def test_retries_transient_error_until_success():
    calls = {"count": 0}

    @retry_transient
    def flaky():
        calls["count"] += 1
        if calls["count"] < 2:
            raise TransientError("network blip")
        return "ok"

    assert flaky.retry_with(wait=wait_none())() == "ok"
    assert calls["count"] == 2


def test_reraises_transient_error_after_exhausting_attempts():
    calls = {"count": 0}

    @retry_transient
    def always_fails():
        calls["count"] += 1
        raise TransientError("still down")

    with pytest.raises(TransientError, match="still down"):
        always_fails.retry_with(wait=wait_none())()
    assert calls["count"] == 2


def test_does_not_retry_non_transient_error():
    calls = {"count": 0}

    @retry_transient
    def permanent_failure():
        calls["count"] += 1
        raise TickerNotFoundError("ZZZZ not found")

    with pytest.raises(TickerNotFoundError):
        permanent_failure.retry_with(wait=wait_none())()
    assert calls["count"] == 1
