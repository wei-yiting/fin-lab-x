"""Tests for the eval runner: scenario discovery, execution, and result CSV output."""

import csv
import sys
import time
from pathlib import Path
from types import ModuleType
from types import SimpleNamespace
from typing import Any
from unittest.mock import MagicMock, patch

import pytest


def _make_eval_result(
    rows: list[dict[str, Any]], scorer_names: list[str]
) -> SimpleNamespace:
    """Build a fake Eval() result with .results and .summary."""
    results = []
    for row in rows:
        scores = {}
        for name in scorer_names:
            scores[name] = SimpleNamespace(score=row["scores"][name])
        results.append(
            SimpleNamespace(
                input=row["input"],
                output=row["output"],
                scores=scores,
            )
        )
    return SimpleNamespace(results=results, summary=SimpleNamespace())


# ---------------------------------------------------------------------------
# discover_scenarios
# ---------------------------------------------------------------------------


class TestDiscoverScenarios:
    def test_finds_directory_with_eval_spec(self, tmp_path: Path) -> None:
        scenario_dir = tmp_path / "my_scenario"
        scenario_dir.mkdir()
        (scenario_dir / "eval_spec.yaml").write_text("name: my_scenario\n")

        from backend.evals.eval_runner import discover_scenarios

        result = discover_scenarios(tmp_path)
        assert result == ["my_scenario"]

    def test_empty_directory_returns_empty_list(self, tmp_path: Path) -> None:
        from backend.evals.eval_runner import discover_scenarios

        assert discover_scenarios(tmp_path) == []

    def test_ignores_directory_without_eval_spec(self, tmp_path: Path) -> None:
        (tmp_path / "no_spec").mkdir()
        (tmp_path / "no_spec" / "dataset.csv").write_text("col\n1\n")

        from backend.evals.eval_runner import discover_scenarios

        assert discover_scenarios(tmp_path) == []

    def test_ignores_files_at_top_level(self, tmp_path: Path) -> None:
        (tmp_path / "eval_spec.yaml").write_text("name: top_level\n")

        from backend.evals.eval_runner import discover_scenarios

        assert discover_scenarios(tmp_path) == []

    def test_returns_sorted_names(self, tmp_path: Path) -> None:
        for name in ["zebra", "alpha", "middle"]:
            d = tmp_path / name
            d.mkdir()
            (d / "eval_spec.yaml").write_text(f"name: {name}\n")

        from backend.evals.eval_runner import discover_scenarios

        assert discover_scenarios(tmp_path) == ["alpha", "middle", "zebra"]

    def test_rejects_directory_name_with_spaces(self, tmp_path: Path) -> None:
        d = tmp_path / "response quality"
        d.mkdir()
        (d / "eval_spec.yaml").write_text("name: response_quality\n")

        from backend.evals.eval_runner import discover_scenarios

        with pytest.raises(ValueError, match="invalid characters"):
            discover_scenarios(tmp_path)

    def test_space_name_suggestion_uses_underscore(self, tmp_path: Path) -> None:
        d = tmp_path / "response quality"
        d.mkdir()
        (d / "eval_spec.yaml").write_text("name: response_quality\n")

        from backend.evals.eval_runner import discover_scenarios

        with pytest.raises(ValueError, match="response_quality"):
            discover_scenarios(tmp_path)


# ---------------------------------------------------------------------------
# write_result_csv
# ---------------------------------------------------------------------------


