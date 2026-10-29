"""Re-anchor the final dataset's ground truth to a re-parsed filing store.

The dataset was assembled against a filing store parsed under edgartools
5.17.1. The A/B runs both arms on edgartools 5.62, whose parse fixes Item
mis-assignments (text the old parse put under Item 16 / 15 / 6 / 1 now sits in
its real Item) and changes whitespace inside rendered tables. Ground truth is
store-anchored (ADR-0016), so every row is re-anchored to the 5.62 store:

- questions, answer requirements and the evidence itself never change;
- each (path, span, snippet) alternative is re-located in the store, exact
  case-insensitive match first, whitespace-insensitive second (then the span
  and snippet are re-extracted as exact store substrings, round-3 T1 rule);
- the alternative's Item comes from wherever the store now holds the text
  (round-3 T2 rule: the actual store header_path), never Item 8;
- ``block_heading`` / ``detection_source`` are refreshed from the 5.62 unit;
- alternatives that collapse onto the same location are deduplicated.

Changed rows get a line appended to ``review_provenance``.

Usage::

    python -m backend.evals.scenarios.sec_retrieval_ab.curation.reanchor_to_store
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from backend.evals.scenarios.sec_retrieval_ab.curation.validate_dataset import (
    load_csv_rows,
    load_filings,
    validate_rows,
)
from backend.ingestion.sec_text_pipeline.filing_models import FlatItem, ParsedFiling

DATASET_PATH = Path(__file__).resolve().parents[1] / "dataset.csv"
LIST_COLUMNS = (
    "expected_header_paths",
    "answer_spans",
    "answer_snippets",
    "block_heading",
    "detection_source",
)
PROVENANCE_TAG = "Re-anchored to the edgartools 5.62 filing store (2026-10-28)"


@dataclass(frozen=True)
class _Unit:
    item_key: str
    label: str
    block_heading: str | None
    detection_source: str
    text: str


def exact_slice(haystack: str, needle: str) -> str | None:
    """The substring of ``haystack`` matching ``needle`` ignoring case/whitespace."""
    positions = [i for i, ch in enumerate(haystack) if not ch.isspace()]
    folded = "".join(haystack[i] for i in positions).lower()
    key = "".join(ch for ch in needle if not ch.isspace()).lower()
    if not key:
        return None
    start = folded.find(key)
    if start < 0:
        return None
    return haystack[positions[start] : positions[start + len(key) - 1] + 1]


def _units(filing: ParsedFiling) -> list[_Unit]:
    units: list[_Unit] = []
    for item in filing.items:
        key = item.item.strip().lower()
        if key == "8":
            continue
        label = f"Item {key.upper()}. {item.title}"
        if isinstance(item, FlatItem):
            units.append(_Unit(key, label, None, "flat", item.text))
            continue
        if item.prelude:
            units.append(_Unit(key, label, None, item.detection_source, item.prelude))
        units.extend(
            _Unit(key, label, block.heading, item.detection_source, block.text)
            for block in item.blocks
        )
    return units


def _item_of(path: str) -> str:
    return path.split(" / ")[2].split(". ")[0]


def reanchor_row(
    row: dict[str, list[Any]], filing: ParsedFiling
) -> tuple[dict[str, list[Any]], list[str]]:
    """Re-locate every alternative of one row; return new lists and change notes."""
    meta = filing.metadata
    prefix = f"{meta.ticker.upper()} / {meta.fiscal_year}"
    units = _units(filing)
    new: dict[str, list[Any]] = {column: [] for column in LIST_COLUMNS}
    seen: set[tuple[str, str]] = set()
    notes: list[str] = []

    alternatives = zip(
        row["expected_header_paths"], row["answer_spans"], row["answer_snippets"]
    )
    for index, (path, span, snippet) in enumerate(alternatives):
        old_item = _item_of(path)
        hits = [u for u in units if span.lower() in u.text.lower()]
        reextracted = False
        if not hits:
            hits = [u for u in units if exact_slice(u.text, span) is not None]
            reextracted = bool(hits)
        if not hits:
            notes.append(
                f"alt{index} ({old_item}): span not found outside Item 8; dropped"
            )
            continue
        preferred = [u for u in hits if f"{prefix} / {u.label}" == path]
        for unit in preferred or hits:
            new_span = exact_slice(unit.text, span) if reextracted else span
            new_snippet = exact_slice(new_span or "", snippet)
            if new_span is None or new_snippet is None:
                notes.append(
                    f"alt{index}: snippet not inside re-extracted span; dropped"
                )
                continue
            new_path = f"{prefix} / {unit.label}"
            if (new_path, new_snippet) in seen:
                notes.append(
                    f"alt{index} ({old_item}): same text now at "
                    f"{_item_of(new_path)}; merged"
                )
                continue
            seen.add((new_path, new_snippet))
            if new_path != path:
                notes.append(f"alt{index}: {old_item} -> {_item_of(new_path)}")
            if reextracted:
                notes.append(f"alt{index}: whitespace re-extracted from store")
            new["expected_header_paths"].append(new_path)
            new["answer_spans"].append(new_span)
            new["answer_snippets"].append(new_snippet)
            new["block_heading"].append(unit.block_heading)
            new["detection_source"].append(unit.detection_source)
    return new, notes


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Re-anchor dataset to the store")
    parser.add_argument("--dataset", type=Path, default=DATASET_PATH)
    args = parser.parse_args(argv)

    filings = load_filings()
    with args.dataset.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        fieldnames = list(reader.fieldnames or [])
        rows = list(reader)

    for row in rows:
        ticker = json.loads(row["expected_tickers"])[0]
        filing = filings[(ticker, int(row["fiscal_year"]))]
        lists = {column: json.loads(row[column]) for column in LIST_COLUMNS}
        new, notes = reanchor_row(lists, filing)
        for column in LIST_COLUMNS:
            row[column] = json.dumps(new[column], ensure_ascii=False)
        if notes:
            row["review_provenance"] = (
                f"{row['review_provenance']} {PROVENANCE_TAG}: {'; '.join(notes)}."
            ).strip()
            print(f"{row['candidate_id']}: {'; '.join(notes)}")

    with args.dataset.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    issues = validate_rows(load_csv_rows(args.dataset), filings)
    for issue in issues:
        print(f"[{issue.row_id}] {issue.rule}: {issue.message}")
    print(f"{'FAIL' if issues else 'OK'} — {len(rows)} rows re-anchored")
    return 1 if issues else 0


if __name__ == "__main__":
    sys.exit(main())
