# Trace-level reasoning transcript on a self-owned root span

Status: accepted (2026-07-30) — F7 ruling (DEV-60 / DEV-105), implemented by DEV-107, carried forward by the Braintrust migration (DEV-114, ADR-0005).

Reasoning persistence to the tracing backend drops from per-LLM-call granularity to one trace-level transcript: an accumulator observes the reasoning domain events (`ReasoningStart/Delta/End`) already flowing to the client, and when the conversation ends the orchestration wrapper writes the full transcript once — a single `reasoning` metadata key, segments delimited by in-value markers — onto a root span that the wrapper itself creates and holds. The previous per-call design required reading `langfuse.langchain.CallbackHandler._runs` (private SDK state) plus a three-layer drift defense (key-shape fallbacks, once-per-process drift warning, a 283-line contract test behind a dedicated pytest marker); all of it is deleted.

**Why.** There is no public API for the per-call shape: Langfuse v4 removed post-hoc trace updates (`update_current_trace` / `span.update_trace` were decomposed into start-time `propagate_attributes`), and the OTel-context path (`update_current_generation`) silently no-ops under LangChain's async dispatch. Holding our own root span reference makes the write deterministic — no current-span guessing, no private state — and gives the abort path the same object: the reasoning tail and the `status: "aborted"` marker are written in one `span.update()` call, eliminating the last `_runs` read (abort cleanup previously value-iterated it to find the root chain).

The self-owned root span is not a Langfuse-specific workaround. The Braintrust POC (`experiment/braintrust-tracing-poc`, NOTES.md Finding 1) showed a bare per-request `BraintrustCallbackHandler` leaks current-span context across requests — consecutive requests chained into one 56-span trace — and Braintrust's official route-handler pattern requires exactly this per-request root span. The F7 end-state was replayed on Braintrust (`gate-reasoning-trace`, all checks pass): the accumulator and transcript shape move unchanged; only the final write call swaps (`span.update(metadata=...)` → `root.log(metadata=...)`).

## Considered options

1. **Keep per-call writes via `_runs` private state** (previous design) — rejected: no public equivalent exists, and the drift-defense scaffolding (contract test, fallbacks, marker) is maintenance the granularity did not justify (DEV-60 test audit). On Braintrust, per-call reasoning is natively visible in generation span outputs anyway, so the lost granularity returns for free after migration.
2. **Side-car span attached via `handler.last_trace_id`** — rejected: the transcript would not live on the root observation, and it adds a handler-attribute dependency.
3. **Self-owned root span, single end-of-conversation write** — chosen.

## Consequences

- The trace tree gains one wrapper level: the LangChain chain tree nests under our root span. Nothing in the repo or the Langfuse UI depended on the old root shape.
- Transcript semantics: markers delimit segments (`=== segment N ===`, one per reasoning part, matching frontend chips one-to-one); `=== aborted ===` appears only when the conversation aborts mid-segment and marks transcript integrity, while conversation-level aborts stay owned by the separate `status: "aborted"` key. The always-write-key contract survives (`"<unsupported>"` / `""` values), as does the 500KB whole-transcript cap (truncate tail, keep head).
- `ReasoningTraceCallback` (the `on_llm_end` path) is retired entirely; its replacement is a platform-agnostic accumulator fed by `astream_run`, with no knowledge of the tracing backend.
- The verify script shrinks to one assertion class: the root trace carries the full transcript.
