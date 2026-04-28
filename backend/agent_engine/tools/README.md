## Scope
Atomic, stateless tool functions and central registry. This module provides the interface for the agent to interact with external data sources, ensuring all data retrieved is grounded and traceable.

## Map
- `registry.py`: Manages the global `TOOL_REGISTRY` dictionary. Provides utility functions for registering, retrieving, and listing available tools.
- `financial.py`: Implements tools for quantitative data retrieval via `yfinance` and event-driven news search via `Tavily`.
- `sec_filing_tools.py`: Implements the two-step SEC 10-K access pair — `sec_filing_list_sections` (returns the canonical item table of contents with `char_count` / `is_stub` metadata) and `sec_filing_get_section` (returns one item's full content by `section_key`). Both call `edgartools`' structured `TenK` API directly via `backend.common.sec_core`.
- `sec_filing.py`: `sec_filing_downloader` — LangChain `@tool` wrapping `SECFilingPipeline.process()`. Downloads 10-K filings on demand (JIT), returns metadata + local file path for downstream RAG. Separate from the edgartools-direct path in `sec_filing_tools.py`.
- `__init__.py`: Contains the `setup_tools()` function, which serves as the central entry point for tool registration.

## Why two SEC paths

`sec_filing_tools.py` and `sec_filing.py` both operate on 10-K filings but serve different consumers: the structured two-step pair gives the agent low-latency, item-level reads that fit inside a single chat turn, while the pipeline-backed downloader produces persistent Markdown for downstream RAG ingestion. Both share the `FilingType` enum, the `SECError` hierarchy, and edgartools-error classification through `backend.common.sec_core` — see [`backend/common/sec_core.md`](../../common/sec_core.md) for the architecture diagram and the rationale that ties the two paths together.

## Design Pattern
- **Registry Pattern**: Tools are maintained in a central `TOOL_REGISTRY` dictionary, allowing the `Orchestrator` to dynamically load only the tools required by a specific version configuration.
- **Decorator Pattern**:
    - Uses LangChain's `@tool` decorator to automatically generate tool schemas from function signatures and Pydantic models.
    - Langfuse tracing for tool invocations is provided by the orchestrator's `CallbackHandler` — individual tools do **not** need `@observe()` for baseline tracing. Add `@observe(name=...)` only when a tool has its own sub-spans, custom metadata, or needs `get_current_observation_id()` from inside its body (see `backend/agent_engine/docs/streaming_observability_guardrails.md` Rule 3).

## Extension Algorithm
1. **Implement Tool Function**: Create a new function in `financial.py`, `sec_filing_tools.py`, or a new module. Ensure it returns a JSON-serializable dictionary.
2. **Define Input Schema**: Create a Pydantic `BaseModel` to define the tool's input arguments and descriptions.
3. **Apply Decorators**: Wrap the function with `@tool("tool_name", args_schema=YourInputModel)`. Do **not** add `@observe()` unless the tool meets one of the criteria in the Design Pattern note above; the `CallbackHandler` in `Orchestrator` already captures tool inputs, outputs, and duration automatically.
4. **Register the Tool**: Import the new tool in `backend/agent_engine/tools/__init__.py` and add a `register_tool("tool_name", your_tool_function)` call inside `setup_tools()`.
5. **Enable in Config**: Add the new `"tool_name"` to the `tools` list in one or more `orchestrator_config.yaml` files in the `versions/` directory.
