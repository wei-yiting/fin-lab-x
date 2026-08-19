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

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

from backend.ingestion.sec_dense_pipeline.vectorizer import (  # noqa: E402
    ingest_filing_with_retry,
    parse_filing_with_retry,
    resolve_latest_fiscal_year_with_retry,
)


async def _embed_one(
    ticker: str,
    fiscal_year: int | None,
    resolved_holder: dict[str, int] | None = None,
) -> int:
    """Ingest one ticker; returns the fiscal year actually ingested so the
    caller can report it — the operator must be able to tell which year was
    picked when --fiscal-year was omitted and latest-year resolution ran.

    ``resolved_holder``, if given, is populated with the resolved fiscal
    year as soon as resolution completes — independent of whether the
    later parse/ingest steps succeed. This lets ``main()``'s failure-path
    summary report the real resolved year instead of falling back to the
    (often ``None``) ``--fiscal-year`` argument when resolution succeeded
    but a later step failed.
    """
    if resolved_holder is None:
        resolved_holder = {}
    resolved_fiscal_year = (
        fiscal_year
        if fiscal_year is not None
        else await asyncio.to_thread(resolve_latest_fiscal_year_with_retry, ticker)
    )
    resolved_holder["fiscal_year"] = resolved_fiscal_year
    filing = await asyncio.to_thread(
        parse_filing_with_retry, ticker, resolved_fiscal_year, False
    )
    await ingest_filing_with_retry(filing)
    return resolved_fiscal_year


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

    results: list[dict] = []

    for ticker in args.tickers:
        ticker_upper = ticker.strip().upper()
        resolved_holder: dict[str, int] = {}
        try:
            resolved_fiscal_year = asyncio.run(
                _embed_one(ticker_upper, args.fiscal_year, resolved_holder)
            )
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
                    # Resolution may have completed before a later parse/
                    # ingest failure — report that real year, not "?"/None.
                    "fiscal_year": resolved_holder.get("fiscal_year", args.fiscal_year),
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
