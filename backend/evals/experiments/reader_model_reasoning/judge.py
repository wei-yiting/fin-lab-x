"""Blinded signal judge for the reader model x reasoning 2x2.

Each answer is judged pass/fail against its row's ``draft_pass_signals``
by fresh, context-free Claude Code subagents — a model family that
produced none of the answers. A subagent receives only the judge prompt
and one batch file: opaque ids, questions, signals and answer texts, never
the arm, model or run metadata. The key lives in a separate directory
the judge is never pointed at.

Discrimination controls. A judge that passes everything cannot rank arms,
so known-worse answers are mixed into the same shuffled pool, built from
one real answer per row (the *base*):

- ``truncated``: the base answer's opening ~15% (cut at a sentence end).
- ``evidence_stripped``: the base answer with every sentence containing a
  digit removed, plus citation markers, reference lines, URLs and bracketed
  source attributions — the argument skeleton without its evidence.
- ``off_topic``: a real answer to a different row, judged against this
  row's signals.

Subcommands:

- ``build-pool``: pool real + control answers, shuffle (fixed seed), write
  ``batches/batch_N.{json,md}`` (30 items each), a re-judge set
  (``rejudge/batch_rK``: 40 pooled items reshuffled into 2 batches, for the
  judge's own run-to-run agreement), ``judge_prompt.md``, and the key into
  ``--key-dir``.
- ``collect``: validate every ``results/result_N.json`` and
  ``rejudge/result_rK.json`` the subagents wrote against their batches.
- ``score``: unblind with the key; per-arm signal pass rates with row
  bootstrap CIs, paired contrasts vs the control arm, the discrimination
  check, and judge self-agreement.
- ``spot-check``: a 15-answer stratified sample with the judge's verdicts,
  still blinded, as Markdown + a CSV for human agree/disagree.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import random
import re
import statistics
from collections import defaultdict
from pathlib import Path
from typing import Any

from backend.evals.experiments.harness import SCENARIO_DIR
from backend.evals.experiments.model_reasoning_benchmark.analyze import _bootstrap
from backend.evals.experiments.reader_model_reasoning.run import (
    ARM_NAMES,
    CONTROL_ARM,
)

POOL_SEED = 20261028
BATCH_SIZE = 30
REJUDGE_ITEMS = 40
REJUDGE_BATCH_SIZE = 20
CONTROL_KINDS = ["truncated", "evidence_stripped", "off_topic"]
OFF_TOPIC_SHIFT = 15

JUDGE_PROMPT = """You are grading answers produced by a financial research assistant for retail investors. The answers are in Traditional Chinese.

Each item in the batch has an id, the user's question, a numbered list of pass signals, and the answer. Decide independently for every signal whether the answer satisfies it.

Grading rules:
- Judge only the answer text in front of you. You have no access to the sources the assistant used, so do not try to verify facts; judge whether the answer itself does what the signal asks.
- Pass (1) only when the answer clearly and specifically satisfies the signal for this question. Fail (0) when the signal is met only vaguely, generically, partially, or not at all.
- A signal about evidence or sources (e.g. citing disclosures, naming concrete events, tying conclusions to news) needs that evidence to actually appear in the answer: named events, figures, filings or cited sources. Asserting a conclusion without them is a fail.
- A signal about a conclusion or judgement needs an explicit conclusion that answers this question, not a hedge or a list of considerations.
- An answer that addresses a different question or company fails every signal it does not satisfy for this question.
- Length, style and formatting are not signals. Do not reward or penalise them beyond what a signal asks.
- Grade every item on its own. The same question can appear several times in a batch with different answers; do not compare answers with each other or grade on a curve.

Write each reason as one short line in Traditional Chinese naming what in the answer made it pass or fail.

