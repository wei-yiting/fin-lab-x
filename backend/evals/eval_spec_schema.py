"""Scenario configuration models and YAML loaders for evaluation specs."""

from pathlib import Path
from typing import Any

import yaml
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    ValidationError,
    field_validator,
    model_validator,
)


class ScorerConfig(BaseModel):
    """Configuration for a single scorer."""

    model_config = ConfigDict(extra="forbid")

    name: str
    function: str | None = None
    type: str | None = None
    rubric: str | None = None
    rubric_file: str | None = None
    model: str | None = None
    use_cot: bool = False
    temperature: float = Field(default=0.0, ge=0.0, le=2.0, allow_inf_nan=False)
    choice_scores: dict[str, float] | None = None
    gate: bool = True
    metric_floor: float = Field(default=1.0, ge=0.0, le=1.0, allow_inf_nan=False)

    @model_validator(mode="after")
    def validate_gate_fields(self) -> "ScorerConfig":
        """Reject dead config: a metric_floor on an ungated scorer (ADR-0008)."""
        if not self.gate and "metric_floor" in self.model_fields_set:
            raise ValueError(
                "metric_floor has no effect when gate is false — remove it "
                "or re-enable the gate"
            )
        return self

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
            if (
                self.rubric is not None
                or self.rubric_file is not None
                or self.model is not None
            ):
                raise ValueError(
                    "Programmatic ScorerConfig must not include llm_judge fields"
                )
            if self.choice_scores is not None:
                raise ValueError(
                    "Programmatic ScorerConfig must not include choice_scores"
                )
            if self.use_cot:
                raise ValueError("Programmatic ScorerConfig must not set use_cot")
            if "temperature" in self.model_fields_set:
                raise ValueError("Programmatic ScorerConfig must not set temperature")
            return self

        if self.type != "llm_judge":
            raise ValueError("ScorerConfig type must be 'llm_judge'")
        if self.rubric is None and self.rubric_file is None:
            raise ValueError("llm_judge ScorerConfig must include rubric_file")
        if self.rubric is not None and self.rubric_file is not None:
            raise ValueError(
                "llm_judge ScorerConfig must not set both rubric and rubric_file"
            )
        if self.choice_scores is None:
            self.choice_scores = {"Y": 1.0, "N": 0.0}
        return self


class RegressionConfig(BaseModel):
    """Gate membership declaration for the Regression Suite (ADR-0008).

    Required on every scenario, with no default for ``enabled``: a spec that
    has not decided its gate membership must fail to load rather than
    silently sit outside the gate.
    """

    model_config = ConfigDict(extra="forbid")

    enabled: bool


class TaskConfig(BaseModel):
    """Configuration for the task function under evaluation."""

    model_config = ConfigDict(extra="forbid")

    function: str
    timeout: float | None = None


class PreRunConfig(BaseModel):
    """Optional hook that runs once before evaluation, returning banner fields."""

    model_config = ConfigDict(extra="forbid")

    function: str


class DiagnosticScenarioConfig(BaseModel):
    """Optional diagnostic scenario contract for dataset identity."""

    model_config = ConfigDict(extra="forbid")

    dataset_name: str
    dataset_version: str
    agent_version: str = "baseline"

    @field_validator("dataset_name", "dataset_version", "agent_version")
    @classmethod
    def validate_non_empty_string(cls, value: str) -> str:
        """Reject empty identity fields."""
        if value.strip() == "":
            raise ValueError("diagnostic identity fields must not be empty")
        return value


class ScenarioConfig(BaseModel):
    """Complete evaluation scenario configuration."""

    model_config = ConfigDict(extra="forbid")

    name: str
    status: str | None = None
    csv: str = "dataset.csv"
    regression: RegressionConfig
    task: TaskConfig
    pre_run: PreRunConfig | None = None
    diagnostic: DiagnosticScenarioConfig | None = None
    column_mapping: dict[str, str]
    column_types: dict[str, str] = {}
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


def _reject_inline_rubrics(config_data: dict[str, Any], config_path: Path) -> None:
    """Enforce the file-only rubric contract at the YAML boundary.

    ``rubric`` stays a model field (the engine consumes the loaded string),
    but spec files may only declare ``rubric_file``.
    """
    scorers = config_data.get("scorers")
    if not isinstance(scorers, list):
        return
    for scorer in scorers:
        if isinstance(scorer, dict) and "rubric" in scorer:
            raise ValueError(
                f"Invalid scenario config in {config_path}: inline rubric is "
                "not allowed — move the rubric text to a file and reference "
                "it with rubric_file"
            )


def _resolve_rubric_files(config: ScenarioConfig, config_path: Path) -> ScenarioConfig:
    """Read each scorer's rubric_file into ``rubric`` for the engine."""
    resolved: list[ScorerConfig] = []
    for scorer in config.scorers:
        if scorer.rubric_file is None:
            resolved.append(scorer)
            continue
        rubric_path = config_path.parent / scorer.rubric_file
        if not rubric_path.is_file():
            raise ValueError(
                f"Invalid scenario config in {config_path}: rubric_file "
                f"'{scorer.rubric_file}' not found at {rubric_path}"
            )
        resolved.append(
            scorer.model_copy(update={"rubric": rubric_path.read_text("utf-8")})
        )
    return config.model_copy(update={"scorers": resolved})


def load_scenario_config(config_path: Path) -> ScenarioConfig:
    """Read eval_spec.yaml and return validated ScenarioConfig."""
    config_data = _load_yaml_mapping(config_path)
    _reject_inline_rubrics(config_data, config_path)
    try:
        config = ScenarioConfig.model_validate(config_data)
    except ValidationError as exc:
        raise ValueError(f"Invalid scenario config in {config_path}: {exc}") from exc
    return _resolve_rubric_files(config, config_path)


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
