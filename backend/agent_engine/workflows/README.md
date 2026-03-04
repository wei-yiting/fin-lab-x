# Workflows

## Folder Responsibility
Defines workflow orchestration layers and execution pipelines for agents.

## File Manifest
- `__init__.py`: Package exports.
- `v1_baseline/`: Naive single-chain workflow.
- `v2_multi_agent/`: Multi-agent workflow (placeholder).
- `v3_debate/`: Debate-style workflow (placeholder).
- `v4_supervisor/`: Supervisor workflow (placeholder).
- `v5_orchestrator/`: Orchestrator workflow (placeholder).

## Architecture & Design
- Each workflow version is isolated in its own folder.
- Workflows should expose clear creation functions (e.g., `create_*`).

## Implementation Guidelines
- Avoid stateful message history in v1 baseline workflows.
- Keep workflow logic independent from API routing.
- Add a README in every new workflow folder.
