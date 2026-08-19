# FinLab-X Agent Guidelines (AGENTS.md)

Welcome, AI Agent! You are operating within the **FinLab-X** repository. This document outlines the critical workflows, commands, and code style guidelines you must follow when contributing to this project.

## 1. Project Overview

FinLab-X is a modular AI agent system designed to provide Just-in-Time (JIT) intelligence for US growth stocks. It follows a **single Orchestrator** pattern — one central reasoning engine with tools as capabilities, not a multi-agent architecture.
The codebase is split into two primary environments:

- **Backend (`backend/`)**: Python-based AI Agent Engine and FastAPI Web Server.
- **Frontend (`frontend/`)**: TypeScript-based Vite + React 19 chat UI (Vercel AI SDK UIMessage Stream Protocol).
- **Evaluation (`backend/evals/`)**: Scenario-first LLMOps evaluation framework (Braintrust).

For the accurate directory-by-directory layout and responsibilities, see
[`docs/file_structure.md`](docs/file_structure.md).

### Design Envelope (read before designing, implementing, or reviewing)

All design, implementation, and code-review decisions are calibrated against
[`docs/design-envelope.md`](docs/design-envelope.md) — the single source of truth for scale
assumptions, robustness targets, and depth allocation. Two symmetric rules:

- Robustness beyond the envelope is **over-engineering** — flag it for removal, not improvement.
- Shortcuts inside an envelope §4 Production-Grade Zone are **under-engineering**.

Both are Major findings in review (envelope §7). Cite envelope sections by number instead of
assuming production-scale requirements.

## 2. Build, Lint, and Test Commands

### Backend (Python / FastAPI / LangGraph)

The backend uses **Ruff** for fast linting and formatting, and **Pytest** for testing. Dependency management uses `uv`.

**Linting & Formatting:**

- Check linting (Ruff): `ruff check backend/`
- Fix auto-fixable lint issues: `ruff check --fix backend/`
- **Format code (Ruff) — run before every push:** `ruff format backend/`. CI's lint job runs `ruff format --check backend/` and will reject unformatted code. This is the only enforcement mechanism; there is no pre-commit hook or editor auto-format (see [ADR-0004](docs/adr/0004-ci-only-ruff-format-enforcement.md)).
- Type checking (MyPy/Pyright - if configured): `mypy backend/` or `pyright backend/`

**Testing (Pytest):**

- Run all tests: `pytest backend/tests/`
- **Run a single test file (CRITICAL for agents):** `pytest backend/tests/path/to/test_file.py`
- Run a specific test function: `pytest backend/tests/path/to/test_file.py::test_function_name`
- Run tests with printed output (useful for debugging): `pytest -s backend/tests/...`

**Regression Suite gate (burns real LLM/API calls — manual, pre-merge, never CI):**

- Run the gate: `pytest backend/evals/regression/ -m eval` (red = a task crash, a gated scorer below its metric floor, a fully-empty gated metric, or an enabled scenario with zero gated scorers; see ADR-0008/ADR-0015)
- Debug one case after a red light: `pytest backend/evals/regression/ -m eval -k "LP-07" -s`
- Test another Workflow Profile: `EVAL_PROFILE=<name> pytest backend/evals/regression/ -m eval` (default `baseline`; this env var is read only by the regression conftest)

### Frontend (Vite / React 19 / TypeScript)

The frontend uses **pnpm** (there is a `pnpm-lock.yaml`; do not introduce `package-lock.json` or `yarn.lock`). Run all commands from the `frontend/` directory.

**Build & Run:**

- Install dependencies: `pnpm install`
- Run development server: `pnpm dev`
- Build for production: `pnpm build` (runs `tsc -b` then `vite build` — type errors fail the build)

**Linting & Formatting:**

- Run ESLint: `pnpm lint`
- Format with Prettier: `pnpm format`
- Check formatting (what CI runs): `pnpm format:check`

**Testing (Vitest / Playwright):**

- Run unit tests: `pnpm test`
- **Run a single test:** `pnpm test path/to/test.file.test.ts`
- Run E2E tests (Playwright): `pnpm test:e2e`

## 3. Code Style Guidelines

### 3.1. Backend (Python)

- **Typing:** Strict typing is mandatory. Use Python's `typing` module (`List`, `Dict`, `Optional`, `Any`, `TypedDict`). All function arguments and return types must be explicitly annotated.
- **Formatting:** Adhere to **Ruff** defaults (typically equivalent to Black, max line length 88).
- **Imports:**
  - Group imports correctly: Standard library first, third-party libraries second, internal project imports last.
  - Use absolute imports within the project (e.g., `from backend.agent_engine.agents.base import Orchestrator`).
- **Naming Conventions:**
  - Variables, functions, methods: `snake_case`
  - Classes, Exceptions: `PascalCase`
  - Constants: `UPPER_SNAKE_CASE`
- **Error Handling:** Use custom exception classes where possible. Never use bare `except:` blocks; always catch specific exceptions (e.g., `except ValueError as e:`). Use FastAPI's `HTTPException` appropriately in the `api/` directory.
- **Docstrings:** Use Google-style docstrings for complex classes and functions. Keep them concise and focused on the _why_.

### 3.2. Frontend (TypeScript & React)

