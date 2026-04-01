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

The main `Langfuse` risk is not "streaming as a whole." It is the narrower path where tracing is attached directly to async generator boundaries, SSE iterators, or per-chunk current-trace mutation.

That path has enough bug history that it should not be treated as the default design center.

At the same time, that risk can be reduced substantially if:

- framework-native orchestration tracing is used at the streaming boundary
- `@observe()` is reserved for deterministic single-return units
- `LlamaIndex` uses its official `Langfuse` integration path

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

If re-evaluation is needed, use [streaming_observability_guardrails.md](/Users/dong.wyt/Documents/dev-projects/fin-lab-x-wt-feat-v1-frontend-streaming/backend/agent_engine/docs/streaming_observability_guardrails.md) as the operational rules baseline and compare alternative designs against it.
