"""Dataset validator for the sec_retrieval_ab curated dataset (DEV-162).

Validates ground truth against the filing store ONLY (ADR-0016): no Qdrant,
no network, no LLM. Pure functions over dataset rows + ParsedFiling JSON, so
the whole contract is unit-testable with fixtures.

Contract rules (one issue `rule` string each):
- list_alignment          header_paths / spans / snippets same length
- entry_count             factoid/passage exactly 1 entry, multi_passage >= 2
- ticker_mismatch         every header_path ticker == expected_tickers[0]
- header_path_format      `TICKER / FY / Item N. Title`, no Part, title match
- filing_missing          (ticker, fiscal year) not in the filing store
- item_missing            Item absent from the parsed filing (e.g. stub-dropped)
- span_not_in_block       span is not a substring of any single unit
                          (prelude / one block / flat text), case-insensitive
- span_too_long           span > SPAN_MAX_TOKENS cl100k tokens (~half a chunk)
- snippet_not_in_span     snippet not a substring of its span
- snippet_length          snippet outside 50-200 chars
- snippet_not_unique      snippet occurs != 1 time across the whole corpus
- multi_passage_same_block   two spans share one block of one structured Item
- multi_passage_too_close    two spans in one flat Item < MIN_FLAT_GAP_TOKENS apart

Usage:
    uv run python -m backend.evals.scenarios.sec_retrieval_ab.curation.validate_dataset \
        [--csv path/to/dataset.csv]
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

from backend.common.data_paths import get_sec_text_dir
from backend.ingestion.sec_text_pipeline.filing_models import (
    FlatItem,
    ParsedFiling,
    StructuredItem,
)

SPAN_MAX_TOKENS = 300
MIN_FLAT_GAP_TOKENS = 600
SNIPPET_MIN_CHARS = 50
SNIPPET_MAX_CHARS = 200


@dataclass(frozen=True)
class Row:
    """One dataset row with JSON-list columns already parsed."""

    row_id: str
    question: str
    header_paths: list[str]
    tickers: list[str]
    spans: list[str]
    snippets: list[str]
    query_type: str


@dataclass(frozen=True)
class Issue:
    row_id: str
    rule: str
    message: str


@dataclass(frozen=True)
class _Unit:
    """One span-addressable text unit: prelude, a block, or the flat body."""

    index: int
    heading: str | None
    text: str


@dataclass(frozen=True)
class _Entry:
    """One resolved (header_path, span, snippet) triple of a row."""

    ticker: str
    fiscal_year: int
    item_key: str
    is_flat: bool
    unit_index: int | None
    span: str
    snippet: str
    flat_char_pos: int = field(default=-1)


@lru_cache(maxsize=1)
def _encoder():
    # Lazy: tiktoken loads (and on cold cache, fetches) the BPE table.
    import tiktoken

    return tiktoken.get_encoding("cl100k_base")


def _token_len(text: str) -> int:
    return len(_encoder().encode(text))


def load_filings(store_dir: Path | None = None) -> dict[tuple[str, int], ParsedFiling]:
    """Load every ParsedFiling JSON under the store into a lookup dict."""
    base = Path(store_dir) if store_dir is not None else get_sec_text_dir()
    filings: dict[tuple[str, int], ParsedFiling] = {}
    for path in sorted(base.glob("*/10-K/*.json")):
        filing = ParsedFiling.model_validate_json(path.read_text(encoding="utf-8"))
        meta = filing.metadata
        filings[(meta.ticker.upper(), meta.fiscal_year)] = filing
    return filings


def _units(item: StructuredItem | FlatItem) -> list[_Unit]:
    if isinstance(item, FlatItem):
        return [_Unit(index=0, heading=None, text=item.text)]
    units: list[_Unit] = []
    if item.prelude:
        units.append(_Unit(index=0, heading=None, text=item.prelude))
    units.extend(
        _Unit(index=len(units) + i, heading=block.heading, text=block.text)
        for i, block in enumerate(item.blocks)
    )
    return units


def _item_label(item: StructuredItem | FlatItem) -> str:
    return f"Item {item.item.strip().upper()}. {item.title}"


def _find_item(filing: ParsedFiling, item_key: str) -> StructuredItem | FlatItem | None:
    for item in filing.items:
        if item.item.strip().lower() == item_key:
            return item
    return None


def _corpus_occurrences(
    filings: dict[tuple[str, int], ParsedFiling], needle_lower: str
) -> int:
    total = 0
    for filing in filings.values():
        for item in filing.items:
            for unit in _units(item):
                total += unit.text.lower().count(needle_lower)
    return total


def _parse_header_path(path: str) -> tuple[str, int, str, str] | None:
    """Return (ticker, fiscal_year, item_key, item_label) or None if malformed."""
    segments = [s.strip() for s in path.split(" / ")]
    if len(segments) != 3:
        return None
    ticker, year_raw, label = segments
    if not year_raw.isdigit():
        return None
    if not label.startswith("Item "):
        return None
    head, _, title = label.partition(". ")
    item_key = head.removeprefix("Item ").strip().lower()
    if not item_key or not title:
        return None
    return ticker.upper(), int(year_raw), item_key, label


def _resolve_entry(
    row: Row,
    index: int,
    filings: dict[tuple[str, int], ParsedFiling],
    issues: list[Issue],
) -> _Entry | None:
    """Validate one (path, span, snippet) triple; return placement on success."""
    path = row.header_paths[index]
    span = row.spans[index]
    snippet = row.snippets[index]

    parsed = _parse_header_path(path)
    if parsed is None or " / Part" in path or path.split(" / ")[1].startswith("Part"):
        issues.append(
            Issue(row.row_id, "header_path_format", f"malformed header_path: {path!r}")
        )
        return None
    ticker, fiscal_year, item_key, label = parsed

    if row.tickers and ticker != row.tickers[0].upper():
        issues.append(
            Issue(
                row.row_id,
                "ticker_mismatch",
                f"header_path ticker {ticker} != expected_tickers[0] "
                f"{row.tickers[0]!r}",
            )
        )
        return None

    filing = filings.get((ticker, fiscal_year))
    if filing is None:
        issues.append(
            Issue(
                row.row_id,
                "filing_missing",
                f"({ticker}, {fiscal_year}) not in the filing store",
            )
        )
        return None

    item = _find_item(filing, item_key)
    if item is None:
        issues.append(
            Issue(
                row.row_id,
                "item_missing",
                f"Item {item_key!r} absent from {ticker} FY{fiscal_year}",
            )
        )
        return None

    if label != _item_label(item):
        issues.append(
            Issue(
                row.row_id,
                "header_path_format",
                f"label {label!r} != store label {_item_label(item)!r}",
            )
        )
        return None

    ok = True
    span_lower = span.lower()
    units = _units(item)
    home = next((u for u in units if span_lower in u.text.lower()), None)
    if home is None:
        issues.append(
            Issue(
                row.row_id,
                "span_not_in_block",
                f"span not found inside any single unit of {label!r}",
            )
        )
        ok = False
    if _token_len(span) > SPAN_MAX_TOKENS:
        issues.append(
            Issue(
                row.row_id,
                "span_too_long",
                f"span is {_token_len(span)} tokens (max {SPAN_MAX_TOKENS})",
            )
        )
        ok = False
    if snippet.lower() not in span_lower:
        issues.append(
            Issue(row.row_id, "snippet_not_in_span", "snippet not inside its span")
        )
        ok = False
    if not SNIPPET_MIN_CHARS <= len(snippet) <= SNIPPET_MAX_CHARS:
        issues.append(
            Issue(
                row.row_id,
                "snippet_length",
                f"snippet is {len(snippet)} chars "
                f"({SNIPPET_MIN_CHARS}-{SNIPPET_MAX_CHARS} required)",
            )
        )
        ok = False
    occurrences = _corpus_occurrences(filings, snippet.lower())
    if occurrences != 1:
        issues.append(
            Issue(
                row.row_id,
                "snippet_not_unique",
                f"snippet occurs {occurrences} times across the parsed corpus",
            )
        )
        ok = False

    if not ok:
        return None
    is_flat = isinstance(item, FlatItem)
    return _Entry(
        ticker=ticker,
        fiscal_year=fiscal_year,
        item_key=item_key,
        is_flat=is_flat,
        unit_index=home.index if home is not None else None,
        span=span,
        snippet=snippet,
        flat_char_pos=item.text.lower().find(span_lower) if is_flat else -1,
    )


def _check_multi_passage_placement(
    row: Row,
    entries: list[_Entry],
    filings: dict[tuple[str, int], ParsedFiling],
    issues: list[Issue],
) -> None:
    for i in range(len(entries)):
        for j in range(i + 1, len(entries)):
            a, b = entries[i], entries[j]
            same_item = (a.ticker, a.fiscal_year, a.item_key) == (
                b.ticker,
                b.fiscal_year,
                b.item_key,
            )
            if not same_item:
                continue
            if not a.is_flat:
                if a.unit_index == b.unit_index:
                    issues.append(
                        Issue(
                            row.row_id,
                            "multi_passage_same_block",
                            f"spans {i} and {j} share one block of Item {a.item_key}",
                        )
                    )
                continue
            filing = filings[(a.ticker, a.fiscal_year)]
            item = _find_item(filing, a.item_key)
            assert isinstance(item, FlatItem)
            first, second = sorted((a, b), key=lambda entry: entry.flat_char_pos)
            gap_start = first.flat_char_pos + len(first.span)
            gap_text = item.text[gap_start : second.flat_char_pos]
            if second.flat_char_pos < gap_start or (
                _token_len(gap_text) < MIN_FLAT_GAP_TOKENS
            ):
                issues.append(
                    Issue(
                        row.row_id,
                        "multi_passage_too_close",
                        f"spans {i} and {j} are < {MIN_FLAT_GAP_TOKENS} "
                        f"tokens apart in flat Item {a.item_key}",
                    )
                )


def validate_rows(
    rows: list[Row], filings: dict[tuple[str, int], ParsedFiling]
) -> list[Issue]:
    """Validate every row; empty result means the dataset passes."""
    issues: list[Issue] = []
    for row in rows:
        n = len(row.header_paths)
        if not (len(row.spans) == len(row.snippets) == n):
            issues.append(
                Issue(
                    row.row_id,
                    "list_alignment",
                    f"paths/spans/snippets lengths differ: "
                    f"{n}/{len(row.spans)}/{len(row.snippets)}",
                )
            )
            continue
        if row.query_type in ("factoid", "passage"):
            if n != 1:
                issues.append(
                    Issue(
                        row.row_id,
                        "entry_count",
                        f"{row.query_type} requires exactly 1 entry, got {n}",
                    )
                )
                continue
        elif row.query_type == "multi_passage":
            if n < 2:
                issues.append(
                    Issue(
                        row.row_id,
                        "entry_count",
                        f"multi_passage requires >= 2 entries, got {n}",
                    )
                )
                continue
        else:
            issues.append(
                Issue(
                    row.row_id,
                    "entry_count",
                    f"unknown query_type {row.query_type!r}",
                )
            )
            continue

        entries = [
            entry
            for i in range(n)
            if (entry := _resolve_entry(row, i, filings, issues)) is not None
        ]
        if row.query_type == "multi_passage" and len(entries) == n:
            _check_multi_passage_placement(row, entries, filings, issues)
    return issues


def load_csv_rows(csv_path: Path) -> list[Row]:
    """Build Rows from dataset.csv (JSON-list columns parsed here)."""
    rows: list[Row] = []
    with csv_path.open("r", encoding="utf-8-sig", newline="") as file:
        for i, raw in enumerate(csv.DictReader(file), start=1):
            rows.append(
                Row(
                    row_id=f"row{i:02d}",
                    question=raw["question"],
                    header_paths=json.loads(raw["expected_header_paths"]),
                    tickers=json.loads(raw["expected_tickers"]),
                    spans=json.loads(raw["answer_spans"]),
                    snippets=json.loads(raw["answer_snippets"]),
                    query_type=raw["query_type"],
                )
            )
    return rows


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--csv",
        type=Path,
        default=Path(__file__).parent.parent / "dataset.csv",
        help="dataset CSV to validate (default: the scenario's dataset.csv)",
    )
    parser.add_argument(
        "--store-dir",
        type=Path,
        default=None,
        help="filing store root (default: the repo data path)",
    )
    args = parser.parse_args(argv)

    rows = load_csv_rows(args.csv)
    issues = validate_rows(rows, load_filings(args.store_dir))
    if issues:
        for issue in issues:
            print(f"[{issue.row_id}] {issue.rule}: {issue.message}")
        print(f"\nFAIL — {len(issues)} issue(s) across {len(rows)} row(s)")
        return 1
    print(f"OK — {len(rows)} rows validated against the filing store")
    return 0


if __name__ == "__main__":
    sys.exit(main())
