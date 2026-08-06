"""Tests for the sec_filing_search RAG tool.

Seam under test: the tool function only — the retriever is mocked
(prior art: test_sec_filing_tools.py mock pattern). LLM behavior
([N] usage, evidence gaps, routing) belongs to DEV-126 evals.
"""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from backend.ingestion.sec_dense_pipeline.retriever import (
    Chunk,
    JITInvalidTickerError,
)


def _make_chunk(
    *,
    ticker: str = "AAPL",
    year: int = 2024,
    item: str = "Item 1A",
    header_path: str = "AAPL / 2024 / Item 1A. Risk Factors / Competition",
    chunk_index: int = 0,
    accession_number: str | None = "0000320193-24-000123",
    text: str = "Competition is intense.",
    score: float = 0.5,
) -> Chunk:
    return Chunk(
        ticker=ticker,
        year=year,
        filing_date="2024-11-01",
        filing_type="10-K",
        accession_number=accession_number,
        item=item,
        header_path=header_path,
        chunk_index=chunk_index,
        text=text,
        ingested_at="2026-08-06T00:00:00+00:00",
        score=score,
    )


def _make_filing_store(source_url: str | None):
    """Mock LocalFilingStore whose .get() yields metadata.source_url."""
    store = MagicMock()
    if source_url is None:
        store.get.return_value = None
    else:
        filing = MagicMock()
        filing.metadata.source_url = source_url
        store.get.return_value = filing
    store_cls = MagicMock(return_value=store)
    return store_cls


def _patches(
    chunks: list[Chunk] | Exception,
    *,
    resolved_fy: int = 2024,
    source_url: str
    | None = "https://www.sec.gov/Archives/edgar/data/320193/000032019324000123/aapl-20240928.htm",
):
    search_mock = (
        AsyncMock(side_effect=chunks)
        if isinstance(chunks, Exception)
        else AsyncMock(return_value=chunks)
    )
    return (
        patch("backend.agent_engine.tools.sec_filing_search.search", search_mock),
        patch(
            "backend.agent_engine.tools.sec_filing_search._resolve_latest_fiscal_year",
            return_value=resolved_fy,
        ),
        patch(
            "backend.agent_engine.tools.sec_filing_search.LocalFilingStore",
            _make_filing_store(source_url),
        ),
        patch(
            "backend.agent_engine.tools.sec_filing_search.get_stream_writer",
            side_effect=RuntimeError("no writer"),
        ),
        search_mock,
    )


async def _tool_call(args: dict) -> dict:
    from backend.agent_engine.tools.sec_filing_search import sec_filing_search

    msg = await sec_filing_search.ainvoke(
        {
            "args": args,
            "name": "sec_filing_search",
            "type": "tool_call",
            "id": "test-call-id",
        }
    )
    return json.loads(msg.content)


@pytest.mark.asyncio
async def test_groups_by_item_and_orders_chunks_by_document_order():
    """Chunks are grouped by (ticker, year, item); within a group they follow
    chunk_index document order regardless of retrieval score order."""
    chunks = [
        _make_chunk(
            item="Item 7",
            chunk_index=90,
            score=0.9,
            header_path="AAPL / 2024 / Item 7. MD&A / Liquidity",
        ),
        _make_chunk(item="Item 1A", chunk_index=12, score=0.8),
        _make_chunk(item="Item 1A", chunk_index=5, score=0.6),
    ]
    p1, p2, p3, p4, _ = _patches(chunks)
    with p1, p2, p3, p4:
        result = await _tool_call(
            {"query": "competition risks", "ticker": "AAPL", "fiscal_year": 2024}
        )

    assert len(result["groups"]) == 2
    # Group order: best-scoring group first.
    assert result["groups"][0]["item"] == "Item 7"
    assert result["groups"][1]["item"] == "Item 1A"
    # In-group document order by chunk_index, not score.
    indices = [c["source"].rsplit("#", 1)[1] for c in result["groups"][1]["chunks"]]
    assert indices == ["5", "12"]


