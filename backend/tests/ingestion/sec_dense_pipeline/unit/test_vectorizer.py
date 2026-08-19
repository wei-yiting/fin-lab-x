"""Unit tests for the retry-wrapped orchestration helpers in vectorizer.py.

parse_filing_with_retry / ingest_filing_with_retry are the shared primitives
the JIT retriever and the batch script both build on — tested here in
isolation (parse_filing / ingest_filing themselves are mocked) so the retry
and error-classification behavior is pinned independent of either caller.
"""

from unittest.mock import AsyncMock, patch

import httpx
import pytest
from pydantic import BaseModel, ValidationError
from qdrant_client.http.exceptions import ResponseHandlingException, UnexpectedResponse
from tenacity import wait_none

from backend.common.errors import TickerNotFoundError, TransientError
from backend.ingestion.sec_dense_pipeline.vectorizer import (
    ingest_filing_with_retry,
    parse_filing_with_retry,
    resolve_latest_fiscal_year_with_retry,
)
from backend.tests.ingestion.sec_dense_pipeline.conftest import make_toy_filing

# --- parse_filing_with_retry ---


def test_parse_filing_with_retry_retries_transient_then_succeeds():
    calls = {"count": 0}
    toy = make_toy_filing()

    def flaky(ticker, fiscal_year, force):
        calls["count"] += 1
        if calls["count"] < 2:
            raise TransientError("EDGAR 5xx")
        return toy

    with patch(
        "backend.ingestion.sec_dense_pipeline.vectorizer.parse_filing",
        side_effect=flaky,
    ):
        result = parse_filing_with_retry.retry_with(wait=wait_none())(
            "AAPL", 2024, False
        )
    assert result is toy
    assert calls["count"] == 2


def test_parse_filing_with_retry_does_not_retry_permanent_failure():
    calls = {"count": 0}

    def always_not_found(ticker, fiscal_year, force):
        calls["count"] += 1
        raise TickerNotFoundError("ZZZZ not found")

    with patch(
        "backend.ingestion.sec_dense_pipeline.vectorizer.parse_filing",
        side_effect=always_not_found,
    ):
        with pytest.raises(TickerNotFoundError):
            parse_filing_with_retry.retry_with(wait=wait_none())("ZZZZ", 2024, False)
    assert calls["count"] == 1


def test_parse_filing_with_retry_passes_force_through():
    with patch(
        "backend.ingestion.sec_dense_pipeline.vectorizer.parse_filing"
    ) as mock_parse:
        mock_parse.return_value = make_toy_filing()
        parse_filing_with_retry.retry_with(wait=wait_none())("AAPL", 2024, True)
    mock_parse.assert_called_once_with("AAPL", 2024, True)


# --- resolve_latest_fiscal_year_with_retry ---


def test_resolve_latest_fiscal_year_with_retry_retries_transient_then_succeeds():
    calls = {"count": 0}

    def flaky(ticker):
        calls["count"] += 1
        if calls["count"] < 2:
            raise TransientError("EDGAR 5xx")
        return 2025

    with patch(
        "backend.ingestion.sec_dense_pipeline.vectorizer._resolve_latest_fiscal_year",
        side_effect=flaky,
    ):
        result = resolve_latest_fiscal_year_with_retry.retry_with(wait=wait_none())(
            "AAPL"
        )
    assert result == 2025
    assert calls["count"] == 2


def test_resolve_latest_fiscal_year_with_retry_does_not_retry_permanent_failure():
    calls = {"count": 0}

    def always_not_found(ticker):
        calls["count"] += 1
        raise TickerNotFoundError("ZZZZ not found")

    with patch(
        "backend.ingestion.sec_dense_pipeline.vectorizer._resolve_latest_fiscal_year",
        side_effect=always_not_found,
    ):
        with pytest.raises(TickerNotFoundError):
            resolve_latest_fiscal_year_with_retry.retry_with(wait=wait_none())("ZZZZ")
    assert calls["count"] == 1


# --- ingest_filing_with_retry ---
#
# qdrant-client's REST transport wraps both connection/timeout failures and
# successful-response schema-validation failures into the same
# ResponseHandlingException type (verified against the installed 1.17.1
# package's api_client.py — see vectorizer._TRANSIENT_SOURCE_TYPES). Tests
# below construct that same wrapped shape (ResponseHandlingException with a
# real `.source`) instead of raising raw httpx/pydantic exceptions directly,
# since that is the actual shape ingest_filing_with_retry receives in
# production.


class _DummyResponseModel(BaseModel):
    x: int


def _make_validation_error() -> ValidationError:
    """A real pydantic ValidationError, matching what qdrant-client's own
    response parsing raises on a malformed-but-successfully-received body."""
    try:
        _DummyResponseModel(x="not-an-int")
    except ValidationError as exc:
        return exc
    raise AssertionError("expected a ValidationError")


@pytest.mark.asyncio
async def test_ingest_filing_with_retry_classifies_connection_shaped_cause_and_retries():
    calls = {"count": 0}

    async def flaky(filing):
        calls["count"] += 1
        if calls["count"] < 2:
            raise ResponseHandlingException(httpx.ConnectError("connection refused"))

    with patch(
        "backend.ingestion.sec_dense_pipeline.vectorizer.ingest_filing",
        new=AsyncMock(side_effect=flaky),
    ):
        await ingest_filing_with_retry.retry_with(wait=wait_none())(make_toy_filing())
    assert calls["count"] == 2


