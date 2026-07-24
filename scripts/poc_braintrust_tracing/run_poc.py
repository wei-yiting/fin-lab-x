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

_REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO_ROOT))  # for backend.* imports when run as a script
load_dotenv(_REPO_ROOT / "backend" / ".env")

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


@tool
async def sec_rag_search(query: str, ticker: str) -> str:
    """Search a company's SEC 10-K filing. Provide an English search query and the stock ticker."""
    from backend.ingestion.sec_dense_pipeline.retriever import search

    chunks = await search(query=query, filters={"ticker": ticker}, top_k=5)
    return "\n---\n".join(
        f"[{c.ticker} FY{c.year} {c.item} | {c.header_path}] {c.text[:400]}"
        for c in chunks
    )


# --- Finding 5 probe: migrated span_tracing pattern (@observe → @traced) ----
from braintrust import traced


@traced(name="sec_retrieval_migrated", type="function")
async def _traced_search_impl(query: str) -> str:
    """Simulates the migrated retriever: @traced outer span (was @observe) +
    start_span sub-span (was traced_span) + LlamaIndex dispatcher spans."""
    with braintrust.start_span(name="check_cache_migrated", type="function") as s:
        s.log(input={"query": query}, output={"embedding_cache_hit": True})
    nodes = await build_retriever().aretrieve(query)
    return "\n".join(n.get_content() for n in nodes)


@tool
async def poc_traced_retrieve(query: str) -> str:
    """Retrieve company facts via the migration-pattern traced search."""
    return await _traced_search_impl(query)


_SYSTEM_PROMPT = (
    "You are a terse financial assistant. ALWAYS answer using tools: "
    "use poc_retrieve for company fundamentals questions, poc_price_note "
    "for price questions, and sec_rag_search for SEC filing questions. "
    "Answer in one sentence."
)


def build_agent(*, sec: bool = False, traced_tool: bool = False) -> Any:
    key = "sec_agent" if sec else ("traced_agent" if traced_tool else "agent")
    tools = [poc_price_note, poc_retrieve]
    if sec:
        tools.append(sec_rag_search)
    if traced_tool:
        tools = [poc_price_note, poc_traced_retrieve]
    if key not in agent_singleton:
        model = init_chat_model("gpt-4o-mini", temperature=0)
        agent_singleton[key] = create_agent(
            model=model, tools=tools, system_prompt=_SYSTEM_PROMPT
        )
    return agent_singleton[key]


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
    sec: bool = False,
    traced_tool: bool = False,
) -> dict[str, Any]:
    """One streamed agent request with its own per-request Braintrust handler."""
    agent = build_agent(sec=sec, traced_tool=traced_tool)
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


async def gate_sec() -> bool:
    """Realistic path: LangGraph tool → sec_dense_pipeline.search() → Qdrant +
    LlamaIndex embed_query. Prewarms the JIT ingest OUTSIDE request scope so
    the gate trace shows the steady-state read path (cache hit)."""
    from backend.ingestion.sec_dense_pipeline.retriever import search

    print("\n[prewarm] JIT ingest AAPL 10-K (EDGAR download + embed on first run — may take minutes)")
    warm = await search(query="risk factors", filters={"ticker": "AAPL"}, top_k=3)
    print(f"[prewarm] done — {len(warm)} chunks (FY{warm[0].year if warm else '?'})")

    r = await run_case(
        "gate-sec-rag",
        "According to its latest 10-K, what are Apple's main risk factors? Use sec_rag_search with ticker AAPL.",
        sec=True,
    )
    return _report(
        r,
        [
            ("stream completed without error", r["stream_error"] is None),
            ("sec_rag_search executed", "sec_rag_search" in r["tools"]),
            ("substantive answer produced", len(r["final_text"]) > 40),
        ],
        [
            "LlamaIndex OpenAIEmbedding span (query embed) nests UNDER the "
            "sec_rag_search tool span, same trace",
            "Langfuse-internal spans (sec_retrieval @observe / traced_span) are "
            "NOT expected in Braintrust — note what visibility is lost vs Langfuse",
        ],
    )


# --- DEV-60 reasoning-tracing probe ------------------------------------------


