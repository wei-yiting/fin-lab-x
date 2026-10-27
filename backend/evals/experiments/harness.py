"""Shared machinery for agent-config experiments on the zh diagnostic scenario.

An experiment module defines its ``Arm``s and a per-row run order; this
module resolves arms the way the orchestrator does, pre-warms SEC caches,
and runs rows x arms row-major (every arm on a row before the next row),
logging each (arm, repetition) to its own Braintrust experiment and writing
one raw JSON per run.

Row selection: ``dev`` goes through ``apply_split``'s dev-only default;
``all`` is an explicit, recorded opt-out of the split (the split is still
``proposed``, so this is a pre-protocol exploration run, not a holdout
evaluation). ``split.json`` is never modified.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import time
import traceback
from collections.abc import Callable, Sequence
from contextvars import ContextVar
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal
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

BACKEND_DIR = Path(__file__).resolve().parents[2]
SCENARIO_DIR = BACKEND_DIR / "evals" / "scenarios" / "baseline_behavior_diagnostic_zh"
BENCHMARK_DIR = SCENARIO_DIR / "benchmark"
CANONICAL_PROMPT = BENCHMARK_DIR / "prompt" / "system_prompt.md"

TASK_TIMEOUT_S = 600

# 10-K filers named by the 30 dataset rows. TSMC and ASML file 20-Fs and
# Airbus is not an SEC registrant, so none of them can be pre-warmed.
DATASET_TICKERS = [
    "TSLA", "DIS", "BA", "INTC", "JNJ", "GOOGL", "JPM", "AAPL", "META", "WMT",
    "XOM", "V", "MA", "COST", "AMZN", "KO", "PEP", "BRK-B", "MSFT", "NVDA",
    "NFLX", "LLY", "NKE", "MCD",
]  # fmt: skip

RowMode = Literal["dev", "all"]


@dataclass(frozen=True)
class Arm:
    name: str
    config_dir: Path
    prompt_path: Path


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def resolve_arm(arm: Arm) -> dict[str, Any]:
    """Everything that controls an arm's behavior, as actually resolved."""
    config = ProfileConfigLoader.load_from_dir(
        arm.config_dir, prompt_path=arm.prompt_path
    )
    chat_model = _init_model(config.model)
    orchestrator = Orchestrator(config, checkpointer=None)
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
        "tool_contracts": {
            tool.name: {
                "description_sha256": _sha256(tool.description or ""),
                "args_schema_sha256": _sha256(
                    json.dumps(tool.args, sort_keys=True, default=str)
                ),
            }
            for tool in orchestrator.tools
        },
        "prompt": {
            "raw_sha256": _sha256(config.system_prompt or ""),
            "rendered_sha256": _sha256(orchestrator.system_prompt),
            "raw_chars": len(config.system_prompt or ""),
        },
    }


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
    "agent_experiment_collector", default=None
)
register_configure_hook(context_var=_collector_var, inheritable=True)


def load_rows(mode: RowMode) -> list[dict[str, str]]:
    _, rows = load_raw_csv_rows(SCENARIO_DIR / "dataset.csv")
    if mode == "all":
        return rows
    return apply_split(rows, load_split_sidecar(BENCHMARK_DIR / "split.json"))


def _tool_call(name: str, **args: Any) -> dict[str, Any]:
    return {"name": name, "args": args, "id": f"prewarm-{name}", "type": "tool_call"}


async def prewarm(tool_names: Sequence[str]) -> list[dict[str, Any]]:
    """Fetch (and, for search, index) each ticker's latest 10-K before timing.

    Otherwise the first arm to touch a ticker pays the EDGAR download (and
    JIT embedding) inside its latency, and which arm that is depends on run
    order. Runs in-process so ``sec_core``'s lru caches are warm too. Each
    tool is warmed independently: one failing must not leave the other cold.
    """
    from backend.agent_engine.tools import setup_tools
    from backend.agent_engine.tools.registry import get_tool

    setup_tools()
    report = []
    for ticker in DATASET_TICKERS:
        entry: dict[str, Any] = {"ticker": ticker}
        for name in tool_names:
            tool = get_tool(name)
            args = {"ticker": ticker}
            if name == "sec_filing_search":
                args["query"] = "risk factors"
            started = time.perf_counter()
            try:
                # These tools take an InjectedToolCallId, so they must be
                # invoked with a full ToolCall rather than bare args.
                message = await tool.ainvoke(_tool_call(name, **args))
                entry[f"{name}_status"] = getattr(message, "status", None)
            except Exception as exc:
                entry[f"{name}_error"] = f"{type(exc).__name__}: {exc}"
            entry[f"{name}_s"] = round(time.perf_counter() - started, 1)
        print("prewarm", entry, flush=True)
        report.append(entry)
    return report


