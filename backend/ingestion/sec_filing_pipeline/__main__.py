"""CLI entry point for the SEC filing pipeline.

Usage:
    uv run python -m backend.ingestion.sec_filing_pipeline AAPL 10-K
    uv run python -m backend.ingestion.sec_filing_pipeline AAPL 10-K --fiscal-year 2025
    uv run python -m backend.ingestion.sec_filing_pipeline AAPL 10-K --force
    uv run python -m backend.ingestion.sec_filing_pipeline AAPL 10-K --verbose
    uv run python -m backend.ingestion.sec_filing_pipeline AAPL 10-K --json
    uv run python -m backend.ingestion.sec_filing_pipeline batch NVDA AAPL TSLA --filing-type 10-K
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[2] / ".env")

from backend.ingestion.sec_filing_pipeline.filing_models import (  # noqa: E402
    FilingMetadata,
    ParsedFiling,
    SECPipelineError,
)
from backend.ingestion.sec_filing_pipeline.pipeline import (  # noqa: E402
    SECFilingPipeline,
)

_STORE_BASE_DIR = Path("data/sec_filings")

_USAGE = """\
usage: python -m backend.ingestion.sec_filing_pipeline TICKER FILING_TYPE [options]
       python -m backend.ingestion.sec_filing_pipeline batch TICKER... --filing-type TYPE [options]

Download and parse SEC filings from EDGAR.

commands:
  (default)   Process a single filing
  batch       Process multiple tickers

options:
  -h, --help  Show this help message

Run with -h after a command for detailed options:
  python -m backend.ingestion.sec_filing_pipeline AAPL 10-K -h
  python -m backend.ingestion.sec_filing_pipeline batch -h
"""


def main(argv: list[str] | None = None) -> None:
    args = sys.argv[1:] if argv is None else argv

    if not args or (len(args) == 1 and args[0] in ("-h", "--help")):
        print(_USAGE, end="")
        return

    if args[0] == "batch":
        _run_batch(args[1:])
    else:
        _run_single(args)


def _run_single(argv: list[str]) -> None:
    parser = argparse.ArgumentParser(
        prog="python -m backend.ingestion.sec_filing_pipeline",
        description="Download and parse a single SEC filing",
    )
    parser.add_argument("ticker", help="Stock ticker symbol (e.g. AAPL)")
    parser.add_argument("filing_type", help="Filing type (e.g. 10-K)")
    parser.add_argument(
        "--fiscal-year", type=int, default=None, help="Fiscal year (default: latest)"
    )
    parser.add_argument(
        "--force", action="store_true", help="Bypass cache and re-download"
    )
    parser.add_argument(
        "--verbose", action="store_true", help="Show full metadata"
    )
    parser.add_argument(
        "--json", action="store_true", dest="json_output", help="Output as JSON"
    )
    args = parser.parse_args(argv)

    try:
        pipeline = SECFilingPipeline.create()
        filing = pipeline.process(
            args.ticker, args.filing_type, args.fiscal_year, args.force
        )
    except SECPipelineError as exc:
        print(f"{type(exc).__name__}: {exc}", file=sys.stderr)
        raise SystemExit(1) from None
    except KeyboardInterrupt:
        raise SystemExit(130) from None

    if args.json_output:
        print(json.dumps(_filing_to_dict(filing), indent=2))
    elif args.verbose:
        _print_verbose(filing)
    else:
        _print_concise(filing)


def _run_batch(argv: list[str]) -> None:
    parser = argparse.ArgumentParser(
        prog="python -m backend.ingestion.sec_filing_pipeline batch",
        description="Download and parse SEC filings for multiple tickers",
    )
    parser.add_argument("tickers", nargs="+", help="Stock ticker symbols")
    parser.add_argument(
        "--filing-type", required=True, help="Filing type (e.g. 10-K)"
    )
    parser.add_argument(
        "--verbose", action="store_true", help="Show full metadata per ticker"
    )
    parser.add_argument(
        "--json", action="store_true", dest="json_output", help="Output as JSON"
    )
    args = parser.parse_args(argv)

    try:
        pipeline = SECFilingPipeline.create()
        results = pipeline.process_batch(args.tickers, args.filing_type)
    except SECPipelineError as exc:
        print(f"{type(exc).__name__}: {exc}", file=sys.stderr)
        raise SystemExit(1) from None
    except KeyboardInterrupt:
        raise SystemExit(130) from None

    has_error = False

    if args.json_output:
        output: dict[str, Any] = {}
        for ticker, result in results.items():
            if result.status == "success":
                assert result.filing is not None
                output[ticker] = _filing_to_dict(result.filing)
                output[ticker]["status"] = "success"
                output[ticker]["from_cache"] = result.from_cache
            else:
                assert result.error is not None
                output[ticker] = {
                    "status": "error",
                    "error": str(result.error),
                    "error_type": type(result.error).__name__,
                }
                has_error = True
        print(json.dumps(output, indent=2))
    elif args.verbose:
        for ticker, result in results.items():
            if result.status == "success":
                assert result.filing is not None
                print(f"--- {ticker} ---")
                _print_verbose(result.filing)
                print()
            else:
                print(f"--- {ticker} ---")
                print("status: error")
                print(f"error:  {result.error}")
                print()
                has_error = True
    else:
        for ticker, result in results.items():
            if result.status == "success":
                assert result.filing is not None
                m = result.filing.metadata
                path = _filing_path(m)
                print(f"{m.ticker}  FY{m.fiscal_year}  ok   {path}")
            else:
                print(f"{ticker}  {'—':>6}  err  {result.error}")
                has_error = True

    if has_error:
        raise SystemExit(1)


def _filing_path(metadata: FilingMetadata) -> Path:
    return (
        _STORE_BASE_DIR
        / metadata.ticker
        / str(metadata.filing_type)
        / f"{metadata.fiscal_year}.md"
    )


def _filing_to_dict(filing: ParsedFiling) -> dict[str, Any]:
    return {
        "metadata": filing.metadata.model_dump(),
        "content_length": len(filing.markdown_content),
        "file_path": str(_filing_path(filing.metadata)),
    }


def _print_concise(filing: ParsedFiling) -> None:
    m = filing.metadata
    path = _filing_path(m)
    chars = len(filing.markdown_content)
    print(f"{m.ticker}  FY{m.fiscal_year}  {m.parsed_at}  {chars} chars  {path}")


def _print_verbose(filing: ParsedFiling) -> None:
    m = filing.metadata
    path = _filing_path(m)
    chars = len(filing.markdown_content)
    print(f"ticker:           {m.ticker}")
    print(f"company_name:     {m.company_name}")
    print(f"filing_type:      {m.filing_type}")
    print(f"fiscal_year:      {m.fiscal_year}")
    print(f"cik:              {m.cik}")
    print(f"accession_number: {m.accession_number}")
    print(f"filing_date:      {m.filing_date}")
    print(f"source_url:       {m.source_url}")
    print(f"parsed_at:        {m.parsed_at}")
    print(f"converter:        {m.converter}")
    print(f"content_length:   {chars} chars")
    print(f"file_path:        {path}")


if __name__ == "__main__":
    main()
