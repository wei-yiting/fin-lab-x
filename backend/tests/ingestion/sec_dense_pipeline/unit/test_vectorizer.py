"""Unit tests for the retry-wrapped orchestration helpers in vectorizer.py.

parse_filing_with_retry / ingest_filing_with_retry are the shared primitives
the JIT retriever and the batch script both build on — tested here in
isolation (parse_filing / ingest_filing themselves are mocked) so the retry
and error-classification behavior is pinned independent of either caller.
"""

from unittest.mock import AsyncMock, patch

import httpx
import pytest
from qdrant_client.http.exceptions import ResponseHandlingException
from tenacity import wait_none

from backend.common.errors import TickerNotFoundError, TransientError
from backend.ingestion.sec_dense_pipeline.vectorizer import (
    ingest_filing_with_retry,
    parse_filing_with_retry,
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


# --- ingest_filing_with_retry ---


@pytest.mark.asyncio
async def test_ingest_filing_with_retry_classifies_connect_error_and_retries():
    calls = {"count": 0}

    async def flaky(filing):
        calls["count"] += 1
        if calls["count"] < 2:
            raise httpx.ConnectError("connection refused")

    with patch(
        "backend.ingestion.sec_dense_pipeline.vectorizer.ingest_filing",
        new=AsyncMock(side_effect=flaky),
    ):
        await ingest_filing_with_retry.retry_with(wait=wait_none())(make_toy_filing())
    assert calls["count"] == 2


@pytest.mark.asyncio
async def test_ingest_filing_with_retry_classifies_response_handling_exception():
    calls = {"count": 0}

    async def flaky(filing):
        calls["count"] += 1
        if calls["count"] < 2:
            raise ResponseHandlingException("upstream reset")

    with patch(
        "backend.ingestion.sec_dense_pipeline.vectorizer.ingest_filing",
        new=AsyncMock(side_effect=flaky),
    ):
        await ingest_filing_with_retry.retry_with(wait=wait_none())(make_toy_filing())
    assert calls["count"] == 2


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
