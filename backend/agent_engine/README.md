# Agent Engine

The core AI orchestration layer for FinLab-X.

## Architecture

### Components

- **Agents**: Central reasoning engine (version-agnostic Orchestrator, loads capabilities from config)
- **Tools**: Atomic, stateless functions (yfinance, Tavily, SEC)
- **Observability**: LangSmith tracing for all execution steps

## Design Principles

1. **Single Orchestrator**: One central brain, not multi-agent routing
2. **Observability First**: Every step is traced via LangSmith
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

## Folder Structure

- `agents/`: Version-agnostic Orchestrator and version configs
- `tools/`: Atomic, stateless tool functions and central registry
- `skills/`: Higher-level capabilities (placeholder)
- `observability/`: LangSmith tracing decorators
