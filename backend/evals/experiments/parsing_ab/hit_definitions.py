"""Recall@5 / recall@10 / MRR for both arms under two hit definitions.

Re-scores the recorded retrievals of the parsing A/B (no re-query). Both
definitions use the same format-insensitive snippet matching
(``analyze._match_key``), so they differ only in the Item requirement:

- snippet-only: any top-k chunk contains the target snippet, whatever its label
  (``analyze.snippet_only_rank``).
- snippet + Item: the chunk containing the snippet also sits under the expected
  Item path (``analyze.format_insensitive_rank``).

The strict scorer (exact snippet + Item) is reported as a reference row.

Usage::

    python -m backend.evals.experiments.parsing_ab.hit_definitions \\
        --dataset <dataset.csv> --raw <retrievals.jsonl> --out <file.md>
"""

from __future__ import annotations

import argparse
import statistics
from pathlib import Path
from typing import Any

from backend.evals.experiments.parsing_ab.analyze import (
    _match_key,
    bootstrap_mean_ci,
    build_records,
    expected_from_row,
    load_dataset,
    load_retrievals,
    paired_bootstrap_delta,
    row_id_for,
)
from backend.evals.scenarios.sec_retrieval_ab.html_arm_compat import normalize_chunks

DEFINITIONS = (
    ("Snippet only (content reached the LLM)", "snippet_rank"),
    ("Snippet + correct Item (content and section label)", "format_rank"),
    ("Strict scorer, reference (exact snippet + Item)", "rank"),
)


def _hits(records: list[dict[str, Any]], arm: str, key: str, k: int) -> list[float]:
    return [
        1.0 if r[arm][key] is not None and r[arm][key] <= k else 0.0 for r in records
    ]


def _rr(records: list[dict[str, Any]], arm: str, key: str) -> list[float]:
    return [1 / r[arm][key] if r[arm][key] is not None else 0.0 for r in records]


def _fmt_ci(ci: tuple[float, float, float], signed: bool = False) -> str:
    fmt = "{:+.3f}" if signed else "{:.3f}"
    return f"{fmt.format(ci[0])} [{fmt.format(ci[1])}, {fmt.format(ci[2])}]"


def headline_table(records: list[dict[str, Any]]) -> list[str]:
    n = len(records)
    lines = [
        "| Hit definition | Metric | HTML | Text | Δ text − html | text-only / html-only hits |",
        "|---|---|---:|---:|---:|---:|",
    ]
    for label, key in DEFINITIONS:
        for metric, k in (("recall@5", 5), ("recall@10", 10)):
            html = _hits(records, "html", key, k)
            text = _hits(records, "text", key, k)
            text_only = sum(1 for h, t in zip(html, text) if t > h)
            html_only = sum(1 for h, t in zip(html, text) if h > t)
            lines.append(
                f"| {label} | {metric} | {statistics.mean(html):.3f} ({int(sum(html))}/{n})"
                f" | {statistics.mean(text):.3f} ({int(sum(text))}/{n})"
                f" | {statistics.mean(text) - statistics.mean(html):+.3f}"
                f" | {text_only} / {html_only} |"
            )
        html_rr = _rr(records, "html", key)
        text_rr = _rr(records, "text", key)
        lines.append(
            f"| {label} | MRR | {statistics.mean(html_rr):.3f} | {statistics.mean(text_rr):.3f}"
            f" | {statistics.mean(text_rr) - statistics.mean(html_rr):+.3f} | — |"
        )
    return lines


def uncertainty_table(records: list[dict[str, Any]]) -> list[str]:
    lines = [
        "| Hit definition | Metric | HTML | Text | Δ text − html |",
        "|---|---|---:|---:|---:|",
    ]
    for label, key in DEFINITIONS:
        series = [
            (
                "recall@5",
                _hits(records, "html", key, 5),
                _hits(records, "text", key, 5),
            ),
            (
                "recall@10",
                _hits(records, "html", key, 10),
                _hits(records, "text", key, 10),
            ),
            ("MRR", _rr(records, "html", key), _rr(records, "text", key)),
        ]
        for metric, html, text in series:
            lines.append(
                f"| {label} | {metric} | {_fmt_ci(bootstrap_mean_ci(html))}"
                f" | {_fmt_ci(bootstrap_mean_ci(text))}"
                f" | {_fmt_ci(paired_bootstrap_delta(html, text), signed=True)} |"
            )
    return lines


def _evidence_paths(chunks: list[dict], snippets: list[str], k: int) -> list[str]:
    keys = [_match_key(s) for s in snippets]
    return [
        c["header_path"]
        for c in chunks[:k]
        if any(s in _match_key(c["text"]) for s in keys)
    ]


def html_miss_diagnosis(
    rows: list[dict[str, str]],
    retrievals: dict[tuple[str, str], dict[str, Any]],
    records: list[dict[str, Any]],
    k: int = 5,
) -> list[str]:
    """Split HTML snippet+Item misses at @k into label vs retrieval misses."""
    lines = [
        "| Row | Ticker | Miss kind | Expected Item path | Label on the top-5 chunk(s) holding the snippet | Snippet rank |",
        "|---|---|---|---|---|---:|",
    ]
    for index, (row, record) in enumerate(zip(rows, records)):
        html = record["html"]
        if html["format_rank"] is not None and html["format_rank"] <= k:
            continue
        chunks = normalize_chunks(
            retrievals[(row_id_for(row, index), "html")]["chunks"]
        )
        paths = _evidence_paths(chunks, expected_from_row(row)["answer_snippets"], k)
        if paths:
            kind = (
                "label: no Item (`_unknown`)"
                if all("Item" not in p for p in paths)
                else "label: wrong Item"
            )
        else:
            kind = "not in top 5"
        lines.append(
            f"| {record['row_id']} | {record['ticker']} | {kind}"
            f" | {' / '.join(f'`{p}`' for p in record['expected_header_paths'])}"
            f" | {', '.join(f'`{p}`' for p in dict.fromkeys(paths)) or '—'}"
            f" | {html['snippet_rank'] or '—'} |"
        )
    return lines


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Recall under two hit definitions")
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--raw", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)

    rows = load_dataset(args.dataset)
    retrievals = load_retrievals(args.raw)
    records = build_records(rows, retrievals)
    sections = [
        "## Headline",
        *headline_table(records),
        "",
        "## Uncertainty (95% row-bootstrap, same seed as report §5.1)",
        *uncertainty_table(records),
        "",
        "## HTML misses under snippet + Item at @5",
        *html_miss_diagnosis(rows, retrievals, records),
    ]
    text = "\n".join(sections) + "\n"
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(text, encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