- **Typing:** Strict TypeScript typing. Avoid `any`; use `unknown` if necessary. Define exact interfaces or types for component props and state.
- **Components:** Use functional components and React Hooks. Prefer default exports for page components and named exports for shared UI components.
- **Styling:** Adhere to the configured styling solution (e.g., Tailwind CSS). Keep utility classes organized.
- **Imports:** Use absolute imports where path aliases (e.g., `@/components/...`) are configured.
- **Naming Conventions:**
  - Components, Interfaces, Types: `PascalCase`
  - Variables, functions, hooks (`use...`): `camelCase`
  - Constants: `UPPER_SNAKE_CASE`
- **Error Handling:** Gracefully handle API errors and render appropriate error boundaries or fallback UI components.

## 4. Architecture & Design Principles

When modifying or generating code, strictly follow the project's **Clean Architecture** and decoupling guidelines:

- **Decoupled API & Agent Engine:** The `backend/api/` directory (FastAPI) handles HTTP/SSE routing only. It MUST NOT contain core AI logic. The `backend/agent_engine/` handles all LLM interactions, tool calls, and LangGraph state management. The API calls the engine, not vice-versa.
- **Single Orchestrator, Not Agent Subclasses:** There is no `BaseAgent` hierarchy. `backend/agent_engine/agents/base.py` defines the one `Orchestrator` class (central reasoning engine); behavior variants are **Workflow Profiles** under `backend/agent_engine/agents/profiles/<name>/` (`orchestrator_config.yaml` + optional `system_prompt.md`), validated by `config_loader.py`. To change agent behavior, edit or add a profile config — do not hardcode prompts or introduce new agent classes.
- **Conversation Memory:** Session memory is LangGraph's `AsyncSqliteSaver` checkpointer, wired in the FastAPI lifespan (`backend/api/main.py`). `backend/agent_engine/infrastructure/` is an empty placeholder reserved for future capabilities — do not add database logic there (or anywhere) without an explicit design decision.
- **Data Ingestion & JIT Retrieval:** Ingestion pipelines live in `backend/ingestion/` (one directory per pipeline: `sec_filing_pipeline_html/`, `sec_dense_pipeline_html/`, `fundamentals_pipeline/`). JIT retrieval at question time goes through `backend/ingestion/sec_dense_pipeline_html/retriever.py` (`retriever.search()` is the single trace root for RAG queries). There is no `services/jit_pipelines/` directory; `backend/agent_engine/services/` is an empty placeholder.
- **Evaluations vs Tests:** Place purely programmatic tests in `backend/tests/`. Place LLM outputs, relevancy, and accuracy evaluations in `backend/evals/` (scenario-first layout: each `scenarios/<name>/` directory is self-contained with `eval_spec.yaml`, dataset, and scorers).

### Ingestion Rewrite Coexistence (temporary until sunset)

- `backend/ingestion/sec_filing_pipeline_html/` (HTML pipeline) is frozen as the A/B baseline; do not modify it.
- `backend/common/sec_core.py` guards the A/B data contract while the baseline lives: existing public signatures and data-path behavior (what gets fetched, how sections parse, stub classification) must not change; new capabilities are added as new functions. Error classification and error-message wording sit outside the evaluated A/B material and may be corrected in place.
- `backend/ingestion/sec_text_pipeline/`'s `ParsedFiling` schema (including the not-yet-produced `StructuredItem` branch) is deliberately frozen now so the follow-up detection/ingest/inspect work builds against a stable contract — a ratified exception to the design-envelope §0 reachability rule.
- The frozen tree participates in the shared error taxonomy (it raises/catches `backend/common/errors` classes) but keeps its own internals — including its local 3-attempt retry loop in `pipeline.py` — as temporary exceptions to ADR-0012/ADR-0013. Do not extend or refactor it beyond what the taxonomy requires, and do not migrate its retry loop to `retry_transient`.
- This entire subsection is deleted in the sunset PR together with the frozen pipeline.

## 5. Agent Operational Directives

- **Understand First:** Before writing any code, heavily utilize `glob`, `read`, and `grep` to understand the existing conventions in the file or module you are modifying.
- **Verify Assumptions:** Do not assume standard configurations. If a command (like `pytest` or `npm test`) fails, inspect the configuration files (e.g., `pyproject.toml`, `package.json`) to deduce the correct execution path.
- **Atomic Changes:** Ensure your implementations don't introduce breaking changes to adjacent modules, especially the streaming contract in `backend/agent_engine/streaming/` and the tool registry in `backend/agent_engine/tools/`.
- **Placeholder Replacement:** When developing a scaffolded feature, proactively replace placeholder content with robust, idiomatic code, but stick to the bounds of the assigned task.
- **Security Check:** Avoid committing secrets. If working with API keys (e.g., OpenAI, Finnhub, Tavily, Braintrust, Langfuse), ensure they are loaded via environment variables and NEVER hardcoded in source files.

(Remember: Always write tests to verify your code before completing a task!)

## Agent skills

### Issue tracker

Issues live in Linear — team Project-Dev (`DEV-`), project FinLab-X. Features are parent issues; tickets are sub-issues with native blocking relations. See `docs/agents/issue-tracker.md`.

### Domain docs

Single-context: one `CONTEXT.md` at the repo root plus `docs/adr/`. See `docs/agents/domain.md`.
