# FinLab-X File Structure and Responsibilities

This document outlines the file structure and architectural responsibilities for the FinLab-X project. It serves as a guide for developers and AI agents navigating the codebase.

## 1. Project Root (`fin-lab-x/`)

The repository is divided into independent environments:

- **`backend/`**: Python-based AI Agent Engine and FastAPI Web Server.
- **`frontend/`**: TypeScript-based Vite + React 19 chat UI (Vercel AI SDK).
- **`docs/`**: Architecture docs, ADRs, and the Design Envelope.

---

## 2. Backend (`backend/`)

The backend follows Clean Architecture principles and strictly decouples the API layer from the core Agent Engine.

### 2.1 API Layer (`backend/api/`)

Handles HTTP and Server-Sent Events (SSE) requests. **MUST NOT** contain core AI logic.

- **`main.py`**: FastAPI entry point; builds one Orchestrator singleton via lifespan.
- **`dependencies.py`**: Dependency injection (Orchestrator instance).
- **`routers/chat.py`**: `POST /api/v1/chat` — SSE streaming endpoint (session busy guard, regenerate preconditions).
- **`routers/chat_invoke.py`**: `POST /api/v1/chat/invoke` — blocking JSON endpoint.

### 2.2 Agent Engine (`backend/agent_engine/`)

The core, independent AI logic. Designed to run independently of the FastAPI server (e.g., via CLI or eval runner).

#### Implemented components:

- **`agents/`**: Central reasoning engine (profile-agnostic Orchestrator).
  - `base.py`: Orchestrator built on LangChain's `create_agent` (ReAct loop) plus middleware (tool-call budget, tool error handling), prompt templating, regenerate support, and tracing wiring.
  - `config_loader.py`: Pydantic-validated profile config loader (YAML-based, `extra="forbid"`).
  - `profiles/<name>/`: One directory per Workflow Profile (`baseline`, `reader`, `quant`, `graph`, `analyst`), each holding `orchestrator_config.yaml` + optional `system_prompt.md`. `baseline` and `reader` are fully implemented; the rest are placeholder tiers.
- **`tools/`**: Atomic, stateless functions for data retrieval.
  - `registry.py`: Global tool registry (`register_tool` / `get_tools_by_names`); `setup_tools()` is idempotent.
  - `finnhub_tools.py` + `finnhub_client.py`: Stock quote and basic financials (LangChain-free client).
  - `news_search.py`: Tavily financial news search with a trusted-domain allowlist.
  - `sec_filing_tools.py`: Two-step SEC access (`sec_filing_list_sections` / `sec_filing_get_section`).
  - `sec_filing.py`: Pipeline-backed SEC filing downloader tool.
- **`streaming/`**: Three-layer streaming pipeline (see module README).
  - `domain_events_schema.py`: Frozen dataclass domain events (`TextDelta`, `ToolCall`, `Finish`, ...).
  - `event_mapper.py`: Stateful LangGraph-chunks → domain-events mapper.
  - `sse_serializer.py`: Stateless serializer to the AI SDK UIMessage Stream Protocol v1.
  - `tool_error_sanitizer.py`: Strips secrets/paths/stack traces before errors reach the client.
- **`utils/`**: `model_context.py` + `model_context_registry.yaml` — committed per-model context-window registry (avoids importing litellm at runtime).

#### Placeholder directories (empty, reserved):

- **`core/`**, **`skills/`**, **`services/`**, **`infrastructure/`**: Reserved for future capabilities; currently `__init__.py` only.

### 2.3 Shared Core (`backend/common/`)

- **`sec_core.py`**: Shared SEC domain types and error taxonomy used by both SEC consumers (agent tool path and RAG ingestion path). See `backend/agent_engine/docs/sec_core.md`.

### 2.4 Ingestion Pipelines (`backend/ingestion/`)

Data ingestion pipelines that land source material into their respective stores. Each subdirectory is an independent pipeline; they share only the cross-pipeline utilities under `backend/utils/`.

- **`sec_filing_pipeline/`**: Downloads SEC 10-K HTML from EDGAR, converts to Markdown (heading promotion, cleanup), persists to `LocalFilingStore`. Single public entry: `SECFilingPipeline.process(ticker, filing_type, fiscal_year=None)`.
- **`sec_dense_pipeline/`**: Chunks filing Markdown, embeds via OpenAI, upserts into Qdrant. Idempotent per `(ticker, year)` commit markers ("committed or absent"). `retriever.search()` is the single trace root for RAG queries; supports JIT ingestion at question time.
- **`fundamentals_pipeline/`**: Foundation layer for structured quant data — DuckDB connection/schema (8 tables), Pydantic row DTOs, `upsert_rows()` column-level merge, `ingestion_run()` audit context manager, retry decorator, calendar-to-fiscal-period helper, error taxonomy, ticker universe YAML + loader. See module README for the full public API.

