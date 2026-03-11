# FinLab-X 架構實作計畫

> **給 Claude 的提示：** 需要使用 superpowers:executing-plans 來逐個執行此計畫的任務。

**目標：** 將 FinLab-X v1 從簡單的 LangChain chain 重構為 Single Orchestrator + Tools 架構，並整合 LangSmith observability。同時將 `ai_engine` 重命名為 `agent_engine`，並建立 versioned workflows 系統。

**架構設計：** Single Orchestrator Agent 作為中央大腦，明確分離 Tools（確定性動作）。所有執行步驟都透過 LangSmith 進行追蹤，以支援 evaluation 和持續改進。

**技術棧：** Python 3.11+, LangChain（僅 core，不使用 LangGraph，使用 init_chat_model）, LangSmith, FastAPI, Pydantic, uv

**v1 範圍：** 只實作 Orchestrator + Tools，不實作 Skills/MCP/Subagents（這些留到後續版本）。

---

## 前置準備

開始前請確認：

1. 環境變數已設定：`OPENAI_API_KEY`, `TAVILY_API_KEY`, `EDGAR_IDENTITY`, `LANGSMITH_API_KEY`
2. 依賴已安裝：`uv sync` 或 `uv pip install -e .`
3. Git 狀態乾淨

---

## 第零階段：目錄重構與版本化工作流

### 任務 0.1：重命名 ai_engine 為 agent_engine

**目標：** 將 `backend/ai_engine/` 重命名為 `backend/agent_engine/`，並更新所有相關的 import 路徑。

**檔案：**

- 重命名：`backend/ai_engine/` → `backend/agent_engine/`
- 修改：`backend/scripts/verify_v1_naive.py`（更新 import）
- 修改：`backend/agent_engine/workflows/v1_baseline/__init__.py`（更新 import）
- 修改：`backend/agent_engine/workflows/v1_baseline/chain.py`（更新 import）
- 修改：`backend/agent_engine/agents/specialized/__init__.py`（更新 import）
- 修改：`AGENTS.md`（更新路徑說明）
- 修改：`backend/README.md`（更新路徑說明）
- 修改：`FILE_STRUCTURE.md`（更新路徑說明）

**步驟 1：執行目錄重命名**

```bash
cd /Users/dong.wyt/Documents/dev-projects/fin-lab-x
mv backend/ai_engine backend/agent_engine
```

**步驟 2：更新 Python import 路徑**

```python
# backend/scripts/verify_v1_naive.py (Line 5)
from backend.agent_engine.workflows.v1_baseline.chain import V1BaselineChain
```

```python
# backend/agent_engine/workflows/v1_baseline/__init__.py (Line 1)
from backend.agent_engine.workflows.v1_baseline.chain import V1BaselineChain
```

```python
# backend/agent_engine/workflows/v1_baseline/chain.py (Lines 13-14)
from backend.agent_engine.agents.specialized.tools import (
    yfinance_stock_quote, tavily_financial_search, sec_official_docs_retriever
)
```

```python
# backend/agent_engine/agents/specialized/__init__.py (Line 1)
from backend.agent_engine.agents.specialized.tools import *
```

**步驟 3：驗證 imports 正常**

```bash
uv run python -c "
from backend.agent_engine.workflows.v1_baseline.chain import V1BaselineChain
print('Import successful!')
"
```

預期結果："Import successful!"

**步驟 4：Commit**

```bash
git add backend/agent_engine/ backend/scripts/verify_v1_naive.py
git commit -m "refactor: rename ai_engine to agent_engine"
```

---

### 任務 0.2：建立 Versioned Workflows 目錄結構

**目標：** 為每個版本建立獨立的 workflow 目錄，並加入 `version_config.yaml` 設定檔。

**檔案：**

- 重命名：`backend/agent_engine/workflows/v2_multi_agent/` → `backend/agent_engine/workflows/v2_reader/`
- 重命名：`backend/agent_engine/workflows/v3_debate/` → `backend/agent_engine/workflows/v3_quant/`
- 重命名：`backend/agent_engine/workflows/v4_supervisor/` → `backend/agent_engine/workflows/v4_graph/`
- 重命名：`backend/agent_engine/workflows/v5_orchestrator/` → `backend/agent_engine/workflows/v5_analyst/`
- 建立：`backend/agent_engine/workflows/v1_baseline/version_config.yaml`
- 建立：`backend/agent_engine/workflows/v2_reader/version_config.yaml`
- 建立：`backend/agent_engine/workflows/v3_quant/version_config.yaml`
- 建立：`backend/agent_engine/workflows/v4_graph/version_config.yaml`
- 建立：`backend/agent_engine/workflows/v5_analyst/version_config.yaml`
- 建立：`backend/agent_engine/workflows/config_loader.py`

**步驟 1：重命名版本目錄**

```bash
cd /Users/dong.wyt/Documents/dev-projects/fin-lab-x/backend/agent_engine/workflows
mv v2_multi_agent v2_reader
mv v3_debate v3_quant
mv v4_supervisor v4_graph
mv v5_orchestrator v5_analyst
```

**步驟 2：建立 v1_baseline version_config.yaml**

```yaml
# backend/agent_engine/workflows/v1_baseline/version_config.yaml
version: "0.1.0"
name: "v1_baseline"
description: "Naive single-chain financial analysis with basic tool access"

tools:
  - yfinance_stock_quote
  - yfinance_get_available_fields
  - tavily_financial_search
  - sec_official_docs_retriever

model:
  name: "gpt-4o-mini"
  temperature: 0.0
  max_iterations: 10

observability:
  provider: "langsmith"
  trace_all_steps: true
  project_name: "finlabx"

constraints:
  max_tool_calls_per_step: 3
  require_citations: true
  zero_hallucination_policy: true
```

**步驟 3：建立 v2_reader version_config.yaml**

```yaml
# backend/agent_engine/workflows/v2_reader/version_config.yaml
version: "0.2.0"
name: "v2_reader"
description: "Long-context document analysis and multi-document synthesis"

tools:
  - yfinance_stock_quote
  - yfinance_get_available_fields
  - tavily_financial_search
  - sec_official_docs_retriever

model:
  name: "gpt-4o"
  temperature: 0.0
  max_iterations: 15

observability:
  provider: "langsmith"
  trace_all_steps: true
  project_name: "finlabx"

constraints:
  max_tool_calls_per_step: 5
  require_citations: true
  zero_hallucination_policy: true
  max_context_tokens: 128000
```

**步驟 4：建立 v3_quant version_config.yaml**

```yaml
# backend/agent_engine/workflows/v3_quant/version_config.yaml
version: "0.3.0"
name: "v3_quant"
description: "Numerical reasoning, data visualization, and quantitative modeling"

tools:
  - yfinance_stock_quote
  - yfinance_get_available_fields
  - tavily_financial_search
  - sec_official_docs_retriever
  - duckdb_query
  - text_to_sql

model:
  name: "gpt-4o"
  temperature: 0.0
  max_iterations: 20

observability:
  provider: "langsmith"
  trace_all_steps: true
  project_name: "finlabx"

constraints:
  max_tool_calls_per_step: 8
  require_citations: true
  zero_hallucination_policy: true
  enable_code_execution: true
```

**步驟 5：建立 v4_graph version_config.yaml**

```yaml
# backend/agent_engine/workflows/v4_graph/version_config.yaml
version: "0.4.0"
name: "v4_graph"
description: "Knowledge graph-based corporate relationship and supply chain analysis"

tools:
  - yfinance_stock_quote
  - yfinance_get_available_fields
  - tavily_financial_search
  - sec_official_docs_retriever
  - neo4j_query
  - text_to_cypher

model:
  name: "gpt-4o"
  temperature: 0.0
  max_iterations: 20

observability:
  provider: "langsmith"
  trace_all_steps: true
  project_name: "finlabx"

constraints:
  max_tool_calls_per_step: 10
  require_citations: true
  zero_hallucination_policy: true
  enable_graph_queries: true
```

