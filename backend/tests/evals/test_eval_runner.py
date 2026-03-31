"""Tests for the eval runner: scenario discovery, execution, and result CSV output."""

import csv
import time
from pathlib import Path
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
            eval_result, "test_scenario", ["accuracy", "relevance"], tmp_path
        )

        assert csv_path.exists()
        with csv_path.open("r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        assert len(rows) == 1
        assert rows[0]["input"] == "hello"
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

    def test_dict_input_is_serialized(self, tmp_path: Path) -> None:
        eval_result = _make_eval_result(
            [
                {
                    "input": {"prompt": "hello", "context": "world"},
                    "output": "response",
                    "scores": {"s": 1.0},
                },
            ],
            ["s"],
        )

        from backend.evals.eval_runner import write_result_csv

        csv_path = write_result_csv(eval_result, "dict_input", ["s"], tmp_path)

        with csv_path.open("r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        import json

        parsed = json.loads(rows[0]["input"])
        assert parsed == {"prompt": "hello", "context": "world"}

    def test_dict_output_extracts_response(self, tmp_path: Path) -> None:
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

        assert rows[0]["output"] == "answer text"

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

    @patch("backend.evals.eval_runner.Eval")
    @patch("backend.evals.eval_runner.resolve_scorers")
    @patch("backend.evals.eval_runner.resolve_function")
    def test_run_scenario_local_produces_result_csv(
        self,
        mock_resolve_task: MagicMock,
        mock_resolve_scorers: MagicMock,
        mock_eval: MagicMock,
        tmp_path: Path,
    ) -> None:
        scenarios_dir, _ = self._setup_scenario(tmp_path)
        output_dir = tmp_path / "results"

        fake_task = MagicMock(return_value="fake response")
        mock_resolve_task.return_value = fake_task

        fake_scorer = MagicMock()
        mock_resolve_scorers.return_value = [fake_scorer]

        mock_eval.return_value = _make_eval_result(
            [
                {
                    "input": "hello world",
                    "output": "fake response",
                    "scores": {"test_scorer": 1.0},
                },
                {
                    "input": "goodbye world",
                    "output": "fake response",
                    "scores": {"test_scorer": 0.8},
                },
            ],
            ["test_scorer"],
        )

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
        assert "input" in reader.fieldnames
        assert "output" in reader.fieldnames
        assert "score_test_scorer" in reader.fieldnames

        mock_eval.assert_called_once()
        call_kwargs = mock_eval.call_args
        assert call_kwargs.kwargs["no_send_logs"] is True

    @patch("backend.evals.eval_runner.Eval")
    @patch("backend.evals.eval_runner.resolve_scorers")
    @patch("backend.evals.eval_runner.resolve_function")
    def test_run_scenario_csv_not_found_raises(
        self,
        mock_resolve_task: MagicMock,
        mock_resolve_scorers: MagicMock,
        mock_eval: MagicMock,
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

    @patch("backend.evals.eval_runner.Eval")
    @patch("backend.evals.eval_runner.resolve_scorers")
    @patch("backend.evals.eval_runner.resolve_function")
    def test_run_scenario_bad_task_dotpath_raises(
        self,
        mock_resolve_task: MagicMock,
        mock_resolve_scorers: MagicMock,
        mock_eval: MagicMock,
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


# ---------------------------------------------------------------------------
# main CLI
# ---------------------------------------------------------------------------


class TestMainCli:
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
