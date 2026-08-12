"""CLI entry point for the SEC text pipeline inspect views.

Usage:
    uv run python -m backend.ingestion.sec_text_pipeline --ticker AAPL --fiscal-year 2025
    uv run python -m backend.ingestion.sec_text_pipeline --ticker AAPL --fiscal-year 2025 --verbose
    uv run python -m backend.ingestion.sec_text_pipeline --ticker AAPL --fiscal-year 2025 --section 1a
    uv run python -m backend.ingestion.sec_text_pipeline inspect --ticker AAPL --fiscal-year 2025

The default (and ``--verbose``) mode prints the one-screen summary table;
``--section`` prints one Item as plain text; the ``inspect`` subcommand
renders the full markdown view to the gitignored inspect directory and
prints the output path. All modes are cache-first: a filing-store miss
triggers fetch + parse automatically (``--force`` re-parses).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[2] / ".env")

from backend.common.data_paths import get_sec_text_inspect_dir  # noqa: E402
from backend.common.errors import FinLabError  # noqa: E402
from backend.ingestion.sec_text_pipeline.filing_models import ParsedFiling  # noqa: E402
from backend.ingestion.sec_text_pipeline.inspect_view import (  # noqa: E402
    to_inspect_markdown,
    to_section_text,
    to_summary_text,
)
from backend.ingestion.sec_text_pipeline.parser import parse_filing  # noqa: E402


def main(argv: list[str] | None = None) -> None:
    args = sys.argv[1:] if argv is None else argv
    if args and args[0] == "inspect":
        _run_inspect(args[1:])
    else:
        _run_view(args)


def _make_parser(prog: str, description: str) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog=prog, description=description)
    parser.add_argument(
        "--ticker", required=True, help="Stock ticker symbol (e.g. AAPL)"
    )
    parser.add_argument(
        "--fiscal-year", type=int, required=True, help="Fiscal year (e.g. 2025)"
    )
    parser.add_argument(
        "--force", action="store_true", help="Bypass the filing store and re-parse"
    )
    return parser


def _load_filing(ticker: str, fiscal_year: int, force: bool) -> ParsedFiling:
    # ValueError covers ticker validation from the filing store, which sits
    # outside the FinLabError taxonomy.
    try:
        return parse_filing(ticker, fiscal_year, force)
    except (FinLabError, ValueError) as exc:
        print(f"{type(exc).__name__}: {exc}", file=sys.stderr)
        raise SystemExit(1) from None
    except KeyboardInterrupt:
        raise SystemExit(130) from None


def _run_view(argv: list[str]) -> None:
    parser = _make_parser(
        prog="python -m backend.ingestion.sec_text_pipeline",
        description=(
            "Summary view of a parsed 10-K (default). Use --section for one "
            "Item as plain text, or the `inspect` subcommand for the full "
            "markdown render."
        ),
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--verbose", action="store_true", help="One-screen summary table (default)"
    )
    mode.add_argument(
        "--section", metavar="KEY", help="Print one Item as plain text (e.g. 7, 1a)"
    )
    args = parser.parse_args(argv)

    filing = _load_filing(args.ticker, args.fiscal_year, args.force)
    if args.section:
        try:
            print(to_section_text(filing, args.section))
        except ValueError as exc:
            print(str(exc), file=sys.stderr)
            raise SystemExit(1) from None
    else:
        print(to_summary_text(filing))


def _run_inspect(argv: list[str]) -> None:
    parser = _make_parser(
        prog="python -m backend.ingestion.sec_text_pipeline inspect",
        description="Render the full markdown inspect view and print its path",
    )
    args = parser.parse_args(argv)

    filing = _load_filing(args.ticker, args.fiscal_year, args.force)
    m = filing.metadata
    out_path = (
        get_sec_text_inspect_dir()
        / m.ticker
        / str(m.filing_type)
        / f"{m.fiscal_year}.md"
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(to_inspect_markdown(filing), encoding="utf-8")
    print(out_path)


if __name__ == "__main__":
    main()
