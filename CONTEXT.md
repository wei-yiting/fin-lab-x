# FinLab-X

A modular AI system providing Just-in-Time (JIT) intelligence for US growth stocks. A portfolio-demo project: its value lives in evaluation rigor, observability, and legible engineering decisions rather than production scale.

## Orchestration

**Single Orchestrator**:
The architecture's one central LLM brain that plans, selects tools, and manages state. Deliberately not a multi-agent router.
_Avoid_: multi-agent, router, supervisor

**Workflow Profile**:
A versioned config directory that fully defines an Orchestrator's behavior; the runtime code is version-agnostic.
_Avoid_: hardcoded agent, agent subclass

**Capability tier**:
One of the five cumulative agent stages — `baseline` → `reader` → `quant` → `graph` → `analyst` — each a Workflow Profile that adds one new capability class. Only `baseline` is implemented; the rest are placeholders. Roadmap phases keep their numbers ("Phase 2 delivers `reader`"); agents keep their names.
_Avoid_: v1–v5 / bare version numbers for agents (legacy naming; collides with pipeline generations, PRD phases, and external SDK versions)

**Capability**:
Anything the Orchestrator can act through — Tools, Skills, MCP, Subagents. Only Tools (atomic, stateless, strictly-typed functions) exist today; the other three are documented placeholders.

**Progressive Disclosure**:
Exposing capability metadata to the Orchestrator only when relevant, to protect the context window.

**Code as Interface**:
The LLM interacts with strictly-typed Python functions and Pydantic schemas, not natural-language tool descriptions.

**Zero Hallucination Policy**:
Every claim in an answer must be grounded in tool output and carry a citation.

**Language Policy**:
Tool arguments are always English; the final answer mirrors the user's language. Measured by CJK-ratio scorers.

## SEC data & JIT ingestion

**JIT ingestion**:
Fetching, parsing, and embedding a filing on demand at query time instead of prewarming a database.
_Avoid_: crawl, prewarm

**Two-path SEC architecture**:
The two independent SEC data paths — the **RAG path** (filing HTML → Markdown → chunks → Qdrant) and the **fundamentals path** (XBRL → DuckDB). A path is the whole route from source to the store agents query; the ETL programs along it are components, not the path itself.
_Avoid_: "V2 pipeline" / "V3 pipeline" (legacy vN naming); "Quant path" (collides with the `quant` capability tier)

**Pipeline**:
An ETL program that moves data along a path (filing parsing, chunk embedding, fundamentals loading). A path contains pipelines plus stores; agents query stores, never pipelines.

**Commit marker**:
The completion record an ingest writes as its very last step; retrieval treats only marker-complete data as present. The write-last discipline is what makes "committed or absent" hold.
_Avoid_: sentinel point (current identifier name in the RAG-path code; rename when that code is next touched)

**Committed or absent**:
The ingestion invariant: a failed, concurrent, or abandoned ingest must never leave partial or stale-mixed retrievable data. Refresh is wipe-before-rerun.

**Filing store**:
The on-disk Markdown cache of parsed filings, shared by the ingestion pipelines and the JIT flow.

**header_path**:
The hierarchical section locator attached to each chunk (e.g. `NVDA / 2026 / Part I / Item 1A`); retrieval scoring matches on it.

**Heading promotion**:
The preprocessing stage that promotes raw 10-K markup to semantic heading levels; tickers are bucketed Class A/B/C by markup difficulty.

**Ticker universe**:
The curated ~10–20 ticker set eligible for batch ingestion; anything outside it is served by JIT only.

**Ingestion run**:
One audited ETL invocation on the fundamentals path, recorded as a row (success or error) in the `ingestion_runs` table.

## Evaluation

**EDD (Evaluation-Driven Development)**:
Development steered by evals throughout the lifecycle: quality criteria live as eval sets defined up front, and every strategy choice, iteration, and tier promotion is justified by measured results — evals play the role tests play in TDD.
_Avoid_: "eval-driven" for postponing a decision (that is defer until evidence); framing EDD as only a final promotion gate

