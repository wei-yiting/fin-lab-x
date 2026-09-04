"""Tests for the sec_filing_search RAG tool.

Seam under test: the tool function only — the retriever is mocked
(prior art: test_sec_filing_tools.py mock pattern). LLM behavior
([N] usage, evidence gaps, routing) belongs to the RAG end-to-end eval.
"""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from pydantic import ValidationError

from backend.common.errors import TickerNotFoundError, TransientError
from backend.common.sec_core import FilingNotFoundError, FilingRef, FilingType
from backend.ingestion.sec_dense_pipeline.retriever import (
    Chunk,
    CorpusUnavailableError,
)


def _make_chunk(
    *,
    ticker: str = "AAPL",
    fiscal_year: int = 2024,
    item: str = "1a",
    header_path: str = "AAPL / 2024 / Item 1A. Risk Factors / Competition",
    chunk_index: int = 0,
    accession_number: str = "0000320193-24-000123",
    cik: str = "320193",
    primary_document: str = "aapl-20240928.htm",
    text: str = "Competition is intense.",
    score: float = 0.5,
) -> Chunk:
    return Chunk(
        ticker=ticker,
        fiscal_year=fiscal_year,
        filing_date="2024-11-01",
        filing_type="10-K",
        accession_number=accession_number,
        cik=cik,
        primary_document=primary_document,
        item=item,
        block_heading=None,
        prelude=None,
        header_path=header_path,
        chunk_index=chunk_index,
        text=text,
        ingested_at="2026-08-06T00:00:00+00:00",
        score=score,
    )


def _expected_edgar_url(chunk: Chunk) -> str:
    accession_no_dashes = chunk.accession_number.replace("-", "")
    return (
        f"https://www.sec.gov/Archives/edgar/data/{chunk.cik}/"
        f"{accession_no_dashes}/{chunk.primary_document}"
    )


def _filing_ref(fiscal_year: int) -> FilingRef:
    return FilingRef(
        fiscal_year=fiscal_year,
        period_of_report=f"{fiscal_year}-09-28",
        accession_number=f"0000320193-{str(fiscal_year)[2:]}-000123",
    )


def _locate_filing_ref_mock(resolved_fy: int):
    """Mock locate_filing_ref: fiscal_year=None resolves to ``resolved_fy``;
    an explicit year echoes back (index lookup found it)."""

    def _locate(ticker: str, filing_type: FilingType, fiscal_year: int | None):
        return _filing_ref(resolved_fy if fiscal_year is None else fiscal_year)

    return MagicMock(side_effect=_locate)


def _patches(chunks: list[Chunk] | Exception, *, resolved_fy: int = 2024):
    search_mock = (
        AsyncMock(side_effect=chunks)
        if isinstance(chunks, Exception)
        else AsyncMock(return_value=chunks)
    )
    return (
        patch("backend.agent_engine.tools.sec_filing_search.search", search_mock),
        patch(
            "backend.agent_engine.tools.sec_filing_search.locate_filing_ref",
            _locate_filing_ref_mock(resolved_fy),
        ),
        patch(
            "backend.agent_engine.tools.sec_filing_search.get_stream_writer",
            side_effect=RuntimeError("no writer"),
        ),
        search_mock,
    )


async def _tool_message(args: dict):
    from backend.agent_engine.tools.sec_filing_search import sec_filing_search

    return await sec_filing_search.ainvoke(
        {
            "args": args,
            "name": "sec_filing_search",
            "type": "tool_call",
            "id": "test-call-id",
        }
    )


async def _tool_call(args: dict) -> dict:
    """Model-facing content only (what the LLM reads)."""
    msg = await _tool_message(args)
    return json.loads(msg.content)


