"""Tests for evaluation scenario configuration loading."""

from pathlib import Path
import textwrap

import pytest
from pydantic import ValidationError

from backend.evals.eval_spec_schema import (
    BraintrustConfig,
    DiagnosticScenarioConfig,
    ScenarioConfig,
    load_braintrust_config,
    load_scenario_config,
)


def test_load_scenario_config_parses_valid_yaml(tmp_path: Path) -> None:
    (tmp_path / "judge_rubric.md").write_text("Evaluate response quality")
    config_path = tmp_path / "eval_spec.yaml"
    config_path.write_text(
        """
name: sample-eval
csv: custom_dataset.csv
regression:
  enabled: true
task:
  function: backend.evals.tasks.run_sample_task
column_mapping:
  prompt: input_text
  response: output_text
scorers:
  - name: programmatic_score
    function: backend.evals.scenarios.example.scorer.score_response
  - name: judge_score
    type: llm_judge
    rubric_file: judge_rubric.md
    model: gpt-4.1
    choice_scores:
      pass: 1.0
      fail: 0.0
""".strip()
    )

    config = load_scenario_config(config_path)

    assert isinstance(config, ScenarioConfig)
    assert config.name == "sample-eval"
    assert config.csv == "custom_dataset.csv"
    assert config.task.function == "backend.evals.tasks.run_sample_task"
    assert config.column_mapping == {
        "prompt": "input_text",
        "response": "output_text",
    }
    assert len(config.scorers) == 2
    assert (
        config.scorers[0].function
        == "backend.evals.scenarios.example.scorer.score_response"
    )
    assert config.scorers[0].type is None
    assert config.scorers[0].use_cot is False
    assert config.scorers[1].type == "llm_judge"
    assert config.scorers[1].rubric == "Evaluate response quality"
    assert config.scorers[1].model == "gpt-4.1"
    assert config.scorers[1].use_cot is False
    assert config.scorers[1].choice_scores == {"pass": 1.0, "fail": 0.0}


def test_load_scenario_config_unknown_field_fails(tmp_path: Path) -> None:
    config_path = tmp_path / "eval_spec.yaml"
    config_path.write_text(
        """
name: sample-eval
unexpected: value
regression:
  enabled: true
task:
  function: backend.evals.tasks.run_sample_task
column_mapping:
  prompt: input_text
scorers:
  - name: programmatic_score
    function: backend.evals.scenarios.example.scorer.score_response
""".strip()
    )

    with pytest.raises(ValueError, match=f"Invalid scenario config in {config_path}"):
        load_scenario_config(config_path)


def test_load_scenario_config_missing_task_function_raises_validation_error(
    tmp_path: Path,
) -> None:
    config_path = tmp_path / "eval_spec.yaml"
    config_path.write_text(
        """
name: invalid-eval
regression:
  enabled: true
task: {}
column_mapping:
  prompt: input_text
scorers:
  - name: judge_score
""".strip()
    )

    with pytest.raises(ValueError, match=f"Invalid scenario config in {config_path}"):
        load_scenario_config(config_path)


@pytest.mark.parametrize(
    ("scorer_yaml", "expected_message"),
    [
        pytest.param(
            """
  - name: judge_score
    type: llm_judge
    function: backend.evals.scenarios.example.scorer.score_response
    rubric_file: judge_rubric.md
""",
            "cannot mix programmatic and llm_judge",
            id="mixed-mode",
        ),
        pytest.param(
            """
  - name: judge_score
    type: llm_judge
    model: gpt-4.1
""",
            "must include rubric_file",
            id="judge-without-rubric-file",
        ),
    ],
)
def test_load_scenario_config_invalid_scorer_shape_fails(
    tmp_path: Path,
    scorer_yaml: str,
    expected_message: str,
) -> None:
    """Each invalid shape fails for its own reason, not an earlier guard's.

    The mixed-mode case references a real rubric_file on purpose: an inline
    rubric would be rejected at the YAML boundary first and leave the
    programmatic/llm_judge conflict untested.
    """
    (tmp_path / "judge_rubric.md").write_text("Evaluate response quality")
    config_path = tmp_path / "eval_spec.yaml"
    scorer_block = textwrap.indent(textwrap.dedent(scorer_yaml).strip(), "  ")
    config_path.write_text(
        "\n".join(
            [
                "name: scorer-eval",
                "regression:",
                "  enabled: true",
                "task:",
                "  function: backend.evals.tasks.run_sample_task",
                "column_mapping:",
                "  prompt: input_text",
                "scorers:",
                scorer_block,
            ]
        )
    )

    with pytest.raises(ValueError, match=expected_message):
        load_scenario_config(config_path)


