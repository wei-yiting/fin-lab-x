"""Summarize raw records into results.json + results.csv (per-run rows).

Usage: python -m backend.evals.experiments.language_middleware.analyze <archive_dir>

Reads ``<archive_dir>/raw/*.json`` (fresh run) or ``raw.jsonl.gz`` (archived).
"""

from __future__ import annotations

import csv
import gzip
import json
import math
import sys
from collections import Counter, defaultdict
from pathlib import Path

from backend.evals.experiments.language_middleware.scorer import score_answer

PRICE_IN, PRICE_CACHED, PRICE_OUT = 0.20e-6, 0.02e-6, 1.20e-6


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return (math.nan, math.nan)
    p = k / n
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return (round(centre - half, 3), round(centre + half, 3))


def fisher_two_sided(k1: int, n1: int, k2: int, n2: int) -> float:
    """Two-sided Fisher exact test on pass counts k1/n1 vs k2/n2."""
    total_pass, n = k1 + k2, n1 + n2

    def prob(a: int) -> float:
        return (
            math.comb(n1, a) * math.comb(n2, total_pass - a) / math.comb(n, total_pass)
        )

    observed = prob(k1)
    lo, hi = max(0, total_pass - n2), min(n1, total_pass)
    return round(
        sum(prob(a) for a in range(lo, hi + 1) if prob(a) <= observed * (1 + 1e-9)), 5
    )


def run_cost(usage: dict) -> float:
    total = 0.0
    for u in (usage or {}).values():
        cached = (u.get("input_token_details") or {}).get("cache_read", 0)
        total += (
            (u["input_tokens"] - cached) * PRICE_IN
            + cached * PRICE_CACHED
            + u["output_tokens"] * PRICE_OUT
        )
    return total


def main(archive: Path) -> None:
    raw_dir = archive / "raw"
    if raw_dir.is_dir():
        records = [
            json.loads(p.read_text()) for p in sorted(raw_dir.glob("[ABC]_*.json"))
        ]
    else:
        # Archived form: run.py's per-run JSONs packed one per line.
        with gzip.open(archive / "raw.jsonl.gz", "rt", encoding="utf-8") as f:
            records = [json.loads(line) for line in f]
    rows = []
    for r in records:
        # Re-score from the stored answer so every record uses the current scorer.
        s = score_answer(r.get("response"), r["expected_lang"])
        rows.append(
            {
                "arm": r["arm"],
                "qid": r["qid"],
                "rep": r["rep"],
                "expected_lang": r["expected_lang"],
                "pass": int(bool(s["pass"])),
                "detected": s["detected"],
                "sec_in_context": r.get("sec_in_context"),
                "error": r.get("error"),
                "latency_s": r["latency_s"],
                "cost_usd": round(run_cost(r.get("usage")), 5),
                "tools_called": "|".join(r.get("tools_called") or []),
            }
        )
    with open(archive / "results.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)

    summary: dict = {}
    by = defaultdict(list)
    for row in rows:
        by[(row["arm"], row["expected_lang"])].append(row)
        if row["expected_lang"] == "en" and row["sec_in_context"]:
            by[(row["arm"], "en_sec_in_context")].append(row)
    for (arm, group), rs in sorted(by.items()):
        k, n = sum(r["pass"] for r in rs), len(rs)
        failed_qids = Counter(r["qid"] for r in rs if not r["pass"])
        summary[f"{arm}/{group}"] = {
            "pass": k,
            "n": n,
            "rate": round(k / n, 3),
            "wilson95": wilson(k, n),
            "detected": dict(Counter(r["detected"] for r in rs)),
            "errors": sum(1 for r in rs if r["error"]),
            "questions_with_failures": dict(failed_qids),
            "questions_failing_any_rep": len(failed_qids),
        }
    for arm in sorted({r["arm"] for r in rows}):
        rs = [r for r in rows if r["arm"] == arm]
        summary[f"{arm}/cost"] = {
            "runs": len(rs),
            "total_usd": round(sum(r["cost_usd"] for r in rs), 3),
            "median_latency_s": sorted(r["latency_s"] for r in rs)[len(rs) // 2],
        }
    for a, b in (("A", "B"), ("C", "B"), ("A", "C")):
        x, y = summary.get(f"{a}/en"), summary.get(f"{b}/en")
        if x and y:
            summary[f"fisher_en_{a}_vs_{b}"] = fisher_two_sided(
                x["pass"], x["n"], y["pass"], y["n"]
            )
    (archive / "results.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False)
    )
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main(Path(sys.argv[1]))