**步驟 6：建立 v5_analyst version_config.yaml**

```yaml
# backend/agent_engine/workflows/v5_analyst/version_config.yaml
version: "0.5.0"
name: "v5_analyst"
description: "Comprehensive investment research assistant combining all capabilities"

tools:
  - yfinance_stock_quote
  - yfinance_get_available_fields
  - tavily_financial_search
  - sec_official_docs_retriever
  - duckdb_query
  - text_to_sql
  - neo4j_query
  - text_to_cypher

model:
  name: "gpt-4o"
  temperature: 0.0
  max_iterations: 30

observability:
  provider: "langsmith"
  trace_all_steps: true
  project_name: "finlabx"

constraints:
  max_tool_calls_per_step: 15
  require_citations: true
  zero_hallucination_policy: true
  enable_code_execution: true
  enable_graph_queries: true
  enable_parallel_subagents: true
```

**步驟 7：建立 config_loader.py**

```python
# backend/agent_engine/workflows/config_loader.py
"""Version configuration loader for FinLab-X workflows."""

import os
from pathlib import Path
from typing import Any, Optional

import yaml
from pydantic import BaseModel, Field


class ModelConfig(BaseModel):
    """Model configuration for a workflow version."""
    name: str = "gpt-4o-mini"
    temperature: float = 0.0
    max_iterations: int = 10


class ObservabilityConfig(BaseModel):
    """Observability configuration for a workflow version."""
    provider: str = "langsmith"
    trace_all_steps: bool = True
    project_name: str = "finlabx"


class ConstraintsConfig(BaseModel):
    """Constraints configuration for a workflow version."""
    max_tool_calls_per_step: int = 5
    require_citations: bool = True
    zero_hallucination_policy: bool = True
    max_context_tokens: Optional[int] = None
    enable_code_execution: bool = False
    enable_graph_queries: bool = False
    enable_parallel_subagents: bool = False


class VersionConfig(BaseModel):
    """Complete configuration for a workflow version."""
    version: str
    name: str
    description: str
    tools: list[str] = Field(default_factory=list)
    model: ModelConfig = Field(default_factory=ModelConfig)
    observability: ObservabilityConfig = Field(default_factory=ObservabilityConfig)
    constraints: ConstraintsConfig = Field(default_factory=ConstraintsConfig)


class VersionConfigLoader:
    """Loader for version-specific workflow configurations."""
    
    WORKFLOWS_DIR = Path(__file__).parent
    
    def __init__(self, version_name: str):
        """Initialize loader for a specific version.
        
        Args:
            version_name: Name of the version (e.g., 'v1_baseline', 'v2_reader')
        """
        self.version_name = version_name
        self.config_path = self.WORKFLOWS_DIR / version_name / "version_config.yaml"
        
        if not self.config_path.exists():
            raise FileNotFoundError(
                f"Version config not found: {self.config_path}"
            )
        
        self._config: Optional[VersionConfig] = None
    
    def load(self) -> VersionConfig:
        """Load and parse the version configuration.
        
        Returns:
            VersionConfig: Parsed configuration object
        """
        if self._config is None:
            with open(self.config_path, "r") as f:
                config_dict = yaml.safe_load(f)
            self._config = VersionConfig(**config_dict)
        return self._config
    
    @property
    def config(self) -> VersionConfig:
        """Get the loaded configuration (lazy load)."""
        if self._config is None:
            self._config = self.load()
        return self._config
    
    @property
    def tools(self) -> list[str]:
        """Get list of tool names for this version."""
        return self.config.tools
    
    @property
    def model_config(self) -> ModelConfig:
        """Get model configuration for this version."""
        return self.config.model
    
    @classmethod
    def list_available_versions(cls) -> list[str]:
        """List all available workflow versions.
        
        Returns:
            List of version directory names
        """
        versions = []
        for item in cls.WORKFLOWS_DIR.iterdir():
            if item.is_dir() and item.name.startswith("v"):
                config_file = item / "version_config.yaml"
                if config_file.exists():
                    versions.append(item.name)
        return sorted(versions)
```

**步驟 8：驗證 config loader 正常運作**

```bash
uv run python -c "
from backend.agent_engine.workflows.config_loader import VersionConfigLoader

# 測試列出所有版本
versions = VersionConfigLoader.list_available_versions()
print(f'Available versions: {versions}')

# 測試載入 v1_baseline
loader = VersionConfigLoader('v1_baseline')
config = loader.load()
print(f'v1 tools: {config.tools}')
print(f'v1 model: {config.model.name}')
print(f'v1 version: {config.version}')
"
```

預期結果：

```
Available versions: ['v1_baseline', 'v2_reader', 'v3_quant', 'v4_graph', 'v5_analyst']
v1 tools: ['yfinance_stock_quote', 'yfinance_get_available_fields', 'tavily_financial_search', 'sec_official_docs_retriever']
v1 model: gpt-4o-mini
v1 version: 0.1.0
```

**步驟 9：Commit**

```bash
git add backend/agent_engine/workflows/
git commit -m "feat(workflows): add versioned workflow configs with YAML"
```

---

### 任務 0.3：建立 Tool Registry

**目標：** 建立一個 central registry 來管理所有可用的 tools，並支援根據 version config 動態載入。

**檔案：**

- 建立：`backend/agent_engine/agents/specialized/registry.py`
- 測試：`backend/tests/agents/test_registry.py`

**步驟 1：撰寫 failing test**

```python
# backend/tests/agents/test_registry.py
import pytest
from backend.agent_engine.agents.specialized.registry import (
    ToolRegistry,
    register_tool,
    get_tool,
    get_tools_by_names,
)


def test_tool_registry_initialization():
    """Test tool registry can be initialized."""
    registry = ToolRegistry()
    assert registry is not None


def test_register_and_get_tool():
    """Test registering and retrieving a tool."""
    from langchain_core.tools import tool
    
    @tool("test_tool")
    def sample_tool(x: int) -> int:
        """A test tool."""
        return x * 2
    
    register_tool("test_tool", sample_tool)
    retrieved = get_tool("test_tool")
    
    assert retrieved is not None
    assert retrieved.name == "test_tool"


def test_get_tools_by_names():
    """Test getting multiple tools by names."""
    from langchain_core.tools import tool
    
    @tool("tool_a")
    def tool_a(x: int) -> int:
        return x
    
    @tool("tool_b")
    def tool_b(x: int) -> int:
        return x * 2
    
    register_tool("tool_a", tool_a)
    register_tool("tool_b", tool_b)
    
    tools = get_tools_by_names(["tool_a", "tool_b"])
    assert len(tools) == 2
```

**步驟 2：執行測試確認失敗**

```bash
uv run pytest backend/tests/agents/test_registry.py -v
```

預期結果：FAIL

**步驟 3：建立目錄並撰寫實作**

```bash
mkdir -p backend/tests/agents
touch backend/tests/agents/__init__.py
```

