## Scope
Workflow Profiles — the config directories the runtime loads. Each capability tier (`baseline` → `reader` → `quant` → `graph` → `analyst`) is realized as one Workflow Profile, storing the declarative definition for that agent's reasoning strategy and toolset. Only `baseline` is implemented; the rest are placeholders.

## Map
- `baseline/`: Standard RAG financial analysis profile.
- `reader/`: Profile optimized for long-context document synthesis and extraction.
- `quant/`: Profile focused on numerical reasoning and quantitative modeling.
- `graph/`: Profile utilizing knowledge graph-based analysis.
- `analyst/`: Comprehensive investment research assistant profile.
- **Key Files per Profile**:
    - `orchestrator_config.yaml`: Defines the semantic version string, tool list, `model:` block (see `ModelConfig` Fields below), and runtime constraints.
    - `system_prompt.md`: Contains the specific system instructions and persona for the profile.

## `ModelConfig` Fields

Each profile's `model:` block accepts the following fields. The provider kwargs matrix is enforced in `_init_model()` — see `backend/agent_engine/agents/README.md` for the full per-provider requirement list.

| Field             | Type                               | Purpose                                                                                                                                    |
| ----------------- | ---------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------ |
| `name`            | `provider:model` string            | e.g. `openai:gpt-5-mini`, `google_genai:gemini-3.1-flash-lite`, `anthropic:claude-haiku-4-5`. Bare names (no `:` prefix) default to OpenAI. |
| `temperature`     | float                              | Sampling temperature. Provider-specific constraints apply when reasoning is on — see the matrix.                                            |
| `reasoning`       | `"on"` / `"off"` / `"unsupported"` | Admin-declared reasoning capability; defaults to `"off"`. Which state is valid for which model — including the OpenAI classic-model caveat — is in the matrix. |
| `thinking_budget` | int / null                         | Reasoning token budget for providers that take one (Anthropic / Gemini); per-provider bounds are in the matrix.                             |

### Provider examples

```yaml
# OpenAI gpt-5-mini (reasoning on) — thinking_budget unused
model:
  name: "openai:gpt-5-mini"
  temperature: 0.0
  reasoning: "on"
  thinking_budget: null

# Gemini 3.1 Flash-Lite (reasoning on)
model:
  name: "google_genai:gemini-3.1-flash-lite"
  temperature: 0.0
  reasoning: "on"
  thinking_budget: 8192

# Anthropic Claude Haiku 4.5 (reasoning on — note the hard constraints in the matrix)
model:
  name: "anthropic:claude-haiku-4-5"
  temperature: 1.0
  reasoning: "on"
  thinking_budget: 4096
```

## Design Pattern
- **Template Pattern**: Each profile directory serves as a configuration template. The `ProfileConfigLoader` uses these templates to instantiate a `WorkflowProfileConfig` object, ensuring a consistent structure across profiles while allowing for specialized behavior.

## Extension Algorithm
1. **Create Profile Directory**: Create a new subdirectory named after the capability tier it implements (e.g., filling in the placeholder `graph/`).
2. **Define Configuration**: Create an `orchestrator_config.yaml` file within the new directory. Specify the `version`, `name`, `description`, list of `tools` from the registry, and the `model:` block (pick `reasoning` and `thinking_budget` based on the chosen provider's contract — see `ModelConfig` Fields above).
3. **Write System Prompt**: Create a `system_prompt.md` file to define the agent's specific instructions, constraints, and output format.
4. **Validation**: Ensure the new profile appears in the output of `ProfileConfigLoader.list_available_profiles()` and can be successfully loaded by the `Orchestrator`. If reasoning is bound but the trace shows empty `metadata.reasoning`, re-check the provider matrix in `agents/README.md` — the reasoning-visibility kwargs it lists are set by `_init_model` only when `reasoning="on"`.
