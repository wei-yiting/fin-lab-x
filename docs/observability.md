# Observability and Tracing

This document covers Langfuse tracing patterns across the two tracing domains in the codebase:

1. **Agent layer** — orchestrator, LLM calls, tool invocations. Traced through LangChain's Langfuse `CallbackHandler` (injected per request) plus `@observe` on individual tool functions.
2. **Ingestion pipelines** — chunking, embedding, Qdrant upsert, EDGAR download/parse for SEC, and (planned) fetch/upsert for the quant subsystem. SEC entry point `search()` opens the trace root; all inner spans only emit when a trace is already active. The shared `traced_span()` helper in `backend/utils/span_tracing.py` is the single mechanism used by any ingestion pipeline that needs structural (not env-toggled) trace boundaries.

Both domains share one Langfuse project and emit `snake_case` spans (`sec_` prefix for SEC-specific operations).

## Agent Layer

`backend/agent_engine/agents/base.py` constructs a per-request `CallbackHandler` in `_build_langfuse_config()` and wires three pieces of trace metadata through LangChain's `config` dict (Langfuse ≥4.3.1 honors these automatically at `on_chain_start`, see [PR #1626](https://github.com/langfuse/langfuse-python/pull/1626)):

| Config key | Value | Effect in Langfuse |
|---|---|---|
| `metadata.langfuse_trace_name` | `f"{VersionConfig.name}_{mode}"` (e.g., `v1_baseline_stream`, `v1_baseline_invoke`) | Renames the root trace so product/version/endpoint are visible |
| `run_name` | `"chat-turn"` | Renames the LangChain root chain span (otherwise defaults to the Runnable class name `LangGraph`) |
| `metadata.request_id` | `uuid.uuid4().hex` minted by each FastAPI handler | Per-request correlation attribute |

`propagate_attributes(trace_name=..., session_id=...)` is still wrapped around the agent invocation to cover the session correlation path and to also set `trace_name` defensively on the active OTel context.

### Tool tracing

Tools executed through `CallbackHandler` (Tavily, yfinance, SEC filing, etc.) have their inputs, outputs, and duration captured automatically — no decorator is needed for that baseline. Add `@observe()` on a tool **only when** you need one of:

- nested sub-spans inside the tool body
- custom metadata attached via `update_current_span(...)`
- access to `get_current_observation_id()` from within the tool

`sec_filing.py` currently retains `@observe(name="sec_filing_downloader")` — this is allowed by the above criteria but not required; most tools (Tavily, yfinance) run decorator-less and still produce a clean tool span via the handler.

Detailed operational rules for the agent layer (streaming boundaries, thread-pool propagation, SDK version constraints) live in [`backend/agent_engine/docs/streaming_observability_guardrails.md`](../backend/agent_engine/docs/streaming_observability_guardrails.md).

## SEC Ingestion Pipeline

### Trace Boundary: `search()` is the Only Entry Point

The dense pipeline has two reachable surfaces:

| Surface | Emits Langfuse traces? |
|---|---|
| `retriever.search()` — called during user query | Yes |
| `vectorizer.ingest_filing()` — called from batch CLI (`embed_sec_filings.py`) or unit tests | No |

Only `search()` carries `@observe(name="sec_retrieval")`. All helpers used inside `search()` — cache lookup, EDGAR download, chunking, embedding, upsert, query embedding — are plain functions that create spans via `traced_span()`, a context manager that **only emits when an outer OpenTelemetry trace is already active**.

This means the same `ingest_filing()` code path produces:
- a nested `sec_dense_ingestion` subtree when `search()` calls it during JIT, and
- zero Langfuse output when the batch CLI or a unit test calls it directly.

No env-var toggling; the trace boundary is structural.

### Mechanism Choice: `@observe` vs. `traced_span`

`@observe` on `search()` uses Langfuse's OpenTelemetry tracer and relies on `contextvars` for nesting. This works within a single async function or a chain of awaits on the same event-loop thread.

`traced_span(name, **kwargs)` (in `backend/utils/span_tracing.py`, a shared cross-pipeline utility) consults the current OTel span:
- If valid, open a Langfuse child span under it.
- If invalid (no outer trace, as with CLI or unit tests), yield a no-op object so callers can still call `.update(...)` without side effects.

Sync helpers that run in a worker thread — `pipeline.download_raw`, `pipeline.parse_raw`, `pipeline.resolve_latest_year` — are dispatched via `asyncio.to_thread(...)`, which copies the current `contextvars` (including the active OTel span) into the thread. The `traced_span` wrapper itself is still opened and closed on the event-loop thread around the `to_thread` call, so the parent/child relationship is captured on the coroutine side where `@observe` established the trace root.

### Where Spans Live

Spans are created by the **calling layer**, not by pipeline modules themselves.

`backend/ingestion/sec_filing_pipeline/` exposes pure data-transformation methods with no Langfuse calls. `backend/ingestion/sec_dense_pipeline/vectorizer.py` exposes `ingest_filing` and helpers with no `@observe` decorators. The `search()` function owns all span creation: it wraps its own steps with `traced_span` and wraps each call into `ingest_filing` likewise. `ingest_filing` internally wraps its own chunking/embedding/upsert steps with `traced_span` — those emit when called during JIT, and stay silent when called by the batch CLI.

### Span Inventory

| Span Name | Emitted By | Condition |
|---|---|---|
| `sec_retrieval` | `search()` `@observe` | Always (root of each query trace) |
| `resolve_latest_year` | `search()` `traced_span` | Only when filters omit `year` |
| `check_sec_cache` | `search()` `traced_span` | Always within a query |
| `sec_filing_pipeline` | `search()` `traced_span` | Only when the local filing cache misses |
| `sec_edgar_download` | `_download_and_parse` `traced_span` | Under `sec_filing_pipeline` |
| `sec_html_to_markdown` | `_download_and_parse` `traced_span` | Under `sec_filing_pipeline` |
| `sec_dense_ingestion` | `search()` `traced_span` | Only when the embedding cache misses |
| `sec_chunking` | `ingest_filing()` `traced_span` | Under `sec_dense_ingestion` |
| `sec_chunk_embedding` | `ingest_filing()` `traced_span` | Under `sec_dense_ingestion` |
| `sec_qdrant_upsert` | `ingest_filing()` `traced_span` | Under `sec_dense_ingestion` |
| `sec_query_embedding` | `search()` `traced_span` | Always within a query |
| `sec_vector_search` | `search()` `traced_span` | Always within a query |

### JIT Trace Hierarchy (cold — both caches miss)

```
sec_retrieval
  ├── resolve_latest_year                (only when year not supplied)
  ├── check_sec_cache                    output: {embedding_cache_hit: false, filing_cache_hit: false}
  ├── sec_filing_pipeline                (skipped when filing_cache_hit = true)
  │     ├── sec_edgar_download
  │     └── sec_html_to_markdown
  ├── sec_dense_ingestion                (skipped when embedding_cache_hit = true)
  │     ├── sec_chunking
  │     ├── sec_chunk_embedding
  │     └── sec_qdrant_upsert
  ├── sec_query_embedding
  └── sec_vector_search
```

### Warm Hierarchy (embedding cache hit)

```
sec_retrieval
  ├── check_sec_cache                    output: {embedding_cache_hit: true, filing_cache_hit: true}
  ├── sec_query_embedding
  └── sec_vector_search
```

### Naming Convention

- SEC-specific operations: prefix with `sec_` (e.g., `sec_dense_ingestion`).
- General-purpose operations: no prefix (e.g., `dense_vector_embedding`).
- Format: `snake_case`.
- Granularity: one span per logical pipeline stage.
