"""Before/after eval of the answer-language fix (#82) on the reader profile.

One process per arm, because the SEC directive text is a module global read at
tool-call time; patching it in a shared process would leak across arms.

  A  before: pre-#82 SEC directive wording, no ResponseLanguageMiddleware
  B  after:  #82 wording + middleware (production code, unpatched)
  C  ablation: #82 wording, no middleware

Production defaults are untouched: arms A and C are applied by monkeypatching
inside this experiment process only.

Usage:
  python -m backend.evals.experiments.language_middleware.run --arm A --reps 2 \
      --out data/experiment-archives/2026-10-28-language-middleware/raw
  python -m backend.evals.experiments.language_middleware.run --prewarm
"""

from __future__ import annotations

import argparse
import asyncio
import json
import time
import traceback
import uuid
from pathlib import Path
from typing import Any

from langchain.agents.middleware import AgentMiddleware
from langchain_core.callbacks import get_usage_metadata_callback
from langchain_core.messages import AIMessage

from backend.agent_engine.agents import base
from backend.agent_engine.agents.config_loader import ProfileConfigLoader
from backend.agent_engine.tools import sec_filing_search, sec_filing_tools
from backend.evals.experiments.language_middleware.questions import QUESTIONS
from backend.evals.experiments.language_middleware.scorer import score_answer

PROFILE = "reader"
TASK_TIMEOUT_S = 420

OLD_DIRECTIVE_PRE = (
    "[LANGUAGE DIRECTIVE] The following SEC filing content is in English. "
    "Your answer must be written in the language the USER wrote their question "
    "in (detect it from the user's message), regardless of the language of this "
    "content."
)
OLD_DIRECTIVE_POST = (
    "[LANGUAGE DIRECTIVE] End of SEC filing content. Reminder: answer in the "
    "language of the user's own message — the same language the user used, "
    "whatever it is."
)


class _NoOpMiddleware(AgentMiddleware):
    pass


def apply_arm(arm: str) -> dict[str, Any]:
    if arm in ("A",):
        for module in (sec_filing_tools, sec_filing_search):
            module._LANGUAGE_DIRECTIVE_PRE = OLD_DIRECTIVE_PRE  # type: ignore[attr-defined]
            module._LANGUAGE_DIRECTIVE_POST = OLD_DIRECTIVE_POST  # type: ignore[attr-defined]
    if arm in ("A", "C"):
        base.ResponseLanguageMiddleware = _NoOpMiddleware  # type: ignore[misc]
    return {
        "arm": arm,
        "directive_pre": sec_filing_tools._LANGUAGE_DIRECTIVE_PRE,
        "directive_pre_search": sec_filing_search._LANGUAGE_DIRECTIVE_PRE,
        "middleware": base.ResponseLanguageMiddleware.__name__,
    }


def _tool_summary(tool_outputs: list[Any]) -> list[str]:
    names = []
    for t in tool_outputs or []:
        if isinstance(t, dict):
            names.append(str(t.get("tool") or t.get("name") or "?"))
        else:
            names.append(str(getattr(t, "tool", None) or getattr(t, "name", "?")))
    return names


