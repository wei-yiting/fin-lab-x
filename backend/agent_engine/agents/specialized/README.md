# Specialized Tools

## Folder Responsibility
Contains LangChain tool implementations used by workflows for external data access.

## File Manifest
- `__init__.py`: Tool exports for workflow wiring.
- `tools.py`: Tool implementations and schemas for v1 baseline.

## Architecture & Design
- Tools are defined with `@tool` decorators and strict Pydantic `args_schema`.
- Each tool returns JSON-serializable payloads or explicit error strings.

## Implementation Guidelines
- Enforce strict input schemas and avoid `any` types.
- Wrap external API calls with `try/except` and return clear errors.
- Hardcode trusted domains for news search to avoid untrusted sources.
