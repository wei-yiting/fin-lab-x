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

### 2.2 Agent Engine (`backend/ai_engine/`)
The core, independent AI logic (LangGraph workflows, LLM interactions, DB operations). Designed to run independently of the FastAPI server (e.g., via CLI or background workers).
- **`core/`**: Framework-level definitions.
  - `state.py`: Global TypedDict definitions for LangGraph state management.
  - `memory.py`: Checkpointing and session management logic.
- **`workflows/`**: Orchestration of agents through evolutionary stages. Contains versioned directories (e.g., `v1_baseline` to `v5_orchestrator`) to safely experiment with new multi-agent architectures without breaking stable versions.
- **`agents/`**: Definitions and behaviors for individual single-responsibility agents.
  - `base.py`: The `BaseAgent` class handling common logic (loading prompts, configs, and binding tools).
  - `factory.py`: Factory pattern for dynamically instantiating agents based on configuration.
  - `specialized/`: Specific agent implementations that override or extend base logic (e.g., ResearcherAgent).
- **`services/`**: Shared business logic and data pipelines.
  - `llm_service.py`: Factory supporting multiple LLM providers.
  - `jit_pipelines/`: Just-in-Time (JIT) ETL operations dynamically triggered via LangGraph nodes.
  - `guardrails.py`: Input and output safety and security validation.
- **`infrastructure/`**: Underlying external services for the Engine.
  - `db/`: Hybrid Memory Layer clients providing abstract interfaces for databases (e.g., Qdrant, DuckDB).
  - `observability/`: Tracing and monitoring hooks (e.g., LangSmith, Langfuse).

### 2.3 Testing (`backend/tests/`)
Contains programmatic software engineering Unit and Integration Tests. These tests have clear pass/fail criteria and execute quickly.

### 2.4 Evaluation (`backend/evaluation/`)
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
