"""Summarise the final-answer replay ablation.

Usage:
  python -m backend.evals.experiments.language_replay.analyze \
      data/experiment-archives/2026-10-29-language-replay
"""

from __future__ import annotations

import collections
import csv
import gzip
import json
import sys
from math import comb
from pathlib import Path
from typing import Any

from backend.evals.experiments.language_middleware.analyze import run_cost, wilson

ORDER = ["P0", "R0", "R2", "R3", "M"]
PAIRS = [
    ("P0", "R0"),
    ("R0", "R2"),
    ("R2", "R3"),
    ("R0", "M"),
    ("R0", "R3"),
    ("M", "R3"),
]


def mcnemar_exact(b: int, c: int) -> float:
    n = b + c
    if n == 0:
        return 1.0
    tail = sum(comb(n, i) for i in range(min(b, c) + 1)) / 2**n
    return min(1.0, 2 * tail)


def load(archive: Path) -> list[dict[str, Any]]:
    raw_dir = archive / "raw"
    if raw_dir.exists():
        return [json.loads(p.read_text()) for p in sorted(raw_dir.glob("*.json"))]
    with gzip.open(archive / "raw.jsonl.gz", "rt") as f:
        return [json.loads(line) for line in f]


def main(archive: Path) -> None:
    rows = [r for r in load(archive) if r["error"] is None]
    errors = [r for r in load(archive) if r["error"] is not None]
    by_key: dict[tuple, dict[str, bool]] = collections.defaultdict(dict)
    results: dict[str, Any] = {"errors": len(errors)}
    for r in rows:
        by_key[(r["qid"], r["orig_rep"], r["rep"], r["expected_lang"])][
            r["condition"]
        ] = r["score"]["pass"]

    for cond in ORDER:
        for lang in ("en", "zh-Hant"):
            sel = [
                r for r in rows if r["condition"] == cond and r["expected_lang"] == lang
            ]
            if not sel:
                continue
            k = sum(r["score"]["pass"] for r in sel)
            lo, hi = wilson(k, len(sel))
            fails = collections.Counter(
                r["score"]["detected"] for r in sel if not r["score"]["pass"]
            )
            fail_q = sorted({r["qid"] for r in sel if not r["score"]["pass"]})
            results[f"{cond}/{lang}"] = {
                "pass": k,
                "n": len(sel),
                "rate": round(k / len(sel), 4),
                "ci95": [round(lo, 4), round(hi, 4)],
                "failure_languages": dict(fails),
                "questions_with_failure": fail_q,
            }
        results[f"{cond}/cost_usd"] = round(
            sum(run_cost(r["usage"]) for r in rows if r["condition"] == cond), 3
        )

    for a, b in PAIRS:
        for lang in ("en",):
            pairs = [v for k, v in by_key.items() if k[3] == lang and a in v and b in v]
            only_a = sum(1 for v in pairs if v[a] and not v[b])
            only_b = sum(1 for v in pairs if v[b] and not v[a])
            results[f"mcnemar_{lang}_{a}_vs_{b}"] = {
                "n_pairs": len(pairs),
                f"pass_only_{a}": only_a,
                f"pass_only_{b}": only_b,
                "p_exact": round(mcnemar_exact(only_a, only_b), 4),
            }

    # Replay fidelity: R0 regenerates the recorded final call with the recorded
    # prompt and evidence, so it should agree with the recorded answer's language.
    r0 = [r for r in rows if r["condition"] == "R0"]
    agree = sum(r["score"]["pass"] == r["recorded_pass"] for r in r0)
    rec_fail = [r for r in r0 if not r["recorded_pass"]]
    rec_pass = [r for r in r0 if r["recorded_pass"]]
    results["fidelity_R0"] = {
        "n": len(r0),
        "pass_agreement": agree,
        "recorded_failures": len(rec_fail),
        "recorded_failures_still_fail": sum(not r["score"]["pass"] for r in rec_fail),
        "recorded_passes": len(rec_pass),
        "recorded_passes_now_fail": sum(not r["score"]["pass"] for r in rec_pass),
        "recorded_en_pass": sum(
            r["recorded_pass"] for r in r0 if r["expected_lang"] == "en"
        ),
        "recorded_en_n": sum(r["expected_lang"] == "en" for r in r0),
    }
    results["forced_no_tools"] = collections.Counter(
        r["condition"] for r in rows if r.get("forced_no_tools")
    )
    results["total_cost_usd"] = round(sum(run_cost(r["usage"]) for r in rows), 3)
    (archive / "results.json").write_text(
        json.dumps(results, indent=2, ensure_ascii=False)
    )

    with (archive / "results.csv").open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(
            [
                "condition",
                "qid",
                "orig_rep",
                "rep",
                "expected_lang",
                "detected",
                "pass",
                "recorded_detected",
                "recorded_pass",
                "n_tool_calls",
                "cost_usd",
            ]
        )
        for r in sorted(
            rows,
            key=lambda r: (
                ORDER.index(r["condition"]),
                r["qid"],
                r["orig_rep"],
                r["rep"],
            ),
        ):
            w.writerow(
                [
                    r["condition"],
                    r["qid"],
                    r["orig_rep"],
                    r["rep"],
                    r["expected_lang"],
                    r["score"]["detected"],
                    r["score"]["pass"],
                    r["recorded_detected"],
                    r["recorded_pass"],
                    r["n_tool_calls"],
                    round(run_cost(r["usage"]), 5),
                ]
            )
    print(json.dumps(results, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main(Path(sys.argv[1]))