@pytest.mark.asyncio
async def test_prelude_once_per_group_and_sequential_numbering():
    chunks = [
        _make_chunk(
            item="Item 7",
            chunk_index=90,
            score=0.9,
            header_path="AAPL / 2024 / Item 7. MD&A / Liquidity",
        ),
        _make_chunk(item="Item 1A", chunk_index=5, score=0.6),
        _make_chunk(item="Item 1A", chunk_index=12, score=0.8),
    ]
    p1, p2, p3, p4, _ = _patches(chunks)
    with p1, p2, p3, p4:
        result = await _tool_call({"query": "q", "ticker": "AAPL", "fiscal_year": 2024})

    for group in result["groups"]:
        assert isinstance(group["prelude"], str) and group["prelude"]
        for chunk in group["chunks"]:
            assert "prelude" not in chunk
    numbers = [c["n"] for g in result["groups"] for c in g["chunks"]]
    assert numbers == [1, 2, 3]
    assert result["total_chunks"] == 3


@pytest.mark.asyncio
async def test_stable_citation_id_format():
    """ID scheme: sec://{accession_number}/{item_key}#{chunk_index} with the
    item normalized to the sec_core key space ("Item 1A" -> "1a")."""
    chunks = [_make_chunk(item="Item 1A", chunk_index=12)]
    p1, p2, p3, p4, _ = _patches(chunks)
    with p1, p2, p3, p4:
        result = await _tool_call({"query": "q", "ticker": "AAPL", "fiscal_year": 2024})

    chunk = result["groups"][0]["chunks"][0]
    assert chunk["source"] == "sec://0000320193-24-000123/1a#12"


@pytest.mark.asyncio
async def test_missing_accession_falls_back_to_ticker_year_key():
    """Legacy ingests without filing metadata have accession_number=None; the
    ID degrades to a ticker-year filing key so IDs stay unique across filings."""
    chunks = [_make_chunk(accession_number=None, chunk_index=3)]
    p1, p2, p3, p4, _ = _patches(chunks)
    with p1, p2, p3, p4:
        result = await _tool_call({"query": "q", "ticker": "AAPL", "fiscal_year": 2024})

    assert result["groups"][0]["chunks"][0]["source"] == "sec://AAPL-FY2024/1a#3"


@pytest.mark.asyncio
async def test_fiscal_year_omitted_resolves_latest_and_reports_it():
    chunks = [_make_chunk(year=2025, header_path="AAPL / 2025 / Item 1A / X")]
    p1, p2, p3, p4, search_mock = _patches(chunks, resolved_fy=2025)
    with p1, p2 as resolve_mock, p3, p4:
        result = await _tool_call({"query": "q", "ticker": "aapl"})

    resolve_mock.assert_called_once_with("AAPL")
    assert result["fiscal_year"] == 2025
    assert result["fiscal_year_source"] == "latest"
    # The resolved year is pushed into the retriever filters so retrieval
    # and reporting cannot diverge.
    _, kwargs = search_mock.call_args
    assert kwargs["filters"] == {"ticker": "AAPL", "year": 2025}


@pytest.mark.asyncio
async def test_fiscal_year_explicit_skips_resolution():
    chunks = [_make_chunk()]
    p1, p2, p3, p4, search_mock = _patches(chunks)
    with p1, p2 as resolve_mock, p3, p4:
        result = await _tool_call({"query": "q", "ticker": "AAPL", "fiscal_year": 2024})

    resolve_mock.assert_not_called()
    assert result["fiscal_year"] == 2024
    assert result["fiscal_year_source"] == "requested"
    _, kwargs = search_mock.call_args
    assert kwargs["filters"] == {"ticker": "AAPL", "year": 2024}


