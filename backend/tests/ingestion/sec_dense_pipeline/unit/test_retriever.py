import pytest

from backend.ingestion.sec_dense_pipeline.retriever import (
    Chunk,
    CorpusUnavailableError,
    EmbeddingServiceError,
    JITDisabledError,
    JITTickerNotFoundError,
    _canonicalize_ticker,
    search,
)


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("NVDA", "NVDA"),
        (" NVDA ", "NVDA"),
        ("nvda", "NVDA"),
        ("NVDA\n", "NVDA"),
        ("BRK.B", "BRK.B"),
        (" brk.b\t", "BRK.B"),
    ],
)
def test_canonicalize_ticker(raw: str, expected: str) -> None:
    assert _canonicalize_ticker(raw) == expected


@pytest.mark.parametrize(
    "invalid",
    [
        ["NVDA", "AMD"],
        None,
        123,
    ],
)
def test_canonicalize_ticker_rejects_non_string(invalid) -> None:
    with pytest.raises((ValueError, TypeError)):
        _canonicalize_ticker(invalid)


def test_chunk_with_accession_number_none() -> None:
    chunk = Chunk(
        ticker="NVDA",
        year=2025,
        filing_date="2025-02-28",
        filing_type="10-K",
        accession_number=None,
        item="Item 1A",
        header_path="NVDA / 2025 / Item 1A / Risks",
        chunk_index=0,
        text="Some SEC content...",
        ingested_at="2026-04-09T00:00:00Z",
        score=0.85,
    )
    assert chunk.accession_number is None
    dumped = chunk.model_dump()
    assert dumped["accession_number"] is None


def test_chunk_with_accession_number_present() -> None:
    chunk = Chunk(
        ticker="AAPL",
        year=2024,
        filing_date="2024-11-01",
        filing_type="10-K",
        accession_number="0000320193-24-000123",
        item="Item 7",
        header_path="AAPL / 2024 / Item 7 / MD&A",
        chunk_index=5,
        text="Revenue discussion...",
        ingested_at="2026-04-09T00:00:00Z",
        score=0.72,
    )
    assert chunk.accession_number == "0000320193-24-000123"


@pytest.mark.parametrize("top_k", [0, -1, -100, 101, 1000])
@pytest.mark.asyncio
async def test_search_rejects_invalid_top_k(top_k: int) -> None:
    with pytest.raises(ValueError):
        await search(query="test", top_k=top_k)



def test_exception_classes_are_distinct() -> None:
    assert not issubclass(JITTickerNotFoundError, EmbeddingServiceError)
    assert not issubclass(EmbeddingServiceError, CorpusUnavailableError)


def test_exception_wraps_cause() -> None:
    original = ConnectionError("Qdrant refused connection")
    err = CorpusUnavailableError("Qdrant down")
    err.__cause__ = original
    assert err.__cause__ is original


def test_jit_disabled_error_is_separate() -> None:
    err = JITDisabledError(
        "JIT disabled by SEC_DISABLE_JIT=1; pre-load ticker=NVDA via batch script"
    )
    assert "NVDA" in str(err)
    assert "batch" in str(err).lower()