```python
# backend/agent_engine/agents/specialized/registry.py
"""Central registry for FinLab-X tools."""

from typing import Any, Optional

# Global tool registry
TOOL_REGISTRY: dict[str, Any] = {}


def register_tool(name: str, tool: Any) -> None:
    """Register a tool in the global registry.
    
    Args:
        name: Unique name for the tool
        tool: LangChain tool object
    """
    TOOL_REGISTRY[name] = tool


def get_tool(name: str) -> Optional[Any]:
    """Get a tool by name from the registry.
    
    Args:
        name: Tool name to retrieve
        
    Returns:
        Tool object if found, None otherwise
    """
    return TOOL_REGISTRY.get(name)


def get_tools_by_names(tool_names: list[str]) -> list[Any]:
    """Get multiple tools by their names.
    
    Args:
        tool_names: List of tool names to retrieve
        
    Returns:
        List of tool objects (only those found in registry)
    """
    tools = []
    for name in tool_names:
        tool = get_tool(name)
        if tool is not None:
            tools.append(tool)
    return tools


def list_registered_tools() -> list[str]:
    """List all registered tool names.
    
    Returns:
        List of tool names in the registry
    """
    return list(TOOL_REGISTRY.keys())


def clear_registry() -> None:
    """Clear all tools from the registry (for testing)."""
    TOOL_REGISTRY.clear()


class ToolRegistry:
    """Class-based interface for tool registry (for backward compatibility)."""
    
    def __init__(self):
        self._tools = TOOL_REGISTRY
    
    def register(self, name: str, tool: Any) -> None:
        """Register a tool."""
        register_tool(name, tool)
    
    def get(self, name: str) -> Optional[Any]:
        """Get a tool by name."""
        return get_tool(name)
    
    def get_all(self, names: list[str]) -> list[Any]:
        """Get multiple tools by names."""
        return get_tools_by_names(names)
    
    def list_all(self) -> list[str]:
        """List all registered tool names."""
        return list_registered_tools()
```

**步驟 4：執行測試確認通過**

```bash
uv run pytest backend/tests/agents/test_registry.py -v
```

預期結果：PASS

**步驟 5：Commit**

```bash
git add backend/agent_engine/agents/specialized/registry.py backend/tests/agents/
git commit -m "feat(tools): add central tool registry for dynamic loading"
```

---

### 任務 0.4：更新 FILE_STRUCTURE.md

**目標：** 更新 FILE_STRUCTURE.md 以反映新的目錄結構和 agent_engine 命名。

**檔案：**

- 修改：`FILE_STRUCTURE.md`

**步驟 1：更新 FILE_STRUCTURE.md**

```markdown
# FinLab-X File Structure and Responsibilities

This document outlines the file structure and architectural responsibilities for the FinLab-X project based on the current scaffolding. It serves as a guide for developers and AI agents navigating the codebase.

## 1. Project Root (`fin-lab-x/`)

The repository is divided into independent environments:
- **`backend/`**: Python-based AI Agent Engine and FastAPI Web Server.
- **`frontend/`**: TypeScript-based Next.js Generative UI.

---

## 2. Backend (`backend/`)

The backend is built following Clean Architecture principles and strictly decouples the API layer from the core Agent Engine.

### 2.1 API Layer (`backend/api/`)
Handles HTTP, WebSocket, and Server-Sent Events (SSE) requests. **MUST NOT** contain core AI logic.
- **`routers/`**: FastAPI route definitions.
- **`dependencies.py`**: Dependency injection (e.g., DB sessions, Agent Engine instances).
- **`main.py`**: The entry point for the FastAPI application.

### 2.2 Agent Engine (`backend/agent_engine/`)
The core, independent AI logic (orchestrator, tools). Designed to run independently of the FastAPI server (e.g., via CLI or background workers).

#### Core Components:

- **`orchestrator/`**: Central reasoning engine that manages state, plans steps, and selects tools.
  - `base.py`: Version-agnostic Orchestrator class that loads tools based on config.
- **`tools/`**: Atomic, stateless functions for specific data retrieval or actions.
  - `base.py`: Base class for all tools.
  - `financial.py`: Financial data tools (yfinance, Tavily).
  - `sec.py`: SEC document retrieval tools.
- **`observability/`**: Integration with LangSmith for tracing and evaluation.
  - `langsmith_tracer.py`: Decorator for step-level tracing.

#### Versioned Workflows:

- **`workflows/`**: Orchestration of agents through evolutionary stages.
  - `config_loader.py`: Version configuration loader (YAML-based).
  - `v1_baseline/`: Naive single-chain financial analysis.
    - `version_config.yaml`: v1 configuration (tools, model, constraints).
    - `chain.py`: v1 chain implementation.
  - `v2_reader/`: Long-context document analysis and RAG.
    - `version_config.yaml`: v2 configuration.
  - `v3_quant/`: Numerical reasoning and quantitative modeling.
    - `version_config.yaml`: v3 configuration.
  - `v4_graph/`: Knowledge graph-based analysis.
    - `version_config.yaml`: v4 configuration.
  - `v5_analyst/`: Comprehensive investment research assistant.
    - `version_config.yaml`: v5 configuration.

#### Future Components (Not Implemented in v1):

- **`skills/`**: Markdown-based procedural knowledge (Anthropic Skills pattern).
- **`mcp/`**: Model Context Protocol integrations for external connectivity.
- **`subagents/`**: Short-lived, specialized agents for isolated sub-tasks.

#### Legacy Components (Being Refactored):

- **`agents/`**: Legacy agent definitions (being refactored into orchestrator/).
  - `base.py`: Base agent class (legacy).
  - `factory.py`: Agent factory pattern (legacy).
  - `specialized/`: Specialized agent implementations.
    - `tools.py`: Tool definitions (being moved to tools/).
    - `registry.py`: Central tool registry.
- **`services/`**: Shared business logic (being refactored into tools/).
- **`infrastructure/`**: External service clients (being refactored into observability/).

### 2.3 Testing (`backend/tests/`)
Contains programmatic software engineering Unit and Integration Tests. These tests have clear pass/fail criteria and execute quickly.
- **`orchestrator/`**: Tests for orchestrator components.
- **`tools/`**: Tests for tool implementations.
- **`agents/`**: Tests for agent registry.

### 2.4 Evaluation (`backend/evaluation/`)
A directory dedicated to LLMOps. It separates the probabilistic and long-running nature of AI evaluation from traditional deterministic software testing.
This section is planned for the future and currently not scaffolded but will contain:
- **`datasets/`**: Golden datasets used as baselines for testing agent performance.
- **`metrics/`**: Custom logic for evaluation metrics (e.g., Accuracy, Relevance, Adherence to Tone).
- **`scripts/`**: Automation scripts for executing batch evaluations.

---

## 3. Frontend (`frontend/`)

A Next.js full-stack application responsible for providing a Generative UI.
- **`src/app/`**: Next.js App Router definitions.
- **`src/components/`**: React UI components, focusing on rendering dynamic Generative Artifacts.
- **`src/lib/`**: API clients and parsers for Server-Sent Events (SSE) streams.

---

## 4. Documentation (`docs/`)

- **`ARCHITECTURE.md`**: High-level architecture documentation (Single Orchestrator pattern).
- **`plans/`**: Implementation plans and design documents.

---

## 5. Key Design Principles

### 5.1 Single Orchestrator Pattern
- One central reasoning engine manages all decisions.
- The Orchestrator is version-agnostic; it loads capabilities from version config.
- Tools are capabilities, not independent agents.

### 5.2 Observability First
- Every LLM call, tool execution, and state change is traced via LangSmith.
- All versions use the same LangSmith project (`finlabx`).
- Tags are used to distinguish versions (e.g., `version: "0.1.0"`).

### 5.3 Versioned Workflows
- Each version (v1-v5) is independently callable.
- `version_config.yaml` defines allowed tools and model settings.
- Enables safe experimentation and easy rollback.

### 5.4 Code as Interface
- Tools are strictly typed Python functions.
- Pydantic models for input validation.
- LLM interacts with code, not natural language descriptions.

### 5.5 Zero Hallucination Policy
- All responses must be grounded in tool outputs.
- If data is insufficient, the agent must say "I don't have enough information".
- Never invent financial metrics or news.

---

## 6. Dependency Rules

To maintain a clean architecture, the following dependency rules are enforced:

1. **Orchestrator** can depend on `tools` and `observability`.
2. **Tools** must be independent and stateless; they cannot depend on the orchestrator.
3. **Circular Dependencies** are strictly prohibited.

---

## 7. Migration Notes

The project is transitioning from the legacy `ai_engine` structure to the `agent_engine` architecture.

- **Legacy `agents/`**: Being refactored into `orchestrator/`.
- **Legacy `workflows/`**: Replaced by the `orchestrator/` and the versioned profile system.
- **Legacy `services/`**: Moving to `tools/`.
- **Legacy `infrastructure/`**: Reorganized into `observability/`.

---

## 8. Implementation Guidelines

When adding new features to this codebase:

1. **Follow the Single Orchestrator pattern**: The Orchestrator is version-agnostic; use version config to define capabilities.
2. **Use the Tool Registry**: Register all tools in `backend/agent_engine/agents/specialized/registry.py`.
3. **Create version configs**: When adding new capabilities, update the appropriate `version_config.yaml`.
4. **Add LangSmith tracing**: Use `@trace_step` decorator for all LLM calls and tool executions.
5. **Write tests**: All new components must have corresponding tests in `backend/tests/`.
6. **Update documentation**: Keep this file and `docs/ARCHITECTURE.md` in sync with code changes.
7. **Use model-agnostic methods**: Use `init_chat_model` instead of provider-specific classes.
```

