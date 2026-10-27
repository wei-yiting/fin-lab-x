"""Blinded signal judge for the reader model x reasoning 2x2.

Each answer is judged pass/fail against its row's ``draft_pass_signals``
by a scripted Claude judge — a model family that produced none of the
answers. The judge sees only an opaque id, the question, the signals and
the answer text: never the arm, model or run metadata.

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
  ``batches/batch_N.json`` (30 items each) and ``KEY_do_not_share.json``.
- ``judge``: call the judge for every pooled item (resumable, one request
  per answer), write ``results/result_N.json`` and ``judge_config.json``.
  ``--rejudge N`` re-judges a fixed random subset into ``rejudge/`` to
  measure the judge's own run-to-run agreement.
- ``score``: unblind with the key; per-arm signal pass rates with row
  bootstrap CIs, paired contrasts vs the control arm, the discrimination
  check, and judge self-agreement.
- ``spot-check``: a 15-answer stratified sample with the judge's verdicts,
  still blinded, as Markdown + a CSV for human agree/disagree.
"""

from __future__ import annotations

import argparse
import asyncio
import csv
import hashlib
import json
import random
import re
import statistics
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import anthropic

from backend.evals.experiments.harness import SCENARIO_DIR
from backend.evals.experiments.model_reasoning_benchmark.analyze import _bootstrap
from backend.evals.experiments.reader_model_reasoning.run import (
    ARM_NAMES,
    CONTROL_ARM,
)

POOL_SEED = 20261028
BATCH_SIZE = 30
CONTROL_KINDS = ["truncated", "evidence_stripped", "off_topic"]
OFF_TOPIC_SHIFT = 15

JUDGE_MODEL = "claude-opus-5-5"
JUDGE_EFFORT = "medium"
JUDGE_MAX_TOKENS = 16000
JUDGE_CONCURRENCY = 8

JUDGE_SYSTEM = """You are grading answers produced by a financial research assistant for retail investors. The answers are in Traditional Chinese.

For each answer you receive the user's question, a list of pass signals, and the answer. Decide independently for every signal whether the answer satisfies it.

Grading rules:
- Judge only the answer text in front of you. You have no access to the sources the assistant used, so do not try to verify facts; judge whether the answer itself does what the signal asks.
- Pass (1) only when the answer clearly and specifically satisfies the signal for this question. Fail (0) when the signal is met only vaguely, generically, partially, or not at all.
- A signal about evidence or sources (e.g. citing disclosures, naming concrete events, tying conclusions to news) needs that evidence to actually appear in the answer: named events, figures, filings or cited sources. Asserting a conclusion without them is a fail.
- A signal about a conclusion or judgement needs an explicit conclusion that answers this question, not a hedge or a list of considerations.
- An answer that addresses a different question or company fails every signal it does not satisfy for this question.
- Length, style and formatting are not signals. Do not reward or penalise them beyond what a signal asks.

Write each reason as one short line in Traditional Chinese naming what in the answer made it pass or fail."""

