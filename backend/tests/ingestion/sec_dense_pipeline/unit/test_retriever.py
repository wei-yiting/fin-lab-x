"""Unit tests for the JIT retriever: pure helpers directly, search()
orchestration with parse_filing / ingest_filing / Qdrant all mocked.

Integration-level behavior (real Qdrant, real commit-marker lifecycle) is
covered separately in integration/test_search.py.
"""

from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest
from qdrant_client import models
from qdrant_client.http.exceptions import UnexpectedResponse

from backend.common.errors import ConfigurationError, TickerNotFoundError
from backend.common.sec_core import FilingNotFoundError
from backend.ingestion.sec_dense_pipeline.retriever import (
    Chunk,
    CorpusUnavailableError,
    EmbeddingServiceError,
    IngestionInProgressError,
    JITDisabledError,
    _build_query_filter,
    _ensure_ingested,
    _inflight_ingests,
    _point_to_chunk,
    _release_ingest_slot,
    _try_claim_ingest_slot,
    search,
)
from backend.ingestion.sec_text_pipeline.parser import EmptyFilingError
from backend.tests.ingestion.sec_dense_pipeline.conftest import make_toy_filing

# --- _build_query_filter (pure) ---


def test_build_query_filter_both_present():
    query_filter = _build_query_filter("AAPL", 2024)
    keys = {c.key for c in query_filter.must}
    assert keys == {"ticker", "fiscal_year"}
    ticker_cond = next(c for c in query_filter.must if c.key == "ticker")
    assert ticker_cond.match == models.MatchValue(value="AAPL")
    fy_cond = next(c for c in query_filter.must if c.key == "fiscal_year")
    assert fy_cond.match == models.MatchValue(value=2024)


def test_build_query_filter_excludes_marker_points():
    query_filter = _build_query_filter("AAPL", 2024)
    assert query_filter.must_not is not None
    assert any(c.key == "status" for c in query_filter.must_not)


# --- in-process ingest registry (pure) ---


def test_try_claim_ingest_slot_first_caller_wins():
    key = ("AAPL", 2024)
    _release_ingest_slot(key)  # defensive: no leftover state from another test
    assert _try_claim_ingest_slot(key) is True
    assert key in _inflight_ingests
    _release_ingest_slot(key)


def test_try_claim_ingest_slot_second_caller_blocked():
    key = ("MSFT", 2025)
    _release_ingest_slot(key)
    assert _try_claim_ingest_slot(key) is True
    assert _try_claim_ingest_slot(key) is False
    _release_ingest_slot(key)


def test_release_ingest_slot_allows_reclaim():
    key = ("NVDA", 2026)
    _release_ingest_slot(key)
    assert _try_claim_ingest_slot(key) is True
    _release_ingest_slot(key)
    assert key not in _inflight_ingests
    assert _try_claim_ingest_slot(key) is True
    _release_ingest_slot(key)


def test_release_ingest_slot_is_idempotent():
    key = ("GE", 2024)
    _release_ingest_slot(key)
    _release_ingest_slot(key)  # must not raise on a key never claimed


# --- _point_to_chunk (pure) ---


def _make_point(**payload_overrides):
    payload = {
        "ticker": "AAPL",
        "fiscal_year": 2024,
        "filing_date": "2024-11-01",
        "filing_type": "10-K",
        "accession_number": "0000320193-24-000123",
        "cik": "320193",
        "primary_document": "aapl-20240928.htm",
        "item": "7",
        "block_heading": "Results of Operations",
        "prelude": "Forward-looking statements...",
        "header_path": "AAPL / 2024 / Item 7 / Results of Operations",
        "chunk_index": 3,
        "text": "Revenue increased...",
        "ingested_at": "2026-08-19T00:00:00+00:00",
    }
    payload.update(payload_overrides)
    return SimpleNamespace(
        id="0d290f1c-1111-4c22-8b7c-1a2b3c4d5e6f", payload=payload, score=0.87
    )