Output: a JSON array with one object per item, in batch order:
[{"id": "J0001", "scores": [{"signal": 0, "pass": 1, "reason": "..."}, ...]}, ...]
Every item must appear exactly once, and every item needs exactly one score per signal, numbered as in the batch (starting at 0)."""

# The reader arms cite search chunks by id; ids carry nothing the judge
# needs, and controls must not differ from real answers by id formatting.
_SEC_CHUNK_ID_RE = re.compile(r"`?sec://[^\s`)\]]+`?")
_SENTENCE_RE = re.compile(r"[^。！？!?\n]*(?:[。！？!?]+|\n|$)")
_DIGIT_RE = re.compile(r"[0-9０-９]")
_REF_LINE_RE = re.compile(r"^\s*\[\d{1,3}\]:.*$", re.MULTILINE)
_INLINE_REF_RE = re.compile(r"\[\d{1,3}\]")
_BRACKET_SOURCE_RE = re.compile(
    r"\[[^\]\n]*(?:SEC|10-K|來源|Source|Tavily|Finnhub)[^\]\n]*\]"
)
_URL_RE = re.compile(r"https?://\S+")


def mask(answer: str) -> str:
    return _SEC_CHUNK_ID_RE.sub("SEC 10-K excerpt", answer)


def truncate(answer: str, share: float = 0.15) -> str:
    limit = max(1, int(len(answer) * share))
    out = ""
    for match in _SENTENCE_RE.finditer(answer):
        sentence = match.group(0)
        if not sentence:
            break
        if out and len(out) + len(sentence) > limit:
            break
        out += sentence
    return out.strip()


def strip_evidence(answer: str) -> str:
    text = _REF_LINE_RE.sub("", answer)
    text = _URL_RE.sub("", text)
    text = _BRACKET_SOURCE_RE.sub("", text)
    text = _INLINE_REF_RE.sub("", text)
    kept = [
        m.group(0)
        for m in _SENTENCE_RE.finditer(text)
        if m.group(0) and not _DIGIT_RE.search(m.group(0))
    ]
    return re.sub(r"\n{3,}", "\n\n", "".join(kept)).strip()


def load_dataset() -> dict[str, dict[str, Any]]:
    with open(SCENARIO_DIR / "dataset.csv", newline="") as f:
        return {
            row["id"]: {
                "question": row["question"],
                "signals": json.loads(row["draft_pass_signals"]),
            }
            for row in csv.DictReader(f)
        }


def _answer(record: dict[str, Any]) -> str:
    return (record.get("output") or {}).get("response") or ""


def render_batch_md(name: str, batch: list[dict[str, Any]]) -> str:
    lines = [f"# Judge batch {name} — {len(batch)} items", ""]
    for item in batch:
        lines += [f"===== ITEM {item['id']} =====", "", "QUESTION:", item["question"]]
        lines += ["", "SIGNALS:"]
        lines += [f"{i}. {s}" for i, s in enumerate(item["signals"])]
        lines += ["", f"----- BEGIN ANSWER {item['id']} -----"]
        lines += [item["answer"] or "(empty answer)"]
        lines += [f"----- END ANSWER {item['id']} -----", ""]
    return "\n".join(lines)


def _write_batches(
    directory: Path, prefix: str, batches: list[list[dict[str, Any]]]
) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    for n, batch in enumerate(batches, start=1):
        name = f"{prefix}{n}"
        (directory / f"batch_{name}.json").write_text(
            json.dumps(batch, ensure_ascii=False, indent=1)
        )
        (directory / f"batch_{name}.md").write_text(render_batch_md(name, batch))


def _chunks(items: list[Any], size: int) -> list[list[Any]]:
    return [items[i : i + size] for i in range(0, len(items), size)]


def cmd_build_pool(raw_dir: Path, judge_dir: Path, key_dir: Path) -> int:
    dataset = load_dataset()
    records = [json.loads(p.read_text()) for p in sorted(raw_dir.rglob("*.json"))]
    by_row: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for rec in records:
        by_row[rec["row_id"]].append(rec)
    rng = random.Random(POOL_SEED)

    items: list[tuple[dict[str, Any], dict[str, Any]]] = []
    for rec in records:
        items.append(
            (
                {"row_id": rec["row_id"], "answer": mask(_answer(rec))},
                {
                    "row": rec["row_id"],
                    "kind": "real",
                    "arm": rec["arm"],
                    "rep": rec["repetition"],
                    "empty_answer": not _answer(rec),
                },
            )
        )

    row_ids = sorted(by_row, key=int)
    for position, row_id in enumerate(row_ids):
        candidates = [r for r in by_row[row_id] if _answer(r)]
        base = rng.choice(candidates)
        base_ref = {"base_arm": base["arm"], "base_rep": base["repetition"]}
        masked = mask(_answer(base))
        items.append(
            (
                {"row_id": row_id, "answer": truncate(masked)},
                {"row": row_id, "kind": "truncated", **base_ref},
            )
        )
        items.append(
            (
                {"row_id": row_id, "answer": strip_evidence(masked)},
                {"row": row_id, "kind": "evidence_stripped", **base_ref},
            )
        )
        other_row = row_ids[(position + OFF_TOPIC_SHIFT) % len(row_ids)]
        other = rng.choice([r for r in by_row[other_row] if _answer(r)])
        items.append(
            (
                {"row_id": row_id, "answer": mask(_answer(other))},
                {
                    "row": row_id,
                    "kind": "off_topic",
                    "source_row": other_row,
                    "base_arm": other["arm"],
                    "base_rep": other["repetition"],
                },
            )
        )

    rng.shuffle(items)
    key: dict[str, dict[str, Any]] = {}
    entries = []
    for index, (item, meta) in enumerate(items, start=1):
        item_id = f"J{index:04d}"
        key[item_id] = meta
        row = dataset[item["row_id"]]
        entries.append(
            {
                "id": item_id,
                "question": row["question"],
                "signals": row["signals"],
                "answer": item["answer"],
            }
        )

    batches = _chunks(entries, BATCH_SIZE)
    _write_batches(judge_dir / "batches", "", batches)
    rejudge = rng.sample(entries, min(REJUDGE_ITEMS, len(entries)))
    _write_batches(judge_dir / "rejudge", "r", _chunks(rejudge, REJUDGE_BATCH_SIZE))
    (judge_dir / "judge_prompt.md").write_text(JUDGE_PROMPT + "\n")
    key_dir.mkdir(parents=True, exist_ok=True)
    (key_dir / "KEY_do_not_share.json").write_text(
        json.dumps(key, ensure_ascii=False, indent=1)
    )
    kinds: dict[str, int] = defaultdict(int)
    for meta in key.values():
        kinds[meta["kind"]] += 1
    print(
        f"{len(key)} items in {len(batches)} batches: {dict(kinds)}; "
        f"re-judge {REJUDGE_ITEMS} items; prompt sha256 "
        f"{hashlib.sha256(JUDGE_PROMPT.encode()).hexdigest()[:12]}"
    )
    return 0


def _batch_pairs(judge_dir: Path) -> list[tuple[Path, Path]]:
    pairs = []
    for sub, results in (("batches", "results"), ("rejudge", "rejudge")):
        for batch in sorted((judge_dir / sub).glob("batch_*.json")):
            name = batch.stem.removeprefix("batch_")
            pairs.append((batch, judge_dir / results / f"result_{name}.json"))
    return pairs


def validate(batch: list[dict[str, Any]], result: Any) -> list[str]:
    """Problems with a subagent's result file, empty when it is usable."""
    if not isinstance(result, list):
        return ["result is not a JSON array"]
    problems = []
    by_id = {}
    for entry in result:
        if entry.get("id") in by_id:
            problems.append(f"{entry.get('id')}: duplicate")
        by_id[entry.get("id")] = entry
    for item in batch:
        entry = by_id.pop(item["id"], None)
        if entry is None:
            problems.append(f"{item['id']}: missing")
            continue
        scores = entry.get("scores") or []
        indices = sorted(s.get("signal") for s in scores)
        if indices != list(range(len(item["signals"]))):
            problems.append(f"{item['id']}: signal indices {indices}")
        if any(s.get("pass") not in (0, 1) for s in scores):
            problems.append(f"{item['id']}: pass not 0/1")
    problems += [f"{extra}: not in batch" for extra in by_id]
    return problems