@pytest.mark.asyncio
async def test_groups_by_item_and_orders_chunks_by_document_order():
    """Chunks are grouped by (ticker, fiscal_year, item); within a group they
    follow chunk_index document order regardless of retrieval score order."""
    chunks = [
        _make_chunk(
            item="7",
            chunk_index=90,
            score=0.9,
            header_path="AAPL / 2024 / Item 7. MD&A / Liquidity",
        ),
        _make_chunk(item="1a", chunk_index=12, score=0.8),
        _make_chunk(item="1a", chunk_index=5, score=0.6),
    ]
    p1, p2, p3, _ = _patches(chunks)
    with p1, p2, p3:
        result = await _tool_call(
            {"query": "competition risks", "ticker": "AAPL", "fiscal_year": 2024}
        )

    assert len(result["groups"]) == 2
    # Group order: best-scoring group first. Group "item" is the raw
    # sec_core key, not the display label (that's _item_display's job, used
    # in the prelude text and chunk titles instead).
    assert result["groups"][0]["item"] == "7"
    assert result["groups"][1]["item"] == "1a"
    # In-group document order by chunk_index, not score.
    indices = [c["source"].rsplit("#", 1)[1] for c in result["groups"][1]["chunks"]]
    assert indices == ["5", "12"]


@pytest.mark.asyncio
async def test_prelude_once_per_group_and_no_tool_side_ordinal():
    chunks = [
        _make_chunk(
            item="7",
            chunk_index=90,
            score=0.9,
            header_path="AAPL / 2024 / Item 7. MD&A / Liquidity",
        ),
        _make_chunk(item="1a", chunk_index=5, score=0.6),
        _make_chunk(item="1a", chunk_index=12, score=0.8),
    ]
    p1, p2, p3, _ = _patches(chunks)
    with p1, p2, p3:
        result = await _tool_call({"query": "q", "ticker": "AAPL", "fiscal_year": 2024})

    for group in result["groups"]:
        assert isinstance(group["prelude"], str) and group["prelude"]
        for chunk in group["chunks"]:
            assert "prelude" not in chunk
    # No per-call ordinal: the model owns [N] numbering across the answer.
    assert all("n" not in c for g in result["groups"] for c in g["chunks"])
    assert result["total_chunks"] == 3


@pytest.mark.asyncio
async def test_stable_citation_id_format():
    """ID scheme: sec://{accession_number}/{item}#{chunk_index}. The
    dense-pipeline payload's item field is already the sec_core key space
    ("1a", not "Item 1A") by contract — see chunking.py's own comment."""
    chunks = [_make_chunk(item="1a", chunk_index=12)]
    p1, p2, p3, _ = _patches(chunks)
    with p1, p2, p3:
        result = await _tool_call({"query": "q", "ticker": "AAPL", "fiscal_year": 2024})

    chunk = result["groups"][0]["chunks"][0]
    assert chunk["source"] == "sec://0000320193-24-000123/1a#12"


@pytest.mark.asyncio
async def test_fiscal_year_omitted_resolves_latest_and_reports_it():
    chunks = [_make_chunk(fiscal_year=2025, header_path="AAPL / 2025 / Item 1A / X")]
    p1, p2, p3, search_mock = _patches(chunks, resolved_fy=2025)
    with p1, p2 as locate_mock, p3:
        result = await _tool_call({"query": "q", "ticker": "aapl"})

    locate_mock.assert_called_once_with("AAPL", FilingType.TEN_K, None)
    assert result["fiscal_year"] == 2025
    assert result["fiscal_year_end"] == "2025-09-28"
    assert result["fiscal_year_source"] == "latest"
    # The resolved year is pushed into the retriever filters so retrieval
    # and reporting cannot diverge.
    _, kwargs = search_mock.call_args
    assert kwargs["filters"] == {"ticker": "AAPL", "fiscal_year": 2025}


@pytest.mark.asyncio
async def test_fiscal_year_explicit_is_validated_against_index():
    """An explicit year still goes through the index lookup: it supplies the
    FY end date and turns a nonexistent 10-K year into a legible error
    instead of an empty retrieval."""
    chunks = [_make_chunk()]
    p1, p2, p3, search_mock = _patches(chunks)
    with p1, p2 as locate_mock, p3:
        result = await _tool_call({"query": "q", "ticker": "AAPL", "fiscal_year": 2024})

    locate_mock.assert_called_once_with("AAPL", FilingType.TEN_K, 2024)
    assert result["fiscal_year"] == 2024
    assert result["fiscal_year_end"] == "2024-09-28"
    assert result["fiscal_year_source"] == "requested"
    _, kwargs = search_mock.call_args
    assert kwargs["filters"] == {"ticker": "AAPL", "fiscal_year": 2024}


