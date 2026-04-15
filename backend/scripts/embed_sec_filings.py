#!/usr/bin/env python
"""Batch ingest SEC filings into the dense vector pipeline.

Examples:
    python -m backend.scripts.embed_sec_filings NVDA AAPL INTC
    python -m backend.scripts.embed_sec_filings NVDA --year 2024
    python -m backend.scripts.embed_sec_filings NVDA AAPL --max-retries 5

For each ticker, fetches the requested fiscal year (or EDGAR's latest if --year is
omitted) via SECFilingPipeline.process — which downloads + parses the filing if
not already cached locally — then embeds the markdown into Qdrant via
ingest_filing.

This script intentionally runs without Langfuse tracing.
"""

import argparse
import asyncio
import sys
import time
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

from backend.ingestion.sec_dense_pipeline.vectorizer import ingest_filing  # noqa: E402
from backend.ingestion.sec_filing_pipeline.pipeline import SECFilingPipeline  # noqa: E402


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
    parser = argparse.ArgumentParser(description="Batch ingest SEC filings")
    parser.add_argument("tickers", nargs="+", help="Ticker symbols to ingest")
    parser.add_argument(
        "--year",
        type=int,
        default=None,
        help="Fiscal year to ingest (default: EDGAR's latest)",
    )
    parser.add_argument(
        "--max-retries",
        type=int,
        default=3,
        help="Max retry attempts per ticker (default: 3)",
    )
    args = parser.parse_args(argv)

    pipeline = SECFilingPipeline.create()
    results: list[dict] = []

    for ticker in args.tickers:
        ticker_upper = ticker.strip().upper()
        status = "success"
        error_msg = None

        last_error: Exception | None = None
        for attempt in range(args.max_retries):
            try:
                asyncio.run(_embed_one(pipeline, ticker_upper, args.year))
                last_error = None
                break
            except Exception as exc:
                last_error = exc
                if attempt < args.max_retries - 1:
                    time.sleep(2**attempt)  # 1s, 2s, 4s

        if last_error is not None:
            status = "skipped"
            error_msg = str(last_error)

        results.append({"ticker": ticker_upper, "status": status, "error": error_msg})

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
