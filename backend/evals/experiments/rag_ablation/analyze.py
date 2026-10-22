"""metrics.csv + summary tables for the RAG bundle ablation (A vs B).

Reuses the model x reasoning benchmark's per-run metrics and bootstrap;
adds what only the ablation needs: which SEC path each run took, and
paired B − A contrasts per row (repetitions averaged first), overall and
by the row's expected best source. Rows whose best source is Finnhub or
Tavily need no 10-K, so they are where A ≈ B is expected.

Usage::

    python -m backend.evals.experiments.rag_ablation.analyze \\
        --raw-dir <out>/raw --out-dir <archive dir>
"""

from __future__ import annotations

import argparse
import csv
import json
import statistics
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from backend.evals.experiments.harness import SCENARIO_DIR
from backend.evals.experiments.model_reasoning_benchmark.analyze import (
    _bootstrap,
    _f,
    _num,
    metrics_for,
    per_row_means,
)
from backend.evals.experiments.rag_ablation.run import ARM_A, ARM_B

CONTRAST_KEYS = [
    ("execution_health", 2),
    ("sec_evidence_tokens", 0),
    ("input_tokens", 0),
    ("output_tokens", 0),
    ("tool_calls_total", 1),
    ("ttft_first_event_s", 1),
    ("e2e_s", 1),
    ("est_cost_usd", 4),
]


def sec_path(row: dict[str, Any]) -> str:
    search = row["calls_sec_filing_search"] > 0
    section = row["calls_sec_filing_get_section"] > 0
    if search and section:
        return "both"
    if search:
        return "search_only"
    if section:
        return "get_section_only"
    return "neither"


def _sources() -> dict[str, str]:
    with open(SCENARIO_DIR / "dataset.csv", newline="") as f:
        return {r["id"]: r["expected_best_source"] for r in csv.DictReader(f)}


def contrasts(rows: list[dict[str, Any]], row_ids: set[str]) -> dict[str, Any]:
    out: dict[str, Any] = {"rows": len(row_ids)}
    for key, _ in CONTRAST_KEYS:
        means = per_row_means([r for r in rows if r["row_id"] in row_ids], key)
        diffs = {
            rid: means[(rid, ARM_B)] - means[(rid, ARM_A)]
            for rid in row_ids
            if (rid, ARM_A) in means and (rid, ARM_B) in means
        }
        if diffs:
            out[key] = _bootstrap(diffs, statistics.mean)
    return out


def summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    sources = _sources()
    all_ids = {r["row_id"] for r in rows}
    by_source: dict[str, set[str]] = defaultdict(set)
    for rid in all_ids:
        by_source[sources[rid]].add(rid)

    arms = {}
    for arm in (ARM_A, ARM_B):
        arm_rows = [r for r in rows if r["arm"] == arm]
        health = per_row_means(arm_rows, "execution_health")
        arms[arm] = {
            "runs": len(arm_rows),
            "task_errors": sum(1 for r in arm_rows if r["task_error"]),
            "health_mean": _bootstrap(
                {rid: v for (rid, _), v in health.items()}, statistics.mean
            ),
            "sec_path_runs": dict(Counter(r["sec_path"] for r in arm_rows)),
            "hard_tool_errors_per_run": statistics.mean(
                r["tool_errors_hard"] for r in arm_rows
            ),
            "runs_at_tool_budget": sum(1 for r in arm_rows if r["reached_tool_budget"]),
            "simplified_drift_runs": sum(
                1 for r in arm_rows if _num(r["no_simplified_chars_score"]) == 0
            ),
            "total_cost_usd": sum(_num(r["est_cost_usd"]) or 0.0 for r in arm_rows),
        }

    per_row = []
    for rid in sorted(all_ids, key=int):
        entry: dict[str, Any] = {"row_id": rid, "source": sources[rid]}
        for arm, tag in ((ARM_A, "A"), (ARM_B, "B")):
            cell = [r for r in rows if r["row_id"] == rid and r["arm"] == arm]
            if not cell:
                continue
            entry[f"{tag}_paths"] = dict(Counter(r["sec_path"] for r in cell))
            for key in (
                "sec_evidence_tokens",
                "e2e_s",
                "est_cost_usd",
                "execution_health",
            ):
                vals = [_num(r[key]) for r in cell if _num(r[key]) is not None]
                entry[f"{tag}_{key}"] = statistics.mean(vals) if vals else None
        per_row.append(entry)

    return {
        "arms": arms,
        "contrast_all": contrasts(rows, all_ids),
        "contrast_by_source": {
            src: contrasts(rows, ids) for src, ids in sorted(by_source.items())
        },
        "per_row": per_row,
    }


