# FinLab-X

A modular AI system providing Just-in-Time (JIT) intelligence for US growth stocks. A portfolio-demo project: its value lives in evaluation rigor, observability, and legible engineering decisions rather than production scale.

## Orchestration

**Single Orchestrator**:
The architecture's one central LLM brain that plans, selects tools, and manages state. Deliberately not a multi-agent router.
_Avoid_: multi-agent, router, supervisor

**Workflow Profile**:
A versioned config directory that fully defines an Orchestrator's behavior; the runtime code is version-agnostic.
_Avoid_: hardcoded agent, agent subclass

**Agent version**:
One of the five capability tiers `v1_baseline` → `v5_analyst`, each a Workflow Profile. Only `v1_baseline` is implemented; v2–v5 are placeholders. Always use the full name.
_Avoid_: bare "v1" / "v2" / "v3" (collides with pipeline generations and PRD phases)

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
The two independent SEC data paths — the RAG path (filing HTML → Markdown → chunks → Qdrant) and the Quant path (XBRL → DuckDB).
_Avoid_: "V2 pipeline" / "V3 pipeline" (collides with agent versions)

**Sentinel point**:
The deterministic per-(ticker, year) Qdrant point whose status payload records ingest state; only a `complete` sentinel counts as a cache hit.
_Avoid_: commit marker (the design-envelope name for the same mechanism — one name repo-wide)

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
One audited ETL invocation, recorded as a row (success or error) in the quant pipeline's `ingestion_runs` table.

## Evaluation

**EDD (Evaluation-Driven Development)**:
The process gate: an agent version advances only on measured improvement over the previous version on the Golden Dataset.
_Avoid_: "eval-driven" in the casual sense of "defer this decision until an eval shows we need it"

**Golden Dataset**:
The git-versioned, hand-curated set of ~30 open-ended financial questions with per-item curation rationale; the baseline for architecture comparison.

**Golden dataset run**:
Executing the single `golden_dataset` scenario against agent versions v1–v3 with the same LLM model id, isolating architecture-driven capability gaps.
_Avoid_: "golden dataset V1/V2/V3" (there is one dataset; the versions are the agents under test)

**near-v1 diagnostic**:
A diagnostic dataset annotating each question with a capability band (core / boundary / reach) and the expected near-v1 behavior — a probe of where a near-v1 agent should pass or fail.

**Eval track**:
One of two deliberately separated kinds of evaluation: the Regression Guardrail (compact pytest gate) and Quality Improvement (dataset-driven scoring uploaded to Braintrust). Never mixed.

**Scenario**:
The convention-based unit of evaluation: a directory with an `eval_spec.yaml` (task, column mapping, scorers), auto-discovered without a registry.

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

**Legible failure**:
An unsupported input produces a structured, user-facing explanation — never a silent empty or partial answer.

**BYOK**:
Bring Your Own Key — the chat LLM runs on a user-supplied key, with one global free-tier daily cap instead of per-user quotas.

**Failure Museum**:
The curated catalog of the project's documented bugs and failures (with fix status), used as portfolio narrative material.
