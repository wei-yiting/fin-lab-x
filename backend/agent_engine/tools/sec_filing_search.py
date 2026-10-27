"""SEC filing dense-retrieval search tool for the FinLab-X agent.

Wraps the sec_dense_pipeline retriever (JIT ingestion, caching, and the
`sec_retrieval` trace span all included) and returns structured evidence
chunks with stable citation IDs, per ADR-0019. Pinpoint questions route
here; synoptic section reading stays on sec_filing_get_section (ADR-0010).

The tool returns ``(content, artifact)``: ``content`` is what the model reads
(evidence chunks + fiscal-year identity); ``artifact`` carries UI-only
metadata (the EDGAR filing URL) that must never enter the model context —
the model is forbidden from writing SEC URLs, so it should not see one.
"""

import asyncio
import logging
import re
from typing import Annotated, Any, NotRequired, TypedDict

import yaml
from langchain.tools import tool
from langchain_core.tools import InjectedToolCallId
from langfuse import observe
from langgraph.config import get_stream_writer
from pydantic import BaseModel, Field, field_validator

from backend.agent_engine.tools.sec_filing_tools import (
    _LANGUAGE_DIRECTIVE_POST,
    _LANGUAGE_DIRECTIVE_PRE,
)
from backend.common.sec_core import (
    TENK_STANDARD_TITLES,
    FilingType,
    locate_filing_ref,
)
from backend.ingestion.sec_dense_pipeline_html.retriever import Chunk, search
from backend.ingestion.sec_filing_pipeline_html.filing_store import LocalFilingStore

logger = logging.getLogger(__name__)

_TOP_K = 10


class EvidenceChunk(TypedDict):
    """One evidence chunk, field shape aligned to Anthropic search_result
    (source / title / content) plus retrieval score. Deliberately carries no
    per-call ordinal: the model numbers its own [N] citations across the
    whole answer, and a tool-side ordinal restarting at 1 on every call was
    a collision magnet. This schema is the API contract the frontend
    citation resolver will consume once DEV-143 lands — keep both sides in
    sync when either changes."""

    source: str
    title: str
    subsection: NotRequired[str]
    content: str
    score: float


class EvidenceGroup(TypedDict):
    ticker: str
    fiscal_year: int
    item: str
    prelude: str
    chunks: list[EvidenceChunk]


# Matches the vectorizer's item format ("Item 1A", "Item 7") and captures the
# number for normalization into the sec_core key space ("1a", "7").
_ITEM_KEY_RE = re.compile(r"^Item\s+(\d{1,2}[A-Za-z]?(?:\(T\))?)$")


