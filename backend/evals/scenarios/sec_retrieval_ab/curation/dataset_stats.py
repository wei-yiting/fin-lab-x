"""Print the README distribution tables for the sec_retrieval_ab dataset.

Reads the draft dataset.csv and emits markdown: per-axis marginal
distributions plus the ticker grid with fiscal year and accession number.
Rerun after any dataset change and paste the output into README.md.

Usage: uv run python -m backend.evals.scenarios.sec_retrieval_ab.curation.dataset_stats
"""

from __future__ import annotations

import csv
import json
import re
import sys
from collections import Counter
from pathlib import Path

DATASET_CSV = Path(__file__).parent.parent / "dataset.csv"


def _table(title: str, counter: Counter[str], total_label: str = "rows") -> str:
    lines = [f"### {title}", "", "| value | rows |", "|---|---|"]
    for value, count in sorted(counter.items(), key=lambda kv: (-kv[1], kv[0])):
        lines.append(f"| {value} | {count} |")
    lines.append(f"| **total ({total_label})** | **{sum(counter.values())}** |")
    return "\n".join(lines) + "\n"


def main() -> int:
    with DATASET_CSV.open("r", encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))

    detection: Counter[str] = Counter()
    items: Counter[str] = Counter()
    for row in rows:
        # cross-item / multi rows count once per referenced bucket
        for source in set(json.loads(row["detection_source"])):
            detection[source] += 1
        row_items = {
            re.sub(r"^Item ([0-9]{1,2}[A-Ca-c]?)\..*$", r"\1", path.split(" / ")[2])
            for path in json.loads(row["expected_header_paths"])
        }
        for key in row_items:
            items[key.upper()] += 1

    print(_table("Detection path (rows touching each bucket)", detection))
    print(_table("Item (rows touching each Item)", items))
    print(_table("Query type", Counter(r["query_type"] for r in rows)))
    print(_table("Sector", Counter(r["sector"] for r in rows)))
    print(
        _table(
            "Market-cap bucket (provenance)",
            Counter(r["market_cap_bucket"] for r in rows),
        )
    )
    print(_table("Generation mode", Counter(r["generation_mode"] for r in rows)))

    print("### Ticker grid (rows / FY / accession)\n")
    print("| ticker | sector | cap | rows | FY | accession |")
    print("|---|---|---|---|---|---|")
    per_ticker: dict[str, list[dict[str, str]]] = {}
    for row in rows:
        per_ticker.setdefault(json.loads(row["expected_tickers"])[0], []).append(row)
    for ticker, ticker_rows in sorted(per_ticker.items()):
        first = ticker_rows[0]
        print(
            f"| {ticker} | {first['sector']} | {first['market_cap_bucket']} "
            f"| {len(ticker_rows)} | {first['fiscal_year']} "
            f"| {first['accession_number']} |"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
