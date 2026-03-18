"""SEC document retrieval tools for FinLab-X."""

import os
import re
from typing import Any, Literal
from pydantic import BaseModel, Field
from langchain.tools import tool

from langfuse import observe


MAX_SECTION_CHARS = 4000


class SecOfficialDocsRetrieverInput(BaseModel):
    """Input schema for SEC document retriever tool."""

    ticker: str = Field(..., description="Stock ticker symbol")
    doc_type: Literal["10-K", "10-Q"] = Field(
        default="10-K", description="SEC filing type: 10-K or 10-Q"
    )


def _extract_section(
    text: str, start_markers: list[str], end_markers: list[str]
) -> str | None:
    """Extract a section from SEC filing text by markers.

    Args:
        text: Full filing text
        start_markers: List of possible section start markers
        end_markers: List of possible section end markers

    Returns:
        Extracted section text or None
    """
    lower_text = text.lower()
    start_index = -1
    for marker in start_markers:
        idx = lower_text.find(marker.lower())
        if idx != -1 and (start_index == -1 or idx < start_index):
            start_index = idx

    if start_index == -1:
        return None

    end_index = -1
    for marker in end_markers:
        idx = lower_text.find(marker.lower(), start_index + 1)
        if idx != -1 and (end_index == -1 or idx < end_index):
            end_index = idx

    extracted = text[start_index : end_index if end_index != -1 else None].strip()
    if len(extracted) > MAX_SECTION_CHARS:
        extracted = extracted[:MAX_SECTION_CHARS].rstrip() + "..."
    return extracted


@tool("sec_official_docs_retriever", args_schema=SecOfficialDocsRetrieverInput)
@observe(name="sec_official_docs_retriever")
def sec_official_docs_retriever(ticker: str, doc_type: str = "10-K") -> dict[str, Any]:
    """Retrieve official SEC filing text sections using edgartools.

    Supports 10-K (annual report) and 10-Q (quarterly report).
    """
    identity = os.getenv("EDGAR_IDENTITY")
    if not identity:
        return {"error": True, "message": "EDGAR_IDENTITY is not set."}

    try:
        from edgar import Company, set_identity

        set_identity(identity)
        normalized_ticker = ticker.strip().upper()
        filings = Company(normalized_ticker).get_filings(form=doc_type)
        filing = filings.latest()
        if not filing:
            return {
                "error": True,
                "message": f"No {doc_type} filing found for {normalized_ticker}.",
            }

        text = getattr(filing, "text")()
        cleaned_text = re.sub(r"\s+", " ", text)
        risk_factors = _extract_section(
            cleaned_text,
            ["Item 1A", "Item 1A."],
            ["Item 1B", "Item 2", "Item 3"],
        )
        mdna = _extract_section(
            cleaned_text,
            ["Item 7", "Item 7."],
            ["Item 7A", "Item 8", "Item 9"],
        )

        return {
            "ticker": normalized_ticker,
            "doc_type": doc_type,
            "filing_date": getattr(filing, "filing_date", None),
            "risk_factors": risk_factors,
            "mdna": mdna,
            "raw_excerpt": cleaned_text[:MAX_SECTION_CHARS].rstrip() + "...",
        }
    except (KeyError, ValueError, ConnectionError, TimeoutError) as exc:
        return {"error": True, "message": f"Could not retrieve SEC filing data: {exc}"}
