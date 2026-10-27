"""Analyze the before/after tool-error-message runs.

Per run (raw JSON written by ``harness.run_one``):

- *failed tool calls*: tool runs that raised.
- *wasted calls*: calls made in a later model turn than a permanent failure
  and covered by that failure's scope — same provider and ticker for
  ticker-level failures (20-F / no 10-K / unknown SEC ticker, Finnhub 403 /
  no data), same ticker + section (+ year) for a missing section, same
  ticker + year for a missing fiscal year. Calls the model issued in the same
  turn as the failure are never wasted: it had not seen the error yet.
  Failures are classified from the *raw* exception text the collector
  records (``tool_runs[].error``), which is identical in both arms; the
  message the model saw is not used.
- *used an acceptable alternative*: a successful call to one of the row's
  ``acceptable_alternatives`` in the same or a later turn than the first
  failure (anywhere in the run if nothing failed).
- *states the data gap*: ``GAP_RE`` keyword heuristic on the answer; every
  match is listed in ``gap_audit.md`` for hand-checking.
- execution health, E2E seconds, tool calls, input/output tokens, est. cost.

Per row: mean over repetitions per arm. Paired difference after − before per
row, row-level bootstrap 95% CI, reported for design, held-out, and control
rows separately.

Usage::

    python -m backend.evals.experiments.tool_error_messages.analyze \\
        --raw-dir <out>/raw --out-dir <archive dir>
"""

from __future__ import annotations

import argparse
import csv
import fnmatch
import json
import random
import re
import statistics
import sys
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from backend.evals.experiments.model_reasoning_benchmark.analyze import call_cost
from backend.evals.experiments.tool_error_messages.run import SCENARIO_DIR

MODEL = "gpt-5.6-luna"
ARMS = ("before", "after")
GROUPS = ("design", "heldout", "control")
BOOTSTRAP_SAMPLES = 10_000
BOOTSTRAP_SEED = 20261027
TAVILY_USD_PER_CREDIT = 0.008

# zh-TW part follows the tool-selection analysis' INSUFFICIENT_EVIDENCE_RE
# (feat/tool-selection-analysis); additions cover "doesn't exist yet / not
# filed / not supported / not covered" phrasings and English answers.
GAP_RE = re.compile(
    r"(證據|資料|數據|資訊)[^。\n]{0,4}(不足|有限|不夠)"
    r"|無法(取得|確認|驗證|查證|擷取|量化|提供|查詢|讀取|調閱)"
    r"|未能(取得|確認|找到|查到|讀取)"
    r"|沒有(取得|找到|查到|拿到)"
    r"|(查|找|拿)不到"
    r"|工具[^。\n]{0,6}(不支援|只支援|無法)"
    r"|(資料|數據|資訊)[^。\n]{0,6}限制"
    r"|(不|並未|沒有)(支援|涵蓋|提供|申報)"
    r"|尚未(申報|提交|發布|公布|出爐)"
    r"|不存在"
    r"|(?i:not available|unavailable|could ?n[o']t (?:retrieve|find|access|obtain|get)"
    r"|unable to (?:retrieve|find|access|obtain|get)|not covered|does ?n[o']t file"
    r"|no data|insufficient|not supported|doesn't exist|does not exist)"
)

_TICKER_LEVEL = [
    ("sec", re.compile(r"files 20-F|has no 10-K filings|not found on SEC EDGAR")),
    (
        "finnhub",
        re.compile(
            r"FinnhubAPIException\(status_code: 40[13]\)"
            r"|^No (quote data|basic financials) for ticker"
        ),
    ),
]
_SECTION_RE = re.compile(
    r"not found in \S+ 10-K FY|added by SEC in 2023|is not a valid 10-K item number"
)
_YEAR_RE = re.compile(
    r"filed yet for|filing history before|filing for \S+ in fiscal year"
)
_ITEM_PREFIX_RE = re.compile(r"^\s*item\s+", re.IGNORECASE)


