"""Secondary quality measures: faithfulness and completeness (Amendment 2).

Both are judged by fresh, context-free Claude Code subagents over blinded
batch files, like ``judge.py``; keys live in a separate directory.

- Faithfulness: each answer is shown with the tool outputs *its own run*
  received; the judge lists checkable factual claims and labels each
  supported / unsupported / contradicted. Control: ``perturbed`` answers
  with one figure altered (the judge should flag the altered figure).
- Completeness: per row, a judge writes 4–8 key points from the question
  and the four arms' rep-1 answers (anonymised, shuffled); every rep-1
  answer is then scored per key point. Control: ``truncated`` answers.

Subcommands: ``build-faith``, ``build-nuggets``, ``build-coverage`` (needs
the nugget results), ``score``.
"""

from __future__ import annotations

import argparse
import json
import random
import re
import statistics
import textwrap
from collections import defaultdict
from pathlib import Path
from typing import Any

from backend.evals.experiments.reader_model_reasoning.judge import (
    _ci,
    _paired,
    load_dataset,
    mask,
    truncate,
)
from backend.evals.experiments.reader_model_reasoning.run import (
    ARM_NAMES,
    CONTROL_ARM,
)

SEED = 20261028
FAITH_ARMS = ["reader_luna_none", "reader_luna_medium"]
FAITH_BATCH = 6
NUGGET_ROWS_PER_BATCH = 5
COVERAGE_BATCH = 30
WRAP = 300

FAITH_PROMPT = """You are checking whether answers from a financial research assistant are faithful to the evidence the assistant retrieved. Answers are in Traditional Chinese; evidence is mostly English tool output (SEC filing excerpts, news search results, market data).

For each item you get the question, the EVIDENCE (every tool result that run received), and the ANSWER.

1. List the checkable factual claims in the answer: figures, percentages, dates, amounts, named events, rulings, guidance, and statements attributed to a filing or news source. Skip opinions, conclusions, hedges, general background and advice. List at most 25 claims, preferring figures and attributed statements. Quote or closely paraphrase each claim in the answer's language.
2. Label each claim against the EVIDENCE only:
   - "supported": the evidence states it (allow rounding, unit conversion and translation);
   - "unsupported": the evidence does not contain it (it may still be true; you are not checking the world, only this evidence);
   - "contradicted": the evidence states something incompatible (e.g. a different figure for the same thing).
3. Grade every item on its own; do not compare items.

Output: a JSON array, one object per item in batch order:
[{"id": "F0001", "claims": [{"claim": "...", "verdict": "supported", "note": "short pointer to the evidence or why not"}, ...]}, ...]
Every item must appear exactly once. If an answer has no checkable claims, return an empty claims list."""

NUGGET_PROMPT = """You are building a grading checklist for questions a retail investor asked a financial research assistant. Everything is in Traditional Chinese.

For each question you get several anonymous answers written by different systems. Use them only to learn which concrete points this question calls for; do not reward any particular answer.

For each question write 4–8 key points ("nuggets") that a complete, well-supported answer must contain. Each nugget is one concrete point a grader can check in any answer (e.g. a specific risk, a disclosed figure and what it means, a distinction the question asks for, an explicit conclusion). Write nuggets in Traditional Chinese, phrased so they can be met with different wording. Mark each "vital" (an answer without it is incomplete) or "okay" (useful but optional). Include at least 3 vital nuggets. Do not include style, length or formatting nuggets.

Output: a JSON array, one object per question in batch order:
[{"row": "6", "nuggets": [{"nugget": "...", "importance": "vital"}, ...]}, ...]"""

COVERAGE_PROMPT = """You are grading how completely answers from a financial research assistant cover a fixed checklist of key points. Everything is in Traditional Chinese.

For each item you get the question, the numbered key points (each marked vital or okay), and the answer. For every key point give a score:
- 1: the answer clearly covers it;
- 0.5: the answer touches it but vaguely or partly;
- 0: the answer does not cover it.
Judge only coverage of each point, not style or length. Grade every item on its own; the same question appears several times with different answers; do not compare them.

Output: a JSON array, one object per item in batch order:
[{"id": "C0001", "nuggets": [{"n": 0, "score": 1, "reason": "one short line in Traditional Chinese"}, ...]}, ...]
Every item must appear exactly once, with one score per key point, numbered as given (starting at 0)."""