def test_point_to_chunk_maps_all_fields():
    chunk = _point_to_chunk(_make_point())
    assert isinstance(chunk, Chunk)
    assert chunk.ticker == "AAPL"
    assert chunk.fiscal_year == 2024
    assert chunk.accession_number == "0000320193-24-000123"
    assert chunk.cik == "320193"
    assert chunk.primary_document == "aapl-20240928.htm"
    assert chunk.block_heading == "Results of Operations"
    assert chunk.score == 0.87


def test_point_to_chunk_handles_none_block_heading_and_prelude():
    point = _make_point(block_heading=None, prelude=None)
    chunk = _point_to_chunk(point)
    assert chunk.block_heading is None
    assert chunk.prelude is None


def test_point_to_chunk_rejects_none_payload_with_clear_error():
    """Qdrant does not guarantee every point carries a payload
    (ScoredPoint.payload is dict[str, Any] | None) — a None payload must
    raise a clear, typed error, not a bare TypeError from unguarded
    indexing."""
    point = SimpleNamespace(id="deadbeef", payload=None, score=0.5)
    with pytest.raises(ValueError, match="no payload"):
        _point_to_chunk(point)


# --- _ensure_ingested: cache_hit return value, asserted directly ---


@pytest.mark.asyncio
async def test_ensure_ingested_returns_true_on_marker_hit_without_jit():
    client = AsyncMock()
    with (
        patch(
            "backend.ingestion.sec_dense_pipeline.retriever.async_check_commit_marker_complete",
            new=AsyncMock(return_value=True),
        ),
        patch(
            "backend.ingestion.sec_dense_pipeline.retriever.parse_filing_with_retry"
        ) as mock_parse,
    ):
        cache_hit = await _ensure_ingested(client, "collection", "AAPL", 2024)
    assert cache_hit is True
    mock_parse.assert_not_called()


@pytest.mark.asyncio
async def test_ensure_ingested_returns_false_on_marker_miss_after_jit():
    client = AsyncMock()
    toy = make_toy_filing()
    with (
        patch(
            "backend.ingestion.sec_dense_pipeline.retriever.async_check_commit_marker_complete",
            new=AsyncMock(return_value=False),
        ),
        patch(
            "backend.ingestion.sec_dense_pipeline.retriever.parse_filing_with_retry",
            return_value=toy,
        ),
        patch(
            "backend.ingestion.sec_dense_pipeline.retriever.ingest_filing_with_retry",
            new=AsyncMock(),
        ),
    ):
        cache_hit = await _ensure_ingested(client, "collection", "AAPL", 2024)
    assert cache_hit is False


@pytest.mark.asyncio
async def test_ensure_ingested_recheck_after_claim_catches_completed_race():
    """Concurrent JIT stale-marker race: a caller's first marker check
    returns a miss (issued before another caller committed), but by the
    time it claims the in-flight slot the marker is already complete —
    must return cache_hit=True and never re-parse/re-ingest."""
    client = AsyncMock()
    with (
        patch(
            "backend.ingestion.sec_dense_pipeline.retriever.async_check_commit_marker_complete",
            new=AsyncMock(side_effect=[False, True]),
        ),
        patch(
            "backend.ingestion.sec_dense_pipeline.retriever.parse_filing_with_retry"
        ) as mock_parse,
        patch(
            "backend.ingestion.sec_dense_pipeline.retriever.ingest_filing_with_retry",
            new=AsyncMock(),
        ) as mock_ingest,
    ):
        cache_hit = await _ensure_ingested(client, "collection", "AAPL", 2024)
    assert cache_hit is True
    mock_parse.assert_not_called()
    mock_ingest.assert_not_awaited()
    assert ("AAPL", 2024) not in _inflight_ingests