@dataclass(frozen=True)
class Scope:
    """What a permanent failure rules out for the rest of the run."""

    kind: str  # "sec" | "finnhub" | "section" | "year"
    ticker: str
    section: str | None = None
    fiscal_year: int | None = None

    def covers(self, call: dict[str, Any]) -> bool:
        tool = call["tool"]
        if _ticker(call) != self.ticker:
            return False
        if self.kind == "finnhub":
            return tool.startswith("finnhub")
        if not tool.startswith("sec_filing"):
            return False
        if self.kind == "sec":
            return True
        year = _args(call).get("fiscal_year")
        if self.kind == "year":
            return year == self.fiscal_year
        return (
            tool == "sec_filing_get_section"
            and _section(call) == self.section
            and (year is None or self.fiscal_year is None or year == self.fiscal_year)
        )


def _args(call: dict[str, Any]) -> dict[str, Any]:
    args = call.get("args")
    return args if isinstance(args, dict) else {}


def _ticker(call: dict[str, Any]) -> str:
    return str(_args(call).get("ticker") or "").strip().upper()


def _section(call: dict[str, Any]) -> str:
    raw = str(_args(call).get("section_key") or "")
    return _ITEM_PREFIX_RE.sub("", raw.strip()).rstrip(".").strip().lower()


def permanent_scope(call: dict[str, Any]) -> Scope | None:
    """Scope of a failed call's permanent failure, or None (transient/other)."""
    error = call.get("error") or ""
    for kind, pattern in _TICKER_LEVEL:
        if pattern.search(error):
            return Scope(kind, _ticker(call))
    year = _args(call).get("fiscal_year")
    if _SECTION_RE.search(error):
        fy = re.search(r"FY(\d{4})", error)
        return Scope(
            "section",
            _ticker(call),
            section=_section(call),
            fiscal_year=int(fy.group(1)) if fy else year,
        )
    if _YEAR_RE.search(error):
        return Scope("year", _ticker(call), fiscal_year=year)
    return None


