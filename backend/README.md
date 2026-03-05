# FinLab-X Backend

## Quick Start

```bash
# Install dependencies
uv sync

# Set environment variables
export OPENAI_API_KEY="..."
export TAVILY_API_KEY="..."
export EDGAR_IDENTITY="..."
export LANGSMITH_API_KEY="..."

# Run tests
uv run pytest

# Start API server
uv run python -m backend.api.main
```

## Architecture

See `backend/agent_engine/README.md` and `docs/ARCHITECTURE.md` for detailed architecture documentation.

## Versioned Workflows

FinLab-X uses versioned workflow configurations. Each version can be called independently:

```bash
# List available versions
uv run python -c "
from backend.agent_engine.workflows.config_loader import VersionConfigLoader
print(VersionConfigLoader.list_available_versions())
"
```

## Folder Structure

- `agent_engine/`: Core Agent Engine components (orchestrator, tools, observability, workflows).
- `api/`: HTTP/SSE routing and request handling (FastAPI).
- `evaluation/`: LLMOps and evaluation workflows.
- `tests/`: Programmatic tests for backend logic.
- `pyproject.toml`: Backend dependency and tooling configuration.

## Implementation Guidelines

- Keep API logic free of AI business logic; call into `agent_engine` services instead.
- Use strict typing for all Python functions and return types.
- Manage dependencies with `uv` and update `pyproject.toml` only with approval.
- Update README files alongside any structural or behavioral changes.