def score(output: dict[str, Any]) -> tuple[dict[str, float | None], dict[str, Any]]:
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
        scores, score_metadata = score(output or {})
        span.log(
            output=output if output is not None else {"error": error},
            scores=scores,
            metadata={"score_details": score_metadata, "task_error": error},
        )
    return {
        "row_id": eval_row["id"],
        "arm": arm.name,
        **order,
        "started_at": started_at,
        "finished_at": datetime.now(tz=timezone.utc).isoformat(),
        "task_error": error,
        "output": output,
        "scores": scores,
        "score_details": score_metadata,
        "llm_calls": collector.llm_calls,
        "tool_runs": collector.tool_runs,
    }


async def run_experiment(
    *,
    experiment_name: str,
    arms: dict[str, Arm],
    arm_order: Callable[[int, int], list[str]],
    prewarm_tools: Sequence[str],
    out_dir: Path,
    label: str,
    rep: int,
    row_mode: RowMode,
    row_ids: list[str] | None,
    extra_metadata: dict[str, Any],
) -> dict[str, str | None]:
    """Run one repetition of every row x arm, row-major. Resumable per run."""
    import braintrust
    from braintrust.integrations.langchain import (
        BraintrustCallbackHandler,
        set_global_handler,
    )

    raw_dir = out_dir / "raw" / f"rep{rep}"
    raw_dir.mkdir(parents=True, exist_ok=True)

    all_rows = load_rows(row_mode)
    all_ids = [row["id"] for row in all_rows]
    rows = all_rows
    if row_ids is not None:
        unknown = [r for r in row_ids if r not in all_ids]
        if unknown:
            raise SystemExit(f"Row ids not in '{row_mode}' rows: {unknown}")
        rows = [row for row in all_rows if row["id"] in row_ids]

    scenario = load_scenario_config(SCENARIO_DIR / "eval_spec.yaml")
    diagnostic = scenario.diagnostic
    bt_config = load_braintrust_config(BRAINTRUST_CONFIG_PATH)

    report = await prewarm(prewarm_tools)
    (out_dir / f"prewarm_{label}_rep{rep}.json").write_text(
        json.dumps(report, indent=2)
    )

    set_global_handler(BraintrustCallbackHandler())
    experiments = {
        name: braintrust.init(
            project=bt_config.project,
            experiment=f"{experiment_name}_{label}_{name}_rep{rep}",
            metadata={
                "dataset_name": diagnostic.dataset_name,
                "dataset_version": diagnostic.dataset_version,
                "row_mode": row_mode,
                "selected_row_ids": [row["id"] for row in rows],
                "arm": name,
                "config_dir": str(arm.config_dir.relative_to(BACKEND_DIR)),
                "prompt_path": str(arm.prompt_path.relative_to(BACKEND_DIR)),
                "git_commit": _git_sha(),
                "run_label": label,
                "repetition": rep,
                "execution": "row-major",
                **extra_metadata,
            },
        )
        for name, arm in arms.items()
    }

    for row in rows:
        position = all_ids.index(row["id"])
        order = arm_order(position, rep)
        for slot, arm_name in enumerate(order):
            raw_path = raw_dir / f"row{int(row['id']):02d}__{arm_name}.json"
            if raw_path.exists():
                print(f"skip {raw_path.name} (exists)", flush=True)
                continue
            arm = arms[arm_name]
            eval_row = _build_diagnostic_eval_rows(
                selected_rows=[row],
                column_mapping=scenario.column_mapping,
                column_types=scenario.column_types,
                dataset_name=diagnostic.dataset_name,
                dataset_version=diagnostic.dataset_version,
                run_label=f"{label}-{arm_name}-rep{rep}",
                agent_version=arm_name,
                experiment_name=f"{experiment_name}_{label}_{arm_name}_rep{rep}",
            )[0]
            print(
                f"[{datetime.now():%H:%M:%S}] rep{rep} row {row['id']} "
                f"slot {slot} {arm_name}",
                flush=True,
            )
            record = await run_one(
                arm=arm,
                eval_row=eval_row,
                experiment=experiments[arm_name],
                order={
                    "repetition": rep,
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
                f"total_s={timing.get('total_s')}",
                flush=True,
            )

    links: dict[str, str | None] = {}
    for name, experiment in experiments.items():
        summary = experiment.summarize(summarize_scores=False)
        links[name] = getattr(summary, "experiment_url", None)
    (out_dir / f"braintrust_links_{label}_rep{rep}.json").write_text(
        json.dumps(links, indent=2)
    )
    braintrust.flush()
    return links
