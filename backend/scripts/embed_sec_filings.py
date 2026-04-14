#!/usr/bin/env python
"""Batch ingest SEC filings into the dense vector pipeline.

Usage: python -m backend.scripts.embed_sec_filings NVDA AAPL INTC
"""

import argparse
import asyncio
import sys
import time
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

from backend.ingestion.sec_filing_pipeline.filing_models import FilingType
from backend.ingestion.sec_filing_pipeline.filing_store import LocalFilingStore
from backend.ingestion.sec_dense_pipeline.vectorizer import ingest_filing


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Batch ingest SEC filings")
    parser.add_argument("tickers", nargs="+", help="Ticker symbols to ingest")
    parser.add_argument("--max-retries", type=int, default=3, help="Max retry attempts per ticker")
    args = parser.parse_args(argv)

    store = LocalFilingStore()
    results: list[dict] = []

    for ticker in args.tickers:
        ticker_upper = ticker.strip().upper()
        status = "success"
        error_msg = None

        try:
            years = store.list_filings(ticker_upper, FilingType.TEN_K)
            if not years:
                status = "skipped"
                error_msg = "No filings found"
                results.append({"ticker": ticker_upper, "status": status, "error": error_msg})
                continue

            year = max(years)
            filing = store.get(ticker_upper, FilingType.TEN_K, year)
            if filing is None:
                status = "skipped"
                error_msg = f"Filing not found for year {year}"
                results.append({"ticker": ticker_upper, "status": status, "error": error_msg})
                continue

            last_error = None
            for attempt in range(args.max_retries):
                try:
                    asyncio.run(ingest_filing(
                        ticker=ticker_upper,
                        year=year,
                        markdown=filing.markdown_content,
                        filing_metadata=filing.metadata,
                    ))
                    last_error = None
                    break
                except Exception as e:
                    last_error = e
                    if attempt < args.max_retries - 1:
                        wait = 2 ** attempt  # 1s, 2s, 4s
                        time.sleep(wait)

            if last_error is not None:
                status = "skipped"
                error_msg = str(last_error)

        except Exception as e:
            status = "skipped"
            error_msg = str(e)

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
