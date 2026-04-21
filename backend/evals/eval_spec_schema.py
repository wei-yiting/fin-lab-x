"""Scenario configuration models and YAML loaders for evaluation specs."""

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, ConfigDict, ValidationError, model_validator


class ScorerConfig(BaseModel):
    """Configuration for a single scorer."""

    model_config = ConfigDict(extra="forbid")

    name: str
    function: str | None = None
    type: str | None = None
    rubric: str | None = None
    model: str | None = None
    use_cot: bool = False
    choice_scores: dict[str, float] | None = None

    @model_validator(mode="after")
    def validate_mode(self) -> "ScorerConfig":
        """Ensure the scorer is either programmatic or llm_judge, not both."""
        has_function = self.function is not None
        is_llm_judge = self.type == "llm_judge"

        if has_function and self.type is not None:
            raise ValueError(
                "ScorerConfig cannot mix programmatic and llm_judge fields"
            )
        if not has_function and not is_llm_judge:
            raise ValueError(
                "ScorerConfig must define either function or type='llm_judge'"
            )

        if has_function:
            if self.rubric is not None or self.model is not None:
                raise ValueError(
                    "Programmatic ScorerConfig must not include llm_judge fields"
                )
            if self.choice_scores is not None:
                raise ValueError(
                    "Programmatic ScorerConfig must not include choice_scores"
                )
            if self.use_cot:
                raise ValueError(
                    "Programmatic ScorerConfig must not set use_cot"
                )
            return self

        if self.type != "llm_judge":
            raise ValueError("ScorerConfig type must be 'llm_judge'")
        if self.rubric is None:
            raise ValueError("llm_judge ScorerConfig must include rubric")
        if self.choice_scores is None:
            self.choice_scores = {"Y": 1.0, "N": 0.0}
        return self


class TaskConfig(BaseModel):
    """Configuration for the task function under evaluation."""

    model_config = ConfigDict(extra="forbid")

    function: str
    timeout: float | None = None


class PreRunConfig(BaseModel):
    """Optional hook that runs once before evaluation, returning banner fields."""

    model_config = ConfigDict(extra="forbid")

    function: str


class ScenarioConfig(BaseModel):
    """Complete evaluation scenario configuration."""

    model_config = ConfigDict(extra="forbid")

    name: str
    status: str | None = None
    csv: str = "dataset.csv"
    task: TaskConfig
    pre_run: PreRunConfig | None = None
    column_mapping: dict[str, str]
    scorers: list[ScorerConfig]

    @model_validator(mode="after")
    def validate_scorer_names(self) -> "ScenarioConfig":
        """Reject duplicate scorer names."""
        scorer_names: set[str] = set()
        for scorer in self.scorers:
            if scorer.name in scorer_names:
                raise ValueError(f"duplicate scorer name: {scorer.name}")
            scorer_names.add(scorer.name)
        return self


class BraintrustConfig(BaseModel):
    """Configuration for Braintrust evaluation execution."""

    model_config = ConfigDict(extra="forbid")

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
    try:
        return ScenarioConfig.model_validate(config_data)
    except ValidationError as exc:
        raise ValueError(f"Invalid scenario config in {config_path}: {exc}") from exc


def load_braintrust_config(config_path: Path) -> BraintrustConfig:
    """Read braintrust_config.yaml and return BraintrustConfig."""
    config_data = _load_yaml_mapping(config_path)
    braintrust_data = config_data.get("braintrust", config_data)

    if not isinstance(braintrust_data, dict):
        raise ValueError(f"Braintrust config must be a mapping: {config_path}")

    try:
        return BraintrustConfig.model_validate(braintrust_data)
    except ValidationError as exc:
        raise ValueError(f"Invalid braintrust config in {config_path}: {exc}") from exc
