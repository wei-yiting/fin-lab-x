"""metrics.csv + factorial tables for the prompt x tool 2x2.

Per run: the model x reasoning benchmark's process metrics, the RAG
ablation's SEC path, and the tool-selection analysis's label-scored routing
metrics (``tool_selection.analyze.score_run``), plus two fields only this
design needs:

- *unknown-tool calls*: calls to a tool outside the arm's own toolset. Arm D
  keeps the reader prompt verbatim, and that prompt names
  ``sec_filing_search``.
- *SEC skip*: on rows where SEC 10-K is labelled 必要 and the row has no
  coverage gap (so the filing is reachable), the run called no SEC tool.
  ``sec_skip`` counts an attempted call (errored or unknown) as consulting
  SEC; ``sec_skip_no_success`` requires a SEC call that returned without
  error. A skip "at budget" is one in a run that hit the tool budget.

Every contrast takes per-row means over repetitions first, then a row-level
bootstrap 95% CI over the per-row contrast. With per-row cell means
``A, B, C, D`` (see ``run.py`` for the cell layout):

- prompt main effect  = ((D − A) + (B − C)) / 2
- tool main effect    = ((C − A) + (B − D)) / 2
- interaction         = (B − D) − (C − A)

Usage::

    python -m backend.evals.experiments.prompt_tool_2x2.analyze \\
        --raw-dir <out>/raw --labels <labels.csv> --out-dir <archive dir>
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import statistics
from collections import Counter
from collections.abc import Callable
from pathlib import Path
from typing import Any

from backend.agent_engine.agents.config_loader import ProfileConfigLoader
from backend.evals.experiments.model_reasoning_benchmark.analyze import (
    _bootstrap,
    _num,
    metrics_for,
    per_row_means,
)
from backend.evals.experiments.prompt_tool_2x2.run import (
    ARM_A,
    ARM_B,
    ARM_C,
    ARM_D,
    ARMS,
)
from backend.evals.experiments.rag_ablation.analyze import _paths, sec_path
from backend.evals.experiments.tool_selection.analyze import (
    GAP_FULL,
    GAP_NONE,
    REQUIRED,
    LabelSheet,
    load_labels,
    score_run,
)

ARM_ORDER = [ARM_A, ARM_B, ARM_C, ARM_D]
ARM_TAG = {ARM_A: "A", ARM_B: "B", ARM_C: "C", ARM_D: "D"}

ROUTING_KEYS = (
    "coverage_gap",
    "recall",
    "recall_success_only",
    "unnecessary",
    "unnecessary_calls",
    "ticker_accuracy",
    "entity_coverage",
    "entity_pair_share",
    "used_sec10k",
    "errored_only_sources",
)

# (metric, decimals, subset of runs it is defined on)
FACTORIAL_METRICS = [
    ("recall", 2, "routing"),
    ("unnecessary", 2, "routing"),
    ("sec_skip", 2, "sec_required"),
    ("sec_skip_no_success", 2, "sec_required"),
    ("sec_evidence_tokens", 0, "all"),
    ("tool_calls_total", 1, "all"),
    ("e2e_s", 1, "all"),
    ("est_cost_usd", 4, "all"),
]

Effect = Callable[[dict[str, float]], float]
EFFECTS: list[tuple[str, Effect]] = [
    ("tool, baseline prompt (C − A)", lambda m: m[ARM_C] - m[ARM_A]),
    ("tool, reader prompt (B − D)", lambda m: m[ARM_B] - m[ARM_D]),
    ("prompt, no search (D − A)", lambda m: m[ARM_D] - m[ARM_A]),
    ("prompt, with search (B − C)", lambda m: m[ARM_B] - m[ARM_C]),
    ("bundle (B − A)", lambda m: m[ARM_B] - m[ARM_A]),
    (
        "**prompt main effect**",
        lambda m: ((m[ARM_D] - m[ARM_A]) + (m[ARM_B] - m[ARM_C])) / 2,
    ),
    (
        "**tool main effect**",
        lambda m: ((m[ARM_C] - m[ARM_A]) + (m[ARM_B] - m[ARM_D])) / 2,
    ),
    (
        "**interaction**",
        lambda m: (m[ARM_B] - m[ARM_D]) - (m[ARM_C] - m[ARM_A]),
    ),
]


def arm_tools() -> dict[str, set[str]]:
    return {
        name: set(ProfileConfigLoader.load_from_dir(arm.config_dir).tools)
        for name, arm in ARMS.items()
    }


def run_metrics(
    record: dict[str, Any], sheet: LabelSheet, tools: dict[str, set[str]]
) -> dict[str, Any]:
    row = metrics_for(record)
    row["sec_path"] = sec_path(row)
    label = sheet.rows.get(record["row_id"])
    routing = score_run(record, label)
    row.update({key: routing[key] for key in ROUTING_KEYS})

    unknown = [
        c["tool"]
        for c in (record.get("output") or {}).get("tool_outputs") or []
        if c["tool"] not in tools[record["arm"]]
    ]
    row["unknown_tool_calls"] = len(unknown)
    row["unknown_tools"] = " ".join(sorted(set(unknown)))

    sec_required = (
        label is not None
        and label.labels["sec10k"] == REQUIRED
        and label.coverage_gap == GAP_NONE
    )
    sec_succeeded = (
        routing["used_sec10k"]
        and "sec10k" not in str(routing["errored_only_sources"]).split()
    )
    row["sec_required"] = sec_required
    row["sec_skip"] = (not routing["used_sec10k"]) if sec_required else ""
    row["sec_skip_no_success"] = (not sec_succeeded) if sec_required else ""
    row["sec_skip_at_budget"] = (
        (not routing["used_sec10k"] and row["reached_tool_budget"])
        if sec_required
        else ""
    )
    return row


def _subset(rows: list[dict[str, Any]], subset: str) -> list[dict[str, Any]]:
    if subset == "routing":
        return [r for r in rows if r["recall"] != "" and r["coverage_gap"] != GAP_FULL]
    if subset == "sec_required":
        return [r for r in rows if r["sec_required"]]
    return rows


def _row_ci(rows: list[dict[str, Any]], key: str) -> tuple[float, float, float] | None:
    means = per_row_means(rows, key)
    if not means:
        return None
    return _bootstrap({rid: v for (rid, _), v in means.items()}, statistics.mean)


def factorial(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for key, _, subset in FACTORIAL_METRICS:
        means = per_row_means(_subset(rows, subset), key)
        cells: dict[str, dict[str, float]] = {}
        for (rid, arm), value in means.items():
            cells.setdefault(rid, {})[arm] = value
        complete = {rid: m for rid, m in cells.items() if len(m) == len(ARM_ORDER)}
        out[key] = {"rows": len(complete), "signs": {}}
        for name, effect in EFFECTS:
            if complete:
                per_row = {rid: effect(m) for rid, m in complete.items()}
                out[key][name] = _bootstrap(per_row, statistics.mean)
                out[key]["signs"][name] = sign_test(list(per_row.values()))
    return out


def sign_test(values: list[float]) -> tuple[int, int, float]:
    """(rows < 0, rows > 0, exact two-sided sign-test p); ties dropped.

    A check on the bootstrap for rare-event metrics, where a handful of rows
    carry the whole contrast and a percentile CI can be optimistic.
    """
    neg = sum(1 for v in values if v < -1e-12)
    pos = sum(1 for v in values if v > 1e-12)
    n = neg + pos
    if n == 0:
        return neg, pos, 1.0
    tail = sum(math.comb(n, i) for i in range(min(neg, pos) + 1)) / 2**n
    return neg, pos, min(1.0, 2 * tail)


def summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    arms: dict[str, Any] = {}
    for arm in ARM_ORDER:
        arm_rows = [r for r in rows if r["arm"] == arm]
        if not arm_rows:
            continue
        sec_required = _subset(arm_rows, "sec_required")
        arms[arm] = {
            "runs": len(arm_rows),
            "task_errors": sum(1 for r in arm_rows if r["task_error"]),
            "health": _row_ci(arm_rows, "execution_health"),
            "sec_path_runs": dict(Counter(r["sec_path"] for r in arm_rows)),
            "hard_tool_errors_per_run": statistics.mean(
                r["tool_errors_hard"] for r in arm_rows
            ),
            "runs_at_tool_budget": sum(1 for r in arm_rows if r["reached_tool_budget"]),
            "unknown_tool_runs": sum(1 for r in arm_rows if r["unknown_tool_calls"]),
            "unknown_tool_calls": sum(r["unknown_tool_calls"] for r in arm_rows),
            "unknown_tools": sorted(
                {t for r in arm_rows for t in r["unknown_tools"].split()}
            ),
            "recall": _row_ci(_subset(arm_rows, "routing"), "recall"),
            "recall_success_only": _row_ci(
                _subset(arm_rows, "routing"), "recall_success_only"
            ),
            "unnecessary": _row_ci(_subset(arm_rows, "routing"), "unnecessary"),
            "entity_coverage": _row_ci(
                [r for r in arm_rows if r["entity_coverage"] != ""], "entity_coverage"
            ),
            "sec_required_runs": len(sec_required),
            "sec_skips": sum(1 for r in sec_required if r["sec_skip"]),
            "sec_skips_no_success": sum(
                1 for r in sec_required if r["sec_skip_no_success"]
            ),
            "sec_skips_at_budget": sum(
                1 for r in sec_required if r["sec_skip_at_budget"]
            ),
            "sec_skip_rows": dict(
                Counter(r["row_id"] for r in sec_required if r["sec_skip"])
            ),
            "sec_evidence_tokens": _row_ci(arm_rows, "sec_evidence_tokens"),
            "e2e_s": _row_ci(arm_rows, "e2e_s"),
            "est_cost_usd": _row_ci(arm_rows, "est_cost_usd"),
            "total_cost_usd": sum(_num(r["est_cost_usd"]) or 0.0 for r in arm_rows),
        }

    per_row = []
    for rid in sorted({r["row_id"] for r in rows}, key=int):
        entry: dict[str, Any] = {"row_id": rid}
        for arm in ARM_ORDER:
            cell = [r for r in rows if r["row_id"] == rid and r["arm"] == arm]
            tag = ARM_TAG[arm]
            entry[f"{tag}_paths"] = dict(Counter(r["sec_path"] for r in cell))
            entry[f"{tag}_sec_skips"] = sum(1 for r in cell if r["sec_skip"])
            entry["sec_required"] = any(r["sec_required"] for r in cell)
        per_row.append(entry)

    return {"arms": arms, "factorial": factorial(rows), "per_row": per_row}


def _ci(value: tuple[float, float, float] | None, digits: int, sign: str = "") -> str:
    if value is None:
        return "–"
    point, lo, hi = value
    fmt = f"{sign},.{digits}f"
    return f"{point:{fmt}} [{lo:{fmt}}, {hi:{fmt}}]"


def render_tables(summary: dict[str, Any]) -> str:
    arms = summary["arms"]
    lines = [
        "## Arms",
        "",
        "| Cell | Arm | Runs | Task errors | Health [95% CI] | SEC path (runs) "
        "| Hard tool errors/run | Runs at budget | Unknown-tool calls (runs) "
        "| Total cost USD |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]
    for arm, s in arms.items():
        unknown = f"{s['unknown_tool_calls']} ({s['unknown_tool_runs']})"
        if s["unknown_tools"]:
            unknown += " " + ", ".join(f"`{t}`" for t in s["unknown_tools"])
        lines.append(
            f"| {ARM_TAG[arm]} | {arm} | {s['runs']} | {s['task_errors']} "
            f"| {_ci(s['health'], 2)} | {_paths(s['sec_path_runs'])} "
            f"| {s['hard_tool_errors_per_run']:.2f} | {s['runs_at_tool_budget']} "
            f"| {unknown} | {s['total_cost_usd']:.2f} |"
        )
    lines += [
        "",
        "SEC path codes: S = search only, G = get_section only, S+G = both, "
        "∅ = neither.",
        "",
        "## Routing (label-scored) per arm",
        "",
        "| Cell | Arm | Routing recall | Recall (success only) | Unnecessary-call rate "
        "| Entity coverage | SEC skips / SEC-必要 runs | …no successful SEC call "
        "| Skips at budget | Skipped rows (runs) |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]
    for arm, s in arms.items():
        skip_rows = (
            " ".join(f"{rid}×{n}" for rid, n in sorted(s["sec_skip_rows"].items()))
            or "–"
        )
        lines.append(
            f"| {ARM_TAG[arm]} | {arm} | {_ci(s['recall'], 2)} "
            f"| {_ci(s['recall_success_only'], 2)} | {_ci(s['unnecessary'], 2)} "
            f"| {_ci(s['entity_coverage'], 2)} "
            f"| {s['sec_skips']} / {s['sec_required_runs']} "
            f"| {s['sec_skips_no_success']} | {s['sec_skips_at_budget']} "
            f"| {skip_rows} |"
        )
    lines += [
        "",
        "## Process means per arm (per-row means, row bootstrap 95% CI)",
        "",
        "| Cell | Arm | SEC evidence tokens | E2E s | Cost USD / run |",
        "|---|---|---|---|---|",
    ]
    for arm, s in arms.items():
        lines.append(
            f"| {ARM_TAG[arm]} | {arm} | {_ci(s['sec_evidence_tokens'], 0)} "
            f"| {_ci(s['e2e_s'], 1)} | {_ci(s['est_cost_usd'], 4)} |"
        )

    fac = summary["factorial"]
    lines += [
        "",
        "## Factorial readout (per-row contrast, row bootstrap 95% CI)",
        "",
        "Recall and unnecessary-call rate: rows without a full coverage gap. "
        "SEC skip: rows with SEC 10-K labelled 必要 and no coverage gap. "
        "Others: all rows.",
        "",
        "| Effect | "
        + " | ".join(f"Δ {k} ({fac[k]['rows']} rows)" for k, _, _ in FACTORIAL_METRICS)
        + " |",
        "|---|" + "---|" * len(FACTORIAL_METRICS),
    ]
    for name, _ in EFFECTS:
        lines.append(
            f"| {name} | "
            + " | ".join(_ci(fac[k].get(name), d, "+") for k, d, _ in FACTORIAL_METRICS)
            + " |"
        )

    routing_keys = [k for k, _, subset in FACTORIAL_METRICS if subset != "all"]
    lines += [
        "",
        "Exact sign test on the per-row contrasts (rows < 0 / rows > 0, ties "
        "dropped; two-sided p). A check on the bootstrap where few rows carry "
        "the contrast:",
        "",
        "| Effect | " + " | ".join(f"{k}" for k in routing_keys) + " |",
        "|---|" + "---|" * len(routing_keys),
    ]
    for name, _ in EFFECTS:
        cells = []
        for k in routing_keys:
            sign = fac[k]["signs"].get(name)
            cells.append(
                "–" if sign is None else f"{sign[0]} / {sign[1]} (p={sign[2]:.3f})"
            )
        lines.append(f"| {name} | " + " | ".join(cells) + " |")
    lines += [
        "",
        "## Per row: SEC path by cell (and SEC skips on SEC-必要 rows)",
        "",
        "| Row | SEC 必要 | A | B | C | D |",
        "|---|---|---|---|---|---|",
    ]
    for r in summary["per_row"]:
        cells = []
        for tag in "ABCD":
            cell = _paths(r[f"{tag}_paths"])
            if r["sec_required"] and r[f"{tag}_sec_skips"]:
                cell += f" (**skip×{r[f'{tag}_sec_skips']}**)"
            cells.append(cell)
        lines.append(
            f"| {r['row_id']} | {'yes' if r['sec_required'] else ''} | "
            + " | ".join(cells)
            + " |"
        )
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw-dir", type=Path, required=True)
    parser.add_argument("--labels", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args(argv)

    sheet = load_labels(args.labels)
    tools = arm_tools()
    records = [json.loads(p.read_text()) for p in sorted(args.raw_dir.rglob("*.json"))]
    rows = [run_metrics(r, sheet, tools) for r in records]
    rank = {arm: i for i, arm in enumerate(ARM_ORDER)}
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
    print(f"{len(rows)} runs -> {args.out_dir / 'metrics.csv'}, tables.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
