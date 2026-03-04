# Agents

## Folder Responsibility
Defines agent abstractions, factories, and specialized tools used by workflows.

## File Manifest
- `__init__.py`: Package exports.
- `base.py`: Base agent contract (placeholder).
- `factory.py`: Agent factory wiring (placeholder).
- `specialized/`: Tool implementations and exports.

## Architecture & Design
- Agents should encapsulate prompt + tool behavior.
- Specialized tools are defined with LangChain `@tool` and strict Pydantic schemas.

## Implementation Guidelines
- Inherit from `BaseAgent` for new agents when implemented.
- Keep tool logic in `specialized/` and avoid coupling to API.
- Return explicit error strings on tool failures.
