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
    ``reasoning_effort`` is an optional strength override, only meaningful
    when ``reasoning="on"``: OpenAI's ``reasoning.effort`` (e.g. ``"none"``,
    ``"medium"``) or Gemini's ``thinking_level`` (e.g. ``"minimal"``,
    ``"medium"``) — left untyped because the valid value set differs per
    provider and model generation; ``_init_model`` maps it to the right
    provider kwarg and rejects it outright for providers with no
    effort-tier concept (Anthropic). Omitting it keeps each provider's
    existing hardcoded default effort.
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
    reasoning_effort: str | None = None

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
        system_prompt: System prompt text. The profile-name constructor
            loads it from a sibling system_prompt.md; load_from_dir()
            injects it explicitly via its prompt_path argument instead
            (used by benchmark/experiment configs that share one prompt
            across several config directories).
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
            prompt_path = self.config_path.parent / "system_prompt.md"
            self._config = self._parse_config(
                self.config_path, prompt_path if prompt_path.exists() else None
            )
        return self._config

    @staticmethod
    def _parse_config(
        config_path: Path, prompt_path: Optional[Path]
    ) -> WorkflowProfileConfig:
        """Read a profile YAML and construct its ``WorkflowProfileConfig``.

        Shared by ``load()`` and ``load_from_dir()``: opens ``config_path``,
        injects ``prompt_path``'s text as ``system_prompt`` when given, and
        validates the result. Callers own *whether* a given ``prompt_path``
        should exist — ``load()`` pre-filters to ``None`` when its
        auto-discovered sibling ``system_prompt.md`` is absent (silent
        skip); ``load_from_dir()`` passes its argument through unchanged (a
        given path is expected to exist and fails loudly via
        ``read_text()`` if it doesn't).
        """
        with open(config_path, "r") as f:
            config_dict = yaml.safe_load(f)

        if prompt_path is not None:
            config_dict["system_prompt"] = prompt_path.read_text().strip()

        return WorkflowProfileConfig(**config_dict)

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
    def load_from_dir(
        cls, config_dir: Path, *, prompt_path: Optional[Path] = None
    ) -> WorkflowProfileConfig:
        """Load a ``WorkflowProfileConfig`` from an arbitrary directory.

        For benchmark/experiment configs that must NOT live under
        ``profiles/`` — that directory is reserved for the product's
        standing Workflow Profiles (validated, deployed defaults), while a
        benchmark config is a one-off experiment variable. Reusing the same
        YAML schema (and this loader) for both gets schema validation for
        free without blurring that boundary: a benchmark config directory
        still parses into a ``WorkflowProfileConfig``, it just doesn't get
        to call itself a profile.

        Unlike the profile-name constructor + ``load()``, this does NOT look
        for a sibling ``system_prompt.md`` — a benchmark config directory is
        expected to hold no prompt file at all, so that N configs sharing
        one prompt can never drift into N slightly-different copies. Pass
        ``prompt_path`` to inject the single canonical prompt explicitly;
        omit it to load with no ``system_prompt`` override.
        """
        config_path = config_dir / "orchestrator_config.yaml"
        if not config_path.exists():
            raise FileNotFoundError(f"Config not found: {config_path}")

        return cls._parse_config(config_path, prompt_path)

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
