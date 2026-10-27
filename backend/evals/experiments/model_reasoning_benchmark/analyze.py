"""metrics.csv + summary tables for the model x reasoning benchmark.

Every metric comes from code or the run's own record (domain events,
LangChain usage callbacks) — no LLM judge.

Aggregation respects the design: each (row, arm) cell has several
repetitions, so per-row means are computed first and arms are compared
across rows. Confidence intervals are row-level (cluster) bootstrap: rows
are resampled with replacement, keeping each row's repetitions together.

Usage::

    python -m backend.evals.experiments.model_reasoning_benchmark.analyze \\
        --raw-dir <out>/raw --out-dir <archive dir>
"""

from __future__ import annotations

import argparse
import csv
import json
import random
import re
import statistics
from collections import defaultdict
from pathlib import Path
from typing import Any

import tiktoken

from backend.evals.experiments.harness import SCENARIO_DIR
from backend.evals.experiments.model_reasoning_benchmark.run import ARM_NAMES

ALL_TOOLS = [
    "finnhub_stock_quote",
    "finnhub_company_basic_financials",
    "tavily_financial_search",
    "sec_filing_list_sections",
    "sec_filing_get_section",
    "sec_filing_search",
]
BUDGET_MARKER = "Per-run tool-call budget reached"

# USD per 1M tokens, list prices read 2026-10-21.
# - openai:gpt-5.6-luna — https://developers.openai.com/api/docs/models/gpt-5.6-luna
#   (reasoning tokens are billed as output tokens)
# - google_genai:gemini-3.6-flash — https://ai.google.dev/gemini-api/docs/pricing,
#   paid tier standard, rate valid through 2026-12-31; output includes thinking.
PRICES = {
    "gpt-5.6-luna": {"input": 0.20, "cached": 0.02, "output": 1.20},
    "gemini-3.6-flash": {"input": 0.75, "cached": 0.075, "output": 3.75},
}
# gpt-5.6-luna: a request with more than 272K input tokens is billed at 2x
# input and 1.5x output for the whole request (same OpenAI model page). Cost
# is therefore computed per model call; cached input is assumed to take the
# input multiplier too.
LONG_CONTEXT_TIERS = {"gpt-5.6-luna": (272_000, 2.0, 1.5)}


def call_cost(model: str, call: dict[str, Any]) -> float:
    price = PRICES[model]
    in_mult, out_mult = 1.0, 1.0
    tier = LONG_CONTEXT_TIERS.get(model)
    if tier and call["input_tokens"] > tier[0]:
        in_mult, out_mult = tier[1], tier[2]
    cached = call["cache_read_tokens"]
    return (
        (call["input_tokens"] - cached) * price["input"] * in_mult
        + cached * price["cached"] * in_mult
        + call["output_tokens"] * price["output"] * out_mult
    ) / 1_000_000


BOOTSTRAP_SAMPLES = 2000
BOOTSTRAP_SEED = 20261022

_ENCODER = tiktoken.get_encoding("cl100k_base")
_INLINE_RE = re.compile(r"(?<!^)\[(\d{1,3})\](?!:)", re.MULTILINE)
_DEF_RE = re.compile(r"^\s*\[(\d{1,3})\]:\s*\S", re.MULTILINE)
_CJK_RE = re.compile(r"[一-鿿]")


def _tokens(text: str) -> int:
    return len(_ENCODER.encode(text, disallowed_special=()))


def citation_check(response: str) -> dict[str, Any]:
    body = "\n".join(line for line in response.splitlines() if not _DEF_RE.match(line))
    inline = {int(n) for n in _INLINE_RE.findall(body)}
    defs = {int(n) for n in _DEF_RE.findall(response)}
    if not inline and not defs:
        return {"inline_markers": 0, "definitions": 0, "citation_bijective": ""}
    return {
        "inline_markers": len(inline),
        "definitions": len(defs),
        "citation_bijective": inline == defs,
    }


