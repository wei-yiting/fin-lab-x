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
        assert "prompt" in reader.fieldnames
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

        import logging

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


# ---------------------------------------------------------------------------
# _convert_cell precision
# ---------------------------------------------------------------------------


class TestConvertCellPrecision:
    def test_preserves_trailing_zero(self) -> None:
        from backend.evals.dataset_loader import _convert_cell

        assert _convert_cell("3.10") == "3.10"

    def test_preserves_leading_zero(self) -> None:
        from backend.evals.dataset_loader import _convert_cell

        assert _convert_cell("001") == "001"

    def test_converts_normal_float(self) -> None:
        from backend.evals.dataset_loader import _convert_cell

        assert _convert_cell("0.8") == 0.8

    def test_converts_integer_string(self) -> None:
        from backend.evals.dataset_loader import _convert_cell

        assert _convert_cell("12") == 12.0
