# Streaming Observability Guardrails

Use this document for the detailed operational rules that must be followed whenever the apply conditions in `backend/agent_engine/CLAUDE.md` are met.

For the higher-level decision, rationale, and re-evaluation logic, read:

@backend/agent_engine/docs/unified_observability_strategy_streaming.md

## Detailed Rules

### Rule 1: `Langfuse` Is the Default Backend

Use `Langfuse` as the default observability backend for all new work in `backend/agent_engine`.

Reason:
The main requirement is unified tracing across `LangChain`, `LangGraph`, and future `LlamaIndex` flows. Reintroducing `LangSmith` as the default backend would improve one part of the stack while fragmenting the whole system.

### Rule 2: Use Framework-Native Tracing at the Streaming Boundary

Trace `LangChain` / `LangGraph` orchestration through framework-native integration such as request-scoped `CallbackHandler`.

Reason:
The orchestration layer already understands tool dispatch, model calls, and chain steps. Rebuilding that visibility with custom decorator logic at the generator boundary is both redundant and more fragile.

### Rule 3: Restrict `@observe()` to Deterministic Single-Return Units

Apply `@observe()` only to deterministic functions that complete once and return once.

Examples:

- tools
- retrieval helpers
- reranking helpers
- parsing, transformation, or normalization functions
- post-processing functions

Reason:
Single-return functions are the most stable tracing unit. They map naturally to one observation with one input, one output, and one error boundary.

### Rule 4: Never Decorate Async Generator Streaming Boundaries with `@observe()`

Do not apply `@observe()` to:

- `async def` functions that `yield`
- `astream()` wrappers
- SSE serializers
- body iterators for `StreamingResponse` or `EventSourceResponse`
- functions whose main purpose is chunk forwarding

Reason:
This is the highest-risk `Langfuse` path. It forces the SDK to manage lifecycle across multiple `yield` boundaries, preserve nested context over time, and handle cancellation and errors correctly. The official issue history shows this is where trace fragmentation and swallowed exceptions have occurred.

### Rule 5: Correlation Must Start at the Request Boundary

Set request-level correlation attributes such as `session_id`, `request_id`, and user-scoped metadata at the orchestration entry point with `propagate_attributes()`.

Reason:
Correlation should be established once at the top, then inherited downward. Passing IDs manually through every tool or helper increases noise and creates mismatch risk.

### Rule 6: Do Not Mutate Current Trace State on Every Stream Chunk

Avoid per-chunk calls to APIs such as `update_current_trace()` or `update_current_observation()` inside streaming loops unless there is a narrowly justified case and a dedicated test.

Reason:
Chunk-level trace mutation pushes the design into the same unstable generator-context path that the rules above are trying to avoid. It also produces noisy, low-signal traces.

### Rule 7: Prefer Final Result Plus Structured Metadata Over Chunk-Level Tool Tracing

For tools and RAG helpers, capture:

- final result
- query parameters
- matched document identifiers
- ranking metadata
- provider and latency metadata

Do not try to trace every intermediate chunk unless that intermediate stream is itself a product requirement.

Reason:
For debugging and evaluation, structured metadata is usually more valuable than a verbose stream of transient chunk states.

### Rule 8: Keep Streaming Glue Thin

The orchestration streaming layer should translate framework events into internal domain events and nothing more.

Reason:
The more business logic or observability logic is packed into the generator wrapper, the more likely the wrapper becomes the place where trace hierarchy breaks.

### Rule 9: Treat New Async Boundaries as Observability Risk

Whenever code introduces:

- `asyncio.create_task`
- background tasks
- thread pools
- nested async generators
- cross-framework async handoff

the change must explicitly verify trace parent-child continuity.

Reason:
Async boundaries are the main place where context propagation silently fails.

### Rule 10: Future `LlamaIndex` Work Must Use Official `Langfuse` Integration

When `LlamaIndex` is introduced for RAG, first use the Context7 MCP Server to verify the current `Langfuse` v4+ and `LlamaIndex` integration guidance, then use the official `Langfuse` integration path instead of building ad hoc trace bridges first.

Reason:
The entire reason for selecting `Langfuse` was unified cross-framework coverage. Bypassing the official integration would erase that advantage.

### Rule 11: Hybrid Observability Requires an Explicit Re-Decision

Do not add `LangSmith` back into `backend/agent_engine` without an explicit architecture decision.

Reason:
Hybrid observability is not a small implementation detail. It changes the debugging model, trace correlation model, and maintenance cost of the entire subsystem.

## Required Design Intent

- Trace stable execution units.
- Do not make the generator boundary the primary tracing unit unless the user explicitly asks for that tradeoff.
- Optimize for unified cross-framework observability, not vendor-specific elegance for one framework.

## Stop Conditions

Stop and ask before proceeding if a change requires any of the following:

- decorating an async generator with `@observe()`
- adding `LangSmith` to this subtree
- introducing a second observability backend
- relying on per-chunk current-trace mutation as a core design mechanism
- shipping a new streaming path without an observability POC

## POC Gate Criteria

Any new streaming observability pattern is blocked until it passes all of the following checks.

### Gate 1: Single Request, Single Top-Level Trace

One streamed request must produce one stable top-level trace for the orchestration path.

Fail if:

- the request creates multiple unrelated top-level traces
- the streaming wrapper appears detached from the parent request scope

### Gate 2: Nested Tool and Retrieval Observations Stay Attached

Tool calls and retrieval helpers triggered by a streamed request must appear under the expected parent trace.

Fail if:

- tool observations become separate traces
- retrieval observations lose request-level correlation attributes

### Gate 3: Cancellation and Disconnect Close Cleanly

Client disconnect, cancellation, or timeout must not leave traces half-open or duplicated.

Fail if:

- partial traces remain open
- cancellation spawns orphan child traces

### Gate 4: Exceptions Are Visible and Not Swallowed

Exceptions raised inside the streaming path must surface in both application behavior and observability output.

Fail if:

- the stream silently ends without an error
- trace data marks the run as successful even though an exception occurred

### Gate 5: Concurrency Does Not Cross-Contaminate Context

Two concurrent streamed requests must not leak `session_id`, metadata, or child observations into each other.

Fail if:

- one request inherits another request's correlation attributes
- child observations attach to the wrong parent under concurrency

### Gate 6: `LlamaIndex` and `LangChain` Are Searchable in the Same Backend

When the first `LlamaIndex` RAG slice lands, the team must be able to inspect both:

- orchestration traces
- RAG traces

inside the same `Langfuse` project with usable correlation keys.

Fail if:

- one side is visible and the other is not
- the traces exist but cannot be correlated for a single request
