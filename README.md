# FinLab-X — Financial Research AI Agent

A financial research agent for US growth stocks. It answers open-ended research questions
("What supply-chain risks does AMD disclose in its 10-K?") by orchestrating live market data,
financial news search, and RAG over SEC filings — with every step streamed to the UI, traced,
and evaluated.

**Stack**: Python · FastAPI · LangChain/LangGraph · Qdrant · DuckDB · Braintrust/Langfuse · React 19 · Vite · Vercel AI SDK

## System architecture

FinLab-X is structured as an **experiment in agent capability composition**. The agent core
(Orchestrator, streaming, tracing) stays fixed; each **Workflow Profile** is an experiment
arm that grants a different capability set — which tools, model, prompt, and budgets the
agent runs with. The profile's `tools[]` names are resolved by the **tool registry** at
startup, and the capabilities reach into three progressively more structured data layers.
Arms are compared on the same golden dataset under a pinned model, so a score delta is
attributable to the capability set, never the model.

```mermaid
flowchart TB
    subgraph Arms["Workflow Profiles — experiment arms (config only)"]
        P1["baseline<br/>quotes · news · SEC reads"]
        P2["reader<br/>+ RAG over 10-Ks (Qdrant)"]
        P3["quant<br/>+ text-to-SQL (DuckDB)"]
        P4["analyst<br/>all capabilities"]
    end

    subgraph Core["Shared agent core — identical across arms"]
        LOADER["ProfileConfigLoader<br/>one arm per run: model ·<br/>prompt · tools[] · budgets"]
        REG["Tool registry<br/>resolves tools[] by name"]
        ORCH["Orchestrator<br/>LangGraph ReAct + middleware"]
    end

    subgraph Caps["Capabilities — three data layers"]
        FINN["Finnhub<br/>quotes"]
        TAV["Tavily<br/>news search"]
        SECQ["SEC 10-K RAG<br/>Qdrant + JIT"]
        DUCK["DuckDB<br/>text-to-SQL"]
    end

    GENUI["Generative UI — streaming end to end<br/>FastAPI SSE · UIMessage Stream v1 → AI SDK useChat<br/>→ reasoning chips · tool cards · streamed markdown + sources"]
    MEASURE["Measure the effect<br/>tracing span tree per run · Braintrust compare:<br/>score Δ = effect of the capability set (same golden dataset · pinned model)"]

    P1 -- "one arm<br/>loaded per run" --> LOADER
    P2 ~~~ LOADER
    P3 ~~~ REG
    P4 ~~~ REG
    LOADER --> ORCH
    REG --> ORCH
    ORCH -- "tool calls: only the<br/>arm's granted tools" --> FINN
    ORCH --> TAV & SECQ
    ORCH -.->|planned| DUCK
    ORCH == "domain events → SSE" ==> GENUI
    ORCH -- "every run traced ·<br/>eval runs" --> MEASURE

    classDef arm fill:#fef3c7,stroke:#d97706,color:#78350f
    classDef core fill:#ede9fe,stroke:#7c3aed,color:#3b2764
    classDef cap fill:#dcfce7,stroke:#16a34a,color:#14532d
    classDef planned fill:#f1f5f9,stroke:#94a3b8,color:#475569,stroke-dasharray:4 3
    classDef plain fill:#f8fafc,stroke:#64748b,color:#334155
    class P1,P2,P3 arm
    class P4 planned
    class LOADER,ORCH,REG core
    class FINN,TAV,SECQ cap
    class DUCK planned
    class GENUI,MEASURE plain
    style Arms fill:transparent,stroke:#d97706
    style Core fill:transparent,stroke:#7c3aed
    style Caps fill:transparent,stroke:#16a34a
```

**The experiment arms** — a profile is a config directory
(`profiles/<name>/orchestrator_config.yaml` + `system_prompt.md`); swapping it swaps the
capability surface without code changes:

| Profile | Approach | Status |
|---|---|---|
| `baseline` | Tool-calling ReAct over Finnhub quotes, Tavily news, SEC filing section reads | **Live default** |
| `reader` | Long-context synthesis + RAG over SEC 10-Ks (Qdrant dense retrieval) | In development |
| `quant` | Text-to-SQL over structured fundamentals (DuckDB) | In development |
| `graph` | Knowledge-graph analysis | Planned |
| `analyst` | Combined research assistant (all capabilities) | Planned |

