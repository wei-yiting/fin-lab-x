"""PROTOTYPE (DEV-100) — Braintrust tracing POC. THROWAWAY: delete after the ADR lands.

Question this prototype answers
-------------------------------
Can runtime tracing move from Langfuse to Braintrust while satisfying the
streaming-observability guardrails (backend/agent_engine/docs/
streaming_observability_guardrails.md)? Specifically:

  Gate 1        per-request BraintrustCallbackHandler + LangGraph astream()
                → one stable top-level trace per request
  Gate NESTING  a LangGraph tool node that internally calls a LlamaIndex
                retriever (setup_llamaindex dispatcher) → retriever spans nest
                UNDER that tool span in the SAME trace (no detached trace).
                This combination has no official example — it is the core risk.
  Gate STREAM   token-level astream: LLM generation span + tool span carry
                complete name/args/result/duration, no orphan/duplicate spans
  Gate CONC     ≥2 concurrent astream() runs with separate handler instances
                → no cross-trace contamination (verifies the per-request
                pattern really sidesteps guardrails Rule 12)
  Gate RULE13   an exception thrown inside a coexisting callback handler must
                not kill the stream

Run (from repo root, on host — Braintrust never runs in Docker here):

    uv run --extra dev --with 'braintrust==0.30.1' \
        python scripts/poc_braintrust_tracing/run_poc.py               # all gates
    (append a gate name — gate1 / nesting / streaming / concurrency / rule13 — to run one)

Programmatic checks (stream completed, tool ran, chunk counts) print as
PASS/FAIL. Trace-shape checks (nesting, attribution) must be eyeballed in the
Braintrust UI — the script prints a per-gate checklist with case names to
search for. Record verdicts in NOTES.md.
"""

import argparse
import asyncio
import os
import sys
import uuid
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[2] / "backend" / ".env")

BT_PROJECT = "poc-braintrust-tracing"  # isolated project: POC noise stays out of eval projects

import braintrust
from braintrust import init_logger

# POC FINDING: repo pins braintrust 0.11.0 + deprecated braintrust-langchain;
# setup_llamaindex only exists in the merged package (>=0.30). Run with:
#   uv run --extra dev --with 'braintrust==0.30.1' python scripts/poc_braintrust_tracing/run_poc.py
from braintrust.integrations.langchain import BraintrustCallbackHandler

from langchain.agents import create_agent
from langchain.chat_models import init_chat_model
from langchain_core.callbacks import AsyncCallbackHandler
from langchain_core.tools import tool

from llama_index.core import Document, VectorStoreIndex
from llama_index.core.retrievers import BaseRetriever
from llama_index.embeddings.openai import OpenAIEmbedding


# --- tiny in-memory LlamaIndex corpus (built once at startup) ----------------

_FAKE_DOCS = [
    "ACME Corp (ticker ACME) reported Q2 revenue of $120M, up 34% YoY, driven by rocket-skate subscriptions.",
    "ACME Corp guidance: full-year operating margin expected between 18% and 21%.",
    "Globex Inc (ticker GLBX) closed the acquisition of Initech for $2.3B in an all-stock deal.",
    "Globex Inc Q2 free cash flow was negative $45M due to one-time integration costs.",
]

_retriever: BaseRetriever | None = None


def build_retriever() -> BaseRetriever:
    global _retriever
    if _retriever is None:
        index = VectorStoreIndex.from_documents(
            [Document(text=t) for t in _FAKE_DOCS],
            embed_model=OpenAIEmbedding(model="text-embedding-3-small"),
        )
        _retriever = index.as_retriever(similarity_top_k=2)
    return _retriever


# --- tools -------------------------------------------------------------------


@tool
def poc_price_note(ticker: str) -> str:
    """Return a deterministic fake price note for a ticker."""
    return f"{ticker}: last close 123.45, 52w range 80.00-150.00 (POC fixture data)"


@tool
async def poc_retrieve(query: str) -> str:
    """Retrieve fundamental facts about a company from the research corpus."""
    nodes = await build_retriever().aretrieve(query)
    return "\n".join(n.get_content() for n in nodes)


_SYSTEM_PROMPT = (
    "You are a terse financial assistant. ALWAYS answer using tools: "
    "use poc_retrieve for company fundamentals questions and poc_price_note "
    "for price questions. Answer in one sentence."
)