# Spans whose digits are not claims: URLs, reference-definition lines,
# filing-type names (10-K, 20-F), ISO dates and list / heading numbers.
_NOT_A_CLAIM = [
    re.compile(r"https?://\S+"),
    re.compile(r"^\s*\[\d{1,3}\]:.*$", re.MULTILINE),
    re.compile(r"\b\d{1,2}-[A-Z]\b"),
    re.compile(r"\b\d{4}-\d{2}-\d{2}\b"),
    re.compile(r"\[\d{1,3}\]"),
    re.compile(r"(?:^|\s)#*\s*\d{1,2}[.、)]\s", re.MULTILINE),
]
_NUMBER_RE = re.compile(r"(?<![\w.\[])(\d{1,3}(?:,\d{3})+|\d+)(\.\d+)?(?![\w\]])")


def _records(raw_dir: Path, rep: int) -> list[dict[str, Any]]:
    return [
        json.loads(p.read_text())
        for p in sorted((raw_dir / f"rep{rep}").glob("*.json"))
    ]


def _answer(rec: dict[str, Any]) -> str:
    return mask((rec.get("output") or {}).get("response") or "")


def _evidence(rec: dict[str, Any]) -> str:
    blocks = []
    for n, out in enumerate((rec.get("output") or {}).get("tool_outputs") or []):
        text = out.get("error") or out.get("result")
        if isinstance(text, str):
            try:
                text = json.loads(text)
            except json.JSONDecodeError:
                pass
        if isinstance(text, dict):
            text = {k: v for k, v in text.items() if "language_directive" not in k}
        body = (
            text
            if isinstance(text, str)
            else json.dumps(text, ensure_ascii=False, indent=1)
        )
        lines = [
            wrapped
            for line in body.splitlines()
            for wrapped in (textwrap.wrap(line, WRAP) or [""])
        ]
        args = json.dumps(out.get("args"), ensure_ascii=False)
        blocks.append(f"[tool {n}] {out.get('tool')} {args}\n" + "\n".join(lines))
    return "\n\n".join(blocks) or "(no tool output)"


def perturb(answer: str, rng: random.Random) -> tuple[str, dict[str, str]] | None:
    """Alter one figure (not a year, not a citation number) by ~+40%."""
    excluded = [m.span() for pattern in _NOT_A_CLAIM for m in pattern.finditer(answer)]
    candidates = []
    for m in _NUMBER_RE.finditer(answer):
        if any(lo <= m.start() < hi for lo, hi in excluded):
            continue
        digits = m.group(1).replace(",", "")
        value = float(digits + (m.group(2) or ""))
        if 1900 <= value <= 2100 and not m.group(2):
            continue
        if value < 2:
            continue
        candidates.append(m)
    if not candidates:
        return None
    m = rng.choice(candidates)
    whole, frac = m.group(1).replace(",", ""), m.group(2) or ""
    new_value = float(whole + frac) * 1.4
    decimals = len(frac) - 1 if frac else 0
    new = (
        f"{new_value:,.{decimals}f}"
        if "," in m.group(1)
        else f"{new_value:.{decimals}f}"
    )
    if new == m.group(0):
        return None
    start, end = m.span()
    context = answer[max(0, start - 60) : end + 60].replace("\n", " ")
    return answer[:start] + new + answer[end:], {
        "original": m.group(0),
        "altered": new,
        "context": context,
    }


def _write(directory: Path, name: str, items: list[dict[str, Any]], render) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    (directory / f"batch_{name}.json").write_text(
        json.dumps(items, ensure_ascii=False, indent=1)
    )
    (directory / f"batch_{name}.md").write_text(render(name, items))


def _render_faith(name: str, items: list[dict[str, Any]]) -> str:
    lines = [f"# Faithfulness batch {name} — {len(items)} items", ""]
    for it in items:
        lines += [f"===== ITEM {it['id']} =====", "", "QUESTION:", it["question"], ""]
        lines += [f"----- BEGIN EVIDENCE {it['id']} -----", it["evidence"]]
        lines += [f"----- END EVIDENCE {it['id']} -----", ""]
        lines += [f"----- BEGIN ANSWER {it['id']} -----", it["answer"]]
        lines += [f"----- END ANSWER {it['id']} -----", ""]
    return "\n".join(lines)