def test_load_scenario_config_duplicate_scorer_names_fail(tmp_path: Path) -> None:
    (tmp_path / "judge_rubric.md").write_text("Evaluate response quality")
    config_path = tmp_path / "eval_spec.yaml"
    config_path.write_text(
        """
name: duplicate-scorers
regression:
  enabled: true
task:
  function: backend.evals.tasks.run_sample_task
column_mapping:
  prompt: input_text
scorers:
  - name: judge_score
    type: llm_judge
    rubric_file: judge_rubric.md
  - name: judge_score
    function: backend.evals.scenarios.example.scorer.score_response
""".strip()
    )

    with pytest.raises(ValueError, match=f"Invalid scenario config in {config_path}"):
        load_scenario_config(config_path)


def test_load_scenario_config_invalid_yaml_syntax_raises_clear_error(
    tmp_path: Path,
) -> None:
    config_path = tmp_path / "eval_spec.yaml"
    config_path.write_text(
        """
name: broken-eval
regression:
  enabled: true
task:
  function: backend.evals.tasks.run_sample_task
column_mapping:
  prompt: input_text
scorers:
  - name: judge_score
    type: llm_judge
    rubric: Evaluate response quality
    model: gpt-4.1
    choice_scores:
      pass: 1.0
      fail: 0.0
  - name: missing_indent
    function: backend.evals.scenarios.example.scorer.score_response
    - invalid
""".strip()
    )

    with pytest.raises(ValueError, match=f"Invalid YAML in {config_path}"):
        load_scenario_config(config_path)


def test_load_scenario_config_top_level_non_mapping_fails_cleanly(
    tmp_path: Path,
) -> None:
    config_path = tmp_path / "eval_spec.yaml"
    config_path.write_text(
        """
- name: sample-eval
- task:
    function: backend.evals.tasks.run_sample_task
""".strip()
    )

    with pytest.raises(ValueError, match="must be a mapping"):
        load_scenario_config(config_path)


def test_load_scenario_config_supports_programmatic_and_llm_judge_scorers(
    tmp_path: Path,
) -> None:
    (tmp_path / "judge_rubric.md").write_text("Judge with a rubric")
    config_path = tmp_path / "eval_spec.yaml"
    config_path.write_text(
        """
name: scorer-eval
regression:
  enabled: true
task:
  function: backend.evals.tasks.run_sample_task
column_mapping:
  prompt: input_text
scorers:
  - name: programmatic_score
    function: backend.evals.scenarios.example.scorer.score_response
  - name: judge_score
    type: llm_judge
    rubric_file: judge_rubric.md
    model: gpt-4.1
""".strip()
    )

    config = load_scenario_config(config_path)

    assert (
        config.scorers[0].function
        == "backend.evals.scenarios.example.scorer.score_response"
    )
    assert config.scorers[0].type is None
    assert config.scorers[1].function is None
    assert config.scorers[1].type == "llm_judge"
    assert config.scorers[1].rubric == "Judge with a rubric"
    assert config.scorers[1].model == "gpt-4.1"
    assert config.scorers[1].use_cot is False
    assert config.scorers[1].choice_scores == {"Y": 1.0, "N": 0.0}


