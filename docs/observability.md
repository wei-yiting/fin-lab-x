# Observability and Tracing

This document covers Langfuse tracing patterns used across the SEC pipeline and agent layer.

## Mechanism Choice: `@observe` vs. Context Manager

`@observe` parent-child nesting relies on `contextvars`, which does **not** propagate across `run_in_executor` thread boundaries. Therefore:

- **Async functions** (`ingest_filing`, `embed_chunks`, `embed_query`): use `@observe` — called with `await`, same event loop thread, nesting works.
- **Sync functions forced to executor** (`download_raw` — `edgartools` has no async API): wrap the call site with `Langfuse().start_as_current_observation()`. The span is created/closed in the event loop thread; the executor call runs inside it.
- **Direct sync calls** (`check_sec_cache`): use `@observe` — called directly from `search()`, same thread, nesting works.

## Where Spans Live

Spans are created by the **calling layer**, not by pipeline modules themselves.

`backend/ingestion/sec_filing_pipeline/` exposes pure data-transformation methods with no Langfuse calls. This keeps the batch CLI (`embed_sec_filings.py`) trace-free and lets the JIT caller (`search()` in `backend/ingestion/sec_dense_pipeline/retriever.py`) wrap each step with the spans it wants.

## Span Inventory

| Span Name | Created By | Mechanism |
|---|---|---|
| `sec_retrieval` | `search()` | `@observe` (async) |
| `check_sec_cache` | `check_sec_cache()` | `@observe` (sync direct call) |
| `sec_filing_pipeline` | `search()` JIT path | context manager (wraps download + parse) |
| `sec_edgar_download` | `search()` JIT path | context manager (wraps `pipeline.download_raw()`) |
| `sec_html_to_markdown` | `search()` JIT path | context manager (wraps `pipeline.parse_raw()`) |
| `sec_dense_ingestion` | `ingest_filing()` | `@observe` (async) |
| `sec_chunking` | `ingest_filing()` | context manager (sync chunk step) |
| `sec_chunk_embedding` | `embed_chunks()` | `@observe` (async, child of ingestion) |
| `sec_qdrant_upsert` | `ingest_filing()` | context manager (sync upsert step) |
| `sec_query_embedding` | `embed_query()` | `@observe` (async, for vector search) |
| `sec_vector_search` | `search()` | context manager (sync Qdrant call) |

## JIT Trace Hierarchy

```
sec_retrieval
  ├── check_sec_cache                (always)
  ├── sec_filing_pipeline            (only on filing cache miss)
  │     ├── sec_edgar_download
  │     └── sec_html_to_markdown
  ├── sec_dense_ingestion            (only on embedding cache miss)
  │     ├── sec_chunking
  │     ├── sec_chunk_embedding
  │     └── sec_qdrant_upsert
  ├── sec_query_embedding
  └── sec_vector_search
```

## Naming Convention

- SEC-specific operations: prefix with `sec_` (e.g., `sec_dense_ingestion`)
- General-purpose operations: no prefix (e.g., `dense_vector_embedding`)
- Format: `snake_case`
- Granularity: one span per logical pipeline stage