def cmd_build_faith(raw_dir: Path, out_dir: Path, key_dir: Path) -> int:
    dataset = load_dataset()
    rng = random.Random(SEED)
    recs = [r for r in _records(raw_dir, 1) if r["arm"] in FAITH_ARMS]
    pool: list[tuple[dict[str, Any], dict[str, Any]]] = []
    for rec in recs:
        pool.append(
            (
                {"rec": rec, "answer": _answer(rec)},
                {"row": rec["row_id"], "kind": "real", "arm": rec["arm"], "rep": 1},
            )
        )
    by_row = defaultdict(list)
    for rec in recs:
        by_row[rec["row_id"]].append(rec)
    for row in sorted(by_row, key=int):
        for base in rng.sample(by_row[row], len(by_row[row])):
            result = perturb(_answer(base), rng)
            if result:
                answer, change = result
                pool.append(
                    (
                        {"rec": base, "answer": answer},
                        {
                            "row": row,
                            "kind": "perturbed",
                            "base_arm": base["arm"],
                            "rep": 1,
                            **change,
                        },  # fmt: skip
                    )
                )
                break
    rng.shuffle(pool)
    key, items = {}, []
    for n, (item, meta) in enumerate(pool, start=1):
        item_id = f"F{n:04d}"
        key[item_id] = meta
        items.append(
            {
                "id": item_id,
                "question": dataset[meta["row"]]["question"],
                "evidence": _evidence(item["rec"]),
                "answer": item["answer"],
            }
        )
    for b, start in enumerate(range(0, len(items), FAITH_BATCH), start=1):
        _write(out_dir / "batches", str(b), items[start : start + FAITH_BATCH],
               _render_faith)  # fmt: skip
    (out_dir / "faith_prompt.md").write_text(FAITH_PROMPT + "\n")
    key_dir.mkdir(parents=True, exist_ok=True)
    (key_dir / "KEY_faith.json").write_text(
        json.dumps(key, ensure_ascii=False, indent=1)
    )
    kinds = defaultdict(int)
    for m in key.values():
        kinds[m["kind"]] += 1
    print(f"{len(items)} faithfulness items in {b} batches: {dict(kinds)}")
    return 0


def _render_nuggets(name: str, rows: list[dict[str, Any]]) -> str:
    lines = [f"# Checklist batch {name} — {len(rows)} questions", ""]
    for r in rows:
        lines += [f"===== QUESTION row {r['row']} =====", r["question"], ""]
        for label, answer in zip("ABCD", r["answers"]):
            lines += [f"----- BEGIN ANSWER {label} -----", answer,
                      f"----- END ANSWER {label} -----", ""]  # fmt: skip
    return "\n".join(lines)


def cmd_build_nuggets(raw_dir: Path, out_dir: Path) -> int:
    dataset = load_dataset()
    rng = random.Random(SEED + 1)
    by_row = defaultdict(list)
    for rec in _records(raw_dir, 1):
        by_row[rec["row_id"]].append(_answer(rec))
    rows = []
    for row in sorted(by_row, key=int):
        answers = by_row[row][:]
        rng.shuffle(answers)
        rows.append(
            {"row": row, "question": dataset[row]["question"], "answers": answers}
        )
    for b, start in enumerate(range(0, len(rows), NUGGET_ROWS_PER_BATCH), start=1):
        _write(out_dir / "batches", str(b), rows[start : start + NUGGET_ROWS_PER_BATCH],
               _render_nuggets)  # fmt: skip
    (out_dir / "nugget_prompt.md").write_text(NUGGET_PROMPT + "\n")
    print(f"{len(rows)} rows in {b} nugget batches")
    return 0


def load_nuggets(nugget_dir: Path) -> dict[str, list[dict[str, str]]]:
    out = {}
    for p in (nugget_dir / "results").glob("result_*.json"):
        for entry in json.loads(p.read_text()):
            out[str(entry["row"])] = entry["nuggets"]
    return out


def _render_coverage(name: str, items: list[dict[str, Any]]) -> str:
    lines = [f"# Coverage batch {name} — {len(items)} items", ""]
    for it in items:
        lines += [f"===== ITEM {it['id']} =====", "", "QUESTION:", it["question"], ""]
        lines += ["KEY POINTS:"]
        lines += [f"{i}. [{n['importance']}] {n['nugget']}"
                  for i, n in enumerate(it["nuggets"])]  # fmt: skip
        lines += ["", f"----- BEGIN ANSWER {it['id']} -----", it["answer"] or "(empty)"]
        lines += [f"----- END ANSWER {it['id']} -----", ""]
    return "\n".join(lines)


