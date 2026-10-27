"""Integration tests for the JIT retriever: real Qdrant, real commit-marker
lifecycle, real ingest_filing — only parse_filing (EDGAR) and OpenAI
embeddings are mocked, so no test in this file reaches the network.
"""

import asyncio
from unittest.mock import patch

import pytest
from qdrant_client import models

from backend.ingestion.sec_dense_pipeline.common import (
    commit_marker_id,
    marker_status_condition,
)
from backend.ingestion.sec_dense_pipeline.retriever import (
    IngestionInProgressError,
    JITDisabledError,
    search,
)
from backend.ingestion.sec_dense_pipeline.vectorizer import ingest_filing
from backend.tests.ingestion.sec_dense_pipeline.conftest import make_toy_filing
from backend.tests.ingestion.sec_dense_pipeline.integration.conftest import (
    TEST_COLLECTION,
)

pytestmark = pytest.mark.integration


def _marker_complete(client, ticker: str, fiscal_year: int) -> bool:
    """Assert marker state via the raw sync qdrant client — the production
    marker check is async-only and mock-covered in the unit suite."""
    points = client.retrieve(
        collection_name=TEST_COLLECTION,
        ids=[commit_marker_id(ticker, fiscal_year)],
        with_payload=True,
    )
    return bool(points) and points[0].payload["status"] == "complete"


def _content_count(client, ticker: str) -> int:
    return client.count(
        collection_name=TEST_COLLECTION,
        count_filter=models.Filter(
            must=[
                models.FieldCondition(
                    key="ticker", match=models.MatchValue(value=ticker)
                )
            ],
            must_not=[marker_status_condition()],
        ),
    ).count


@pytest.mark.asyncio
async def test_hot_path_returns_results_without_parsing(
    clean_collection, mock_openai_embed, toy_filing, qdrant_client
):
    await ingest_filing(toy_filing)
    assert _marker_complete(qdrant_client, "AAPL", 2024)

    with patch(
        "backend.ingestion.sec_dense_pipeline.retriever.parse_filing_with_retry"
    ) as mock_parse:
        chunks = await search(
            query="revenue", filters={"ticker": "AAPL", "fiscal_year": 2024}
        )
    mock_parse.assert_not_called()
    assert chunks
    assert all(c.ticker == "AAPL" and c.fiscal_year == 2024 for c in chunks)


@pytest.mark.asyncio
async def test_cold_path_ingests_then_serves_from_the_same_call(
    clean_collection, mock_openai_embed, qdrant_client
):
    # clean_collection already guarantees the collection doesn't exist yet
    # at this point (a stronger, more direct precondition than checking the
    # marker — async_check_commit_marker_complete requires an existing collection
    # to check, matching how it's always called downstream of
    # async_ensure_collection_and_indexes() in the real search() flow).
    toy = make_toy_filing()

    with patch(
        "backend.ingestion.sec_dense_pipeline.retriever.parse_filing_with_retry",
        return_value=toy,
    ) as mock_parse:
        chunks = await search(
            query="revenue", filters={"ticker": "AAPL", "fiscal_year": 2024}
        )

    mock_parse.assert_called_once_with("AAPL", 2024, False)
    assert chunks
    assert _marker_complete(qdrant_client, "AAPL", 2024)
    assert _content_count(qdrant_client, "AAPL") > 0


@pytest.mark.asyncio
async def test_cold_path_second_call_after_ingest_is_a_hot_hit(
    clean_collection, mock_openai_embed, qdrant_client
):
    toy = make_toy_filing()
    with patch(
        "backend.ingestion.sec_dense_pipeline.retriever.parse_filing_with_retry",
        return_value=toy,
    ):
        await search(query="revenue", filters={"ticker": "AAPL", "fiscal_year": 2024})

    with patch(
        "backend.ingestion.sec_dense_pipeline.retriever.parse_filing_with_retry"
    ) as mock_parse_again:
        await search(query="revenue", filters={"ticker": "AAPL", "fiscal_year": 2024})
    mock_parse_again.assert_not_called()