@pytest.mark.asyncio
async def test_ensure_ingested_raises_jit_disabled_on_miss(monkeypatch):
    """SEC_DISABLE_JIT must fire only on a genuine marker miss — the
    marker-hit case is covered separately above and must never reach this
    branch."""
    monkeypatch.setenv("SEC_DISABLE_JIT", "1")
    client = AsyncMock()
    with (
        patch(
            "backend.ingestion.sec_dense_pipeline.retriever.async_check_commit_marker_complete",
            new=AsyncMock(return_value=False),
        ),
        patch(
            "backend.ingestion.sec_dense_pipeline.retriever.parse_filing_with_retry"
        ) as mock_parse,
    ):
        with pytest.raises(JITDisabledError):
            await _ensure_ingested(client, "collection", "AAPL", 2024)
    mock_parse.assert_not_called()
    assert ("AAPL", 2024) not in _inflight_ingests


@pytest.mark.asyncio
async def test_ensure_ingested_propagates_marker_check_failure_without_jit_attempt():
    """A Qdrant failure during the marker check must reach the caller as-is,
    never get folded into a cache-miss that then triggers a JIT parse/ingest
    attempt."""
    client = AsyncMock()
    with (
        patch(
            "backend.ingestion.sec_dense_pipeline.retriever.async_check_commit_marker_complete",
            new=AsyncMock(side_effect=RuntimeError("Qdrant unreachable")),
        ),
        patch(
            "backend.ingestion.sec_dense_pipeline.retriever.parse_filing_with_retry"
        ) as mock_parse,
        patch(
            "backend.ingestion.sec_dense_pipeline.retriever.ingest_filing_with_retry",
            new=AsyncMock(),
        ) as mock_ingest,
    ):
        with pytest.raises(RuntimeError, match="Qdrant unreachable"):
            await _ensure_ingested(client, "collection", "AAPL", 2024)
    mock_parse.assert_not_called()
    mock_ingest.assert_not_awaited()
    assert ("AAPL", 2024) not in _inflight_ingests


# --- search() orchestration (parse_filing / ingest_filing / Qdrant mocked) ---


def _mock_client(*, points: list | None = None):
    client = AsyncMock()
    client.query_points = AsyncMock(return_value=SimpleNamespace(points=points or []))
    client.close = AsyncMock()
    return client


@pytest.fixture(autouse=True)
def _clear_registry():
    """Guard against state leaking between tests via the module-level set."""
    _inflight_ingests.clear()
    yield
    _inflight_ingests.clear()


@pytest.mark.parametrize("top_k", [0, -1, 101, 1000])
@pytest.mark.asyncio
async def test_search_rejects_invalid_top_k(top_k):
    """top_k is validated before filters, so a valid filters dict is passed
    here to isolate this from the separate filters-rejection tests below."""
    with pytest.raises(ValueError):
        await search(query="test", filters={"ticker": "AAPL"}, top_k=top_k)


@pytest.mark.asyncio
async def test_search_raises_when_filters_is_none():
    """ticker is a required search() filter: an omitted/absent filters dict
    must not fall through to an unfiltered, collection-wide query — naive
    search is a proven-harmful retrieval mode with no legitimate production
    caller. filters is a required parameter, so an untyped caller passing
    None explicitly (rather than a typed caller omitting the argument
    outright, which Python itself rejects with a TypeError) is what this
    pins."""
    with pytest.raises(ValueError, match="ticker"):
        await search(query="revenue", filters=None)  # type: ignore[arg-type]


@pytest.mark.asyncio
async def test_search_raises_when_filters_empty():
    with pytest.raises(ValueError, match="ticker"):
        await search(query="revenue", filters={})


@pytest.mark.asyncio
async def test_search_raises_when_fiscal_year_given_without_ticker():
    """fiscal_year alone must not be silently accepted/dropped — ticker is
    mandatory regardless of what else is in filters."""
    with pytest.raises(ValueError, match="ticker"):
        await search(query="revenue", filters={"fiscal_year": 2024})


@pytest.mark.asyncio
async def test_search_rejects_legacy_year_key():
    """The old filter contract's `year` key must be rejected outright, not
    silently ignored — an ignored `year` would resolve the ticker's latest
    fiscal year instead of the one the caller actually asked for."""
    with pytest.raises(ValueError, match="year"):
        await search(query="revenue", filters={"ticker": "AAPL", "year": 2024})


