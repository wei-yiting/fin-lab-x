# FinLab-X Architecture Documentation

This document outlines the architectural principles, module structure, and workflow mechanisms of the FinLab-X AI Agent Engine.

## 1. Architecture Overview

FinLab-X utilizes a **Single Orchestrator** pattern. Instead of complex multi-agent routing that can lead to non-deterministic behavior and high latency, a central orchestrator manages the execution flow. This orchestrator leverages specialized components to perform tasks:

- **Orchestrator**: The central reasoning engine (typically a high-capability LLM) that manages state, plans steps, and selects tools.
- **Tools**: Atomic, stateless functions for specific data retrieval or actions.
- **Skills**: Higher-level, encapsulated capabilities that combine multiple tools or complex logic.
- **MCP (Model Context Protocol)**: Standardized interfaces for interacting with external data sources and services.
- **Subagents**: Short-lived, specialized agents spawned by the orchestrator for isolated sub-tasks (e.g., deep research or code generation).

## 2. Module Structure

The core AI runtime resides in `backend/agent_engine/`. The directory is organized as follows:

- `agents/`: Central reasoning engine (version-agnostic Orchestrator). Contains `base.py`, `config_loader.py`, and `versions/`.
- `tools/`: A library of atomic functions (e.g., `get_stock_price`, `search_sec_filings`).
- `skills/`: Complex, reusable capabilities (e.g., `perform_discounted_cash_flow_analysis`).
- `observability/`: Integration with LangSmith and internal logging for tracing and evaluation.
- `mcp/`: (Planned) MCP integrations for external ecosystems.
- `subagents/`: (Planned) Short-lived specialized agents.
- `core/`: (Planned) Shared core primitives (state, memory).
- `infrastructure/`: (Planned) Integrations for persistence and external services.

## 3. Versioned Workflow Profiles

FinLab-X uses **Workflow Profiles** to manage the evolution of agent capabilities. Each profile is a self-contained configuration that defines how the agent behaves.

### Profile Mechanism

Profiles allow for rapid experimentation and safe rollbacks. By switching a profile ID, the system loads a different set of prompts, tool configurations, and model parameters.

### Versions

1.  **v1_baseline**: Standard RAG (Retrieval-Augmented Generation) with basic financial tool access.
2.  **v2_reader**: Optimized for long-context document analysis and multi-document synthesis.
3.  **v3_quant**: Specialized in numerical reasoning, data visualization, and quantitative modeling.
4.  **v4_graph**: Leverages knowledge graphs to understand complex corporate relationships and supply chains.
5.  **v5_analyst**: The flagship profile, combining all previous capabilities into a comprehensive investment research assistant.

### Profile Directory Structure

Each version in `backend/agent_engine/agents/versions/` currently contains:

- `orchestrator_config.yaml`: Model selection (e.g., GPT-4o, Claude 3.5 Sonnet), temperature, and tool-specific limits.

Future versions (v2+) will include:

- `system_prompt.md`: The core identity and behavioral instructions for the agent.
- `README.md`: Documentation of the profile's specific use cases, strengths, and known limitations.

## 4. Design Principles

- **Single Orchestrator**: Centralize decision-making to maintain control and reduce "agentic loop" overhead.
- **Progressive Disclosure**: Only expose tools and skills to the orchestrator when they are relevant to the current task to minimize prompt noise and token usage.
- **Observability First**: Every LLM call, tool execution, and state change must be traceable via LangSmith. If it isn't logged, it didn't happen.
- **Code as Interface**: Tools and skills are defined as strictly typed Python functions. This makes them the "API" that the LLM interacts with.

## 5. Dependency Rules

To maintain a clean architecture, the following dependency rules are enforced:

1.  **Orchestrator** can depend on `tools`, `skills`, `mcp`, `subagents`, and `observability`.
2.  **Subagents** can depend on `tools` and `mcp`.
3.  **Skills** can depend on `tools` and `mcp`.
4.  **Tools** and **MCP** must be independent and stateless; they cannot depend on the orchestrator or skills.
5.  **Circular Dependencies** are strictly prohibited.

