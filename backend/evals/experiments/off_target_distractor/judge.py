"""Blinded off-target judge (functional rubric) + known-bad controls.

``build`` writes shuffled batch files with every answer from both conditions
plus control items (a C0 answer with one injected sentence carrying an
unrelated company's news, drawn from that row's deleted spans); condition
and control status live only in the key file. Each batch is graded by a
fresh, context-free Claude Code subagent that writes ``results/<batch>.json``.
``score`` joins verdicts to the key.

Subcommands: ``build``, ``score``.
"""

from __future__ import annotations

import argparse
import json
import random
from pathlib import Path
from typing import Any

from backend.evals.experiments.off_target_distractor.run import RECAP_TEMPLATE
from backend.evals.experiments.off_target_distractor.score import _exact_two_sided

SEED = 20261029
BATCH = 16

# One injected sentence per row, translated from a sentence the labels mark
# unrelated_other in that row's fixture.
CONTROL_SENTENCES = {
    "1": "另外，美國銀行本週公布的每股盈餘不如預期，股價走低；Baird 認為這波賣壓過頭，視為買進機會。",
    "7": "此外，Apple 可能因 App Store 違反《數位市場法》面臨更多罰款，歐盟先前已在 Spotify 案中對其開罰 18 億歐元。",
    "10": "另外，歐盟近期突擊搜查多家飲料公司，調查可口可樂在歐洲的裝瓶商是否限制跨境貿易。",
    "24": "此外，Anthropic 是 Bessemer 創立 116 年來最大的一筆投資。",
    "26": "另外，BP 宣布削減再生能源投資，並將每年油氣支出提高到 100 億美元。",
    "27": "另外，UBS 仍須籌措約 200 億美元的新資本，與瑞士政府的資本爭議已延續多年。",
    "29": "另外，安哥拉正尋求取得 Anglo American 旗下鑽石事業 De Beers 20% 至 30% 的股權。",
}

PROMPT = """You are grading answers from a financial research assistant. Answers are in Traditional Chinese. Each item gives the user's question, the company or companies the user asked about (TARGET), and the ANSWER.

Rubric (functional criterion). Every part of the answer should serve the user's question about the TARGET. Content about another company or the broader market is acceptable only when it directly supports the answer to the question that was asked — e.g. a peer comparison or market context that helps explain the TARGET's situation on the aspect the question asks about. Content about another company that stands on its own — that company's own news, results, deals or regulatory matters with no stated link to what the question asks about the TARGET — is OFF-TARGET, regardless of length. Mentioning another company only to say it is unrelated is fine. Data sources, analysts or media cited as the source of a statement are not "another company".

For each item:
1. List every statement in the answer that is about a company other than the TARGET (skip statements that only name a source). Quote or closely paraphrase it.
2. Label each "supports" or "off_target", with a short reason.
3. verdict = "N" if any statement is off_target, else "Y".

Grade every item on its own; do not compare items.

Output: write a JSON array, one object per item in batch order, to the result path given below:
[{"id": "J001", "statements": [{"text": "...", "company": "...", "label": "supports", "reason": "..."}], "verdict": "Y"}, ...]
Every item must appear exactly once. Write the JSON file only; reply "done" when written."""


def _answers(raw_dir: Path) -> list[dict[str, Any]]:
    out = []
    for path in sorted(raw_dir.glob("*/rep*/row*__C*.json")):
        rec = json.loads(path.read_text())
        out.append(
            {
                "arm": path.parts[-3],
                "row": rec["row_id"],
                "rep": rec["repetition"],
                "condition": rec["condition"],
                "answer": (rec.get("output") or {}).get("response") or "",
            }
        )
    return out


def _inject(answer: str, sentence: str) -> str:
    # Before the sources block when there is one, so the sentence sits in the body.
    for marker in ("\n資料來源", "\n參考來源", "\n來源", "\n[1]:"):
        i = answer.find(marker)
        if i > 0:
            return answer[:i].rstrip() + "\n\n" + sentence + "\n" + answer[i:]
    return answer.rstrip() + "\n\n" + sentence


def _question(row: dict[str, Any], arm: str) -> str:
    if arm.endswith("__recap"):
        return RECAP_TEMPLATE.format(companies=" 和 ".join(row["target_companies"]))
    return row["question_zh"]


