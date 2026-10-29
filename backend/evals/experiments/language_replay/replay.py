"""Final-answer replay ablation of the answer-language fixes (#82).

Every recorded arm-A run of the 2026-10-28 language-middleware eval (reader
profile, gpt-5.6-luna, old SEC directive wording, no middleware) is rebuilt as
a message list — user question, then each recorded tool call and its recorded
result — and only the final model call is regenerated under each condition.
All conditions see byte-identical evidence; only the language-related text
differs.

  P0  no prompt answer-language rule (bullet removed from the reader prompt),
      old directive, no middleware
  R0  as recorded: reader prompt (rule present), old directive, no middleware
  R2  R0 + #82's neutral directive wording inside the recorded SEC results
  R3  R2 + ResponseLanguageMiddleware's system-message instruction
  M   R0 + middleware only (old directive)

Usage:
  python -m backend.evals.experiments.language_replay.replay \
      --conditions P0,R0,R2,R3,M --rep 1 \
      --out data/experiment-archives/2026-10-29-language-replay/raw
"""

from __future__ import annotations

import argparse
import ast
import asyncio
import gzip
import json
import time
import traceback
from pathlib import Path
from typing import Any

from langchain_core.callbacks import get_usage_metadata_callback
from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
)

from backend.agent_engine.agents import base
from backend.agent_engine.agents.config_loader import ProfileConfigLoader
from backend.agent_engine.agents.response_language import _with_language_instruction
from backend.agent_engine.tools.sec_filing_tools import (
    _LANGUAGE_DIRECTIVE_POST as NEW_DIRECTIVE_POST,
)
from backend.agent_engine.tools.sec_filing_tools import (
    _LANGUAGE_DIRECTIVE_PRE as NEW_DIRECTIVE_PRE,
)
from backend.evals.experiments.language_middleware.run import (
    OLD_DIRECTIVE_POST,
    OLD_DIRECTIVE_PRE,
)
from backend.evals.experiments.language_middleware.scorer import score_answer

PROFILE = "reader"
RECORDING = Path("data/experiment-archives/2026-10-28-language-middleware/raw.jsonl.gz")
PROMPT_RULE = (
    "- Your final answer MUST be in the language of the USER'S MESSAGE — the "
    "language the user typed the question in. Tool outputs (SEC filings, news) "
    "are English and the examples below are English; neither determines the "
    "answer language. Re-read the user's message before writing the answer and "
    "match its language exactly.\n"
)
CONDITIONS = {
    "P0": {"prompt_rule": False, "new_directive": False, "middleware": False},
    "R0": {"prompt_rule": True, "new_directive": False, "middleware": False},
    "R2": {"prompt_rule": True, "new_directive": True, "middleware": False},
    "R3": {"prompt_rule": True, "new_directive": True, "middleware": True},
    "M": {"prompt_rule": True, "new_directive": False, "middleware": True},
}
CALL_TIMEOUT_S = 300


class _Request:
    """The two attributes ``_with_language_instruction`` reads, plus override."""

    def __init__(self, messages: list[BaseMessage], system_message: SystemMessage):
        self.messages = messages
        self.system_message = system_message

    def override(self, system_message: SystemMessage) -> _Request:
        return _Request(self.messages, system_message)


def load_recordings() -> list[dict[str, Any]]:
    with gzip.open(RECORDING, "rt") as f:
        rows = [json.loads(line) for line in f]
    return [r for r in rows if r["arm"] == "A" and r["error"] is None]


def _args(raw: Any) -> dict[str, Any]:
    return raw if isinstance(raw, dict) else ast.literal_eval(raw)


def rebuild_messages(record: dict[str, Any], new_directive: bool) -> list[BaseMessage]:
    # The recording keeps each tool call and its result but not the original
    # turn grouping or intermediate model text, so each call becomes its own
    # AI turn. Replay fidelity (R0 vs the recorded answer) measures the cost.
    messages: list[BaseMessage] = [HumanMessage(record["question"])]
    for i, t in enumerate(record["tool_outputs"]):
        call_id = f"call_{i}"
        messages.append(
            AIMessage(
                content="",
                tool_calls=[
                    {"name": t["tool"], "args": _args(t["args"]), "id": call_id}
                ],
            )
        )
        result = t["result"]
        if new_directive:
            result = result.replace(OLD_DIRECTIVE_PRE, NEW_DIRECTIVE_PRE).replace(
                OLD_DIRECTIVE_POST, NEW_DIRECTIVE_POST
            )
        messages.append(
            ToolMessage(content=result, tool_call_id=call_id, name=t["tool"])
        )
    return messages


