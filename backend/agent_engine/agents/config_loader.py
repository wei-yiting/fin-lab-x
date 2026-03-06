"""Version configuration loader for FinLab-X workflows."""

from pathlib import Path
from typing import Optional

import yaml
from pydantic import BaseModel, Field


class ModelConfig(BaseModel):
    """Model configuration for a workflow version."""

    name: str = "gpt-4o-mini"
    temperature: float = 0.0


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

    VERSIONS_DIR = Path(__file__).parent / "versions"

    def __init__(self, version_name: str):
        """Initialize loader for a specific version.

        Args:
            version_name: Name of the version (e.g., 'v1_baseline', 'v2_reader')
        """
        self.version_name = version_name
        self.config_path = self.VERSIONS_DIR / version_name / "version_config.yaml"

        if not self.config_path.exists():
            raise FileNotFoundError(f"Version config not found: {self.config_path}")

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

    @classmethod
    def list_available_versions(cls) -> list[str]:
        """List all available workflow versions.

        Returns:
            List of version directory names
        """
        versions = []
        for item in cls.VERSIONS_DIR.iterdir():
            if item.is_dir() and item.name.startswith("v"):
                config_file = item / "version_config.yaml"
                if config_file.exists():
                    versions.append(item.name)
        return sorted(versions)