**The three data layers** the capabilities draw from:

| Layer | Source → Store | Agent entry point |
|---|---|---|
| News search | Tavily (trusted-domain allowlist) | `tavily_financial_search` |
| Unstructured RAG | SEC EDGAR 10-K → Markdown → Qdrant dense vectors | `search_sec_filings` (JIT) |
| Structured quant | SEC XBRL / market data → DuckDB (8-table schema) | text-to-SQL (`quant` profile, in development) |

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

| Pipeline | Median time-to-first-visible-token |
|---|---|
| Blocking `POST /chat/invoke` | **36.3 s** |
| SSE without reasoning forwarding | 6.1 s |
| SSE with reasoning streaming | **3.9 s** |

*First visible token* = first of `reasoning-delta` / `tool-input-available` / `text-delta`.
Reasoning streaming is
provider-agnostic: one config knob (`reasoning: on | off | unsupported`) maps to each
provider's thinking parameters (OpenAI Responses, Gemini, Anthropic), rendered as collapsible
"Thought for Xs" transcript chips.

## Evaluation & Observability

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
golden dataset** for cross-profile comparison under a pinned model, with LLM judges accepted
only after reaching Cohen's κ ≥ 0.7 against human annotations.

**Observability** follows *if it isn't logged, it didn't happen*: every LLM call, tool
execution, and retrieval step emits spans, so each run uploads a full trace tree to the
tracing platform (Braintrust, POC-verified and ADR-ratified). Because platform retention is
finite, notable traces don't stay only on the platform — they are pulled down, manually
curated, and committed to git as permanent evidence:

```mermaid
flowchart LR
    RUNT["Agent run<br/>span tree"] --> PLAT["Tracing platform<br/>trace drill-down UI"]
    PLAT -- "within retention window:<br/>bt sync pull (NDJSON)" --> CURATE["Manual curation<br/>notable failures +<br/>their fixed counterparts"]
    CURATE --> GIT["data/trace-archives/<br/>git-tracked<br/>permanent evidence"]
    GIT -. "re-upload when needed<br/>for side-by-side compare" .-> PLAT

    classDef runtime fill:#ede9fe,stroke:#7c3aed,color:#3b2764
    classDef plat fill:#dbeafe,stroke:#2563eb,color:#1e3a5f
    classDef curate fill:#fef3c7,stroke:#d97706,color:#78350f
    classDef git fill:#dcfce7,stroke:#16a34a,color:#14532d
    class RUNT runtime
    class PLAT plat
    class CURATE curate
    class GIT git
```

The archive holds runtime traces only — experiments are retained long-term on the platform
and need no retention-driven archival. Platform choices are ratified by ADRs with POC
verification before each migration (see [`docs/adr/`](docs/adr/)).

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
    sec_filing_pipeline_html/   EDGAR → Markdown (heading promotion, cleanup)
    sec_dense_pipeline_html/    Markdown → Qdrant (JIT, commit markers)
    fundamentals_pipeline/ DuckDB 8-table foundation
  tests/                ~755 tests mirroring source layout
data/trace-archives/    Curated trace bundles (permanent evidence)
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

## Related writing & talks

- **Article — [RAG Is Not Just Vector Search: Entity Mismatch in 10-K Retrieval](https://medium.com/@wytdong/rag-%E4%B8%8D%E5%8F%AA%E6%98%AF-vector-search-%E5%BE%9E-10-k-%E6%AA%A2%E7%B4%A2%E7%9A%84%E5%AF%A6%E9%AB%94%E9%8C%AF%E8%AA%A4-%E8%AB%87-metadata-filtering-%E7%9A%84%E4%B8%89%E5%B1%A4%E5%A5%91%E7%B4%84-30db7e644a5c)** (Medium) — an 18-query controlled experiment on metadata pre-filtering and tenant-aware indexing, run on this repo's SEC corpus.
- **Talk — [Agent Observability & Evaluation](https://docs.google.com/presentation/d/103yxXhcqoV-vw3QB00NKDVfVbI41nchdMlZ3a702l6E/present)** — tracing, evaluation datasets, and failure analysis for LLM agents, drawn from this project's observability and eval work.
