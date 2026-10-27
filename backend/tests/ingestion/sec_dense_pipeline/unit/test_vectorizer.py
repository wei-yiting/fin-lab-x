"""Unit tests for ingest_filing_with_retry's blanket retry classification
(ingest_filing itself is mocked): one retry for Qdrant transport failures
and 5xx responses, first-attempt propagation for everything else.
"""

from unittest.mock import AsyncMock, patch

import pytest
from qdrant_client.http.exceptions import ResponseHandlingException, UnexpectedResponse
from tenacity import wait_none

from backend.ingestion.sec_dense_pipeline.vectorizer import ingest_filing_with_retry
from backend.tests.ingestion.sec_dense_pipeline.conftest import make_toy_filing


@pytest.mark.asyncio
async def test_ingest_filing_with_retry_retries_response_handling_exception():
    """qdrant-client wraps every transport failure into
    ResponseHandlingException and has no built-in retry — any such
    exception gets one blanket retry, regardless of the wrapped source."""
    calls = {"count": 0}

    async def flaky(filing):
        calls["count"] += 1
        if calls["count"] < 2:
            raise ResponseHandlingException(RuntimeError("transport failure"))

    with patch(
        "backend.ingestion.sec_dense_pipeline.vectorizer.ingest_filing",
        new=AsyncMock(side_effect=flaky),
    ):
        await ingest_filing_with_retry.retry_with(wait=wait_none())(make_toy_filing())
    assert calls["count"] == 2


@pytest.mark.asyncio
async def test_ingest_filing_with_retry_retries_5xx_but_not_4xx():
    calls = {"count": 0}

    async def flaky_503(filing):
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
        new=AsyncMock(side_effect=flaky_503),
    ):
        await ingest_filing_with_retry.retry_with(wait=wait_none())(make_toy_filing())
    assert calls["count"] == 2

    calls["count"] = 0

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
    """Anything outside the two Qdrant surfaces (e.g. EmptyIngestError, or
    a plain bug) propagates unchanged on the first attempt."""
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