@pytest.mark.asyncio
async def test_ingest_filing_with_retry_classifies_write_timeout_and_retries():
    """WriteTimeout is a httpx.TimeoutException subclass, not one of the
    previously-hardcoded three source types — pins the broadened tuple."""
    calls = {"count": 0}

    async def flaky(filing):
        calls["count"] += 1
        if calls["count"] < 2:
            raise ResponseHandlingException(httpx.WriteTimeout("write timed out"))

    with patch(
        "backend.ingestion.sec_dense_pipeline.vectorizer.ingest_filing",
        new=AsyncMock(side_effect=flaky),
    ):
        await ingest_filing_with_retry.retry_with(wait=wait_none())(make_toy_filing())
    assert calls["count"] == 2


@pytest.mark.asyncio
async def test_ingest_filing_with_retry_classifies_read_error_and_retries():
    """ReadError is a httpx.NetworkError subclass, not one of the
    previously-hardcoded three source types — pins the broadened tuple."""
    calls = {"count": 0}

    async def flaky(filing):
        calls["count"] += 1
        if calls["count"] < 2:
            raise ResponseHandlingException(httpx.ReadError("connection reset"))

    with patch(
        "backend.ingestion.sec_dense_pipeline.vectorizer.ingest_filing",
        new=AsyncMock(side_effect=flaky),
    ):
        await ingest_filing_with_retry.retry_with(wait=wait_none())(make_toy_filing())
    assert calls["count"] == 2


@pytest.mark.asyncio
async def test_ingest_filing_with_retry_does_not_retry_remote_protocol_error():
    """Pins the deliberate exclusion of RemoteProtocolError from the
    transient set (see the reasoning comment on _TRANSIENT_SOURCE_TYPES)."""
    calls = {"count": 0}

    async def always_protocol_error(filing):
        calls["count"] += 1
        raise ResponseHandlingException(
            httpx.RemoteProtocolError("peer closed connection mid-response")
        )

    with patch(
        "backend.ingestion.sec_dense_pipeline.vectorizer.ingest_filing",
        new=AsyncMock(side_effect=always_protocol_error),
    ):
        with pytest.raises(ResponseHandlingException):
            await ingest_filing_with_retry.retry_with(wait=wait_none())(
                make_toy_filing()
            )
    assert calls["count"] == 1


@pytest.mark.asyncio
async def test_ingest_filing_with_retry_does_not_retry_validation_error_shaped_cause():
    """A ResponseHandlingException wrapping a ValidationError means Qdrant
    answered but the response didn't match the expected schema — a
    permanent problem, not a transient one; must not be retried."""
    calls = {"count": 0}

    async def always_validation_error(filing):
        calls["count"] += 1
        raise ResponseHandlingException(_make_validation_error())

    with patch(
        "backend.ingestion.sec_dense_pipeline.vectorizer.ingest_filing",
        new=AsyncMock(side_effect=always_validation_error),
    ):
        with pytest.raises(ResponseHandlingException):
            await ingest_filing_with_retry.retry_with(wait=wait_none())(
                make_toy_filing()
            )
    assert calls["count"] == 1


@pytest.mark.asyncio
async def test_ingest_filing_with_retry_classifies_5xx_unexpected_response_and_retries():
    calls = {"count": 0}

    async def flaky(filing):
        calls["count"] += 1
        if calls["count"] < 2:
            raise UnexpectedResponse(
                status_code=503,
                reason_phrase="Service Unavailable",
                content=b"",
                headers=None,
            )

    with patch(
        "backend.ingestion.sec_dense_pipeline.vectorizer.ingest_filing",
        new=AsyncMock(side_effect=flaky),
    ):
        await ingest_filing_with_retry.retry_with(wait=wait_none())(make_toy_filing())
    assert calls["count"] == 2


@pytest.mark.asyncio
async def test_ingest_filing_with_retry_does_not_retry_4xx_unexpected_response():
    calls = {"count": 0}

    async def always_400(filing):
        calls["count"] += 1
        raise UnexpectedResponse(
            status_code=400, reason_phrase="Bad Request", content=b"", headers=None
        )

    with patch(
        "backend.ingestion.sec_dense_pipeline.vectorizer.ingest_filing",
        new=AsyncMock(side_effect=always_400),
    ):
        with pytest.raises(UnexpectedResponse):
            await ingest_filing_with_retry.retry_with(wait=wait_none())(
                make_toy_filing()
            )
    assert calls["count"] == 1


@pytest.mark.asyncio
async def test_ingest_filing_with_retry_does_not_retry_unclassified_error():
    calls = {"count": 0}

    async def always_value_error(filing):
        calls["count"] += 1
        raise ValueError("not a transient failure")

    with patch(
        "backend.ingestion.sec_dense_pipeline.vectorizer.ingest_filing",
        new=AsyncMock(side_effect=always_value_error),
    ):
        with pytest.raises(ValueError, match="not a transient failure"):
            await ingest_filing_with_retry.retry_with(wait=wait_none())(
                make_toy_filing()
            )
    assert calls["count"] == 1


@pytest.mark.asyncio
async def test_ingest_filing_with_retry_succeeds_first_try_without_retry():
    mock_ingest = AsyncMock(return_value=None)
    with patch(
        "backend.ingestion.sec_dense_pipeline.vectorizer.ingest_filing",
        new=mock_ingest,
    ):
        await ingest_filing_with_retry.retry_with(wait=wait_none())(make_toy_filing())
    mock_ingest.assert_awaited_once()
