import asyncio
from unittest.mock import MagicMock, patch

import pytest

from backend.ingestion.sec_dense_pipeline.common import canonicalize_ticker
from backend.ingestion.sec_dense_pipeline.retriever import (
    Chunk,
    CorpusUnavailableError,
    EmbeddingServiceError,
    JITDisabledError,
    JITTickerNotFoundError,
    _check_caches,
    _download_and_parse,
    _resolve_latest_year,
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
    assert canonicalize_ticker(raw) == expected


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
        canonicalize_ticker(invalid)


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


# --- _check_caches (Qdrant sentinel + local filing store) ---

def _mock_qdrant_client(sentinel_complete: bool = False):
    client = MagicMock()
    if sentinel_complete:
        mock_point = MagicMock()
        mock_point.payload = {"status": "complete"}
        client.retrieve.return_value = [mock_point]
    else:
        client.retrieve.return_value = []
    return client


@pytest.mark.parametrize(
    "sentinel_complete,filing_exists,expected",
    [
        (False, False, (False, False)),
        (True, False, (True, False)),
        (False, True, (False, True)),
        (True, True, (True, True)),
    ],
)
def test_check_caches_matrix(sentinel_complete, filing_exists, expected) -> None:
    client = _mock_qdrant_client(sentinel_complete=sentinel_complete)
    with patch(
        "backend.ingestion.sec_dense_pipeline.retriever.LocalFilingStore"
    ) as mock_store_cls:
        mock_store_cls.return_value.exists.return_value = filing_exists
        result = _check_caches(client, "test_col", "NVDA", 2024)
    assert result == expected


# --- _resolve_latest_year (EDGAR metadata call) ---

def test_resolve_latest_year_calls_edgar() -> None:
    pipeline = MagicMock()
    pipeline.resolve_latest_year.return_value = 2025
    loop = asyncio.new_event_loop()
    try:
        result = loop.run_until_complete(_resolve_latest_year(pipeline, "NVDA", loop))
    finally:
        loop.close()
    assert result == 2025
    pipeline.resolve_latest_year.assert_called_once_with("NVDA", "10-K")


def test_resolve_latest_year_converts_ticker_not_found() -> None:
    from backend.ingestion.sec_filing_pipeline.filing_models import TickerNotFoundError

    pipeline = MagicMock()
    original = TickerNotFoundError("ZZZZZ not found")
    pipeline.resolve_latest_year.side_effect = original

    loop = asyncio.new_event_loop()
    try:
        with pytest.raises(JITTickerNotFoundError) as exc_info:
            loop.run_until_complete(_resolve_latest_year(pipeline, "ZZZZZ", loop))
    finally:
        loop.close()

    assert exc_info.value.__cause__ is original


# --- _download_and_parse (EDGAR download + markdown parse) ---

def test_download_and_parse_returns_filing() -> None:
    fetched = MagicMock()
    fetched.markdown_content = "# Item 1"
    fetched.metadata.fiscal_year = 2025
    raw = MagicMock()
    raw.fiscal_year = 2025

    pipeline = MagicMock()
    pipeline.download_raw.return_value = raw
    pipeline.parse_raw.return_value = fetched

    loop = asyncio.new_event_loop()
    try:
        result = loop.run_until_complete(
            _download_and_parse(pipeline, "NVDA", 2025, loop)
        )
    finally:
        loop.close()

    assert result is fetched
    pipeline.download_raw.assert_called_once_with("NVDA", "10-K", 2025)
    pipeline.parse_raw.assert_called_once_with(raw, "10-K")


def test_download_and_parse_converts_ticker_not_found() -> None:
    from backend.ingestion.sec_filing_pipeline.filing_models import TickerNotFoundError

    pipeline = MagicMock()
    original = TickerNotFoundError("ZZZZZ not found")
    pipeline.download_raw.side_effect = original

    loop = asyncio.new_event_loop()
    try:
        with pytest.raises(JITTickerNotFoundError) as exc_info:
            loop.run_until_complete(
                _download_and_parse(pipeline, "ZZZZZ", 2025, loop)
            )
    finally:
        loop.close()

    assert exc_info.value.__cause__ is original
