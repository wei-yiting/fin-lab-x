"""One-shot ingest for the sec_retrieval_ab ticker grid.

Parses the latest 10-K of every ticker in ``TICKER_GRID`` into the filing
store via ``sec_text_pipeline.parse_filing`` (cache-first), then prints a
per-(ticker, item) detection-path table so the sampling step can verify all
four detection paths (markdown_h3 / markdown_h4 / text_fallback / flat)
have natural samples before the grid is finalized.

The grid is the sector x market-cap selection tool from the issue spec —
NOT a sampling axis. Swapping a ticker (parse failure, or a detection path
with zero samples) must stay within the same grid cell.

Usage: uv run python -m backend.evals.scenarios.sec_retrieval_ab.curation.ingest_tickers
"""

from __future__ import annotations

import sys
from collections import Counter
from typing import TypedDict

from backend.common.errors import FinLabError

# Latest-fiscal-year resolution deliberately reuses sec_core's private
# helper: the public parse path requires an explicit year, and duplicating
# the "latest 10-K period_of_report" lookup here would just drift. Read-only
# use from a one-shot curation script; not part of the frozen data contract.
from backend.common.sec_core import _resolve_latest_fiscal_year
from backend.ingestion.sec_text_pipeline.filing_models import (
    ParsedFiling,
    StructuredItem,
)
from backend.ingestion.sec_text_pipeline.parser import parse_filing


class GridCell(TypedDict):
    sector: str
    cap: str  # large | mid | small — provenance bucket, not a sampling axis


# GICS sector x cap grid (DEV-162 spec): every sector >=1 large cap, about
# half the sectors add one mid/small cap. ~16 tickers, latest 10-K each.
TICKER_GRID: dict[str, GridCell] = {
    "NVDA": {"sector": "Information Technology", "cap": "large"},
    "DDOG": {"sector": "Information Technology", "cap": "mid"},
    "LLY": {"sector": "Health Care", "cap": "large"},
    "PODD": {"sector": "Health Care", "cap": "mid"},
    "JPM": {"sector": "Financials", "cap": "large"},
    "COIN": {"sector": "Financials", "cap": "mid"},
    "AMZN": {"sector": "Consumer Discretionary", "cap": "large"},
    "DECK": {"sector": "Consumer Discretionary", "cap": "mid"},
    "GOOGL": {"sector": "Communication Services", "cap": "large"},
    "CAT": {"sector": "Industrials", "cap": "large"},
    "AXON": {"sector": "Industrials", "cap": "mid"},
    "COST": {"sector": "Consumer Staples", "cap": "large"},
    "XOM": {"sector": "Energy", "cap": "large"},
    "NEE": {"sector": "Utilities", "cap": "large"},
    "PLD": {"sector": "Real Estate", "cap": "large"},
    "LIN": {"sector": "Materials", "cap": "large"},
}


def item_detection_path(filing: ParsedFiling, item_key: str) -> str | None:
    """The detection-path bucket of one Item (None if absent)."""
    for item in filing.items:
        if item.item.strip().lower() == item_key.strip().lower():
            if isinstance(item, StructuredItem):
                return item.detection_source
            return "flat"
    return None


def main() -> int:
    parsed: dict[str, ParsedFiling] = {}
    failures: dict[str, str] = {}

    for ticker in TICKER_GRID:
        try:
            fy = _resolve_latest_fiscal_year(ticker)
            filing = parse_filing(ticker, fy)
        except (FinLabError, ValueError) as exc:
            failures[ticker] = f"{type(exc).__name__}: {exc}"
            print(f"[FAIL] {ticker}: {failures[ticker]}", flush=True)
            continue
        parsed[ticker] = filing
        print(
            f"[OK]   {ticker} FY{filing.metadata.fiscal_year} "
            f"({len(filing.items)} items, accession "
            f"{filing.metadata.accession_number})",
            flush=True,
        )

    # Detection-path table over everything now in the store for the grid.
    print("\n=== detection path per (ticker, item) ===")
    path_totals: Counter[str] = Counter()
    for ticker, filing in sorted(parsed.items()):
        cells = []
        for item in filing.items:
            path = item.detection_source if isinstance(item, StructuredItem) else "flat"
            path_totals[path] += 1
            cells.append(f"{item.item}:{path}")
        print(f"{ticker:6} {' '.join(cells)}")

    print("\n=== totals ===")
    for path in ("markdown_h3", "markdown_h4", "text_fallback", "flat"):
        print(f"{path:15} {path_totals.get(path, 0)}")
    if failures:
        print("\n=== failures (swap within the same grid cell) ===")
        for ticker, msg in failures.items():
            print(f"{ticker}: {msg}")
    return 0 if parsed else 1


if __name__ == "__main__":
    sys.exit(main())
