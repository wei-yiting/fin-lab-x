"""Version configuration loader for FinLab-X workflows."""

from pathlib import Path
from typing import Optional

import yaml
from pydantic import BaseModel, ConfigDict, Field


class ModelConfig(BaseModel):
    """Model configuration for a workflow version."""

    model_config = ConfigDict(extra="forbid")

    name: str = "gpt-4o-mini"
    temperature: float = 0.0


class ConstraintsConfig(BaseModel):
    """Constraints configuration for a workflow version."""

    model_config = ConfigDict(extra="forbid")

    max_tool_calls_per_run: int = 5


class VersionConfig(BaseModel):
    """Complete configuration for a workflow version.

    Fields:
        version: Semantic version string (e.g., "0.1.0")
        name: Version identifier (e.g., "v1_baseline")
        description: Human-readable description of this version's capabilities
        tools: List of tool names to load from the tool registry
        model: LLM model configuration
        constraints: Runtime constraints. Currently enforced:
            - max_tool_calls_per_run (via ToolCallLimitMiddleware)
        system_prompt: System prompt text, loaded from system_prompt.md
            in the version directory by VersionConfigLoader
    """

    model_config = ConfigDict(extra="forbid")

    version: str
    name: str
    description: str
    tools: list[str] = Field(default_factory=list)
    model: ModelConfig = Field(default_factory=ModelConfig)
    constraints: ConstraintsConfig = Field(default_factory=ConstraintsConfig)
    system_prompt: Optional[str] = None


class VersionConfigLoader:
    """Loader for version-specific workflow configurations."""

    VERSIONS_DIR = Path(__file__).parent / "versions"

    def __init__(self, version_name: str):
        """Initialize loader for a specific version.

        Args:
            version_name: Name of the version (e.g., 'v1_baseline', 'v2_reader')
        """
        self.version_name = version_name
        self.config_path = self.VERSIONS_DIR / version_name / "orchestrator_config.yaml"

        if not self.config_path.exists():
            raise FileNotFoundError(f"Version config not found: {self.config_path}")

        self._config: Optional[VersionConfig] = None

    def load(self) -> VersionConfig:
        """Load and parse the version configuration.

        Loads orchestrator_config.yaml and, if present, system_prompt.md
        from the version directory.

        Returns:
            VersionConfig: Parsed configuration object
        """
        if self._config is None:
            with open(self.config_path, "r") as f:
                config_dict = yaml.safe_load(f)

            prompt_path = self.config_path.parent / "system_prompt.md"
            if prompt_path.exists():
                config_dict["system_prompt"] = prompt_path.read_text().strip()

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

    @classmethod
    def list_available_versions(cls) -> list[str]:
        """List all available workflow versions.

        Returns:
            List of version directory names
        """
        versions = []
        for item in cls.VERSIONS_DIR.iterdir():
            if item.is_dir() and item.name.startswith("v"):
                config_file = item / "orchestrator_config.yaml"
                if config_file.exists():
                    versions.append(item.name)
        return sorted(versions)