def metrics_for(record: dict[str, Any]) -> dict[str, Any]:
    output = record.get("output") or {}
    tool_outputs = output.get("tool_outputs") or []
    counts = {tool: 0 for tool in ALL_TOOLS}
    tokens_by_tool = {tool: 0 for tool in ALL_TOOLS}
    hard_errors = 0
    budget_blocked = 0
    for tool_output in tool_outputs:
        name = tool_output.get("tool", "unknown")
        counts[name] = counts.get(name, 0) + 1
        error = tool_output.get("error")
        text = error if error not in (None, "") else tool_output.get("result")
        text = text if isinstance(text, str) else json.dumps(text, ensure_ascii=False)
        if BUDGET_MARKER in (text or ""):
            budget_blocked += 1
        elif error not in (None, ""):
            hard_errors += 1
        tokens_by_tool[name] = tokens_by_tool.get(name, 0) + _tokens(text or "")

    llm_calls = record.get("llm_calls") or []
    input_tokens = sum(c["input_tokens"] for c in llm_calls)
    output_tokens = sum(c["output_tokens"] for c in llm_calls)
    cached_tokens = sum(c["cache_read_tokens"] for c in llm_calls)
    model = (output.get("model") or "").split(":", 1)[-1]
    cost = (
        round(sum(call_cost(model, call) for call in llm_calls), 5)
        if model in PRICES and llm_calls
        else ""
    )
    long_context_calls = sum(
        1
        for call in llm_calls
        if model in LONG_CONTEXT_TIERS
        and call["input_tokens"] > LONG_CONTEXT_TIERS[model][0]
    )

    details = record.get("score_details") or {}
    health = details.get("execution_health") or {}
    simplified = details.get("response_no_simplified_chars") or {}
    timing = output.get("timing") or {}
    usage = output.get("usage") or {}
    response = output.get("response") or ""

    return {
        "row_id": record["row_id"],
        "arm": record["arm"],
        "rep": record["repetition"],
        "model": output.get("model", ""),
        "slot_in_row": record["slot_in_row"],
        "started_at": record["started_at"],
        "finished_at": record["finished_at"],
        "task_error": record.get("task_error") or "",
        "execution_health": record["scores"].get("diagnostic_execution_health"),
        "execution_complete": health.get("execution_complete"),
        "tool_call_all_successful": health.get("tool_call_all_successful"),
        "tool_calls_total": len(tool_outputs),
        **{f"calls_{tool}": counts[tool] for tool in ALL_TOOLS},
        "tool_errors_hard": hard_errors,
        "budget_blocked_calls": budget_blocked,
        "reached_tool_budget": budget_blocked > 0 or len(tool_outputs) >= 10,
        "sec_evidence_tokens": tokens_by_tool["sec_filing_get_section"]
        + tokens_by_tool["sec_filing_search"],
        "all_tool_output_tokens": sum(tokens_by_tool.values()),
        "ttft_first_event_s": timing.get("first_event_s"),
        "first_text_s": timing.get("first_text_s"),
        "e2e_s": timing.get("total_s"),
        "llm_calls": len(llm_calls),
        "input_tokens": input_tokens,
        "cached_input_tokens": cached_tokens,
        "output_tokens": output_tokens,
        "reasoning_tokens": sum(c["reasoning_tokens"] for c in llm_calls),
        "finish_usage_input_tokens": usage.get("input_tokens", ""),
        "finish_usage_output_tokens": usage.get("output_tokens", ""),
        "est_cost_usd": cost,
        "long_context_priced_calls": long_context_calls,
        "response_chars": len(response),
        "response_cjk_chars": len(_CJK_RE.findall(response)),
        "no_simplified_chars_score": record["scores"].get(
            "response_no_simplified_chars", ""
        ),
        "simplified_genuine_changes": simplified.get("genuine_changes", ""),
        **citation_check(response),
    }


def _num(value: Any) -> float | None:
    if value in (None, ""):
        return None
    if isinstance(value, bool):
        return float(value)
    return float(value)


def per_row_means(rows: list[dict[str, Any]], key: str) -> dict[tuple[str, str], float]:
    """(row_id, arm) -> mean of ``key`` over that cell's repetitions."""
    cells: dict[tuple[str, str], list[float]] = defaultdict(list)
    for r in rows:
        value = _num(r[key])
        if value is not None:
            cells[(r["row_id"], r["arm"])].append(value)
    return {cell: statistics.mean(vals) for cell, vals in cells.items()}


def _bootstrap(values_by_row: dict[str, float], stat) -> tuple[float, float, float]:
    row_ids = sorted(values_by_row)
    point = stat([values_by_row[r] for r in row_ids])
    rng = random.Random(BOOTSTRAP_SEED)
    samples = sorted(
        stat([values_by_row[rng.choice(row_ids)] for _ in row_ids])
        for _ in range(BOOTSTRAP_SAMPLES)
    )
    lo = samples[int(0.025 * BOOTSTRAP_SAMPLES)]
    hi = samples[int(0.975 * BOOTSTRAP_SAMPLES) - 1]
    return point, lo, hi