class TestWriteResultCsv:
    def test_writes_correct_columns_and_data(self, tmp_path: Path) -> None:
        eval_result = _make_eval_result(
            [
                {
                    "input": "hello",
                    "output": "world",
                    "scores": {"accuracy": 1.0, "relevance": 0.5},
                },
            ],
            ["accuracy", "relevance"],
        )

        from backend.evals.eval_runner import write_result_csv

        csv_path = write_result_csv(
            eval_result,
            "test_scenario",
            ["accuracy", "relevance"],
            tmp_path,
            original_columns=["prompt"],
            original_rows=[{"prompt": "hello"}],
        )

        assert csv_path.exists()
        with csv_path.open("r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        assert len(rows) == 1
        assert rows[0]["prompt"] == "hello"
        assert rows[0]["output"] == "world"
        assert rows[0]["score_accuracy"] == "1.0"
        assert rows[0]["score_relevance"] == "0.5"

    def test_filename_matches_pattern(self, tmp_path: Path) -> None:
        eval_result = _make_eval_result(
            [{"input": "x", "output": "y", "scores": {"s": 0.8}}],
            ["s"],
        )

        from backend.evals.eval_runner import write_result_csv

        csv_path = write_result_csv(eval_result, "my_scenario", ["s"], tmp_path)

        assert csv_path.name.startswith("my_scenario_")
        assert csv_path.suffix == ".csv"
        parts = csv_path.stem.split("_", 2)
        assert len(parts) >= 2

    def test_two_writes_produce_different_files(self, tmp_path: Path) -> None:
        eval_result = _make_eval_result(
            [{"input": "x", "output": "y", "scores": {"s": 1.0}}],
            ["s"],
        )

        from backend.evals.eval_runner import write_result_csv

        path1 = write_result_csv(eval_result, "sc", ["s"], tmp_path)
        time.sleep(0.05)
        path2 = write_result_csv(eval_result, "sc", ["s"], tmp_path)

        assert path1 != path2
        assert path1.exists() and path2.exists()

    def test_output_with_commas_and_newlines_escaped(self, tmp_path: Path) -> None:
        eval_result = _make_eval_result(
            [
                {
                    "input": "question",
                    "output": 'has, commas\nand "quotes"',
                    "scores": {"s": 0.9},
                },
            ],
            ["s"],
        )

        from backend.evals.eval_runner import write_result_csv

        csv_path = write_result_csv(eval_result, "escape_test", ["s"], tmp_path)

        with csv_path.open("r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        assert rows[0]["output"] == 'has, commas\nand "quotes"'

    def test_dict_output_expands_to_output_dot_columns(self, tmp_path: Path) -> None:
        eval_result = _make_eval_result(
            [
                {
                    "input": "q",
                    "output": {"response": "answer text", "model": "gpt-4"},
                    "scores": {"s": 1.0},
                },
            ],
            ["s"],
        )

        from backend.evals.eval_runner import write_result_csv

        csv_path = write_result_csv(eval_result, "dict_output", ["s"], tmp_path)

        with csv_path.open("r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        assert rows[0]["output.response"] == "answer text"
        assert rows[0]["output.model"] == "gpt-4"

    def test_creates_output_dir_if_missing(self, tmp_path: Path) -> None:
        output_dir = tmp_path / "nested" / "results"
        eval_result = _make_eval_result(
            [{"input": "x", "output": "y", "scores": {"s": 1.0}}],
            ["s"],
        )

        from backend.evals.eval_runner import write_result_csv

        csv_path = write_result_csv(eval_result, "sc", ["s"], output_dir)

        assert csv_path.exists()
        assert output_dir.exists()

    def test_original_columns_preserved_in_result(self, tmp_path: Path) -> None:
        eval_result = _make_eval_result(
            [
                {
                    "input": "hello",
                    "output": "world",
                    "scores": {"s": 1.0},
                },
            ],
            ["s"],
        )

        from backend.evals.eval_runner import write_result_csv

        csv_path = write_result_csv(
            eval_result,
            "test",
            ["s"],
            tmp_path,
            original_columns=["prompt", "notes"],
            original_rows=[{"prompt": "hello", "notes": "test note"}],
        )

        with csv_path.open("r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        assert rows[0]["prompt"] == "hello"
        assert rows[0]["notes"] == "test note"
        assert rows[0]["output"] == "world"

    def test_error_row_marked_with_error(self, tmp_path: Path) -> None:
        from backend.evals.eval_runner import _ERROR_MARKER

        results = []
        results.append(
            SimpleNamespace(
                input="ok",
                output="good",
                scores={"s": SimpleNamespace(score=1.0)},
            )
        )
        results.append(
            SimpleNamespace(
                input="fail",
                output=_ERROR_MARKER,
                scores={"s": None},
            )
        )
        eval_result = SimpleNamespace(results=results)

        from backend.evals.eval_runner import write_result_csv

        csv_path = write_result_csv(eval_result, "err", ["s"], tmp_path)

        with csv_path.open("r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        assert rows[0]["output"] == "good"
        assert rows[0]["score_s"] == "1.0"
        assert rows[1]["output"] == "ERROR"
        assert rows[1]["score_s"] == "ERROR"

    def test_scorer_error_marked_distinct_from_zero(self, tmp_path: Path) -> None:
        results = [
            SimpleNamespace(
                input="q",
                output="a",
                scores={"s1": SimpleNamespace(score=0.0), "s2": None},
            )
        ]
        eval_result = SimpleNamespace(results=results)

        from backend.evals.eval_runner import write_result_csv

        csv_path = write_result_csv(eval_result, "mix", ["s1", "s2"], tmp_path)

        with csv_path.open("r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        assert rows[0]["score_s1"] == "0.0"
        assert rows[0]["score_s2"] == "ERROR"


# ---------------------------------------------------------------------------
# run_scenario
# ---------------------------------------------------------------------------


class TestRunScenario:
    def _setup_scenario(
        self, tmp_path: Path, scenario_name: str = "test_scenario"
    ) -> tuple[Path, Path]:
        scenarios_dir = tmp_path / "scenarios"
        scenario_dir = scenarios_dir / scenario_name
        scenario_dir.mkdir(parents=True)

        spec = {
            "name": scenario_name,
            "csv": "dataset.csv",
            "task": {"function": "backend.evals.eval_tasks.run_v1"},
            "column_mapping": {"prompt": "input"},
            "scorers": [
                {
                    "name": "test_scorer",
                    "function": "backend.evals.scorers.language_policy_scorer.tool_arg_no_cjk",
                }
            ],
        }
        import yaml

        (scenario_dir / "eval_spec.yaml").write_text(yaml.dump(spec))

        csv_content = "prompt\nhello world\ngoodbye world\n"
        (scenario_dir / "dataset.csv").write_text(csv_content)

        return scenarios_dir, scenario_dir

    def _setup_diagnostic_scenario_contract_csv(
        self, tmp_path: Path, scenario_name: str = "near_v1_diagnostic"
    ) -> tuple[Path, Path]:
        scenarios_dir = tmp_path / "scenarios"
        scenario_dir = scenarios_dir / scenario_name
        scenario_dir.mkdir(parents=True)

        spec = {
            "name": scenario_name,
            "csv": "dataset.csv",
            "diagnostic": {
                "dataset_name": "near_v1_diagnostic",
                "dataset_version": "2026-04-24",
                "row_id_column": "id",
                "question_column": "question",
                "agent_version": "v1_baseline",
            },
            "task": {"function": "backend.evals.eval_tasks.run_near_v1_diagnostic"},
            "column_mapping": {"question": "input.question"},
            "scorers": [
                {
                    "name": "diagnostic_execution_health",
                    "function": "backend.evals.diagnostic.execution_scorer.execution_health",
                }
            ],
        }
        import yaml

        (scenario_dir / "eval_spec.yaml").write_text(yaml.dump(spec))
        (scenario_dir / "dataset.csv").write_text(
            "id,question,capability_band,category,expected_near_v1_behavior,"
            "primary_failure_mechanism,secondary_failure_mechanism,expected_best_source,"
            "likely_tuning_lever,draft_pass_signals\n"
            "1,First question,boundary,regulatory_or_legal_risk,may_pass_with_tuning,"
            'tool_routing_error,evidence_synthesis_limit,mixed,tool_description,"[""signal1""]"\n'
            "2,Second question,boundary,regulatory_or_legal_risk,may_pass_with_tuning,"
            'tool_routing_error,,mixed,tool_description,"[""signal2""]"\n'
        )

        return scenarios_dir, scenario_dir

    @patch("backend.evals.eval_runner.resolve_scorers")
    @patch("backend.evals.eval_runner.resolve_function")
    def test_run_scenario_local_produces_result_csv(
        self,
        mock_resolve_task: MagicMock,
        mock_resolve_scorers: MagicMock,
        tmp_path: Path,
    ) -> None:
        scenarios_dir, _ = self._setup_scenario(tmp_path)
        output_dir = tmp_path / "results"

        fake_task = MagicMock(return_value="fake response")
        mock_resolve_task.return_value = fake_task

        fake_scorer = MagicMock(return_value=0.9)
        fake_scorer.__name__ = "test_scorer"
        mock_resolve_scorers.return_value = [fake_scorer]

        from backend.evals.eval_runner import run_scenario

        result_path = run_scenario(
            "test_scenario",
            local_only=True,
            output_dir=output_dir,
            scenarios_dir=scenarios_dir,
        )

        assert result_path.exists()
        assert result_path.suffix == ".csv"

        with result_path.open("r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        assert len(rows) == 2
        assert reader.fieldnames is not None
        assert "prompt" in reader.fieldnames
        assert "output" in reader.fieldnames
        assert "score_test_scorer" in reader.fieldnames

    @patch("backend.evals.eval_runner.resolve_scorers")
    @patch("backend.evals.eval_runner.resolve_function")
    def test_run_scenario_local_does_not_import_braintrust(
        self,
        mock_resolve_task: MagicMock,
        mock_resolve_scorers: MagicMock,
        tmp_path: Path,
    ) -> None:
        """local_only=True must not attempt to import braintrust."""
        scenarios_dir, _ = self._setup_scenario(tmp_path)
        output_dir = tmp_path / "results"

        fake_task = MagicMock(return_value="fake response")
        mock_resolve_task.return_value = fake_task

        fake_scorer = MagicMock(return_value=0.5)
        fake_scorer.__name__ = "test_scorer"
        mock_resolve_scorers.return_value = [fake_scorer]

        import builtins

        original_import = builtins.__import__

        def _guarded_import(name: str, *args: Any, **kwargs: Any) -> Any:
            if name == "braintrust":
                raise ModuleNotFoundError("braintrust not installed")
            return original_import(name, *args, **kwargs)

        with patch("builtins.__import__", side_effect=_guarded_import):
            from backend.evals.eval_runner import run_scenario

            result_path = run_scenario(
                "test_scenario",
                local_only=True,
                output_dir=output_dir,
                scenarios_dir=scenarios_dir,
            )

        assert result_path.exists()

    @patch("backend.evals.eval_runner.resolve_scorers")
    @patch("backend.evals.eval_runner.resolve_function")
    def test_run_scenario_csv_not_found_raises(
        self,
        mock_resolve_task: MagicMock,
        mock_resolve_scorers: MagicMock,
        tmp_path: Path,
    ) -> None:
        scenarios_dir, scenario_dir = self._setup_scenario(tmp_path)
        (scenario_dir / "dataset.csv").unlink()

        from backend.evals.eval_runner import run_scenario

        with pytest.raises(FileNotFoundError, match="dataset.csv"):
            run_scenario(
                "test_scenario",
                local_only=True,
                output_dir=tmp_path / "results",
                scenarios_dir=scenarios_dir,
            )

    @patch("backend.evals.eval_runner.resolve_scorers")
    @patch("backend.evals.eval_runner.resolve_function")
    def test_run_scenario_bad_task_dotpath_raises(
        self,
        mock_resolve_task: MagicMock,
        mock_resolve_scorers: MagicMock,
        tmp_path: Path,
    ) -> None:
        scenarios_dir, _ = self._setup_scenario(tmp_path)
        mock_resolve_task.side_effect = ImportError("Could not import task")

        from backend.evals.eval_runner import run_scenario

        with pytest.raises(ImportError, match="import"):
            run_scenario(
                "test_scenario",
                local_only=True,
                output_dir=tmp_path / "results",
                scenarios_dir=scenarios_dir,
            )

    @patch("backend.evals.eval_runner.resolve_scorers")
    @patch("backend.evals.eval_runner.resolve_function")
    def test_run_scenario_rejects_diagnostic_flags_for_non_diagnostic_scenario_contract_csv(
        self,
        mock_resolve_task: MagicMock,
        mock_resolve_scorers: MagicMock,
        tmp_path: Path,
    ) -> None:
        scenarios_dir, _ = self._setup_scenario(tmp_path)
        mock_resolve_task.return_value = MagicMock(return_value="ok")
        fake_scorer = MagicMock(return_value=1.0)
        fake_scorer.__name__ = "test_scorer"
        mock_resolve_scorers.return_value = [fake_scorer]

        from backend.evals.eval_runner import run_scenario

        with pytest.raises(ValueError, match="Diagnostic flags"):
            run_scenario(
                "test_scenario",
                local_only=True,
                output_dir=tmp_path / "results",
                scenarios_dir=scenarios_dir,
                row_ids="1,2",
            )

    @patch("backend.evals.eval_runner.resolve_git_commit", return_value="12f85db")
    @patch("backend.evals.eval_runner.resolve_scorers")
    @patch("backend.evals.eval_runner.resolve_function")
    def test_run_scenario_diagnostic_local_only_runs_selected_rows_and_aligns_csv_contract_csv(
        self,
        mock_resolve_task: MagicMock,
        mock_resolve_scorers: MagicMock,
        mock_resolve_git_commit: MagicMock,
        tmp_path: Path,
    ) -> None:
        scenarios_dir, _ = self._setup_diagnostic_scenario_contract_csv(tmp_path)
        output_dir = tmp_path / "results"

        def fake_task(input: Any) -> dict[str, Any]:
            assert isinstance(input, dict)
            return {"response": input["question"].upper()}

        mock_resolve_task.return_value = fake_task

        fake_scorer = MagicMock(return_value=1.0)
        fake_scorer.__name__ = "diagnostic_execution_health"
        mock_resolve_scorers.return_value = [fake_scorer]

        from backend.evals.eval_runner import run_scenario

        result_path = run_scenario(
            "near_v1_diagnostic",
            local_only=True,
            output_dir=output_dir,
            scenarios_dir=scenarios_dir,
            run_label="slice-run",
            run_group="nightly",
            agent_version="v1_override",
            row_ids="2,1",
        )

        with result_path.open("r", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            rows = list(reader)

        assert [row["id"] for row in rows] == ["2", "1"]
        assert [row["question"] for row in rows] == [
            "Second question",
            "First question",
        ]
        assert [row["output.response"] for row in rows] == [
            "SECOND QUESTION",
            "FIRST QUESTION",
        ]

    @patch("backend.evals.eval_runner.resolve_git_commit", return_value="12f85db")
    @patch("backend.evals.eval_runner._init_platform_tracing")
    @patch("backend.evals.eval_runner._run_local_eval")
    @patch("backend.evals.eval_runner.resolve_scorers")
    @patch("backend.evals.eval_runner.resolve_function")
    def test_run_scenario_diagnostic_platform_uses_eval_once_and_writes_manifest_contract_csv(
        self,
        mock_resolve_task: MagicMock,
        mock_resolve_scorers: MagicMock,
        mock_run_local_eval: MagicMock,
        mock_init_platform_tracing: MagicMock,
        mock_resolve_git_commit: MagicMock,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        scenarios_dir, _ = self._setup_diagnostic_scenario_contract_csv(tmp_path)
        output_dir = tmp_path / "results"
        monkeypatch.setenv("BRAINTRUST_API_KEY", "test-key")

        fake_task = MagicMock(return_value={"response": "ok"})
        mock_resolve_task.return_value = fake_task
        fake_scorer = MagicMock(return_value=1.0)
        fake_scorer.__name__ = "diagnostic_execution_health"
        mock_resolve_scorers.return_value = [fake_scorer]
        mock_run_local_eval.side_effect = AssertionError(
            "diagnostic platform mode must not pre-run local eval"
        )

        eval_calls: list[dict[str, Any]] = []

        class FakeEvalCase:
            def __init__(
                self,
                *,
                input: Any,
                expected: Any = None,
                metadata: Any = None,
                id: str | None = None,
            ) -> None:
                self.input = input
                self.expected = expected
                self.metadata = metadata
                self.id = id

        def fake_eval(project: str, **kwargs: Any) -> SimpleNamespace:
            eval_calls.append({"project": project, **kwargs})
            return SimpleNamespace(results=[], summary=SimpleNamespace())

        braintrust_module = ModuleType("braintrust")
        setattr(braintrust_module, "Eval", fake_eval)
        setattr(braintrust_module, "EvalCase", FakeEvalCase)
        setattr(braintrust_module, "flush", MagicMock())

        monkeypatch.setitem(sys.modules, "braintrust", braintrust_module)

        from backend.evals.eval_runner import run_scenario

        result_path = run_scenario(
            "near_v1_diagnostic",
            local_only=False,
            output_dir=output_dir,
            scenarios_dir=scenarios_dir,
            run_label="slice-run",
            run_group="nightly",
            agent_version="v1_override",
            slice_label="focused-boundary",
            row_ids="2",
        )

        assert result_path.exists()
        assert len(eval_calls) == 1
        assert mock_run_local_eval.call_count == 0
        mock_init_platform_tracing.assert_called_once()

        eval_call = eval_calls[0]
        assert eval_call["project"] == "finlab-x"
        assert eval_call["experiment_name"].startswith("near_v1_diagnostic_")
        assert eval_call["metadata"]["dataset_name"] == "near_v1_diagnostic"
        assert eval_call["metadata"]["dataset_version"] == "2026-04-24"
        assert eval_call["metadata"]["run_label"] == "slice-run"
        assert eval_call["metadata"]["run_group"] == "nightly"
        assert eval_call["metadata"]["slice_label"] == "focused-boundary"
        assert eval_call["metadata"]["slice_type"] == "row_ids"
        assert eval_call["metadata"]["selected_row_count"] == 1
        assert eval_call["metadata"]["agent_version"] == "v1_override"
        assert eval_call["metadata"]["git_commit"] == "12f85db"

        eval_cases = eval_call["data"]
        assert len(eval_cases) == 1
        assert eval_cases[0].id == "2"
        assert eval_cases[0].metadata["row_id"] == "2"
        assert eval_cases[0].metadata["run_label"] == "slice-run"
        assert eval_cases[0].metadata["slice_label"] == "focused-boundary"

        with result_path.open("r", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            rows = list(reader)

        assert reader.fieldnames is not None
        assert "output.response" not in reader.fieldnames
        assert len(rows) == 1
        assert rows[0]["row_id"] == "2"
        assert rows[0]["session_id"] == "near_v1_diagnostic::slice-run::2"
        assert rows[0]["experiment_name"] == eval_call["experiment_name"]
        assert rows[0]["run_label"] == "slice-run"
        assert rows[0]["dataset_version"] == "2026-04-24"
        assert rows[0]["slice_label"] == "focused-boundary"
        assert rows[0]["slice_type"] == "row_ids"
        assert rows[0]["selected_row_ids"] == '["2"]'
        assert rows[0]["git_commit"] == "12f85db"
        assert rows[0]["braintrust_project"] == "finlab-x"

    def _setup_diagnostic_scenario(
        self, tmp_path: Path, scenario_name: str = "near_v1_diagnostic"
    ) -> tuple[Path, Path]:
        scenarios_dir = tmp_path / "scenarios"
        scenario_dir = scenarios_dir / scenario_name
        scenario_dir.mkdir(parents=True)

        spec = {
            "name": scenario_name,
            "csv": "dataset.csv",
            "diagnostic": {
                "dataset_name": scenario_name,
                "dataset_version": "2026-04-24",
                "row_id_column": "id",
                "question_column": "question",
                "agent_version": "v1_baseline",
            },
            "task": {"function": "backend.evals.eval_tasks.run_near_v1_diagnostic"},
            "column_mapping": {"question": "input.question"},
            "scorers": [{"name": "diagnostic_execution_health", "function": "x.y"}],
        }
        import yaml

        (scenario_dir / "eval_spec.yaml").write_text(yaml.dump(spec))
        (scenario_dir / "dataset.csv").write_text(
            "\n".join(
                [
                    "id,question,category,capability_band,expected_near_v1_behavior,primary_failure_mechanism,secondary_failure_mechanism,expected_best_source,likely_tuning_lever,draft_pass_signals",
                    '1,"First question",news,core,should_pass,tool_routing_error,,SEC,none,"[""a""]"',
                    '2,"Second question",news,boundary,may_pass_with_tuning,tool_routing_error,evidence_synthesis_limit,mixed,max_tool_calls,"[""b""]"',
                ]
            )
            + "\n"
        )
        return scenarios_dir, scenario_dir

    def test_run_scenario_rejects_diagnostic_flags_for_non_diagnostic_scenario(
        self,
        tmp_path: Path,
    ) -> None:
        scenarios_dir, _ = self._setup_scenario(tmp_path)

        from backend.evals.eval_runner import run_scenario

        with pytest.raises(ValueError, match="Diagnostic flags are only supported"):
            run_scenario(
                "test_scenario",
                local_only=True,
                output_dir=tmp_path / "results",
                scenarios_dir=scenarios_dir,
                row_ids="1,2",
            )

    @patch("backend.evals.eval_runner.resolve_git_commit", return_value="abc1234")
    @patch("backend.evals.eval_runner.resolve_scorers")
    @patch("backend.evals.eval_runner.resolve_function")
    def test_run_scenario_diagnostic_local_only_runs_selected_rows_and_writes_result_csv(
        self,
        mock_resolve_task: MagicMock,
        mock_resolve_scorers: MagicMock,
        mock_git_commit: MagicMock,
        tmp_path: Path,
    ) -> None:
        scenarios_dir, _ = self._setup_diagnostic_scenario(tmp_path)

        task_calls: list[dict[str, Any]] = []

        def fake_task(input: Any) -> Any:
            task_calls.append(input)
            return {"response": f"handled {input['question']}"}

        fake_scorer = MagicMock(return_value=1.0)
        fake_scorer.__name__ = "diagnostic_execution_health"
        mock_resolve_task.return_value = fake_task
        mock_resolve_scorers.return_value = [fake_scorer]

        from backend.evals.eval_runner import run_scenario

        result_path = run_scenario(
            "near_v1_diagnostic",
            local_only=True,
            output_dir=tmp_path / "results",
            scenarios_dir=scenarios_dir,
            run_label="baseline",
            run_group="near-v1",
            row_ids="2",
        )

        with result_path.open("r", encoding="utf-8") as file:
            rows = list(csv.DictReader(file))

        assert len(rows) == 1
        assert rows[0]["id"] == "2"
        assert len(task_calls) == 1
        assert task_calls[0]["question"] == "Second question"
        assert task_calls[0]["session_id"] == "near_v1_diagnostic::baseline::2"
        trace_metadata = task_calls[0]["trace_metadata"]
        assert trace_metadata["row_id"] == "2"
        assert trace_metadata["slice_label"] == "rows-2"
        assert trace_metadata["slice_type"] == "row_ids"
        assert trace_metadata["slice_selector"] == "2"
        assert trace_metadata["reference_best_source"] == "mixed"
        assert trace_metadata["reference_pass_signals"] == ["b"]
        assert trace_metadata["experiment_name"].startswith("near_v1_diagnostic_")

    @patch("backend.evals.eval_runner.resolve_git_commit", return_value="abc1234")
    @patch("backend.evals.eval_runner.write_diagnostic_run_manifest")
    @patch("backend.evals.eval_runner._init_platform_tracing")
    @patch("backend.evals.eval_runner._run_local_eval")
    @patch("backend.evals.eval_runner.resolve_scorers")
    @patch("backend.evals.eval_runner.resolve_function")
    def test_run_scenario_diagnostic_platform_mode_uses_eval_once_and_writes_manifest(
        self,
        mock_resolve_task: MagicMock,
        mock_resolve_scorers: MagicMock,
        mock_run_local_eval: MagicMock,
        mock_init_tracing: MagicMock,
        mock_write_manifest: MagicMock,
        mock_git_commit: MagicMock,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        scenarios_dir, _ = self._setup_diagnostic_scenario(tmp_path)
        mock_resolve_task.return_value = MagicMock(return_value={"response": "ok"})
        fake_scorer = MagicMock(return_value=1.0)
        fake_scorer.__name__ = "diagnostic_execution_health"
        mock_resolve_scorers.return_value = [fake_scorer]
        mock_write_manifest.return_value = tmp_path / "results" / "manifest.csv"

        eval_calls: list[dict[str, Any]] = []
        eval_cases: list[dict[str, Any]] = []
        flushed: list[bool] = []

        class FakeEvalCase:
            def __init__(self, **kwargs: Any) -> None:
                eval_cases.append(kwargs)

        fake_braintrust = SimpleNamespace(
            Eval=lambda *args, **kwargs: eval_calls.append(
                {"args": args, "kwargs": kwargs}
            ),
            EvalCase=FakeEvalCase,
            flush=lambda: flushed.append(True),
        )

        monkeypatch.setitem(sys.modules, "braintrust", fake_braintrust)
        monkeypatch.setenv("BRAINTRUST_API_KEY", "test-key")

        with patch(
            "backend.evals.eval_runner.load_braintrust_config",
            return_value=SimpleNamespace(
                project="finlab-x",
                api_key_env="BRAINTRUST_API_KEY",
                local_mode=False,
            ),
        ):
            from backend.evals.eval_runner import run_scenario

            result_path = run_scenario(
                "near_v1_diagnostic",
                local_only=False,
                output_dir=tmp_path / "results",
                scenarios_dir=scenarios_dir,
                run_label="baseline",
                run_group="near-v1",
                row_ids="2",
            )

        assert result_path == tmp_path / "results" / "manifest.csv"
        mock_run_local_eval.assert_not_called()
        assert len(eval_calls) == 1
        assert len(eval_cases) == 1
        assert eval_cases[0]["id"] == "2"
        assert eval_cases[0]["metadata"]["row_id"] == "2"
        assert (
            eval_calls[0]["kwargs"]["metadata"]["dataset_name"] == "near_v1_diagnostic"
        )
        assert eval_calls[0]["kwargs"]["metadata"]["selected_row_count"] == 1
        manifest_rows = mock_write_manifest.call_args.kwargs["manifest_rows"]
        assert manifest_rows == [
            {
                "row_id": "2",
                "session_id": "near_v1_diagnostic::baseline::2",
                "experiment_name": eval_calls[0]["kwargs"]["experiment_name"],
                "run_label": "baseline",
                "dataset_version": "2026-04-24",
                "slice_label": "rows-2",
                "slice_type": "row_ids",
                "selected_row_ids": ["2"],
                "git_commit": "abc1234",
                "braintrust_project": "finlab-x",
            }
        ]
        assert flushed == [True]


# ---------------------------------------------------------------------------
# main CLI
# ---------------------------------------------------------------------------


class TestMainCli:
    @patch("backend.evals.eval_runner.run_scenario")
    def test_main_forwards_diagnostic_cli_flags(
        self,
        mock_run_scenario: MagicMock,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        scenarios_dir = tmp_path / "scenarios"
        scenario_dir = scenarios_dir / "near_v1_diagnostic"
        scenario_dir.mkdir(parents=True)
        (scenario_dir / "eval_spec.yaml").write_text("name: near_v1_diagnostic\n")
        mock_run_scenario.return_value = tmp_path / "results" / "manifest.csv"

        from backend.evals.eval_runner import main

        main(
            [
                "near_v1_diagnostic",
                "--run-label",
                "slice-run",
                "--run-group",
                "nightly",
                "--agent-version",
                "v1_override",
                "--slice-label",
                "focused-boundary",
                "--row-ids",
                "2,1",
            ],
            scenarios_dir=scenarios_dir,
            output_dir=tmp_path / "results",
        )

        kwargs = mock_run_scenario.call_args.kwargs
        assert kwargs["run_label"] == "slice-run"
        assert kwargs["run_group"] == "nightly"
        assert kwargs["agent_version"] == "v1_override"
        assert kwargs["slice_label"] == "focused-boundary"
        assert kwargs["row_ids"] == "2,1"

    def test_nonexistent_scenario_exits_nonzero(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        scenarios_dir = tmp_path / "scenarios"
        scenarios_dir.mkdir()
        valid = scenarios_dir / "existing_one"
        valid.mkdir()
        (valid / "eval_spec.yaml").write_text("name: existing_one\n")

        from backend.evals.eval_runner import main

        with pytest.raises(SystemExit) as exc_info:
            main(
                ["nonexistent"],
                scenarios_dir=scenarios_dir,
                output_dir=tmp_path / "results",
            )

        assert exc_info.value.code != 0
        captured = capsys.readouterr()
        assert "existing_one" in captured.err

    def test_all_flag_empty_scenarios_prints_message(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        scenarios_dir = tmp_path / "scenarios"
        scenarios_dir.mkdir()

        from backend.evals.eval_runner import main

        with pytest.raises(SystemExit) as exc_info:
            main(
                ["--all"],
                scenarios_dir=scenarios_dir,
                output_dir=tmp_path / "results",
            )

        assert exc_info.value.code != 0
        captured = capsys.readouterr()
        assert "no scenarios found" in captured.err.lower()

    @patch("backend.evals.eval_runner.run_scenario")
    def test_all_flag_warns_on_duplicate_config_names(
        self,
        mock_run: MagicMock,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        import yaml

        scenarios_dir = tmp_path / "scenarios"
        for dir_name in ["v1_quality", "v2_quality"]:
            d = scenarios_dir / dir_name
            d.mkdir(parents=True)
            spec = {
                "name": "response_quality",
                "csv": "dataset.csv",
                "task": {"function": "backend.evals.eval_tasks.run_v1"},
                "column_mapping": {"prompt": "input"},
                "scorers": [{"name": "s", "function": "some.func"}],
            }
            (d / "eval_spec.yaml").write_text(yaml.dump(spec))

        mock_run.side_effect = [
            tmp_path / "results" / "r1.csv",
            tmp_path / "results" / "r2.csv",
        ]

        from backend.evals.eval_runner import main

        with patch("backend.evals.eval_runner.logger") as mock_logger:
            main(
                ["--all"],
                scenarios_dir=scenarios_dir,
                output_dir=tmp_path / "results",
            )

            mock_logger.warning.assert_called_once()
            warning_args = mock_logger.warning.call_args
            assert "response_quality" in str(warning_args)

    @patch("backend.evals.eval_runner.run_scenario")
    def test_all_flag_skips_invalid_and_reports_summary(
        self,
        mock_run: MagicMock,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        scenarios_dir = tmp_path / "scenarios"
        for name in ["good_one", "bad_one"]:
            d = scenarios_dir / name
            d.mkdir(parents=True)
            (d / "eval_spec.yaml").write_text(f"name: {name}\n")

        mock_run.side_effect = [
            tmp_path / "results" / "good_one_result.csv",
            ValueError("bad scenario config"),
        ]

        from backend.evals.eval_runner import main

        main(
            ["--all"],
            scenarios_dir=scenarios_dir,
            output_dir=tmp_path / "results",
        )

        captured = capsys.readouterr()
        assert "1 succeeded" in captured.out
        assert "1 skipped" in captured.out


# ---------------------------------------------------------------------------
# _wrap_task
# ---------------------------------------------------------------------------


class TestWrapTask:
    def test_task_returning_none_returns_error_marker(self) -> None:
        from backend.evals.eval_runner import _ERROR_MARKER, _wrap_task

        def bad_task(input: Any) -> None:
            return None

        wrapped = _wrap_task(bad_task)
        result = wrapped("test")
        assert result == _ERROR_MARKER

    def test_task_exception_returns_error_marker(self) -> None:
        from backend.evals.eval_runner import _ERROR_MARKER, _wrap_task

        def crashing_task(input: Any) -> str:
            raise TimeoutError("timed out")

        wrapped = _wrap_task(crashing_task)
        result = wrapped("test")
        assert result == _ERROR_MARKER

    def test_task_normal_return_passes_through(self) -> None:
        from backend.evals.eval_runner import _wrap_task

        def ok_task(input: Any) -> str:
            return "result"

        wrapped = _wrap_task(ok_task)
        assert wrapped("test") == "result"


# ---------------------------------------------------------------------------
# _wrap_scorer
# ---------------------------------------------------------------------------


class TestWrapScorer:
    def test_scorer_crash_returns_none(self) -> None:
        from backend.evals.eval_runner import _wrap_scorer

        def bad_scorer(*, output: Any, expected: Any, **kw: Any) -> float:
            raise RuntimeError("boom")

        wrapped = _wrap_scorer(bad_scorer, "bad")
        result = wrapped(output="a", expected="b")
        assert result is None

    def test_scorer_normal_return_passes_through(self) -> None:
        from backend.evals.eval_runner import _wrap_scorer

        def ok_scorer(*, output: Any, expected: Any, **kw: Any) -> float:
            return 0.5

        wrapped = _wrap_scorer(ok_scorer, "ok")
        assert wrapped(output="a", expected="b") == 0.5

    def test_scorer_skipped_on_error_row(self) -> None:
        from backend.evals.eval_runner import _ERROR_MARKER, _wrap_scorer

        call_count = 0

        def counting_scorer(*, output: Any, expected: Any, **kw: Any) -> float:
            nonlocal call_count
            call_count += 1
            return 1.0

        wrapped = _wrap_scorer(counting_scorer, "cnt")
        result = wrapped(output=_ERROR_MARKER, expected="b")
        assert result is None
        assert call_count == 0

    def test_diagnostic_scorer_runs_on_error_row(self) -> None:
        from backend.evals.diagnostic.execution_scorer import execution_health
        from backend.evals.eval_runner import _ERROR_MARKER, _wrap_scorer

        wrapped = _wrap_scorer(execution_health, "diagnostic_execution_health")
        result = wrapped(output=_ERROR_MARKER, expected={})

        assert result is not None
        assert result["score"] == 0.0
        assert result["metadata"]["execution_complete"] is False

    def test_extra_kwargs_filtered_for_strict_scorer(self) -> None:
        """V-5.1 regression: scorers without **kwargs must not receive extra
        keyword arguments like ``metadata`` that Braintrust passes."""
        from backend.evals.eval_runner import _wrap_scorer

        def strict_scorer(*, output: Any, expected: Any, input: Any) -> float:
            return 1.0

        wrapped = _wrap_scorer(strict_scorer, "strict")
        # Simulate Braintrust passing metadata kwarg
        result = wrapped(output="a", expected="b", input="q", metadata={"row_id": 1})
        assert result == 1.0

    def test_extra_kwargs_forwarded_for_permissive_scorer(self) -> None:
        """Scorers that accept **kwargs should still receive all extra kwargs."""
        from backend.evals.eval_runner import _wrap_scorer

        received: dict[str, Any] = {}

        def permissive_scorer(*, output: Any, expected: Any, **kw: Any) -> float:
            received.update(kw)
            return 0.9

        wrapped = _wrap_scorer(permissive_scorer, "permissive")
        result = wrapped(output="a", expected="b", input="q", metadata={"row_id": 1})
        assert result == 0.9
        assert received["metadata"] == {"row_id": 1}
        assert received["input"] == "q"

    def test_real_scorer_resilient_to_metadata_kwarg(self) -> None:
        """V-5.1 regression: real language_policy scorers must not crash when
        Braintrust passes ``metadata``."""
        from backend.evals.eval_runner import _wrap_scorer
        from backend.evals.scorers.language_policy_scorer import (
            response_language,
            tool_arg_no_cjk,
        )

        wrapped_tool = _wrap_scorer(tool_arg_no_cjk, "tool_arg_no_cjk")
        result = wrapped_tool(
            output={"response": "hello", "tool_outputs": []},
            expected={"search_query_no_cjk": True, "tool": "search"},
            input="What is AAPL?",
            metadata={"row_id": 42},
        )
        assert result is not None

        wrapped_lang = _wrap_scorer(response_language, "response_language")
        result = wrapped_lang(
            output={"response": "這是中文回應"},
            expected={"cjk_min": 0.5, "cjk_max": 1.0},
            input="用中文回答",
            metadata={"row_id": 99},
        )
        assert result is not None


# ---------------------------------------------------------------------------
# _filter_kwargs_for
# ---------------------------------------------------------------------------


class TestFilterKwargsFor:
    def test_filters_out_unknown_kwargs(self) -> None:
        from backend.evals.eval_runner import _filter_kwargs_for

        def fn(*, output: Any, expected: Any, input: Any) -> float:
            return 1.0

        result = _filter_kwargs_for(
            fn, {"input": "q", "metadata": {"id": 1}, "extra": True}
        )
        assert result == {"input": "q"}

    def test_passes_all_when_var_keyword_present(self) -> None:
        from backend.evals.eval_runner import _filter_kwargs_for

        def fn(*, output: Any, expected: Any, **kw: Any) -> float:
            return 1.0

        kwargs = {"input": "q", "metadata": {"id": 1}}
        result = _filter_kwargs_for(fn, kwargs)
        assert result == kwargs

    def test_empty_kwargs_returns_empty(self) -> None:
        from backend.evals.eval_runner import _filter_kwargs_for

        def fn(*, output: Any, expected: Any) -> float:
            return 1.0

        assert _filter_kwargs_for(fn, {}) == {}


# ---------------------------------------------------------------------------
# _convert_cell precision
# ---------------------------------------------------------------------------


class TestConvertCellPrecision:
    def test_converts_trailing_zero(self) -> None:
        from backend.evals.dataset_loader import _convert_cell

        assert _convert_cell("3.10") == 3.1

    def test_converts_leading_zero(self) -> None:
        from backend.evals.dataset_loader import _convert_cell

        assert _convert_cell("001") == 1.0

    def test_converts_normal_float(self) -> None:
        from backend.evals.dataset_loader import _convert_cell

        assert _convert_cell("0.8") == 0.8

    def test_converts_integer_string(self) -> None:
        from backend.evals.dataset_loader import _convert_cell

        assert _convert_cell("12") == 12.0


# ---------------------------------------------------------------------------
# _run_local_eval – input forwarding regression
# ---------------------------------------------------------------------------


class TestRunLocalEvalInputForwarding:
    """Regression tests for B-3.1: local-only must pass `input` to scorers."""

    def test_local_eval_passes_input_to_scorer(self) -> None:
        """Scorer receiving `input` keyword must not raise TypeError."""
        from backend.evals.eval_runner import _run_local_eval

        def task_fn(inp: Any) -> str:
            return "output"

        received_inputs: list[Any] = []

        def scorer_needing_input(
            *, output: Any, expected: Any, input: Any, **kw: Any
        ) -> float:
            received_inputs.append(input)
            return 1.0

        scorer_needing_input.__name__ = "needs_input"

        raw_data = [{"input": "hello", "expected": "world"}]
        result = _run_local_eval(raw_data, task_fn, [scorer_needing_input])

        assert len(result.results) == 1
        assert received_inputs == ["hello"]
        assert result.results[0].scores["needs_input"] == 1.0

    def test_local_eval_with_real_scorer_no_error(self) -> None:
        """Real scorer (tool_arg_no_cjk) must produce valid score, not ERROR."""
        from backend.evals.eval_runner import (
            _ERROR_MARKER,
            _run_local_eval,
            _wrap_scorer,
        )
        from backend.evals.scorers.language_policy_scorer import tool_arg_no_cjk

        wrapped = _wrap_scorer(tool_arg_no_cjk, "tool_arg_no_cjk")

        def task_fn(inp: Any) -> dict[str, Any]:
            return {"response": "hello world", "tool_outputs": []}

        raw_data = [
            {
                "input": "What is AAPL?",
                "expected": {"search_query_no_cjk": True, "tool": "search"},
            },
        ]
        result = _run_local_eval(raw_data, task_fn, [wrapped])

        score_val = result.results[0].scores["tool_arg_no_cjk"]
        assert score_val != _ERROR_MARKER, "Scorer should not produce ERROR"
        assert isinstance(score_val, (int, float))
        assert score_val == 1.0

    def test_local_eval_diagnostic_scorer_observes_error_row(self) -> None:
        from backend.evals.diagnostic.execution_scorer import execution_health
        from backend.evals.eval_runner import _run_local_eval, _wrap_scorer, _wrap_task

        def task_fn(inp: Any) -> str:
            raise RuntimeError("boom")

        raw_data = [{"input": {"question": "UNH 發生什麼事？"}, "expected": {}}]
        result = _run_local_eval(
            raw_data,
            _wrap_task(task_fn),
            [_wrap_scorer(execution_health, "diagnostic_execution_health")],
        )

        score_val = result.results[0].scores["diagnostic_execution_health"]
        assert isinstance(score_val, dict)
        assert score_val["score"] == 0.0
        assert score_val["metadata"]["execution_complete"] is False
