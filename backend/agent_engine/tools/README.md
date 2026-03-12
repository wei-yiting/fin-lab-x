## Scope
Atomic, stateless tool functions and central registry. This module provides the interface for the agent to interact with external data sources, ensuring all data retrieved is grounded and traceable.

## Map
- `registry.py`: Manages the global `TOOL_REGISTRY` dictionary. Provides utility functions for registering, retrieving, and listing available tools.
- `financial.py`: Implements tools for quantitative data retrieval via `yfinance` and event-driven news search via `Tavily`.
- `sec.py`: Implements tools for retrieving official SEC filings (10-K, 10-Q) and extracting key sections like Risk Factors and MD&A.
- `__init__.py`: Contains the `setup_tools()` function, which serves as the central entry point for tool registration.

## Design Pattern
- **Registry Pattern**: Tools are maintained in a central `TOOL_REGISTRY` dictionary, allowing the `Orchestrator` to dynamically load only the tools required by a specific version configuration.
- **Decorator Pattern**: 
    - Uses LangChain's `@tool` decorator to automatically generate tool schemas from function signatures and Pydantic models.
    - Uses a custom `@trace_step` decorator to inject LangSmith tracing and metadata into tool execution.

## Extension Algorithm
1. **Implement Tool Function**: Create a new function in `financial.py`, `sec.py`, or a new module. Ensure it returns a JSON-serializable dictionary.
2. **Define Input Schema**: Create a Pydantic `BaseModel` to define the tool's input arguments and descriptions.
3. **Apply Decorators**: Wrap the function with `@tool("tool_name", args_schema=YourInputModel)` and `@trace_step(...)`.
4. **Register the Tool**: Import the new tool in `backend/agent_engine/tools/__init__.py` and add a `register_tool("tool_name", your_tool_function)` call inside `setup_tools()`.
5. **Enable in Config**: Add the new `"tool_name"` to the `tools` list in one or more `orchestrator_config.yaml` files in the `versions/` directory.