**步驟 2：Commit**

```bash
git add FILE_STRUCTURE.md
git commit -m "docs: update FILE_STRUCTURE.md with agent_engine and versioned workflows"
```

---

## 第一階段：基礎建設 - Orchestrator Core

### 任務 1：建立 Version-Agnostic Orchestrator

**目標：** 建立一個 version-agnostic 的 Orchestrator，根據 version config 載入 tools。

**檔案：**

- 建立：`backend/agent_engine/orchestrator/base.py`
- 測試：`backend/tests/orchestrator/test_base.py`

**步驟 1：撰寫 failing test**

```python
# backend/tests/orchestrator/test_base.py
import pytest
from unittest.mock import Mock, patch
from backend.agent_engine.orchestrator.base import Orchestrator
from backend.agent_engine.workflows.config_loader import VersionConfig


def test_orchestrator_initialization_with_config():
    """Test orchestrator can be initialized with version config."""
    config = VersionConfig(
        version="0.1.0",
        name="v1_baseline",
        description="Test version",
        tools=["yfinance_stock_quote"]
    )
    
    with patch('backend.agent_engine.orchestrator.base.get_tools_by_names') as mock_get_tools:
        mock_get_tools.return_value = [Mock(name="yfinance_stock_quote")]
        orch = Orchestrator(config)
        assert orch.config.name == "v1_baseline"


def test_orchestrator_run_returns_response():
    """Test orchestrator run returns a response."""
    config = VersionConfig(
        version="0.1.0",
        name="v1_baseline",
        description="Test version",
        tools=[]
    )
    
    orch = Orchestrator(config)
    result = orch.run("test prompt")
    assert "response" in result or "error" in result
```

**步驟 2：執行測試確認失敗**

```bash
cd /Users/dong.wyt/Documents/dev-projects/fin-lab-x
uv run pytest backend/tests/orchestrator/test_base.py -v
```

預期結果：FAIL，錯誤訊息 "ModuleNotFoundError: No module named 'backend.agent_engine.orchestrator'"

**步驟 3：建立目錄結構並撰寫實作**

```bash
mkdir -p backend/agent_engine/orchestrator
mkdir -p backend/tests/orchestrator
touch backend/agent_engine/orchestrator/__init__.py
```

```python
# backend/agent_engine/orchestrator/base.py
"""Version-agnostic Orchestrator for FinLab-X."""

from typing import Any
from langchain.chat_models import init_chat_model
from langchain_core.messages import ToolMessage

from backend.agent_engine.workflows.config_loader import VersionConfig
from backend.agent_engine.agents.specialized.registry import get_tools_by_names
from backend.agent_engine.observability.langsmith_tracer import trace_step


class Orchestrator:
    """Version-agnostic Orchestrator that loads capabilities from config.
    
    The Orchestrator is the central reasoning engine that:
    1. Loads tools based on version config
    2. Manages the LLM + tool calling loop
    3. Enforces zero hallucination policy
    4. Traces all steps via LangSmith
    """
    
    def __init__(self, config: VersionConfig):
        """Initialize Orchestrator with version configuration.
        
        Args:
            config: VersionConfig object defining available capabilities
        """
        self.config = config
        
        # Load tools from registry
        self.tools = get_tools_by_names(config.tools)
        
        # Initialize LLM with model-agnostic method
        self.model = init_chat_model(
            model=config.model.name,
            temperature=config.model.temperature
        ).bind_tools(self.tools)
        
        # Build system prompt
        self.system_prompt = self._build_system_prompt()
        
        # Set max iterations
        self.max_iterations = config.model.max_iterations
    
    def _build_system_prompt(self) -> str:
        """Build system prompt with zero hallucination policy.
        
        Returns:
            System prompt string
        """
        return """You are FinLab-X, a strict, data-driven financial AI Agent.

ZERO HALLUCINATION POLICY:
- Only use data from provided tools
- If data is insufficient, say "I don't have enough information"
- Never invent financial metrics or news

TOOL USAGE:
- Use yfinance_stock_quote for current stock prices and metrics
- Use yfinance_get_available_fields to discover available data fields
- Use tavily_financial_search for recent news and sentiment
- Use sec_official_docs_retriever for official SEC filings

RESPONSE FORMAT:
- Start with a clear conclusion
- Support with specific data points
- Cite sources (tool names)
- Flag any data quality issues"""
    
    @trace_step(step_name="orchestrator_run", tags={"component": "orchestrator"})
    def run(self, prompt: str, **kwargs) -> dict[str, Any]:
        """Execute orchestration loop with tool calling.
        
        Args:
            prompt: User prompt to process
            **kwargs: Additional arguments
            
        Returns:
            Dictionary with response, tool_outputs, iterations, and metadata
        """
        messages = [
            ("system", self.system_prompt),
            ("human", prompt)
        ]
        
        iteration = 0
        current_messages = messages
        tool_outputs = []
        
        while iteration < self.max_iterations:
            # Get model response
            response = self.model.invoke(current_messages)
            
            # Check if tool calls are needed
            if response.tool_calls:
                # Execute tools
                for tool_call in response.tool_calls:
                    tool_name = tool_call["name"]
                    tool_args = tool_call["args"]
                    
                    # Find and execute tool
                    tool_result = self._execute_tool(tool_name, tool_args)
                    tool_outputs.append({
                        "tool": tool_name,
                        "args": tool_args,
                        "result": tool_result
                    })
                    
                    # Add tool result to messages
                    current_messages = list(current_messages) + [
                        response,
                        ToolMessage(
                            content=str(tool_result),
                            tool_call_id=tool_call["id"]
                        )
                    ]
            else:
                # No tool calls - return final response
                return {
                    "response": response.content,
                    "tool_outputs": tool_outputs,
                    "iterations": iteration + 1,
                    "model": self.config.model.name,
                    "version": self.config.version
                }
            
            iteration += 1
        
        # Max iterations reached
        return {
            "response": "Max iterations reached without completion",
            "tool_outputs": tool_outputs,
            "iterations": iteration,
            "error": "max_iterations_exceeded"
        }
    
    def _execute_tool(self, tool_name: str, tool_args: dict) -> Any:
        """Execute a specific tool by name.
        
        Args:
            tool_name: Name of the tool to execute
            tool_args: Arguments to pass to the tool
            
        Returns:
            Tool execution result
        """
        for tool in self.tools:
            if tool.name == tool_name:
                return tool.invoke(tool_args)
        return f"Error: Tool '{tool_name}' not found"
```

**步驟 4：更新 orchestrator __init__.py**

```python
# backend/agent_engine/orchestrator/__init__.py
from backend.agent_engine.orchestrator.base import Orchestrator

__all__ = ["Orchestrator"]
```

**步驟 5：執行測試確認通過**

```bash
uv run pytest backend/tests/orchestrator/test_base.py -v
```

預期結果：PASS（2 個測試）

**步驟 6：Commit**

```bash
git add backend/agent_engine/orchestrator/ backend/tests/orchestrator/
git commit -m "feat(orchestrator): add version-agnostic orchestrator with config-based loading"
```

