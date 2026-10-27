#!/usr/bin/env python
"""Batch ingest the Ticker universe from yfinance into the fundamentals DuckDB store.

Examples:
    python -m backend.scripts.ingest_yfinance_fundamentals
    python -m backend.scripts.ingest_yfinance_fundamentals NVDA INTC --db-path /tmp/f.db

Runs tickers sequentially (DuckDB is single-writer). A ticker that fails is recorded
in ``ingestion_runs`` and the batch moves on; rerunning is safe because every write is
an upsert. Run it from a developer machine: yfinance rate-limits cloud IPs.
"""

import argparse
import sys
from datetime import date

from backend.ingestion.fundamentals_pipeline.duck_db.connection import get_connection
from backend.ingestion.fundamentals_pipeline.ticker_universe_loader import (
    load_ticker_universe,
)
from backend.ingestion.fundamentals_pipeline.yfinance_fetcher import (
    ingest_ticker,
    open_ticker,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("tickers", nargs="*", help="Default: the Ticker universe")
    parser.add_argument("--db-path", default=None, help="Default: $DUCKDB_PATH")
    args = parser.parse_args(argv)

    tickers = [t.upper() for t in args.tickers] or load_ticker_universe()
    as_of = date.today()
    failures: list[tuple[str, str]] = []

    with get_connection(args.db_path) as conn:
        for ticker in tickers:
            try:
                written = ingest_ticker(conn, ticker, open_ticker(ticker), as_of)
            # Batch boundary: yfinance surfaces network, parsing and rate-limit
            # failures as unrelated exception types; the audit row keeps the class.
            except Exception as exc:  # noqa: BLE001
                failures.append((ticker, f"{type(exc).__name__}: {exc}"))
                print(f"✗ {ticker:6} {type(exc).__name__}: {exc}")
                continue
            print(f"✓ {ticker:6} {written}")

    print(f"\n{len(tickers) - len(failures)}/{len(tickers)} tickers ingested")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