class ReasoningEnrichProbe(AsyncCallbackHandler):
    """F7-relevant probe: can a sibling callback enrich the Braintrust LLM
    span by run_id (the pattern that on Langfuse requires the private `_runs`
    dict + suffers the OTel-context no-op bug)? Braintrust's handler exposes
    `spans: dict[UUID, Span]` — must run BEFORE the handler in the callbacks
    list so the span is looked up before the handler ends/pops it."""

    raise_error = False

    def __init__(self, bt_handler: Any):
        self.bt = bt_handler
        self._captured: dict[Any, Any] = {}
        self.enriched: list[str] = []
        self.errors: list[str] = []

    def _capture(self, run_id: Any) -> None:
        # The Braintrust handler is sync/run_inline and pops the span in its
        # own on_llm_end before an async sibling runs — so grab the span ref
        # at llm-start (it exists by then; chat-model start dispatches first).
        span = dict(getattr(self.bt, "spans", {}) or {}).get(run_id)
        if span is not None:
            self._captured[run_id] = span

    async def on_chat_model_start(self, *args: Any, run_id: Any, **kwargs: Any) -> None:
        self._capture(run_id)

    async def on_llm_start(self, *args: Any, run_id: Any, **kwargs: Any) -> None:
        self._capture(run_id)

    async def on_llm_end(self, response: Any, *, run_id: Any, **kwargs: Any) -> None:
        span = self._captured.get(run_id) or dict(getattr(self.bt, "spans", {}) or {}).get(run_id)
        if span is None:
            self.errors.append(f"no span for run_id {run_id}")
            return
        try:
            span.log(metadata={"reasoning_enrich_probe": f"run:{run_id}"})
            self.enriched.append(str(run_id))
        except Exception as e:
            self.errors.append(f"{type(e).__name__}: {e}")


async def gate_reasoning() -> bool:
    """DEV-60: reasoning-capable model (gpt-5-mini, responses API — mirrors
    multi-provider _init_model's openai branch) under astream + per-request
    Braintrust handler. Checks reasoning blocks stream through, and probes
    run_id-based span enrichment."""
    if "reasoning_agent" not in agent_singleton:
        model = init_chat_model(
            "gpt-5-mini", reasoning_effort="medium", use_responses_api=True
        )
        agent_singleton["reasoning_agent"] = create_agent(
            model=model, tools=[poc_price_note, poc_retrieve], system_prompt=_SYSTEM_PROMPT
        )
    agent = agent_singleton["reasoning_agent"]

    handler = BraintrustCallbackHandler()
    probe = ReasoningEnrichProbe(handler)
    request_id = uuid.uuid4().hex[:8]
    config = {
        "callbacks": [probe, handler],
        "run_name": "gate-reasoning",
        "metadata": {"poc_case": "gate-reasoning", "request_id": request_id},
        "configurable": {"thread_id": f"gate-reasoning-{request_id}"},
    }

    reasoning_chunks = 0
    text_chunks = 0
    tool_names: list[str] = []
    final_text = ""
    error: str | None = None
    with braintrust.start_span(name="request:gate-reasoning", type="task") as root:
        try:
            link = root.permalink()
        except Exception:
            link = None
        root.log(input="reasoning gate", metadata={"poc_case": "gate-reasoning", "request_id": request_id})
        try:
            async for raw in agent.astream(
                {"messages": [{"role": "user", "content": "Compare ACME's revenue growth against its price level. Use tools."}]},
                config=config,
                stream_mode=["messages", "updates"],
                version="v2",
            ):
                mode, data = raw if isinstance(raw, tuple) else ("updates", raw)
                if mode == "messages":
                    msg = data[0]
                    for block in getattr(msg, "content_blocks", None) or []:
                        btype = block.get("type", "") if isinstance(block, dict) else ""
                        if "reasoning" in btype:
                            reasoning_chunks += 1
                        elif btype == "text":
                            text_chunks += 1
                            final_text += block.get("text", "")
                elif mode == "updates" and isinstance(data, dict):
                    for node_out in data.values():
                        for m in (node_out or {}).get("messages", []):
                            if type(m).__name__ == "ToolMessage":
                                tool_names.append(m.name or "?")
        except Exception as e:
            error = f"{type(e).__name__}: {e}"
        root.log(output=final_text.strip())

    print(f"\n=== gate-reasoning (request_id={request_id}) ===")
    checks = [
        ("stream completed without error", error is None),
        ("reasoning blocks streamed", reasoning_chunks > 0),
        ("tool call observed", bool(tool_names)),
        ("final answer produced", bool(final_text.strip())),
        ("run_id span lookup + enrich worked", bool(probe.enriched) and not probe.errors),
    ]
    ok = all(p for _, p in checks)
    for label, passed in checks:
        print(f"  [{'PASS' if passed else 'FAIL'}] {label}")
    print(f"  reasoning_chunks={reasoning_chunks} text_chunks={text_chunks} tools={tool_names}")
    print(f"  probe: enriched={len(probe.enriched)} errors={probe.errors or 'none'}")
    if error:
        print(f"  stream_error: {error}")
    print(f"  trace: {link or '(search gate-reasoning in UI)'}")
    print("  UI-CHECK: ChatOpenAI generation span output — does it contain the "
          "reasoning content natively (vs text-only)? metadata.reasoning_enrich_probe present?")
    return ok


