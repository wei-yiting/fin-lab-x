"""SEC filing dense-retrieval search tool for the FinLab-X agent.

Wraps the sec_dense_pipeline retriever (JIT ingestion, caching, and the
`sec_retrieval` trace span all included) and returns structured evidence
chunks with stable citation IDs, per ADR-0008. Pinpoint questions route
here; synoptic section reading stays on sec_filing_get_section (ADR-0010).
"""

import asyncio
import re
from typing import Annotated, Any

from langchain.tools import tool
from langchain_core.tools import InjectedToolCallId
from langfuse import observe
from langgraph.config import get_stream_writer
from pydantic import BaseModel, Field

from backend.agent_engine.tools.sec_filing_tools import (
    _LANGUAGE_DIRECTIVE_POST,
    _LANGUAGE_DIRECTIVE_PRE,
)
from backend.common.sec_core import (
    TENK_STANDARD_TITLES,
    FilingType,
    _resolve_latest_fiscal_year,
)
from backend.ingestion.sec_dense_pipeline.retriever import Chunk, search
from backend.ingestion.sec_filing_pipeline.filing_store import LocalFilingStore

_TOP_K = 10

# Matches the vectorizer's item format ("Item 1A", "Item 7") and captures the
# number for normalization into the sec_core key space ("1a", "7").
_ITEM_KEY_RE = re.compile(r"^Item\s+(\d{1,2}[A-Za-z]?(?:\(T\))?)$")


class SecFilingSearchInput(BaseModel):
    """Input schema for sec_filing_search tool."""

    query: str = Field(
        ...,
        description=(
            "Search query in English describing the specific fact or topic "
            "to locate inside the filing"
        ),
    )
    ticker: str = Field(
        ...,
        description=(
            "Single stock ticker symbol (e.g. AAPL). One ticker per call — "
            "for cross-company or cross-year comparisons, make one call per "
            "(ticker, fiscal year)"
        ),
    )
    fiscal_year: int | None = Field(
        default=None, description="Fiscal year (omit for latest 10-K)"
    )


def _item_key(item: str) -> str:
    """Normalize the vectorizer's item label ("Item 1A") to the sec_core key
    space ("1a"). The vectorizer's `_unknown` sentinel maps to "unknown"."""
    match = _ITEM_KEY_RE.match(item.strip())
    if match:
        return match.group(1).lower()
    return "unknown"


def _filing_key(chunk: Chunk) -> str:
    """Filing identifier for the stable citation ID. Prefers the accession
    number; legacy ingests without filing metadata degrade to a ticker-year
    key so IDs stay unique across filings."""
    return chunk.accession_number or f"{chunk.ticker}-FY{chunk.year}"


def _citation_id(chunk: Chunk) -> str:
    return f"sec://{_filing_key(chunk)}/{_item_key(chunk.item)}#{chunk.chunk_index}"


def _subsection(chunk: Chunk) -> str | None:
    """Sub-item locator: the header_path segments below the Item level.

    header_path format is "{TICKER} / {year} / Item 1A. Risk Factors / ...".
    A flat item (no sub-headings) has nothing below the Item segment — the
    locator honestly degrades to Item level (None), never fabricated.
    """
    segments = [s.strip() for s in chunk.header_path.split(" / ")]
    for i, segment in enumerate(segments):
        if segment.lower().startswith("item "):
            tail = segments[i + 1 :]
            return " / ".join(tail) if tail else None
    return None


def _item_display(item: str) -> str:
    key = _item_key(item)
    title = TENK_STANDARD_TITLES.get(key)
    if title:
        return f"{item} ({title})"
    return item


def _chunk_title(chunk: Chunk) -> str:
    parts = [f"{chunk.ticker} FY{chunk.year} 10-K"]
    if chunk.item != "_unknown":
        parts.append(chunk.item)
    subsection = _subsection(chunk)
    if subsection:
        parts.append(subsection)
    return " · ".join(parts)


def _edgar_filing_url(ticker: str, fiscal_year: int) -> str | None:
    """EDGAR direct link to the 10-K primary document, from the filing store's
    persisted metadata (written by JIT ingestion). The chunk payload carries
    no cik/source_url (schema owned by DEV-65/DEV-127), so this is resolved
    out-of-band; a cold store degrades to None rather than a fabricated URL.
    """
    try:
        filing = LocalFilingStore().get(ticker, FilingType.TEN_K, fiscal_year)
    except (OSError, ValueError):
        return None
    if filing is None:
        return None
    return filing.metadata.source_url


