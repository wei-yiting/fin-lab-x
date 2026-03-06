# FinLab-X Backend

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

See `backend/agent_engine/README.md` and `docs/ARCHITECTURE.md` for detailed architecture documentation.

## Versioned Workflows

FinLab-X uses versioned workflow configurations. Each version can be called independently:

```bash
# List available versions
uv run python -c "
from backend.agent_engine.agents.config_loader import VersionConfigLoader
print(VersionConfigLoader.list_available_versions())
"
```

## Folder Structure

- `agent_engine/`: Core Agent Engine components (orchestrator, tools, observability).
- `api/`: HTTP/SSE routing and request handling (FastAPI).
- `evaluation/`: LLMOps and evaluation workflows.
- `tests/`: Programmatic tests for backend logic.
- `../pyproject.toml`: Project dependency and tooling configuration (at project root).

## Implementation Guidelines

- Keep API logic free of AI business logic; call into `agent_engine` services instead.
- Use strict typing for all Python functions and return types.
- Manage dependencies with `uv` and update `pyproject.toml` only with approval.
- Update README files alongside any structural or behavioral changes.