def test_load_scenario_config_parses_diagnostic_block_with_defaults(
    tmp_path: Path,
) -> None:
    config_path = tmp_path / "eval_spec.yaml"
    config_path.write_text(
        """
name: baseline_behavior_diagnostic
csv: dataset.csv
regression:
  enabled: false
diagnostic:
  dataset_name: baseline_behavior_diagnostic
  dataset_version: "2026-04-24"
task:
  function: backend.evals.eval_tasks.run_baseline_behavior_diagnostic
column_mapping:
  question: input.question
scorers:
  - name: diagnostic_execution_health
    function: backend.evals.diagnostic.execution_scorer.execution_health
""".strip()
    )

    config = load_scenario_config(config_path)

    assert isinstance(config.diagnostic, DiagnosticScenarioConfig)
    assert config.diagnostic.dataset_name == "baseline_behavior_diagnostic"
    assert config.diagnostic.dataset_version == "2026-04-24"
    assert config.diagnostic.agent_version == "baseline"


@pytest.mark.parametrize("removed_field", ["row_id_column", "question_column"])
def test_diagnostic_config_rejects_removed_column_fields(removed_field: str) -> None:
    """id/question are a fixed dataset convention — no longer configurable."""
    payload = {
        "dataset_name": "baseline_behavior_diagnostic",
        "dataset_version": "2026-04-24",
        "agent_version": "baseline",
        removed_field: "custom",
    }

    with pytest.raises(ValidationError):
        DiagnosticScenarioConfig.model_validate(payload)


def test_load_scenario_config_rejects_unknown_diagnostic_field(
    tmp_path: Path,
) -> None:
    config_path = tmp_path / "eval_spec.yaml"
    config_path.write_text(
        """
name: baseline_behavior_diagnostic
regression:
  enabled: false
diagnostic:
  dataset_name: baseline_behavior_diagnostic
  dataset_version: "2026-04-24"
  unknown_field: nope
task:
  function: backend.evals.eval_tasks.run_baseline_behavior_diagnostic
column_mapping:
  question: input.question
scorers:
  - name: diagnostic_execution_health
    function: backend.evals.diagnostic.execution_scorer.execution_health
""".strip()
    )

    with pytest.raises(ValueError, match=f"Invalid scenario config in {config_path}"):
        load_scenario_config(config_path)


@pytest.mark.parametrize(
    ("field_name", "field_value"),
    [
        ("dataset_name", ""),
        ("dataset_version", ""),
        ("agent_version", ""),
    ],
)
def test_diagnostic_config_rejects_empty_identity_fields(
    field_name: str,
    field_value: str,
) -> None:
    payload = {
        "dataset_name": "baseline_behavior_diagnostic",
        "dataset_version": "2026-04-24",
        "agent_version": "baseline",
    }
    payload[field_name] = field_value

    with pytest.raises(ValidationError):
        DiagnosticScenarioConfig.model_validate(payload)


def test_checked_in_baseline_behavior_diagnostic_spec_loads_and_resolves_contract() -> (
    None
):
    from backend.evals.scorer_registry import resolve_function

    config_path = (
        Path(__file__).resolve().parents[2]
        / "evals"
        / "scenarios"
        / "baseline_behavior_diagnostic"
        / "eval_spec.yaml"
    )

    config = load_scenario_config(config_path)
    task_fn = resolve_function(config.task.function, label="task")
    scorer_fn = resolve_function(config.scorers[0].function or "", label="scorer")

    assert config.name == "baseline_behavior_diagnostic"
    assert config.diagnostic is not None
    assert callable(task_fn)
    assert callable(scorer_fn)


def test_load_scenario_config_missing_regression_block_fails(tmp_path: Path) -> None:
    """Gate membership must be declared — a spec without it does not load."""
    config_path = tmp_path / "eval_spec.yaml"
    config_path.write_text(
        """
name: no-regression-eval
task:
  function: backend.evals.tasks.run_sample_task
column_mapping:
  prompt: input_text
scorers:
  - name: programmatic_score
    function: backend.evals.scenarios.example.scorer.score_response
""".strip()
    )

    with pytest.raises(ValueError, match="regression"):
        load_scenario_config(config_path)


