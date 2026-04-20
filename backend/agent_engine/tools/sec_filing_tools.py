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
    _resolve_latest_fiscal_year,
    fetch_filing_obj,
    is_stub_section,
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
    """Extract a normalized item number from a section name string."""
    lowered = name.strip().lower()
    m = re.search(r"item[_ ]+([0-9]{1,2}[a-c]?)\b", lowered)
    if m:
        return m.group(1)
    return None


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
    for name, section in tenk.document.sections.items():
        item = section.item or _derive_item_from_name(name)
        if item is None:
            continue
        normalized = item.lower()
        if normalized in TENK_STANDARD_TITLES:
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
        "company_name": getattr(tenk.company, "name", None) or str(tenk.company),
        "sections": out_sections,
    }
