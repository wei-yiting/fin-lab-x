# FinLab-X

A modular AI system providing Just-in-Time (JIT) intelligence for US growth stocks. A portfolio-demo project: its value lives in evaluation rigor, observability, and legible engineering decisions rather than production scale.

## Orchestration

**Single Orchestrator**:
The single central LLM brain that plans, selects tools, and manages state. Describes the top-level control flow only: Subagents are Capabilities the Orchestrator acts through, not peer agents behind a router or supervisor.

**Workflow Profile**:
A versioned config directory that fully defines an Orchestrator's behavior; the runtime code is version-agnostic. Loaded by `ProfileConfigLoader`; named after the capability tier it realizes.
_Avoid_: hardcoded agent, agent subclass, workflow version (legacy code vocabulary for the config bundle, retired by the capability-tier rename — the profile's own semver still lives in the `version` field)

**Capability tier**:
One of the five cumulative agent stages — `baseline` → `reader` → `quant` → `graph` → `analyst` — each a Workflow Profile that adds one new capability class. Only `baseline` is implemented; the rest are placeholders. Roadmap phases keep their numbers ("Phase 2 delivers `reader`"); agents keep their names.
_Avoid_: v1–v5 / bare version numbers for agents (legacy naming; collides with pipeline generations, PRD phases, and external SDK versions)

**Capability**:
Anything the Orchestrator can act through — Tools, Skills, MCP, Subagents. Only Tools (atomic, stateless, strictly-typed functions) exist today; the other three are documented placeholders.

**Zero Hallucination Policy**:
Every claim in an answer must be grounded in tool output and carry a citation.

**Language Policy**:
Tool arguments are always English; the final answer mirrors the user's language. Measured by CJK-ratio scorers.

## SEC data & JIT ingestion

**JIT ingestion**:
Fetching, parsing, and embedding a filing on demand at query time instead of prewarming a database.
_Avoid_: crawl, prewarm

**Two-path SEC architecture**:
The two independent SEC data paths — the **RAG path** (raw filing → parsed document → chunks → Qdrant) and the **fundamentals path** (XBRL → DuckDB). A path is the whole route from source to the store agents query; the ETL programs along it are components, not the path itself.
_Avoid_: "V2 pipeline" / "V3 pipeline" (legacy vN naming); "Quant path" (collides with the `quant` capability tier)

**Pipeline**:
An ETL program that moves data along a path (filing parsing, chunk embedding, fundamentals loading). A path contains pipelines plus stores; agents query stores, never pipelines.

**Commit marker**:
A per-(ticker, year) point written as `status: "pending"` at ingest start, then overwritten as `status: "complete"` as the final commit step. Retrieval treats only a `complete` marker as present; the write-`complete`-last discipline is what makes "committed or absent" hold.
_Avoid_: sentinel point (legacy term)

**Committed or absent**:
The ingestion invariant: a failed, concurrent, or abandoned ingest must never leave partial or stale-mixed retrievable data. Refresh is wipe-before-rerun.

**Canonical Item order**:
The SEC Form 10-K standard item sequence (1, 1a, 1b, 1c, 2, … 15, 16) as fixed by the item registry, independent of any particular filing. Parsed filings emit items in this order; the actual position of an item inside a filing's document is not measured and not promised.
_Avoid_: "filing order" / "document order" (implies a per-filing measurement the pipeline does not make)

**Filing store**:
The on-disk cache of parsed filings, shared by the ingestion pipelines and the JIT flow. The text pipeline stores schema-validated `ParsedFiling` JSON; the frozen HTML baseline keeps its legacy Markdown variant until sunset.

**header_path**:
The hierarchical section locator attached to each chunk; retrieval scoring matches on it. New contract: `TICKER / fiscal year / Item N. Title / block heading`, with no Part level. The frozen HTML baseline's variant may include Part segments.

**Heading promotion**:
The preprocessing stage that promotes raw 10-K markup to semantic heading levels; tickers are bucketed Class A/B/C by markup difficulty.

**Ticker universe**:
The curated ~10–20 ticker set eligible for batch ingestion; anything outside it is served by JIT only.

**Ingestion run**:
One audited ETL invocation on the fundamentals path, recorded as a row (success or error) in the `ingestion_runs` table. The RAG path keeps no run audit; its integrity mechanism is the commit marker.

## Evaluation

**EDD (Evaluation-Driven Development)**:
Development steered by evals throughout the lifecycle: quality criteria live as eval sets defined up front, and every strategy choice, iteration, and tier promotion is justified by measured results — evals play the role tests play in TDD.
_Avoid_: "eval-driven" for postponing a decision (that is defer until evidence); framing EDD as only a final promotion gate

**Golden Dataset**:
The git-versioned, hand-curated set of ~30 open-ended financial questions with per-item curation rationale. Its flagship use is the cross-tier comparison — `baseline` / `reader` / `quant` under the same LLM model id — isolating architecture-caused capability gaps.

**Baseline behavior diagnostic**:
The behavior-health check for an agent close to the `baseline` spec: each question carries a capability band (core / boundary / reach) and the expected pass/fail behavior, scored by deterministic execution-health checks (ran to completion, every tool call succeeded) plus human trace review. Whether the agent reached for an appropriate tool is a human-review judgement, deliberately kept out of the deterministic scorer — the scorer never reads the dataset's reference hints. It diagnoses behavior and names the tuning lever; it never grades answer quality.
_Avoid_: near-v1 diagnostic (legacy dataset/scenario name, to be renamed at rework)

**Regression Suite**:
The stable set of test cases rerun manually before merging any change to a scenario's behavior determinants — system prompt, model, or retrieval pipeline — answering "did existing behavior get worse" with a binary red/green verdict. Scorers may be programmatic or binary-rubric LLM judges; each gated scorer's dataset-level metric must clear its declared metric floor. A gated scorer's aggregate is the mean over cases that produced a score; deliberate skips and scorer errors leave the denominator, while any task crash, a fully-empty metric, or an enabled scenario with no gated scorer turns the gate red — absence of evidence never supports green. A development-stage gate, deliberately kept out of CI.
_Avoid_: Prompt Regression Suite (superseded — the suite also gates non-prompt subsystems such as retrieval); Regression Guardrail (a guardrail is a runtime concept — see Guardrail)

**Quality Track**:
The Braintrust experiment track that measures quality movement while iterating on prompts or models — answers "did it get better". Complements the Regression Suite; the two are never mixed.
_Avoid_: Quality Improvement (superseded README wording)

**Guardrail**:
A runtime mechanism that checks each production request's input and output in real time (blocking prompt injection, filtering unsafe content). Never the name for a development-stage test or eval; no guardrail exists in this repo yet.

**Scenario**:
The convention-based unit of evaluation: a directory with an `eval_spec.yaml` (task, column mapping, scorers), auto-discovered without a registry.

**Eval run**:
One execution of a scenario against a single agent configuration, persisted as one result CSV — the permanent record. By default the CSV lands in the gitignored results directory (dev-loop runs are noise); a run worth keeping is curated by the operator into a git-tracked location, the same event-driven pattern as the Trace Archive. Uploading a run as a Braintrust experiment (Quality Track) is opt-in per run; an uploaded run can be compared against a pinned base experiment. Compose freely: "a golden-dataset run of `reader`".

**Scorer**:
A scoring function `(output, expected, input) → Score` — programmatic when the criterion is structurally decidable, LLM-judge when semantic.

**Metric floor**:
The declared minimum a gated scorer's dataset-level metric value must clear for the Regression Suite to stay green — mean for per-case scorers, the metric's own aggregate for rank metrics (MRR, MAP), pass rate for binary judges. The floor is the ADR-0008 strict default `1.0` unless explicitly calibrated; an explicitly calibrated floor derives from a recorded **reference measurement** — one run (git sha + collection/model + date), recorded as a paired record + raw-run CSV under `backend/evals/regression/reference_measurements/<scenario>/` — minus a margin wide enough to catch collapse, not slow erosion (derivation rationale, current example: `backend/evals/regression/sec_retrieval-metric-floors.md`).
_Avoid_: min_score (the value gated is a metric — recall, MRR, pass rate — not a per-case "score" minimum); baseline (overloaded — see Workflow Profile's `baseline` tier and the frozen HTML pipeline, neither of which this term means here)

**Binary rubric**:
All LLM-judge dimensions score 0/1, one LLM call per criterion — never free-form scales — to avoid halo and anchoring bias.

**sec_retrieval**:
Names two things: the root trace span on retrieval, and the eval scenario measuring retrieval quality. Qualify which one you mean ("sec_retrieval span" / "sec_retrieval scenario").

**Trace Archive**:
A curated bundle of traces pulled from the tracing platform within its retention window and kept in the repo (`data/trace-archives/`) as the permanent record — typically a notable failure and its later successful counterpart. Re-uploadable to the platform for side-by-side analysis. Event-driven, per trace worth keeping; never a bulk backup of all traces.

**Experiment Archive**:
The curated, git-tracked record of a one-shot experiment's results (`data/experiment-archives/<date>-<topic>/`): a report, the per-query metrics behind it, and raw eval-run CSVs worth keeping. Always paired with a git tag of the same name under `experiment/` that pins the code that produced it — the tag holds how to run it, the archive holds what it produced. Event-driven like the Trace Archive; distinct from a standing scenario, whose runs are gated rather than archived.

## Verification

**Journey**:
An end-to-end multi-tool user scenario; the unit of journey-level verification. Verification checks that an implementation meets its stated goal — distinct from evaluation, which measures agent quality.

## Streaming & chat

**Domain Event**:
A frozen value object (`MessageStart`, `TextDelta`, `ToolCall`, `Finish`, …) forming the contract between LangGraph stream chunks and SSE serialization.

**Session**:
One conversation thread, checkpointed under a thread id. The busy-guard rejects concurrent runs on the same session (HTTP 409).

**Waiting indicator**:
The frontend placeholder shown between sending a message and the first streamed part arriving — it fills perceived latency and has nothing to do with model reasoning.
_Avoid_: reasoning indicator (current component name; rename when that code is next touched), thinking indicator

**Reasoning chip**:
The collapsible transcript block rendering one provider reasoning segment — live and auto-scrolling while streaming, collapsed to a "Thought for Xs" header afterwards. One chip per reasoning segment; chips persist in the transcript for the session, not across reload.

**Reasoning stream**:
Provider reasoning tokens streamed as their own domain events. The word "reasoning" belongs to this feature alone — never to the waiting indicator.

**Tool progress**:
A transient sidecar SSE event that updates a running tool card without entering message history.

**Extract-on-finish**:
The citation strategy: source extraction runs exactly once when the stream finishes (status leaves `streaming` — ready, error, or stop), never during streaming.
_Avoid_: defer-to-ready (superseded name)

## Design calibration

**Design Envelope**:
The calibration contract fixing the project's scale — the numbers live in `docs/design-envelope.md` (SSOT). Robustness beyond it is over-engineering; shortcuts inside Production-Grade Zones are under-engineering — equal-severity findings.

**Production-Grade Zone**:
An area held to full production standard because it is the portfolio value itself; the authoritative zone list and per-zone standards live in design-envelope §4.

**Defer until evidence**:
Postponing a design decision until an eval result or incident demonstrates the need. An anti-over-engineering discipline; not a form of EDD.
_Avoid_: "eval-driven" as the name for this

**Legible failure**:
An unsupported input produces a structured, user-facing explanation — never a silent empty or partial answer.

**BYOK**:
Bring Your Own Key — the chat LLM runs on a user-supplied key, with one global free-tier daily cap instead of per-user quotas.

**Failure Museum**:
The curated catalog of the project's documented bugs and failures (with fix status), used as portfolio narrative material.