@pytest.mark.asyncio
async def test_search_rejects_non_string_ticker():
    """A non-string ticker must surface as a legible ValueError here, not
    reach canonicalize_ticker as a TypeError that the generic exception
    handler at the bottom of search() would misreport as
    CorpusUnavailableError."""
    with pytest.raises(ValueError, match="ticker"):
        await search(query="revenue", filters={"ticker": 123})


@pytest.mark.asyncio
async def test_search_rejects_non_int_fiscal_year():
    with pytest.raises(ValueError, match="fiscal_year"):
        await search(query="revenue", filters={"ticker": "AAPL", "fiscal_year": "2024"})


@pytest.mark.asyncio
async def test_search_rejects_bool_fiscal_year():
    """bool is technically an int subclass in Python but not a meaningful
    fiscal year — must be rejected like any other wrong type."""
    with pytest.raises(ValueError, match="fiscal_year"):
        await search(query="revenue", filters={"ticker": "AAPL", "fiscal_year": True})


@pytest.mark.asyncio
async def test_search_respects_sec_disable_jit(monkeypatch):
    """Omitted fiscal_year + SEC_DISABLE_JIT=1: latest-year resolution is
    itself an EDGAR call and must be blocked before it ever runs."""
    monkeypatch.setenv("SEC_DISABLE_JIT", "1")
    client = _mock_client()
    with patch(
        "backend.ingestion.sec_dense_pipeline.retriever.AsyncQdrantClient",
        return_value=client,
    ):
        with pytest.raises(JITDisabledError):
            await search(query="revenue", filters={"ticker": "AAPL"})
    client.close.assert_awaited_once()


@pytest.mark.asyncio
async def test_search_disable_jit_allows_hot_hit_with_explicit_fiscal_year(
    monkeypatch,
):
    """An already-ingested (ticker, fiscal_year) must still succeed under
    SEC_DISABLE_JIT=1 — the flag blocks JIT work, not already-complete hot
    hits."""
    monkeypatch.setenv("SEC_DISABLE_JIT", "1")
    client = _mock_client(points=[_make_point()])
    with (
        patch(
            "backend.ingestion.sec_dense_pipeline.retriever.AsyncQdrantClient",
            return_value=client,
        ),
        patch(
            "backend.ingestion.sec_dense_pipeline.retriever.async_ensure_collection_and_indexes",
            new=AsyncMock(),
        ),
        patch(
            "backend.ingestion.sec_dense_pipeline.retriever.async_check_commit_marker_complete",
            new=AsyncMock(return_value=True),
        ),
        patch(
            "backend.ingestion.sec_dense_pipeline.retriever.parse_filing_with_retry"
        ) as mock_parse,
        patch(
            "backend.ingestion.sec_dense_pipeline.retriever.vectorizer._embed_texts",
            new=AsyncMock(return_value=[[0.1] * 3072]),
        ),
    ):
        chunks = await search(
            query="revenue", filters={"ticker": "AAPL", "fiscal_year": 2024}
        )
    assert len(chunks) == 1
    mock_parse.assert_not_called()


@pytest.mark.asyncio
async def test_search_disable_jit_still_blocks_explicit_fiscal_year_marker_miss(
    monkeypatch,
):
    """The other half of the SEC_DISABLE_JIT contract: a genuine marker miss
    on an explicit fiscal_year must still be blocked by the flag, exactly as
    before."""
    monkeypatch.setenv("SEC_DISABLE_JIT", "1")
    client = _mock_client()
    with (
        patch(
            "backend.ingestion.sec_dense_pipeline.retriever.AsyncQdrantClient",
            return_value=client,
        ),
        patch(
            "backend.ingestion.sec_dense_pipeline.retriever.async_ensure_collection_and_indexes",
            new=AsyncMock(),
        ),
        patch(
            "backend.ingestion.sec_dense_pipeline.retriever.async_check_commit_marker_complete",
            new=AsyncMock(return_value=False),
        ),
    ):
        with pytest.raises(JITDisabledError):
            await search(
                query="revenue", filters={"ticker": "AAPL", "fiscal_year": 2024}
            )