@pytest.mark.asyncio
async def test_index_lookup_errors_bubble_before_retrieval():
    p1, _, p3, search_mock = _patches([_make_chunk()])
    locate_patch = patch(
        "backend.agent_engine.tools.sec_filing_search.locate_filing_ref",
        side_effect=TickerNotFoundError("Ticker 'ZZZZZ' has no 10-K filings"),
    )
    with p1, locate_patch, p3, pytest.raises(TickerNotFoundError, match="ZZZZZ"):
        await _tool_call({"query": "q", "ticker": "ZZZZZ"})
    search_mock.assert_not_called()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "fiscal_year,exc",
    [
        pytest.param(
            1994,
            FilingNotFoundError(
                "AAPL has no 10-K filing history before FY2003; fiscal "
                "year 1994 could never have one."
            ),
            id="structurally-impossible",
        ),
        pytest.param(
            2026,
            FilingNotFoundError(
                "No 10-K filed yet for AAPL fiscal year 2026 — the most "
                "recent available is FY2024."
            ),
            id="not-yet-due",
        ),
        pytest.param(
            2019,
            TransientError("SEC EDGAR returned 503 for AAPL."),
            id="transient",
        ),
    ],
)
async def test_nonexistence_reasons_bubble_up_unmodified(fiscal_year, exc):
    """A requested fiscal_year's 10-K can be unavailable for three distinct
    reasons (structurally impossible, not yet due, transient upstream
    failure), and each must bubble through the tool call unmodified — same
    pattern as test_index_lookup_errors_bubble_before_retrieval. The
    message-distinguishing logic itself lives in sec_core's
    locate_filing_ref/_locate_filing_cached (see test_sec_core.py); this
    seam only proves the tool doesn't mangle or collapse whatever it
    raises."""
    p1, _, p3, search_mock = _patches([_make_chunk()])
    locate_patch = patch(
        "backend.agent_engine.tools.sec_filing_search.locate_filing_ref",
        side_effect=exc,
    )
    with p1, locate_patch, p3, pytest.raises(type(exc)) as exc_info:
        await _tool_call({"query": "q", "ticker": "AAPL", "fiscal_year": fiscal_year})
    assert str(exc_info.value) == str(exc)
    search_mock.assert_not_called()


@pytest.mark.asyncio
@pytest.mark.parametrize("query", ["", "   "])
async def test_blank_query_rejected_before_retrieval(query):
    """Empty and whitespace-only queries fail schema validation before the
    tool body runs — retrieval and the index lookup are never reached."""
    p1, p2, p3, search_mock = _patches([_make_chunk()])
    with p1, p2 as locate_mock, p3, pytest.raises(ValidationError):
        await _tool_call({"query": query, "ticker": "AAPL", "fiscal_year": 2024})
    search_mock.assert_not_called()
    locate_mock.assert_not_called()


@pytest.mark.asyncio
async def test_blank_ticker_rejected_before_retrieval():
    """A whitespace-only ticker fails schema validation before the tool body
    runs — retrieval and the index lookup are never reached (mirrors the
    blank-query check: min_length=1 alone lets "   " through)."""
    p1, p2, p3, search_mock = _patches([_make_chunk()])
    with p1, p2 as locate_mock, p3, pytest.raises(ValidationError):
        await _tool_call({"query": "q", "ticker": "   ", "fiscal_year": 2024})
    search_mock.assert_not_called()
    locate_mock.assert_not_called()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "args",
    [
        {"query": "q", "ticker": "", "fiscal_year": 2024},
        {"query": "q", "ticker": "AAPL", "fiscal_year": 1900},
    ],
)
async def test_ticker_and_fiscal_year_bounds_rejected_before_retrieval(args):
    """An empty ticker and a pre-EDGAR-mandate fiscal_year both fail schema
    validation before retrieval or the index lookup run."""
    p1, p2, p3, search_mock = _patches([_make_chunk()])
    with p1, p2 as locate_mock, p3, pytest.raises(ValidationError):
        await _tool_call(args)
    search_mock.assert_not_called()
    locate_mock.assert_not_called()