def _cell(contrast: dict[str, Any], key: str, digits: int) -> str:
    if key not in contrast:
        return "–"
    point, lo, hi = contrast[key]
    return f"{point:+,.{digits}f} [{lo:+,.{digits}f}, {hi:+,.{digits}f}]"


def _paths(paths: dict[str, int] | None) -> str:
    if not paths:
        return "–"
    short = {"search_only": "S", "get_section_only": "G", "both": "S+G", "neither": "∅"}
    return " ".join(f"{short[k]}×{v}" for k, v in sorted(paths.items()))


def render_tables(summary: dict[str, Any]) -> str:
    lines = [
        "## Arms",
        "",
        "| Arm | Runs | Task errors | Health mean [95% CI] | SEC path (runs) "
        "| Hard tool errors/run | Runs at tool budget | Simplified-drift runs "
        "| Total cost USD |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for arm, s in summary["arms"].items():
        point, lo, hi = s["health_mean"]
        lines.append(
            f"| {arm} | {s['runs']} | {s['task_errors']} "
            f"| {point:.2f} [{lo:.2f}, {hi:.2f}] | {_paths(s['sec_path_runs'])} "
            f"| {s['hard_tool_errors_per_run']:.2f} | {s['runs_at_tool_budget']} "
            f"| {s['simplified_drift_runs']} | {s['total_cost_usd']:.2f} |"
        )
    header = "| Rows | " + " | ".join(f"Δ {k}" for k, _ in CONTRAST_KEYS) + " |"
    lines += [
        "",
        "SEC path codes: S = search only, G = get_section only, S+G = both, ∅ = neither.",
        "",
        "## Paired contrast B − A (per-row means over repetitions; 95% CI = row bootstrap)",
        "",
        "| Subset " + header,
        "|---|---|" + "---|" * len(CONTRAST_KEYS),
    ]

    def contrast_line(name: str, c: dict[str, Any]) -> str:
        return (
            f"| {name} | {c['rows']} | "
            + " | ".join(_cell(c, k, d) for k, d in CONTRAST_KEYS)
            + " |"
        )

    lines.append(contrast_line("all rows", summary["contrast_all"]))
    for src, c in summary["contrast_by_source"].items():
        lines.append(contrast_line(f"source = {src}", c))
    lines += [
        "",
        "## Per row (means over repetitions; cells are A / B)",
        "",
        "| Row | Source | SEC path A | SEC path B | SEC tokens | E2E s | Cost USD | Health |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for r in summary["per_row"]:

        def ab(key: str, digits: int) -> str:
            return f"{_f(r.get('A_' + key), digits)} / {_f(r.get('B_' + key), digits)}"

        lines.append(
            f"| {r['row_id']} | {r['source']} | {_paths(r.get('A_paths'))} "
            f"| {_paths(r.get('B_paths'))} | {ab('sec_evidence_tokens', 0)} "
            f"| {ab('e2e_s', 1)} | {ab('est_cost_usd', 4)} "
            f"| {ab('execution_health', 2)} |"
        )
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw-dir", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args(argv)

    records = [json.loads(p.read_text()) for p in sorted(args.raw_dir.rglob("*.json"))]
    rank = {ARM_A: 0, ARM_B: 1}
    rows = []
    for record in records:
        row = metrics_for(record)
        row["sec_path"] = sec_path(row)
        rows.append(row)
    rows.sort(key=lambda r: (int(r["row_id"]), rank[r["arm"]], r["rep"]))

    args.out_dir.mkdir(parents=True, exist_ok=True)
    with open(args.out_dir / "metrics.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    summary = summarize(rows)
    (args.out_dir / "summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False, default=str)
    )
    (args.out_dir / "tables.md").write_text(render_tables(summary))
    print(f"{len(rows)} runs -> {args.out_dir / 'metrics.csv'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
