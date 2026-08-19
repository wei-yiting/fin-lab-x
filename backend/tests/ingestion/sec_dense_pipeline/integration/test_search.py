"""Integration tests for the JIT retriever: real Qdrant, real commit-marker
lifecycle, real ingest_filing — only parse_filing (EDGAR) and OpenAI
embeddings are mocked, so no test in this file reaches the network.
"""

import asyncio
from unittest.mock import patch

import pytest
from qdrant_client import models

from backend.ingestion.sec_dense_pipeline.common import (
    check_commit_marker_complete,
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
    assert check_commit_marker_complete(qdrant_client, TEST_COLLECTION, "AAPL", 2024)

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
    toy = make_toy_filing()
    assert not check_commit_marker_complete(
        qdrant_client, TEST_COLLECTION, "AAPL", 2024
    )

    with patch(
        "backend.ingestion.sec_dense_pipeline.retriever.parse_filing_with_retry",
        return_value=toy,
    ) as mock_parse:
        chunks = await search(
            query="revenue", filters={"ticker": "AAPL", "fiscal_year": 2024}
        )

    mock_parse.assert_called_once_with("AAPL", 2024, False)
    assert chunks
    assert check_commit_marker_complete(qdrant_client, TEST_COLLECTION, "AAPL", 2024)
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
    silent duplicate ingest or a hang."""
    toy = make_toy_filing()

    with patch(
        "backend.ingestion.sec_dense_pipeline.retriever.parse_filing_with_retry",
        side_effect=lambda *a: toy,
    ):
        # asyncio.to_thread runs parse_filing_with_retry off-loop, so both
        # calls race into _ensure_ingested; only one can claim the slot.
        results = await asyncio.gather(
            search(query="revenue", filters={"ticker": "AAPL", "fiscal_year": 2024}),
            search(query="revenue", filters={"ticker": "AAPL", "fiscal_year": 2024}),
            return_exceptions=True,
        )

    errors = [r for r in results if isinstance(r, BaseException)]
    successes = [r for r in results if not isinstance(r, BaseException)]
    assert len(errors) == 1
    assert isinstance(errors[0], IngestionInProgressError)
    assert len(successes) == 1
    assert check_commit_marker_complete(qdrant_client, TEST_COLLECTION, "AAPL", 2024)
