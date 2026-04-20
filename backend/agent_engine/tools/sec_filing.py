"""SEC filing pipeline tool for FinLab-X agent (v2+).

Downloads and parses SEC filings via SECFilingPipeline, returning metadata and
the local file path for downstream RAG consumption. Uses the full pipeline
with HTML preprocessing, Markdown conversion, and local caching.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

from langchain.tools import tool
from langfuse import observe
from pydantic import BaseModel, Field

from backend.ingestion.sec_filing_pipeline import SECFilingPipeline

_STORE_BASE_DIR = Path("data/sec_filings")


class SecFilingDownloaderInput(BaseModel):
    """Input schema for SEC filing downloader tool."""

    ticker: str = Field(..., description="Stock ticker symbol (e.g. AAPL)")
    filing_type: Literal["10-K"] = Field(
        default="10-K", description="SEC filing type"
    )
    fiscal_year: int | None = Field(
        default=None, description="Fiscal year (omit for latest)"
    )


def _filing_path(ticker: str, filing_type: str, fiscal_year: int) -> Path:
    return _STORE_BASE_DIR / ticker.upper() / filing_type / f"{fiscal_year}.md"


@tool("sec_filing_downloader", args_schema=SecFilingDownloaderInput)
@observe(name="sec_filing_downloader")
def sec_filing_downloader(
    ticker: str, filing_type: str = "10-K", fiscal_year: int | None = None
) -> dict[str, Any]:
    """Download and parse an SEC filing via the ingestion pipeline.

    Ensures the filing is downloaded, preprocessed, converted to Markdown, and
    cached locally. Returns metadata and the file path for RAG integration.
    """
    try:
        pipeline = SECFilingPipeline.create()
        filing = pipeline.process(ticker, filing_type, fiscal_year)
        m = filing.metadata
        return {
            "ticker": m.ticker,
            "company_name": m.company_name,
            "filing_type": str(m.filing_type),
            "fiscal_year": m.fiscal_year,
            "filing_date": m.filing_date,
            "parsed_at": m.parsed_at,
            "file_path": str(_filing_path(m.ticker, str(m.filing_type), m.fiscal_year)),
        }
    except Exception as exc:
        return {"error": True, "message": f"{type(exc).__name__}: {exc}"}