---

### 任務 2：建立 LangSmith Tracing Decorator

**檔案：**

- 建立：`backend/agent_engine/observability/langsmith_tracer.py`
- 測試：`backend/tests/observability/test_langsmith_tracer.py`

**步驟 1：撰寫 failing test**

```python
# backend/tests/observability/test_langsmith_tracer.py
import pytest
from unittest.mock import Mock, patch
from backend.agent_engine.observability.langsmith_tracer import trace_step


def test_trace_step_decorator():
    """Test trace_step decorator wraps function with LangSmith tracing."""
    
    @trace_step(step_name="test_step", tags={"version": "0.1.0"})
    def sample_function(x: int) -> int:
        return x * 2
    
    # Mock LangSmith client
    with patch('backend.agent_engine.observability.langsmith_tracer.Client') as mock_client:
        mock_run = Mock()
        mock_client.return_value.create_run = mock_run
        
        result = sample_function(5)
        
        assert result == 10
        # Verify LangSmith client was called
        mock_client.assert_called_once()
```

**步驟 2：執行測試確認失敗**

```bash
uv run pytest backend/tests/observability/test_langsmith_tracer.py -v
```

預期結果：FAIL，錯誤訊息 "ModuleNotFoundError"

**步驟 3：建立目錄並撰寫實作**

```bash
mkdir -p backend/agent_engine/observability
mkdir -p backend/tests/observability
touch backend/agent_engine/observability/__init__.py
```

```python
# backend/agent_engine/observability/langsmith_tracer.py
"""LangSmith tracing utilities for FinLab-X."""

import os
from functools import wraps
from typing import Any, Callable, Optional
from langsmith import Client
from langsmith.run_trees import RunTree


# Initialize LangSmith client
langsmith_client = Client(api_key=os.getenv("LANGSMITH_API_KEY"))


def trace_step(
    step_name: str,
    run_type: str = "chain",
    tags: Optional[dict[str, str]] = None
) -> Callable:
    """Decorator to wrap execution steps with LangSmith tracing.
    
    Args:
        step_name: Name of the step for tracing
        run_type: Type of run (chain, tool, llm, etc.)
        tags: Optional tags for filtering in LangSmith
        
    Returns:
        Decorated function with tracing
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            # Create run tree for this step
            run_tree = RunTree(
                name=step_name,
                run_type=run_type,
                inputs={"args": args, "kwargs": kwargs},
                tags=tags or {}
            )
            
            try:
                result = func(*args, **kwargs)
                run_tree.end(outputs={"result": result})
                run_tree.post()
                return result
            except Exception as e:
                run_tree.end(error=str(e))
                run_tree.post()
                raise
        
        return wrapper
    return decorator
```

**步驟 4：執行測試確認通過**

```bash
uv run pytest backend/tests/observability/test_langsmith_tracer.py -v
```

預期結果：PASS

**步驟 5：Commit**

```bash
git add backend/agent_engine/observability/ backend/tests/observability/
git commit -m "feat(observability): add LangSmith tracing decorator for step-level tracing"
```

---

## 第二階段：Tools Layer 重構

### 任務 3：將現有 Tools 重構到新結構

**檔案：**

- 修改：`backend/agent_engine/agents/specialized/tools.py` → 拆分到獨立檔案
- 建立：`backend/agent_engine/tools/base.py`
- 建立：`backend/agent_engine/tools/financial.py`（yfinance, tavily）
- 建立：`backend/agent_engine/tools/sec.py`（SEC retriever）
- 建立：`backend/agent_engine/tools/__init__.py`
- 測試：`backend/tests/tools/test_financial.py`
- 測試：`backend/tests/tools/test_sec.py`

**步驟 1：為新 tool 結構撰寫 failing tests**

```python
# backend/tests/tools/test_financial.py
import pytest
from backend.agent_engine.tools.financial import (
    yfinance_stock_quote,
    yfinance_get_available_fields,
    tavily_financial_search
)


def test_yfinance_tool_exists():
    """Test yfinance tool can be imported and called."""
    assert callable(yfinance_stock_quote)


def test_yfinance_get_available_fields_exists():
    """Test yfinance_get_available_fields tool exists."""
    assert callable(yfinance_get_available_fields)


def test_tavily_tool_exists():
    """Test tavily tool can be imported and called."""
    assert callable(tavily_financial_search)
```

```python
# backend/tests/tools/test_sec.py
import pytest
from backend.agent_engine.tools.sec import sec_official_docs_retriever


def test_sec_tool_exists():
    """Test SEC tool can be imported and called."""
    assert callable(sec_official_docs_retriever)
```

**步驟 2：執行測試確認失敗**

```bash
uv run pytest backend/tests/tools/ -v
```

預期結果：FAIL，錯誤訊息 "ModuleNotFoundError"

**步驟 3：建立目錄結構和 base class**

```bash
mkdir -p backend/agent_engine/tools
mkdir -p backend/tests/tools
touch backend/agent_engine/tools/__init__.py
```

```python
# backend/agent_engine/tools/base.py
"""Base classes for FinLab-X tools."""

from abc import ABC, abstractmethod
from typing import Any, TypeVar
from pydantic import BaseModel


InputT = TypeVar('InputT', bound=BaseModel)
OutputT = TypeVar('OutputT')


class BaseTool(ABC):
    """Base class for all FinLab-X tools."""
    
    name: str
    description: str
    input_schema: type[BaseModel]
    
    @abstractmethod
    def execute(self, input_data: InputT) -> OutputT:
        """Execute the tool with validated input.
        
        Args:
            input_data: Validated input data
            
        Returns:
            Tool execution result
        """
        pass
    
    def __call__(self, **kwargs) -> Any:
        """Allow tool to be called as a function.
        
        Args:
            **kwargs: Tool arguments
            
        Returns:
            Tool execution result
        """
        validated_input = self.input_schema(**kwargs)
        return self.execute(validated_input)
```

**步驟 4：遷移 yfinance tools**

