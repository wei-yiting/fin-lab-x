"""Agent-config benchmark on the zh diagnostic dev split (DEV-206).

Two questions share one batch of runs:

- E1 (ablation): does the RAG capability bundle (``sec_filing_search`` +
  the reader prompt) beat reading whole 10-K sections? Arm A =
  ``configs/luna_medium``, Arm B = ``ablations/reader_luna_medium`` — same
  model, reasoning effort, temperature and tool budget.
- E2 (2x2): model family x reasoning strength over the 4 benchmark configs.
  ``luna_medium`` doubles as E1's Arm A.

Subcommands:

- ``dump``: resolve every arm's config (model kwargs as actually built,
  tools, prompt hashes) into JSON and diff Arm A vs Arm B. Exits non-zero
  if they differ anywhere except identity, tools and prompt.
- ``run``: pre-warm the SEC caches for the dev-row tickers, then execute
  dev rows x arms row-major (one row through every arm before the next row),
  n=1, logging each arm to its own Braintrust experiment and writing one raw
  JSON per run.

Only dev rows are ever read (``apply_split`` defaults to dev-only); this
module never edits ``split.json``.
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import sys
import time
import traceback
from contextvars import ContextVar
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import UUID

from langchain_core.callbacks import AsyncCallbackHandler
from langchain_core.tracers.context import register_configure_hook

from backend.agent_engine.agents.base import Orchestrator, _init_model
from backend.agent_engine.agents.config_loader import ProfileConfigLoader
from backend.evals.dataset_loader import load_raw_csv_rows
from backend.evals.diagnostic.execution_scorer import execution_health
from backend.evals.diagnostic.row_selection import apply_split, load_split_sidecar
from backend.evals.eval_runner import (
    BRAINTRUST_CONFIG_PATH,
    _build_diagnostic_eval_rows,
    _git_sha,
)
from backend.evals.eval_spec_schema import load_braintrust_config, load_scenario_config
from backend.evals.eval_tasks import run_baseline_behavior_diagnostic
from backend.evals.scenarios.language_policy.scorer import (
    response_no_simplified_chars,
)

BACKEND_DIR = Path(__file__).resolve().parents[3]
SCENARIO_DIR = BACKEND_DIR / "evals" / "scenarios" / "baseline_behavior_diagnostic_zh"
BENCHMARK_DIR = SCENARIO_DIR / "benchmark"
CANONICAL_PROMPT = BENCHMARK_DIR / "prompt" / "system_prompt.md"
READER_PROMPT = (
    BACKEND_DIR / "agent_engine" / "agents" / "profiles" / "reader" / "system_prompt.md"
)

TASK_TIMEOUT_S = 600

# Tickers the dev rows ask about that file 10-Ks (Airbus, row 29, does not).
DEV_ROW_TICKERS = ["BA", "JNJ", "AAPL", "META", "V", "MA", "AMZN", "KO", "TSLA", "NVDA"]


@dataclass(frozen=True)
class Arm:
    name: str
    config_dir: Path
    prompt_path: Path
    experiments: tuple[str, ...]


ARM_A = "luna_medium"
ARM_B = "reader_luna_medium"
E2_OTHERS = ["luna_none", "gemini_minimal", "gemini_medium"]

ARMS: dict[str, Arm] = {
    ARM_A: Arm(
        ARM_A, BENCHMARK_DIR / "configs" / ARM_A, CANONICAL_PROMPT, ("E1", "E2")
    ),
    ARM_B: Arm(ARM_B, BENCHMARK_DIR / "ablations" / ARM_B, READER_PROMPT, ("E1",)),
    **{
        name: Arm(name, BENCHMARK_DIR / "configs" / name, CANONICAL_PROMPT, ("E2",))
        for name in E2_OTHERS
    },
}


def arm_order(row_index: int) -> list[str]:
    """Run order for the ``row_index``-th dev row.

    The E1 pair runs back-to-back (smallest live-data gap between A and B)
    and alternates which arm goes first; the other E2 arms rotate.
    """
    pair = [ARM_A, ARM_B] if row_index % 2 == 0 else [ARM_B, ARM_A]
    shift = row_index % len(E2_OTHERS)
    return pair + E2_OTHERS[shift:] + E2_OTHERS[:shift]


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


# ---------------------------------------------------------------------------
# dump
# ---------------------------------------------------------------------------


def resolve_arm(arm: Arm) -> dict[str, Any]:
    """Everything that controls an arm's behavior, as actually resolved."""
    config = ProfileConfigLoader.load_from_dir(
        arm.config_dir, prompt_path=arm.prompt_path
    )
    chat_model = _init_model(config.model)
    orchestrator = Orchestrator(config, checkpointer=None)
    tool_descriptions = {
        tool.name: {
            "description_sha256": _sha256(tool.description or ""),
            "args_schema_sha256": _sha256(
                json.dumps(tool.args, sort_keys=True, default=str)
            ),
        }
        for tool in orchestrator.tools
    }
    return {
        "arm": arm.name,
        "config_dir": str(arm.config_dir.relative_to(BACKEND_DIR)),
        "prompt_path": str(arm.prompt_path.relative_to(BACKEND_DIR)),
        "identity": {"name": config.name, "description": config.description},
        "config_model": config.model.model_dump(),
        "built_model": {
            "class": type(chat_model).__name__,
            "model": getattr(chat_model, "model_name", None)
            or getattr(chat_model, "model", None),
            "temperature": getattr(chat_model, "temperature", None),
            "reasoning": getattr(chat_model, "reasoning", None),
            "use_responses_api": getattr(chat_model, "use_responses_api", None),
            "thinking_level": getattr(chat_model, "thinking_level", None),
            "thinking_budget": getattr(chat_model, "thinking_budget", None),
            "include_thoughts": getattr(chat_model, "include_thoughts", None),
        },
        "constraints": config.constraints.model_dump(),
        "tools": config.tools,
        "tool_contracts": tool_descriptions,
        "prompt": {
            "raw_sha256": _sha256(config.system_prompt or ""),
            "rendered_sha256": _sha256(orchestrator.system_prompt),
            "raw_chars": len(config.system_prompt or ""),
        },
    }


