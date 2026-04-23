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

- retrieval helpers
- reranking helpers
- parsing, transformation, or normalization functions
- post-processing functions

For tools executed through LangGraph/LangChain `CallbackHandler`, basic I/O tracing (arguments, return value, duration) is already captured by the handler. Add `@observe()` on a tool only when you need one of:

- nested sub-spans inside the tool body (e.g., the tool calls another LLM or multiple retrieval steps you want separately attributed)
- custom metadata attached to that tool observation via `update_current_span(...)`
- access to `get_current_observation_id()` inside the tool body

If none of the above applies, rely on the handler and skip `@observe()` to avoid same-name double-nesting.

Reason:
Single-return functions are the most stable tracing unit. They map naturally to one observation with one input, one output, and one error boundary. Stacking `@observe()` on top of the CallbackHandler's auto-trace creates a visible duplicate span (same name) with no new information.

### Rule 4: Require `langfuse>=4.5.0` When Decorating Async Generators or SSE Streams

`@observe()` on async generators and on functions returning `StreamingResponse` / `EventSourceResponse` is supported on `langfuse>=4.5.0` ([PR #1628](https://github.com/langfuse/langfuse-python/pull/1628) wraps `isasyncgen` and `StreamingResponse.body_iterator`, defers `span.end()` until stream exhaustion, and preserves nested context propagation).

Pre-4.5 issue history that used to justify a blanket ban:
- [#7226](https://github.com/langfuse/langfuse/issues/7226) — async gen wrapped as sync; output captured as `<async_generator>`
- [#8216](https://github.com/langfuse/langfuse/issues/8216) — `StreamingResponse` broke into separate traces
- [#8447](https://github.com/langfuse/langfuse/issues/8447) — "No active span in current context" inside `@observe`-decorated async gens

All three are closed. The ban is lifted for 4.5+.

Still prefer the metadata path (see Rule 5) when all you need is to rename the trace — fewer moving parts than decorating the generator itself.

### Rule 5: Correlation Must Start at the Request Boundary

Set request-level correlation attributes (`session_id`, `request_id`, `trace_name`, user-scoped metadata) at the orchestration entry point. Two equivalent paths:

1. **LangChain config metadata** (preferred post-Langfuse 4.3.1 — see [PR #1626](https://github.com/langfuse/langfuse-python/pull/1626)):
   ```
   config = {
       "callbacks": [handler],
       "run_name": "chat-turn",
       "metadata": {
           "langfuse_trace_name": "v1_baseline_stream",
           "langfuse_session_id": session_id,
           "request_id": request_id,
       },
   }
   ```
   The CallbackHandler reads these at `on_chain_start` of the root run and renames the trace / sets session_id automatically.
2. **`propagate_attributes()` context manager** (works any time, including when no LangChain config is in scope):
   ```
   with propagate_attributes(trace_name=..., session_id=..., metadata={...}):
       ...
   ```

Both paths can coexist (e.g., session_id via `propagate_attributes` for scope that outlives the chain, plus `langfuse_trace_name` via LangChain metadata).

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
- `loop.run_in_executor` or raw `ThreadPoolExecutor.submit`
- background tasks
- thread pools
- nested async generators
- cross-framework async handoff

the change must explicitly verify trace parent-child continuity.

Remediation for thread-pool / executor boundaries (Langfuse [advanced-usage docs](https://langfuse.com/docs/observability/sdk/python/advanced-usage) confirm OTel contextvars do NOT propagate to worker threads by default), in order of preference:

1. `asyncio.to_thread(fn, *args)` — Python 3.9+, copies contextvars automatically
2. `ctx = contextvars.copy_context(); loop.run_in_executor(executor, ctx.run, fn, *args)`
3. `from opentelemetry.instrumentation.threading import ThreadingInstrumentor; ThreadingInstrumentor().instrument()` at app startup (monkey-patches `threading.Thread` and `ThreadPoolExecutor.submit`)

`asyncio.create_task` and `asyncio.gather` are both safe without workarounds — both go through `Task.__init__` which calls `copy_context()` per [PEP 567](https://peps.python.org/pep-0567/).

Reason:
Async boundaries are the main place where context propagation silently fails. The failure mode is subtle — orphan spans under the SDK's default trace rather than an error.

### Rule 10: Future `LlamaIndex` Work Must Use Official `Langfuse` Integration

When `LlamaIndex` is introduced for RAG, first use the Context7 MCP Server to verify the current `Langfuse` v4+ and `LlamaIndex` integration guidance, then use the official `Langfuse` integration path instead of building ad hoc trace bridges first.

Reason:
The entire reason for selecting `Langfuse` was unified cross-framework coverage. Bypassing the official integration would erase that advantage.

### Rule 11: Hybrid Observability Requires an Explicit Re-Decision

Do not add `LangSmith` back into `backend/agent_engine` without an explicit architecture decision.

Reason:
Hybrid observability is not a small implementation detail. It changes the debugging model, trace correlation model, and maintenance cost of the entire subsystem.

### Rule 12: Braintrust Eval Must Run Sequential — No Concurrent `astream()` Under Global Handler

When running evaluations with `set_global_handler(BraintrustCallbackHandler())`, eval cases must execute sequentially (one `astream_run()` at a time). Do not use `asyncio.gather()` or concurrent tasks for multiple eval cases in the same process.

Reason:
`set_global_handler()` registers a process-level singleton handler with **mutable internal state** (active-span stacks, per-case buffers, etc.). Concurrent `astream()` calls that share this singleton interleave their mutations and corrupt trace attribution — spans from case A may end up under case B's trace.

This is **handler-state** contamination, not a contextvars problem. `contextvars` are copied per-`Task` by [PEP 567](https://peps.python.org/pep-0567/) in BOTH `asyncio.gather` and `asyncio.create_task` (gather auto-schedules awaitables as Tasks via `ensure_future` → `Task.__init__` → `copy_context()`). So telemetry contextvars are safe; the global handler's non-contextvar fields are not.

Sequential execution ensures each case's callbacks complete before the next begins. (Discovered via Three Amigos BDD analysis, 2026-04-02; mechanism corrected 2026-04-23 after verifying against PEP 567.)

### Rule 13: Handler Failure Must Not Propagate Across Platforms

When multiple callback handlers coexist (e.g., Langfuse per-request + Braintrust global), a failure in one handler must not terminate the streaming response or prevent the other handler from receiving callbacks.

Reason:
LangChain's `AsyncCallbackManager` callback dispatch behavior for handler-level exceptions is version-dependent. POC Gate 7 must verify that exception injection in one handler does not kill the stream or the other handler's trace. If isolation is not guaranteed by LangChain, the integration layer must wrap each handler's callbacks with try/except. (Discovered via Three Amigos BDD analysis, 2026-04-02)

## Required Design Intent

- Trace stable execution units.
- Do not make the generator boundary the primary tracing unit unless the user explicitly asks for that tradeoff.
- Optimize for unified cross-framework observability, not vendor-specific elegance for one framework.

## Stop Conditions

Stop and ask before proceeding if a change requires any of the following:

- adding `LangSmith` to this subtree
- introducing a second observability backend
- relying on per-chunk current-trace mutation as a core design mechanism
- shipping a new streaming path without an observability POC
- decorating an async generator with `@observe()` on Langfuse < 4.5.0

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

### Gate 6: `LlamaIndex` and `LangChain` Are Searchable in the Same Backend (Future)

When the first `LlamaIndex` RAG slice lands, the team must be able to inspect both:

- orchestration traces
- RAG traces

inside the same `Langfuse` project with usable correlation keys.

Fail if:

- one side is visible and the other is not
- the traces exist but cannot be correlated for a single request

### Gate 7: Braintrust + Langfuse Coexist Under `astream()` Streaming

When `set_global_handler(BraintrustCallbackHandler())` is active alongside a per-request Langfuse `CallbackHandler`, a single `astream()` call with tool calls must produce complete, correct traces on both platforms.

Sub-checks:

- **7a — Trace completeness**: Both Langfuse and Braintrust receive LLM generation spans + tool call spans with correct name/args/result/duration. Neither platform shows duplicated or orphaned spans.
- **7b — Handler failure isolation**: Inject an exception in one handler's `on_llm_new_token` callback. The streaming response must continue. The healthy handler's trace must remain complete.
- **7c — Structural equivalence**: The sequence of domain events (event types + order) from `astream()` must be identical with and without Braintrust global handler present.

Fail if:

- either platform is missing spans that the other has
- a handler exception terminates the stream or corrupts the other handler's trace
- the presence of Braintrust global handler changes the domain event sequence
- sequential eval cases produce cross-contaminated traces (case A spans in case B's trace)

Fallback: If Gate 7 fails, eval task function falls back to `run()` (non-streaming). API server streaming with Langfuse-only is unaffected.