def cmd_collect(judge_dir: Path) -> int:
    ok = True
    for batch_path, result_path in _batch_pairs(judge_dir):
        batch = json.loads(batch_path.read_text())
        if not result_path.exists():
            print(f"{result_path.name}: MISSING")
            ok = False
            continue
        problems = validate(batch, json.loads(result_path.read_text()))
        print(f"{result_path.name}: {'OK' if not problems else problems[:5]}")
        ok = ok and not problems
    return 0 if ok else 1


def load_results(directory: Path) -> dict[str, list[dict[str, Any]]]:
    out = {}
    for path in directory.glob("result_*.json"):
        for entry in json.loads(path.read_text()):
            out[entry["id"]] = sorted(entry["scores"], key=lambda s: s["signal"])
    return out


def _pass_rate(scores: list[dict[str, Any]]) -> float:
    return statistics.mean(s["pass"] for s in scores)


def _row_means(
    entries: list[dict[str, Any]], group: str, value: str
) -> dict[str, dict[str, float]]:
    """group -> row -> mean of ``value`` over that cell's entries."""
    cells: dict[tuple[str, str], list[float]] = defaultdict(list)
    for e in entries:
        cells[(e[group], e["row"])].append(e[value])
    out: dict[str, dict[str, float]] = defaultdict(dict)
    for (g, row), vals in cells.items():
        out[g][row] = statistics.mean(vals)
    return out


