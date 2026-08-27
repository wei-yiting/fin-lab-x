"""Dataset validator for the sec_retrieval_ab curated dataset.

Validates ground truth against the filing store ONLY (ADR-0016): no Qdrant,
no network, no LLM. Pure functions over dataset rows + ParsedFiling JSON, so
the whole contract is unit-testable with fixtures.

Round-3 semantics (ratified 2026-08-27, see curation/round3_assembly_instructions.md):
the per-row entry lists (`header_paths` / `spans` / `snippets`, index-aligned)
are OR alternatives — retrieval hitting ANY listed location counts as a hit.
`multi_passage` was removed, and Item 8 is outside the retrieval scope on both
A/B arms, so it can neither appear as an expected location nor cause a
uniqueness failure.

Contract rules (one issue `rule` string each):
- list_alignment          header_paths / spans / snippets same length
- entry_count             query_type must be factoid|passage, with >= 1 entry
- ticker_mismatch         every header_path ticker == expected_tickers[0]
- header_path_format      `TICKER / FY / Item N. Title`, no Part, title match
- item_8_excluded         header_path targets Item 8 (outside retrieval scope)
- filing_missing          (ticker, fiscal year) not in the filing store
- item_missing            Item absent from the parsed filing (e.g. stub-dropped)
- span_not_in_block       span is not a substring of any single unit
                          (prelude / one block / flat text), case-insensitive
- span_too_long           span > SPAN_MAX_TOKENS cl100k tokens
- snippet_not_in_span     snippet not a substring of its span
- snippet_length          snippet outside SNIPPET_MIN/MAX_CHARS
- snippet_not_unique      enumerated exemption: a snippet's occurrence count
                          across the corpus (Item 8 excluded) must equal the
                          number of times the row lists it; unlisted extra
                          occurrences fail

Usage:
    uv run python -m backend.evals.scenarios.sec_retrieval_ab.curation.validate_dataset \
        [--csv path/to/dataset.csv]
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import tiktoken

from backend.common.data_paths import get_sec_text_dir
from backend.ingestion.sec_text_pipeline.filing_models import (
    FlatItem,
    ParsedFiling,
    StructuredItem,
)

# Ratified contract (round-2 review, 2026-08-27): span ~half the old arm's
# 512-token chunks so it keeps discriminative power.
SPAN_MAX_TOKENS = 300
# The snippet is the strict-containment hit key. 200 chars (~50 tokens)
# matches the old arm's chunk overlap, so a conforming snippet cannot
# straddle a chunk boundary and silently kill the row on that arm.
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
    text: str


@dataclass(frozen=True)
class _Entry:
    """One resolved (header_path, span, snippet) triple of a row."""

    ticker: str
    fiscal_year: int
    item_key: str
    span: str
    snippet: str


@lru_cache(maxsize=1)
def _encoder() -> "tiktoken.Encoding":
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
        return [_Unit(index=0, text=item.text)]
    units: list[_Unit] = []
    if item.prelude:
        units.append(_Unit(index=0, text=item.prelude))
    units.extend(
        _Unit(index=len(units) + i, text=block.text)
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
    """Occurrences across the corpus, excluding Item 8.

    Item 8 is outside the retrieval scope on both A/B arms (round-3
    decision 4), so a copy of a snippet living there can never be retrieved
    and must not count against uniqueness.
    """
    total = 0
    for filing in filings.values():
        for item in filing.items:
            if item.item.strip().lower() == "8":
                continue
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

    if item_key == "8":
        issues.append(
            Issue(
                row.row_id,
                "item_8_excluded",
                f"header_path targets Item 8, which is outside the retrieval "
                f"scope on both A/B arms: {path!r}",
            )
        )
        return None

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
    if not ok:
        return None
    return _Entry(
        ticker=ticker,
        fiscal_year=fiscal_year,
        item_key=item_key,
        span=span,
        snippet=snippet,
    )


def _check_snippet_enumeration(
    row: Row,
    filings: dict[tuple[str, int], ParsedFiling],
    issues: list[Issue],
) -> None:
    """Enumerated-exemption uniqueness (round-3 decision 6).

    For each distinct snippet text in the row's OR-set, its occurrence count
    across the corpus (Item 8 excluded) must equal the number of times the
    row lists it — every reachable copy must be an enumerated alternative.
    """
    listed_counts = Counter(s.lower() for s in row.snippets)
    for text, listed in listed_counts.items():
        occurrences = _corpus_occurrences(filings, text)
        if occurrences != listed:
            issues.append(
                Issue(
                    row.row_id,
                    "snippet_not_unique",
                    f"snippet occurs {occurrences} time(s) in the corpus "
                    f"outside Item 8 but the row lists {listed} location(s)",
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
        if row.query_type not in ("factoid", "passage"):
            issues.append(
                Issue(
                    row.row_id,
                    "entry_count",
                    f"unknown query_type {row.query_type!r} "
                    "(multi_passage was removed in round 3)",
                )
            )
            continue
        if n < 1:
            issues.append(
                Issue(
                    row.row_id,
                    "entry_count",
                    f"{row.query_type} requires at least 1 entry, got {n}",
                )
            )
            continue

        for i in range(n):
            _resolve_entry(row, i, filings, issues)
        _check_snippet_enumeration(row, filings, issues)
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
