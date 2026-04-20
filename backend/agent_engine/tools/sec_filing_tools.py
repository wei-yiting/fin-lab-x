"""SEC filing structured access tools for FinLab-X agent (v2+).

Provides section-level access to SEC 10-K filings backed by edgartools,
with canonical ordering, stub detection, and fiscal year resolution.
"""

import re
from typing import Annotated, Any, Literal

from langchain.tools import tool
from langchain_core.tools import InjectedToolCallId
from langfuse import observe
from langgraph.config import get_stream_writer
from pydantic import BaseModel, Field

from backend.common.sec_core import (
    TENK_STANDARD_TITLES,
    FilingType,
    SectionNotFoundError,
    _resolve_latest_fiscal_year,
    fetch_filing_obj,
    is_stub_section,
    parse_item_number,
)


class SecFilingListSectionsInput(BaseModel):
    """Input schema for sec_filing_list_sections tool."""

    ticker: str = Field(..., description="Stock ticker symbol (e.g. AAPL)")
    doc_type: Literal["10-K"] = Field(
        default="10-K", description="SEC filing type; only 10-K supported"
    )
    fiscal_year: int | None = Field(
        default=None, description="Fiscal year (omit for latest filing)"
    )


def _derive_item_from_name(name: str) -> str | None:
    """Extract a normalized item number from an edgartools section name.

    Distinct from `parse_item_number` (sec_core): that one normalizes
    agent-provided keys like "Item 1a" with strict ^[0-9]{1,2}[a-c]?$
    validation and raises on invalid input. This one searches inside
    edgartools' internal naming convention (e.g. "part_i_item_1a",
    "part_ii_item_7a") where the item number is a substring, not the
    whole string. Returns None on no match — non-item sections (TOC,
    signatures, etc.) are silently skipped.
    """
    lowered = name.strip().lower()
    m = re.search(r"item[_ ]+([0-9]{1,2}[a-c]?)\b", lowered)
    if m:
        return m.group(1)
    return None


def _iter_resolved_sections(tenk: Any):
    """Yield `(normalized_item_key, section)` for each section in the filing
    that resolves to a known TENK_STANDARD_TITLES key.

    Single source of truth for the resolution rule shared by both
    list_sections and get_section: prefer `Section.item` (lower-cased),
    else fall back to `_derive_item_from_name(name)`. Sections that
    don't resolve to a standard item are skipped silently.
    """
    for name, section in tenk.document.sections.items():
        item = (section.item or "").lower() or _derive_item_from_name(name)
        if item is None or item not in TENK_STANDARD_TITLES:
            continue
        yield item, section


@tool("sec_filing_list_sections", args_schema=SecFilingListSectionsInput)
@observe(name="sec_filing_list_sections")
def sec_filing_list_sections(
    ticker: str,
    doc_type: str = "10-K",
    fiscal_year: int | None = None,
    tool_call_id: Annotated[str, InjectedToolCallId] = "",
) -> dict[str, Any]:
    """List all available 10-K sections with char_count and stub detection.

    Returns sections in SEC canonical order. Stub sections include is_stub
    and stub_reason; non-stub sections omit those keys entirely.
    """
    ticker_upper = ticker.strip().upper()

    if fiscal_year is None:
        resolved_fy = _resolve_latest_fiscal_year(ticker_upper)
    else:
        resolved_fy = fiscal_year

    try:
        writer = get_stream_writer()
    except Exception:
        writer = None

    if writer:
        writer({
            "status": "listing_sections",
            "message": f"Listing {doc_type} sections for {ticker_upper} FY{resolved_fy}...",
            "toolName": "sec_filing_list_sections",
            "toolCallId": tool_call_id,
        })

    tenk = fetch_filing_obj(ticker_upper, FilingType(doc_type), resolved_fy)
    period_of_report = tenk.period_of_report

    key_to_section: dict[str, Any] = {}
    for normalized, section in _iter_resolved_sections(tenk):
        key_to_section.setdefault(normalized, section)

    out_sections: list[dict[str, Any]] = []
    for key in TENK_STANDARD_TITLES:
        section = key_to_section.get(key)
        if section is None:
            continue
        text = section.text()
        entry: dict[str, Any] = {"key": key, "char_count": len(text)}
        is_stub, stub_reason = is_stub_section(text)
        if is_stub:
            entry["is_stub"] = True
            entry["stub_reason"] = stub_reason
        out_sections.append(entry)

    return {
        "ticker": ticker_upper,
        "doc_type": doc_type,
        "fiscal_year": resolved_fy,
        "period_of_report": period_of_report,
        "filing_date": str(tenk.filing_date) if tenk.filing_date else None,
        # edgartools returns `tenk.company` as a plain str in production,
        # but our mocks set `.name` on a MagicMock — handle both shapes.
        "company_name": getattr(tenk.company, "name", None) or str(tenk.company),
        "sections": out_sections,
    }