JUDGE_SCHEMA = {
    "type": "object",
    "properties": {
        "scores": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "signal": {"type": "integer"},
                    "pass": {"type": "integer", "enum": [0, 1]},
                    "reason": {"type": "string"},
                },
                "required": ["signal", "pass", "reason"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["scores"],
    "additionalProperties": False,
}

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


def cmd_build_pool(raw_dir: Path, out_dir: Path) -> int:
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
    batches: list[list[dict[str, Any]]] = []
    for index, (item, meta) in enumerate(items, start=1):
        item_id = f"J{index:04d}"
        key[item_id] = meta
        row = dataset[item["row_id"]]
        entry = {
            "id": item_id,
            "question": row["question"],
            "signals": row["signals"],
            "answer": item["answer"],
        }
        if (index - 1) % BATCH_SIZE == 0:
            batches.append([])
        batches[-1].append(entry)

    (out_dir / "batches").mkdir(parents=True, exist_ok=True)
    for n, batch in enumerate(batches, start=1):
        (out_dir / "batches" / f"batch_{n}.json").write_text(
            json.dumps(batch, ensure_ascii=False, indent=1)
        )
    (out_dir / "KEY_do_not_share.json").write_text(
        json.dumps(key, ensure_ascii=False, indent=1)
    )
    kinds = defaultdict(int)
    for meta in key.values():
        kinds[meta["kind"]] += 1
    print(f"{len(key)} items in {len(batches)} batches: {dict(kinds)}")
    return 0


def _user_message(item: dict[str, Any]) -> str:
    signals = "\n".join(f"{i}. {s}" for i, s in enumerate(item["signals"]))
    return (
        f"<question>\n{item['question']}\n</question>\n\n"
        f"<signals>\n{signals}\n</signals>\n\n"
        f"<answer>\n{item['answer'] or '(empty answer)'}\n</answer>\n\n"
        "Return one score per signal, using the signal numbers above."
    )


async def _judge_one(
    client: anthropic.AsyncAnthropic, item: dict[str, Any], sem: asyncio.Semaphore
) -> dict[str, Any]:
    async with sem:
        response = await client.messages.create(
            model=JUDGE_MODEL,
            max_tokens=JUDGE_MAX_TOKENS,
            system=JUDGE_SYSTEM,
            output_config={
                "effort": JUDGE_EFFORT,
                "format": {"type": "json_schema", "schema": JUDGE_SCHEMA},
            },
            messages=[{"role": "user", "content": _user_message(item)}],
        )
    if response.stop_reason != "end_turn":
        raise RuntimeError(f"{item['id']}: stop_reason={response.stop_reason}")
    text = next(b.text for b in response.content if b.type == "text")
    scores = json.loads(text)["scores"]
    if sorted(s["signal"] for s in scores) != list(range(len(item["signals"]))):
        raise RuntimeError(f"{item['id']}: signal indices {scores}")
    return {
        "id": item["id"],
        "scores": sorted(scores, key=lambda s: s["signal"]),
        "usage": {
            "input_tokens": response.usage.input_tokens,
            "output_tokens": response.usage.output_tokens,
        },
        "request_id": response._request_id,
    }


async def _judge_all(
    items: list[dict[str, Any]], cache_dir: Path
) -> dict[str, dict[str, Any]]:
    cache_dir.mkdir(parents=True, exist_ok=True)
    client = anthropic.AsyncAnthropic(max_retries=6)
    sem = asyncio.Semaphore(JUDGE_CONCURRENCY)
    todo = [it for it in items if not (cache_dir / f"{it['id']}.json").exists()]
    print(f"{len(items) - len(todo)} cached, {len(todo)} to judge", flush=True)

    async def run(item: dict[str, Any]) -> None:
        try:
            result = await _judge_one(client, item, sem)
        except Exception as exc:
            print(f"FAILED {item['id']}: {type(exc).__name__}: {exc}", flush=True)
            return
        (cache_dir / f"{item['id']}.json").write_text(
            json.dumps(result, ensure_ascii=False, indent=1)
        )

    await asyncio.gather(*(run(it) for it in todo))
    return {
        p.stem: json.loads(p.read_text()) for p in sorted(cache_dir.glob("J*.json"))
    }


def _judge_config() -> dict[str, Any]:
    return {
        "model": JUDGE_MODEL,
        "output_config": {"effort": JUDGE_EFFORT, "format": "json_schema"},
        "thinking": "adaptive (default; cannot be disabled on this model)",
        "temperature": "not settable on this model",
        "max_tokens": JUDGE_MAX_TOKENS,
        "one_request_per_answer": True,
        "system_prompt": JUDGE_SYSTEM,
        "system_prompt_sha256": hashlib.sha256(JUDGE_SYSTEM.encode()).hexdigest(),
        "schema": JUDGE_SCHEMA,
        "anthropic_sdk": anthropic.__version__,
    }


def _load_batches(pool_dir: Path) -> list[list[dict[str, Any]]]:
    paths = sorted(
        (pool_dir / "batches").glob("batch_*.json"),
        key=lambda p: int(p.stem.split("_")[1]),
    )
    return [json.loads(p.read_text()) for p in paths]


def cmd_judge(pool_dir: Path, rejudge: int | None, limit: int | None) -> int:
    batches = _load_batches(pool_dir)
    items = [item for batch in batches for item in batch]
    if rejudge:
        items = random.Random(POOL_SEED + 1).sample(items, rejudge)
        cache_dir = pool_dir / "rejudge"
    else:
        cache_dir = pool_dir / "judge_cache"
    if limit:
        items = items[:limit]
    results = asyncio.run(_judge_all(items, cache_dir))
    config = {**_judge_config(), "judged_at": datetime.now(timezone.utc).isoformat()}
    (cache_dir / "judge_config.json").write_text(
        json.dumps(config, ensure_ascii=False, indent=1)
    )
    if not rejudge and not limit:
        (pool_dir / "results").mkdir(exist_ok=True)
        for n, batch in enumerate(batches, start=1):
            out = [
                {"id": it["id"], "scores": results[it["id"]]["scores"]}
                for it in batch
                if it["id"] in results
            ]
            (pool_dir / "results" / f"result_{n}.json").write_text(
                json.dumps(out, ensure_ascii=False, indent=1)
            )
        (pool_dir / "judge_config.json").write_text(
            json.dumps(config, ensure_ascii=False, indent=1)
        )
    usage_in = sum(r["usage"]["input_tokens"] for r in results.values())
    usage_out = sum(r["usage"]["output_tokens"] for r in results.values())
    missing = [it["id"] for it in items if it["id"] not in results]
    print(
        f"judged {len(results)}/{len(items)}; missing {missing[:10]}; "
        f"tokens in={usage_in} out={usage_out}"
    )
    return 0 if not missing else 1


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


def cmd_score(pool_dir: Path, out_dir: Path) -> int:
    key = json.loads((pool_dir / "KEY_do_not_share.json").read_text())
    results = {
        p.stem: json.loads(p.read_text())
        for p in sorted((pool_dir / "judge_cache").glob("J*.json"))
    }
    entries = []
    for item_id, meta in key.items():
        if item_id not in results:
            continue
        scores = results[item_id]["scores"]
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
    arms = {}
    for arm in ARM_NAMES:
        arms[arm] = {
            "answers": sum(1 for e in entries if e["group"] == arm),
            "signal_pass_rate": _ci(rate[arm]),
            "all_signals_pass": _ci(all_pass[arm]),
        }
    contrasts = {
        arm: {
            "signal_pass_rate": _paired(rate[arm], rate[CONTROL_ARM]),
            "all_signals_pass": _paired(all_pass[arm], all_pass[CONTROL_ARM]),
        }
        for arm in ARM_NAMES
        if arm != CONTROL_ARM
    }

    # Discrimination: each control vs the real answer it was built from
    # (off_topic: vs the real answers to this row, all arms pooled).
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
        discrimination[kind] = {
            "n": len(controls),
            "control_pass_rate": _ci({e["row"]: e["pass_rate"] for e in controls}),
            "delta_vs_real": _ci(pairs),
        }
    real_overall = _ci(real_by_row)

    agreement = None
    rejudge_dir = pool_dir / "rejudge"
    if rejudge_dir.exists():
        same = total = items_same = items = 0
        for p in rejudge_dir.glob("J*.json"):
            second = json.loads(p.read_text())["scores"]
            first = results[p.stem]["scores"]
            matches = [a["pass"] == b["pass"] for a, b in zip(first, second)]
            same += sum(matches)
            total += len(matches)
            items_same += all(matches)
            items += 1
        agreement = {
            "items": items,
            "signal_agreement": same / total if total else None,
            "item_exact_agreement": items_same / items if items else None,
        }

    per_signal = defaultdict(list)
    for e in entries:
        if e["kind"] == "real":
            for i, p in enumerate(e["passes"]):
                per_signal[(e["row"], i)].append(p)
    signal_ceiling = {
        "signals": len(per_signal),
        "always_pass": sum(1 for v in per_signal.values() if all(v)),
        "always_fail": sum(1 for v in per_signal.values() if not any(v)),
    }

    summary = {
        "judged": len(entries),
        "real_overall_signal_pass_rate": real_overall,
        "arms": arms,
        "contrasts_vs_control": contrasts,
        "discrimination": discrimination,
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


def cmd_spot_check(pool_dir: Path, out_dir: Path, n_per_arm: int = 3) -> int:
    """Blinded 15-answer sample: 3 real answers per arm + 1 per control kind.

    Within each arm, answers with at least one failed signal are taken
    first (up to one), so the sample contains the judge's fails, not only
    its passes.
    """
    key = json.loads((pool_dir / "KEY_do_not_share.json").read_text())
    items = {it["id"]: it for b in _load_batches(pool_dir) for it in b}
    results = {
        p.stem: json.loads(p.read_text())["scores"]
        for p in (pool_dir / "judge_cache").glob("J*.json")
    }
    rng = random.Random(POOL_SEED + 2)
    picked: list[str] = []
    for arm in ARM_NAMES:
        ids = sorted(
            i for i, m in key.items() if m.get("arm") == arm and m["kind"] == "real"
        )
        failing = [i for i in ids if not all(s["pass"] for s in results[i])]
        chosen = rng.sample(failing, min(1, len(failing)))
        rest = [i for i in ids if i not in chosen]
        chosen += rng.sample(rest, n_per_arm - len(chosen))
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
        "For each answer, read the question and answer, then for every signal "
        "mark in `spot_check.csv` whether **you** think it passes "
        "(`human_pass` = 1 / 0). The judge's verdict and reason are shown so "
        "you can disagree with them; the answer's source is not shown.",
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
    build.add_argument("--out-dir", type=Path, required=True)
    judge = sub.add_parser("judge")
    judge.add_argument("--pool-dir", type=Path, required=True)
    judge.add_argument("--rejudge", type=int)
    judge.add_argument("--limit", type=int, help="Judge only the first N (smoke)")
    score = sub.add_parser("score")
    score.add_argument("--pool-dir", type=Path, required=True)
    score.add_argument("--out-dir", type=Path, required=True)
    spot = sub.add_parser("spot-check")
    spot.add_argument("--pool-dir", type=Path, required=True)
    spot.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args(argv)

    if args.cmd == "build-pool":
        return cmd_build_pool(args.raw_dir, args.out_dir)
    if args.cmd == "judge":
        return cmd_judge(args.pool_dir, args.rejudge, args.limit)
    if args.cmd == "score":
        return cmd_score(args.pool_dir, args.out_dir)
    return cmd_spot_check(args.pool_dir, args.out_dir)


if __name__ == "__main__":
    raise SystemExit(main())
