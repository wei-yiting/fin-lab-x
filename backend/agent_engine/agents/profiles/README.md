## Scope
Workflow Profiles — the config directories the runtime loads. Each capability tier (`baseline` → `reader` → `quant` → `graph` → `analyst`) is realized as one Workflow Profile, storing the declarative definition for that agent's reasoning strategy and toolset. Only `baseline` is implemented; the rest are placeholders.

## Map
- `baseline/`: Standard RAG financial analysis profile.
- `reader/`: Profile optimized for long-context document synthesis and extraction.
- `quant/`: Profile focused on numerical reasoning and quantitative modeling.
- `graph/`: Profile utilizing knowledge graph-based analysis.
- `analyst/`: Comprehensive investment research assistant profile.
- **Key Files per Profile**:
    - `orchestrator_config.yaml`: Defines the semantic version string, tool list, model parameters, and runtime constraints.
    - `system_prompt.md`: Contains the specific system instructions and persona for the profile.

## Design Pattern
- **Template Pattern**: Each profile directory serves as a configuration template. The `ProfileConfigLoader` uses these templates to instantiate a `WorkflowProfileConfig` object, ensuring a consistent structure across profiles while allowing for specialized behavior.

## Extension Algorithm
1. **Create Profile Directory**: Create a new subdirectory named after the capability tier it implements (e.g., filling in the placeholder `graph/`).
2. **Define Configuration**: Create an `orchestrator_config.yaml` file within the new directory. Specify the `version`, `name`, `description`, and the list of `tools` from the registry.
3. **Write System Prompt**: Create a `system_prompt.md` file to define the agent's specific instructions, constraints, and output format.
4. **Validation**: Ensure the new profile appears in the output of `ProfileConfigLoader.list_available_profiles()` and can be successfully loaded by the `Orchestrator`.
