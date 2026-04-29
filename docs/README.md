# FinLab-X Documentation

## Scope

Central repository for architectural specifications, design plans, and project guides.

## Map

- `agent_architecture.md`: High-level architecture, Single Orchestrator pattern, and design principles.
- `file_structure.md`: Comprehensive mapping of directory responsibilities and file roles.
- `observability.md`: Langfuse tracing patterns across the agent layer and ingestion pipelines; span inventory and trace hierarchy for the SEC pipeline.
- `project_requirement.md`: Product Requirements Document (PRD) covering the v1-v5 evolutionary phases, architectural philosophy, and evaluation-driven development strategy.
- `frontend_chat_architecture.md`: Streaming chat UI architecture — atomic 6-layer taxonomy, SSE event handling, AI SDK v6 contract findings, defer-to-ready markdown strategy.
- `frontend_dom_contract.md`: Stable `data-testid` / `data-status` / `aria-label` contract for the streaming chat UI, referenced by component tests and e2e specs.

## Design Pattern

Documentation is organized following a **Hierarchical Knowledge Base** pattern:

- **Source of Truth**: Centralized architectural specifications.
- **Modular Plans**: Feature-specific design documents stored in the `plans/` directory.
- **Living Documentation**: README files at every major directory level to ensure local context.

## Folder Responsibility

This directory maintains the "Source of Truth" for the project's design and evolution.

## Implementation Guidelines

- All documentation must be written in English.
- Update documentation simultaneously with code changes (Definition of Done).
- Follow the AGENTS.md guidelines for folder-level documentation.

## Extension Algorithm

To add new documentation files:

1. Determine the appropriate location (root `docs/` for general architecture, `docs/plans/` for feature-specific plans).
2. Create a new Markdown file with a clear, descriptive name.
3. Ensure the content follows the project's documentation standards (English only, no emojis).
4. Update the `Map` in this README.md to include the new file.
5. If the documentation relates to a specific code module, ensure the module's local README.md also references it.
