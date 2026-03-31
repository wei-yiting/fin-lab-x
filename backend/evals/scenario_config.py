"""Scenario configuration models and YAML loaders for evaluation specs."""

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel


class ScorerConfig(BaseModel):
    """Configuration for a single scorer."""

    name: str
    function: str | None = None
    type: str | None = None
    rubric: str | None = None
    model: str | None = None
    use_cot: bool = False
    choice_scores: dict[str, float] | None = None


class TaskConfig(BaseModel):
    """Configuration for the task function under evaluation."""

    function: str


class ScenarioConfig(BaseModel):
    """Complete evaluation scenario configuration."""

    name: str
    csv: str = "dataset.csv"
    task: TaskConfig
    column_mapping: dict[str, str]
    scorers: list[ScorerConfig]


class BraintrustConfig(BaseModel):
    """Configuration for Braintrust evaluation execution."""

    project: str = "finlab-x"
    api_key_env: str = "BRAINTRUST_API_KEY"
    local_mode: bool = False


def _load_yaml_mapping(config_path: Path) -> dict[str, Any]:
    """Load a YAML file and validate that it contains a mapping."""
    try:
        with config_path.open("r", encoding="utf-8") as file:
            loaded = yaml.safe_load(file) or {}
    except yaml.YAMLError as exc:
        raise ValueError(f"Invalid YAML in {config_path}: {exc}") from exc

    if not isinstance(loaded, dict):
        raise ValueError(f"YAML config must be a mapping: {config_path}")

    return loaded


def load_scenario_config(config_path: Path) -> ScenarioConfig:
    """Read eval_spec.yaml and return validated ScenarioConfig."""
    config_data = _load_yaml_mapping(config_path)
    return ScenarioConfig.model_validate(config_data)


def load_braintrust_config(config_path: Path) -> BraintrustConfig:
    """Read braintrust_config.yaml and return BraintrustConfig."""
    config_data = _load_yaml_mapping(config_path)
    braintrust_data = config_data.get("braintrust", config_data)

    if not isinstance(braintrust_data, dict):
        raise ValueError(f"Braintrust config must be a mapping: {config_path}")

    return BraintrustConfig.model_validate(braintrust_data)