class SecFilingGetSectionInput(BaseModel):
    """Input schema for sec_filing_get_section tool."""

    ticker: str = Field(..., description="Stock ticker symbol (e.g. AAPL)")
    doc_type: Literal["10-K"] = Field(
        default="10-K", description="SEC filing type; only 10-K supported"
    )
    section_key: str = Field(
        ..., description="Normalized item number such as '1', '1a', '7', '7a'"
    )
    fiscal_year: int | None = Field(
        default=None, description="Fiscal year (omit for latest filing)"
    )


def _locate_section(tenk: Any, normalized: str) -> Any | None:
    """Find the Section whose resolved item key matches `normalized`.

    Uses `_iter_resolved_sections` so the resolution rule is identical to
    `sec_filing_list_sections` — guarantees that any key reported by
    list_sections can be retrieved by get_section.
    """
    for item, section in _iter_resolved_sections(tenk):
        if item == normalized:
            return section
    return None


@tool("sec_filing_get_section", args_schema=SecFilingGetSectionInput)
@observe(name="sec_filing_get_section")
def sec_filing_get_section(
    ticker: str,
    section_key: str,
    doc_type: str = "10-K",
    fiscal_year: int | None = None,
    tool_call_id: Annotated[str, InjectedToolCallId] = "",
) -> dict[str, Any]:
    """Return the full plaintext of a single 10-K section.

    Resolves section_key (e.g. "1a", "Item 7") against the SEC standard item
    map, fetches the filing, locates the matching section, and returns the
    section text plus the filing's period_of_report. Stub sections include
    is_stub and stub_reason; non-stub responses omit those keys entirely.
    The input arguments (ticker / doc_type / fiscal_year / section_key) are
    intentionally NOT echoed back — the agent already has them.
    """
    normalized = parse_item_number(section_key)
    title = TENK_STANDARD_TITLES[normalized]

    ticker_upper = ticker.strip().upper()

    if fiscal_year is None:
        resolved_fy = _resolve_latest_fiscal_year(ticker_upper)
    else:
        resolved_fy = fiscal_year

    tenk = fetch_filing_obj(ticker_upper, FilingType(doc_type), resolved_fy)
    period_of_report = tenk.period_of_report
    # fetch_filing_obj's _find_by_fiscal_year guarantees
    # period_of_report[:4] == resolved_fy, so no re-derive needed.

    section = _locate_section(tenk, normalized)
    if section is None:
        if normalized == "1c" and resolved_fy < 2023:
            raise SectionNotFoundError(
                f"Section '1c' (Cybersecurity) was added by SEC in 2023 and is not "
                f"present in FY{resolved_fy}."
            )
        raise SectionNotFoundError(
            f"Section {section_key!r} not found in {ticker_upper} 10-K FY{resolved_fy}. "
            "Call sec_filing_list_sections first to see available section keys."
        )

    try:
        writer = get_stream_writer()
    except Exception:
        writer = None

    if writer:
        writer({
            "status": "fetching_section",
            "message": (
                f"Fetching Item {normalized.upper()}. {title} for "
                f"{ticker_upper} FY{resolved_fy}..."
            ),
            "toolName": "sec_filing_get_section",
            "toolCallId": tool_call_id,
        })

    content = section.text()
    is_stub, stub_reason = is_stub_section(content)

    out: dict[str, Any] = {
        "period_of_report": period_of_report,
        "content": content,
    }
    if is_stub:
        out["is_stub"] = True
        out["stub_reason"] = stub_reason
    return out
