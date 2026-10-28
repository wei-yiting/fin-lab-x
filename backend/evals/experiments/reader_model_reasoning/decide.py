"""Apply the pre-registered decision rule (see the archive's preregistration.md).

An arm is acceptable only if (1) its signal pass rate is non-inferior to
the control arm (paired Δ lower 95% CI bound > −0.03), (2) the judge passed
the discrimination check, and (3) routing recall is not materially worse
(paired Δ lower bound > −0.10). Among acceptable arms the cheapest wins;
if two acceptable arms' cost CIs overlap, the one with lower median E2E.

Usage::

    python -m backend.evals.experiments.reader_model_reasoning.decide \\
        --toolsel-metrics <toolsel>/metrics.csv \\
        --process-summary <archive>/summary.json \\
        --judge-summary <archive>/judge/judge_summary.json --out-dir <archive>
"""

from __future__ import annotations

import argparse
import csv
import json
import statistics
from collections import defaultdict
from pathlib import Path
from typing import Any

from backend.evals.experiments.model_reasoning_benchmark.analyze import _bootstrap
from backend.evals.experiments.reader_model_reasoning.run import (
    ARM_NAMES,
    CONTROL_ARM,
)

QUALITY_MARGIN = -0.03
ROUTING_MARGIN = -0.10


def routing_contrasts(path: Path) -> dict[str, tuple[float, float, float]]:
    cells: dict[tuple[str, str], list[float]] = defaultdict(list)
    with open(path, newline="") as f:
        for r in csv.DictReader(f):
            if r["recall"] in ("True", "False"):
                cells[(r["arm"], r["row_id"])].append(float(r["recall"] == "True"))
    means = {cell: statistics.mean(v) for cell, v in cells.items()}
    out = {}
    for arm in ARM_NAMES:
        if arm == CONTROL_ARM:
            continue
        diffs = {
            row: means[(arm, row)] - means[(CONTROL_ARM, row)]
            for (a, row) in means
            if a == arm and (CONTROL_ARM, row) in means
        }
        if diffs:
            out[arm] = _bootstrap(diffs, statistics.mean)
    return out


def decide(
    routing: dict[str, tuple[float, float, float]],
    process: dict[str, Any],
    judge: dict[str, Any],
) -> dict[str, Any]:
    arms = {a["arm"]: a for a in process["arms"]}
    discrimination = judge["discrimination_passed"]
    verdicts = {}
    for arm, quality in judge["contrasts_vs_control"].items():
        q_lo = quality["signal_pass_rate"][1]
        r = routing.get(arm)
        checks = {
            "quality_non_inferior": q_lo > QUALITY_MARGIN,
            "discrimination_passed": discrimination,
            "routing_not_worse": r is not None and r[1] > ROUTING_MARGIN,
        }
        verdicts[arm] = {
            "signal_pass_rate_delta": quality["signal_pass_rate"],
            "routing_recall_delta": r,
            "mean_cost_per_run": arms[arm]["mean_cost_per_run"],
            "mean_cost_ci": arms[arm]["mean_cost_ci"],
            "median_e2e_s": arms[arm]["median_e2e_s"],
            "checks": checks,
            "acceptable": all(checks.values()),
        }
    acceptable = sorted(
        (a for a, v in verdicts.items() if v["acceptable"]),
        key=lambda a: verdicts[a]["mean_cost_per_run"],
    )
    pick = acceptable[0] if acceptable else None
    if len(acceptable) > 1:
        first, second = verdicts[acceptable[0]], verdicts[acceptable[1]]
        if first["mean_cost_ci"][1] >= second["mean_cost_ci"][0]:
            pick = min(acceptable[:2], key=lambda a: verdicts[a]["median_e2e_s"])
    return {
        "control": CONTROL_ARM,
        "quality_margin": QUALITY_MARGIN,
        "routing_margin": ROUTING_MARGIN,
        "arms": verdicts,
        "acceptable": acceptable,
        "recommendation": pick or CONTROL_ARM,
        "recommendation_reason": (
            "lowest-cost acceptable arm"
            if pick
            else "no arm met every condition; stay on the control"
        ),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--toolsel-metrics", type=Path, required=True)
    parser.add_argument("--process-summary", type=Path, required=True)
    parser.add_argument("--judge-summary", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args(argv)

    result = decide(
        routing_contrasts(args.toolsel_metrics),
        json.loads(args.process_summary.read_text()),
        json.loads(args.judge_summary.read_text()),
    )
    args.out_dir.mkdir(parents=True, exist_ok=True)
    (args.out_dir / "decision.json").write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