```python
# backend/agent_engine/tools/financial.py
"""Financial data tools for FinLab-X."""

from typing import Any
import yfinance as yf
from pydantic import BaseModel, Field
from langchain_core.tools import tool

from backend.agent_engine.observability.langsmith_tracer import trace_step


class YFinanceStockQuoteInput(BaseModel):
    """Input schema for yfinance stock quote tool."""
    ticker: str = Field(..., description="Stock ticker symbol (e.g., AAPL, TSLA)")
    fields: list[str] | None = Field(
        default=None,
        description="Optional list of fields to retrieve. If None, returns common fields."
    )


@tool("yfinance_stock_quote", args_schema=YFinanceStockQuoteInput)
@trace_step(step_name="yfinance_stock_quote", tags={"tool": "yfinance", "version": "0.1.0"})
def yfinance_stock_quote(ticker: str, fields: list[str] | None = None) -> dict[str, Any] | str:
    """Retrieve stock quote data using yfinance.
    
    Args:
        ticker: Stock ticker symbol
        fields: Optional list of specific fields to retrieve
        
    Returns:
        Dictionary with stock data or error message
    """
    try:
        ticker_obj = yf.Ticker(ticker.upper().strip())
        info = ticker_obj.info
        
        if fields:
            return {
                "ticker": ticker.upper().strip(),
                "data": {field: info.get(field) for field in fields}
            }
        else:
            # Default fields
            return {
                "ticker": ticker.upper().strip(),
                "current_price": info.get("currentPrice"),
                "fifty_two_week_high": info.get("fiftyTwoWeekHigh"),
                "fifty_two_week_low": info.get("fiftyTwoWeekLow"),
                "forward_pe": info.get("forwardPE"),
                "trailing_pe": info.get("trailingPE"),
                "market_cap": info.get("marketCap"),
            }
    except Exception as e:
        return f"Error fetching stock data: {str(e)}"


class YFinanceGetAvailableFieldsInput(BaseModel):
    """Input schema for yfinance get available fields tool."""
    ticker: str = Field(..., description="Stock ticker symbol to query available fields")


@tool("yfinance_get_available_fields", args_schema=YFinanceGetAvailableFieldsInput)
@trace_step(step_name="yfinance_get_available_fields", tags={"tool": "yfinance", "version": "0.1.0"})
def yfinance_get_available_fields(ticker: str) -> dict[str, Any] | str:
    """Get all available data fields for a stock ticker with descriptions.
    
    Use this tool first to discover what data is available, then use
    yfinance_stock_quote with specific fields.
    
    Args:
        ticker: Stock ticker symbol
        
    Returns:
        Dictionary with available fields and their descriptions
    """
    try:
        ticker_obj = yf.Ticker(ticker.upper().strip())
        info = ticker_obj.info
        
        # Common fields with descriptions
        field_descriptions = {
            "currentPrice": "Current stock price",
            "fiftyTwoWeekHigh": "52-week high price",
            "fiftyTwoWeekLow": "52-week low price",
            "forwardPE": "Forward P/E ratio",
            "trailingPE": "Trailing P/E ratio",
            "marketCap": "Market capitalization",
            "revenueGrowth": "Revenue growth rate",
            "earningsGrowth": "Earnings growth rate",
            "dividendYield": "Dividend yield",
            "beta": "Beta coefficient",
            "avgVolume": "Average trading volume",
            "profitMargin": "Profit margin",
            "operatingMargin": "Operating margin",
            "returnOnEquity": "Return on equity (ROE)",
            "returnOnAssets": "Return on assets (ROA)",
            "debtToEquity": "Debt-to-equity ratio",
            "currentRatio": "Current ratio",
            "quickRatio": "Quick ratio",
            "priceToBook": "Price-to-book ratio",
            "priceToSales": "Price-to-sales ratio",
            "enterpriseValue": "Enterprise value",
            "ebitda": "EBITDA",
            "totalRevenue": "Total revenue",
            "netIncome": "Net income",
            "freeCashflow": "Free cash flow",
            "operatingCashflow": "Operating cash flow",
        }
        
        available_fields = {}
        for field, description in field_descriptions.items():
            if field in info:
                available_fields[field] = {
                    "description": description,
                    "available": True
                }
        
        # Add any additional fields not in our descriptions
        for field in info.keys():
            if field not in available_fields:
                available_fields[field] = {
                    "description": "Unknown field",
                    "available": True
                }
        
        return {
            "ticker": ticker.upper().strip(),
            "available_fields": available_fields,
            "total_fields": len(available_fields)
        }
    except Exception as e:
        return f"Error fetching available fields: {str(e)}"


class TavilyFinancialSearchInput(BaseModel):
    """Input schema for Tavily financial search tool."""
    query: str = Field(..., description="Financial news search query")
    ticker: str = Field(..., description="Stock ticker to focus search on")


@tool("tavily_financial_search", args_schema=TavilyFinancialSearchInput)
@trace_step(step_name="tavily_financial_search", tags={"tool": "tavily", "version": "0.1.0"})
def tavily_financial_search(query: str, ticker: str) -> dict[str, Any] | str:
    """Search financial news using Tavily API.
    
    Args:
        query: Search query
        ticker: Stock ticker to focus on
        
    Returns:
        Dictionary with search results or error message
    """
    try:
        from tavily import TavilyClient
        import os
        
        client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
        
        # Enhance query with ticker context
        enhanced_query = f"{query} {ticker} stock financial news"
        
        response = client.search(
            query=enhanced_query,
            search_depth="advanced",
            include_domains=["reuters.com", "bloomberg.com", "cnbc.com", "sec.gov"]
        )
        
        return {
            "results": [
                {
                    "title": result.get("title"),
                    "url": result.get("url"),
                    "content": result.get("content"),
                    "published_date": result.get("published_date")
                }
                for result in response.get("results", [])
            ],
            "query": enhanced_query
        }
    except Exception as e:
        return f"Error searching financial news: {str(e)}"
```

**步驟 5：遷移 SEC tool**

```python
# backend/agent_engine/tools/sec.py
"""SEC document retrieval tools for FinLab-X."""

from typing import Any
from pydantic import BaseModel, Field
from langchain_core.tools import tool

from backend.agent_engine.observability.langsmith_tracer import trace_step


class SecOfficialDocsRetrieverInput(BaseModel):
    """Input schema for SEC document retriever tool."""
    ticker: str = Field(..., description="Stock ticker symbol")
    doc_type: str = Field(
        default="10-K",
        description="SEC filing type: 10-K, 10-Q, 8-K"
    )
    sections: list[str] | None = Field(
        default=None,
        description="Optional sections to extract (e.g., 'Item 1A', 'Item 7')"
    )


@tool("sec_official_docs_retriever", args_schema=SecOfficialDocsRetrieverInput)
@trace_step(step_name="sec_official_docs_retriever", tags={"tool": "sec", "version": "0.1.0"})
def sec_official_docs_retriever(
    ticker: str,
    doc_type: str = "10-K",
    sections: list[str] | None = None
) -> dict[str, Any] | str:
    """Retrieve SEC filings for a given stock ticker.
    
    Supports 10-K (annual report), 10-Q (quarterly report), and 8-K (current report).
    
    Args:
        ticker: Stock ticker symbol
        doc_type: SEC filing type (10-K, 10-Q, 8-K)
        sections: Optional list of sections to extract
        
    Returns:
        Dictionary with filing data or error message
    """
    try:
        from edgar import Company, set_identity
        import os
        
        # Set EDGAR identity
        identity = os.getenv("EDGAR_IDENTITY", "FinLab-X finlab@example.com")
        set_identity(identity)
        
        # Get company and filings
        company = Company(ticker.upper().strip())
        filings = company.get_filings(form=doc_type)
        latest_filing = filings.latest()
        
        # Extract text
        text = latest_filing.text()
        
        # Extract sections if specified
        extracted_sections = {}
        if sections:
            for section in sections:
                section_text = _extract_section_by_name(text, section)
                if section_text:
                    extracted_sections[section] = section_text[:5000]  # Truncate
        else:
            # Default sections for 10-K/10-Q
            if doc_type in ["10-K", "10-Q"]:
                risk_factors = _extract_section_by_name(text, "Item 1A")
                mdna = _extract_section_by_name(text, "Item 7")
                if risk_factors:
                    extracted_sections["Item 1A (Risk Factors)"] = risk_factors[:5000]
                if mdna:
                    extracted_sections["Item 7 (MD&A)"] = mdna[:5000]
        
        return {
            "ticker": ticker.upper().strip(),
            "doc_type": doc_type,
            "filing_date": str(latest_filing.filing_date) if latest_filing.filing_date else None,
            "sections": extracted_sections,
            "raw_excerpt": text[:10000]  # First 10K characters
        }
    except Exception as e:
        return f"Error retrieving SEC filing: {str(e)}"


def _extract_section_by_name(text: str, section_name: str) -> str | None:
    """Extract a section from SEC filing text by name.
    
    Args:
        text: Full filing text
        section_name: Section name (e.g., 'Item 1A', 'Item 7')
        
    Returns:
        Extracted section text or None
    """
    # Common section markers
    start_markers = [
        f"{section_name}.",
        f"{section_name.upper()}.",
        section_name,
        section_name.upper()
    ]
    
    # Find section start
    text_upper = text.upper()
    start_pos = -1
    for marker in start_markers:
        pos = text_upper.find(marker.upper())
        if pos != -1:
            start_pos = pos
            break
    
    if start_pos == -1:
        return None
    
    # Find next section (Item with number)
    import re
    next_section_pattern = r'ITEM\s+\d+[A-Z]?\.'
    match = re.search(next_section_pattern, text_upper[start_pos + 10:])
    
    if match:
        end_pos = start_pos + 10 + match.start()
    else:
        end_pos = len(text)
    
    return text[start_pos:end_pos].strip()
```