def _ci(values: dict[str, float]) -> tuple[float, float, float]:
    return _bootstrap(values, statistics.mean)


def _paired(a: dict[str, float], b: dict[str, float]) -> tuple[float, float, float]:
    return _ci({r: a[r] - b[r] for r in a if r in b})


def cmd_score(judge_dir: Path, key_path: Path, out_dir: Path) -> int:
    key = json.loads(key_path.read_text())
    results = load_results(judge_dir / "results")
    entries = []
    for item_id, meta in key.items():
        if item_id not in results:
            continue
        scores = results[item_id]
        entries.append(
            {
                "id": item_id,
                **meta,
                "group": meta["arm"] if meta["kind"] == "real" else meta["kind"],
                "pass_rate": _pass_rate(scores),
                "all_pass": float(all(s["pass"] for s in scores)),
                "n_signals": len(scores),
                "passes": [s["pass"] for s in scores],
            }
        )

    rate = _row_means(entries, "group", "pass_rate")
    all_pass = _row_means(entries, "group", "all_pass")
    arms = {
        arm: {
            "answers": sum(1 for e in entries if e["group"] == arm),
            "signal_pass_rate": _ci(rate[arm]),
            "all_signals_pass": _ci(all_pass[arm]),
        }
        for arm in ARM_NAMES
        if arm in rate
    }
    contrasts = {
        arm: {
            "signal_pass_rate": _paired(rate[arm], rate[CONTROL_ARM]),
            "all_signals_pass": _paired(all_pass[arm], all_pass[CONTROL_ARM]),
        }
        for arm in ARM_NAMES
        if arm != CONTROL_ARM and arm in rate
    }

    # Discrimination: truncated / evidence_stripped vs the exact real answer
    # they were built from; off_topic vs this row's real answers (all arms).
    real = {(e["row"], e["arm"], e["rep"]): e for e in entries if e["kind"] == "real"}
    real_by_row = _row_means(
        [{**e, "all": "all"} for e in entries if e["kind"] == "real"],
        "all",
        "pass_rate",
    )["all"]
    discrimination = {}
    for kind in CONTROL_KINDS:
        controls = [e for e in entries if e["kind"] == kind]
        if kind == "off_topic":
            pairs = {e["row"]: e["pass_rate"] - real_by_row[e["row"]] for e in controls}
        else:
            pairs = {
                e["row"]: e["pass_rate"]
                - real[(e["row"], e["base_arm"], e["base_rep"])]["pass_rate"]
                for e in controls
                if (e["row"], e["base_arm"], e["base_rep"]) in real
            }
        control_rate = _ci({e["row"]: e["pass_rate"] for e in controls})
        delta = _ci(pairs)
        passed = (
            control_rate[0] <= 0.15
            if kind == "off_topic"
            else delta[0] <= -0.25 and delta[2] < 0
        )
        discrimination[kind] = {
            "n": len(controls),
            "control_pass_rate": control_rate,
            "delta_vs_real": delta,
            "passed": passed,
        }

    agreement = None
    rejudged = load_results(judge_dir / "rejudge")
    if rejudged:
        same = total = items_same = 0
        flips = []
        for item_id, second in rejudged.items():
            first = results[item_id]
            matches = [a["pass"] == b["pass"] for a, b in zip(first, second)]
            same += sum(matches)
            total += len(matches)
            items_same += all(matches)
            if not all(matches):
                flips.append(item_id)
        agreement = {
            "items": len(rejudged),
            "signal_agreement": same / total,
            "item_exact_agreement": items_same / len(rejudged),
            "items_with_flips": sorted(flips),
        }

    per_signal = defaultdict(list)
    for e in entries:
        if e["kind"] == "real":
            for i, p in enumerate(e["passes"]):
                per_signal[(e["row"], i)].append(p)
    signal_ceiling = {
        "row_signals": len(per_signal),
        "passed_by_every_real_answer": sum(1 for v in per_signal.values() if all(v)),
        "failed_by_every_real_answer": sum(
            1 for v in per_signal.values() if not any(v)
        ),
    }

    summary = {
        "judged": len(entries),
        "pooled": len(key),
        "real_overall_signal_pass_rate": _ci(real_by_row),
        "arms": arms,
        "contrasts_vs_control": contrasts,
        "discrimination": discrimination,
        "discrimination_passed": all(d["passed"] for d in discrimination.values()),
        "judge_self_agreement": agreement,
        "signal_ceiling": signal_ceiling,
    }
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "judge_summary.json").write_text(json.dumps(summary, indent=2))
    with open(out_dir / "judge_scores.csv", "w", newline="") as f:
        fields = ["id", "row", "kind", "arm", "rep", "base_arm", "base_rep",
                  "source_row", "pass_rate", "all_pass", "n_signals", "passes"]  # fmt: skip
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for e in sorted(entries, key=lambda e: e["id"]):
            writer.writerow({**e, "passes": "".join(str(p) for p in e["passes"])})
    print(json.dumps(summary, indent=2))
    return 0


