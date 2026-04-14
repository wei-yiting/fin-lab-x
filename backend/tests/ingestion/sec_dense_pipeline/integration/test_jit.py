import pytest
from unittest.mock import patch, MagicMock
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


def _mock_filing(ticker="NVDA", year=2025, markdown=FIXTURE_MARKDOWN_CLASS_A):
    """Create a mock filing object for JIT tests."""
    mock_f = MagicMock()
    mock_f.markdown_content = markdown
    mock_f.metadata = MagicMock()
    mock_f.metadata.fiscal_year = year
    mock_f.metadata.filing_date = "2025-02-28"
    mock_f.metadata.filing_type = "10-K"
    mock_f.metadata.accession_number = "0001234567-25-000001"
    return mock_f


@pytest.mark.integration
@pytest.mark.asyncio
async def test_jit_fires_on_empty_collection(clean_collection, mock_openai_embed):
    from backend.ingestion.sec_dense_pipeline.retriever import search

    mock_filing = _mock_filing()
    mock_pipeline = MagicMock()
    mock_pipeline.process.return_value = mock_filing

    with patch(
        "backend.ingestion.sec_filing_pipeline.filing_store.LocalFilingStore.list_filings",
        return_value=[],
    ), patch(
        "backend.ingestion.sec_filing_pipeline.filing_store.LocalFilingStore.get",
        return_value=None,
    ), patch(
        "backend.ingestion.sec_filing_pipeline.pipeline.SECFilingPipeline.create"
    ) as mock_create:
        mock_create.return_value = mock_pipeline
        result = await search(query="test", filters={"ticker": "NVDA"}, top_k=10)

    assert len(result) > 0
    assert all(c.ticker == "NVDA" for c in result)
    mock_create.assert_called_once()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_jit_skips_when_already_complete(clean_collection, mock_openai_embed):
    from backend.ingestion.sec_dense_pipeline.retriever import search
    from backend.ingestion.sec_dense_pipeline.vectorizer import ingest_filing

    await ingest_filing("NVDA", 2025, FIXTURE_MARKDOWN_CLASS_A)

    with patch(
        "backend.ingestion.sec_filing_pipeline.pipeline.SECFilingPipeline.create"
    ) as mock_create:
        await search(query="test", filters={"ticker": "NVDA", "year": 2025}, top_k=10)
        mock_create.assert_not_called()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_jit_fires_for_missing_year(clean_collection, mock_openai_embed):
    from backend.ingestion.sec_dense_pipeline.retriever import search
    from backend.ingestion.sec_dense_pipeline.vectorizer import ingest_filing

    await ingest_filing("NVDA", 2025, FIXTURE_MARKDOWN_CLASS_A)

    mock_filing_2024 = _mock_filing(year=2024)
    mock_pipeline = MagicMock()
    mock_pipeline.process.return_value = mock_filing_2024

    with patch(
        "backend.ingestion.sec_filing_pipeline.filing_store.LocalFilingStore.list_filings",
        return_value=[2025],
    ), patch(
        "backend.ingestion.sec_filing_pipeline.filing_store.LocalFilingStore.get",
        return_value=None,
    ), patch(
        "backend.ingestion.sec_filing_pipeline.pipeline.SECFilingPipeline.create"
    ) as mock_create:
        mock_create.return_value = mock_pipeline
        await search(query="test", filters={"ticker": "NVDA", "year": 2024}, top_k=10)
        mock_create.assert_called_once()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_jit_does_not_fire_without_ticker(clean_collection, mock_openai_embed):
    from backend.ingestion.sec_dense_pipeline.retriever import search
    from backend.ingestion.sec_dense_pipeline.vectorizer import ingest_filing

    await ingest_filing("NVDA", 2025, FIXTURE_MARKDOWN_CLASS_A)

    with patch(
        "backend.ingestion.sec_filing_pipeline.pipeline.SECFilingPipeline.create"
    ) as mock_create:
        await search(query="test", filters=None, top_k=10)
        mock_create.assert_not_called()

        await search(query="test", filters={}, top_k=10)
        mock_create.assert_not_called()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_lowercase_ticker_does_not_dual_store(clean_collection, mock_openai_embed):
    from backend.ingestion.sec_dense_pipeline.retriever import search

    mock_f = _mock_filing()
    mock_pipeline = MagicMock()
    mock_pipeline.process.return_value = mock_f

    with patch(
        "backend.ingestion.sec_filing_pipeline.filing_store.LocalFilingStore.list_filings",
        return_value=[],
    ), patch(
        "backend.ingestion.sec_filing_pipeline.filing_store.LocalFilingStore.get",
        return_value=None,
    ), patch(
        "backend.ingestion.sec_filing_pipeline.pipeline.SECFilingPipeline.create"
    ) as mock_create:
        mock_create.return_value = mock_pipeline
        await search(query="test", filters={"ticker": "NVDA"}, top_k=10)
    count_after_first = _qdrant_count("NVDA")

    with patch(
        "backend.ingestion.sec_filing_pipeline.filing_store.LocalFilingStore.list_filings",
        return_value=[],
    ), patch(
        "backend.ingestion.sec_filing_pipeline.filing_store.LocalFilingStore.get",
        return_value=None,
    ), patch(
        "backend.ingestion.sec_filing_pipeline.pipeline.SECFilingPipeline.create"
    ) as mock_create:
        mock_create.return_value = mock_pipeline
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
    """Verify full JIT path when filing is absent from local store: EDGAR download → ingest → search."""
    from backend.ingestion.sec_dense_pipeline.retriever import search

    mock_filing = MagicMock()
    mock_filing.markdown_content = FIXTURE_MARKDOWN_CLASS_A
    mock_filing.metadata.fiscal_year = 2025
    mock_filing.metadata.filing_date = "2025-02-28"
    mock_filing.metadata.filing_type = "10-K"
    mock_filing.metadata.accession_number = "0001234567-25-000001"

    with patch(
        "backend.ingestion.sec_filing_pipeline.filing_store.LocalFilingStore.list_filings",
        return_value=[],
    ), patch(
        "backend.ingestion.sec_filing_pipeline.filing_store.LocalFilingStore.get",
        return_value=None,
    ), patch(
        "backend.ingestion.sec_filing_pipeline.pipeline.SECFilingPipeline.create"
    ) as mock_create:
        mock_pipeline = MagicMock()
        mock_pipeline.process.return_value = mock_filing
        mock_create.return_value = mock_pipeline

        result = await search(query="GPU data center revenue", filters={"ticker": "NVDA"}, top_k=10)

    assert len(result) > 0
    assert all(c.ticker == "NVDA" for c in result)
    mock_create.assert_called_once()
    mock_pipeline.process.assert_called_once()
