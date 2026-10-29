"""Deterministic leak score for the off-target distractor eval.

A run "leaks" when its answer names a company that the fixture labels place
only in unrelated sentences (``leak_companies``): in C1 the answer could have
taken it from the evidence, in C0 that evidence was removed, so C0 mentions
measure what the model brings in on its own. This is a mention signal, not a
relevance verdict: a mention the answer genuinely needs still counts.

A run is "exposed" when the replay served at least one fixture call whose
C1 results contain a deleted sentence (same definition for both conditions,
so C0 exposure means "would have seen it under C1").
"""

from __future__ import annotations

import argparse
import json
import math
import re
from collections import defaultdict
from pathlib import Path
from typing import Any

from backend.evals.experiments.off_target_distractor.fixtures import FIXTURE_PATH

# canonical -> surface forms searched in the (Traditional Chinese) answer.
ALIASES = {
    "Bank of America": ["Bank of America", "BofA", "美國銀行", "美銀"],
    "Baird": ["Baird"],
    "SK Hynix": ["SK Hynix", "Hynix", "海力士"],
    "Seagate": ["Seagate", "希捷"],
    "Western Digital": ["Western Digital", "威騰"],
    "AMD": ["AMD", "Advanced Micro", "超微"],
    "Altera": ["Altera"],
    "DeepSeek": ["DeepSeek", "深度求索"],
    "Fairchild Semiconductor": ["Fairchild", "快捷半導體"],
    "GlobalFoundries": ["GlobalFoundries", "格羅方德", "格芯"],
    "Google": ["Google", "Alphabet", "谷歌"],
    "Meta": ["Meta", "Facebook", "臉書"],
    "Microsoft": ["Microsoft", "微軟"],
    "Rapidus": ["Rapidus"],
    "SoftBank": ["SoftBank", "軟銀"],
    "Xilinx": ["Xilinx", "賽靈思"],
    "Apple": ["Apple", "蘋果"],
    "Nvidia": ["Nvidia", "NVIDIA", "輝達", "英偉達"],
    "OneTrust": ["OneTrust", "Onetrust"],
    "ByteDance": ["ByteDance", "Bytedance", "TikTok", "字節跳動", "抖音"],
    "Spotify": ["Spotify"],
    "Coca-Cola": [
        "Coca-Cola",
        "Coca Cola",
        "可口可樂",
        "Europacific",
        "HBC",
        "Hellenic",
    ],
    "Elliott Management": ["Elliott", "艾略特"],
    "OpenAI": ["OpenAI"],
    "PepsiCo": ["PepsiCo", "Pepsi", "百事"],
    "Sam's Club": ["Sam's Club", "Sam’s Club", "山姆會員", "山姆俱樂部"],
    "BJ's Wholesale": ["BJ's", "BJ’s"],
    "Netflix": ["Netflix", "網飛", "奈飛"],
    "Intel": ["Intel", "英特爾"],
    "Huawei": ["Huawei", "華為"],
    "TechInsights": ["TechInsights"],
    "Amazon": ["Amazon", "亞馬遜"],
    "Anthropic": ["Anthropic"],
    "Bessemer": ["Bessemer"],
    "BP": ["BP", "英國石油"],
    "LVMH": ["LVMH", "路威酩軒"],
    "Blue Owl": ["Blue Owl"],
    "UBS": ["UBS", "瑞銀"],
    "Anglo American": ["Anglo American", "英美資源"],
    "De Beers": ["De Beers", "戴比爾斯"],
}


def canonical(name: str) -> str:
    low = name.lower()
    for canon, forms in ALIASES.items():
        if any(f.lower() in low for f in forms if f.isascii()):
            return canon
    return name


def mentions(text: str, canon: str) -> list[str]:
    hits = []
    for form in ALIASES.get(canon, [canon]):
        if form.isascii():
            pattern = rf"(?<![A-Za-z]){re.escape(form)}(?![A-Za-z])"
            if re.search(pattern, text, flags=0 if form.isupper() else re.IGNORECASE):
                hits.append(form)
        elif form in text:
            hits.append(form)
    return hits


def _exact_two_sided(k: int, n: int) -> float:
    """Exact binomial (p=0.5) two-sided p-value, for McNemar / sign tests."""
    if n == 0:
        return 1.0
    tail = sum(math.comb(n, i) for i in range(0, min(k, n - k) + 1)) / 2**n
    return min(1.0, 2 * tail)