@pytest.mark.asyncio
async def test_search_hot_path_skips_parse_and_ingest(monkeypatch):
    monkeypatch.delenv("SEC_DISABLE_JIT", raising=False)
    client = _mock_client(points=[_make_point()])
    with (
        patch(
            "backend.ingestion.sec_dense_pipeline.retriever.AsyncQdrantClient",
            return_value=client,
        ),
        patch(
            "backend.ingestion.sec_dense_pipeline.retriever.async_ensure_collection_and_indexes",
            new=AsyncMock(),
        ),
        patch(
            "backend.ingestion.sec_dense_pipeline.retriever.async_check_commit_marker_complete",
            new=AsyncMock(return_value=True),
        ),
        patch(
            "backend.ingestion.sec_dense_pipeline.retriever.parse_filing_with_retry"
        ) as mock_parse,
        patch(
            "backend.ingestion.sec_dense_pipeline.retriever.ingest_filing_with_retry",
            new=AsyncMock(),
        ) as mock_ingest,
        patch(
            "backend.ingestion.sec_dense_pipeline.retriever.vectorizer._embed_texts",
            new=AsyncMock(return_value=[[0.1] * 3072]),
        ),
    ):
        chunks = await search(
            query="revenue", filters={"ticker": "AAPL", "fiscal_year": 2024}
        )
    assert len(chunks) == 1
    mock_parse.assert_not_called()
    mock_ingest.assert_not_awaited()
    called_filter = client.query_points.call_args.kwargs["query_filter"]
    keys = {c.key for c in called_filter.must}
    assert keys == {"ticker", "fiscal_year"}


@pytest.mark.asyncio
async def test_search_cold_path_parses_and_ingests(monkeypatch):
    monkeypatch.delenv("SEC_DISABLE_JIT", raising=False)
    client = _mock_client(points=[_make_point()])
    toy = make_toy_filing()
    with (
        patch(
            "backend.ingestion.sec_dense_pipeline.retriever.AsyncQdrantClient",
            return_value=client,
        ),
        patch(
            "backend.ingestion.sec_dense_pipeline.retriever.async_ensure_collection_and_indexes",
            new=AsyncMock(),
        ),
        patch(
            "backend.ingestion.sec_dense_pipeline.retriever.async_check_commit_marker_complete",
            new=AsyncMock(return_value=False),
        ),
        patch(
            "backend.ingestion.sec_dense_pipeline.retriever.parse_filing_with_retry",
            return_value=toy,
        ) as mock_parse,
        patch(
            "backend.ingestion.sec_dense_pipeline.retriever.ingest_filing_with_retry",
            new=AsyncMock(),
        ) as mock_ingest,
        patch(
            "backend.ingestion.sec_dense_pipeline.retriever.vectorizer._embed_texts",
            new=AsyncMock(return_value=[[0.1] * 3072]),
        ),
    ):
        chunks = await search(
            query="revenue", filters={"ticker": "AAPL", "fiscal_year": 2024}
        )
    assert len(chunks) == 1
    mock_parse.assert_called_once_with("AAPL", 2024, False)
    mock_ingest.assert_awaited_once_with(toy)
    # Slot must be released after a successful cold path.
    assert ("AAPL", 2024) not in _inflight_ingests


