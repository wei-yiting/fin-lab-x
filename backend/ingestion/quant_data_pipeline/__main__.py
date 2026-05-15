"""CLI entrypoint for the quant data pipeline.

Subcommands:
  refresh-yfinance [TICKER...]  Run yfinance refresh against the universe
                                 (default) or specific tickers (overrides).
                                 Exit 0 if at least one ticker succeeded;
                                 non-zero if all tickers failed.

Per-ticker failures are isolated: a ``QuantPipelineError`` raised by
``refresh_yfinance_ticker`` is logged and the for-loop continues to the next
ticker. The audit row for the failure is written inside
``track_ingestion_run`` (the ``__exit__`` path), so the CLI never re-records
it.
"""

import argparse
import logging
import sys
from collections.abc import Sequence
from pathlib import Path

from backend.ingestion.quant_data_pipeline.duck_db.connection import get_connection
from backend.ingestion.quant_data_pipeline.quant_pipeline_errors import (
    QuantPipelineError,
)
from backend.ingestion.quant_data_pipeline.ticker_universe_loader import (
    load_ticker_universe,
)
from backend.ingestion.quant_data_pipeline.yfinance import refresh_yfinance_ticker

logger = logging.getLogger(__name__)


def _refresh_yfinance(args: argparse.Namespace) -> int:
    tickers: list[str] = (
        args.tickers if args.tickers else load_ticker_universe(args.universe_path)
    )
    conn = get_connection(args.db_path)
    success_count = 0
    error_count = 0
    try:
        for ticker in tickers:
            try:
                refresh_yfinance_ticker(conn, ticker)
                success_count += 1
            except QuantPipelineError as exc:
                logger.warning(
                    "yfinance refresh failed for %s: %s: %s",
                    ticker,
                    type(exc).__name__,
                    exc,
                )
                error_count += 1
                continue
    finally:
        conn.close()
    logger.info(
        "yfinance batch finished: %d succeeded, %d failed",
        success_count,
        error_count,
    )
    return 0 if success_count > 0 else 1


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="quant_data_pipeline")
    subparsers = parser.add_subparsers(dest="subcommand", required=True)

    yf_parser = subparsers.add_parser(
        "refresh-yfinance",
        help="Run yfinance refresh against the configured ticker universe",
    )
    yf_parser.add_argument(
        "tickers",
        nargs="*",
        help="Optional explicit tickers (overrides universe)",
    )
    yf_parser.add_argument(
        "--db-path",
        default=None,
        help="DuckDB file path (overrides $DUCKDB_PATH)",
    )
    yf_parser.add_argument(
        "--universe-path",
        type=Path,
        default=None,
        help="Ticker universe YAML path (overrides default)",
    )
    yf_parser.set_defaults(handler=_refresh_yfinance)
    return parser


def main(argv: Sequence[str] | None = None) -> None:
    logging.basicConfig(level=logging.INFO)
    parser = _build_parser()
    args = parser.parse_args(argv)
    sys.exit(args.handler(args))


if __name__ == "__main__":
    main()
