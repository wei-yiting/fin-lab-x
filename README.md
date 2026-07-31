# FinLab-X — Financial Research AI Agent

A financial research agent for US growth stocks. It answers open-ended research questions
("What supply-chain risks does AMD disclose in its 10-K?") by orchestrating live market data,
financial news search, and RAG over SEC filings — with every step streamed to the UI, traced,
and evaluated.

**Stack**: Python · FastAPI · LangChain/LangGraph · Qdrant · DuckDB · Braintrust/Langfuse · React 19 · Vite · Vercel AI SDK

## System architecture

One central **Orchestrator** (LangGraph ReAct loop) whose entire capability surface is
assembled from configuration: a **Workflow Profile** declares which tools, model, prompt, and
budgets the agent runs with, and the **tool registry** resolves the profile's tool names into
implementations at startup. Observability is a first-class layer — every run emits a full
trace tree.

```mermaid
flowchart TB
    subgraph Config["Profile configuration"]
        direction LR
        PROF["profiles/&lt;name&gt;/<br/>orchestrator_config.yaml<br/>+ system_prompt.md"]
        LOADER["ProfileConfigLoader<br/>(pydantic, fail-fast)"]
    end

    subgraph Runtime["Runtime"]
        direction LR
        API["FastAPI<br/>/api/v1/chat · SSE"]
        ORCH["Orchestrator<br/>LangGraph ReAct + middleware"]
        REG["Tool registry<br/>setup_tools() →<br/>get_tools_by_names()"]
    end

    subgraph Sources["Data sources"]
        direction LR
        FINN["Finnhub<br/>quotes"]
        TAV["Tavily<br/>news"]
        SECQ["SEC 10-K RAG<br/>Qdrant + JIT"]
        DUCK["DuckDB<br/>fundamentals"]
    end

    subgraph Obs["Observability"]
        direction LR
        LF["Langfuse<br/>runtime traces"]
        BT["Braintrust<br/>eval experiments"]
    end

    PROF --> LOADER
    LOADER -- "model · prompt · budgets" --> ORCH
    REG -- "tools[] resolved by name" --> ORCH
    API <--> ORCH
    ORCH --> FINN & TAV & SECQ
    ORCH -.->|planned| DUCK
    ORCH -. "span tree per run" .-> LF
    ORCH -. "eval runs" .-> BT

    classDef config fill:#fef3c7,stroke:#d97706,color:#78350f
    classDef runtime fill:#ede9fe,stroke:#7c3aed,color:#3b2764
    classDef data fill:#dcfce7,stroke:#16a34a,color:#14532d
    classDef planned fill:#f1f5f9,stroke:#94a3b8,color:#475569,stroke-dasharray:4 3
    classDef obs fill:#dbeafe,stroke:#2563eb,color:#1e3a5f
    class PROF,LOADER config
    class API,ORCH,REG runtime
    class FINN,TAV,SECQ data
    class DUCK planned
    class LF,BT obs
    style Config fill:transparent,stroke:#d97706
    style Runtime fill:transparent,stroke:#7c3aed
    style Sources fill:transparent,stroke:#16a34a
    style Obs fill:transparent,stroke:#2563eb
```

Each profile is one architecture stage of the same agent — swapping a profile swaps the
capability surface without code changes:

| Profile | Approach | Status |
|---|---|---|
| `baseline` | Tool-calling ReAct over Finnhub quotes, Tavily news, SEC filing section reads | **Live default** |
| `reader` | Long-context synthesis + RAG over SEC 10-Ks (Qdrant dense retrieval) | In development |
| `quant` | Text-to-SQL over structured fundamentals (DuckDB) | In development |
| `graph` | Knowledge-graph analysis | Planned |
| `analyst` | Combined research assistant (all capabilities) | Planned |

The Single Orchestrator + capabilities pattern keeps every decision in one trace tree; the
architecture leaves room for additional agents later (e.g. a reviewer agent in front of the
orchestrator) without changing the profile or tool contracts.