def test_load_scenario_config_missing_regression_enabled_fails(
    tmp_path: Path,
) -> None:
    """The regression block itself must state enabled — no default either way."""
    config_path = tmp_path / "eval_spec.yaml"
    config_path.write_text(
        """
name: empty-regression-eval
regression: {}
task:
  function: backend.evals.tasks.run_sample_task
column_mapping:
  prompt: input_text
scorers:
  - name: programmatic_score
    function: backend.evals.scenarios.example.scorer.score_response
""".strip()
    )

    with pytest.raises(ValueError, match="enabled"):
        load_scenario_config(config_path)


@pytest.mark.parametrize("enabled", [True, False])
def test_load_scenario_config_parses_regression_enabled(
    tmp_path: Path, enabled: bool
) -> None:
    config_path = tmp_path / "eval_spec.yaml"
    config_path.write_text(
        f"""
name: regression-eval
regression:
  enabled: {str(enabled).lower()}
task:
  function: backend.evals.tasks.run_sample_task
column_mapping:
  prompt: input_text
scorers:
  - name: programmatic_score
    function: backend.evals.scenarios.example.scorer.score_response
""".strip()
    )

    config = load_scenario_config(config_path)

    assert config.regression.enabled is enabled


def test_scorer_gate_fields_default_to_strictest(tmp_path: Path) -> None:
    """Omitted gate fields mean counted-in with a 1.0 floor — never a hole."""
    config_path = tmp_path / "eval_spec.yaml"
    config_path.write_text(
        """
name: gate-defaults-eval
regression:
  enabled: true
task:
  function: backend.evals.tasks.run_sample_task
column_mapping:
  prompt: input_text
scorers:
  - name: programmatic_score
    function: backend.evals.scenarios.example.scorer.score_response
""".strip()
    )

    config = load_scenario_config(config_path)

    assert config.scorers[0].gate is True
    assert config.scorers[0].metric_floor == 1.0


def test_scorer_gate_fields_accept_explicit_values(tmp_path: Path) -> None:
    config_path = tmp_path / "eval_spec.yaml"
    config_path.write_text(
        """
name: gate-explicit-eval
regression:
  enabled: true
task:
  function: backend.evals.tasks.run_sample_task
column_mapping:
  prompt: input_text
scorers:
  - name: floored_score
    function: backend.evals.scenarios.example.scorer.score_response
    metric_floor: 0.7
  - name: ungated_score
    function: backend.evals.scenarios.example.scorer.score_response
    gate: false
""".strip()
    )

    config = load_scenario_config(config_path)

    assert config.scorers[0].gate is True
    assert config.scorers[0].metric_floor == 0.7
    assert config.scorers[1].gate is False


def test_scorer_explicit_metric_floor_with_gate_false_fails(tmp_path: Path) -> None:
    """A floor on an ungated scorer is dead config — reject it (ADR-0008)."""
    config_path = tmp_path / "eval_spec.yaml"
    config_path.write_text(
        """
name: dead-floor-eval
regression:
  enabled: true
task:
  function: backend.evals.tasks.run_sample_task
column_mapping:
  prompt: input_text
scorers:
  - name: dead_floor_score
    function: backend.evals.scenarios.example.scorer.score_response
    gate: false
    metric_floor: 0.7
""".strip()
    )

    with pytest.raises(ValueError, match="metric_floor"):
        load_scenario_config(config_path)


@pytest.mark.parametrize("floor", [-0.1, 1.5])
def test_scorer_metric_floor_out_of_range_fails(tmp_path: Path, floor: float) -> None:
    config_path = tmp_path / "eval_spec.yaml"
    config_path.write_text(
        f"""
name: floor-range-eval
regression:
  enabled: true
task:
  function: backend.evals.tasks.run_sample_task
column_mapping:
  prompt: input_text
scorers:
  - name: bad_floor_score
    function: backend.evals.scenarios.example.scorer.score_response
    metric_floor: {floor}
""".strip()
    )

    with pytest.raises(ValueError, match=f"Invalid scenario config in {config_path}"):
        load_scenario_config(config_path)