**Golden Dataset**:
The git-versioned, hand-curated set of ~30 open-ended financial questions with per-item curation rationale. Its flagship use is the cross-tier comparison — `baseline` / `reader` / `quant` under the same LLM model id — isolating architecture-caused capability gaps.

**Baseline behavior diagnostic**:
The behavior-health check for an agent close to the `baseline` spec: each question carries a capability band (core / boundary / reach) and the expected pass/fail behavior, scored by deterministic execution checks (ran to completion, right tool chosen) plus human trace review. It diagnoses behavior and names the tuning lever; it never grades answer quality.
_Avoid_: near-v1 diagnostic (legacy dataset/scenario name, to be renamed at rework)

**Prompt Regression Suite**:
The stable set of test cases rerun manually before merging any system-prompt or model change, answering "did existing behavior get worse" with an objective pass/fail. A development-stage gate, deliberately kept out of CI.
_Avoid_: Regression Guardrail (a guardrail is a runtime concept — see Guardrail)

**Quality Track**:
The Braintrust experiment track that measures quality movement while iterating on prompts or models — answers "did it get better". Complements the Prompt Regression Suite; the two are never mixed.
_Avoid_: Quality Improvement (superseded README wording)

**Guardrail**:
A runtime mechanism that checks each production request's input and output in real time (blocking prompt injection, filtering unsafe content). Never the name for a development-stage test or eval; no guardrail exists in this repo yet.

**Scenario**:
The convention-based unit of evaluation: a directory with an `eval_spec.yaml` (task, column mapping, scorers), auto-discovered without a registry.

**Eval run**:
One execution of a scenario against a single agent configuration, persisted as one Braintrust experiment (Quality Track) and optionally compared against a pinned base experiment. Compose freely: "a golden-dataset run of `reader`".

**Scorer**:
A scoring function `(output, expected, input) → Score` — programmatic when the criterion is structurally decidable, LLM-judge when semantic.

**Binary rubric**:
All LLM-judge dimensions score 0/1, one LLM call per criterion — never free-form scales — to avoid halo and anchoring bias.

**sec_retrieval**:
Names two things: the root trace span on retrieval, and the eval scenario measuring retrieval quality. Qualify which one you mean ("sec_retrieval span" / "sec_retrieval scenario").

## Streaming & chat

**Domain Event**:
A frozen value object (`MessageStart`, `TextDelta`, `ToolCall`, `Finish`, …) forming the contract between LangGraph stream chunks and SSE serialization.

**Session**:
One conversation thread, checkpointed under a thread id. The busy-guard rejects concurrent runs on the same session (HTTP 409).

**Journey**:
An end-to-end multi-tool user scenario; the unit of journey-level verification.

**Reasoning indicator**:
The frontend "thinking" placeholder shown before the first streamed part arrives. Not model reasoning tokens.
_Avoid_: reasoning stream (that is the provider-token feature)

**Reasoning stream**:
Provider reasoning tokens streamed as their own domain events (multi-provider branch).

**Tool progress**:
A transient sidecar SSE event that updates a running tool card without entering message history.

**Defer-to-ready**:
The citation strategy: source extraction runs exactly once when the stream finishes, never during streaming.

## Design calibration

**Design Envelope**:
The calibration contract fixing the project's scale (portfolio demo, ≤3 concurrent users, 1 operator). Robustness beyond it is over-engineering; shortcuts inside Production-Grade Zones are under-engineering — equal-severity findings.

**Production-Grade Zone**:
An area held to full production standard because it is the portfolio value itself: eval rigor, observability, ADRs, retrieval correctness, failure legibility, API contract.

**Defer until evidence**:
Postponing a design decision until an eval result or incident demonstrates the need. An anti-over-engineering discipline; not a form of EDD.
_Avoid_: "eval-driven" as the name for this

**Legible failure**:
An unsupported input produces a structured, user-facing explanation — never a silent empty or partial answer.

**BYOK**:
Bring Your Own Key — the chat LLM runs on a user-supplied key, with one global free-tier daily cap instead of per-user quotas.

**Failure Museum**:
The curated catalog of the project's documented bugs and failures (with fix status), used as portfolio narrative material.