def build_agent() -> Any:
    model = init_chat_model("gpt-4o-mini", temperature=0)
    return agent_singleton.setdefault(
        "agent",
        create_agent(model=model, tools=[poc_price_note, poc_retrieve], system_prompt=_SYSTEM_PROMPT),
    )


agent_singleton: dict[str, Any] = {}


# --- failing handler for Rule 13 --------------------------------------------


class FailingHandler(AsyncCallbackHandler):
    """Coexisting handler that blows up on every token (Rule 13 probe)."""

    raise_error = False  # LangChain must NOT get permission to propagate

    async def on_llm_new_token(self, token: str, **kwargs: Any) -> None:
        raise RuntimeError("POC FailingHandler: intentional token-callback failure")


# --- core runner -------------------------------------------------------------


async def run_case(
    case_name: str,
    prompt: str,
    *,
    extra_handlers: list[Any] | None = None,
) -> dict[str, Any]:
    """One streamed agent request with its own per-request Braintrust handler."""
    agent = build_agent()
    handler = BraintrustCallbackHandler()
    request_id = uuid.uuid4().hex[:8]
    config = {
        "callbacks": [handler, *(extra_handlers or [])],
        "run_name": case_name,
        "metadata": {"poc_case": case_name, "request_id": request_id},
        "configurable": {"thread_id": f"{case_name}-{request_id}"},
    }

    token_chunks = 0
    tool_names: list[str] = []
    final_text = ""
    error: str | None = None
    permalink: str | None = None
    # Official Braintrust route-handler pattern: each request gets an explicit
    # root span; the callback handler parents under current_span(). WITHOUT
    # this wrapper, sequential requests in one process chain into a single
    # ever-growing trace (root-span current-context leak — observed run 1).
    with braintrust.start_span(name=f"request:{case_name}", type="task") as root:
        root.log(input=prompt, metadata={"poc_case": case_name, "request_id": request_id})
        try:
            permalink = root.permalink()
        except Exception:
            permalink = None
        try:
            async for raw in agent.astream(
                {"messages": [{"role": "user", "content": prompt}]},
                config=config,
                stream_mode=["messages", "updates"],
                version="v2",
            ):
                mode, data = raw if isinstance(raw, tuple) else ("updates", raw)
                if mode == "messages":
                    msg = data[0]
                    if getattr(msg, "content", None) and type(msg).__name__ == "AIMessageChunk":
                        token_chunks += 1
                        final_text += msg.content if isinstance(msg.content, str) else ""
                elif mode == "updates" and isinstance(data, dict):
                    for node_out in data.values():
                        for m in (node_out or {}).get("messages", []):
                            if type(m).__name__ == "ToolMessage":
                                tool_names.append(m.name or "?")
        except Exception as e:  # stream death is itself a finding, not a crash
            error = f"{type(e).__name__}: {e}"
        root.log(output=final_text.strip())

    return {
        "case": case_name,
        "request_id": request_id,
        "token_chunks": token_chunks,
        "tools": tool_names,
        "final_text": final_text.strip(),
        "stream_error": error,
        "permalink": permalink,
    }


def _try_permalink(handler: Any) -> str | None:
    """Best-effort root-span permalink from the handler's internal span map."""
    for attr in ("spans", "_spans", "run_map", "_run_map"):
        spans = getattr(handler, attr, None)
        if spans:
            try:
                return next(iter(dict(spans).values())).permalink()
            except Exception:
                continue
    return None


# --- gates -------------------------------------------------------------------


def _report(result: dict[str, Any], checks: list[tuple[str, bool]], ui_checklist: list[str]) -> bool:
    ok = all(passed for _, passed in checks)
    print(f"\n=== {result['case']} (request_id={result['request_id']}) ===")
    for label, passed in checks:
        print(f"  [{'PASS' if passed else 'FAIL'}] {label}")
    print(f"  tokens={result['token_chunks']} tools={result['tools']}")
    if result["stream_error"]:
        print(f"  stream_error: {result['stream_error']}")
    print(f"  answer: {result['final_text'][:120]}")
    print(f"  trace: {result['permalink'] or '(permalink unavailable — search case name in UI)'}")
    for item in ui_checklist:
        print(f"  UI-CHECK: {item}")
    return ok