def score(raw_dir: Path) -> dict[str, Any]:
    fixtures = json.loads(FIXTURE_PATH.read_text())
    rows_fx = fixtures["rows"]
    packet_sent = {}  # per row: set of fixture call indices whose C1 results carry deleted text
    for row_id, fx in rows_fx.items():
        hot = set()
        for i, (c1, c0) in enumerate(zip(fx["C1"], fx["C0"])):
            if any(
                a["content"] != b["content"]
                for a, b in zip(c1["results"], c0["results"])
            ):
                hot.add(i)
        packet_sent[row_id] = hot

    runs = []
    for path in sorted(raw_dir.glob("rep*/row*__C*.json")):
        rec = json.loads(path.read_text())
        row_id = rec["row_id"]
        fx = rows_fx[row_id]
        leak_set = sorted(
            {canonical(c) for c in fx["leak_companies"]}
            - {canonical(t) for t in fx["target_companies"]}
        )
        response = (rec.get("output") or {}).get("response") or ""
        found = {c: mentions(response, c) for c in leak_set}
        found = {c: h for c, h in found.items() if h}
        served = {s["fixture_call"] for s in rec.get("tavily_replay") or []}
        runs.append(
            {
                "row": row_id,
                "rep": rec["repetition"],
                "condition": rec["condition"],
                "task_error": rec["task_error"],
                "tavily_calls": len(rec.get("tavily_replay") or []),
                "exposed": bool(served & packet_sent[row_id]),
                "leak_set": leak_set,
                "leaked": found,
                "leak": bool(found),
                "response_chars": len(response),
            }
        )

    def rate(rs):
        return (sum(r["leak"] for r in rs), len(rs))

    by_cond = {c: [r for r in runs if r["condition"] == c] for c in ("C0", "C1")}
    exposed_pairs = defaultdict(dict)
    all_pairs = defaultdict(dict)
    for r in runs:
        all_pairs[(r["row"], r["rep"])][r["condition"]] = r
    for key, pair in all_pairs.items():
        if "C0" in pair and "C1" in pair and pair["C1"]["exposed"]:
            exposed_pairs[key] = pair

    def mcnemar(pairs):
        b = sum(p["C1"]["leak"] and not p["C0"]["leak"] for p in pairs.values())
        c = sum(p["C0"]["leak"] and not p["C1"]["leak"] for p in pairs.values())
        return {
            "pairs": len(pairs),
            "c1_only_leak": b,
            "c0_only_leak": c,
            "p_exact": _exact_two_sided(min(b, c), b + c),
        }

    per_row = {}
    for row_id in sorted({r["row"] for r in runs}, key=int):
        rr = [r for r in runs if r["row"] == row_id]
        per_row[row_id] = {
            "leak_set": rr[0]["leak_set"],
            "C0": rate([r for r in rr if r["condition"] == "C0"]),
            "C1": rate([r for r in rr if r["condition"] == "C1"]),
            "C1_exposed": sum(r["exposed"] for r in rr if r["condition"] == "C1"),
        }
    up = sum(
        v["C1"][0] / v["C1"][1] > v["C0"][0] / v["C0"][1] for v in per_row.values()
    )
    down = sum(
        v["C1"][0] / v["C1"][1] < v["C0"][0] / v["C0"][1] for v in per_row.values()
    )
    return {
        "n_runs": len(runs),
        "errors": sum(bool(r["task_error"]) for r in runs),
        "leak_rate": {c: rate(rs) for c, rs in by_cond.items()},
        "exposure_C1": rate([{"leak": r["exposed"]} for r in by_cond["C1"]]),
        "mcnemar_all_pairs": mcnemar(
            {k: v for k, v in all_pairs.items() if len(v) == 2}
        ),
        "mcnemar_exposed_pairs": mcnemar(exposed_pairs),
        "row_sign_test": {
            "rows_c1_higher": up,
            "rows_c0_higher": down,
            "p_exact": _exact_two_sided(min(up, down), up + down),
        },
        "per_row": per_row,
        "runs": runs,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw-dir", type=Path, required=True)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    result = score(args.raw_dir)
    if args.out:
        args.out.write_text(json.dumps(result, indent=1, ensure_ascii=False))
    summary = {k: v for k, v in result.items() if k != "runs"}
    print(json.dumps(summary, indent=1, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
