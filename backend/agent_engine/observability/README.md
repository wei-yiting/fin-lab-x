# Observability

## Scope

Langfuse integration for tracing all AI agent execution in FinLab-X.

## Architecture

Two tracing mechanisms work together:

| Mechanism | Where | What It Traces |
|-----------|-------|----------------|
| `CallbackHandler` | Injected once in `Orchestrator.run()`/`arun()` | All LangChain activity: LLM calls, tool dispatch, chain steps |
| `@observe()` | Applied directly on tool functions | Deterministic code paths (data transforms, API calls) |

`CallbackHandler` provides automatic parent-child trace hierarchy — all spans from a single request are linked under one trace.

## When to Use Which

- **LLM calls, tool dispatch, chain steps** → Automatic via `CallbackHandler` (no action needed)
- **New deterministic tool code** → Add `@observe(name="my_function")` decorator

## File Manifest

- `__init__.py` — Module docstring documenting the architecture
- `README.md` — This file

## Environment Variables

| Variable | Description |
|----------|-------------|
| `LANGFUSE_SECRET_KEY` | Langfuse project secret key |
| `LANGFUSE_PUBLIC_KEY` | Langfuse project public key |
| `LANGFUSE_HOST` | Langfuse host URL (default: `https://cloud.langfuse.com`) |

## Adding Observability to New Tools

```python
from langfuse import observe

@tool("my_new_tool", args_schema=MyInputModel)
@observe(name="my_new_tool")
def my_new_tool(param: str) -> dict[str, Any]:
    ...
```

Decorator stacking order: `@tool` (outer) → `@observe` (inner).