async def gate1() -> bool:
    r = await run_case("gate1-single-trace", "What is the price situation of ACME?")
    return _report(
        r,
        [
            ("stream completed without error", r["stream_error"] is None),
            ("tool call observed", "poc_price_note" in r["tools"]),
            ("final answer produced", bool(r["final_text"])),
        ],
        [
            "exactly ONE top-level trace named 'gate1-single-trace' in project "
            f"'{BT_PROJECT}' logs — no second detached trace for this request_id",
        ],
    )


async def gate_nesting() -> bool:
    r = await run_case(
        "gate-nesting-llamaindex",
        "Using the research corpus, what happened with Globex Inc recently?",
    )
    return _report(
        r,
        [
            ("stream completed without error", r["stream_error"] is None),
            ("poc_retrieve executed", "poc_retrieve" in r["tools"]),
        ],
        [
            "LlamaIndex retrieve/embedding spans appear NESTED UNDER the "
            "poc_retrieve tool span, inside the SAME trace",
            "no separate top-level LlamaIndex trace exists for this request_id",
        ],
    )


async def gate_streaming() -> bool:
    r = await run_case("gate-streaming-integrity", "Compare ACME revenue growth with its price level.")
    return _report(
        r,
        [
            ("token-level streaming observed (>5 chunks)", r["token_chunks"] > 5),
            ("stream completed without error", r["stream_error"] is None),
            ("at least one tool ran", bool(r["tools"])),
        ],
        [
            "LLM generation span has full input/output + duration (not cut off at first token)",
            "each tool span shows name/args/result/duration; no orphan or duplicate spans",
        ],
    )


async def gate_concurrency() -> bool:
    a, b = await asyncio.gather(
        run_case("gate-conc-A", "What is ACME's revenue growth? Use the corpus."),
        run_case("gate-conc-B", "What is the price note for GLBX?"),
    )
    checks = [
        ("both streams completed", a["stream_error"] is None and b["stream_error"] is None),
        ("A answered about ACME", "acme" in a["final_text"].lower()),
        ("B answered about GLBX", "glbx" in b["final_text"].lower()),
    ]
    ok_a = _report(a, checks, ["trace gate-conc-A contains ONLY ACME/corpus spans — nothing about GLBX"])
    ok_b = _report(b, [], ["trace gate-conc-B contains ONLY GLBX price spans — nothing about ACME; "
                          "neither trace's request_id metadata appears in the other"])
    return ok_a and ok_b


async def gate_rule13() -> bool:
    r = await run_case(
        "gate-rule13-handler-failure",
        "What is the price note for ACME?",
        extra_handlers=[FailingHandler()],
    )
    return _report(
        r,
        [
            ("stream survived failing coexisting handler", r["stream_error"] is None),
            ("final answer still produced", bool(r["final_text"])),
        ],
        ["Braintrust trace for this case is still complete despite the failing handler"],
    )


GATES = {
    "gate1": gate1,
    "nesting": gate_nesting,
    "streaming": gate_streaming,
    "concurrency": gate_concurrency,
    "rule13": gate_rule13,
}


async def main() -> int:
    parser = argparse.ArgumentParser(description="DEV-100 Braintrust tracing POC")
    parser.add_argument("gates", nargs="*", choices=[*GATES, "all"])
    args = parser.parse_args()
    selected = list(GATES) if not args.gates or "all" in args.gates else args.gates

    if not os.environ.get("BRAINTRUST_API_KEY"):
        print("BRAINTRUST_API_KEY missing (backend/.env)", file=sys.stderr)
        return 2

    init_logger(project=BT_PROJECT, api_key=os.environ["BRAINTRUST_API_KEY"])
    from braintrust.integrations.llamaindex import setup_llamaindex

    setup_llamaindex(project_name=BT_PROJECT)
    build_retriever()  # build corpus BEFORE gates so index-build spans don't pollute case traces

    results = {}
    for name in selected:
        results[name] = await GATES[name]()

    braintrust.flush()
    print("\n----- programmatic summary (UI checks still required) -----")
    for name, ok in results.items():
        print(f"  {name}: {'PASS' if ok else 'FAIL'}")
    print(f"\nBraintrust project: {BT_PROJECT} → verify UI-CHECK items, then fill NOTES.md")
    return 0 if all(results.values()) else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