@pytest.mark.asyncio
async def test_sec_disable_jit_blocks_cold_ticker_without_touching_edgar(
    clean_collection, monkeypatch
):
    monkeypatch.setenv("SEC_DISABLE_JIT", "1")
    with patch(
        "backend.ingestion.sec_dense_pipeline.retriever.parse_filing_with_retry"
    ) as mock_parse:
        with pytest.raises(JITDisabledError):
            await search(
                query="revenue", filters={"ticker": "AAPL", "fiscal_year": 2024}
            )
    mock_parse.assert_not_called()


@pytest.mark.asyncio
async def test_filter_excludes_other_tickers_no_cross_ticker_bleed(
    clean_collection, mock_openai_embed, qdrant_client
):
    aapl = make_toy_filing(ticker="AAPL")
    msft = make_toy_filing(ticker="MSFT")
    await ingest_filing(aapl)
    await ingest_filing(msft)

    with patch(
        "backend.ingestion.sec_dense_pipeline.retriever.parse_filing_with_retry"
    ):
        chunks = await search(
            query="revenue", filters={"ticker": "AAPL", "fiscal_year": 2024}, top_k=50
        )
    assert chunks
    assert all(c.ticker == "AAPL" for c in chunks)


@pytest.mark.asyncio
async def test_concurrent_jit_for_same_ticker_year_one_wins_one_gets_legible_error(
    clean_collection, mock_openai_embed, qdrant_client
):
    """Envelope §1 concurrent-JIT resolution: the second concurrent caller
    for the same (ticker, fiscal_year) gets IngestionInProgressError, not a
    silent duplicate ingest or a hang.

    The first call's ingest step is held on a barrier until it signals that
    it has reached ingestion — which only happens after it has already
    claimed the in-flight slot — before the second call starts. Without this
    barrier, a first call that finishes (and commits the marker) before the
    second call runs its own marker check would legitimately land a hot hit
    on both calls instead of the in-flight rejection this test targets: a
    different, already-covered scenario (see
    test_ensure_ingested_returns_true_on_marker_hit_without_jit in the unit
    suite).

    Waiting for the barrier races it against first_call itself, bounded by
    an overall timeout: if first_call fails (or unexpectedly succeeds)
    before ever reaching the barrier — e.g. a regression earlier in
    search() — that outcome surfaces immediately instead of this test
    hanging forever on ingest_claimed.wait().
    """
    barrier_timeout_s = 10
    toy = make_toy_filing()
    ingest_claimed = asyncio.Event()
    release_ingest = asyncio.Event()

    async def blocked_then_real_ingest(filing):
        ingest_claimed.set()
        await release_ingest.wait()
        await ingest_filing(filing)

    with (
        patch(
            "backend.ingestion.sec_dense_pipeline.retriever.parse_filing_with_retry",
            side_effect=lambda *a: toy,
        ),
        patch(
            "backend.ingestion.sec_dense_pipeline.retriever.ingest_filing_with_retry",
            new=blocked_then_real_ingest,
        ),
    ):
        first_call = asyncio.create_task(
            search(query="revenue", filters={"ticker": "AAPL", "fiscal_year": 2024})
        )
        claimed_wait = asyncio.create_task(ingest_claimed.wait())
        try:
            done, _pending = await asyncio.wait_for(
                asyncio.wait(
                    {claimed_wait, first_call}, return_when=asyncio.FIRST_COMPLETED
                ),
                timeout=barrier_timeout_s,
            )

            if first_call in done:
                # first_call finished before ever signalling the barrier.
                # Retrieving its result here surfaces the real failure
                # immediately (the regression this race guards against)
                # instead of the test hanging on ingest_claimed.wait()
                # below forever. If it unexpectedly succeeded instead, that
                # is itself surprising and reported explicitly rather than
                # silently falling through.
                first_call.result()
                raise AssertionError(
                    "first_call finished before signalling ingest_claimed; "
                    "expected it to block on the ingest barrier first"
                )

            with pytest.raises(IngestionInProgressError):
                await search(
                    query="revenue", filters={"ticker": "AAPL", "fiscal_year": 2024}
                )
        finally:
            release_ingest.set()
            claimed_wait.cancel()
            try:
                await claimed_wait
            except asyncio.CancelledError:
                pass
            if not first_call.done():
                try:
                    await asyncio.wait_for(first_call, timeout=barrier_timeout_s)
                except TimeoutError:
                    pass

        first_result = await first_call

    assert first_result
    assert _marker_complete(qdrant_client, "AAPL", 2024)
