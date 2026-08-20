#!/usr/bin/env python
"""Batch ingest SEC filings into the frozen dense vector pipeline (_html baseline).

Examples:
    python -m backend.scripts.embed_sec_filings_html NVDA AAPL INTC
    python -m backend.scripts.embed_sec_filings_html NVDA --year 2024

For each ticker, fetches the requested fiscal year (or EDGAR's latest if
--year is omitted) via SECFilingPipeline.process — which downloads + parses
the filing if not already cached locally, retrying transient failures
internally — then embeds the markdown into Qdrant via
sec_dense_pipeline_html.vectorizer.ingest_filing. A failure on one ticker
does not retry further (SECFilingPipeline.process already exhausted its own
retry budget for transient errors) and does not abort the rest of the batch.

Operator backfill path for the frozen sec_dense_pipeline_html collection
(see backend/ingestion/sec_dense_pipeline_html/README.md): the
structured-contract batch script (embed_sec_filings.py) exclusively targets
the new sec_dense_pipeline collection, so this script is what is left to
pre-load tickers into the old collection — e.g. for an A/B eval backfill or
a new eval dataset that needs tickers not yet present there.

This mirrors the repo's established _html sunset convention: this whole
file is deleted together with the rest of the frozen pipeline at sunset,
rather than the batch-ingest logic being surgically kept alive inside a
shared script (see AGENTS.md "Ingestion Rewrite Coexistence").

This script intentionally runs without Langfuse tracing.
"""

import argparse
import asyncio
import sys
from pathlib import Path
from typing import Literal, TypedDict

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

from backend.ingestion.sec_dense_pipeline_html.vectorizer import (  # noqa: E402
    ingest_filing,
)
from backend.ingestion.sec_filing_pipeline_html.pipeline import (  # noqa: E402
    SECFilingPipeline,
)


class BatchIngestResult(TypedDict):
    """One row of the batch-ingest summary table."""

    ticker: str
    status: Literal["success", "failed"]
    error: str | None


async def _embed_one(
    pipeline: SECFilingPipeline,
    ticker: str,
    year: int | None,
) -> None:
    filing = await asyncio.to_thread(pipeline.process, ticker, "10-K", year)
    await ingest_filing(
        ticker=ticker,
        year=filing.metadata.fiscal_year,
        markdown=filing.markdown_content,
        filing_metadata=filing.metadata,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Batch ingest SEC filings into the frozen _html pipeline"
    )
    parser.add_argument("tickers", nargs="+", help="Ticker symbols to ingest")
    parser.add_argument(
        "--year",
        type=int,
        default=None,
        help="Fiscal year to ingest (default: EDGAR's latest)",
    )
    args = parser.parse_args(argv)

    pipeline = SECFilingPipeline.create()
    results: list[BatchIngestResult] = []

    for ticker in args.tickers:
        ticker_upper = ticker.strip().upper()
        try:
            asyncio.run(_embed_one(pipeline, ticker_upper, args.year))
            results.append({"ticker": ticker_upper, "status": "success", "error": None})
        except Exception as exc:
            results.append(
                {"ticker": ticker_upper, "status": "failed", "error": str(exc)}
            )

    print("\n--- Batch Ingest Summary ---")
    print(f"{'Ticker':<10} {'Status':<10} {'Error'}")
    print("-" * 40)
    for r in results:
        error_str = r["error"] or ""
        print(f"{r['ticker']:<10} {r['status']:<10} {error_str}")

    has_failures = any(r["status"] != "success" for r in results)
    return 1 if has_failures else 0


if __name__ == "__main__":
    sys.exit(main())
