import logging

import pytest

from backend.ingestion.quant_data_pipeline.quant_pipeline_errors import TransientError
from backend.ingestion.quant_data_pipeline.quant_retry import with_retry


@pytest.fixture
def fake_sleep(monkeypatch):
    recorded: list[float] = []
    monkeypatch.setattr(
        "backend.ingestion.quant_data_pipeline.quant_retry.time.sleep",
        lambda s: recorded.append(s),
    )
    return recorded


def test_no_error_returns_immediately(fake_sleep):
    call_count = 0

    @with_retry()
    def fn():
        nonlocal call_count
        call_count += 1
        return 42

    result = fn()
    assert result == 42
    assert call_count == 1
    assert fake_sleep == []


def test_eventually_succeeds(fake_sleep):
    call_count = 0

    @with_retry()
    def fn():
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise TransientError("blip")
        return "ok"

    result = fn()
    assert result == "ok"
    assert call_count == 3
    assert fake_sleep == [1.0, 2.0]


def test_exhausts_attempts(fake_sleep):
    call_count = 0

    @with_retry()
    def fn():
        nonlocal call_count
        call_count += 1
        raise TransientError("boom")

    with pytest.raises(TransientError, match="boom"):
        fn()

    assert call_count == 3
    assert fake_sleep == [1.0, 2.0]


def test_non_transient_not_retried(fake_sleep):
    call_count = 0

    @with_retry()
    def fn():
        nonlocal call_count
        call_count += 1
        raise ValueError("nope")

    with pytest.raises(ValueError, match="nope"):
        fn()

    assert call_count == 1
    assert fake_sleep == []


def test_custom_params(fake_sleep):
    call_count = 0

    @with_retry(max_attempts=2, base_delay_seconds=0.5)
    def fn():
        nonlocal call_count
        call_count += 1
        raise TransientError("fail")

    with pytest.raises(TransientError):
        fn()

    assert call_count == 2
    assert fake_sleep == [0.5]


def test_subclass_of_transient_is_retried(fake_sleep):
    class FakeRateLimit(TransientError):
        pass

    call_count = 0

    @with_retry()
    def fn():
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise FakeRateLimit("rate limited")
        return "done"

    result = fn()
    assert result == "done"
    assert fake_sleep == [1.0]


def test_warning_logged_on_retry(fake_sleep, caplog):
    call_count = 0

    @with_retry()
    def fn():
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise TransientError("blip")
        return "ok"

    with caplog.at_level(logging.WARNING):
        fn()

    retrying_records = [r for r in caplog.records if "Retrying in" in r.message]
    assert len(retrying_records) >= 1


def test_with_retry_rejects_zero_max_attempts():
    with pytest.raises(ValueError, match="max_attempts must be >= 1"):
        with_retry(max_attempts=0)


def test_with_retry_rejects_negative_max_attempts():
    with pytest.raises(ValueError, match="max_attempts must be >= 1"):
        with_retry(max_attempts=-1)


def test_with_retry_rejects_negative_base_delay():
    with pytest.raises(ValueError, match="base_delay_seconds must be >= 0"):
        with_retry(base_delay_seconds=-0.5)