## End-to-end streaming

Reasoning, tool calls, and answer text all render progressively in the UI over SSE, speaking
the Vercel AI SDK's UIMessage Stream Protocol v1 natively. The backend pipeline is three
strictly separated layers: a frozen provider-agnostic **domain-event schema**, a stateful
**event mapper** (LangChain chunks → domain events), and a stateless **SSE serializer**.

```mermaid
sequenceDiagram
    box rgb(237, 233, 254) Agent Engine
        participant LG as LangGraph<br/>astream
        participant EM as StreamEvent<br/>Mapper
        participant SER as SSE<br/>serializer
    end
    box rgb(219, 234, 254) Frontend
        participant UI as React<br/>useChat
    end

    LG->>EM: content_blocks<br/>(reasoning / text / tool_call_chunk)
    EM->>SER: frozen domain events<br/>(ReasoningDelta, ToolCall, TextDelta, ...)
    SER->>UI: reasoning-start/delta/end ·<br/>tool-input-available · text-delta
    Note over UI: reasoning chips → tool cards<br/>→ markdown answer
```

**Measured impact** — benchmarked against the blocking JSON endpoint on the same queries
(`gpt-5-mini` with reasoning on, warmups discarded):

| Pipeline | Pooled median time-to-first-visible-token | n |
|---|---|---|
| Blocking `POST /chat/invoke` | **36.3 s** | 9 |
| SSE without reasoning forwarding | 6.1 s | 24 (derived) |
| SSE with reasoning streaming | **3.9 s** | 24 |

*First visible token* = first of `reasoning-delta` / `tool-input-available` / `text-delta`.
On the heaviest SEC query the gap is ~29× (98 s → 3.4 s). Reasoning streaming is
provider-agnostic: one config knob (`reasoning: on | off | unsupported`) maps to each
provider's thinking parameters (OpenAI Responses, Gemini, Anthropic), rendered as collapsible
"Thought for Xs" transcript chips.

## Just-in-time SEC ingestion

Any ticker outside the pre-ingested universe is ingested on demand at question time —
EDGAR download → Markdown conversion → chunking + embedding → Qdrant:

```mermaid
flowchart LR
    Q["Agent query:<br/>ticker X"] --> Y["Resolve latest<br/>fiscal year<br/>(EDGAR only)"]
    Y --> M{"Commit marker<br/>complete?"}
    M -- yes --> S["Vector<br/>search"]
    M -- no --> L{"Markdown in<br/>local store?"}
    L -- no --> D["Download + parse<br/>from EDGAR"] --> E
    L -- yes --> E["Embed + upsert<br/>chunks"]
    E --> C["Commit marker:<br/>complete<br/>(always LAST)"] --> S

    classDef step fill:#dbeafe,stroke:#2563eb,color:#1e3a5f
    classDef decision fill:#fef3c7,stroke:#d97706,color:#78350f
    classDef commit fill:#fee2e2,stroke:#dc2626,color:#7f1d1d
    classDef done fill:#dcfce7,stroke:#16a34a,color:#14532d
    class Q,Y,E,D step
    class M,L decision
    class C commit
    class S done
```

A per-(ticker, year) **commit marker** is written `pending` first and flipped to `complete`
only after every chunk is upserted — a partially ingested filing can never be mistaken for a
complete one ("committed or absent"). Ingestion is idempotent (UUID5 point IDs), and the
filing pipeline's heading-promotion heuristics were calibrated against 23 tickers across
clean/messy/hard document classes.

## Evaluation

Evaluation is scenario-first: each scenario directory is a self-contained contract
(spec + dataset + scorers), executed by Braintrust `Eval()` — local-first by default,
platform upload as explicit opt-in.

