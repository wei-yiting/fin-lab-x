## Scope
Versioned workflow configurations (v1-v5). This directory stores the declarative definitions for different agent analysis profiles, allowing the system to switch between different reasoning strategies and toolsets.

## Map
- `v1_baseline/`: Standard RAG financial analysis profile.
- `v2_reader/`: Profile optimized for long-context document synthesis and extraction.
- `v3_quant/`: Profile focused on numerical reasoning and quantitative modeling.
- `v4_graph/`: Profile utilizing knowledge graph-based analysis.
- `v5_analyst/`: Comprehensive investment research assistant profile.
- **Key Files per Version**:
    - `orchestrator_config.yaml`: Defines the version string, tool list, model parameters, and runtime constraints.
    - `system_prompt.md`: Contains the specific system instructions and persona for the agent version.

## Design Pattern
- **Template Pattern**: Each version directory serves as a configuration template. The `VersionConfigLoader` uses these templates to instantiate a `VersionConfig` object, ensuring a consistent structure across different agent profiles while allowing for specialized behavior.

## Extension Algorithm
1. **Create Version Directory**: Create a new subdirectory following the `vN_name` convention (e.g., `v6_new_feature`).
2. **Define Configuration**: Create an `orchestrator_config.yaml` file within the new directory. Specify the `version`, `name`, `description`, and the list of `tools` from the registry.
3. **Write System Prompt**: Create a `system_prompt.md` file to define the agent's specific instructions, constraints, and output format.
4. **Validation**: Ensure the new version appears in the output of `VersionConfigLoader.list_available_versions()` and can be successfully loaded by the `Orchestrator`.