def _build_groups(chunks: list[Chunk], edgar_url: str | None) -> list[dict[str, Any]]:
    """Group chunks by (ticker, year, item); groups ordered most-relevant
    first (max score), chunks within a group in document order (chunk_index).
    Citation numbers are sequential across the whole result."""
    grouped: dict[tuple[str, int, str], list[Chunk]] = {}
    for chunk in chunks:
        grouped.setdefault((chunk.ticker, chunk.year, chunk.item), []).append(chunk)

    ordered_keys = sorted(
        grouped, key=lambda key: max(c.score for c in grouped[key]), reverse=True
    )

    groups: list[dict[str, Any]] = []
    number = 0
    for key in ordered_keys:
        ticker, year, item = key
        members = sorted(grouped[key], key=lambda c: c.chunk_index)
        out_chunks: list[dict[str, Any]] = []
        for chunk in members:
            number += 1
            entry: dict[str, Any] = {
                "n": number,
                "source": _citation_id(chunk),
                "title": _chunk_title(chunk),
            }
            subsection = _subsection(chunk)
            if subsection:
                entry["subsection"] = subsection
            entry["content"] = chunk.text
            entry["score"] = round(chunk.score, 4)
            out_chunks.append(entry)
        groups.append(
            {
                "ticker": ticker,
                "fiscal_year": year,
                "item": item,
                "prelude": (
                    f"Excerpts from {ticker} FY{year} 10-K, "
                    f"{_item_display(item)} — {len(members)} passage(s) "
                    "in document order."
                ),
                "edgar_url": edgar_url,
                "chunks": out_chunks,
            }
        )
    return groups


@tool("sec_filing_search", args_schema=SecFilingSearchInput)
@observe(name="sec_filing_search")
async def sec_filing_search(
    query: str,
    ticker: str,
    fiscal_year: int | None = None,
    tool_call_id: Annotated[str, InjectedToolCallId] = "",
) -> dict[str, Any]:
    """Semantic search over a company's 10-K filing for pinpoint questions.

    Returns numbered evidence chunks grouped by (ticker, year, item), each
    with a stable citation ID (`source`), locator title, content, and score.
    Retrieval errors (unknown ticker, missing filing, corpus unavailable)
    bubble up as exceptions with legible messages.
    """
    ticker_upper = ticker.strip().upper()

    if fiscal_year is None:
        resolved_fy = await asyncio.to_thread(_resolve_latest_fiscal_year, ticker_upper)
        fiscal_year_source = "latest"
    else:
        resolved_fy = fiscal_year
        fiscal_year_source = "requested"

    try:
        writer = get_stream_writer()
    except Exception:
        writer = None

    if writer:
        writer(
            {
                "status": "searching_filing",
                "message": (
                    f"Searching {ticker_upper} FY{resolved_fy} 10-K "
                    f"(fetching and indexing first if not cached)..."
                ),
                "toolName": "sec_filing_search",
                "toolCallId": tool_call_id,
            }
        )

    chunks = await search(
        query=query,
        filters={"ticker": ticker_upper, "year": resolved_fy},
        top_k=_TOP_K,
    )

    out: dict[str, Any] = {
        # First key: pre-content language directive (same sandwich contract
        # as sec_filing_get_section — key insertion order is the mechanism).
        "language_directive_pre": _LANGUAGE_DIRECTIVE_PRE,
        "fiscal_year": resolved_fy,
        "fiscal_year_source": fiscal_year_source,
        "total_chunks": len(chunks),
    }

    if chunks:
        edgar_url = await asyncio.to_thread(
            _edgar_filing_url, ticker_upper, resolved_fy
        )
        out["groups"] = _build_groups(chunks, edgar_url)
    else:
        out["groups"] = []
        out["message"] = (
            f"No indexed passages matched this query for {ticker_upper} "
            f"FY{resolved_fy}. The filing may not cover this topic — consider "
            "sec_filing_list_sections + sec_filing_get_section to read a "
            "full section instead."
        )

    out["language_directive_post"] = _LANGUAGE_DIRECTIVE_POST
    return out