### 2.5 Cross-Pipeline Utilities (`backend/utils/`)

- **`span_tracing.py`**: `traced_span()` context manager that opens a tracing span only when an outer trace is already active (no-op otherwise). Used by the ingestion pipelines to get the same structural trace boundary without env-var toggling.

### 2.6 Evaluation (`backend/evals/`)

LLMOps evaluation framework, separated from deterministic software testing. Organized **scenario-first**: each `scenarios/<name>/` directory is self-contained (`eval_spec.yaml` + `dataset.csv` + scorers).

- **`eval_runner.py`**: CLI + orchestrator; Braintrust `Eval()` is the sole executor, local-only by default (`--upload` is explicit opt-in).
- **`eval_spec_schema.py`**: Pydantic models for `eval_spec.yaml` / `braintrust_config.yaml`.
- **`dataset_loader.py`**: CSV → eval cases via `column_mapping` with `column_types` pinning.
- **`scorer_registry.py`**: Dotpath scorer resolution; builds `autoevals.LLMClassifier` for LLM judges.
- **`eval_tasks.py`**: Task functions; the baseline task reuses the production `astream_run()` code path.
- **`scenarios/`**: `language_policy` (live) and `sec_retrieval` (draft).
- **`ARCHITECTURE.md`**: Key decisions, constraints, and platform split (runtime tracing vs. eval).

### 2.7 Scripts (`backend/scripts/`)

Operational and validation CLIs (e.g., `embed_sec_filings.py`, `refresh_model_context_registry.py`, `validation/` checkers).

### 2.8 Testing (`backend/tests/`)

Programmatic unit and integration tests with clear pass/fail criteria, mirroring the source layout: `agents/`, `api/`, `common/`, `evals/`, `ingestion/{sec_filing,sec_dense,fundamentals}_pipeline/`, `streaming/`, `tools/`, `utils/`, `integration/`. Markers deselected by default: `eval`, `integration`, `sec_integration`, `finnhub_integration` (see `pyproject.toml`).

---

## 3. Frontend (`frontend/`)

A Vite + React 19 single-page chat application speaking the Vercel AI SDK UIMessage Stream Protocol v1. See `docs/frontend_chat_architecture.md` for the full architecture.

- **`src/components/`**: Atomic six-layer component tree — `primitives/` (shadcn, CLI-managed) → `atoms/` → `molecules/` → `organisms/` → `templates/` → `pages/` (`ChatPanel`, the only layer wiring `useChat`).
- **`src/hooks/`**: Shared React hooks (tool progress, etc.).
- **`src/lib/`**: HTTP client, error classification, markdown source extraction, message helpers.
- **`src/__tests__/`**: Contract tests + MSW fixtures covering the failure matrix.
- **`tests/e2e/`**: Playwright specs (`smoke/`, `critical/`, `security/`).

---

## 4. Documentation (`docs/`)

- **`design-envelope.md`**: Calibration SSOT for scale assumptions, robustness targets, and depth allocation.
- **`adr/`**: Architecture Decision Records.
- **`agent_architecture.md`**: Single Orchestrator pattern, Workflow Profiles, data pipeline architecture.
- **`observability.md`**: Tracing conventions.
- **`frontend_chat_architecture.md`** / **`frontend_dom_contract.md`** / **`ai_sdk_v6_contract_findings.md`**: Frontend architecture and contracts.
- **`agents/`**: Agent-facing docs (issue tracker, domain docs conventions).

---

## 5. Key Design Principles

### 5.1 Single Orchestrator Pattern

- One central reasoning engine manages all decisions.
- No complex multi-agent routing that can lead to non-deterministic behavior.
- Tools (and future Skills/MCP/Subagents) are capabilities, not independent agents.

### 5.2 Observability First

- Every LLM call, tool execution, and retrieval step is traced.
- If it isn't logged, it didn't happen.
- Runtime tracing currently runs on Langfuse; ADR-0005 ratifies unifying on Braintrust (migration pending). Evaluation runs on Braintrust.

### 5.3 Workflow Profiles

- Each profile (`baseline` through `analyst`) is independently callable.
- `orchestrator_config.yaml` defines allowed tools, model, and constraints.
- Enables safe experimentation and easy rollback.

### 5.4 Code as Interface

- Tools are strictly typed Python functions.
- Pydantic models for input validation.
- LLM interacts with code, not natural language descriptions.

---

## 6. Dependency Rules

To maintain a clean architecture, the following dependency rules are enforced:

1. **API layer** depends on the Agent Engine, never the reverse.
2. **Agents (Orchestrator)** can depend on `tools`, `streaming`, and `utils`.
3. **Tools** must be independent and stateless; they cannot depend on the orchestrator.
4. **Ingestion pipelines** are independent siblings sharing only `backend/utils/`.
5. **Circular dependencies** are strictly prohibited.
