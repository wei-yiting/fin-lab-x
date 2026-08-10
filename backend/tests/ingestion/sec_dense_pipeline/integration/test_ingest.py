"""Seam-2 integration tests: ingest_filing → Qdrant-observable state.

Toy ParsedFiling in, assertions on what a Qdrant reader can see: full
payload schema, commit-marker lifecycle (pending → complete, wipe including
the marker, committed-or-absent on mid-ingest failure), and marker exclusion
from content queries.
"""

from unittest.mock import patch

import numpy as np
import pytest
from qdrant_client import QdrantClient, models

from backend.common.errors import TransientError
from backend.ingestion.sec_dense_pipeline.common import (
    check_commit_marker_complete,
    commit_marker_id,
    marker_status_condition,
)
from backend.ingestion.sec_dense_pipeline.vectorizer import ingest_filing
from backend.tests.ingestion.sec_dense_pipeline.integration.conftest import (
    QDRANT_URL,
    TEST_COLLECTION,
)

pytestmark = pytest.mark.asyncio


def _client() -> QdrantClient:
    return QdrantClient(url=QDRANT_URL)


def _content_count(client: QdrantClient) -> int:
    return client.count(
        collection_name=TEST_COLLECTION,
        count_filter=models.Filter(must_not=[marker_status_condition()]),
    ).count


def _marker_status(client: QdrantClient, ticker: str, fiscal_year: int) -> str | None:
    points = client.retrieve(
        collection_name=TEST_COLLECTION,
        ids=[commit_marker_id(ticker, fiscal_year)],
        with_payload=True,
    )
    return points[0].payload["status"] if points else None


@pytest.mark.integration
async def test_ingest_writes_full_payload_and_completes_marker(
    clean_collection, mock_openai_embed, toy_filing
) -> None:
    await ingest_filing(toy_filing)

    client = _client()
    points, _ = client.scroll(
        collection_name=TEST_COLLECTION,
        limit=1000,
        with_payload=True,
        scroll_filter=models.Filter(must_not=[marker_status_condition()]),
    )
    assert points, "no content points ingested"
    for point in points:
        payload = point.payload
        # Citation chain fields, denormalized on every chunk.
        assert payload["accession_number"] == "0000320193-24-000123"
        assert payload["cik"] == "320193"
        assert payload["primary_document"] == "aapl-20240928.htm"
        assert payload["ticker"] == "AAPL"
        assert payload["fiscal_year"] == 2024
        assert payload["filing_type"] == "10-K"
        assert "ingested_at" in payload
        assert isinstance(payload["chunk_index"], int)

    # prelude=None expressed for FlatItem and reclassified; attached for valid.
    by_item = {}
    for point in points:
        by_item.setdefault(point.payload["item"], []).append(point.payload)
    assert all(p["prelude"] is None for p in by_item["1a"])
    assert all(p["prelude"] is None for p in by_item["8"])
    assert all(isinstance(p["prelude"], str) and p["prelude"] for p in by_item["7"])

    assert _marker_status(client, "AAPL", 2024) == "complete"
    assert check_commit_marker_complete(client, TEST_COLLECTION, "AAPL", 2024)


@pytest.mark.integration
async def test_mid_ingest_failure_is_absent_to_readers(
    clean_collection, toy_filing
) -> None:
    async def failing_embed(texts):
        raise TransientError("upstream 5xx during embedding")

    with patch(
        "backend.ingestion.sec_dense_pipeline.vectorizer._embed_texts",
        new=failing_embed,
    ):
        with pytest.raises(TransientError):
            await ingest_filing(toy_filing)

    client = _client()
    # Committed or absent: no content points, marker stuck at pending,
    # retrieval-side check treats the filing as not ingested.
    assert _content_count(client) == 0
    assert _marker_status(client, "AAPL", 2024) == "pending"
    assert not check_commit_marker_complete(client, TEST_COLLECTION, "AAPL", 2024)


@pytest.mark.integration
async def test_wipe_before_rerun_clears_chunks_and_resets_marker(
    clean_collection, mock_openai_embed, toy_filing
) -> None:
    await ingest_filing(toy_filing)
    client = _client()
    first_count = _content_count(client)
    assert first_count > 0
    assert _marker_status(client, "AAPL", 2024) == "complete"

    # Rerun that dies mid-flight: previous chunks and the previous
    # 'complete' marker must both be gone from a reader's perspective.
    async def failing_embed(texts):
        raise TransientError("rerun fails after wipe")

    with patch(
        "backend.ingestion.sec_dense_pipeline.vectorizer._embed_texts",
        new=failing_embed,
    ):
        with pytest.raises(TransientError):
            await ingest_filing(toy_filing)

    assert _content_count(client) == 0
    assert _marker_status(client, "AAPL", 2024) == "pending"
    assert not check_commit_marker_complete(client, TEST_COLLECTION, "AAPL", 2024)


@pytest.mark.integration
async def test_successful_rerun_is_idempotent(
    clean_collection, mock_openai_embed, toy_filing
) -> None:
    await ingest_filing(toy_filing)
    client = _client()
    first_count = _content_count(client)

    await ingest_filing(toy_filing)
    assert _content_count(client) == first_count, "rerun duplicated points"
    assert _marker_status(client, "AAPL", 2024) == "complete"


@pytest.mark.integration
async def test_content_queries_exclude_the_marker_point(
    clean_collection, mock_openai_embed, toy_filing
) -> None:
    await ingest_filing(toy_filing)
    client = _client()

    from backend.ingestion.sec_dense_pipeline.vectorizer import _EMBED_DIM

    query_vector = np.random.default_rng(7).random(_EMBED_DIM).tolist()
    results = client.query_points(
        collection_name=TEST_COLLECTION,
        query=query_vector,
        limit=1000,
        with_payload=True,
        query_filter=models.Filter(must_not=[marker_status_condition()]),
    )
    assert results.points, "content query returned nothing"
    assert all("status" not in p.payload for p in results.points), (
        "marker point leaked into a content query"
    )
    # The exclusion filter is what separates content from markers: without
    # it the same query surfaces exactly one extra point (the marker).
    unfiltered = client.query_points(
        collection_name=TEST_COLLECTION,
        query=query_vector,
        limit=1000,
        with_payload=True,
    )
    assert len(unfiltered.points) == len(results.points) + 1