@pytest.mark.asyncio
async def test_search_logs_cache_hit_true_on_hot_path(monkeypatch, caplog):
    """cache_hit is asserted via the log record search() emits, independent
    of span/tracing infrastructure."""
    monkeypatch.delenv("SEC_DISABLE_JIT", raising=False)
    client = _mock_client(points=[_make_point()])
    with (
        patch(
            "backend.ingestion.sec_dense_pipeline.retriever.AsyncQdrantClient",
            return_value=client,
        ),
        patch(
            "backend.ingestion.sec_dense_pipeline.retriever.async_ensure_collection_and_indexes",
            new=AsyncMock(),
        ),
        patch(
            "backend.ingestion.sec_dense_pipeline.retriever.async_check_commit_marker_complete",
            new=AsyncMock(return_value=True),
        ),
        patch(
            "backend.ingestion.sec_dense_pipeline.retriever.vectorizer._embed_texts",
            new=AsyncMock(return_value=[[0.1] * 3072]),
        ),
        caplog.at_level("INFO"),
    ):
        await search(query="revenue", filters={"ticker": "AAPL", "fiscal_year": 2024})
    [record] = [r for r in caplog.records if "cache_hit" in r.getMessage()]
    assert record.getMessage() == (
        "SEC JIT search ticker=AAPL fiscal_year=2024 cache_hit=True"
    )


@pytest.mark.asyncio
async def test_search_logs_cache_hit_false_on_cold_path(monkeypatch, caplog):
    monkeypatch.delenv("SEC_DISABLE_JIT", raising=False)
    client = _mock_client(points=[_make_point()])
    toy = make_toy_filing()
    with (
        patch(
            "backend.ingestion.sec_dense_pipeline.retriever.AsyncQdrantClient",
            return_value=client,
        ),
        patch(
            "backend.ingestion.sec_dense_pipeline.retriever.async_ensure_collection_and_indexes",
            new=AsyncMock(),
        ),
        patch(
            "backend.ingestion.sec_dense_pipeline.retriever.async_check_commit_marker_complete",
            new=AsyncMock(return_value=False),
        ),
        patch(
            "backend.ingestion.sec_dense_pipeline.retriever.parse_filing_with_retry",
            return_value=toy,
        ),
        patch(
            "backend.ingestion.sec_dense_pipeline.retriever.ingest_filing_with_retry",
            new=AsyncMock(),
        ),
        patch(
            "backend.ingestion.sec_dense_pipeline.retriever.vectorizer._embed_texts",
            new=AsyncMock(return_value=[[0.1] * 3072]),
        ),
        caplog.at_level("INFO"),
    ):
        await search(query="revenue", filters={"ticker": "AAPL", "fiscal_year": 2024})
    [record] = [r for r in caplog.records if "cache_hit" in r.getMessage()]
    assert record.getMessage() == (
        "SEC JIT search ticker=AAPL fiscal_year=2024 cache_hit=False"
    )


@pytest.mark.asyncio
async def test_search_resolves_latest_fiscal_year_when_omitted(monkeypatch):
    monkeypatch.delenv("SEC_DISABLE_JIT", raising=False)
    client = _mock_client(points=[])
    toy = make_toy_filing()
    with (
        patch(
            "backend.ingestion.sec_dense_pipeline.retriever.AsyncQdrantClient",
            return_value=client,
        ),
        patch(
            "backend.ingestion.sec_dense_pipeline.retriever.async_ensure_collection_and_indexes",
            new=AsyncMock(),
        ),
        patch(
            "backend.ingestion.sec_dense_pipeline.retriever.async_check_commit_marker_complete",
            new=AsyncMock(return_value=True),
        ),
        patch(
            "backend.ingestion.sec_dense_pipeline.retriever.resolve_latest_fiscal_year_with_retry",
            return_value=2025,
        ) as mock_resolve,
        patch(
            "backend.ingestion.sec_dense_pipeline.retriever.parse_filing_with_retry",
            return_value=toy,
        ),
        patch(
            "backend.ingestion.sec_dense_pipeline.retriever.vectorizer._embed_texts",
            new=AsyncMock(return_value=[[0.1] * 3072]),
        ),
    ):
        await search(query="revenue", filters={"ticker": "AAPL"})
    mock_resolve.assert_called_once_with("AAPL")
    called_filter = client.query_points.call_args.kwargs["query_filter"]
    fy_cond = next(c for c in called_filter.must if c.key == "fiscal_year")
    assert fy_cond.match == models.MatchValue(value=2025)


