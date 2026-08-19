#!/usr/bin/env python
"""Batch ingest SEC filings into the dense vector pipeline (new contract).

Examples:
    python -m backend.scripts.embed_sec_filings NVDA AAPL INTC
    python -m backend.scripts.embed_sec_filings NVDA --fiscal-year 2024

For each ticker, fetches and parses the requested fiscal year (or the
ticker's latest 10-K if --fiscal-year is omitted) via parse_filing_with_retry
— filing-store cache first, EDGAR on miss — then embeds it into Qdrant via
ingest_filing_with_retry. Both steps carry a single retry on transient
failures (ADR-0013); a failure that survives the retry does not abort the
rest of the batch — it is recorded and the script moves to the next ticker.

This script intentionally runs without Braintrust tracing.
"""

import argparse
import asyncio
import sys
from pathlib import Path
from typing import Literal, TypedDict

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

from backend.ingestion.sec_dense_pipeline.vectorizer import (  # noqa: E402
    ingest_filing_with_retry,
    parse_filing_with_retry,
    resolve_latest_fiscal_year_with_retry,
)


class BatchIngestResult(TypedDict):
    """One row of the batch-ingest summary table."""

    ticker: str
    fiscal_year: int | None
    status: Literal["success", "failed"]
    error: str | None


async def _parse_and_ingest(ticker: str, fiscal_year: int) -> None:
    """Parse and ingest one ticker's already-resolved fiscal year.

    Takes a concrete ``fiscal_year`` — latest-year resolution happens
    earlier, in ``main()``'s per-ticker loop, so the caller already has the
    real year in hand before this can fail; this function has no partial
    progress of its own to report back.
    """
    filing = await asyncio.to_thread(
        parse_filing_with_retry, ticker, fiscal_year, False
    )
    await ingest_filing_with_retry(filing)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Batch ingest SEC filings")
    parser.add_argument("tickers", nargs="+", help="Ticker symbols to ingest")
    parser.add_argument(
        "--fiscal-year",
        type=int,
        default=None,
        dest="fiscal_year",
        help="Fiscal year to ingest (default: ticker's latest 10-K)",
    )
    args = parser.parse_args(argv)

    results: list[BatchIngestResult] = []

    for ticker in args.tickers:
        ticker_upper = ticker.strip().upper()
        # Resolved eagerly, before the parse/ingest call: if a later step
        # fails, this local variable still holds the real resolved year
        # (not the often-None --fiscal-year argument) for the summary below.
        resolved_fiscal_year: int | None = args.fiscal_year
        try:
            if resolved_fiscal_year is None:
                resolved_fiscal_year = resolve_latest_fiscal_year_with_retry(
                    ticker_upper
                )
            asyncio.run(_parse_and_ingest(ticker_upper, resolved_fiscal_year))
            results.append(
                {
                    "ticker": ticker_upper,
                    "fiscal_year": resolved_fiscal_year,
                    "status": "success",
                    "error": None,
                }
            )
        except Exception as exc:
            results.append(
                {
                    "ticker": ticker_upper,
                    "fiscal_year": resolved_fiscal_year,
                    "status": "failed",
                    "error": str(exc),
                }
            )

    print("\n--- Batch Ingest Summary ---")
    print(f"{'Ticker':<10} {'Fiscal Year':<12} {'Status':<10} {'Error'}")
    print("-" * 60)
    for r in results:
        fiscal_year_str = str(r["fiscal_year"]) if r["fiscal_year"] is not None else "?"
        error_str = r["error"] or ""
        print(f"{r['ticker']:<10} {fiscal_year_str:<12} {r['status']:<10} {error_str}")

    has_failures = any(r["status"] != "success" for r in results)
    return 1 if has_failures else 0


if __name__ == "__main__":
    sys.exit(main())