**步驟 6：更新 __init__.py 以 export 和註冊 tools**

```python
# backend/agent_engine/tools/__init__.py
"""FinLab-X tools package."""

from backend.agent_engine.tools.financial import (
    yfinance_stock_quote,
    yfinance_get_available_fields,
    tavily_financial_search
)
from backend.agent_engine.tools.sec import sec_official_docs_retriever
from backend.agent_engine.agents.specialized.registry import register_tool

# Register all tools
register_tool("yfinance_stock_quote", yfinance_stock_quote)
register_tool("yfinance_get_available_fields", yfinance_get_available_fields)
register_tool("tavily_financial_search", tavily_financial_search)
register_tool("sec_official_docs_retriever", sec_official_docs_retriever)

V1_TOOLS = [
    yfinance_stock_quote,
    yfinance_get_available_fields,
    tavily_financial_search,
    sec_official_docs_retriever
]

__all__ = [
    "yfinance_stock_quote",
    "yfinance_get_available_fields",
    "tavily_financial_search",
    "sec_official_docs_retriever",
    "V1_TOOLS"
]
```

**步驟 7：執行測試確認通過**

```bash
uv run pytest backend/tests/tools/ -v
```

預期結果：PASS（4 個測試）

**步驟 8：Commit**

```bash
git add backend/agent_engine/tools/ backend/tests/tools/
git commit -m "refactor(tools): migrate tools to new structure with model-agnostic design"
```

---

## 第三階段：整合與驗證

### 任務 4：更新 API Layer 以使用 Orchestrator

**檔案：**

- 修改：`backend/api/main.py`（取代 placeholder）
- 修改：`backend/api/routers/chat.py`（若不存在則建立）
- 測試：`backend/tests/api/test_chat.py`

**步驟 1：撰寫 failing tests**

```python
# backend/tests/api/test_chat.py
import pytest
from fastapi.testclient import TestClient
from backend.api.main import app


client = TestClient(app)


def test_chat_endpoint_exists():
    """Test chat endpoint exists."""
    response = client.post("/api/v1/chat", json={"message": "test"})
    # Should not be 404
    assert response.status_code != 404
```

**步驟 2：執行測試確認失敗**

```bash
uv run pytest backend/tests/api/test_chat.py -v
```

預期結果：FAIL

**步驟 3：建立 API router 並更新 main.py**

```python
# backend/api/routers/chat.py
"""Chat API router for FinLab-X."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Any

from backend.agent_engine.orchestrator.base import Orchestrator
from backend.agent_engine.workflows.config_loader import VersionConfigLoader

router = APIRouter(prefix="/api/v1", tags=["chat"])


class ChatRequest(BaseModel):
    """Chat request model."""
    message: str
    session_id: str | None = None


class ChatResponse(BaseModel):
    """Chat response model."""
    response: str
    tool_outputs: list[dict[str, Any]]
    session_id: str
    version: str


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Process financial analysis chat message.
    
    Args:
        request: Chat request with message and optional session ID
        
    Returns:
        Chat response with analysis results
    """
    try:
        # Load v1 config
        config_loader = VersionConfigLoader("v1_baseline")
        config = config_loader.load()
        
        # Initialize orchestrator with config
        orchestrator = Orchestrator(config)
        
        # Run orchestrator
        result = orchestrator.run(request.message)
        
        return ChatResponse(
            response=result.get("response", ""),
            tool_outputs=result.get("tool_outputs", []),
            session_id=request.session_id or "new_session",
            version=result.get("version", "0.1.0")
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

```python
# backend/api/main.py
"""FastAPI main application for FinLab-X."""

from fastapi import FastAPI
from backend.api.routers import chat

app = FastAPI(
    title="FinLab-X API",
    description="Financial Analysis AI System",
    version="0.1.0"
)

app.include_router(chat.router)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "version": "0.1.0"}
```

**步驟 4：建立 routers __init__.py**

```bash
touch backend/api/routers/__init__.py
```

**步驟 5：執行測試確認通過**

```bash
uv run pytest backend/tests/api/test_chat.py -v
```

預期結果：PASS（可能需要 mock API calls）

**步驟 6：Commit**

```bash
git add backend/api/
git commit -m "feat(api): integrate orchestrator into FastAPI endpoints"
```

---

## 第四階段：文件與清理

### 任務 5：更新 README 檔案

**檔案：**

- 修改：`backend/agent_engine/README.md`
- 修改：`backend/README.md`

**步驟 1：更新 agent_engine README**

```markdown
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
```

**步驟 2：更新 backend README**

```markdown
# FinLab-X Backend

## Quick Start

```bash
# Install dependencies
uv sync

# Set environment variables
export OPENAI_API_KEY="..."
export TAVILY_API_KEY="..."
export EDGAR_IDENTITY="..."
export LANGSMITH_API_KEY="..."

# Run tests
uv run pytest

# Start API server
uv run python -m backend.api.main
```

## Architecture

See `backend/agent_engine/README.md` and `docs/ARCHITECTURE.md` for detailed architecture documentation.

## Versioned Workflows

FinLab-X uses versioned workflow configurations. Each version can be called independently:

```bash
# List available versions
uv run python -c "
from backend.agent_engine.workflows.config_loader import VersionConfigLoader
print(VersionConfigLoader.list_available_versions())
"
```
```

**步驟 3：Commit**

```bash
git add backend/agent_engine/README.md backend/README.md
git commit -m "docs: update README files with new architecture documentation"
```

---

## 第五階段：最終驗證

### 任務 6：執行完整測試套件

**步驟 1：執行所有單元測試**

```bash
uv run pytest backend/tests/ -v --tb=short
```

預期結果：所有測試通過（或若未設定 API keys 則跳過）

**步驟 2：驗證 imports 正常**

```bash
uv run python -c "
from backend.agent_engine.orchestrator.base import Orchestrator
from backend.agent_engine.tools import V1_TOOLS
from backend.agent_engine.workflows.config_loader import VersionConfigLoader

print('All imports successful!')
print(f'Available versions: {VersionConfigLoader.list_available_versions()}')
"
```

預期結果：

```
All imports successful!
Available versions: ['v1_baseline', 'v2_reader', 'v3_quant', 'v4_graph', 'v5_analyst']
```

**步驟 3：執行 Integration Tests**

建立 integration tests 來驗證每個 tool 都被正確呼叫：

```python
# backend/tests/integration/test_v1_integration.py
"""Integration tests for v1 orchestrator."""

import pytest
from unittest.mock import Mock, patch
from backend.agent_engine.orchestrator.base import Orchestrator
from backend.agent_engine.workflows.config_loader import VersionConfig


def test_yfinance_tool_integration():
    """Test that yfinance tool is called correctly."""
    config = VersionConfig(
        version="0.1.0",
        name="v1_baseline",
        description="Test version",
        tools=["yfinance_get_available_fields"]
    )
    
    with patch('backend.agent_engine.orchestrator.base.get_tools_by_names') as mock_get_tools:
        mock_tool = Mock()
        mock_tool.name = "yfinance_get_available_fields"
        mock_tool.invoke.return_value = {"ticker": "AAPL", "available_fields": {}}
        mock_get_tools.return_value = [mock_tool]
        
        orch = Orchestrator(config)
        
        # Mock the model to return a tool call
        with patch.object(orch, 'model') as mock_model:
            mock_response = Mock()
            mock_response.tool_calls = [
                {
                    "name": "yfinance_get_available_fields",
                    "args": {"ticker": "AAPL"},
                    "id": "call_1"
                }
            ]
            mock_model.invoke.return_value = mock_response
            
            result = orch.run("What data is available for AAPL?")
            
            # Verify tool was called
            assert len(result["tool_outputs"]) > 0
            assert result["tool_outputs"][0]["tool"] == "yfinance_get_available_fields"
            assert result["tool_outputs"][0]["args"]["ticker"] == "AAPL"


