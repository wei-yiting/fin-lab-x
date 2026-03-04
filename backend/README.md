# Backend

## Folder Responsibility
Houses the FastAPI API layer, Agent Engine, evaluation harness, and automated tests for FinLab-X.

## File Manifest
- `agent_engine/`: Core Agent Engine components (agents, workflows, services, infrastructure).
- `api/`: HTTP/SSE routing and request handling.
- `evaluation/`: LLMOps and evaluation workflows.
- `tests/`: Programmatic tests for backend logic.
- `pyproject.toml`: Backend dependency and tooling configuration.

## Architecture & Design
- Clean Architecture separation: API routes are thin and call into `agent_engine`.
- AI logic (LLM, tools, workflows) lives only in `agent_engine`.
- Evaluations and tests are kept separate by design.

## Implementation Guidelines
- Keep API logic free of AI business logic; call into `agent_engine` services instead.
- Use strict typing for all Python functions and return types.
- Manage dependencies with `uv` and update `pyproject.toml` only with approval.
- Update README files alongside any structural or behavioral changes.
