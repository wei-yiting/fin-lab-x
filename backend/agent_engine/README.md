# Agent Engine

The core AI orchestration layer for FinLab-X.

## Architecture

### Components

- **Orchestrator**: Central reasoning engine (version-agnostic, loads capabilities from config)
- **Tools**: Atomic, stateless functions (yfinance, Tavily, SEC)
- **Observability**: LangSmith tracing for all execution steps

## Design Principles

1. **Single Orchestrator**: One central brain, not multi-agent routing
2. **Observability First**: Every step is traced via LangSmith
3. **Version-Agnostic Orchestrator**: Capabilities defined by version config, not code
4. **Zero Hallucination Policy**: All responses must be grounded in tool outputs

## Versioned Workflows

Each version has an independent `version_config.yaml` defining available tools and model settings:

- **v1_baseline (0.1.0)**: Naive single-chain financial analysis
- **v2_reader (0.2.0)**: Long-context document analysis with RAG
- **v3_quant (0.3.0)**: Numerical reasoning and quantitative modeling
- **v4_graph (0.4.0)**: Knowledge graph-based analysis
- **v5_analyst (0.5.0)**: Comprehensive investment research assistant

## Usage

```python
from backend.agent_engine.orchestrator.base import Orchestrator
from backend.agent_engine.workflows.config_loader import VersionConfigLoader

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
from backend.agent_engine.workflows.config_loader import VersionConfigLoader

loader = VersionConfigLoader('v1_baseline')
config = loader.load()

print(config.tools)  # ['yfinance_stock_quote', 'yfinance_get_available_fields', ...]
print(config.model.name)  # 'gpt-4o-mini'
print(config.version)  # '0.1.0'
```

## Folder Structure

- `orchestrator/`: Version-agnostic orchestrator (central reasoning engine)
- `tools/`: Atomic, stateless tool functions (financial, SEC)
- `observability/`: LangSmith tracing decorators
- `agents/specialized/`: Tool registry for dynamic loading
- `workflows/`: Versioned workflow configs and config loader
- `core/`: Shared core primitives (state, memory)
- `infrastructure/`: Integrations for persistence
- `services/`: Shared services (LLM access, guardrails)

## Implementation Guidelines

- Keep all LLM orchestration and tool usage within `agent_engine`.
- Prefer absolute imports (e.g., `from backend.agent_engine...`).
- Add new workflows under `workflows/` with their own `version_config.yaml`.
- Ensure tool definitions include strict schemas and error handling.
- All tools must be registered in the tool registry (`agents/specialized/registry.py`).
- Use `@trace_step` decorator for LangSmith observability on key functions.