def _ordered(tool_runs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(tool_runs, key=lambda r: (r.get("turn", 0), r.get("start_seq", 0)))


def wasted_calls(tool_runs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    scopes: list[tuple[int, Scope]] = []
    wasted = []
    for call in _ordered(tool_runs):
        turn = call.get("turn", 0)
        if any(t < turn and s.covers(call) for t, s in scopes):
            wasted.append(call)
        if call.get("error"):
            scope = permanent_scope(call)
            if scope is not None:
                scopes.append((turn, scope))
    return wasted


def _matches_alternative(call: dict[str, Any], alternatives: Sequence[str]) -> bool:
    for alt in alternatives:
        pattern, _, ticker = alt.partition(":")
        if fnmatch.fnmatch(call["tool"], pattern) and (
            not ticker or _ticker(call) == ticker
        ):
            return True
    return False


def used_alternative(
    tool_runs: list[dict[str, Any]], alternatives: Sequence[str]
) -> bool:
    failed_turns = [c.get("turn", 0) for c in tool_runs if c.get("error")]
    first_failure = min(failed_turns) if failed_turns else -1
    return any(
        not c.get("error")
        and c.get("turn", 0) >= first_failure
        and _matches_alternative(c, alternatives)
        for c in tool_runs
    )


def gap_phrases(response: str) -> list[str]:
    return [m.group(0) for m in GAP_RE.finditer(response or "")]


def run_metrics(record: dict[str, Any], row: dict[str, str]) -> dict[str, Any]:
    tool_runs = record.get("tool_runs") or []
    llm_calls = record.get("llm_calls") or []
    output = record.get("output") or {}
    phrases = gap_phrases(str(output.get("response") or ""))
    alternatives = [a for a in row["acceptable_alternatives"].split("|") if a]
    tavily = sum(1 for c in tool_runs if c["tool"] == "tavily_financial_search")
    model_cost = sum(call_cost(MODEL, c) for c in llm_calls)
    return {
        "row_id": record["row_id"],
        "arm": record["arm"],
        "repetition": record["repetition"],
        "slot_in_row": record["slot_in_row"],
        "task_error": record.get("task_error"),
        "failed_calls": sum(1 for c in tool_runs if c.get("error")),
        "wasted_calls": len(wasted_calls(tool_runs)),
        "used_alternative": (
            float(used_alternative(tool_runs, alternatives)) if alternatives else None
        ),
        "states_gap": float(bool(phrases)),
        "gap_phrases": " | ".join(phrases),
        "execution_health": (record.get("scores") or {}).get(
            "diagnostic_execution_health"
        ),
        "e2e_s": (output.get("timing") or {}).get("total_s"),
        "tool_calls": len(tool_runs),
        "tavily_calls": tavily,
        "input_tokens": sum(c["input_tokens"] for c in llm_calls),
        "output_tokens": sum(c["output_tokens"] for c in llm_calls),
        "model_cost_usd": round(model_cost, 6),
        "est_cost_usd": round(model_cost + tavily * TAVILY_USD_PER_CREDIT, 6),
    }


METRICS: list[tuple[str, str]] = [
    ("failed_calls", "Failed tool calls / run"),
    ("wasted_calls", "Wasted calls / run"),
    ("used_alternative", "Used acceptable alternative (rate)"),
    ("states_gap", "Answer states the data gap (rate)"),
    ("execution_health", "Execution health"),
    ("e2e_s", "E2E s"),
    ("tool_calls", "Tool calls / run"),
    ("input_tokens", "Input tokens / run"),
    ("output_tokens", "Output tokens / run"),
    ("est_cost_usd", "Est. cost USD / run (model + Tavily)"),
]


def _mean(values: list[float | None]) -> float | None:
    present = [v for v in values if v is not None]
    return statistics.fmean(present) if present else None


def bootstrap_ci(
    values: list[float], stat: Callable[[list[float]], float] = statistics.fmean
) -> tuple[float, float, float] | None:
    if not values:
        return None
    rng = random.Random(BOOTSTRAP_SEED)
    samples = sorted(
        stat([rng.choice(values) for _ in values]) for _ in range(BOOTSTRAP_SAMPLES)
    )
    lo = samples[int(0.025 * BOOTSTRAP_SAMPLES)]
    hi = samples[int(0.975 * BOOTSTRAP_SAMPLES) - 1]
    return stat(values), lo, hi


def load_dataset() -> tuple[dict[str, dict[str, str]], dict[str, str]]:
    with (SCENARIO_DIR / "dataset.csv").open(encoding="utf-8") as fh:
        rows = {r["id"]: r for r in csv.DictReader(fh)}
    split = json.loads((SCENARIO_DIR / "split.json").read_text())
    group_of = {rid: g for g in GROUPS for rid in split[g]}
    return rows, group_of


def summarize(
    runs: list[dict[str, Any]], group_of: dict[str, str]
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    per_row: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for run in runs:
        per_row.setdefault((str(run["row_id"]), run["arm"]), []).append(run)
    row_ids = sorted({rid for rid, _ in per_row}, key=int)

    row_table = []
    for rid in row_ids:
        entry: dict[str, Any] = {"row_id": rid, "group": group_of[rid]}
        for arm in ARMS:
            reps = per_row.get((rid, arm), [])
            entry[f"{arm}_n"] = len(reps)
            for key, _ in METRICS:
                entry[f"{arm}_{key}"] = _mean([r[key] for r in reps])
        row_table.append(entry)

    summary: dict[str, Any] = {}
    for group in (*GROUPS, "all_error"):
        members = [
            r
            for r in row_table
            if r["group"] == group or (group == "all_error" and r["group"] != "control")
        ]
        group_summary: dict[str, Any] = {"rows": len(members)}
        for key, _ in METRICS:
            pairs = [
                (r[f"before_{key}"], r[f"after_{key}"])
                for r in members
                if r[f"before_{key}"] is not None and r[f"after_{key}"] is not None
            ]
            if not pairs:
                continue
            diff = bootstrap_ci([a - b for b, a in pairs])
            group_summary[key] = {
                "n_rows": len(pairs),
                "before_mean": statistics.fmean(b for b, _ in pairs),
                "after_mean": statistics.fmean(a for _, a in pairs),
                "diff_mean": diff[0] if diff else None,
                "diff_ci": [diff[1], diff[2]] if diff else None,
            }
        summary[group] = group_summary
    return row_table, summary


def _fmt(value: float | None, key: str) -> str:
    if value is None:
        return "–"
    if key in ("input_tokens", "output_tokens"):
        return f"{value:,.0f}"
    if key == "est_cost_usd":
        return f"{value:.4f}"
    return f"{value:.2f}"


def render_tables(summary: dict[str, Any], row_table: list[dict[str, Any]]) -> str:
    lines = []
    titles = {
        "design": "Design half (rows looked at while writing messages)",
        "heldout": "Held-out half",
        "control": "Controls (should not hit errors)",
        "all_error": "All error rows (design + held-out)",
    }
    for group in ("heldout", "design", "control", "all_error"):
        g = summary[group]
        lines += [
            f"### {titles[group]} — {g['rows']} rows",
            "",
            "| Metric | Before | After | After − Before [95% CI] |",
            "|---|---|---|---|",
        ]
        for key, label in METRICS:
            if key not in g:
                continue
            m = g[key]
            lo, hi = m["diff_ci"]
            lines.append(
                f"| {label} | {_fmt(m['before_mean'], key)} | "
                f"{_fmt(m['after_mean'], key)} | {_fmt(m['diff_mean'], key)} "
                f"[{_fmt(lo, key)}, {_fmt(hi, key)}] |"
            )
        lines.append("")
    lines += [
        "### Per row (rep means)",
        "",
        "| Row | Group | Failed B→A | Wasted B→A | Alt B→A | Gap B→A | Tool calls B→A |",
        "|---|---|---|---|---|---|---|",
    ]
    for r in row_table:
        cells = [
            f"{_fmt(r[f'before_{k}'], k)}→{_fmt(r[f'after_{k}'], k)}"
            for k in (
                "failed_calls",
                "wasted_calls",
                "used_alternative",
                "states_gap",
                "tool_calls",
            )
        ]
        lines.append(f"| {r['row_id']} | {r['group']} | " + " | ".join(cells) + " |")
    return "\n".join(lines) + "\n"


def render_gap_audit(runs: list[dict[str, Any]]) -> str:
    lines = [
        "# Data-gap heuristic audit",
        "",
        "Every run with the phrase(s) `GAP_RE` matched. Hand-check that each match "
        "states a data gap (not a topical use).",
        "",
        "| Row | Arm | Rep | Matched phrases |",
        "|---|---|---|---|",
    ]
    for r in sorted(runs, key=lambda r: (int(r["row_id"]), r["arm"], r["repetition"])):
        lines.append(
            f"| {r['row_id']} | {r['arm']} | {r['repetition']} | "
            f"{r['gap_phrases'] or '(none)'} |"
        )
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--raw-dir", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args(argv)

    rows, group_of = load_dataset()
    runs = []
    for path in sorted(args.raw_dir.glob("rep*/row*__*.json")):
        record = json.loads(path.read_text())
        runs.append(run_metrics(record, rows[str(record["row_id"])]))
    if not runs:
        raise SystemExit(f"No raw runs under {args.raw_dir}")

    args.out_dir.mkdir(parents=True, exist_ok=True)
    with (args.out_dir / "metrics.csv").open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(runs[0]))
        writer.writeheader()
        writer.writerows(runs)
    row_table, summary = summarize(runs, group_of)
    with (args.out_dir / "per_row.csv").open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(row_table[0]))
        writer.writeheader()
        writer.writerows(row_table)
    (args.out_dir / "summary.json").write_text(json.dumps(summary, indent=2))
    (args.out_dir / "tables.md").write_text(render_tables(summary, row_table))
    (args.out_dir / "gap_audit.md").write_text(render_gap_audit(runs))
    total = sum(r["est_cost_usd"] for r in runs)
    print(f"{len(runs)} runs, est. cost US${total:.2f} (model + Tavily)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