def cmd_build_coverage(
    raw_dir: Path, nugget_dir: Path, out_dir: Path, key_dir: Path
) -> int:
    dataset = load_dataset()
    nuggets = load_nuggets(nugget_dir)
    rng = random.Random(SEED + 2)
    recs = _records(raw_dir, 1)
    pool = [
        (_answer(r), {"row": r["row_id"], "kind": "real", "arm": r["arm"], "rep": 1})
        for r in recs
    ]
    by_row = defaultdict(list)
    for r in recs:
        if r["arm"] in FAITH_ARMS:
            by_row[r["row_id"]].append(r)
    for row in sorted(by_row, key=int):
        base = rng.choice(by_row[row])
        pool.append(
            (
                truncate(_answer(base)),
                {"row": row, "kind": "truncated", "base_arm": base["arm"], "rep": 1},
            )
        )
    rng.shuffle(pool)
    key, items = {}, []
    for n, (answer, meta) in enumerate(pool, start=1):
        item_id = f"C{n:04d}"
        key[item_id] = meta
        items.append(
            {
                "id": item_id,
                "question": dataset[meta["row"]]["question"],
                "nuggets": nuggets[meta["row"]],
                "answer": answer,
            }
        )
    for b, start in enumerate(range(0, len(items), COVERAGE_BATCH), start=1):
        _write(out_dir / "batches", str(b), items[start : start + COVERAGE_BATCH],
               _render_coverage)  # fmt: skip
    (out_dir / "coverage_prompt.md").write_text(COVERAGE_PROMPT + "\n")
    key_dir.mkdir(parents=True, exist_ok=True)
    (key_dir / "KEY_coverage.json").write_text(
        json.dumps(key, ensure_ascii=False, indent=1)
    )
    print(f"{len(items)} coverage items in {b} batches")
    return 0


def _results(directory: Path, field: str) -> dict[str, list[dict[str, Any]]]:
    out = {}
    for p in (directory / "results").glob("result_*.json"):
        for entry in json.loads(p.read_text()):
            out[entry["id"]] = entry[field]
    return out


def _by_row(entries: list[dict[str, Any]], arm: str, value: str) -> dict[str, float]:
    return {
        e["row"]: e[value]
        for e in entries
        if e.get("arm") == arm and e["kind"] == "real"
    }


def score_faith(faith_dir: Path, key_path: Path) -> dict[str, Any]:
    key = json.loads(key_path.read_text())
    results = _results(faith_dir, "claims")
    entries = []
    for item_id, meta in key.items():
        claims = results.get(item_id)
        if claims is None:
            continue
        verdicts = [c["verdict"] for c in claims]
        n = len(verdicts)
        entries.append(
            {
                **meta,
                "id": item_id,
                "claims": n,
                "support_rate": verdicts.count("supported") / n if n else 1.0,
                "contradicted": verdicts.count("contradicted"),
                "unsupported": verdicts.count("unsupported"),
                "flagged_alteration": meta["kind"] == "perturbed"
                and any(
                    c["verdict"] != "supported"
                    and meta["altered"].replace(",", "") in c["claim"].replace(",", "")
                    for c in claims
                ),
            }
        )
    arms = {
        arm: {
            "answers": sum(1 for e in entries if e.get("arm") == arm),
            "support_rate": _ci(_by_row(entries, arm, "support_rate")),
            "median_claims": statistics.median(
                e["claims"] for e in entries if e.get("arm") == arm
            ),
            "answers_with_contradiction": sum(
                1 for e in entries if e.get("arm") == arm and e["contradicted"]
            ),
        }
        for arm in FAITH_ARMS
    }
    treat = "reader_luna_none"
    perturbed = [e for e in entries if e["kind"] == "perturbed"]
    real = {(e["row"], e["arm"]): e for e in entries if e["kind"] == "real"}
    return {
        "arms": arms,
        "delta_support_rate": _paired(
            _by_row(entries, treat, "support_rate"),
            _by_row(entries, CONTROL_ARM, "support_rate"),
        ),
        "perturbed": {
            "n": len(perturbed),
            "flagged_rate": sum(e["flagged_alteration"] for e in perturbed)
            / len(perturbed),
            "delta_support_vs_base": _ci(
                {
                    e["row"]: e["support_rate"]
                    - real[(e["row"], e["base_arm"])]["support_rate"]
                    for e in perturbed
                    if (e["row"], e["base_arm"]) in real
                }
            ),
        },
        "entries": entries,
    }