# Keys allowed to differ between Arm A and Arm B: identity (name/description
# strings), the tool list and its contracts, and the prompt — i.e. the RAG
# bundle under test.
_E1_ALLOWED_DIFF = {
    "arm",
    "config_dir",
    "prompt_path",
    "identity",
    "tools",
    "tool_contracts",
    "prompt",
}


def diff_e1(a: dict[str, Any], b: dict[str, Any]) -> dict[str, Any]:
    differing = sorted(k for k in a.keys() | b.keys() if a.get(k) != b.get(k))
    shared_tools = set(a["tools"]) & set(b["tools"])
    return {
        "differing_keys": differing,
        "unexpected_differences": [k for k in differing if k not in _E1_ALLOWED_DIFF],
        "tools_only_in_b": [t for t in b["tools"] if t not in a["tools"]],
        "tools_only_in_a": [t for t in a["tools"] if t not in b["tools"]],
        "shared_tool_contracts_identical": all(
            a["tool_contracts"][t] == b["tool_contracts"][t] for t in shared_tools
        ),
    }


def cmd_dump(out_dir: Path) -> int:
    out_dir.mkdir(parents=True, exist_ok=True)
    resolved = {name: resolve_arm(arm) for name, arm in ARMS.items()}
    (out_dir / "resolved_configs.json").write_text(
        json.dumps(resolved, indent=2, ensure_ascii=False, default=str)
    )
    diff = diff_e1(resolved[ARM_A], resolved[ARM_B])
    (out_dir / "e1_config_diff.json").write_text(json.dumps(diff, indent=2))
    print(json.dumps(diff, indent=2))
    ok = not diff["unexpected_differences"] and diff["shared_tool_contracts_identical"]
    print("E1 config alignment:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


# ---------------------------------------------------------------------------
# run
# ---------------------------------------------------------------------------


class RunCollector(AsyncCallbackHandler):
    """Per-run LangChain callback: model-call usage and tool timings.

    Registered through ``register_configure_hook`` (the same mechanism the
    Braintrust handler uses), so it sees every model/tool run without
    touching the orchestrator.
    """

    def __init__(self) -> None:
        self._starts: dict[UUID, float] = {}
        self._tool_names: dict[UUID, str] = {}
        self.llm_calls: list[dict[str, Any]] = []
        self.tool_runs: list[dict[str, Any]] = []

    async def on_chat_model_start(self, serialized, messages, *, run_id, **kwargs):
        self._starts[run_id] = time.perf_counter()

    async def on_llm_end(self, response, *, run_id, **kwargs):
        usage: dict[str, Any] = {}
        try:
            message = response.generations[0][0].message
            usage = dict(getattr(message, "usage_metadata", None) or {})
        except (AttributeError, IndexError):
            pass
        started = self._starts.pop(run_id, None)
        self.llm_calls.append(
            {
                "duration_s": None
                if started is None
                else time.perf_counter() - started,
                "input_tokens": usage.get("input_tokens", 0),
                "output_tokens": usage.get("output_tokens", 0),
                "reasoning_tokens": (usage.get("output_token_details") or {}).get(
                    "reasoning", 0
                ),
                "cache_read_tokens": (usage.get("input_token_details") or {}).get(
                    "cache_read", 0
                ),
            }
        )

    async def on_tool_start(self, serialized, input_str, *, run_id, **kwargs):
        self._starts[run_id] = time.perf_counter()
        self._tool_names[run_id] = (serialized or {}).get("name") or kwargs.get(
            "name", "unknown"
        )

    async def on_tool_end(self, output, *, run_id, **kwargs):
        self._finish_tool(run_id, error=None)

    async def on_tool_error(self, error, *, run_id, **kwargs):
        self._finish_tool(run_id, error=str(error))

    def _finish_tool(self, run_id: UUID, *, error: str | None) -> None:
        started = self._starts.pop(run_id, None)
        self.tool_runs.append(
            {
                "tool": self._tool_names.pop(run_id, "unknown"),
                "duration_s": None
                if started is None
                else time.perf_counter() - started,
                "error": error,
            }
        )


_collector_var: ContextVar[RunCollector | None] = ContextVar(
    "agent_config_benchmark_collector", default=None
)
register_configure_hook(context_var=_collector_var, inheritable=True)


def load_dev_rows() -> tuple[list[str], list[dict[str, str]]]:
    columns, rows = load_raw_csv_rows(SCENARIO_DIR / "dataset.csv")
    split = load_split_sidecar(BENCHMARK_DIR / "split.json")
    return columns, apply_split(rows, split)


def _tool_call(name: str, **args: Any) -> dict[str, Any]:
    return {"name": name, "args": args, "id": f"prewarm-{name}", "type": "tool_call"}


async def prewarm() -> list[dict[str, Any]]:
    """Fetch + index each dev ticker's latest 10-K before any timed run.

    Without this the first arm to touch a ticker pays EDGAR download and
    JIT embedding (minutes) inside its latency, and which arm that is
    depends on run order. Runs in-process so ``sec_core``'s lru caches are
    warm too.
    """
    from backend.agent_engine.tools import setup_tools
    from backend.agent_engine.tools.registry import get_tool

    setup_tools()
    list_sections = get_tool("sec_filing_list_sections")
    search = get_tool("sec_filing_search")
    report = []
    for ticker in DEV_ROW_TICKERS:
        entry: dict[str, Any] = {"ticker": ticker}
        started = time.perf_counter()
        try:
            # Both tools take an InjectedToolCallId, so they must be invoked
            # with a full ToolCall rather than bare args.
            listing = await asyncio.to_thread(
                list_sections.invoke, _tool_call(list_sections.name, ticker=ticker)
            )
            entry["list_sections_s"] = round(time.perf_counter() - started, 1)
            entry["list_sections_status"] = getattr(listing, "status", None)
            started = time.perf_counter()
            found = await search.ainvoke(
                _tool_call(search.name, query="risk factors", ticker=ticker)
            )
            entry["search_s"] = round(time.perf_counter() - started, 1)
            entry["search_status"] = getattr(found, "status", None)
        except Exception as exc:
            entry["error"] = f"{type(exc).__name__}: {exc}"
        print("prewarm", entry, flush=True)
        report.append(entry)
    return report


def _score(output: dict[str, Any]) -> tuple[dict[str, float | None], dict[str, Any]]:
    health = execution_health(output, {})
    scores: dict[str, float | None] = {"diagnostic_execution_health": health["score"]}
    metadata: dict[str, Any] = {"execution_health": health["metadata"]}
    simplified = response_no_simplified_chars(output, {"cjk_min": 0.3}, input=None)
    if simplified is not None:
        scores["response_no_simplified_chars"] = simplified.score
        metadata["response_no_simplified_chars"] = simplified.metadata
    return scores, metadata


async def run_one(
    *, arm: Arm, eval_row: dict[str, Any], experiment: Any, order: dict[str, Any]
) -> dict[str, Any]:
    collector = RunCollector()
    token = _collector_var.set(collector)
    started_at = datetime.now(tz=timezone.utc).isoformat()
    error: str | None = None
    output: dict[str, Any] | None = None
    with experiment.start_span(
        name="task",
        input=eval_row["input"],
        metadata={**eval_row["metadata"], "arm": arm.name, **order},
    ) as span:
        try:
            output = dict(
                await asyncio.wait_for(
                    run_baseline_behavior_diagnostic(
                        eval_row["input"],
                        config_dir=arm.config_dir,
                        prompt_path=arm.prompt_path,
                    ),
                    timeout=TASK_TIMEOUT_S,
                )
            )
        except Exception as exc:
            error = f"{type(exc).__name__}: {exc}"
            traceback.print_exc()
        finally:
            _collector_var.reset(token)
        scores, score_metadata = _score(output or {})
        span.log(
            output=output if output is not None else {"error": error},
            scores=scores,
            metadata={"score_details": score_metadata, "task_error": error},
        )
        span_id = getattr(span, "id", None)
    return {
        "row_id": eval_row["id"],
        "arm": arm.name,
        "experiments": list(arm.experiments),
        **order,
        "started_at": started_at,
        "finished_at": datetime.now(tz=timezone.utc).isoformat(),
        "task_error": error,
        "output": output,
        "scores": scores,
        "score_details": score_metadata,
        "llm_calls": collector.llm_calls,
        "tool_runs": collector.tool_runs,
        "braintrust_span_id": span_id,
    }


async def cmd_run(
    out_dir: Path, row_ids: list[str] | None, arms: list[str] | None, label: str
) -> int:
    import braintrust
    from braintrust.integrations.langchain import (
        BraintrustCallbackHandler,
        set_global_handler,
    )

    raw_dir = out_dir / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)

    columns, dev_rows = load_dev_rows()
    dev_ids = [row["id"] for row in dev_rows]
    if row_ids is not None:
        unknown = [r for r in row_ids if r not in dev_ids]
        if unknown:
            raise SystemExit(f"Not dev rows: {unknown} (dev = {dev_ids})")
        dev_rows = [row for row in dev_rows if row["id"] in row_ids]
    selected_arms = arms or list(ARMS)

    scenario = load_scenario_config(SCENARIO_DIR / "eval_spec.yaml")
    diagnostic = scenario.diagnostic
    git_sha = _git_sha()
    bt_config = load_braintrust_config(BRAINTRUST_CONFIG_PATH)

    prewarm_report = await prewarm()
    (out_dir / f"prewarm_{label}.json").write_text(json.dumps(prewarm_report, indent=2))

    set_global_handler(BraintrustCallbackHandler())
    experiments = {
        name: braintrust.init(
            project=bt_config.project,
            experiment=f"agent-config-benchmark-dev_{label}_{name}",
            metadata={
                "dataset_name": diagnostic.dataset_name,
                "dataset_version": diagnostic.dataset_version,
                "split": "dev",
                "selected_row_ids": [row["id"] for row in dev_rows],
                "arm": name,
                "config_dir": str(ARMS[name].config_dir.relative_to(BACKEND_DIR)),
                "prompt_path": str(ARMS[name].prompt_path.relative_to(BACKEND_DIR)),
                "experiments": list(ARMS[name].experiments),
                "git_commit": git_sha,
                "run_label": label,
                "n": 1,
                "execution": "row-major",
            },
        )
        for name in selected_arms
    }

    for row_index, row in enumerate(dev_rows):
        position = dev_ids.index(row["id"])
        order = [a for a in arm_order(position) if a in selected_arms]
        for slot, arm_name in enumerate(order):
            raw_path = raw_dir / f"row{int(row['id']):02d}__{arm_name}.json"
            if raw_path.exists():
                print(f"skip {raw_path.name} (exists)", flush=True)
                continue
            arm = ARMS[arm_name]
            eval_row = _build_diagnostic_eval_rows(
                selected_rows=[row],
                column_mapping=scenario.column_mapping,
                column_types=scenario.column_types,
                dataset_name=diagnostic.dataset_name,
                dataset_version=diagnostic.dataset_version,
                run_label=f"{label}-{arm_name}",
                agent_version=arm_name,
                experiment_name=f"agent-config-benchmark-dev_{label}_{arm_name}",
            )[0]
            print(
                f"[{datetime.now():%H:%M:%S}] row {row['id']} ({row_index + 1}/"
                f"{len(dev_rows)}) slot {slot} {arm_name}",
                flush=True,
            )
            record = await run_one(
                arm=arm,
                eval_row=eval_row,
                experiment=experiments[arm_name],
                order={
                    "row_position": position,
                    "slot_in_row": slot,
                    "row_order": order,
                },
            )
            raw_path.write_text(
                json.dumps(record, indent=2, ensure_ascii=False, default=str)
            )
            timing = (record["output"] or {}).get("timing", {})
            print(
                f"    done: error={record['task_error']} scores={record['scores']} "
                f"total_s={timing.get('total_s')} tools={len((record['output'] or {}).get('tool_outputs', []))}",
                flush=True,
            )

    links = {}
    for name, experiment in experiments.items():
        summary = experiment.summarize(summarize_scores=False)
        links[name] = getattr(summary, "experiment_url", None)
        print(name, links[name], flush=True)
    (out_dir / f"braintrust_links_{label}.json").write_text(json.dumps(links, indent=2))
    braintrust.flush()
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="cmd", required=True)
    dump = sub.add_parser("dump")
    dump.add_argument("--out-dir", type=Path, required=True)
    run = sub.add_parser("run")
    run.add_argument("--out-dir", type=Path, required=True)
    run.add_argument("--label", required=True)
    run.add_argument("--row-ids", help="Comma-separated dev row ids (default: all dev)")
    run.add_argument("--arms", help=f"Comma-separated arms (default: {','.join(ARMS)})")
    args = parser.parse_args(argv)

    if args.cmd == "dump":
        return cmd_dump(args.out_dir)
    row_ids = args.row_ids.split(",") if args.row_ids else None
    arms = args.arms.split(",") if args.arms else None
    if arms:
        unknown = [a for a in arms if a not in ARMS]
        if unknown:
            parser.error(f"Unknown arms: {unknown}")
    return asyncio.run(cmd_run(args.out_dir, row_ids, arms, args.label))


if __name__ == "__main__":
    sys.exit(main())
