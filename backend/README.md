# FinLab-X Backend

## Scope

This directory contains the backend services for FinLab-X, including the AI Agent Engine, API server, and evaluation framework.

## Map

- `agent_engine/`: Core Agent Engine components (orchestrator, tools, observability).
- `api/`: HTTP/SSE routing and request handling (FastAPI).
- `evaluation/`: LLMOps and evaluation workflows.
- `tests/`: Programmatic tests for backend logic.
- `../pyproject.toml`: Project dependency and tooling configuration (at project root).

## Design Pattern

The backend follows a **Clean Architecture** approach with a strict decoupling between the API layer and the Agent Engine:
- **Decoupled API & Engine**: The `api/` directory handles HTTP/SSE routing and request/response formatting only. It must not contain core AI logic.
- **Service Layer**: The API calls into `agent_engine` services, which encapsulate the business logic and LLM interactions.
- **Modular Agents**: AI logic is organized into modular agents and workflows within the `agent_engine`.

## Quick Start

```bash
# Install dependencies (from project root)
uv sync

# Set environment variables
cp backend/.env.example backend/.env
# Edit backend/.env with your API keys

# Run tests
uv run pytest

# Start API server
uv run uvicorn backend.api.main:app --reload
```

## Architecture

See `backend/agent_engine/README.md` and `docs/agent_architecture.md` for detailed architecture documentation.

## Versioned Workflows

FinLab-X uses versioned workflow configurations. Each version can be called independently:

```bash
# List available versions
uv run python -c "
from backend.agent_engine.agents.config_loader import VersionConfigLoader
print(VersionConfigLoader.list_available_versions())
"
```

## Implementation Guidelines

- Keep API logic free of AI business logic; call into `agent_engine` services instead.
- Use strict typing for all Python functions and return types.
- Manage dependencies with `uv` and update `pyproject.toml` only with approval.
- Update README files alongside any structural or behavioral changes.

## Extension Algorithm

To add a new module to the backend:
1. Identify the module's responsibility (API, Agent Engine, or Infrastructure).
2. Create a new directory or file in the appropriate location (e.g., `backend/agent_engine/services/`).
3. Define the module's interface using strict Python typing.
4. Implement the logic, ensuring it remains decoupled from other modules.
5. Add unit tests in `backend/tests/` to verify the new module's functionality.
6. Update the relevant README.md files to reflect the new module.