def score_coverage(cov_dir: Path, key_path: Path, nugget_dir: Path) -> dict[str, Any]:
    key = json.loads(key_path.read_text())
    nuggets = load_nuggets(nugget_dir)
    results = _results(cov_dir, "nuggets")
    entries = []
    for item_id, meta in key.items():
        scores = results.get(item_id)
        if scores is None:
            continue
        row_nuggets = nuggets[meta["row"]]
        by_n = {s["n"]: float(s["score"]) for s in scores}
        vital = [i for i, n in enumerate(row_nuggets) if n["importance"] == "vital"]
        entries.append(
            {
                **meta,
                "id": item_id,
                "vital_recall": statistics.mean(by_n.get(i, 0.0) for i in vital),
                "all_recall": statistics.mean(
                    by_n.get(i, 0.0) for i in range(len(row_nuggets))
                ),
            }
        )
    arms = {
        arm: {
            "vital_recall": _ci(_by_row(entries, arm, "vital_recall")),
            "all_recall": _ci(_by_row(entries, arm, "all_recall")),
        }
        for arm in ARM_NAMES
    }
    contrasts = {
        arm: _paired(
            _by_row(entries, arm, "vital_recall"),
            _by_row(entries, CONTROL_ARM, "vital_recall"),
        )
        for arm in ARM_NAMES
        if arm != CONTROL_ARM
    }
    real = {(e["row"], e["arm"]): e for e in entries if e["kind"] == "real"}
    truncated = [e for e in entries if e["kind"] == "truncated"]
    return {
        "nugget_rows": len(nuggets),
        "nuggets_per_row_median": statistics.median(len(v) for v in nuggets.values()),
        "arms": arms,
        "delta_vital_recall_vs_control": contrasts,
        "truncated": {
            "n": len(truncated),
            "vital_recall": _ci({e["row"]: e["vital_recall"] for e in truncated}),
            "delta_vs_base": _ci(
                {
                    e["row"]: e["vital_recall"]
                    - real[(e["row"], e["base_arm"])]["vital_recall"]
                    for e in truncated
                }
            ),
        },
        "entries": entries,
    }


def cmd_score(
    faith_dir: Path, faith_key: Path, cov_dir: Path, cov_key: Path,
    nugget_dir: Path, out_dir: Path,
) -> int:  # fmt: skip
    faith = score_faith(faith_dir, faith_key)
    coverage = score_coverage(cov_dir, cov_key, nugget_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    summary = {
        "faithfulness": {k: v for k, v in faith.items() if k != "entries"},
        "completeness": {k: v for k, v in coverage.items() if k != "entries"},
    }
    (out_dir / "grounding_summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False)
    )
    (out_dir / "faith_scores.json").write_text(
        json.dumps(faith["entries"], indent=1, ensure_ascii=False)
    )
    (out_dir / "coverage_scores.json").write_text(
        json.dumps(coverage["entries"], indent=1, ensure_ascii=False)
    )
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("build-faith")
    for a in ("--raw-dir", "--out-dir", "--key-dir"):
        p.add_argument(a, type=Path, required=True)
    p = sub.add_parser("build-nuggets")
    for a in ("--raw-dir", "--out-dir"):
        p.add_argument(a, type=Path, required=True)
    p = sub.add_parser("build-coverage")
    for a in ("--raw-dir", "--nugget-dir", "--out-dir", "--key-dir"):
        p.add_argument(a, type=Path, required=True)
    p = sub.add_parser("score")
    for a in ("--faith-dir", "--faith-key", "--cov-dir", "--cov-key", "--nugget-dir",
              "--out-dir"):  # fmt: skip
        p.add_argument(a, type=Path, required=True)
    args = parser.parse_args(argv)
    if args.cmd == "build-faith":
        return cmd_build_faith(args.raw_dir, args.out_dir, args.key_dir)
    if args.cmd == "build-nuggets":
        return cmd_build_nuggets(args.raw_dir, args.out_dir)
    if args.cmd == "build-coverage":
        return cmd_build_coverage(
            args.raw_dir, args.nugget_dir, args.out_dir, args.key_dir
        )
    return cmd_score(args.faith_dir, args.faith_key, args.cov_dir, args.cov_key,
                     args.nugget_dir, args.out_dir)  # fmt: skip


if __name__ == "__main__":
    raise SystemExit(main())
