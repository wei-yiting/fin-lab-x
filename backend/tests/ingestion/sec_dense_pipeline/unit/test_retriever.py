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
    _ensure_filing_locally,
    _resolve_year,
    check_sec_cache,
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


# --- check_sec_cache (now only checks embedding sentinel) ---

def _mock_qdrant_client(sentinel_complete: bool = False):
    client = MagicMock()
    if sentinel_complete:
        mock_point = MagicMock()
        mock_point.payload = {"status": "complete"}
        client.retrieve.return_value = [mock_point]
    else:
        client.retrieve.return_value = []
    return client


def test_check_sec_cache_miss() -> None:
    assert check_sec_cache("NVDA", 2024, _mock_qdrant_client(), "test_col") is False


def test_check_sec_cache_hit() -> None:
    assert (
        check_sec_cache("NVDA", 2024, _mock_qdrant_client(sentinel_complete=True), "test_col")
        is True
    )


# --- _resolve_year (EDGAR-first when year is None) ---

def test_resolve_year_passthrough_when_provided() -> None:
    pipeline = MagicMock()
    loop = asyncio.new_event_loop()
    try:
        result = loop.run_until_complete(_resolve_year(pipeline, "NVDA", 2024, loop))
    finally:
        loop.close()
    assert result == 2024
    pipeline.resolve_latest_year.assert_not_called()


def test_resolve_year_calls_edgar_when_none() -> None:
    pipeline = MagicMock()
    pipeline.resolve_latest_year.return_value = 2025
    loop = asyncio.new_event_loop()
    try:
        result = loop.run_until_complete(_resolve_year(pipeline, "NVDA", None, loop))
    finally:
        loop.close()
    assert result == 2025
    pipeline.resolve_latest_year.assert_called_once_with("NVDA", "10-K")


def test_resolve_year_converts_ticker_not_found() -> None:
    from backend.ingestion.sec_filing_pipeline.filing_models import TickerNotFoundError

    pipeline = MagicMock()
    original = TickerNotFoundError("ZZZZZ not found")
    pipeline.resolve_latest_year.side_effect = original

    loop = asyncio.new_event_loop()
    try:
        with pytest.raises(JITTickerNotFoundError) as exc_info:
            loop.run_until_complete(_resolve_year(pipeline, "ZZZZZ", None, loop))
    finally:
        loop.close()

    assert exc_info.value.__cause__ is original


# --- _ensure_filing_locally (filing cache + EDGAR fallback) ---

def test_ensure_filing_locally_returns_cached_when_present() -> None:
    cached = MagicMock()
    pipeline = MagicMock()
    lf = MagicMock()
    loop = asyncio.new_event_loop()

    with patch(
        "backend.ingestion.sec_dense_pipeline.retriever.LocalFilingStore"
    ) as mock_store_cls:
        mock_store_cls.return_value.get.return_value = cached
        try:
            result = loop.run_until_complete(
                _ensure_filing_locally(pipeline, "NVDA", 2024, loop, lf)
            )
        finally:
            loop.close()

    assert result is cached
    pipeline.download_raw.assert_not_called()
    pipeline.parse_raw.assert_not_called()


def test_ensure_filing_locally_fetches_when_cache_miss() -> None:
    fetched = MagicMock()
    fetched.markdown_content = "# Item 1"
    fetched.metadata.fiscal_year = 2025
    raw = MagicMock()
    raw.fiscal_year = 2025

    pipeline = MagicMock()
    pipeline.download_raw.return_value = raw
    pipeline.parse_raw.return_value = fetched

    lf = MagicMock()
    lf.start_as_current_observation.return_value.__enter__.return_value = MagicMock()
    lf.start_as_current_observation.return_value.__exit__.return_value = False

    loop = asyncio.new_event_loop()

    with patch(
        "backend.ingestion.sec_dense_pipeline.retriever.LocalFilingStore"
    ) as mock_store_cls:
        mock_store_cls.return_value.get.return_value = None
        try:
            result = loop.run_until_complete(
                _ensure_filing_locally(pipeline, "NVDA", 2025, loop, lf)
            )
        finally:
            loop.close()

    assert result is fetched
    pipeline.download_raw.assert_called_once_with("NVDA", "10-K", 2025)
    pipeline.parse_raw.assert_called_once_with(raw, "10-K")


def test_ensure_filing_locally_converts_ticker_not_found() -> None:
    from backend.ingestion.sec_filing_pipeline.filing_models import TickerNotFoundError

    pipeline = MagicMock()
    original = TickerNotFoundError("ZZZZZ not found")
    pipeline.download_raw.side_effect = original

    lf = MagicMock()
    lf.start_as_current_observation.return_value.__enter__.return_value = MagicMock()
    lf.start_as_current_observation.return_value.__exit__.return_value = False

    loop = asyncio.new_event_loop()

    with patch(
        "backend.ingestion.sec_dense_pipeline.retriever.LocalFilingStore"
    ) as mock_store_cls:
        mock_store_cls.return_value.get.return_value = None
        try:
            with pytest.raises(JITTickerNotFoundError) as exc_info:
                loop.run_until_complete(
                    _ensure_filing_locally(pipeline, "ZZZZZ", 2025, loop, lf)
                )
        finally:
            loop.close()

    assert exc_info.value.__cause__ is original