class SecFilingSearchInput(BaseModel):
    """Input schema for sec_filing_search tool."""

    query: str = Field(
        ...,
        min_length=1,
        description=(
            "Search query in English describing the specific fact or topic "
            "to locate inside the filing"
        ),
    )
    ticker: str = Field(
        ...,
        min_length=1,
        max_length=10,
        description=(
            "Single stock ticker symbol (e.g. AAPL). One ticker per call — "
            "for cross-company or cross-year comparisons, make one call per "
            "(ticker, fiscal year)"
        ),
    )
    fiscal_year: int | None = Field(
        default=None, ge=1994, description="Fiscal year (omit for latest 10-K)"
    )

    @field_validator("query")
    @classmethod
    def _query_not_blank(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("query must not be blank")
        return stripped

    @field_validator("ticker")
    @classmethod
    def _ticker_not_blank(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("ticker must not be blank")
        return stripped


def _item_key(item: str) -> str:
    """Normalize the vectorizer's item label ("Item 1A") to the sec_core key
    space ("1a"). The vectorizer's `_unknown` sentinel maps to "unknown"."""
    match = _ITEM_KEY_RE.match(item.strip())
    if match:
        return match.group(1).lower()
    return "unknown"


def _citation_id(chunk: Chunk, fallback_accession_number: str) -> str:
    # Chunk's own accession number wins when present; fallback_accession_number
    # (already resolved and always valid by the time this runs) covers
    # older/legacy-ingested chunks missing their own.
    filing_key = chunk.accession_number or fallback_accession_number
    return f"sec://{filing_key}/{_item_key(chunk.item)}#{chunk.chunk_index}"


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
    no cik/source_url (schema owned by the SEC ingestion rewrite), so this is
    resolved out-of-band; a cold store degrades to None rather than a
    fabricated URL.
    """
    try:
        filing = LocalFilingStore().get(ticker, FilingType.TEN_K, fiscal_year)
    except (OSError, ValueError, yaml.YAMLError, TypeError) as exc:
        logger.warning(
            "Failed to read filing-store metadata for %s FY%s: %s",
            ticker,
            fiscal_year,
            exc,
        )
        return None
    if filing is None:
        return None
    return filing.metadata.source_url


def _build_groups(chunks: list[Chunk], accession_number: str) -> list[EvidenceGroup]:
    """Group chunks by (ticker, year, item); groups ordered most-relevant
    first (max score), chunks within a group in document order (chunk_index).

    ``accession_number`` is the authoritative accession number for this
    filing, already resolved by ``locate_filing_ref`` before retrieval ran.
    It is threaded into each chunk's citation ID as the fallback for chunks
    whose own ``accession_number`` is missing (older/legacy-ingested data).
    """
    grouped: dict[tuple[str, int, str], list[Chunk]] = {}
    for chunk in chunks:
        grouped.setdefault((chunk.ticker, chunk.year, chunk.item), []).append(chunk)

    ordered_keys = sorted(
        grouped, key=lambda key: max(c.score for c in grouped[key]), reverse=True
    )

    groups: list[EvidenceGroup] = []
    for key in ordered_keys:
        ticker, year, item = key
        members = sorted(grouped[key], key=lambda c: c.chunk_index)
        out_chunks: list[EvidenceChunk] = []
        for chunk in members:
            entry: EvidenceChunk = {
                "source": _citation_id(chunk, accession_number),
                "title": _chunk_title(chunk),
                "content": chunk.text,
                "score": round(chunk.score, 4),
            }
            subsection = _subsection(chunk)
            if subsection:
                entry["subsection"] = subsection
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
                "chunks": out_chunks,
            }
        )
    return groups


@tool(
    "sec_filing_search",
    args_schema=SecFilingSearchInput,
    response_format="content_and_artifact",
)
@observe(name="sec_filing_search")
async def sec_filing_search(
    query: str,
    ticker: str,
    fiscal_year: int | None = None,
    tool_call_id: Annotated[str, InjectedToolCallId] = "",
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Semantic search over a company's 10-K filing for pinpoint questions.

    Returns evidence chunks grouped by (ticker, year, item), each with a
    stable citation ID (`source`), locator title, content, and score, plus
    the filing's fiscal year and fiscal-year end date. Retrieval errors
    (unknown ticker, missing filing, corpus unavailable) bubble up as
    exceptions with legible messages.
    """
    ticker_upper = ticker.strip().upper()

    # Index-only lookup (cached per ticker/year): names the filing the
    # evidence comes from — FY, FY end date — and turns "no such 10-K year"
    # into a legible error instead of an empty Qdrant result.
    filing_ref = await asyncio.to_thread(
        locate_filing_ref, ticker_upper, FilingType.TEN_K, fiscal_year
    )
    resolved_fy = filing_ref.fiscal_year
    fiscal_year_source = "latest" if fiscal_year is None else "requested"

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
        "fiscal_year_end": filing_ref.period_of_report,
        "fiscal_year_source": fiscal_year_source,
        "total_chunks": len(chunks),
    }

    edgar_url: str | None = None
    if chunks:
        edgar_url = await asyncio.to_thread(
            _edgar_filing_url, ticker_upper, resolved_fy
        )
        out["groups"] = _build_groups(chunks, filing_ref.accession_number)
    else:
        out["groups"] = []
        out["message"] = (
            f"No indexed passages matched this query for {ticker_upper} "
            f"FY{resolved_fy}. The filing may not cover this topic — consider "
            "sec_filing_list_sections + sec_filing_get_section to read a "
            "full section instead."
        )

    out["language_directive_post"] = _LANGUAGE_DIRECTIVE_POST
    # UI-only metadata rides on ToolMessage.artifact (forwarded to the
    # frontend as a data-tool-artifact part), never in the model's context.
    return out, {"edgar_url": edgar_url}