def cmd_spot_check(judge_dir: Path, key_path: Path, out_dir: Path) -> int:
    """Blinded 15-answer sample: 3 real answers per arm + 1 per control kind.

    Within each arm, one answer with at least one failed signal is taken
    first when the arm has any, so the sample contains the judge's fails,
    not only its passes.
    """
    key = json.loads(key_path.read_text())
    items = {
        it["id"]: it
        for p in (judge_dir / "batches").glob("batch_*.json")
        for it in json.loads(p.read_text())
    }
    results = load_results(judge_dir / "results")
    rng = random.Random(POOL_SEED + 2)
    picked: list[str] = []
    for arm in ARM_NAMES:
        ids = sorted(
            i for i, m in key.items() if m.get("arm") == arm and m["kind"] == "real"
        )
        failing = [i for i in ids if not all(s["pass"] for s in results[i])]
        chosen = rng.sample(failing, min(1, len(failing)))
        rest = [i for i in ids if i not in chosen]
        chosen += rng.sample(rest, 3 - len(chosen))
        picked += chosen
    for kind in CONTROL_KINDS:
        picked.append(
            rng.choice(sorted(i for i, m in key.items() if m["kind"] == kind))
        )
    rng.shuffle(picked)

    out_dir.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Signal-judge spot check (blinded)",
        "",
        "For each answer, read the question and the answer, then for every "
        "signal fill `human_pass` (1 / 0) in `spot_check.csv` with **your own** "
        "verdict. The judge's verdict and reason are shown so you can disagree "
        "with them; where the answer came from is not shown.",
        "",
    ]
    rows = []
    for item_id in picked:
        item = items[item_id]
        lines += [f"## {item_id}", "", f"**Question:** {item['question']}", ""]
        lines += ["| # | Signal | Judge | Judge reason |", "|---|---|---|---|"]
        for s in results[item_id]:
            signal = item["signals"][s["signal"]]
            lines.append(
                f"| {s['signal']} | {signal} | {'pass' if s['pass'] else 'FAIL'} "
                f"| {s['reason']} |"
            )
            rows.append(
                {
                    "id": item_id,
                    "signal_index": s["signal"],
                    "signal": signal,
                    "judge_pass": s["pass"],
                    "judge_reason": s["reason"],
                    "human_pass": "",
                    "human_note": "",
                }
            )
        lines += ["", "<details><summary>Answer</summary>", "", item["answer"], "",
                  "</details>", ""]  # fmt: skip
    (out_dir / "spot_check.md").write_text("\n".join(lines))
    with open(out_dir / "spot_check.csv", "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    print(f"{len(picked)} answers, {len(rows)} signal verdicts -> {out_dir}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="cmd", required=True)
    build = sub.add_parser("build-pool")
    build.add_argument("--raw-dir", type=Path, required=True)
    build.add_argument("--judge-dir", type=Path, required=True)
    build.add_argument("--key-dir", type=Path, required=True)
    collect = sub.add_parser("collect")
    collect.add_argument("--judge-dir", type=Path, required=True)
    for name in ("score", "spot-check"):
        p = sub.add_parser(name)
        p.add_argument("--judge-dir", type=Path, required=True)
        p.add_argument("--key", type=Path, required=True)
        p.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args(argv)

    if args.cmd == "build-pool":
        return cmd_build_pool(args.raw_dir, args.judge_dir, args.key_dir)
    if args.cmd == "collect":
        return cmd_collect(args.judge_dir)
    if args.cmd == "score":
        return cmd_score(args.judge_dir, args.key, args.out_dir)
    return cmd_spot_check(args.judge_dir, args.key, args.out_dir)


if __name__ == "__main__":
    raise SystemExit(main())