```mermaid
flowchart LR
    SCEN["scenarios/&lt;name&gt;/<br/>eval_spec.yaml ·<br/>dataset.csv · scorers"] --> RUN["eval_runner CLI"]
    RUN --> EXE["braintrust Eval()"]
    EXE --> TASK["task = production<br/>astream_run() path"]
    TASK --> DET["Deterministic scorers<br/>tool-call sets · citations ·<br/>language checks"]
    TASK --> JUDGE["LLM judges<br/>binary rubrics ·<br/>one call per criterion"]
    DET --> OUT["Result CSV<br/>(git SHA provenance)"]
    JUDGE --> OUT
    OUT -. "--upload (opt-in)" .-> BT["Braintrust<br/>experiment compare"]

    classDef config fill:#fef3c7,stroke:#d97706,color:#78350f
    classDef runtime fill:#ede9fe,stroke:#7c3aed,color:#3b2764
    classDef score fill:#dbeafe,stroke:#2563eb,color:#1e3a5f
    classDef out fill:#dcfce7,stroke:#16a34a,color:#14532d
    class SCEN config
    class RUN,EXE,TASK runtime
    class DET,JUDGE score
    class OUT,BT out
```

Principles: anything decidable programmatically never spends a judge call; LLM judges use
0/1 rubrics (no 1–5 scales) with one call per criterion; eval tasks drive the same streaming
code path the API serves. In development on feature branches: a hand-curated **30-question
golden dataset** for cross-profile comparison under a pinned model (score deltas attributable
to architecture, never model upgrades), with LLM judges accepted only after reaching
Cohen's κ ≥ 0.7 against human annotations.

## Three data layers

| Layer | Source → Store | Agent entry point |
|---|---|---|
| News search | Tavily (trusted-domain allowlist) | `tavily_financial_search` |
| Unstructured RAG | SEC EDGAR 10-K → Markdown → Qdrant dense vectors | `search_sec_filings` (JIT) |
| Structured quant | SEC XBRL / market data → DuckDB (8-table schema) | text-to-SQL (`quant` profile, in development) |

## Observability

Principle: *if it isn't logged, it didn't happen.* Every LLM call, tool execution, and
retrieval step emits spans; the JIT path produces a full trace tree per request. Runtime
tracing runs on Langfuse and evaluation on Braintrust; platform choices are ratified by ADRs
(with POC verification before each migration) in [`docs/adr/`](docs/adr/).

## Repository layout

```
backend/
  api/                  FastAPI routers (SSE chat, JSON invoke) — no AI logic
  agent_engine/
    agents/             Orchestrator + config-driven profiles (baseline, reader, quant, ...)
    streaming/          Domain events → event mapper → SSE serializer
    tools/              Finnhub, Tavily, SEC filing tools (registry pattern)
  common/               Shared SEC domain types & error taxonomy
  evals/                Scenario-first eval framework (Braintrust executor)
  ingestion/
    sec_filing_pipeline/   EDGAR → Markdown (heading promotion, cleanup)
    sec_dense_pipeline/    Markdown → Qdrant (JIT, commit markers)
    fundamentals_pipeline/ DuckDB 8-table foundation
  tests/                ~755 tests mirroring source layout
frontend/               React 19 + Vite + AI SDK chat UI (atomic component tree)
docs/                   design-envelope.md · adr/ · agent_architecture.md · observability.md
```

## Quick start

```bash
# Backend (Python 3.13, uv)
uv sync
uv run uvicorn backend.api.main:app --reload

# Frontend (pnpm)
cd frontend
pnpm install
pnpm dev

# Or: backend + Qdrant via Docker
docker compose up
```

Run the test suites:

```bash
pytest backend/tests/            # backend unit tests
cd frontend && pnpm test         # frontend unit tests
```

Run an evaluation scenario (local-only by default):

```bash
python -m backend.evals.eval_runner language_policy
```

## Status

`main` carries the live baseline agent (streaming chat, SEC RAG with JIT ingestion, eval
framework, CI). Active branches extend it — multi-provider reasoning streaming, the golden
dataset cross-profile eval, and a human-in-the-loop behavior diagnostic — each developed
behind its own design doc and verification plan before merge.
