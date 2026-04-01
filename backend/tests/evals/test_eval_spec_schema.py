"""Tests for evaluation scenario configuration loading."""

from pathlib import Path
import textwrap

import pytest

from backend.evals.eval_spec_schema import (
    BraintrustConfig,
    ScenarioConfig,
    load_braintrust_config,
    load_scenario_config,
)


def test_load_scenario_config_parses_valid_yaml(tmp_path: Path) -> None:
    config_path = tmp_path / "eval_spec.yaml"
    config_path.write_text(
        """
name: sample-eval
csv: custom_dataset.csv
task:
  function: backend.evals.tasks.run_sample_task
column_mapping:
  prompt: input_text
  response: output_text
scorers:
  - name: programmatic_score
    function: backend.evals.scorers.score_response
  - name: judge_score
    type: llm_judge
    rubric: Evaluate response quality
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
    assert config.scorers[0].function == "backend.evals.scorers.score_response"
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
task:
  function: backend.evals.tasks.run_sample_task
column_mapping:
  prompt: input_text
scorers:
  - name: programmatic_score
    function: backend.evals.scorers.score_response
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
    "scorer_yaml",
    [
        """
  - name: judge_score
    type: llm_judge
    function: backend.evals.scorers.score_response
    rubric: Evaluate response quality
""",
        """
  - name: judge_score
    type: llm_judge
    model: gpt-4.1
""",
    ],
)
def test_load_scenario_config_invalid_scorer_shape_fails(
    tmp_path: Path,
    scorer_yaml: str,
) -> None:
    config_path = tmp_path / "eval_spec.yaml"
    scorer_block = textwrap.indent(textwrap.dedent(scorer_yaml).strip(), "  ")
    config_path.write_text(
        "\n".join(
            [
                "name: scorer-eval",
                "task:",
                "  function: backend.evals.tasks.run_sample_task",
                "column_mapping:",
                "  prompt: input_text",
                "scorers:",
                scorer_block,
            ]
        )
    )

    with pytest.raises(ValueError, match=f"Invalid scenario config in {config_path}"):
        load_scenario_config(config_path)


def test_load_scenario_config_duplicate_scorer_names_fail(tmp_path: Path) -> None:
    config_path = tmp_path / "eval_spec.yaml"
    config_path.write_text(
        """
name: duplicate-scorers
task:
  function: backend.evals.tasks.run_sample_task
column_mapping:
  prompt: input_text
scorers:
  - name: judge_score
    type: llm_judge
    rubric: Evaluate response quality
  - name: judge_score
    function: backend.evals.scorers.score_response
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
    function: backend.evals.scorers.score_response
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
    config_path = tmp_path / "eval_spec.yaml"
    config_path.write_text(
        """
name: scorer-eval
task:
  function: backend.evals.tasks.run_sample_task
column_mapping:
  prompt: input_text
scorers:
  - name: programmatic_score
    function: backend.evals.scorers.score_response
  - name: judge_score
    type: llm_judge
    rubric: Judge with a rubric
    model: gpt-4.1
""".strip()
    )

    config = load_scenario_config(config_path)

    assert config.scorers[0].function == "backend.evals.scorers.score_response"
    assert config.scorers[0].type is None
    assert config.scorers[1].function is None
    assert config.scorers[1].type == "llm_judge"
    assert config.scorers[1].rubric == "Judge with a rubric"
    assert config.scorers[1].model == "gpt-4.1"
    assert config.scorers[1].use_cot is False
    assert config.scorers[1].choice_scores == {"Y": 1.0, "N": 0.0}


def test_load_braintrust_config_applies_project_default_when_omitted(
    tmp_path: Path,
) -> None:
    config_path = tmp_path / "braintrust_config.yaml"
    config_path.write_text(
        """
braintrust:
  api_key_env: CUSTOM_BRAINTRUST_KEY
  local_mode: true
""".strip()
    )

    config = load_braintrust_config(config_path)

    assert isinstance(config, BraintrustConfig)
    assert config.project == "finlab-x"
    assert config.api_key_env == "CUSTOM_BRAINTRUST_KEY"
    assert config.local_mode is True
