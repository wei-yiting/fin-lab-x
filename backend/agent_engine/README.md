# Agent Engine

## Scope

The core AI orchestration layer for FinLab-X, responsible for managing agents, tools, and workflows.

## Map

- `agents/`: Version-agnostic Orchestrator and version configs.
- `tools/`: Atomic, stateless tool functions and central registry.
- `skills/`: Higher-level capabilities (placeholder).

## Design Pattern

The Agent Engine follows a **Version-Agnostic Orchestrator** pattern:
- **Single Orchestrator**: A central brain that executes workflows based on configuration.
- **Configuration-Driven**: Capabilities, tools, and model settings are defined in version-specific YAML files.
- **Stateless Tools**: Tools are atomic, stateless functions that can be easily plugged into any workflow.

## Extension Algorithm

To add a new component (tool, skill, or agent version):

### Adding a New Tool
1. Create a new Python file in `backend/agent_engine/tools/`.
2. Define the tool function with clear docstrings and type hints.
3. Register the tool in the central tool registry.
4. Add the tool name to the relevant `orchestrator_config.yaml` in `backend/agent_engine/agents/versions/`.

### Adding a New Skill
1. Create a new module in `backend/agent_engine/skills/`.
2. Implement the skill logic, ensuring it is modular and reusable.
3. Expose the skill through a clear interface.

### Adding a New Agent Version
1. Create a new directory in `backend/agent_engine/agents/versions/` (e.g., `v6_new_agent/`).
2. Create an `orchestrator_config.yaml` file defining the tools, model, and version metadata.
3. Update the `VersionConfigLoader` if necessary to support the new version.

## Architecture

### Components

- **Agents**: Central reasoning engine (version-agnostic Orchestrator, loads capabilities from config)
- **Tools**: Atomic, stateless functions (yfinance, Tavily, SEC)
- **Observability**: Langfuse tracing via `CallbackHandler` + LangChain `config.metadata` (trace_name, request_id) + `propagate_attributes()` for session correlation

## Observability

Langfuse integration traces all AI agent execution in FinLab-X. Requires `langfuse>=4.5.0`.

### Tracing Mechanisms

| Mechanism | Where | What It Does |
|---|---|---|
| `CallbackHandler` | Per-request instance built in `_build_langfuse_config()` | Auto-traces LLM calls, tool dispatch, chain steps (including tool I/O) |
| `config["metadata"]["langfuse_trace_name"]` | `f"{VersionConfig.name}_{mode}"` in `_build_langfuse_config()` | Renames root trace (`v1_baseline_stream` / `v1_baseline_invoke`) via Langfuse ≥4.3.1 PR #1626 |
| `config["run_name"]` | `"chat-turn"` in `_build_langfuse_config()` | Renames the LangChain root chain span so it's not called `LangGraph` |
| `config["metadata"]["request_id"]` | `uuid.uuid4().hex` minted per FastAPI request | Per-request correlation attribute |
| `propagate_attributes(trace_name=..., session_id=...)` | Wraps `invoke`/`ainvoke`/`astream` in `Orchestrator` | Sets `trace_name` on OTel context + propagates session_id to children (incl. any `@observe` tools) |
| `@observe()` | Applied selectively on deterministic helpers and on a tool when it needs sub-spans / custom metadata | Traces a function as a single observation |

Trace name follows the agent `VersionConfig.name` dynamically — switching to a future `v2_xxx` config automatically re-names traces to `v2_xxx_{mode}` with no code change.

### When to Use Which

- **LLM calls, tool I/O, chain steps** — automatic via `CallbackHandler`; no decorator needed.
- **Rename root trace / inner root span** — done once in `_build_langfuse_config()`, callers only choose `mode="invoke"` vs `mode="stream"`.
- **Per-request `request_id`** — generated in the FastAPI router (`chat.py`, `chat_invoke.py`), passed into the orchestrator method.
- **Session correlation (`session_id`, `trace_name`)** — `propagate_attributes()` inside `Orchestrator.run`/`arun`/`astream_run`.
- **A new deterministic helper with nested work worth separating** — add `@observe(name="...")`.
- **A tool that needs sub-spans, custom metadata, or the observation id from inside its body** — add `@observe(name="tool_name")` on that specific tool (uncommon; most tools work well without it).

### Environment Variables

| Variable | Description |
|---|---|
| `LANGFUSE_SECRET_KEY` | Langfuse project secret key |
| `LANGFUSE_PUBLIC_KEY` | Langfuse project public key |
| `LANGFUSE_HOST` | Langfuse host URL (default: `https://cloud.langfuse.com`) |

### Adding a New Tool (default — no `@observe`)

```python
@tool("my_new_tool", args_schema=MyInputModel)
def my_new_tool(param: str) -> dict[str, Any]:
    ...
```

`CallbackHandler` will emit a tool span with input args, return value, and duration.

### Adding a Tool That Needs Its Own `@observe`

Reserve this for tools with sub-operations you want individually timed or annotated.

```python
from langfuse import observe

@tool("my_heavy_tool", args_schema=MyInputModel)
@observe(name="my_heavy_tool")
def my_heavy_tool(param: str) -> dict[str, Any]:
    # e.g., uses traced_span(...) internally, or calls get_current_observation_id()
    ...
```

Decorator stacking order: `@tool` (outer) → `@observe` (inner).

## Design Principles

1. **Single Orchestrator**: One central brain, not multi-agent routing
2. **Observability First**: Every step is traced via Langfuse
3. **Version-Agnostic Orchestrator**: Capabilities defined by version config, not code
4. **Zero Hallucination Policy**: All responses must be grounded in tool outputs

## Versioned Workflows

Each version has an independent `orchestrator_config.yaml` defining available tools and model settings:

- **v1_baseline (0.1.0)**: Naive single-chain financial analysis
- **v2_reader (0.2.0)**: Long-context document analysis with RAG
- **v3_quant (0.3.0)**: Numerical reasoning and quantitative modeling
- **v4_graph (0.4.0)**: Knowledge graph-based analysis
- **v5_analyst (0.5.0)**: Comprehensive investment research assistant

## Usage

```python
from backend.agent_engine.agents.base import Orchestrator
from backend.agent_engine.agents.config_loader import VersionConfigLoader

# Load version config
config_loader = VersionConfigLoader('v1_baseline')
config = config_loader.load()

# Initialize orchestrator
orchestrator = Orchestrator(config)

# Run
result = orchestrator.run("Analyze AAPL stock")
```

## Loading Version Config

```python
from backend.agent_engine.agents.config_loader import VersionConfigLoader

loader = VersionConfigLoader('v1_baseline')
config = loader.load()

print(config.tools)  # ['yfinance_stock_quote', 'yfinance_get_available_fields', ...]
print(config.model.name)  # 'gpt-4o-mini'
print(config.version)  # '0.1.0'
```
