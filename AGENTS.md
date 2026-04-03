# FinLab-X Agent Guidelines (AGENTS.md)

Welcome, AI Agent! You are operating within the **FinLab-X** repository. This document outlines the critical workflows, commands, and code style guidelines you must follow when contributing to this project.

## 1. Project Overview

FinLab-X is a modular, multi-agent AI system designed to provide Just-in-Time (JIT) intelligence for US growth stocks.
The codebase is split into two primary environments:

- **Backend (`/backend`)**: Python-based AI Agent Engine and FastAPI Web Server.
- **Frontend (`/frontend`)**: TypeScript-based Next.js Generative UI.
- **Evaluation (`backend/evaluation`)**: Independent LLMOps and evaluation framework.

## 2. Build, Lint, and Test Commands

### Backend (Python / FastAPI / LangGraph)

The backend uses **Ruff** for fast linting and formatting, and **Pytest** for testing. Dependency management is intended to be handled by modern tools like `uv` or `poetry`.

**Linting & Formatting:**

- Check linting (Ruff): `ruff check backend/`
- Fix auto-fixable lint issues: `ruff check --fix backend/`
- Format code (Ruff): `ruff format backend/`
- Type checking (MyPy/Pyright - if configured): `mypy backend/` or `pyright backend/`

**Testing (Pytest):**

- Run all tests: `pytest backend/tests/`
- **Run a single test file (CRITICAL for agents):** `pytest backend/tests/path/to/test_file.py`
- Run a specific test function: `pytest backend/tests/path/to/test_file.py::test_function_name`
- Run tests with printed output (useful for debugging): `pytest -s backend/tests/...`

### Frontend (Next.js / React / TypeScript)

The frontend uses standard Node.js package managers (`npm`, `pnpm`, or `yarn`).

**Build & Run:**

- Install dependencies: `npm install` (or `pnpm install`)
- Run development server: `npm run dev`
- Build for production: `npm run build`

**Linting & Formatting:**

- Run ESLint: `npm run lint`
- Fix ESLint issues: `npm run lint --fix`
- Format with Prettier: `npx prettier --write "frontend/src/**/*.{ts,tsx,css,md}"`

**Testing (Jest/Vitest/Playwright):**

- Run unit tests: `npm run test`
- **Run a single test:** `npm run test -- path/to/test.file.test.ts`
- Run E2E tests: `npm run test:e2e` (if configured)

## 3. Code Style Guidelines

### 3.1. Backend (Python)

- **Typing:** Strict typing is mandatory. Use Python's `typing` module (`List`, `Dict`, `Optional`, `Any`, `TypedDict`). All function arguments and return types must be explicitly annotated.
- **Formatting:** Adhere to **Ruff** defaults (typically equivalent to Black, max line length 88).
- **Imports:**
  - Group imports correctly: Standard library first, third-party libraries second, internal project imports last.
  - Use absolute imports within the project (e.g., `from backend.agent_engine.core.state import State`).
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
- **Agent Modularity:** In `backend/agent_engine/agents/`, inherit from `BaseAgent`. Keep single-responsibility principles in mind. Agents should rely on configuration files (`config/agents/`) rather than hardcoding prompts.
- **Hybrid Memory Layer:** Database logic goes in `backend/agent_engine/infrastructure/db/`. Do not bleed DB operations into the API routers or Agent logic directly; use abstract service interfaces.
- **JIT Data Pipelines:** ETL or data retrieval logic invoked by agents must reside in `backend/agent_engine/services/jit_pipelines/`.
- **Evaluations vs Tests:** Place purely programmatic tests in `backend/tests/`. Place LLM outputs, relevancy, and accuracy tests in the `backend/evaluation/` directory.

## 5. Agent Operational Directives

- **Understand First:** Before writing any code, heavily utilize `glob`, `read`, and `grep` to understand the existing conventions in the file or module you are modifying.
- **Verify Assumptions:** Do not assume standard configurations. If a command (like `pytest` or `npm test`) fails, inspect the configuration files (e.g., `pyproject.toml`, `package.json`) to deduce the correct execution path.
- **Atomic Changes:** Ensure your implementations don't introduce breaking changes to adjacent modules, especially within `backend/agent_engine/workflows/`.
- **Placeholder Replacement:** When developing a scaffolded feature, proactively replace placeholder content with robust, idiomatic code, but stick to the bounds of the assigned task.
- **Security Check:** Avoid committing secrets. If working with API keys (e.g., OpenAI, LangSmith), ensure they are loaded via environment variables and NEVER hardcoded in source files.

(Remember: Always write tests to verify your code before completing a task!)
