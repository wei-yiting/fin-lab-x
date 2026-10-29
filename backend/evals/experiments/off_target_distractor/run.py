"""Off-target distractor eval: C1 (recorded Tavily output) vs C0 (same output
with unrelated-company sentences removed), reader_luna_medium only.

Tavily is replayed from ``fixtures.json``; every other tool is live (SEC via
the local Qdrant index, Finnhub via the API). Runs are interleaved
row x condition x repetition, with the condition order alternating by row
and repetition, and executed with bounded concurrency. One raw JSON per run.
"""

from __future__ import annotations

import argparse
import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import Any

from backend.evals.eval_runner import _build_diagnostic_eval_rows
from backend.evals.eval_spec_schema import load_scenario_config
from backend.evals.eval_tasks import _get_orchestrator_from_dir
from backend.evals.experiments.harness import (
    BACKEND_DIR,
    BENCHMARK_DIR,
    SCENARIO_DIR,
    Arm,
    _LocalOnlyExperiment,
    load_rows,
    prewarm,
    resolve_arm,
    run_one,
)
from backend.evals.experiments.off_target_distractor import replay
from backend.evals.experiments.off_target_distractor.fixtures import FIXTURE_PATH

EXPERIMENT_NAME = "off-target-distractor"
READER_PROMPT = (
    BACKEND_DIR / "agent_engine" / "agents" / "profiles" / "reader" / "system_prompt.md"
)
# Primary arm is reader_luna_medium; reader_luna_none is the exploratory
# sensitivity arm (the reader 2x2 saw more synthesis errors without reasoning).
ARMS = {
    name: Arm(name, BENCHMARK_DIR / "ablations" / name, READER_PROMPT)
    for name in ("reader_luna_medium", "reader_luna_none")
}
CONDITIONS = ("C0", "C1")
# Exploratory prompt variant: an open news-recap question over the same
# fixtures (the trace failure was seen on recap-style prompts, which invite
# listing whatever the search returned).
RECAP_TEMPLATE = "{companies} 最近有什麼新聞？"


def plan(row_ids: list[str], reps: int) -> list[tuple[int, str, str]]:
    order = []
    for rep in range(1, reps + 1):
        for position, row_id in enumerate(row_ids):
            first = (position + rep) % 2
            for cond in (CONDITIONS[first], CONDITIONS[1 - first]):
                order.append((rep, row_id, cond))
    return order


async def _one(
    arm: Arm,
    rep: int,
    row_id: str,
    cond: str,
    slot: int,
    eval_row: dict[str, Any],
    fixture: dict[str, Any],
    raw_dir: Path,
    sem: asyncio.Semaphore,
) -> None:
    raw_path = raw_dir / f"rep{rep}" / f"row{int(row_id):02d}__{cond}.json"
    if raw_path.exists():
        return
    async with sem:
        state = replay.ReplayState(calls=fixture[cond])
        token = replay.replay_state.set(state)
        print(
            f"[{datetime.now():%H:%M:%S}] start {arm.name} rep{rep} row {row_id} {cond}",
            flush=True,
        )
        try:
            record = await run_one(
                arm=arm,
                eval_row=eval_row,
                experiment=_LocalOnlyExperiment(),
                order={"repetition": rep, "condition": cond, "plan_slot": slot},
            )
        finally:
            replay.replay_state.reset(token)
        record["condition"] = cond
        record["tavily_replay"] = state.served
        raw_path.parent.mkdir(parents=True, exist_ok=True)
        raw_path.write_text(
            json.dumps(record, indent=2, ensure_ascii=False, default=str)
        )
        timing = (record["output"] or {}).get("timing", {})
        print(
            f"    done rep{rep} row {row_id} {cond}: error={record['task_error']} "
            f"tavily_calls={len(state.served)} total_s={timing.get('total_s')}",
            flush=True,
        )


async def run(
    arm: Arm,
    out_dir: Path,
    row_ids: list[str],
    reps: int,
    concurrency: int,
    do_prewarm: bool,
    prompt_variant: str,
) -> None:
    fixtures = json.loads(FIXTURE_PATH.read_text())["rows"]
    replay.install()
    _get_orchestrator_from_dir.cache_clear()
    resolved = resolve_arm(arm)
    orchestrator = _get_orchestrator_from_dir(arm.config_dir, arm.prompt_path)
    news = [t for t in orchestrator.tools if t.name == replay.replay_tavily.name]
    if news != [replay.replay_tavily]:
        raise SystemExit("orchestrator is not using the Tavily replay tool")
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / f"resolved_{arm.name}.json").write_text(json.dumps(resolved, indent=2))

    if do_prewarm:
        report = await prewarm(["sec_filing_list_sections", "sec_filing_search"])
        (out_dir / "prewarm.json").write_text(json.dumps(report, indent=2))

    scenario = load_scenario_config(SCENARIO_DIR / "eval_spec.yaml")
    diagnostic = scenario.diagnostic
    rows = {r["id"]: r for r in load_rows("all")}
    sem = asyncio.Semaphore(concurrency)
    jobs = []
    for slot, (rep, row_id, cond) in enumerate(plan(row_ids, reps)):
        eval_row = _build_diagnostic_eval_rows(
            selected_rows=[rows[row_id]],
            column_mapping=scenario.column_mapping,
            column_types=scenario.column_types,
            dataset_name=diagnostic.dataset_name,
            dataset_version=diagnostic.dataset_version,
            run_label=f"{EXPERIMENT_NAME}-{cond}-rep{rep}",
            agent_version=arm.name,
            experiment_name=f"{EXPERIMENT_NAME}_{cond}_rep{rep}",
        )[0]
        if prompt_variant == "recap":
            companies = " 和 ".join(fixtures[row_id]["target_companies"])
            eval_row["input"] = {
                **eval_row["input"],
                "question": RECAP_TEMPLATE.format(companies=companies),
            }
        run_dir = (
            arm.name
            if prompt_variant == "original"
            else f"{arm.name}__{prompt_variant}"
        )
        jobs.append(
            _one(
                arm,
                rep,
                row_id,
                cond,
                slot,
                eval_row,
                fixtures[row_id],
                out_dir / "raw" / run_dir,
                sem,
            )
        )
    await asyncio.gather(*jobs)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--arm", choices=sorted(ARMS), default="reader_luna_medium")
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--rows", required=True, help="comma-separated row ids")
    parser.add_argument("--reps", type=int, default=3)
    parser.add_argument("--concurrency", type=int, default=6)
    parser.add_argument("--no-prewarm", action="store_true")
    parser.add_argument(
        "--prompt-variant", choices=["original", "recap"], default="original"
    )
    args = parser.parse_args()
    asyncio.run(
        run(
            ARMS[args.arm],
            args.out_dir,
            args.rows.split(","),
            args.reps,
            args.concurrency,
            not args.no_prewarm,
            args.prompt_variant,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
