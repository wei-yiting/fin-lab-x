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
The core, independent AI logic (orchestrator, tools, skills, MCP, subagents). Designed to run independently of the FastAPI server (e.g., via CLI or background workers).

#### Core Components:
- **`orchestrator/`**: Central reasoning engine that manages state, plans steps, and selects tools.
  - `base.py`: Abstract base class for all orchestrators.
  - `v1_financial.py`: v1 financial analysis orchestrator implementation.
- **`tools/`**: Atomic, stateless functions for specific data retrieval or actions.
  - `base.py`: Base class for all tools.
  - `financial.py`: Financial data tools (yfinance, Tavily).
  - `sec.py`: SEC document retrieval tools.
- **`skills/`**: Higher-level, encapsulated capabilities with progressive disclosure.
  - `base.py`: Base class and metadata structure for skills.
  - `registry.py`: Skill registry with lazy loading.
- **`mcp/`**: Model Context Protocol integrations for external connectivity.
  - `base.py`: Base class for MCP server connections.
  - `client.py`: MCP client for managing multiple server connections.
- **`subagents/`**: Short-lived, specialized agents for isolated sub-tasks.
  - `base.py`: Subagent configuration and base class.
  - `spawner.py`: Subagent spawning and management.
- **`observability/`**: Integration with LangSmith for tracing and evaluation.
  - `langsmith_tracer.py`: Decorator for step-level tracing.

#### Versioned Workflows:
- **`workflows/`**: Orchestration of agents through evolutionary stages.
  - `config_loader.py`: Version configuration loader (YAML-based).
  - `v1_baseline/`: Naive single-chain financial analysis.
    - `version_config.yaml`: v1 configuration (tools, model, constraints).
    - `chain.py`: v1 chain implementation.
  - `v2_reader/`: Long-context document analysis and RAG.
    - `version_config.yaml`: v2 configuration with RAG skills.
  - `v3_quant/`: Numerical reasoning and quantitative modeling.
    - `version_config.yaml`: v3 configuration with quant skills.
  - `v4_graph/`: Knowledge graph-based analysis.
    - `version_config.yaml`: v4 configuration with graph skills.
  - `v5_analyst/`: Comprehensive investment research assistant.
    - `version_config.yaml`: v5 configuration with all capabilities.

#### Legacy Components (Being Refactored):
- **`agents/`**: Legacy agent definitions (being refactored into orchestrator/ and subagents/).
  - `base.py`: Base agent class (legacy).
  - `factory.py`: Agent factory pattern (legacy).
  - `specialized/`: Specialized agent implementations.
    - `tools.py`: Tool definitions (being moved to tools/).
    - `registry.py`: Central tool registry.
- **`services/`**: Shared business logic (being refactored into tools/ and skills/).
- **`infrastructure/`**: External service clients (being refactored into observability/ and mcp/).

### 2.3 Testing (`backend/tests/`)
Contains programmatic software engineering Unit and Integration Tests. These tests have clear pass/fail criteria and execute quickly.
- **`orchestrator/`**: Tests for orchestrator components.
- **`tools/`**: Tests for tool implementations.
- **`skills/`**: Tests for skill registry and loading.
- **`mcp/`**: Tests for MCP client.
- **`subagents/`**: Tests for subagent spawner.
- **`agents/`**: Tests for agent registry.

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

---

## 4. Documentation (`docs/`)

- **`ARCHITECTURE.md`**: High-level architecture documentation (Single Orchestrator pattern).
- **`plans/`**: Implementation plans and design documents.

---

## 5. Skills Directory (`backend/skills/`)

Filesystem-based skills storage with progressive disclosure:
- Each skill is a directory containing:
  - `skill.md`: Skill definition with YAML frontmatter (metadata) and full instructions.
  - Additional resources (examples, templates, etc.).
- Skills are loaded lazily: metadata first, full instructions on demand.

---

## 6. Key Design Principles

### 6.1 Single Orchestrator Pattern
- One central reasoning engine manages all decisions.
- No complex multi-agent routing that can lead to non-deterministic behavior.
- Tools, Skills, MCP, and Subagents are capabilities, not independent agents.

### 6.2 Progressive Disclosure
- Skills expose metadata first (name, description, estimated tokens).
- Full skill instructions are loaded only when needed.
- Minimizes prompt noise and token usage.

### 6.3 Observability First
- Every LLM call, tool execution, and state change is traced via LangSmith.
- If it isn't logged, it didn't happen.
- Enables evaluation, debugging, and continuous improvement.

### 6.4 Versioned Workflows
- Each version (v1-v5) is independently callable.
- `version_config.yaml` defines allowed tools, skills, MCP, and subagents.
- Enables safe experimentation and easy rollback.

### 6.5 Code as Interface
- Tools and skills are strictly typed Python functions.
- Pydantic models for input validation.
- LLM interacts with code, not natural language descriptions.

---

## 7. Dependency Rules

To maintain a clean architecture, the following dependency rules are enforced:

1. **Orchestrator** can depend on `tools`, `skills`, `mcp`, `subagents`, and `observability`.
2. **Subagents** can depend on `tools` and `mcp`.
3. **Skills** can depend on `tools` and `mcp`.
4. **Tools** and **MCP** must be independent and stateless; they cannot depend on the orchestrator or skills.
5. **Circular Dependencies** are strictly prohibited.

---

## 8. Migration Notes

The project is transitioning from the legacy `ai_engine` structure to the `agent_engine` architecture.

- **Legacy `agents/`**: Being refactored into `subagents/` or integrated into the `orchestrator/` logic.
- **Legacy `workflows/`**: Replaced by the `orchestrator/` and the versioned profile system.
- **Legacy `services/`**: Moving to `tools/` (for atomic actions) or `skills/` (for complex logic).
- **Legacy `infrastructure/`**: Reorganized into `observability/` and `mcp/`.

---

## 9. Implementation Guidelines

When adding new features to this codebase:

1. **Follow the Single Orchestrator pattern**: Do not create new agent classes unless they are truly independent subagents.
2. **Use the Tool Registry**: Register all tools in `backend/agent_engine/agents/specialized/registry.py`.
3. **Create version configs**: When adding new capabilities, update the appropriate `version_config.yaml`.
4. **Add LangSmith tracing**: Use `@trace_step` decorator for all LLM calls and tool executions.
5. **Write tests**: All new components must have corresponding tests in `backend/tests/`.
6. **Update documentation**: Keep this file and `docs/ARCHITECTURE.md` in sync with code changes.
