from contextlib import contextmanager
from unittest.mock import MagicMock, patch

import pytest

from backend.tests.ingestion.sec_dense_pipeline.integration.conftest import (
    FIXTURE_MARKDOWN_CLASS_A,
    QDRANT_URL,
    TEST_COLLECTION,
)


def _qdrant_count(ticker: str) -> int:
    from qdrant_client import QdrantClient, models
    client = QdrantClient(url=QDRANT_URL)
    result = client.count(
        collection_name=TEST_COLLECTION,
        count_filter=models.Filter(
            must=[
                models.FieldCondition(key="ticker", match=models.MatchValue(value=ticker)),
            ],
            must_not=[
                models.FieldCondition(key="status", match=models.MatchAny(any=["pending", "complete"])),
            ],
        ),
    )
    return result.count


def _qdrant_count_raw(ticker: str) -> int:
    """Count points with exact ticker value (case sensitive)."""
    from qdrant_client import QdrantClient, models
    client = QdrantClient(url=QDRANT_URL)
    result = client.count(
        collection_name=TEST_COLLECTION,
        count_filter=models.Filter(
            must=[
                models.FieldCondition(key="ticker", match=models.MatchValue(value=ticker)),
            ],
        ),
    )
    return result.count


def _mock_filing(year=2025, markdown=FIXTURE_MARKDOWN_CLASS_A):
    """Create a mock ParsedFiling-like object."""
    mock_f = MagicMock()
    mock_f.markdown_content = markdown
    mock_f.metadata = MagicMock()
    mock_f.metadata.fiscal_year = year
    mock_f.metadata.filing_date = "2025-02-28"
    mock_f.metadata.filing_type = "10-K"
    mock_f.metadata.accession_number = "0001234567-25-000001"
    return mock_f


def _mock_raw_filing(ticker="NVDA", year=2025):
    """Create a mock RawFiling."""
    mock_raw = MagicMock()
    mock_raw.fiscal_year = year
    mock_raw.ticker = ticker
    return mock_raw


@contextmanager
def _patch_pipeline_and_store(*, latest_year=2025, raw=None, parsed=None, store_hit=None):
    """Patch SECFilingPipeline.create and LocalFilingStore for retriever JIT tests.

    Returns (mock_pipeline, mock_store) so tests can assert on call counts.
    """
    raw = raw if raw is not None else _mock_raw_filing(year=latest_year)
    parsed = parsed if parsed is not None else _mock_filing(year=latest_year)
    with patch(
        "backend.ingestion.sec_dense_pipeline.retriever.SECFilingPipeline.create"
    ) as mock_create, patch(
        "backend.ingestion.sec_dense_pipeline.retriever.LocalFilingStore"
    ) as mock_store_cls:
        mock_pipeline = MagicMock()
        mock_pipeline.resolve_latest_year.return_value = latest_year
        mock_pipeline.download_raw.return_value = raw
        mock_pipeline.parse_raw.return_value = parsed
        mock_create.return_value = mock_pipeline

        mock_store = MagicMock()
        mock_store.get.return_value = store_hit
        mock_store.exists.return_value = store_hit is not None
        mock_store_cls.return_value = mock_store

        yield mock_pipeline, mock_store