def cmd_build(raw_dir: Path, fixtures: Path, out_dir: Path, key_dir: Path) -> int:
    rows = json.loads(fixtures.read_text())["rows"]
    answers = _answers(raw_dir)
    items = [{**a, "kind": "real"} for a in answers]
    for row_id, sentence in CONTROL_SENTENCES.items():
        base = [
            a
            for a in answers
            if a["row"] == row_id
            and a["condition"] == "C0"
            and a["arm"] == "reader_luna_medium"
        ]
        if not base:
            continue
        b = sorted(base, key=lambda a: a["rep"])[0]
        items.append(
            {
                **b,
                "kind": "control_injected",
                "answer": _inject(b["answer"], sentence),
                "injected": sentence,
            }
        )
    rng = random.Random(SEED)
    rng.shuffle(items)
    out_dir.mkdir(parents=True, exist_ok=True)
    key_dir.mkdir(parents=True, exist_ok=True)
    key = {}
    for b in range(0, len(items), BATCH):
        chunk = items[b : b + BATCH]
        name = f"batch_{b // BATCH + 1:02d}"
        lines = [f"# {name}\n"]
        for i, it in enumerate(chunk):
            jid = f"J{b + i + 1:03d}"
            key[jid] = {k: v for k, v in it.items() if k != "answer"}
            target = ", ".join(rows[it["row"]]["target_companies"])
            lines.append(
                f"## {jid}\n\nQUESTION: {_question(rows[it['row']], it['arm'])}\n\nTARGET: {target}\n\nANSWER:\n\n{it['answer']}\n"
            )
        (out_dir / f"{name}.md").write_text("\n".join(lines), encoding="utf-8")
    (key_dir / "judge_key.json").write_text(
        json.dumps(key, indent=1, ensure_ascii=False)
    )
    (out_dir / "PROMPT.md").write_text(PROMPT, encoding="utf-8")
    print(f"items={len(items)} batches={(len(items) + BATCH - 1) // BATCH}")
    return 0


def cmd_score(results_dir: Path, key_path: Path, out: Path | None) -> int:
    key = json.loads(key_path.read_text())
    verdicts = {}
    for path in sorted(results_dir.glob("batch_*.json")):
        for v in json.loads(path.read_text()):
            verdicts[v["id"]] = v
    missing = sorted(set(key) - set(verdicts))
    real: dict[str, dict[str, list[bool]]] = {}
    pairs: dict[tuple[str, str, int], dict[str, bool]] = {}
    controls = []
    for jid, k in key.items():
        if jid not in verdicts:
            continue
        off = verdicts[jid]["verdict"] == "N"
        if k["kind"] == "real":
            real.setdefault(k["arm"], {"C0": [], "C1": []})[k["condition"]].append(off)
            pairs.setdefault((k["arm"], k["row"], k["rep"]), {})[k["condition"]] = off
        else:
            controls.append(
                {
                    "id": jid,
                    "row": k["row"],
                    "flagged": off,
                    "flagged_statements": [
                        s
                        for s in verdicts[jid]["statements"]
                        if s["label"] == "off_target"
                    ],
                }
            )
    mcnemar = {}
    for arm in real:
        full = [p for (a, _, _), p in pairs.items() if a == arm and len(p) == 2]
        b = sum(p["C1"] and not p["C0"] for p in full)
        c = sum(p["C0"] and not p["C1"] for p in full)
        mcnemar[arm] = {
            "pairs": len(full),
            "c1_only": b,
            "c0_only": c,
            "p_exact": _exact_two_sided(min(b, c), b + c),
        }
    result = {
        "missing": missing,
        "off_target_rate": {
            arm: {c: [sum(v), len(v)] for c, v in d.items()} for arm, d in real.items()
        },
        "mcnemar": mcnemar,
        "control_tpr": [sum(x["flagged"] for x in controls), len(controls)],
        "controls": controls,
        "off_target_items": [
            {
                "id": jid,
                **{
                    k: v
                    for k, v in key[jid].items()
                    if k in ("arm", "row", "rep", "condition")
                },
                "statements": [
                    s for s in verdicts[jid]["statements"] if s["label"] == "off_target"
                ],
            }
            for jid in sorted(verdicts)
            if key[jid]["kind"] == "real" and verdicts[jid]["verdict"] == "N"
        ],
    }
    if out:
        out.write_text(json.dumps(result, indent=1, ensure_ascii=False))
    print(
        json.dumps(
            {
                k: v
                for k, v in result.items()
                if k not in ("controls", "off_target_items")
            },
            indent=1,
        )
    )
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build")
    b.add_argument("--raw-dir", type=Path, required=True)
    b.add_argument("--fixtures", type=Path, required=True)
    b.add_argument("--out-dir", type=Path, required=True)
    b.add_argument("--key-dir", type=Path, required=True)
    s = sub.add_parser("score")
    s.add_argument("--results-dir", type=Path, required=True)
    s.add_argument("--key", type=Path, required=True)
    s.add_argument("--out", type=Path)
    args = parser.parse_args()
    if args.cmd == "build":
        return cmd_build(args.raw_dir, args.fixtures, args.out_dir, args.key_dir)
    return cmd_score(args.results_dir, args.key, args.out)


if __name__ == "__main__":
    raise SystemExit(main())
