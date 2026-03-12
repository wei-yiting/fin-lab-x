## Scope
Version-agnostic Orchestrator and configuration loading. This module provides the central reasoning engine that loads capabilities and constraints from versioned configuration files.

## Map
- `base.py`: Defines the `Orchestrator` class, which uses LangChain to manage the ReAct tool-calling loop and extract results.
- `config_loader.py`: Implements `VersionConfigLoader` and `VersionConfig` Pydantic models for loading `orchestrator_config.yaml` and `system_prompt.md` from version directories.
- `versions/`: Subdirectory containing versioned workflow configurations (v1-v5).

## Design Pattern
- **Strategy Pattern**: The `Orchestrator` behavior is determined by the `VersionConfig` passed at initialization, allowing different analysis strategies (baseline, reader, quant, etc.) without changing the core logic.
- **Singleton Pattern**: The `Orchestrator` is typically managed as a singleton within the application lifecycle to maintain consistent state and resource usage.

## Extension Algorithm
1. **Modify Orchestrator Logic**: Update the `Orchestrator` class in `base.py` to change how agents are initialized or how results are extracted.
2. **Add Configuration Fields**: Update the `VersionConfig`, `ModelConfig`, or `ConstraintsConfig` classes in `config_loader.py` to support new configuration parameters.
3. **Update System Prompts**: Modify the `_DEFAULT_SYSTEM_PROMPT` in `base.py` for global changes, or update individual `system_prompt.md` files in the `versions/` directory.