async def gate_traced() -> bool:
    """Finding 5 remediation probe: @traced (migrated @observe) + start_span
    (migrated traced_span) + LlamaIndex dispatcher, all under a LangGraph tool
    span in one trace."""
    r = await run_case(
        "gate-traced-migration",
        "Using the research corpus, what did Globex acquire?",
        traced_tool=True,
    )
    return _report(
        r,
        [
            ("stream completed without error", r["stream_error"] is None),
            ("poc_traced_retrieve executed", "poc_traced_retrieve" in r["tools"]),
        ],
        [
            "tool span → sec_retrieval_migrated (@traced) → check_cache_migrated "
            "+ VectorIndexRetriever/OpenAIEmbedding, ALL in one trace",
        ],
    )


async def gate_ingest_root() -> bool:
    """Finding 6 remediation probe: wrapping an ingestion run in an explicit
    root span must collapse the orphan dispatcher-span forest into one trace."""
    from llama_index.core import Document as _Doc, VectorStoreIndex as _VSI

    with braintrust.start_span(name="ingestion:poc-corpus", type="task") as root:
        try:
            link = root.permalink()
        except Exception:
            link = None
        _VSI.from_documents(
            [_Doc(text=t) for t in _FAKE_DOCS],
            embed_model=OpenAIEmbedding(model="text-embedding-3-small"),
        )
        root.log(input={"docs": len(_FAKE_DOCS)}, output="ingested")
    print("\n=== gate-ingest-root ===")
    print(f"  trace: {link or '(search ingestion:poc-corpus in UI)'}")
    print("  UI-CHECK: ALL SentenceSplitter/OpenAIEmbedding spans from this build "
          "are inside the single 'ingestion:poc-corpus' trace — no orphan traces")
    return True


def _block_reasoning_text(block: Any) -> str:
    """Defensive reasoning-text extraction across LangChain block shapes."""
    if not isinstance(block, dict):
        return ""
    if isinstance(block.get("reasoning"), str):
        return block["reasoning"]
    if isinstance(block.get("text"), str):
        return block["text"]
    parts = []
    for s in block.get("summary") or []:
        if isinstance(s, dict) and isinstance(s.get("text"), str):
            parts.append(s["text"])
    return "".join(parts)