def test_llm_judge_inline_rubric_fails_with_guidance(tmp_path: Path) -> None:
    """Rubrics are prompt assets — file-only, never inline YAML."""
    config_path = tmp_path / "eval_spec.yaml"
    config_path.write_text(
        """
name: inline-rubric-eval
regression:
  enabled: true
task:
  function: backend.evals.tasks.run_sample_task
column_mapping:
  prompt: input_text
scorers:
  - name: judge_score
    type: llm_judge
    rubric: Judge inline
    model: gpt-4.1
""".strip()
    )

    with pytest.raises(ValueError, match="rubric_file"):
        load_scenario_config(config_path)


def test_llm_judge_rubric_file_missing_fails(tmp_path: Path) -> None:
    config_path = tmp_path / "eval_spec.yaml"
    config_path.write_text(
        """
name: missing-rubric-file-eval
regression:
  enabled: true
task:
  function: backend.evals.tasks.run_sample_task
column_mapping:
  prompt: input_text
scorers:
  - name: judge_score
    type: llm_judge
    rubric_file: nonexistent.md
    model: gpt-4.1
""".strip()
    )

    with pytest.raises(ValueError, match="nonexistent.md"):
        load_scenario_config(config_path)


def test_llm_judge_rubric_file_populates_rubric(tmp_path: Path) -> None:
    """The loader reads the file so the engine still consumes a rubric string."""
    rubric_text = "Judge the response for {{expected.ticker}} focus."
    (tmp_path / "rubric.md").write_text(rubric_text)
    config_path = tmp_path / "eval_spec.yaml"
    config_path.write_text(
        """
name: rubric-file-eval
regression:
  enabled: true
task:
  function: backend.evals.tasks.run_sample_task
column_mapping:
  prompt: input_text
scorers:
  - name: judge_score
    type: llm_judge
    rubric_file: rubric.md
    model: gpt-4.1
""".strip()
    )

    config = load_scenario_config(config_path)

    assert config.scorers[0].rubric_file == "rubric.md"
    assert config.scorers[0].rubric == rubric_text


def test_llm_judge_absolute_rubric_file_fails(tmp_path: Path) -> None:
    """rubric_file is relative to the scenario dir — absolute paths escape it."""
    rubric_path = tmp_path / "rubric.md"
    rubric_path.write_text("Judge with a rubric")
    config_path = tmp_path / "eval_spec.yaml"
    config_path.write_text(
        f"""
name: absolute-rubric-file-eval
regression:
  enabled: true
task:
  function: backend.evals.tasks.run_sample_task
column_mapping:
  prompt: input_text
scorers:
  - name: judge_score
    type: llm_judge
    rubric_file: {rubric_path}
    model: gpt-4.1
""".strip()
    )

    with pytest.raises(ValueError, match="must be a path relative"):
        load_scenario_config(config_path)


def test_loaded_config_round_trips_through_validation(tmp_path: Path) -> None:
    """The loader's output (rubric populated from rubric_file) stays valid
    against the schema — both fields set is a legitimate loaded state."""
    (tmp_path / "rubric.md").write_text("Judge with a rubric")
    config_path = tmp_path / "eval_spec.yaml"
    config_path.write_text(
        """
name: round-trip-eval
regression:
  enabled: true
task:
  function: backend.evals.tasks.run_sample_task
column_mapping:
  prompt: input_text
scorers:
  - name: judge_score
    type: llm_judge
    rubric_file: rubric.md
    model: gpt-4.1
""".strip()
    )

    config = load_scenario_config(config_path)
    revalidated = ScenarioConfig.model_validate(config.model_dump())

    assert revalidated.scorers[0].rubric == "Judge with a rubric"
    assert revalidated.scorers[0].rubric_file == "rubric.md"


def test_programmatic_scorer_with_rubric_file_fails(tmp_path: Path) -> None:
    config_path = tmp_path / "eval_spec.yaml"
    config_path.write_text(
        """
name: programmatic-rubric-file-eval
regression:
  enabled: true
task:
  function: backend.evals.tasks.run_sample_task
column_mapping:
  prompt: input_text
scorers:
  - name: programmatic_score
    function: backend.evals.scenarios.example.scorer.score_response
    rubric_file: rubric.md
""".strip()
    )

    with pytest.raises(ValueError, match=f"Invalid scenario config in {config_path}"):
        load_scenario_config(config_path)


