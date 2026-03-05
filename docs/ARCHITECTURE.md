# FinLab-X Architecture Documentation

This document outlines the architectural principles, module structure, and workflow mechanisms of the FinLab-X AI Agent Engine.

## 1. Architecture Overview

FinLab-X utilizes a **Single Orchestrator** pattern. Instead of complex multi-agent routing that can lead to non-deterministic behavior and high latency, a central orchestrator manages the execution flow. This orchestrator leverages specialized components to perform tasks:

*   **Orchestrator**: The central reasoning engine (typically a high-capability LLM) that manages state, plans steps, and selects tools.
*   **Tools**: Atomic, stateless functions for specific data retrieval or actions.
*   **Skills**: Higher-level, encapsulated capabilities that combine multiple tools or complex logic.
*   **MCP (Model Context Protocol)**: Standardized interfaces for interacting with external data sources and services.
*   **Subagents**: Short-lived, specialized agents spawned by the orchestrator for isolated sub-tasks (e.g., deep research or code generation).

## 2. Module Structure

The core AI runtime resides in `backend/agent_engine/`. The directory is organized as follows:

*   `orchestrator/`: Contains the core logic for the central brain, including state management and transition logic.
*   `tools/`: A library of atomic functions (e.g., `get_stock_price`, `search_sec_filings`).
*   `skills/`: Complex, reusable capabilities (e.g., `perform_discounted_cash_flow_analysis`).
*   `mcp/`: Integrations for the Model Context Protocol to connect with external ecosystems.
*   `subagents/`: Definitions for specialized agents that the orchestrator can delegate to.
*   `observability/`: Integration with LangSmith and internal logging for tracing and evaluation.

## 3. Versioned Workflow Profiles

FinLab-X uses **Workflow Profiles** to manage the evolution of agent capabilities. Each profile is a self-contained configuration that defines how the agent behaves.

### Profile Mechanism
Profiles allow for rapid experimentation and safe rollbacks. By switching a profile ID, the system loads a different set of prompts, tool configurations, and model parameters.

### Versions
1.  **v1_baseline**: Standard RAG (Retrieval-Augmented Generation) with basic financial tool access.
2.  **v2_reader**: Optimized for long-context document analysis and multi-document synthesis.
3.  **v3_quant**: Specialized in numerical reasoning, data visualization, and quantitative modeling.
4.  **v4_graph**: Leverages knowledge graphs to understand complex corporate relationships and supply chains.
5.  **v5_analyst**: The flagship profile, combining all previous capabilities into a comprehensive investment research assistant.

### Profile Directory Structure
Each profile in `backend/agent_engine/profiles/` contains:
*   `version_config.yaml`: Model selection (e.g., GPT-4o, Claude 3.5 Sonnet), temperature, and tool-specific limits.
*   `system_prompt.md`: The core identity and behavioral instructions for the agent.
*   `README.md`: Documentation of the profile's specific use cases, strengths, and known limitations.

## 4. Design Principles

*   **Single Orchestrator**: Centralize decision-making to maintain control and reduce "agentic loop" overhead.
*   **Progressive Disclosure**: Only expose tools and skills to the orchestrator when they are relevant to the current task to minimize prompt noise and token usage.
*   **Observability First**: Every LLM call, tool execution, and state change must be traceable via LangSmith. If it isn't logged, it didn't happen.
*   **Code as Interface**: Tools and skills are defined as strictly typed Python functions. This makes them the "API" that the LLM interacts with.

## 5. Dependency Rules

To maintain a clean architecture, the following dependency rules are enforced:

1.  **Orchestrator** can depend on `tools`, `skills`, `mcp`, `subagents`, and `observability`.
2.  **Subagents** can depend on `tools` and `mcp`.
3.  **Skills** can depend on `tools` and `mcp`.
4.  **Tools** and **MCP** must be independent and stateless; they cannot depend on the orchestrator or skills.
5.  **Circular Dependencies** are strictly prohibited.

## 6. Migration Notes

The project is transitioning from the legacy `ai_engine` structure to the `agent_engine` architecture.

*   **Legacy `agents/`**: Being refactored into `subagents/` or integrated into the `orchestrator/` logic.
*   **Legacy `workflows/`**: Replaced by the `orchestrator/` and the versioned profile system.
*   **Legacy `services/`**: Moving to `tools/` (for atomic actions) or `skills/` (for complex logic).
*   **Legacy `infrastructure/`**: Reorganized into `observability/` and `mcp/`.

---

### Recommendations for Implementation:
1.  **Directory Creation**: Create the `backend/agent_engine/` structure before moving files to avoid broken imports.
2.  **Type Safety**: Ensure all new tools in `agent_engine/tools/` use Pydantic for input validation, as this significantly improves LLM tool-calling reliability.
3.  **Profile Validation**: Implement a script to validate that every profile contains the required `version_config.yaml` and `system_prompt.md` files.