async def gate_reasoning_trace_level() -> bool:
    """Post-F7-ruling design mapped onto Braintrust: collect reasoning segments
    during astream, write the joined full text (per-call boundary markers) ONCE
    to the request root span at stream end — public API only, zero handler
    internals. Then verify via the Braintrust REST API that the metadata
    persisted."""
    if "reasoning_sum_agent" not in agent_singleton:
        model = init_chat_model(
            "gpt-5-mini",
            reasoning={"effort": "medium", "summary": "auto"},
            use_responses_api=True,
        )
        agent_singleton["reasoning_sum_agent"] = create_agent(
            model=model, tools=[poc_price_note, poc_retrieve], system_prompt=_SYSTEM_PROMPT
        )
    agent = agent_singleton["reasoning_sum_agent"]

    handler = BraintrustCallbackHandler()
    request_id = uuid.uuid4().hex[:8]
    config = {
        "callbacks": [handler],
        "run_name": "gate-reasoning-trace",
        "metadata": {"poc_case": "gate-reasoning-trace", "request_id": request_id},
        "configurable": {"thread_id": f"gate-reasoning-trace-{request_id}"},
    }

    segments: dict[str, list[str]] = {}  # AIMessage id → reasoning text pieces
    tool_names: list[str] = []
    error: str | None = None
    root_span_id: str | None = None
    with braintrust.start_span(name="request:gate-reasoning-trace", type="task") as root:
        root_span_id = root.span_id
        try:
            link = root.permalink()
        except Exception:
            link = None
        root.log(input="reasoning trace-level gate", metadata={"poc_case": "gate-reasoning-trace", "request_id": request_id})
        try:
            async for raw in agent.astream(
                {"messages": [{"role": "user", "content": (
                    "Strictly one tool call at a time, never in parallel: first call "
                    "poc_price_note for ACME and wait for the result; then, using that result, "
                    "call poc_retrieve for ACME revenue facts; then compare price vs revenue growth."
                )}]},
                config=config,
                stream_mode=["messages", "updates"],
                version="v2",
            ):
                mode, data = raw if isinstance(raw, tuple) else ("updates", raw)
                if mode == "messages":
                    msg = data[0]
                    for block in getattr(msg, "content_blocks", None) or []:
                        if isinstance(block, dict) and "reasoning" in block.get("type", ""):
                            text = _block_reasoning_text(block)
                            if text:
                                segments.setdefault(msg.id or "?", []).append(text)
                elif mode == "updates" and isinstance(data, dict):
                    for node_out in data.values():
                        for m in (node_out or {}).get("messages", []):
                            if type(m).__name__ == "ToolMessage":
                                tool_names.append(m.name or "?")
        except Exception as e:
            error = f"{type(e).__name__}: {e}"
        # Post-F7 design: single key, per-call boundary markers inside the value.
        joined = "\n\n=== llm-call boundary ===\n\n".join(
            "".join(parts) for parts in segments.values()
        )
        root.log(metadata={"reasoning": joined or "<no-reasoning-emitted>"})
        root.log(output=f"{len(segments)} reasoning segment groups")

    braintrust.flush()

    # Verify persistence via public REST API — the post-F7 verify script's job.
    persisted = None
    try:
        import urllib.request

        req = urllib.request.Request(
            "https://api.braintrust.dev/v1/project_logs/9d978f09-ab2c-4bce-88d5-15c7522fd2ff/fetch?limit=100",
            headers={"Authorization": f"Bearer {os.environ['BRAINTRUST_API_KEY']}"},
        )
        import json as _json

        rows = _json.load(urllib.request.urlopen(req))["events"]
        for r in rows:
            if r.get("span_id") == root_span_id:
                persisted = (r.get("metadata") or {}).get("reasoning")
                break
    except Exception as e:
        persisted = f"<api-error: {e}>"

    print(f"\n=== gate-reasoning-trace (request_id={request_id}) ===")
    checks = [
        ("stream completed without error", error is None),
        ("readable reasoning collected (summary=auto)", bool(segments) and any(any(p for p in v) for v in segments.values())),
        ("multiple llm-call segments (tool loop)", len(segments) >= 2),
        ("root metadata.reasoning persisted (API-verified)", isinstance(persisted, str) and len(persisted) > 20 and not persisted.startswith("<")),
        ("per-call boundary marker present", isinstance(persisted, str) and "llm-call boundary" in persisted),
    ]
    ok = all(p for _, p in checks)
    for label, passed in checks:
        print(f"  [{'PASS' if passed else 'FAIL'}] {label}")
    print(f"  segments={len(segments)} tools={tool_names}")
    if isinstance(persisted, str):
        print(f"  persisted reasoning ({len(persisted)} chars): {persisted[:200]}...")
    if error:
        print(f"  stream_error: {error}")
    print(f"  trace: {link or '(search gate-reasoning-trace in UI)'}")
    return ok


GATES = {
    "gate1": gate1,
    "sec": gate_sec,
    "reasoning-trace": gate_reasoning_trace_level,
    "traced": gate_traced,
    "ingest-root": gate_ingest_root,
    "reasoning": gate_reasoning,
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
