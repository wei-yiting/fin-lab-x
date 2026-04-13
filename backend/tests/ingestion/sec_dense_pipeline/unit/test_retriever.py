import pytest
from unittest.mock import MagicMock, patch

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


# --- fetch_filing() EDGAR fallback unit tests ---

def _make_mock_filing(fiscal_year: int = 2025):
    filing = MagicMock()
    filing.metadata.fiscal_year = fiscal_year
    filing.metadata.filing_date = "2025-02-28"
    filing.metadata.filing_type = "10-K"
    filing.metadata.accession_number = "0001234567-25-000001"
    filing.markdown_content = "# Item 1. Business\n\nSome content."
    return filing


def test_fetch_filing_falls_back_to_edgar() -> None:
    from backend.ingestion.sec_dense_pipeline.retriever import fetch_filing

    mock_filing = _make_mock_filing(fiscal_year=2025)

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

        result_filing, result_year = fetch_filing("NVDA")

    assert result_filing is mock_filing
    assert result_year == 2025
    mock_create.assert_called_once()
    mock_pipeline.process.assert_called_once()


def test_fetch_filing_edgar_with_explicit_year() -> None:
    from backend.ingestion.sec_dense_pipeline.retriever import fetch_filing

    mock_filing = _make_mock_filing(fiscal_year=2023)

    with patch(
        "backend.ingestion.sec_filing_pipeline.filing_store.LocalFilingStore.get",
        return_value=None,
    ), patch(
        "backend.ingestion.sec_filing_pipeline.pipeline.SECFilingPipeline.create"
    ) as mock_create:
        mock_pipeline = MagicMock()
        mock_pipeline.process.return_value = mock_filing
        mock_create.return_value = mock_pipeline

        _, result_year = fetch_filing("NVDA", 2023)

    assert result_year == 2023
    _, call_kwargs = mock_pipeline.process.call_args
    assert call_kwargs.get("fiscal_year") == 2023


def test_fetch_filing_edgar_converts_pipeline_error() -> None:
    from backend.ingestion.sec_dense_pipeline.retriever import fetch_filing
    from backend.ingestion.sec_filing_pipeline import TickerNotFoundError

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
        original_exc = TickerNotFoundError("ZZZZZ not found in SEC EDGAR")
        mock_pipeline.process.side_effect = original_exc
        mock_create.return_value = mock_pipeline

        with pytest.raises(JITTickerNotFoundError) as exc_info:
            fetch_filing("ZZZZZ")

    assert exc_info.value.__cause__ is original_exc


def test_fetch_filing_local_hit_skips_edgar() -> None:
    from backend.ingestion.sec_dense_pipeline.retriever import fetch_filing

    cached_filing = _make_mock_filing(fiscal_year=2024)

    with patch(
        "backend.ingestion.sec_filing_pipeline.filing_store.LocalFilingStore.list_filings",
        return_value=[2024],
    ), patch(
        "backend.ingestion.sec_filing_pipeline.filing_store.LocalFilingStore.get",
        return_value=cached_filing,
    ), patch(
        "backend.ingestion.sec_filing_pipeline.pipeline.SECFilingPipeline.create"
    ) as mock_create:
        result_filing, result_year = fetch_filing("NVDA")

    assert result_filing is cached_filing
    assert result_year == 2024
    mock_create.assert_not_called()
