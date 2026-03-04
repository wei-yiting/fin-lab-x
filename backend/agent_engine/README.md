# Agent Engine

## Folder Responsibility
Implements the core Agent Engine for FinLab-X, including agents, workflows, services, and infrastructure components.

## File Manifest
- `__init__.py`: Package exports.
- `agents/`: Agent definitions, factories, and specialized tools.
- `core/`: Shared core primitives (state, memory, etc.).
- `infrastructure/`: Integrations for observability and persistence.
- `services/`: Shared services (LLM access, guardrails).
- `workflows/`: Agent workflows and orchestration layers.

## Architecture & Design
- Agents encapsulate LLM prompting and tool usage.
- Workflows define execution flow without coupling to API routing.
- Infrastructure components are isolated from business logic via services.

## Implementation Guidelines
- Keep all LLM orchestration and tool usage within `agent_engine`.
- Prefer absolute imports (e.g., `from backend.agent_engine...`).
- Add new workflows under `workflows/` with their own README.
- Ensure tool definitions include strict schemas and error handling.