REAL_SCENARIOS_DIR = Path(__file__).parents[2] / "evals" / "scenarios"

# Discovered rather than hand-listed: a new scenario that forgets its
# regression declaration must fail here without anyone remembering to add it.
REAL_SCENARIOS = sorted(
    spec.parent.name for spec in REAL_SCENARIOS_DIR.glob("*/eval_spec.yaml")
)


def test_real_scenario_discovery_is_not_empty() -> None:
    """Guard the glob above: zero scenarios would silently run zero tests."""
    assert REAL_SCENARIOS


@pytest.mark.parametrize("scenario", REAL_SCENARIOS)
def test_real_scenario_specs_load(scenario: str) -> None:
    """Every shipped scenario satisfies the gate contract on load."""
    config = load_scenario_config(REAL_SCENARIOS_DIR / scenario / "eval_spec.yaml")

    assert config.name == scenario
    for scorer in config.scorers:
        if scorer.type == "llm_judge":
            assert scorer.rubric_file is not None
            assert scorer.rubric  # populated from the file by the loader


def test_real_language_policy_spec_matches_gate_contract() -> None:
    config = load_scenario_config(
        REAL_SCENARIOS_DIR / "language_policy" / "eval_spec.yaml"
    )

    assert config.regression.enabled is True
    scorer_names = [scorer.name for scorer in config.scorers]
    assert "expected_tool_called" in scorer_names
    assert "response_relevance" not in scorer_names


def test_real_sec_retrieval_spec_matches_gate_contract() -> None:
    """The floors are pinned because they derive from a recorded reference
    measurement (see the scenario README and the measurement record under
    backend/evals/regression/reference_measurements/sec_retrieval/). Any
    intentional change must go through re-derivation per the recorded
    derivation (backend/evals/regression/sec_retrieval-metric-floors.md),
    not an in-place edit."""
    config = load_scenario_config(
        REAL_SCENARIOS_DIR / "sec_retrieval" / "eval_spec.yaml"
    )

    assert config.regression.enabled is True
    expected_floors = {
        "header_path_recall_at_5": 0.75,
        "header_path_recall_at_10": 0.75,
        "mrr": 0.60,
        "map": 0.55,
    }
    assert {s.name for s in config.scorers} == set(expected_floors)
    for scorer in config.scorers:
        assert scorer.type is None
        assert scorer.gate is True
        assert scorer.metric_floor == expected_floors[scorer.name]


def test_real_on_target_company_spec_matches_gate_contract() -> None:
    config = load_scenario_config(
        REAL_SCENARIOS_DIR / "on_target_company" / "eval_spec.yaml"
    )

    assert config.regression.enabled is False
    assert len(config.scorers) == 1
    judge = config.scorers[0]
    assert judge.name == "on_target_company"
    assert judge.type == "llm_judge"
    assert judge.gate is True
    assert judge.metric_floor == 1.0
    assert "{{expected.ticker}}" in (judge.rubric or "")


def test_load_braintrust_config_applies_project_default_when_omitted(
    tmp_path: Path,
) -> None:
    config_path = tmp_path / "braintrust_config.yaml"
    config_path.write_text(
        """
braintrust:
  api_key_env: CUSTOM_BRAINTRUST_KEY
""".strip()
    )

    config = load_braintrust_config(config_path)

    assert isinstance(config, BraintrustConfig)
    assert config.project == "finlab-x"
    assert config.api_key_env == "CUSTOM_BRAINTRUST_KEY"


def test_braintrust_config_rejects_local_mode_field(tmp_path: Path) -> None:
    """local_mode was removed — --upload is the only mode switch now."""
    config_path = tmp_path / "braintrust_config.yaml"
    config_path.write_text(
        """
braintrust:
  api_key_env: CUSTOM_BRAINTRUST_KEY
  local_mode: true
""".strip()
    )

    with pytest.raises(ValueError, match="Invalid braintrust config"):
        load_braintrust_config(config_path)