@pytest.mark.asyncio
async def test_search_second_concurrent_call_gets_ingestion_in_progress(monkeypatch):
    monkeypatch.delenv("SEC_DISABLE_JIT", raising=False)
    client = _mock_client()
    with (
        patch(
            "backend.ingestion.sec_dense_pipeline.retriever.AsyncQdrantClient",
            return_value=client,
        ),
        patch(
            "backend.ingestion.sec_dense_pipeline.retriever.async_ensure_collection_and_indexes",
            new=AsyncMock(),
        ),
        patch(
            "backend.ingestion.sec_dense_pipeline.retriever.async_check_commit_marker_complete",
            new=AsyncMock(return_value=False),
        ),
    ):
        # Simulate a first call's in-flight claim without letting it finish.
        assert _try_claim_ingest_slot(("AAPL", 2024)) is True
        try:
            with pytest.raises(IngestionInProgressError):
                await search(
                    query="revenue", filters={"ticker": "AAPL", "fiscal_year": 2024}
                )
        finally:
            _release_ingest_slot(("AAPL", 2024))


@pytest.mark.asyncio
async def test_search_propagates_empty_filing_error_unwrapped(monkeypatch):
    """Source-level missing item content -> parse_filing raises EmptyFilingError,
    which must reach the caller as-is (structured, legible) — never swallowed
    into a generic CorpusUnavailableError or a silent empty result."""
    monkeypatch.delenv("SEC_DISABLE_JIT", raising=False)
    client = _mock_client()
    with (
        patch(
            "backend.ingestion.sec_dense_pipeline.retriever.AsyncQdrantClient",
            return_value=client,
        ),
        patch(
            "backend.ingestion.sec_dense_pipeline.retriever.async_ensure_collection_and_indexes",
            new=AsyncMock(),
        ),
        patch(
            "backend.ingestion.sec_dense_pipeline.retriever.async_check_commit_marker_complete",
            new=AsyncMock(return_value=False),
        ),
        patch(
            "backend.ingestion.sec_dense_pipeline.retriever.parse_filing_with_retry",
            side_effect=EmptyFilingError("Parsed 0 substantive items for GE FY2024"),
        ),
    ):
        with pytest.raises(EmptyFilingError, match="GE FY2024"):
            await search(query="revenue", filters={"ticker": "GE", "fiscal_year": 2024})
    # Slot must be released even when parse_filing raises.
    assert ("GE", 2024) not in _inflight_ingests


@pytest.mark.parametrize(
    "exc",
    [
        TickerNotFoundError("ZZZZ not found"),
        FilingNotFoundError("no 10-K for FY2099"),
        ConfigurationError("EDGAR_IDENTITY not set"),
    ],
)
@pytest.mark.asyncio
async def test_search_propagates_finlaberror_family_unwrapped(monkeypatch, exc):
    monkeypatch.delenv("SEC_DISABLE_JIT", raising=False)
    client = _mock_client()
    with (
        patch(
            "backend.ingestion.sec_dense_pipeline.retriever.AsyncQdrantClient",
            return_value=client,
        ),
        patch(
            "backend.ingestion.sec_dense_pipeline.retriever.async_ensure_collection_and_indexes",
            new=AsyncMock(),
        ),
        patch(
            "backend.ingestion.sec_dense_pipeline.retriever.async_check_commit_marker_complete",
            new=AsyncMock(return_value=False),
        ),
        patch(
            "backend.ingestion.sec_dense_pipeline.retriever.parse_filing_with_retry",
            side_effect=exc,
        ),
    ):
        with pytest.raises(type(exc)):
            await search(
                query="revenue", filters={"ticker": "ZZZZ", "fiscal_year": 2024}
            )


