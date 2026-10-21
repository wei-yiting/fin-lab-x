"""Turn the raw per-run JSONs from ``run.py`` into metrics.csv + summaries.

Every metric is computed from code or the run's own record (domain events,
LangChain usage callbacks) — no LLM judge.

Usage::

    python -m backend.evals.experiments.agent_config_benchmark.analyze \\
        --raw-dir <out>/raw --out-dir <archive dir>
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import statistics
from pathlib import Path
from typing import Any

import tiktoken

from backend.evals.experiments.agent_config_benchmark.run import (
    ARM_A,
    ARM_B,
    ARMS,
    SCENARIO_DIR,
)

SEC_TOOLS = ["sec_filing_list_sections", "sec_filing_get_section", "sec_filing_search"]
ALL_TOOLS = [
    "finnhub_stock_quote",
    "finnhub_company_basic_financials",
    "tavily_financial_search",
    *SEC_TOOLS,
]
BUDGET_MARKER = "Per-run tool-call budget reached"

# USD per 1M tokens, list prices on 2026-10-21.
# - openai:gpt-5.6-luna — https://developers.openai.com/api/docs/models/gpt-5.6-luna
#   (reasoning tokens are billed as output tokens)
# - google_genai:gemini-3.6-flash — https://ai.google.dev/gemini-api/docs/pricing,
#   paid tier standard, rate valid through 2026-12-31; output includes thinking.
PRICES = {
    "gpt-5.6-luna": {"input": 0.20, "cached": 0.02, "output": 1.20},
    "gemini-3.6-flash": {"input": 0.75, "cached": 0.075, "output": 3.75},
}

_ENCODER = tiktoken.get_encoding("cl100k_base")
_INLINE_RE = re.compile(r"(?<!^)\[(\d{1,3})\](?!:)", re.MULTILINE)
_DEF_RE = re.compile(r"^\s*\[(\d{1,3})\]:\s*\S", re.MULTILINE)
_CJK_RE = re.compile(r"[一-鿿]")


def _tokens(text: str) -> int:
    return len(_ENCODER.encode(text, disallowed_special=()))


def _model_key(model_name: str) -> str:
    return model_name.split(":", 1)[-1]


def citation_check(response: str) -> dict[str, Any]:
    body_lines = [line for line in response.splitlines() if not _DEF_RE.match(line)]
    inline = {int(n) for n in _INLINE_RE.findall("\n".join(body_lines))}
    defs = {int(n) for n in _DEF_RE.findall(response)}
    if not inline and not defs:
        return {"inline_markers": 0, "definitions": 0, "citation_bijective": ""}
    return {
        "inline_markers": len(inline),
        "definitions": len(defs),
        "citation_bijective": inline == defs,
    }


def sec_path(counts: dict[str, int]) -> str:
    search = counts.get("sec_filing_search", 0) > 0
    section = counts.get("sec_filing_get_section", 0) > 0
    if search and section:
        return "both"
    if search:
        return "search_only"
    if section:
        return "get_section_only"
    return "neither"


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
        result = tool_output.get("result")
        error = tool_output.get("error")
        text = error if error not in (None, "") else result
        text = text if isinstance(text, str) else json.dumps(text, ensure_ascii=False)
        if BUDGET_MARKER in (text or ""):
            budget_blocked += 1
        elif error not in (None, ""):
            hard_errors += 1
        tokens_by_tool[name] = tokens_by_tool.get(name, 0) + _tokens(text or "")

    llm_calls = record.get("llm_calls") or []
    input_tokens = sum(c["input_tokens"] for c in llm_calls)
    output_tokens = sum(c["output_tokens"] for c in llm_calls)
    reasoning_tokens = sum(c["reasoning_tokens"] for c in llm_calls)
    cached_tokens = sum(c["cache_read_tokens"] for c in llm_calls)
    model = _model_key(output.get("model") or "")
    price = PRICES.get(model)
    cost = (
        round(
            (
                (input_tokens - cached_tokens) * price["input"]
                + cached_tokens * price["cached"]
                + output_tokens * price["output"]
            )
            / 1_000_000,
            5,
        )
        if price and llm_calls
        else ""
    )

    details = record.get("score_details") or {}
    health = details.get("execution_health") or {}
    simplified = details.get("response_no_simplified_chars") or {}
    timing = output.get("timing") or {}
    usage = output.get("usage") or {}
    response = output.get("response") or ""

    row = {
        "row_id": record["row_id"],
        "arm": record["arm"],
        "experiments": "+".join(record["experiments"]),
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
        "sec_path": sec_path(counts),
        "used_sec_filing_search": counts["sec_filing_search"] > 0,
        "tool_errors_hard": hard_errors,
        "budget_blocked_calls": budget_blocked,
        "hit_tool_budget": budget_blocked > 0 or len(tool_outputs) >= 10,
        "sec_evidence_tokens": tokens_by_tool["sec_filing_get_section"]
        + tokens_by_tool["sec_filing_search"],
        "get_section_tokens": tokens_by_tool["sec_filing_get_section"],
        "search_tokens": tokens_by_tool["sec_filing_search"],
        "list_sections_tokens": tokens_by_tool["sec_filing_list_sections"],
        "all_tool_output_tokens": sum(tokens_by_tool.values()),
        "ttft_first_event_s": timing.get("first_event_s"),
        "first_text_s": timing.get("first_text_s"),
        "e2e_s": timing.get("total_s"),
        "llm_calls": len(llm_calls),
        "input_tokens": input_tokens,
        "cached_input_tokens": cached_tokens,
        "output_tokens": output_tokens,
        "reasoning_tokens": reasoning_tokens,
        "finish_usage_input_tokens": usage.get("input_tokens", ""),
        "finish_usage_output_tokens": usage.get("output_tokens", ""),
        "est_cost_usd": cost,
        "response_chars": len(response),
        "response_cjk_chars": len(_CJK_RE.findall(response)),
        "no_simplified_chars_score": record["scores"].get(
            "response_no_simplified_chars", ""
        ),
        "simplified_genuine_changes": simplified.get("genuine_changes", ""),
        **citation_check(response),
    }
    return row


def _median(values: list[float]) -> float | str:
    values = [v for v in values if isinstance(v, (int, float))]
    return round(statistics.median(values), 2) if values else ""


def summarize_e2(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    summary = []
    for arm in ["luna_none", "luna_medium", "gemini_minimal", "gemini_medium"]:
        arm_rows = [r for r in rows if r["arm"] == arm]
        if not arm_rows:
            continue
        costs = [r["est_cost_usd"] for r in arm_rows if r["est_cost_usd"] != ""]
        summary.append(
            {
                "arm": arm,
                "runs": len(arm_rows),
                "execution_health_mean": round(
                    statistics.mean(r["execution_health"] or 0 for r in arm_rows), 2
                ),
                "task_errors": sum(1 for r in arm_rows if r["task_error"]),
                "tool_errors_hard_total": sum(r["tool_errors_hard"] for r in arm_rows),
                "runs_hitting_budget": sum(1 for r in arm_rows if r["hit_tool_budget"]),
                "median_tool_calls": _median([r["tool_calls_total"] for r in arm_rows]),
                "median_llm_calls": _median([r["llm_calls"] for r in arm_rows]),
                "median_ttft_s": _median([r["ttft_first_event_s"] for r in arm_rows]),
                "median_e2e_s": _median([r["e2e_s"] for r in arm_rows]),
                "median_input_tokens": _median([r["input_tokens"] for r in arm_rows]),
                "median_output_tokens": _median([r["output_tokens"] for r in arm_rows]),
                "median_reasoning_tokens": _median(
                    [r["reasoning_tokens"] for r in arm_rows]
                ),
                "total_cost_usd": round(sum(costs), 4) if costs else "",
                "simplified_drift_runs": sum(
                    1 for r in arm_rows if r["no_simplified_chars_score"] == 0
                ),
            }
        )
    return summary


def _fmt(value: Any, digits: int = 1) -> str:
    if value in (None, ""):
        return "–"
    if isinstance(value, bool):
        return "✓" if value else "✗"
    if isinstance(value, float):
        return f"{value:.{digits}f}"
    return str(value)


def _pair(a: dict | None, b: dict | None, key: str, digits: int = 1) -> str:
    return f"{_fmt((a or {}).get(key), digits)} / {_fmt((b or {}).get(key), digits)}"


def render_tables(summary: dict[str, Any]) -> str:
    """Markdown tables for report.md, generated so no number is hand-copied."""
    with open(SCENARIO_DIR / "dataset.csv", newline="") as f:
        sources = {r["id"]: r["expected_best_source"] for r in csv.DictReader(f)}

    lines = [
        "## E1 paired (A = luna_medium, no RAG / B = reader_luna_medium, RAG bundle)",
        "",
        "Cells are `A / B`.",
        "",
        "| Row | Expected source | SEC path | Tool calls | search calls | get_section calls "
        "| Hard tool errors | SEC evidence tokens | Input tokens | Output tokens "
        "| TTFT s | E2E s | Cost USD | Health | No-simplified | [N] bijective |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for pair in summary["e1_pairs"]:
        a, b = pair["A"], pair["B"]
        lines.append(
            f"| {pair['row_id']} | {sources.get(pair['row_id'], '')} "
            f"| {_pair(a, b, 'sec_path')} | {_pair(a, b, 'tool_calls_total')} "
            f"| {_pair(a, b, 'calls_sec_filing_search')} "
            f"| {_pair(a, b, 'calls_sec_filing_get_section')} "
            f"| {_pair(a, b, 'tool_errors_hard')} | {_pair(a, b, 'sec_evidence_tokens')} "
            f"| {_pair(a, b, 'input_tokens')} | {_pair(a, b, 'output_tokens')} "
            f"| {_pair(a, b, 'ttft_first_event_s')} | {_pair(a, b, 'e2e_s')} "
            f"| {_pair(a, b, 'est_cost_usd', 4)} | {_pair(a, b, 'execution_health')} "
            f"| {_pair(a, b, 'no_simplified_chars_score')} "
            f"| {_pair(a, b, 'citation_bijective')} |"
        )

    complete = [p for p in summary["e1_pairs"] if p["A"] and p["B"]]
    paths: dict[str, int] = {}
    for pair in complete:
        paths[pair["B"]["sec_path"]] = paths.get(pair["B"]["sec_path"], 0) + 1
    lines += [
        "",
        f"## E1 aggregate ({len(complete)} complete pairs)",
        "",
        "| Metric | A (no RAG) | B (RAG bundle) |",
        "|---|---|---|",
    ]
    for label, key, agg in [
        ("Median SEC evidence tokens", "sec_evidence_tokens", "median"),
        ("Median input tokens", "input_tokens", "median"),
        ("Median output tokens", "output_tokens", "median"),
        ("Median tool calls", "tool_calls_total", "median"),
        ("Median TTFT s", "ttft_first_event_s", "median"),
        ("Median E2E s", "e2e_s", "median"),
        ("Hard tool errors (sum)", "tool_errors_hard", "sum"),
        ("Total cost USD", "est_cost_usd", "sum"),
    ]:
        cells = []
        for side in ("A", "B"):
            values = [p[side][key] for p in complete if p[side][key] != ""]
            if agg == "median":
                cells.append(_fmt(_median(values)))
            else:
                cells.append(_fmt(round(sum(values), 4), 4 if "cost" in key else 0))
        lines.append(f"| {label} | {cells[0]} | {cells[1]} |")
    health = [
        sum(1 for p in complete if p[side]["execution_health"] == 1.0)
        for side in ("A", "B")
    ]
    lines.append(f"| Runs with health 1.0 | {health[0]} | {health[1]} |")
    lines.append(
        "| B's SEC path | – | "
        + ", ".join(f"{k}: {v}" for k, v in sorted(paths.items()))
        + " |"
    )

    lines += [
        "",
        "## E2 summary (dev 8 rows each, n=1)",
        "",
        "| Arm | Runs | Health mean | Task errors | Hard tool errors | Runs at tool budget "
        "| Median tool calls | Median LLM calls | Median TTFT s | Median E2E s "
        "| Median input tok | Median output tok | Median reasoning tok | Total cost USD "
        "| Simplified-drift runs |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for s in summary["e2"]:
        lines.append(
            f"| {s['arm']} | {s['runs']} | {_fmt(s['execution_health_mean'], 2)} "
            f"| {s['task_errors']} | {s['tool_errors_hard_total']} "
            f"| {s['runs_hitting_budget']} | {_fmt(s['median_tool_calls'])} "
            f"| {_fmt(s['median_llm_calls'])} | {_fmt(s['median_ttft_s'])} "
            f"| {_fmt(s['median_e2e_s'])} | {_fmt(s['median_input_tokens'], 0)} "
            f"| {_fmt(s['median_output_tokens'], 0)} "
            f"| {_fmt(s['median_reasoning_tokens'], 0)} "
            f"| {_fmt(s['total_cost_usd'], 4)} | {s['simplified_drift_runs']} |"
        )
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw-dir", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args(argv)

    records = [json.loads(p.read_text()) for p in sorted(args.raw_dir.glob("*.json"))]
    arm_rank = {name: i for i, name in enumerate(ARMS)}
    rows = sorted(
        (metrics_for(r) for r in records),
        key=lambda r: (int(r["row_id"]), arm_rank[r["arm"]]),
    )
    args.out_dir.mkdir(parents=True, exist_ok=True)
    with open(args.out_dir / "metrics.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    summary = {
        "e2": summarize_e2(rows),
        "e1_pairs": [
            {
                "row_id": row_id,
                "A": next(
                    (r for r in rows if r["row_id"] == row_id and r["arm"] == ARM_A),
                    None,
                ),
                "B": next(
                    (r for r in rows if r["row_id"] == row_id and r["arm"] == ARM_B),
                    None,
                ),
            }
            for row_id in sorted({r["row_id"] for r in rows}, key=int)
        ],
    }
    (args.out_dir / "summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False, default=str)
    )
    (args.out_dir / "tables.md").write_text(render_tables(summary))
    print(f"{len(rows)} runs -> {args.out_dir / 'metrics.csv'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