async def run_one(
    orch: base.Orchestrator, q: dict[str, str], rep: int, arm: str
) -> dict[str, Any]:
    started = time.perf_counter()
    record: dict[str, Any] = {"arm": arm, "rep": rep, **q}
    try:
        with get_usage_metadata_callback() as usage_cb:
            output = await asyncio.wait_for(
                orch.agent.ainvoke(
                    {"messages": [{"role": "user", "content": q["question"]}]},
                    config={"configurable": {"thread_id": str(uuid.uuid4())}},
                ),
                TASK_TIMEOUT_S,
            )
        result = orch._extract_result(output)
        # _extract_result str()-ifies list content (reasoning + text blocks);
        # score only the final message's text blocks.
        final = next(
            m
            for m in reversed(output["messages"])
            if isinstance(m, AIMessage) and not m.tool_calls
        )
        record["response"] = final.text
        record["tool_outputs"] = result["tool_outputs"]
        record["tools_called"] = _tool_summary(result["tool_outputs"])
        record["sec_in_context"] = any(
            t["tool"].startswith("sec_filing")
            and "language_directive_pre" in t["result"]
            for t in result["tool_outputs"]
        )
        record["usage"] = {k: dict(v) for k, v in usage_cb.usage_metadata.items()}
        record["error"] = None
    except Exception as exc:
        record["response"] = None
        record["error"] = f"{type(exc).__name__}: {exc}"
        record["traceback"] = traceback.format_exc()
    record["latency_s"] = round(time.perf_counter() - started, 1)
    record["score"] = score_answer(record.get("response"), q["expected_lang"])
    return record


async def run_arm(
    arm: str, reps: int, out_dir: Path, concurrency: int, only: set[str] | None
) -> None:
    resolved = apply_arm(arm)
    config = ProfileConfigLoader(PROFILE).load()
    orch = base.Orchestrator(config)
    resolved["model"] = config.model.model_dump()
    resolved["tools"] = config.tools
    resolved["agent_middleware"] = (
        [type(m).__name__ for m in orch.agent.middleware]
        if hasattr(orch.agent, "middleware")
        else None
    )
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / f"arm_{arm}_resolved.json").write_text(
        json.dumps(resolved, indent=2, ensure_ascii=False)
    )

    questions = [q for q in QUESTIONS if only is None or q["qid"] in only]
    # Row-major: every rep of a question before the next question.
    jobs = [(q, rep) for rep in range(1, reps + 1) for q in questions]
    sem = asyncio.Semaphore(concurrency)

    async def guarded(q: dict[str, str], rep: int) -> None:
        path = out_dir / f"{arm}_{q['qid']}_r{rep}.json"
        if path.exists():
            return
        async with sem:
            record = await run_one(orch, q, rep, arm)
        path.write_text(json.dumps(record, indent=2, ensure_ascii=False, default=str))
        s = record["score"]
        print(
            f"[{arm}] {q['qid']} r{rep} sec={record.get('sec_in_context')} pass={s['pass']} lang={s['detected']} {record['latency_s']}s err={record['error']}",
            flush=True,
        )

    await asyncio.gather(*(guarded(q, rep) for q, rep in jobs))


async def prewarm() -> None:
    from backend.agent_engine.tools import setup_tools
    from backend.agent_engine.tools.registry import get_tool

    setup_tools()
    tickers = sorted({t for q in QUESTIONS for t in q["tickers"].split("|") if t})
    for ticker in tickers:
        for name in ("sec_filing_list_sections", "sec_filing_search"):
            args: dict[str, Any] = {"ticker": ticker}
            if name == "sec_filing_search":
                args["query"] = "risk factors"
            started = time.perf_counter()
            try:
                msg = await get_tool(name).ainvoke(
                    {
                        "name": name,
                        "args": args,
                        "id": f"prewarm-{name}",
                        "type": "tool_call",
                    }
                )
                status = getattr(msg, "status", None)
            except Exception as exc:
                status = f"{type(exc).__name__}: {exc}"
            print(
                "prewarm",
                ticker,
                name,
                status,
                round(time.perf_counter() - started, 1),
                flush=True,
            )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--arm", choices=["A", "B", "C"])
    parser.add_argument("--reps", type=int, default=2)
    parser.add_argument("--concurrency", type=int, default=5)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--only", help="comma-separated qids")
    parser.add_argument("--prewarm", action="store_true")
    args = parser.parse_args()
    if args.prewarm:
        asyncio.run(prewarm())
        return
    only = set(args.only.split(",")) if args.only else None
    asyncio.run(run_arm(args.arm, args.reps, args.out, args.concurrency, only))


if __name__ == "__main__":
    main()
