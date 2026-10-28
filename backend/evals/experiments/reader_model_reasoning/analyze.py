"""metrics.csv + summary tables for the reader model x reasoning 2x2.

Same per-run metrics, aggregation (per-row means over repetitions first)
and row-level bootstrap CIs as ``model_reasoning_benchmark.analyze``; this
module adds the SEC path each run took, citation integrity per arm, and
contrasts against the control arm ``reader_luna_medium``.

Usage::

    python -m backend.evals.experiments.reader_model_reasoning.analyze \\
        --raw-dir <out>/raw --out-dir <archive dir>
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path
from typing import Any

from backend.evals.experiments.model_reasoning_benchmark.analyze import (
    arm_summary,
    by_source,
    metrics_for,
    paired_contrasts,
    render_tables,
)
from backend.evals.experiments.rag_ablation.analyze import sec_path
from backend.evals.experiments.reader_model_reasoning.run import (
    ARM_NAMES,
    CONTROL_ARM,
)

CONTRASTS = [
    ("vs control: Luna, no reasoning", "reader_luna_none", CONTROL_ARM),
    ("vs control: Gemini minimal", "reader_gemini_minimal", CONTROL_ARM),
    ("vs control: Gemini medium", "reader_gemini_medium", CONTROL_ARM),
    ("reasoning, Gemini", "reader_gemini_medium", "reader_gemini_minimal"),
    ("family, low tier", "reader_gemini_minimal", "reader_luna_none"),
]


def citation_summary(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    out = {}
    for arm in ARM_NAMES:
        arm_rows = [r for r in rows if r["arm"] == arm]
        cited = [r for r in arm_rows if r["citation_bijective"] != ""]
        out[arm] = {
            "runs": len(arm_rows),
            "runs_with_citations": len(cited),
            "bijective": sum(1 for r in cited if r["citation_bijective"] is True),
            "sec_path_runs": dict(Counter(r["sec_path"] for r in arm_rows)),
        }
    return out


def render_extra(summary: dict[str, Any]) -> str:
    lines = [
        "",
        "## Citations and SEC path",
        "",
        "| Arm | Runs | Runs with [N] citations | Bijective (inline ↔ defs) "
        "| SEC path (runs) |",
        "|---|---|---|---|---|",
    ]
    for arm, c in summary["citations"].items():
        paths = ", ".join(f"{k} {v}" for k, v in sorted(c["sec_path_runs"].items()))
        lines.append(
            f"| {arm} | {c['runs']} | {c['runs_with_citations']} "
            f"| {c['bijective']} | {paths} |"
        )
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw-dir", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args(argv)

    records = [json.loads(p.read_text()) for p in sorted(args.raw_dir.rglob("*.json"))]
    rank = {name: i for i, name in enumerate(ARM_NAMES)}
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

    summary = {
        "arms": arm_summary(rows, ARM_NAMES),
        "contrasts": paired_contrasts(rows, CONTRASTS),
        "health_by_source": by_source(rows),
        "citations": citation_summary(rows),
    }
    (args.out_dir / "summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False, default=str)
    )
    (args.out_dir / "tables.md").write_text(
        render_tables(summary, ARM_NAMES) + render_extra(summary)
    )
    print(f"{len(rows)} runs -> {args.out_dir / 'metrics.csv'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