@pytest.mark.asyncio
async def test_edgar_url_from_filing_store_metadata():
    url = "https://www.sec.gov/Archives/edgar/data/320193/000032019324000123/aapl-20240928.htm"
    chunks = [_make_chunk()]
    p1, p2, p3, p4, _ = _patches(chunks, source_url=url)
    with p1, p2, p3, p4:
        result = await _tool_call({"query": "q", "ticker": "AAPL", "fiscal_year": 2024})

    assert result["groups"][0]["edgar_url"] == url


@pytest.mark.asyncio
async def test_edgar_url_degrades_to_none_when_store_cold():
    chunks = [_make_chunk()]
    p1, p2, p3, p4, _ = _patches(chunks, source_url=None)
    with p1, p2, p3, p4:
        result = await _tool_call({"query": "q", "ticker": "AAPL", "fiscal_year": 2024})

    assert result["groups"][0]["edgar_url"] is None


@pytest.mark.asyncio
async def test_flat_item_degrades_to_item_level_locator():
    """A chunk whose header_path has no sub-heading below the Item level
    (FlatItem) gets an Item-level title and NO subsection key — the field is
    optional, never fabricated."""
    chunks = [
        _make_chunk(header_path="AAPL / 2024 / Item 1A. Risk Factors"),
        _make_chunk(
            chunk_index=1,
            header_path="AAPL / 2024 / Item 1A. Risk Factors / Competition",
        ),
    ]
    p1, p2, p3, p4, _ = _patches(chunks)
    with p1, p2, p3, p4:
        result = await _tool_call({"query": "q", "ticker": "AAPL", "fiscal_year": 2024})

    flat, nested = result["groups"][0]["chunks"]
    assert "subsection" not in flat
    assert flat["title"] == "AAPL FY2024 10-K · Item 1A"
    assert nested["subsection"] == "Competition"
    assert nested["title"] == "AAPL FY2024 10-K · Item 1A · Competition"


@pytest.mark.asyncio
async def test_evidence_shape_aligns_with_search_result():
    """Each evidence chunk carries source / title / content (Anthropic
    search_result field shape) plus n and score."""
    chunks = [_make_chunk(text="Competition is intense.", score=0.8123456)]
    p1, p2, p3, p4, _ = _patches(chunks)
    with p1, p2, p3, p4:
        result = await _tool_call({"query": "q", "ticker": "AAPL", "fiscal_year": 2024})

    chunk = result["groups"][0]["chunks"][0]
    assert chunk["content"] == "Competition is intense."
    assert chunk["score"] == pytest.approx(0.8123, abs=1e-4)
    assert set(chunk) >= {"n", "source", "title", "content", "score"}


@pytest.mark.asyncio
async def test_language_directive_sandwich_key_order():
    chunks = [_make_chunk()]
    p1, p2, p3, p4, _ = _patches(chunks)
    with p1, p2, p3, p4:
        result = await _tool_call({"query": "q", "ticker": "AAPL", "fiscal_year": 2024})

    keys = list(result.keys())
    assert keys[0] == "language_directive_pre"
    assert keys[-1] == "language_directive_post"


@pytest.mark.asyncio
async def test_empty_results_return_legible_message():
    p1, p2, p3, p4, _ = _patches([])
    with p1, p2, p3, p4:
        result = await _tool_call({"query": "q", "ticker": "AAPL", "fiscal_year": 2024})

    assert result["groups"] == []
    assert "AAPL" in result["message"]
    assert "2024" in result["message"]


@pytest.mark.asyncio
async def test_retriever_errors_bubble_up():
    """JIT/retrieval errors propagate as raised exceptions (consistent with
    the SEC tools convention); the middleware maps them to legible
    ToolMessages."""
    p1, p2, p3, p4, _ = _patches(
        JITInvalidTickerError("Ticker 'ZZZZZ' not found in SEC EDGAR")
    )
    with p1, p2, p3, p4, pytest.raises(JITInvalidTickerError, match="ZZZZZ"):
        await _tool_call({"query": "q", "ticker": "ZZZZZ", "fiscal_year": 2024})
