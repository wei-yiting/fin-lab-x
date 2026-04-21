from unittest.mock import MagicMock, patch

import pytest

from backend.tests.ingestion.sec_dense_pipeline.integration.conftest import (
    FIXTURE_MARKDOWN_CLASS_A,
    FIXTURE_MARKDOWN_CLASS_C,
)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_search_returns_full_chunk_schema(clean_collection, mock_openai_embed):
    from backend.ingestion.sec_dense_pipeline.retriever import Chunk, search
    from backend.ingestion.sec_dense_pipeline.vectorizer import ingest_filing

    await ingest_filing(
        ticker="NVDA", year=2025, markdown=FIXTURE_MARKDOWN_CLASS_A
    )

    results = await search(query="GPU revenue", top_k=5)

    assert len(results) == 5
    assert all(isinstance(c, Chunk) for c in results)
    for c in results:
        assert c.ticker == "NVDA"
        assert c.year == 2025
        assert isinstance(c.score, float)
        assert len(c.text) > 0
    scores = [c.score for c in results]
    assert scores == sorted(scores, reverse=True)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_nonexistent_ticker_raises_invalid_ticker(
    clean_collection, mock_openai_embed
):
    """Bogus ticker hits EDGAR via JIT and surfaces as JITInvalidTickerError."""
    from backend.ingestion.sec_dense_pipeline.retriever import (
        JITInvalidTickerError,
        search,
    )
    from backend.ingestion.sec_filing_pipeline.filing_models import (
        TickerNotFoundError,
    )

    mock_pipeline = MagicMock()
    mock_pipeline.resolve_latest_year.side_effect = TickerNotFoundError(
        "FAKECORP not found"
    )
    with patch(
        "backend.ingestion.sec_dense_pipeline.retriever.SECFilingPipeline.create",
        return_value=mock_pipeline,
    ):
        with pytest.raises(JITInvalidTickerError):
            await search(query="test", filters={"ticker": "FAKECORP"}, top_k=10)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_future_year_raises_filing_not_found(
    clean_collection, mock_openai_embed
):
    """Valid ticker but a year with no 10-K surfaces as JITFilingNotFoundError."""
    from backend.ingestion.sec_dense_pipeline.retriever import (
        JITFilingNotFoundError,
        search,
    )
    from backend.ingestion.sec_filing_pipeline.filing_models import (
        FilingNotFoundError,
    )

    mock_pipeline = MagicMock()
    mock_pipeline.download_raw.side_effect = FilingNotFoundError(
        "No 10-K for NVDA in 2099"
    )
    mock_store = MagicMock()
    mock_store.exists.return_value = False
    with patch(
        "backend.ingestion.sec_dense_pipeline.retriever.SECFilingPipeline.create",
        return_value=mock_pipeline,
    ), patch(
        "backend.ingestion.sec_dense_pipeline.retriever.LocalFilingStore",
        return_value=mock_store,
    ):
        with pytest.raises(JITFilingNotFoundError):
            await search(
                query="test",
                filters={"ticker": "NVDA", "year": 2099},
                top_k=10,
            )


@pytest.mark.integration
@pytest.mark.asyncio
async def test_qdrant_down_raises_corpus_unavailable(mock_openai_embed, monkeypatch):
    from backend.ingestion.sec_dense_pipeline.retriever import (
        CorpusUnavailableError,
        search,
    )

    monkeypatch.setenv("QDRANT_URL", "http://unreachable.invalid:9999")
    with pytest.raises(CorpusUnavailableError):
        await search(query="test", top_k=10)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_ticker_filter_excludes_other_tickers(clean_collection, mock_openai_embed):
    from backend.ingestion.sec_dense_pipeline.vectorizer import ingest_filing
    from backend.ingestion.sec_dense_pipeline.retriever import search

    await ingest_filing("NVDA", 2025, FIXTURE_MARKDOWN_CLASS_A)
    await ingest_filing("INTC", 2025, FIXTURE_MARKDOWN_CLASS_C)

    filtered = await search(
        query="semiconductor business",
        filters={"ticker": "NVDA", "year": 2025},
        top_k=10,
    )
    assert len(filtered) > 0
    assert all(c.ticker == "NVDA" for c in filtered)
    assert all(c.year == 2025 for c in filtered)

    unfiltered = await search(
        query="semiconductor business", filters=None, top_k=10
    )
    unfiltered_tickers = {c.ticker for c in unfiltered}
    assert unfiltered_tickers >= {"NVDA", "INTC"}


@pytest.mark.integration
@pytest.mark.asyncio
async def test_year_filter_scopes_results(clean_collection, mock_openai_embed):
    from backend.ingestion.sec_dense_pipeline.vectorizer import ingest_filing
    from backend.ingestion.sec_dense_pipeline.retriever import search

    await ingest_filing("NVDA", 2024, FIXTURE_MARKDOWN_CLASS_A)
    await ingest_filing("NVDA", 2025, FIXTURE_MARKDOWN_CLASS_C)

    results = await search(
        query="semiconductor business",
        filters={"ticker": "NVDA", "year": 2024},
        top_k=10,
    )
    assert len(results) > 0
    assert all(c.year == 2024 for c in results)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_resolved_latest_year_scopes_results(clean_collection, mock_openai_embed):
    """When caller omits year, JIT-resolved latest year must also scope Qdrant
    results — otherwise older cached years bleed into the top-k."""
    from backend.ingestion.sec_dense_pipeline.vectorizer import ingest_filing
    from backend.ingestion.sec_dense_pipeline.retriever import search

    await ingest_filing("NVDA", 2023, FIXTURE_MARKDOWN_CLASS_A)
    await ingest_filing("NVDA", 2024, FIXTURE_MARKDOWN_CLASS_C)

    mock_pipeline = MagicMock()
    mock_pipeline.resolve_latest_year.return_value = 2024
    mock_store = MagicMock()
    mock_store.exists.return_value = False
    with patch(
        "backend.ingestion.sec_dense_pipeline.retriever.SECFilingPipeline.create",
        return_value=mock_pipeline,
    ), patch(
        "backend.ingestion.sec_dense_pipeline.retriever.LocalFilingStore",
        return_value=mock_store,
    ):
        results = await search(
            query="semiconductor business",
            filters={"ticker": "NVDA"},
            top_k=10,
        )

    assert len(results) > 0
    assert all(c.year == 2024 for c in results)
    assert all(c.ticker == "NVDA" for c in results)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_search_succeeds_with_langfuse_down(clean_collection, mock_openai_embed, monkeypatch):
    from backend.ingestion.sec_dense_pipeline.vectorizer import ingest_filing
    from backend.ingestion.sec_dense_pipeline.retriever import search

    await ingest_filing("NVDA", 2025, FIXTURE_MARKDOWN_CLASS_A)

    monkeypatch.setenv("LANGFUSE_HOST", "http://unreachable.invalid:9999")
    results = await search(query="GPU revenue", top_k=5)
    assert len(results) == 5
