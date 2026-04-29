# FinLab-X File Structure and Responsibilities

This document outlines the file structure and architectural responsibilities for the FinLab-X project based on the current scaffolding. It serves as a guide for developers and AI agents navigating the codebase.

## 1. Project Root (`fin-lab-x/`)

The repository is divided into independent environments:
- **`backend/`**: Python-based AI Agent Engine and FastAPI Web Server.
- **`frontend/`**: TypeScript-based Next.js Generative UI.

---

## 2. Backend (`backend/`)

The backend is built following Clean Architecture principles and strictly decouples the API layer from the core Agent Engine.

### 2.1 API Layer (`backend/api/`)
Handles HTTP, WebSocket, and Server-Sent Events (SSE) requests. **MUST NOT** contain core AI logic.
- **`routers/`**: FastAPI route definitions.
- **`dependencies.py`**: Dependency injection (e.g., DB sessions, Agent Engine instances).
- **`main.py`**: The entry point for the FastAPI application.

### 2.2 Agent Engine (`backend/agent_engine/`)
The core, independent AI logic (agents, tools, skills). Designed to run independently of the FastAPI server (e.g., via CLI or background workers).

#### Core Components:
- **`agents/`**: Central reasoning engine (version-agnostic Orchestrator).
  - `base.py`: Orchestrator implementation using LangChain's `create_agent`.
  - `config_loader.py`: Version configuration loader (YAML-based).
  - `versions/`: Versioned workflow configs (each version has its own `orchestrator_config.yaml`).
- **`tools/`**: Atomic, stateless functions for specific data retrieval or actions.
  - `registry.py`: Central tool registry for dynamic loading.
  - `financial.py`: Financial data tools (yfinance, Tavily).
  - `sec.py`: SEC document retrieval tools.
- **`skills/`**: Higher-level, encapsulated capabilities (placeholder for future use).
- **`observability/`**: Integration with LangSmith for tracing and evaluation.
  - `langsmith_tracer.py`: Decorator for step-level tracing.

#### Supporting Directories (planned):
- **`services/`**: Shared services (LLM access, guardrails).
- **`core/`**: Shared core primitives (state, memory).
- **`infrastructure/`**: Integrations for persistence and external services.

### 2.3 Ingestion Pipelines (`backend/ingestion/`)
Data ingestion pipelines that land source material into their respective stores. Each subdirectory is an independent pipeline; they share only the cross-pipeline utilities under `backend/utils/`.

- **`sec_filing_pipeline/`**: Downloads SEC 10-K/10-Q HTML from EDGAR, converts to Markdown, persists to `LocalFilingStore`. Single public entry: `SECFilingPipeline.process(ticker, filing_type, fiscal_year=None)`.
- **`sec_dense_pipeline/`**: Chunks filing Markdown, embeds via OpenAI, upserts into Qdrant. Idempotent per `(ticker, year)` sentinel points. `retriever.search()` is the single Langfuse trace root for RAG queries.
- **`quant_data_pipeline/`**: Foundation layer shared by yfinance and SEC XBRL subsystems — DuckDB connection/schema, Pydantic row DTOs, `upsert_rows()` column-level merge, `ingestion_run()` audit context manager, retry decorator, calendar-to-fiscal-period helper, error taxonomy, ticker universe YAML + loader. See module README for the full public API.

### 2.4 Cross-Pipeline Utilities (`backend/utils/`)
Utilities shared across ingestion pipelines and the agent layer.

- **`span_tracing.py`**: `traced_span()` context manager that opens a Langfuse span only when an outer OpenTelemetry trace is already active (no-op otherwise). Used by `sec_dense_pipeline` and the quant pipeline to get the same structural trace boundary without env-var toggling.

### 2.5 Testing (`backend/tests/`)
Contains programmatic software engineering Unit and Integration Tests. These tests have clear pass/fail criteria and execute quickly.
- **`agents/`**: Tests for Orchestrator components.
- **`tools/`**: Tests for tool implementations and registry.
- **`observability/`**: Tests for LangSmith tracing.
- **`integration/`**: Integration tests for end-to-end workflows.
- **`api/`**: Tests for API endpoints.

### 2.6 Evaluation (`backend/evaluation/`)
A directory dedicated to LLMOps. It separates the probabilistic and long-running nature of AI evaluation from traditional deterministic software testing.
This section is planned for the future and currently not scaffolded but will contain:
- **`datasets/`**: Golden datasets used as baselines for testing agent performance.
- **`metrics/`**: Custom logic for evaluation metrics (e.g., Accuracy, Relevance, Adherence to Tone).
- **`scripts/`**: Automation scripts for executing batch evaluations.

---

## 3. Frontend (`frontend/`)

A Next.js full-stack application responsible for providing a Generative UI.
- **`src/app/`**: Next.js App Router definitions.
- **`src/components/`**: React UI components, focusing on rendering dynamic Generative Artifacts.
- **`src/lib/`**: API clients and parsers for Server-Sent Events (SSE) streams.

---

## 4. Documentation (`docs/`)

- **`agent_architecture.md`**: High-level architecture documentation (Single Orchestrator pattern).
- **`plans/`**: Implementation plans and design documents.

---

## 5. Key Design Principles

### 5.1 Single Orchestrator Pattern
- One central reasoning engine manages all decisions.
- No complex multi-agent routing that can lead to non-deterministic behavior.
- Tools and Skills are capabilities, not independent agents.

### 5.2 Observability First
- Every LLM call, tool execution, and state change is traced via LangSmith.
- If it isn't logged, it didn't happen.
- Enables evaluation, debugging, and continuous improvement.

### 5.3 Versioned Workflows
- Each version (v1-v5) is independently callable.
- `orchestrator_config.yaml` defines allowed tools and model settings.
- Enables safe experimentation and easy rollback.

### 5.4 Code as Interface
- Tools and skills are strictly typed Python functions.
- Pydantic models for input validation.
- LLM interacts with code, not natural language descriptions.

---

## 6. Dependency Rules

To maintain a clean architecture, the following dependency rules are enforced:

1. **Agents (Orchestrator)** can depend on `tools`, `skills`, and `observability`.
2. **Skills** can depend on `tools`.
3. **Tools** must be independent and stateless; they cannot depend on agents or skills.
4. **Circular Dependencies** are strictly prohibited.
