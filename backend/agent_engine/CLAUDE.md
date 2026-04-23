## Streaming Observability Guardrails

Use this section whenever work under `backend/agent_engine/` touches any of the following:

- `Langfuse`, `Braintrust`, `LangChain`, `LangGraph`, or `LlamaIndex` observability or tracing
- streaming orchestration, `astream()` wrappers, or SSE body generation
- new async boundaries, cancellation paths, or request-level correlation
- observability architecture decisions, migrations, or proof-of-concept work

If the work matches any apply condition above, you must read the following file before implementing and then follow it strictly:

@backend/agent_engine/docs/streaming_observability_guardrails.md

### Core Rules

- Use request-scoped `langfuse.langchain.CallbackHandler` for `LangChain` / `LangGraph` orchestration tracing.
- Set correlation attributes (`session_id`, `request_id`, `trace_name`, user-scoped metadata) at the orchestration entry point. Preferred path: LangChain `config={"metadata": {"langfuse_trace_name": ..., "request_id": ..., ...}, "run_name": ...}` (handled automatically by CallbackHandler on Langfuse ≥4.3.1). `propagate_attributes()` is the fallback when no LangChain config is in scope.
- Apply `@observe()` only to deterministic single-return functions. For tools already traced by CallbackHandler, add `@observe()` only when you need nested sub-spans, custom metadata, or `get_current_observation_id()` inside the tool.
- On Langfuse ≥4.5.0 `@observe()` is supported on async generators and `StreamingResponse.body_iterator`; prefer the metadata path above unless you need generator-level decoration.
- When `LlamaIndex` is added under this subtree, first use the Context7 MCP Server to verify the current `Langfuse` v4+ and `LlamaIndex` integration guidance, then implement the official `Langfuse` integration path.

### Stop Conditions

Stop and ask before proceeding if a change requires any of the following:

- adding `LangSmith` to this subtree
- introducing a second observability backend
- relying on per-chunk current-trace mutation as a core design mechanism
- shipping a new streaming path without an observability POC
- decorating an async generator with `@observe()` on Langfuse < 4.5.0
