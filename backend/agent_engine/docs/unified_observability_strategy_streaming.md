# Unified Observability Strategy for Streaming

## Context

`backend/agent_engine` is expected to evolve toward streaming-first orchestration and response generation while also supporting future `LlamaIndex`-based RAG work.

That creates a structural observability requirement:

- `LangChain` / `LangGraph` orchestration must be traceable
- future `LlamaIndex` retrieval and query internals must be traceable
- both sides should remain inspectable within one coherent backend

The key tradeoff is not "which SDK traces generators better in isolation." The key tradeoff is whether the chosen backend supports unified cross-framework observability without forcing the team into permanent hybrid-debugging overhead.

## Recommendation

Use `Langfuse` as the primary observability backend for `backend/agent_engine`.

Do not switch the subtree back to `LangSmith` as the default tracing backend.
Do not adopt a dual-backend setup (`LangSmith` + `Langfuse`) as the default plan.

## Why This Decision

### Unified Coverage Is the Primary Requirement

`LangSmith` is stronger when the system is mostly `LangChain` / `LangGraph`, especially around generator-style tracing and native run hierarchy inside that ecosystem.

However, this subtree is not being optimized for a single-framework future. It is being optimized for:

- `LangChain` / `LangGraph` orchestration
- future `LlamaIndex` RAG internals
- custom tool and helper code

That makes unified backend coverage more important than maximizing elegance for one framework's generator path.

### The Main `Langfuse` Risk Is Real but Localized

The main `Langfuse` risk historically lived in the narrower path where tracing is attached directly to async generator boundaries, SSE iterators, or per-chunk current-trace mutation.

The most prominent bugs in that path — [#7226](https://github.com/langfuse/langfuse/issues/7226), [#8216](https://github.com/langfuse/langfuse/issues/8216), [#8447](https://github.com/langfuse/langfuse/issues/8447) — are all closed, and [PR #1628](https://github.com/langfuse/langfuse-python/pull/1628) in Langfuse Python SDK v4.5.0 explicitly wraps `isasyncgen` and `StreamingResponse.body_iterator` with deferred `span.end()`. On `langfuse>=4.5.0` the path works, and live tests in this codebase show no OTel detach noise under SSE streaming or under `run_in_executor` handoff to `edgartools`.

Even so, we keep generator-boundary `@observe()` off the default design center. The metadata-based path (`config={"metadata": {"langfuse_trace_name": ...}, "run_name": ...}`, handled by `CallbackHandler` on Langfuse ≥4.3.1) achieves the same naming outcomes with less moving lifecycle machinery, so it wins on simplicity rather than on bug avoidance.

Remaining risk-reduction levers:

- framework-native orchestration tracing at the streaming boundary (`CallbackHandler`)
- `@observe()` reserved for deterministic single-return units; on generators only when there is a product reason beyond naming
- `LlamaIndex` uses its official `Langfuse` integration path
- thread-pool / `run_in_executor` boundaries use `asyncio.to_thread` or `copy_context().run` to keep OTel contextvars attached (see guardrails Rule 9)

### Dual Backends Create Ongoing Cost

A split design where `LangSmith` handles orchestration and `Langfuse` handles `LlamaIndex` would increase:

- dashboard sprawl
- correlation complexity
- architecture drift
- room for AI coding agents to violate observability rules

That cost is not a one-time migration cost. It becomes a permanent debugging tax on the subtree.

## Decision Summary

The subtree should optimize for:

1. one primary observability backend
2. stable correlation across orchestration and future RAG
3. disciplined placement of tracing boundaries
4. explicit proof-of-concept gates for new streaming paths

The subtree should not optimize for:

1. tracing the generator boundary itself as the default primary object
2. convenience for one framework at the cost of cross-framework fragmentation
3. ad hoc hybrid observability during feature work

## When To Re-Evaluate

Revisit this decision only if one of the following becomes true:

- generator-boundary traces become a product-level requirement rather than an implementation-level nice-to-have
- `Langfuse` fails the streaming observability POC gates even when the guardrails are followed
- `LlamaIndex` official `Langfuse` integration does not provide enough debugging fidelity
- the team intentionally decides to invest in a more complex hybrid or `OpenTelemetry`-based observability architecture

If re-evaluation is needed, use [streaming_observability_guardrails.md](./streaming_observability_guardrails.md) as the operational rules baseline and compare alternative designs against it.
