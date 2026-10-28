"""Paired analysis for the HTML-vs-text parsing A/B (DEV-138 / DEV-183).

Scores every (row, arm) retrieval with the unmodified OR-set
``sec_retrieval`` scorer — the HTML arm's chunks first pass through the
DEV-180 compatibility wrapper (``html_arm_compat.normalize_chunks``) — then
compares the arms row by row.

Statistics are row-level: each dataset row is one paired observation (both
arms answer the same question against the same filing), so confidence
intervals come from resampling rows with replacement and recomputing the
mean (per arm) or the mean paired delta (text − html). Recall@k is 0/1 per
row under OR-set scoring, so an exact McNemar test on the discordant pairs
is reported alongside. MAP equals MRR under OR-set scoring (one relevant
target per row) and is deliberately not reported as a separate metric.

Usage::

    python -m backend.evals.experiments.parsing_ab.analyze \\
        --dataset <dataset.csv> --raw <retrievals.jsonl> --out-dir <dir>
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import random
import re
import statistics
from collections import defaultdict
from pathlib import Path
from typing import Any

from backend.evals.scenarios.sec_retrieval.scorer import (
    header_path_recall_at_5,
    header_path_recall_at_10,
    mean_reciprocal_rank,
)
from backend.evals.scenarios.sec_retrieval_ab.html_arm_compat import normalize_chunks

ARMS = ("html", "text")
METRICS = ("recall_at_5", "recall_at_10", "mrr")
BREAKDOWN_COLUMNS = ("query_type", "detection_source", "ticker")
BOOTSTRAP_SAMPLES = 10_000
BOOTSTRAP_SEED = 20261028


def expected_from_row(row: dict[str, str]) -> dict[str, list[str]]:
    return {
        "header_paths": json.loads(row["expected_header_paths"]),
        "answer_snippets": json.loads(row["answer_snippets"]),
    }


def score_arm(
    arm: str, chunks: list[dict], expected: dict[str, list[str]]
) -> dict[str, Any]:
    if arm not in ARMS:
        raise ValueError(f"unknown arm {arm!r}; expected one of {ARMS}")
    scored = normalize_chunks(chunks) if arm == "html" else chunks
    output = {"retrieved_chunks": scored}
    mrr = mean_reciprocal_rank(output, expected, input=None).score
    return {
        "rank": round(1 / mrr) if mrr else None,
        "recall_at_5": header_path_recall_at_5(output, expected, input=None).score,
        "recall_at_10": header_path_recall_at_10(output, expected, input=None).score,
        "mrr": mrr,
    }


_TABLE_NOISE_RE = re.compile(r"\||-{3,}|\s+")


def _match_key(text: str) -> str:
    return _TABLE_NOISE_RE.sub("", text.lower())


def snippet_only_rank(chunks: list[dict], expected: dict[str, list[str]]) -> int | None:
    """Rank of the first chunk containing any expected snippet, ignoring paths.

    Diagnostic only: separates "the evidence was retrieved but labelled with a
    different Item" from "the evidence was not retrieved at all". Matching
    ignores case, whitespace and markdown table syntax (``|``, ``---``) on
    both arms alike, so a table-anchored snippet the HTML arm renders as a
    pipe table still counts as retrieved evidence here — the primary metrics
    keep the scorer's strict containment.
    """
    snippets = [_match_key(s) for s in expected["answer_snippets"]]
    for rank, chunk in enumerate(chunks, start=1):
        text = _match_key(chunk["text"])
        if any(s in text for s in snippets):
            return rank
    return None


def row_buckets(row: dict[str, Any], column: str) -> list[str]:
    """Bucket values a row belongs to; list-valued (OR-set) columns give a set."""
    value = row[column]
    if isinstance(value, list):
        return sorted(set(value))
    if isinstance(value, str) and value.startswith("["):
        return sorted(set(json.loads(value)))
    return [value]


def _bootstrap(rows: list[Any], stat: Any) -> tuple[float, float, float]:
    point = stat(rows)
    rng = random.Random(BOOTSTRAP_SEED)
    n = len(rows)
    samples = sorted(
        stat([rows[rng.randrange(n)] for _ in range(n)])
        for _ in range(BOOTSTRAP_SAMPLES)
    )
    lo = samples[int(0.025 * BOOTSTRAP_SAMPLES)]
    hi = samples[int(0.975 * BOOTSTRAP_SAMPLES) - 1]
    return point, lo, hi


def bootstrap_mean_ci(values: list[float]) -> tuple[float, float, float]:
    """Mean with a 95% percentile row-bootstrap interval."""
    return _bootstrap(values, statistics.mean)


def paired_bootstrap_delta(
    html: list[float], text: list[float]
) -> tuple[float, float, float]:
    """Mean paired delta (text − html) with a 95% row-bootstrap interval."""
    if len(html) != len(text):
        raise ValueError("paired arms must have one value per row each")
    return _bootstrap([t - h for h, t in zip(html, text)], statistics.mean)


def mcnemar_exact_p(html_only: int, text_only: int) -> float:
    """Two-sided exact McNemar (binomial on discordant pairs, p=0.5)."""
    n = html_only + text_only
    if n == 0:
        return 1.0
    k = min(html_only, text_only)
    tail = sum(math.comb(n, i) for i in range(k + 1)) / 2**n
    return min(1.0, 2 * tail)


def summarize_arms(records: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    summary: dict[str, dict[str, Any]] = {}
    for metric in METRICS:
        html = [r["html"][metric] for r in records]
        text = [r["text"][metric] for r in records]
        entry: dict[str, Any] = {
            "n": len(records),
            "html": bootstrap_mean_ci(html),
            "text": bootstrap_mean_ci(text),
            "delta": paired_bootstrap_delta(html, text),
        }
        if metric.startswith("recall"):
            html_only = sum(1 for h, t in zip(html, text) if h > t)
            text_only = sum(1 for h, t in zip(html, text) if t > h)
            entry["html_only_hits"] = html_only
            entry["text_only_hits"] = text_only
            entry["mcnemar_p"] = mcnemar_exact_p(html_only, text_only)
        summary[metric] = entry
    return summary


def snippet_recall_summary(records: list[dict[str, Any]]) -> dict[str, Any]:
    """Label-agnostic recall@10: was any expected snippet in the top 10 at all."""

    def hit(scores: dict[str, Any]) -> float:
        rank = scores["snippet_rank"]
        return 1.0 if rank is not None and rank <= 10 else 0.0

    html = [hit(r["html"]) for r in records]
    text = [hit(r["text"]) for r in records]
    return {
        "n": len(records),
        "html": bootstrap_mean_ci(html),
        "text": bootstrap_mean_ci(text),
        "delta": paired_bootstrap_delta(html, text),
    }


def degraded_html_filings(
    manifest: dict[str, Any], threshold: float = 0.5
) -> list[str]:
    """Tickers whose HTML-arm chunks are mostly ``_unknown`` (Item detection failed)."""
    degraded = []
    for key, entry in manifest["filings"].items():
        html = entry["html"]
        if (
            html.get("chunks")
            and html["items"].get("_unknown", 0) / html["chunks"] >= threshold
        ):
            degraded.append(key.split("/")[0])
    return sorted(degraded)


def breakdown(
    records: list[dict[str, Any]], column: str, metric: str
) -> list[dict[str, Any]]:
    """Per-bucket arm means; a row counts in every bucket it touches."""
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        for bucket in row_buckets(record, column):
            grouped[bucket].append(record)
    table = []
    for bucket in sorted(grouped, key=lambda b: (-len(grouped[b]), b)):
        rows = grouped[bucket]
        html = statistics.mean(r["html"][metric] for r in rows)
        text = statistics.mean(r["text"][metric] for r in rows)
        table.append({"bucket": bucket, "n": len(rows), "html": html, "text": text})
    return table


def row_id_for(row: dict[str, str], index: int) -> str:
    for column in ("id", "candidate_id", "row_id"):
        if row.get(column):
            return row[column]
    return f"row{index:02d}"


def ticker_for(row: dict[str, str]) -> str:
    return json.loads(row["expected_tickers"])[0]


def load_dataset(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def load_retrievals(path: Path) -> dict[tuple[str, str], dict[str, Any]]:
    out: dict[tuple[str, str], dict[str, Any]] = {}
    with path.open(encoding="utf-8") as f:
        for line in f:
            rec = json.loads(line)
            out[(rec["row_id"], rec["arm"])] = rec
    return out


def build_records(
    rows: list[dict[str, str]], retrievals: dict[tuple[str, str], dict[str, Any]]
) -> list[dict[str, Any]]:
    records = []
    for index, row in enumerate(rows):
        row_id = row_id_for(row, index)
        expected = expected_from_row(row)
        record: dict[str, Any] = {
            "row_id": row_id,
            "ticker": ticker_for(row),
            "question": row["question"],
            "query_type": row_buckets(row, "query_type"),
            "detection_source": row_buckets(row, "detection_source"),
            "expected_header_paths": expected["header_paths"],
        }
        for arm in ARMS:
            retrieval = retrievals[(row_id, arm)]
            if retrieval.get("error"):
                raise RuntimeError(
                    f"{row_id}/{arm} retrieval failed: {retrieval['error']}"
                )
            chunks = retrieval["chunks"]
            scores = score_arm(arm, chunks, expected)
            scores["snippet_rank"] = snippet_only_rank(chunks, expected)
            scored = normalize_chunks(chunks) if arm == "html" else chunks
            scores["top_paths"] = [c["header_path"] for c in scored[:3]]
            record[arm] = scores
        records.append(record)
    return records


def _fmt_ci(ci: tuple[float, float, float]) -> str:
    point, lo, hi = ci
    return f"{point:.3f} [{lo:.3f}, {hi:.3f}]"


def _fmt_delta(ci: tuple[float, float, float]) -> str:
    point, lo, hi = ci
    return f"{point:+.3f} [{lo:+.3f}, {hi:+.3f}]"


def _miss_kind(scores: dict[str, Any]) -> str:
    if scores["recall_at_10"]:
        return "hit"
    if scores["snippet_rank"] is not None:
        return "label-miss"
    return "retrieval-miss"


def _aggregate_rows(summary: dict[str, dict[str, Any]]) -> list[str]:
    lines = []
    for metric in METRICS:
        s = summary[metric]
        discordant = (
            f"{s['text_only_hits']} / {s['html_only_hits']}"
            if "mcnemar_p" in s
            else "—"
        )
        p = f"{s['mcnemar_p']:.3f}" if "mcnemar_p" in s else "—"
        lines.append(
            f"| {metric} | {_fmt_ci(s['html'])} | {_fmt_ci(s['text'])} | "
            f"{_fmt_delta(s['delta'])} | {discordant} | {p} |"
        )
    return lines


def render_tables(
    records: list[dict[str, Any]], degraded: list[str] | None = None
) -> str:
    header = [
        "| Metric | HTML (frozen) | Text | Δ text − html | text-only / html-only hits"
        " | McNemar exact p |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    lines = [
        "## Aggregate (95% row-bootstrap CI, "
        f"{BOOTSTRAP_SAMPLES:,} resamples, seed {BOOTSTRAP_SEED})",
        "",
        *header,
        *_aggregate_rows(summarize_arms(records)),
        "",
        f"n = {len(records)} rows. MAP is not reported: under OR-set scoring "
        "each row has one relevant target, so MAP equals MRR.",
        "",
    ]

    if degraded:
        kept = [r for r in records if r["ticker"] not in degraded]
        lines += [
            "## Sensitivity: filings with failed HTML Item detection excluded",
            "",
            f"Excluded tickers (≥50% of HTML-arm chunks labelled `_unknown`): "
            f"{', '.join(degraded)} — {len(records) - len(kept)} rows dropped.",
            "",
            *header,
            *_aggregate_rows(summarize_arms(kept)),
            "",
            f"n = {len(kept)} rows.",
            "",
        ]

    snippet = snippet_recall_summary(records)
    lines += [
        "## Sensitivity: label-agnostic recall@10 (snippet anywhere in top 10, "
        "case/whitespace/table-syntax insensitive)",
        "",
        "| HTML (frozen) | Text | Δ text − html |",
        "|---:|---:|---:|",
        f"| {_fmt_ci(snippet['html'])} | {_fmt_ci(snippet['text'])} | "
        f"{_fmt_delta(snippet['delta'])} |",
        "",
    ]

    for column in BREAKDOWN_COLUMNS:
        lines += [
            f"## Breakdown by {column} (recall@10 / MRR means; a row counts in "
            "every bucket it touches)",
            "",
            "| bucket | n | HTML r@10 | Text r@10 | HTML MRR | Text MRR |",
            "|---|---:|---:|---:|---:|---:|",
        ]
        r10 = breakdown(records, column, "recall_at_10")
        mrr = {e["bucket"]: e for e in breakdown(records, column, "mrr")}
        for e in r10:
            m = mrr[e["bucket"]]
            lines.append(
                f"| {e['bucket']} | {e['n']} | {e['html']:.3f} | {e['text']:.3f} | "
                f"{m['html']:.3f} | {m['text']:.3f} |"
            )
        lines.append("")

    lines += [
        "## Miss diagnosis (@10)",
        "",
        "`label-miss` = an expected snippet is inside a top-10 chunk (matched "
        "ignoring case, whitespace and table syntax), but the "
        "chunk's header_path does not start with any expected Item path; "
        "`retrieval-miss` = no top-10 chunk contains any expected snippet.",
        "",
        "| arm | hit | label-miss | retrieval-miss |",
        "|---|---:|---:|---:|",
    ]
    for arm in ARMS:
        kinds = [_miss_kind(r[arm]) for r in records]
        lines.append(
            f"| {arm} | {kinds.count('hit')} | {kinds.count('label-miss')} | "
            f"{kinds.count('retrieval-miss')} |"
        )
    lines.append("")

    lines += [
        "## Discordant rows (@10: one arm hits, the other misses)",
        "",
    ]
    discordant = [
        r for r in records if r["html"]["recall_at_10"] != r["text"]["recall_at_10"]
    ]
    if not discordant:
        lines += ["None.", ""]
    for r in discordant:
        winner = "text" if r["text"]["recall_at_10"] else "html"
        loser = "html" if winner == "text" else "text"
        lines += [
            f"### {r['row_id']} ({r['ticker']}, {', '.join(r['query_type'])}, "
            f"{', '.join(r['detection_source'])}) — {winner} hits, {loser} misses",
            "",
            f"- Question: {r['question']}",
            f"- Expected: {' | '.join(r['expected_header_paths'])}",
            f"- {winner} rank: {r[winner]['rank']}",
            f"- {loser} miss kind: {_miss_kind(r[loser])}"
            + (
                f" (snippet at rank {r[loser]['snippet_rank']})"
                if r[loser]["snippet_rank"]
                else ""
            ),
            f"- {loser} top-3 paths: " + " ‖ ".join(r[loser]["top_paths"]),
            "",
        ]
    return "\n".join(lines)


def write_per_row(records: list[dict[str, Any]], path: Path) -> None:
    fields = [
        "row_id",
        "ticker",
        "query_type",
        "detection_source",
        "html_rank",
        "text_rank",
        "html_snippet_rank",
        "text_snippet_rank",
        "html_mrr",
        "text_mrr",
        "html_miss_kind",
        "text_miss_kind",
        "question",
    ]
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for r in records:
            writer.writerow(
                {
                    "row_id": r["row_id"],
                    "ticker": r["ticker"],
                    "query_type": "|".join(r["query_type"]),
                    "detection_source": "|".join(r["detection_source"]),
                    "html_rank": r["html"]["rank"] or "",
                    "text_rank": r["text"]["rank"] or "",
                    "html_snippet_rank": r["html"]["snippet_rank"] or "",
                    "text_snippet_rank": r["text"]["snippet_rank"] or "",
                    "html_mrr": f"{r['html']['mrr']:.4f}",
                    "text_mrr": f"{r['text']['mrr']:.4f}",
                    "html_miss_kind": _miss_kind(r["html"]),
                    "text_miss_kind": _miss_kind(r["text"]),
                    "question": r["question"],
                }
            )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Analyze the parsing A/B run")
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--raw", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, default=None)
    args = parser.parse_args(argv)

    records = build_records(load_dataset(args.dataset), load_retrievals(args.raw))
    args.out_dir.mkdir(parents=True, exist_ok=True)
    write_per_row(records, args.out_dir / "per_row.csv")
    (args.out_dir / "summary.json").write_text(
        json.dumps(summarize_arms(records), indent=2) + "\n", encoding="utf-8"
    )
    degraded = (
        degraded_html_filings(json.loads(args.manifest.read_text(encoding="utf-8")))
        if args.manifest
        else None
    )
    tables = render_tables(records, degraded)
    (args.out_dir / "tables.md").write_text(tables + "\n", encoding="utf-8")
    print(tables)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
