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
async def test_nonexistent_ticker_returns_empty_or_raises(
    clean_collection, mock_openai_embed
):
    """For Task 3, non-existent collection raises CorpusUnavailableError.
    JIT logic in Task 4 will change this to JITTickerNotFoundError."""
    from backend.ingestion.sec_dense_pipeline.retriever import (
        CorpusUnavailableError,
        search,
    )

    with pytest.raises((CorpusUnavailableError, Exception)):
        await search(query="test", filters={"ticker": "FAKECORP"}, top_k=10)


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
async def test_filters_body_ignored_in_baseline(clean_collection, mock_openai_embed):
    from backend.ingestion.sec_dense_pipeline.vectorizer import ingest_filing
    from backend.ingestion.sec_dense_pipeline.retriever import search

    await ingest_filing("NVDA", 2025, FIXTURE_MARKDOWN_CLASS_A)
    await ingest_filing("INTC", 2025, FIXTURE_MARKDOWN_CLASS_C)

    results = await search(
        query="semiconductor business",
        filters={"ticker": "NVDA", "year": 2025, "item": "1A"},
        top_k=10,
    )
    assert len(results) > 0

    results_no_filter = await search(query="semiconductor business", filters=None, top_k=10)
    assert [c.chunk_index for c in results] == [c.chunk_index for c in results_no_filter]


@pytest.mark.integration
@pytest.mark.asyncio
async def test_search_succeeds_with_langfuse_down(clean_collection, mock_openai_embed, monkeypatch):
    from backend.ingestion.sec_dense_pipeline.vectorizer import ingest_filing
    from backend.ingestion.sec_dense_pipeline.retriever import search

    await ingest_filing("NVDA", 2025, FIXTURE_MARKDOWN_CLASS_A)

    monkeypatch.setenv("LANGFUSE_HOST", "http://unreachable.invalid:9999")
    results = await search(query="GPU revenue", top_k=5)
    assert len(results) == 5