@pytest.mark.asyncio
async def test_edgar_url_rides_on_artifact_not_content():
    """The EDGAR URL is UI-only: it lives on ToolMessage.artifact (forwarded
    as a data-tool-artifact part) and never appears in the model-facing
    content, which the prompt forbids from carrying SEC URLs. Built directly
    from the first result chunk's cik/accession_number/primary_document —
    the new payload denormalizes all three onto every chunk, so this is pure
    string formatting, not a lookup that can go cold or fail."""
    chunk = _make_chunk()
    p1, p2, p3, _ = _patches([chunk])
    with p1, p2, p3:
        msg = await _tool_message({"query": "q", "ticker": "AAPL", "fiscal_year": 2024})

    assert msg.artifact == {"edgar_url": _expected_edgar_url(chunk)}
    assert "sec.gov" not in msg.content


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
    p1, p2, p3, _ = _patches(chunks)
    with p1, p2, p3:
        result = await _tool_call({"query": "q", "ticker": "AAPL", "fiscal_year": 2024})

    flat, nested = result["groups"][0]["chunks"]
    assert "subsection" not in flat
    assert flat["title"] == "AAPL FY2024 10-K · Item 1A"
    assert nested["subsection"] == "Competition"
    assert nested["title"] == "AAPL FY2024 10-K · Item 1A · Competition"


@pytest.mark.asyncio
async def test_evidence_shape_aligns_with_search_result():
    """Each evidence chunk carries source / title / content (Anthropic
    search_result field shape) plus score."""
    chunks = [_make_chunk(text="Competition is intense.", score=0.8123456)]
    p1, p2, p3, _ = _patches(chunks)
    with p1, p2, p3:
        result = await _tool_call({"query": "q", "ticker": "AAPL", "fiscal_year": 2024})

    chunk = result["groups"][0]["chunks"][0]
    assert chunk["content"] == "Competition is intense."
    assert chunk["score"] == pytest.approx(0.8123, abs=1e-4)
    assert set(chunk) >= {"source", "title", "content", "score"}
    assert "n" not in chunk


@pytest.mark.asyncio
async def test_language_directive_sandwich_key_order():
    chunks = [_make_chunk()]
    p1, p2, p3, _ = _patches(chunks)
    with p1, p2, p3:
        result = await _tool_call({"query": "q", "ticker": "AAPL", "fiscal_year": 2024})

    keys = list(result.keys())
    assert keys[0] == "language_directive_pre"
    assert keys[-1] == "language_directive_post"


@pytest.mark.asyncio
async def test_empty_results_return_legible_message():
    p1, p2, p3, _ = _patches([])
    with p1, p2, p3:
        result = await _tool_call({"query": "q", "ticker": "AAPL", "fiscal_year": 2024})

    assert result["groups"] == []
    assert "AAPL" in result["message"]
    assert "2024" in result["message"]


@pytest.mark.asyncio
async def test_retriever_errors_bubble_up():
    """JIT/retrieval errors propagate as raised exceptions (consistent with
    the SEC tools convention); the middleware maps them to legible
    ToolMessages. Uses the new retriever's own CorpusUnavailableError (it no
    longer raises retriever-specific ticker-not-found errors — unknown
    tickers surface as the shared TickerNotFoundError, already covered by
    test_index_lookup_errors_bubble_before_retrieval via locate_filing_ref)."""
    p1, p2, p3, _ = _patches(CorpusUnavailableError("Qdrant resource missing"))
    with p1, p2, p3, pytest.raises(CorpusUnavailableError, match="Qdrant"):
        await _tool_call({"query": "q", "ticker": "AAPL", "fiscal_year": 2024})
