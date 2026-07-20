# FinLab-X Documentation

## Scope

Central repository for architectural specifications, design plans, and project guides.

## Map

- `design-envelope.md`: **Read first.** Calibration SSOT for scale assumptions, robustness targets, and depth allocation — every design, implementation, and review decision cites it by section number.
- `adr/`: Architecture Decision Records — one file per decision (`NNNN-slug.md`, ≤100 words: decision + rejected alternatives + why). A reversed decision gets a new ADR superseding the old by number; envelope-reduced robustness cites `design-envelope.md` §9.
- `agent_architecture.md`: High-level architecture, Single Orchestrator pattern, and design principles.
- `file_structure.md`: Comprehensive mapping of directory responsibilities and file roles.
- `observability.md`: Langfuse tracing patterns across the agent layer and ingestion pipelines; span inventory and trace hierarchy for the SEC pipeline.
- `project_requirement.md`: Product Requirements Document (PRD) covering the v1-v5 evolutionary phases, architectural philosophy, and evaluation-driven development strategy.
- `frontend_chat_architecture.md`: Streaming chat UI architecture — atomic 6-layer taxonomy, SSE event handling, AI SDK v6 contract findings, defer-to-ready markdown strategy.
- `frontend_dom_contract.md`: Stable `data-testid` / `data-status` / `aria-label` contract for the streaming chat UI, referenced by component tests and e2e specs.

## Placement Policy

Documentation placement follows the Documentation Envelope (`design-envelope.md` §6):

- README files exist only where behavior is not evident from the code — never per test folder.
- Durable decision narrative goes to `docs/adr/` (one ADR per decision), not new structure documents.
- Per-feature design docs are disposable; this directory holds only long-lived references.

## Folder Responsibility

This directory maintains the "Source of Truth" for the project's design and evolution.

## Implementation Guidelines

- All documentation must be written in English.
- Update documentation simultaneously with code changes (Definition of Done).
- Follow `design-envelope.md` §6 for documentation placement.

## Extension Algorithm

To add new documentation files:

1. First ask whether the document should exist at all (`design-envelope.md` §6) — durable decisions go to `docs/adr/`, not new structure documents.
2. Create a new Markdown file with a clear, descriptive name in root `docs/`.
3. Ensure the content follows the project's documentation standards (English only, no emojis).
4. Update the `Map` in this README.md to include the new file.