@pytest.mark.integration
@pytest.mark.asyncio
async def test_jit_fires_on_empty_collection(clean_collection, mock_openai_embed):
    from backend.ingestion.sec_dense_pipeline.retriever import search

    with _patch_pipeline_and_store(latest_year=2025) as (mock_pipeline, _):
        result = await search(query="test", filters={"ticker": "NVDA"}, top_k=10)

    assert len(result) > 0
    assert all(c.ticker == "NVDA" for c in result)
    mock_pipeline.resolve_latest_year.assert_called_once_with("NVDA", "10-K")
    mock_pipeline.download_raw.assert_called_once()
    mock_pipeline.parse_raw.assert_called_once()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_jit_skips_when_already_complete(clean_collection, mock_openai_embed):
    from backend.ingestion.sec_dense_pipeline.retriever import search
    from backend.ingestion.sec_dense_pipeline.vectorizer import ingest_filing

    await ingest_filing("NVDA", 2025, FIXTURE_MARKDOWN_CLASS_A)

    with _patch_pipeline_and_store(latest_year=2025) as (mock_pipeline, _):
        await search(query="test", filters={"ticker": "NVDA", "year": 2025}, top_k=10)

    mock_pipeline.download_raw.assert_not_called()
    mock_pipeline.parse_raw.assert_not_called()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_jit_fires_for_missing_year(clean_collection, mock_openai_embed):
    from backend.ingestion.sec_dense_pipeline.retriever import search
    from backend.ingestion.sec_dense_pipeline.vectorizer import ingest_filing

    await ingest_filing("NVDA", 2025, FIXTURE_MARKDOWN_CLASS_A)

    with _patch_pipeline_and_store(
        latest_year=2024,
        raw=_mock_raw_filing(year=2024),
        parsed=_mock_filing(year=2024),
    ) as (mock_pipeline, _):
        await search(query="test", filters={"ticker": "NVDA", "year": 2024}, top_k=10)

    mock_pipeline.download_raw.assert_called_once()
    mock_pipeline.parse_raw.assert_called_once()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_jit_does_not_fire_without_ticker(clean_collection, mock_openai_embed):
    from backend.ingestion.sec_dense_pipeline.retriever import search
    from backend.ingestion.sec_dense_pipeline.vectorizer import ingest_filing

    await ingest_filing("NVDA", 2025, FIXTURE_MARKDOWN_CLASS_A)

    with _patch_pipeline_and_store() as (mock_pipeline, _):
        await search(query="test", filters=None, top_k=10)
        await search(query="test", filters={}, top_k=10)

    mock_pipeline.resolve_latest_year.assert_not_called()
    mock_pipeline.download_raw.assert_not_called()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_lowercase_ticker_does_not_dual_store(clean_collection, mock_openai_embed):
    from backend.ingestion.sec_dense_pipeline.retriever import search

    with _patch_pipeline_and_store(latest_year=2025):
        await search(query="test", filters={"ticker": "NVDA"}, top_k=10)
    count_after_first = _qdrant_count("NVDA")

    with _patch_pipeline_and_store(latest_year=2025):
        await search(query="test", filters={"ticker": " nvda "}, top_k=10)

    count_after_second = _qdrant_count("NVDA")
    assert count_after_first == count_after_second
    assert _qdrant_count_raw("nvda") == 0


@pytest.mark.integration
@pytest.mark.asyncio
async def test_disable_jit_raises(clean_collection, monkeypatch):
    from backend.ingestion.sec_dense_pipeline.retriever import JITDisabledError, search

    monkeypatch.setenv("SEC_DISABLE_JIT", "1")

    with pytest.raises(JITDisabledError, match="NVDA"):
        await search(query="test", filters={"ticker": "NVDA"}, top_k=10)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_jit_fires_edgar_fallback_on_empty_store(clean_collection, mock_openai_embed):
    """Verify full JIT path when filing is absent from local store: EDGAR -> parse -> ingest -> search."""
    from backend.ingestion.sec_dense_pipeline.retriever import search

    with _patch_pipeline_and_store(latest_year=2025) as (mock_pipeline, _):
        result = await search(query="GPU data center revenue", filters={"ticker": "NVDA"}, top_k=10)

    assert len(result) > 0
    assert all(c.ticker == "NVDA" for c in result)
    mock_pipeline.download_raw.assert_called_once()
    mock_pipeline.parse_raw.assert_called_once()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_jit_uses_local_store_when_filing_cached(clean_collection, mock_openai_embed):
    """When LocalFilingStore has the filing, JIT should not call EDGAR download."""
    from backend.ingestion.sec_dense_pipeline.retriever import search

    cached = _mock_filing(year=2025)
    with _patch_pipeline_and_store(latest_year=2025, store_hit=cached) as (mock_pipeline, _):
        result = await search(query="test", filters={"ticker": "NVDA"}, top_k=10)

    assert len(result) > 0
    mock_pipeline.download_raw.assert_not_called()
    mock_pipeline.parse_raw.assert_not_called()