def build_system(
    prompt: str, cond: dict[str, bool], messages: list[BaseMessage]
) -> SystemMessage:
    if not cond["prompt_rule"]:
        assert PROMPT_RULE in prompt, "prompt rule text not found in reader prompt"
        prompt = prompt.replace(PROMPT_RULE, "")
    system = SystemMessage(prompt)
    if cond["middleware"]:
        system = _with_language_instruction(_Request(messages, system)).system_message  # type: ignore[arg-type]
    return system


async def replay_one(
    model: Any, prompt: str, record: dict[str, Any], cond_name: str, rep: int
) -> dict[str, Any]:
    cond = CONDITIONS[cond_name]
    messages = rebuild_messages(record, cond["new_directive"])
    system = build_system(prompt, cond, messages)
    out: dict[str, Any] = {
        "condition": cond_name,
        "rep": rep,
        "qid": record["qid"],
        "orig_rep": record["rep"],
        "expected_lang": record["expected_lang"],
        "question": record["question"],
        "recorded_detected": record["score"]["detected"],
        "recorded_pass": record["score"]["pass"],
        "n_tool_calls": len(record["tool_outputs"]),
    }
    started = time.perf_counter()
    try:
        with get_usage_metadata_callback() as usage_cb:
            reply = await asyncio.wait_for(
                model.ainvoke([system, *messages]), CALL_TIMEOUT_S
            )
            out["replay_tool_calls"] = [tc["name"] for tc in reply.tool_calls]
            if reply.tool_calls and not reply.text:
                # The frozen trajectory ends here; ask for the answer without tools.
                reply = await asyncio.wait_for(
                    model.bind(tool_choice="none").ainvoke([system, *messages]),
                    CALL_TIMEOUT_S,
                )
                out["forced_no_tools"] = True
        out["response"] = reply.text
        out["usage"] = {k: dict(v) for k, v in usage_cb.usage_metadata.items()}
        out["error"] = None
    except Exception as exc:
        out["response"] = None
        out["error"] = f"{type(exc).__name__}: {exc}"
        out["traceback"] = traceback.format_exc()
    out["latency_s"] = round(time.perf_counter() - started, 1)
    out["score"] = score_answer(out.get("response"), record["expected_lang"])
    return out


async def main_async(
    conditions: list[str],
    rep: int,
    out_dir: Path,
    concurrency: int,
    only: set[str] | None,
) -> None:
    config = ProfileConfigLoader(PROFILE).load()
    orch = base.Orchestrator(config)
    model = base._init_model(config.model).bind_tools(orch.tools)
    prompt = orch.system_prompt
    records = load_recordings()
    if only is not None:
        records = [r for r in records if r["qid"] in only and r["rep"] == 1]
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir.parent / "replay_config.json").write_text(
        json.dumps(
            {
                "model": config.model.model_dump(),
                "tools": config.tools,
                "conditions": CONDITIONS,
                "old_directive": [OLD_DIRECTIVE_PRE, OLD_DIRECTIVE_POST],
                "new_directive": [NEW_DIRECTIVE_PRE, NEW_DIRECTIVE_POST],
                "prompt_rule_removed_in_P0": PROMPT_RULE,
                "middleware_instruction_example": build_system(
                    prompt, CONDITIONS["R3"], [HumanMessage("Hello")]
                ).content[-1],
            },
            indent=2,
            ensure_ascii=False,
        )
    )
    sem = asyncio.Semaphore(concurrency)

    async def guarded(record: dict[str, Any], cond_name: str) -> None:
        path = out_dir / f"{cond_name}_{record['qid']}_o{record['rep']}_r{rep}.json"
        if path.exists():
            return
        async with sem:
            res = await replay_one(model, prompt, record, cond_name, rep)
        path.write_text(json.dumps(res, indent=2, ensure_ascii=False, default=str))
        s = res["score"]
        print(
            f"[{cond_name}] {record['qid']} o{record['rep']} r{rep} pass={s['pass']} "
            f"lang={s['detected']} rec={res['recorded_detected']} {res['latency_s']}s err={res['error']}",
            flush=True,
        )

    await asyncio.gather(*(guarded(r, c) for c in conditions for r in records))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--conditions", default="P0,R0,R2,R3,M")
    parser.add_argument("--rep", type=int, default=1)
    parser.add_argument("--concurrency", type=int, default=16)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--only", help="comma-separated qids (smoke test)")
    args = parser.parse_args()
    only = set(args.only.split(",")) if args.only else None
    asyncio.run(
        main_async(
            args.conditions.split(","), args.rep, args.out, args.concurrency, only
        )
    )


if __name__ == "__main__":
    main()