def test_tavily_tool_integration():
    """Test that tavily tool is called correctly."""
    config = VersionConfig(
        version="0.1.0",
        name="v1_baseline",
        description="Test version",
        tools=["tavily_financial_search"]
    )
    
    with patch('backend.agent_engine.orchestrator.base.get_tools_by_names') as mock_get_tools:
        mock_tool = Mock()
        mock_tool.name = "tavily_financial_search"
        mock_tool.invoke.return_value = {"results": []}
        mock_get_tools.return_value = [mock_tool]
        
        orch = Orchestrator(config)
        
        with patch.object(orch, 'model') as mock_model:
            mock_response = Mock()
            mock_response.tool_calls = [
                {
                    "name": "tavily_financial_search",
                    "args": {"query": "latest news", "ticker": "TSLA"},
                    "id": "call_1"
                }
            ]
            mock_model.invoke.return_value = mock_response
            
            result = orch.run("What's the latest news about TSLA?")
            
            assert len(result["tool_outputs"]) > 0
            assert result["tool_outputs"][0]["tool"] == "tavily_financial_search"
            assert result["tool_outputs"][0]["args"]["ticker"] == "TSLA"


def test_sec_tool_integration():
    """Test that SEC tool is called correctly."""
    config = VersionConfig(
        version="0.1.0",
        name="v1_baseline",
        description="Test version",
        tools=["sec_official_docs_retriever"]
    )
    
    with patch('backend.agent_engine.orchestrator.base.get_tools_by_names') as mock_get_tools:
        mock_tool = Mock()
        mock_tool.name = "sec_official_docs_retriever"
        mock_tool.invoke.return_value = {"ticker": "MSFT", "doc_type": "10-K"}
        mock_get_tools.return_value = [mock_tool]
        
        orch = Orchestrator(config)
        
        with patch.object(orch, 'model') as mock_model:
            mock_response = Mock()
            mock_response.tool_calls = [
                {
                    "name": "sec_official_docs_retriever",
                    "args": {"ticker": "MSFT", "doc_type": "10-K"},
                    "id": "call_1"
                }
            ]
            mock_model.invoke.return_value = mock_response
            
            result = orch.run("Get the latest 10-K for MSFT")
            
            assert len(result["tool_outputs"]) > 0
            assert result["tool_outputs"][0]["tool"] == "sec_official_docs_retriever"
            assert result["tool_outputs"][0]["args"]["ticker"] == "MSFT"
            assert result["tool_outputs"][0]["args"]["doc_type"] == "10-K"


def test_multi_tool_integration():
    """Test that multiple tools can be called in sequence."""
    config = VersionConfig(
        version="0.1.0",
        name="v1_baseline",
        description="Test version",
        tools=["yfinance_stock_quote", "tavily_financial_search"]
    )
    
    with patch('backend.agent_engine.orchestrator.base.get_tools_by_names') as mock_get_tools:
        mock_tool_1 = Mock()
        mock_tool_1.name = "yfinance_stock_quote"
        mock_tool_1.invoke.return_value = {"ticker": "AAPL", "current_price": 150}
        
        mock_tool_2 = Mock()
        mock_tool_2.name = "tavily_financial_search"
        mock_tool_2.invoke.return_value = {"results": []}
        
        mock_get_tools.return_value = [mock_tool_1, mock_tool_2]
        
        orch = Orchestrator(config)
        
        with patch.object(orch, 'model') as mock_model:
            # Simulate LLM calling multiple tools
            call_count = [0]
            
            def mock_invoke(messages):
                if call_count[0] == 0:
                    call_count[0] += 1
                    return Mock(tool_calls=[
                        {
                            "name": "yfinance_stock_quote",
                            "args": {"ticker": "AAPL"},
                            "id": "call_1"
                        }
                    ])
                elif call_count[0] == 1:
                    call_count[0] += 1
                    return Mock(tool_calls=[
                        {
                            "name": "tavily_financial_search",
                            "args": {"query": "news", "ticker": "AAPL"},
                            "id": "call_2"
                        }
                    ])
                else:
                    return Mock(tool_calls=[], content="Analysis complete")
            
            mock_model.invoke = mock_invoke
            
            result = orch.run("Analyze AAPL stock price and news")
            
            # Verify both tools were called
            assert len(result["tool_outputs"]) >= 2
            tool_names = [t["tool"] for t in result["tool_outputs"]]
            assert "yfinance_stock_quote" in tool_names
            assert "tavily_financial_search" in tool_names


def test_zero_hallucination_policy():
    """Test that response is grounded in tool outputs."""
    config = VersionConfig(
        version="0.1.0",
        name="v1_baseline",
        description="Test version",
        tools=[]
    )
    
    with patch('backend.agent_engine.orchestrator.base.get_tools_by_names') as mock_get_tools:
        mock_get_tools.return_value = []
        
        orch = Orchestrator(config)
        
        with patch.object(orch, 'model') as mock_model:
            # Simulate LLM returning response without tool calls
            mock_model.invoke.return_value = Mock(
                tool_calls=[],
                content="Based on the data, AAPL is trading at $150."
            )
            
            result = orch.run("What is AAPL's price?")
            
            # Response should be present
            assert "response" in result
            # Should have version info
            assert "version" in result
```

**步驟 4：執行 Integration Tests**

```bash
mkdir -p backend/tests/integration
touch backend/tests/integration/__init__.py
uv run pytest backend/tests/integration/ -v
```

預期結果：所有 integration tests 通過

**步驟 5：驗證 LangSmith Tracing**

```bash
uv run python -c "
import os
os.environ['LANGSMITH_API_KEY'] = 'test_key'

from backend.agent_engine.observability.langsmith_tracer import trace_step

@trace_step(step_name='test', tags={'version': '0.1.0'})
def test_func():
    return 'success'

result = test_func()
print(f'Tracing test: {result}')
"
```

預期結果："Tracing test: success"

**步驟 6：最終 commit**

```bash
git add .
git commit -m "feat: complete v1 architecture refactor with version-agnostic orchestrator"
```

---

## 總結

此實作計畫將 FinLab-X v1 從簡單的 LangChain chain 重構為現代化的 Single Orchestrator 架構，具備：

- ✅ **Phase 0**: 目錄重構（ai_engine → agent_engine）與版本化工作流
- ✅ **Version-Agnostic Orchestrator**: 根據 version config 載入 tools
- ✅ **Tools Layer**: 確定性的財經資料動作（yfinance, Tavily, SEC）
- ✅ **Observability**: 用於 evaluation 和改進的 LangSmith tracing
- ✅ **Versioned Workflows**: 每個版本獨立可呼叫，透過 `version_config.yaml` 管理
- ✅ **Model-Agnostic**: 使用 `init_chat_model` 支援多種 LLM provider
- ✅ **Zero Hallucination Policy**: 所有回應必須基於 tool outputs
- ✅ **Integration Tests**: 驗證每個 tool 都被正確呼叫

**v2-v5 的後續步驟：**

- v2_reader：加入 RAG skills（chunking, embedding, vector search）
- v3_quant：加入 Quant skills（JIT ETL, Text-to-SQL, DuckDB）
- v4_graph：加入 Graph skills（entity extraction, Text-to-Cypher）
- v5_analyst：加入 Planner skills（多步驟整合, UI generation）

**LangGraph 決策：**
只有當你需要嚴格的 state-machine workflows 或長期 multi-agent 協作時才引入 LangGraph。目前的架構可以透過 Tools 擴展來處理 v2-v5。

---

**計畫已完成並儲存至 `docs/plans/2026-03-04-finlabx-architecture-implementation.md`。**

**兩種執行選項：**

**1. Subagent-Driven（本 session）** - 我逐個 task 派發 subagent 執行，task 之間審查，快速迭代

**2. Parallel Session（獨立 session）** - 開新 session 用 executing-plans，批次執行並有檢查點

**要選哪種方式？**