def arm_summary(
    rows: list[dict[str, Any]], arm_names: list[str] = ARM_NAMES
) -> list[dict[str, Any]]:
    means = {
        key: per_row_means(rows, key)
        for key in [
            "execution_health",
            "e2e_s",
            "ttft_first_event_s",
            "tool_calls_total",
            "llm_calls",
            "input_tokens",
            "output_tokens",
            "reasoning_tokens",
            "est_cost_usd",
            "tool_errors_hard",
        ]
    }
    out = []
    for arm in arm_names:
        arm_rows = [r for r in rows if r["arm"] == arm]
        if not arm_rows:
            continue

        def by_row(key: str) -> dict[str, float]:
            return {rid: v for (rid, a), v in means[key].items() if a == arm}

        health = _bootstrap(by_row("execution_health"), statistics.mean)
        e2e = _bootstrap(by_row("e2e_s"), statistics.median)
        cost = _bootstrap(by_row("est_cost_usd"), statistics.mean)

        reps_by_row: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for r in arm_rows:
            reps_by_row[r["row_id"]].append(r)
        multi = {rid: reps for rid, reps in reps_by_row.items() if len(reps) > 1}
        health_agree = (
            sum(
                1
                for reps in multi.values()
                if len({r["execution_health"] for r in reps}) == 1
            )
            / len(multi)
            if multi
            else None
        )
        e2e_cv = [
            statistics.stdev(vals) / statistics.mean(vals)
            for reps in multi.values()
            if len(vals := [_num(r["e2e_s"]) for r in reps if _num(r["e2e_s"])]) > 1
        ]
        tool_sd = [
            statistics.stdev([r["tool_calls_total"] for r in reps])
            for reps in multi.values()
        ]
        costs = [_num(r["est_cost_usd"]) or 0.0 for r in arm_rows]
        out.append(
            {
                "arm": arm,
                "rows": len(reps_by_row),
                "runs": len(arm_rows),
                "task_errors": sum(1 for r in arm_rows if r["task_error"]),
                "health_mean": health[0],
                "health_ci": (health[1], health[2]),
                "median_e2e_s": e2e[0],
                "median_e2e_ci": (e2e[1], e2e[2]),
                "median_ttft_s": statistics.median(
                    by_row("ttft_first_event_s").values()
                ),
                "median_tool_calls": statistics.median(
                    by_row("tool_calls_total").values()
                ),
                "median_llm_calls": statistics.median(by_row("llm_calls").values()),
                "median_input_tokens": statistics.median(
                    by_row("input_tokens").values()
                ),
                "median_output_tokens": statistics.median(
                    by_row("output_tokens").values()
                ),
                "median_reasoning_tokens": statistics.median(
                    by_row("reasoning_tokens").values()
                ),
                "mean_cost_per_run": cost[0],
                "mean_cost_ci": (cost[1], cost[2]),
                "total_cost_usd": sum(costs),
                "hard_tool_errors_per_run": statistics.mean(
                    r["tool_errors_hard"] for r in arm_rows
                ),
                "runs_at_tool_budget": sum(
                    1 for r in arm_rows if r["reached_tool_budget"]
                ),
                "simplified_drift_runs": sum(
                    1 for r in arm_rows if _num(r["no_simplified_chars_score"]) == 0
                ),
                "health_same_across_reps": health_agree,
                "median_within_row_e2e_cv": statistics.median(e2e_cv)
                if e2e_cv
                else None,
                "median_within_row_tool_calls_sd": statistics.median(tool_sd)
                if tool_sd
                else None,
            }
        )
    return out


CONTRASTS = [
    ("reasoning, Luna", "luna_medium", "luna_none"),
    ("reasoning, Gemini", "gemini_medium", "gemini_minimal"),
    ("family, low tier", "gemini_minimal", "luna_none"),
    ("family, medium tier", "gemini_medium", "luna_medium"),
]


def paired_contrasts(
    rows: list[dict[str, Any]],
    contrasts: list[tuple[str, str, str]] = CONTRASTS,
) -> list[dict[str, Any]]:
    """Per-row paired differences (treatment − control) with bootstrap CIs."""
    out = []
    for label, treat, control in contrasts:
        entry: dict[str, Any] = {
            "contrast": label,
            "treatment": treat,
            "control": control,
        }
        for key in ["execution_health", "e2e_s", "est_cost_usd", "tool_calls_total"]:
            means = per_row_means(rows, key)
            diffs = {
                rid: means[(rid, treat)] - means[(rid, control)]
                for (rid, arm) in means
                if arm == treat and (rid, control) in means
            }
            if diffs:
                entry[key] = _bootstrap(diffs, statistics.mean)
        out.append(entry)
    return out


def by_source(rows: list[dict[str, Any]]) -> dict[str, dict[str, float]]:
    with open(SCENARIO_DIR / "dataset.csv", newline="") as f:
        source = {r["id"]: r["expected_best_source"] for r in csv.DictReader(f)}
    health = per_row_means(rows, "execution_health")
    out: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
    for (rid, arm), value in health.items():
        out[source[rid]][arm].append(value)
    return {
        src: {arm: statistics.mean(vals) for arm, vals in arms.items()}
        for src, arms in out.items()
    }


