"""Workflow profile configuration loader for FinLab-X."""

from pathlib import Path
from typing import Literal, Optional

import yaml
from pydantic import BaseModel, ConfigDict, Field


class ModelConfig(BaseModel):
    """Model configuration for a workflow profile.

    ``name`` is a LangChain-style ``provider:model`` identifier; bare names
    (no ``:``) default to OpenAI. ``reasoning`` is the admin-declared
    reasoning capability: ``"on"`` / ``"off"`` / ``"unsupported"`` (the
    latter = never pass any reasoning-control kwarg to the bound model).
    The per-provider kwarg mapping, hard constraints (Anthropic budget and
    temperature rules, Gemini budget bounds), and empirically verified API
    caveats (including which models each state is valid for) are documented
    once, in ``backend/agent_engine/agents/README.md`` under
    "Multi-Provider Reasoning Configuration" — not repeated here.
    """

    model_config = ConfigDict(extra="forbid")

    name: str = "openai:gpt-5-nano"
    temperature: float = 0.0
    reasoning: Literal["on", "off", "unsupported"] = "off"
    thinking_budget: int | None = None

    # ``name`` is parsed exactly once, here. Every consumer (_init_model's
    # provider branching and routing, context-window lookup, the registry
    # refresh script) reads these two properties instead of re-splitting the
    # string — a second parser (including LangChain's own, which only strips
    # the prefix when model_provider is NOT explicitly given) is how routing
    # bugs happened before.
    @property
    def provider(self) -> str:
        """Provider segment of ``name``; bare names default to ``"openai"``."""
        return self.name.split(":", 1)[0] if ":" in self.name else "openai"

    @property
    def bare_name(self) -> str:
        """``name`` without its ``provider:`` prefix — the model id the
        provider API actually accepts."""
        return self.name.split(":", 1)[1] if ":" in self.name else self.name


class ConstraintsConfig(BaseModel):
    """Constraints configuration for a workflow profile."""

    model_config = ConfigDict(extra="forbid")

    max_tool_calls_per_run: int = 5


class WorkflowProfileConfig(BaseModel):
    """Complete configuration for a workflow profile.

    Fields:
        version: Semantic version string (e.g., "0.1.0")
        name: Profile identifier (e.g., "baseline")
        description: Human-readable description of this profile's capabilities
        tools: List of tool names to load from the tool registry
        model: LLM model configuration
        constraints: Runtime constraints. Currently enforced:
            - max_tool_calls_per_run (via ToolCallLimitMiddleware)
        system_prompt: System prompt text, loaded from system_prompt.md
            in the profile directory by ProfileConfigLoader
    """

    model_config = ConfigDict(extra="forbid")

    version: str
    name: str
    description: str
    tools: list[str] = Field(default_factory=list)
    model: ModelConfig = Field(default_factory=ModelConfig)
    constraints: ConstraintsConfig = Field(default_factory=ConstraintsConfig)
    system_prompt: Optional[str] = None


class ProfileConfigLoader:
    """Loader for a single workflow profile's configuration."""

    PROFILES_DIR = Path(__file__).parent / "profiles"

    def __init__(self, profile_name: str):
        """Initialize loader for a specific profile.

        Args:
            profile_name: Name of the profile (e.g., 'baseline', 'reader')
        """
        self.profile_name = profile_name
        self.config_path = self.PROFILES_DIR / profile_name / "orchestrator_config.yaml"

        if not self.config_path.exists():
            raise FileNotFoundError(f"Profile config not found: {self.config_path}")

        self._config: Optional[WorkflowProfileConfig] = None

    def load(self) -> WorkflowProfileConfig:
        """Load and parse the profile configuration.

        Loads orchestrator_config.yaml and, if present, system_prompt.md
        from the profile directory.

        Returns:
            WorkflowProfileConfig: Parsed configuration object
        """
        if self._config is None:
            with open(self.config_path, "r") as f:
                config_dict = yaml.safe_load(f)

            prompt_path = self.config_path.parent / "system_prompt.md"
            if prompt_path.exists():
                config_dict["system_prompt"] = prompt_path.read_text().strip()

            self._config = WorkflowProfileConfig(**config_dict)
        return self._config

    @property
    def config(self) -> WorkflowProfileConfig:
        """Get the loaded configuration (lazy load)."""
        if self._config is None:
            self._config = self.load()
        return self._config

    @property
    def tools(self) -> list[str]:
        """Get list of tool names for this profile."""
        return self.config.tools

    @classmethod
    def list_available_profiles(cls) -> list[str]:
        """List all available workflow profiles.

        Returns:
            List of profile directory names
        """
        profiles = []
        for item in cls.PROFILES_DIR.iterdir():
            if item.is_dir():
                config_file = item / "orchestrator_config.yaml"
                if config_file.exists():
                    profiles.append(item.name)
        return sorted(profiles)
