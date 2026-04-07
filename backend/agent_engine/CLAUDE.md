## Streaming Observability Guardrails

Use this section whenever work under `backend/agent_engine/` touches any of the following:

- `Langfuse`, `LangChain`, `LangGraph`, or `LlamaIndex` observability or tracing
- streaming orchestration, `astream()` wrappers, or SSE body generation
- new async boundaries, cancellation paths, or request-level correlation
- observability architecture decisions, migrations, or proof-of-concept work

If the work matches any apply condition above, you must read the following file before implementing and then follow it strictly:

@backend/agent_engine/docs/streaming_observability_guardrails.md

### Core Rules

- Use request-scoped `langfuse.langchain.CallbackHandler` for `LangChain` / `LangGraph` orchestration tracing.
- Set correlation attributes such as `session_id`, `request_id`, and user-scoped metadata at the orchestration entry point via `propagate_attributes()`.
- Apply `@observe()` only to deterministic single-return functions.
- Never apply `@observe()` to `async def` functions that `yield`, `astream()` wrappers, SSE serializers, `StreamingResponse` or `EventSourceResponse` body iterators, or chunk-forwarding glue code.
- When `LlamaIndex` is added under this subtree, first use the Context7 MCP Server to verify the current `Langfuse` v4+ and `LlamaIndex` integration guidance, then implement the official `Langfuse` integration path.

### Stop Conditions

Stop and ask before proceeding if a change requires any of the following:

- decorating an async generator with `@observe()`
- adding `LangSmith` to this subtree
- introducing a second observability backend
- relying on per-chunk current-trace mutation as a core design mechanism
- shipping a new streaming path without an observability POC