## 6. Data Pipeline Architecture

The agent invokes two independent SEC data pipelines depending on the task. They share neither source format nor cache layer.

```mermaid
flowchart TD
    Agent[Agent Orchestrator]

    subgraph V2 [RAG Pipeline V2 current]
        V2A[SEC EDGAR HTML]
        V2B[LocalFilingStore Markdown]
        V2C[Qdrant dense vectors]
        V2A --> V2B --> V2C
    end

    subgraph V3 [Quant Pipeline V3 planned]
        V3A[SEC EDGAR XBRL]
        V3B[DuckDB tables]
        V3A --> V3B
    end

    Agent -->|search_sec_filings| V2C
    Agent -->|query_financial_data| V3B
```

### V2 — Current RAG Pipeline

V2 retrieves unstructured text from 10-K filings. Two modules:

- `backend/ingestion/sec_filing_pipeline/` — downloads HTML from EDGAR, converts to Markdown, persists to `LocalFilingStore`. Single public entry: `SECFilingPipeline.process(ticker, filing_type, fiscal_year=None)` returning a `ParsedFiling`. Granular methods (`resolve_latest_year`, `download_raw`, `parse_raw`) are also public for callers that need finer-grained control or per-step tracing.
- `backend/ingestion/sec_dense_pipeline/` — chunks the Markdown, embeds with OpenAI `text-embedding-3-large`, stores in Qdrant. Idempotent via per-(ticker, year) sentinel points (status `pending` / `complete`).

#### JIT cache-check flow

When `search()` receives a ticker filter, it checks two independent caches in order (embedding sentinel → local filing store) and only falls through to EDGAR on a miss at both tiers:

```mermaid
flowchart TD
    Q[search with ticker filter] --> Y{year supplied?}
    Y -->|No| RL[pipeline.resolve_latest_year - EDGAR metadata only]
    Y -->|Yes| ES
    RL --> ES{embedding sentinel complete in Qdrant?}
    ES -->|Yes| VS[Vector search]
    ES -->|No| FS{filing in LocalFilingStore?}
    FS -->|Yes| IN[ingest_filing - chunk, embed, upsert]
    FS -->|No| DL[pipeline.download_raw then parse_raw]
    DL --> IN
    IN --> VS
```

1. **Year resolution.** If `year` is omitted, `pipeline.resolve_latest_year` hits EDGAR's filing index for metadata only (no HTML download). Local store is never consulted as the source of truth for "what is latest".
2. **Embedding cache (dense vector layer).** Sentinel points in Qdrant track per-(ticker, year) ingest status. A `complete` sentinel means chunks are already embedded and upserted — skip JIT entirely and go straight to vector search.
3. **Filing cache (markdown layer).** On embedding miss, check `LocalFilingStore` for the cached `ParsedFiling`. On hit, re-embed that markdown directly. On miss, call `pipeline.download_raw()` + `pipeline.parse_raw()` to fetch from EDGAR and persist the markdown locally.
4. **Ingest.** Always runs on embedding miss regardless of filing-cache state. Idempotent via UUID5 point IDs (same content → same IDs → safe re-run).

### V3 — Planned Quant Pipeline

V3 will support structured numeric queries (e.g., "show me five-year revenue trend"). It will ingest XBRL — SEC's tagged financial data format — directly into DuckDB. **It does not share the V2 HTML→Markdown pipeline**: source format and downstream consumption pattern are fundamentally different. The two pipelines coexist as independent siblings.

## 7. Observability and Tracing

All agent and pipeline operations are traced via Langfuse. Span naming uses `snake_case` with a `sec_` prefix for SEC-specific operations.

- **JIT path** through `search()` produces a full trace tree (cache check → EDGAR download → Markdown conversion → embedding → vector search).
- **Batch CLI** (`embed_sec_filings.py`) intentionally runs without tracing — pipeline modules emit no spans on their own; spans are created by the calling layer (retriever) only when needed.

For trace hierarchy, span definitions, and the rationale behind `@observe` vs. context-manager choices, see [`docs/observability.md`](./observability.md).
