"""Count repeated identical failing tool calls in archived benchmark runs.

A call is a *repeat after error* when the same (tool, normalized args) pair
already returned a hard error earlier in the same run. Budget-blocked calls
(the RunBudgetMiddleware message) are not hard errors and are never keys.
Args are normalized by dropping None/empty values, stripping strings and
upper-casing ``ticker``; ``fiscal_year=None`` vs an explicit year stays
different, because the tool resolves them to different requests.

Usage::

    python -I diagnose_repeats.py --out per_run.csv ROUND=RAW_DIR [ROUND=RAW_DIR ...]

RAW_DIR holds ``rep*/row*__<arm>.json`` (an extracted ``raw.tar.gz``) or
``row*__<arm>.json`` directly (single-repetition rounds).
"""

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path

BUDGET_MARKER = "Per-run tool-call budget reached"
BUDGET = 10


def normalize(args):
    out = {}
    for key, value in sorted((args or {}).items()):
        if value is None or value == "":
            continue
        if isinstance(value, str):
            value = value.strip().upper() if key == "ticker" else value.strip()
        out[key] = value
    return json.dumps(out, sort_keys=True, ensure_ascii=False)


def run_metrics(path):
    record = json.loads(path.read_text())
    calls = (record.get("output") or {}).get("tool_outputs") or []
    failed, repeats, blocked, hard = set(), [], 0, 0
    for call in calls:
        error = call.get("error") or ""
        if BUDGET_MARKER in error:
            blocked += 1
            continue
        key = (call["tool"], normalize(call.get("args")))
        if key in failed:
            repeats.append(f"{key[0]}({key[1]})")
        if error:
            hard += 1
            failed.add(key)
    tickers = {(c.get("args") or {}).get("ticker") for c in calls} - {None}
    stem = path.stem
    return {
        "row_id": stem.split("__")[0].removeprefix("row").lstrip("0"),
        "arm": record.get("arm") or stem.split("__", 1)[1],
        "rep": record.get("repetition", 1),
        "tool_calls_total": len(calls),
        "hard_tool_errors": hard,
        "budget_blocked_calls": blocked,
        # analyze.py's definition: blocked, or used the whole budget.
        "reached_tool_budget": blocked > 0 or len(calls) >= BUDGET,
        "repeat_failing_calls": len(repeats),
        "repeat_examples": "; ".join(repeats),
        "distinct_tickers": len(tickers),
        "health": (record.get("scores") or {}).get("diagnostic_execution_health"),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("rounds", nargs="+", help="ROUND=RAW_DIR")
    parser.add_argument("--out", required=True)
    ns = parser.parse_args()
    rows = []
    for spec in ns.rounds:
        name, raw = spec.split("=", 1)
        paths = sorted(Path(raw).glob("rep*/row*.json")) or sorted(Path(raw).glob("row*.json"))
        rows += [{"round": name, **run_metrics(p)} for p in paths]
    with open(ns.out, "w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    groups = defaultdict(list)
    for r in rows:
        groups[(r["round"], r["arm"])].append(r)
    print("| Round | Arm | Runs | Runs w/ hard error | Runs w/ repeat after error | Repeat calls | "
          "Runs at budget | …of which blocked | Budget runs w/ repeat | Budget runs w/ ≥2 tickers |")
    print("|---|---|---|---|---|---|---|---|---|---|")
    for (rnd, arm), rs in groups.items():
        at = [r for r in rs if r["reached_tool_budget"]]
        print(f"| {rnd} | {arm} | {len(rs)} | {sum(1 for r in rs if r['hard_tool_errors'])} "
              f"| {sum(1 for r in rs if r['repeat_failing_calls'])} | {sum(r['repeat_failing_calls'] for r in rs)} "
              f"| {len(at)} | {sum(1 for r in at if r['budget_blocked_calls'])} "
              f"| {sum(1 for r in at if r['repeat_failing_calls'])} | {sum(1 for r in at if r['distinct_tickers'] >= 2)} |")


if __name__ == "__main__":
    main()