def _f(value: Any, digits: int = 1) -> str:
    if value in (None, ""):
        return "–"
    if isinstance(value, tuple):
        return f"[{value[0]:.{digits}f}, {value[1]:.{digits}f}]"
    if isinstance(value, float):
        return f"{value:.{digits}f}"
    return str(value)


def render_tables(summary: dict[str, Any], arm_names: list[str] = ARM_NAMES) -> str:
    lines = [
        "## Arm summary (per-row means over repetitions; 95% CI = row-level bootstrap)",
        "",
        "| Arm | Rows × reps | Task errors | Health mean [95% CI] | Median E2E s [95% CI] "
        "| Median TTFT s | Median tool calls | Median LLM calls | Median input tok "
        "| Median output tok | Median reasoning tok | Mean cost/run USD [95% CI] "
        "| Total cost USD | Hard tool errors/run | Runs at tool budget "
        "| Simplified-drift runs |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for s in summary["arms"]:
        lines.append(
            f"| {s['arm']} | {s['rows']} × {s['runs'] // max(s['rows'], 1)} "
            f"| {s['task_errors']} "
            f"| {_f(s['health_mean'], 2)} {_f(s['health_ci'], 2)} "
            f"| {_f(s['median_e2e_s'])} {_f(s['median_e2e_ci'])} "
            f"| {_f(s['median_ttft_s'])} | {_f(s['median_tool_calls'])} "
            f"| {_f(s['median_llm_calls'])} | {_f(s['median_input_tokens'], 0)} "
            f"| {_f(s['median_output_tokens'], 0)} "
            f"| {_f(s['median_reasoning_tokens'], 0)} "
            f"| {_f(s['mean_cost_per_run'], 4)} {_f(s['mean_cost_ci'], 4)} "
            f"| {_f(s['total_cost_usd'], 2)} | {_f(s['hard_tool_errors_per_run'], 2)} "
            f"| {s['runs_at_tool_budget']} | {s['simplified_drift_runs']} |"
        )
    lines += [
        "",
        "## Run-to-run variability (same row, same arm, different repetition)",
        "",
        "| Arm | Rows where health is identical across reps "
        "| Median within-row E2E CV | Median within-row SD of tool calls |",
        "|---|---|---|---|",
    ]
    for s in summary["arms"]:
        agree = s["health_same_across_reps"]
        lines.append(
            f"| {s['arm']} | {_f(agree * 100 if agree is not None else None, 0)}% "
            f"| {_f(s['median_within_row_e2e_cv'], 2)} "
            f"| {_f(s['median_within_row_tool_calls_sd'], 2)} |"
        )
    lines += [
        "",
        "## Paired contrasts (mean per-row difference, treatment − control, 95% CI)",
        "",
        "| Contrast | Treatment − control | Δ health | Δ E2E s | Δ cost/run USD "
        "| Δ tool calls |",
        "|---|---|---|---|---|---|",
    ]
    for c in summary["contrasts"]:

        def cell(key: str, digits: int) -> str:
            if key not in c:
                return "–"
            point, lo, hi = c[key]
            return f"{point:+.{digits}f} [{lo:+.{digits}f}, {hi:+.{digits}f}]"

        lines.append(
            f"| {c['contrast']} | {c['treatment']} − {c['control']} "
            f"| {cell('execution_health', 2)} | {cell('e2e_s', 1)} "
            f"| {cell('est_cost_usd', 4)} | {cell('tool_calls_total', 1)} |"
        )
    lines += [
        "",
        "## Health mean by expected best source",
        "",
        "| Source | " + " | ".join(arm_names) + " |",
        "|---|" + "---|" * len(arm_names),
    ]
    for src, arms in sorted(summary["health_by_source"].items()):
        lines.append(
            f"| {src} | " + " | ".join(_f(arms.get(a), 2) for a in arm_names) + " |"
        )
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw-dir", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args(argv)

    records = [json.loads(p.read_text()) for p in sorted(args.raw_dir.rglob("*.json"))]
    rank = {name: i for i, name in enumerate(ARM_NAMES)}
    rows = sorted(
        (metrics_for(r) for r in records),
        key=lambda r: (int(r["row_id"]), rank[r["arm"]], r["rep"]),
    )
    args.out_dir.mkdir(parents=True, exist_ok=True)
    with open(args.out_dir / "metrics.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    summary = {
        "arms": arm_summary(rows),
        "contrasts": paired_contrasts(rows),
        "health_by_source": by_source(rows),
    }
    (args.out_dir / "summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False, default=str)
    )
    (args.out_dir / "tables.md").write_text(render_tables(summary))
    print(f"{len(rows)} runs -> {args.out_dir / 'metrics.csv'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