@pytest.mark.asyncio
async def test_search_wraps_embedding_failure():
    client = _mock_client()
    with (
        patch(
            "backend.ingestion.sec_dense_pipeline.retriever.AsyncQdrantClient",
            return_value=client,
        ),
        patch(
            "backend.ingestion.sec_dense_pipeline.retriever.async_ensure_collection_and_indexes",
            new=AsyncMock(),
        ),
        patch(
            "backend.ingestion.sec_dense_pipeline.retriever.async_check_commit_marker_complete",
            new=AsyncMock(return_value=True),
        ),
        patch(
            "backend.ingestion.sec_dense_pipeline.retriever.vectorizer._embed_texts",
            new=AsyncMock(side_effect=RuntimeError("OpenAI down")),
        ),
    ):
        with pytest.raises(EmbeddingServiceError):
            await search(
                query="revenue", filters={"ticker": "AAPL", "fiscal_year": 2024}
            )


@pytest.mark.asyncio
async def test_search_maps_404_unexpected_response_to_corpus_unavailable():
    """query_points() is the last real Qdrant round-trip search() makes —
    the natural place a 404 (e.g. the collection vanished between the
    earlier ensure-collection call and this query) would actually surface."""
    client = _mock_client()
    client.query_points = AsyncMock(
        side_effect=UnexpectedResponse(
            status_code=404, reason_phrase="Not Found", content=b"", headers=None
        )
    )
    with (
        patch(
            "backend.ingestion.sec_dense_pipeline.retriever.AsyncQdrantClient",
            return_value=client,
        ),
        patch(
            "backend.ingestion.sec_dense_pipeline.retriever.async_ensure_collection_and_indexes",
            new=AsyncMock(),
        ),
        patch(
            "backend.ingestion.sec_dense_pipeline.retriever.async_check_commit_marker_complete",
            new=AsyncMock(return_value=True),
        ),
        patch(
            "backend.ingestion.sec_dense_pipeline.retriever.vectorizer._embed_texts",
            new=AsyncMock(return_value=[[0.1] * 3072]),
        ),
    ):
        with pytest.raises(CorpusUnavailableError):
            await search(
                query="revenue", filters={"ticker": "AAPL", "fiscal_year": 2024}
            )


@pytest.mark.asyncio
async def test_search_maps_malformed_payload_to_corpus_unavailable():
    """A Qdrant payload that doesn't match Chunk's shape makes pydantic
    raise ValidationError while building the Chunk. That must surface as
    CorpusUnavailableError — a vector-store data-integrity problem — not
    leak out raw through the except (ValueError, FinLabError) passthrough
    meant for caller-input rejections."""
    client = _mock_client(points=[_make_point(ticker=None)])
    with (
        patch(
            "backend.ingestion.sec_dense_pipeline.retriever.AsyncQdrantClient",
            return_value=client,
        ),
        patch(
            "backend.ingestion.sec_dense_pipeline.retriever.async_ensure_collection_and_indexes",
            new=AsyncMock(),
        ),
        patch(
            "backend.ingestion.sec_dense_pipeline.retriever.async_check_commit_marker_complete",
            new=AsyncMock(return_value=True),
        ),
        patch(
            "backend.ingestion.sec_dense_pipeline.retriever.vectorizer._embed_texts",
            new=AsyncMock(return_value=[[0.1] * 3072]),
        ),
    ):
        with pytest.raises(CorpusUnavailableError):
            await search(
                query="revenue", filters={"ticker": "AAPL", "fiscal_year": 2024}
            )


@pytest.mark.asyncio
async def test_search_closes_client_even_on_failure():
    client = _mock_client()
    with (
        patch(
            "backend.ingestion.sec_dense_pipeline.retriever.AsyncQdrantClient",
            return_value=client,
        ),
        patch(
            "backend.ingestion.sec_dense_pipeline.retriever.async_ensure_collection_and_indexes",
            new=AsyncMock(side_effect=RuntimeError("boom")),
        ),
    ):
        with pytest.raises(CorpusUnavailableError):
            await search(
                query="revenue", filters={"ticker": "AAPL", "fiscal_year": 2024}
            )
    client.close.assert_awaited_once()
