"""Tests for the eval runner: scenario discovery, execution, and result CSV output."""

import asyncio
import csv
import json
import subprocess
import threading
import time
from pathlib import Path
from types import SimpleNamespace
from typing import Any
from unittest.mock import MagicMock, patch

import pytest


def _make_eval_result(
    rows: list[dict[str, Any]], scorer_names: list[str]
) -> SimpleNamespace:
    """Build a fake Eval() result with .results and .summary.

    Mirrors the real ``EvalResult`` shape: ``scores`` values are plain
    ``float | None`` (never wrapped), and ``error``/``metadata`` are always
    present, defaulting to the no-error/no-metadata case unless overridden
    via the row dict's ``error``/``metadata`` keys.
    """
    results = []
    for row in rows:
        scores = {name: row["scores"][name] for name in scorer_names}
        results.append(
            SimpleNamespace(
                input=row["input"],
                output=row["output"],
                scores=scores,
                error=row.get("error"),
                metadata=row.get("metadata", {}),
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
        """A task exception (EvalResult.error set) marks the whole row ERROR."""
        results = [
            SimpleNamespace(
                input="ok", output="good", scores={"s": 1.0}, error=None, metadata={}
            ),
            SimpleNamespace(
                input="fail",
                output=None,
                scores={},
                error=RuntimeError("boom"),
                metadata={},
            ),
        ]
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

    def test_scorer_skip_marked_as_skipped(self, tmp_path: Path) -> None:
        """A scorer deliberately returning None (no crash) writes SKIPPED."""
        eval_result = _make_eval_result(
            [{"input": "q", "output": "a", "scores": {"s1": 0.0, "s2": None}}],
            ["s1", "s2"],
        )

        from backend.evals.eval_runner import write_result_csv

        csv_path = write_result_csv(eval_result, "mix", ["s1", "s2"], tmp_path)

        with csv_path.open("r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        assert rows[0]["score_s1"] == "0.0"
        assert rows[0]["score_s2"] == "SKIPPED"

    def test_scorer_crash_marked_as_error(self, tmp_path: Path) -> None:
        """A scorer recorded in metadata.scorer_errors (crashed) writes ERROR,
        distinct from a deliberate skip even though both leave scores[name] absent."""
        eval_result = _make_eval_result(
            [
                {
                    "input": "q",
                    "output": "a",
                    "scores": {"s1": 0.0, "s2": None},
                    "metadata": {
                        "scorer_errors": {"s2": "Traceback...\nValueError: boom"}
                    },
                }
            ],
            ["s1", "s2"],
        )

        from backend.evals.eval_runner import write_result_csv

        csv_path = write_result_csv(eval_result, "mix", ["s1", "s2"], tmp_path)

        with csv_path.open("r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        assert rows[0]["score_s1"] == "0.0"
        assert rows[0]["score_s2"] == "ERROR"

    def test_output_json_column_serializes_full_output(self, tmp_path: Path) -> None:
        eval_result = _make_eval_result(
            [
                {
                    "input": "q",
                    "output": {"response": "answer", "tool_outputs": [{"a": 1}]},
                    "scores": {"s": 1.0},
                }
            ],
            ["s"],
        )

        from backend.evals.eval_runner import write_result_csv

        csv_path = write_result_csv(eval_result, "replay", ["s"], tmp_path)

        with csv_path.open("r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        assert json.loads(rows[0]["output_json"]) == {
            "response": "answer",
            "tool_outputs": [{"a": 1}],
        }

    def test_output_json_empty_on_error_row(self, tmp_path: Path) -> None:
        """output_json's contract is replay source-of-truth; an error row leaves
        it empty rather than smuggling a traceback into a would-be-JSON column."""
        results = [
            SimpleNamespace(
                input="fail",
                output=None,
                scores={},
                error=RuntimeError("boom"),
                metadata={},
            ),
        ]
        eval_result = SimpleNamespace(results=results)

        from backend.evals.eval_runner import write_result_csv

        csv_path = write_result_csv(eval_result, "err", [], tmp_path)

        with csv_path.open("r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        assert rows[0]["output_json"] == ""

    def test_experiment_name_and_git_sha_columns_written(self, tmp_path: Path) -> None:
        eval_result = _make_eval_result(
            [{"input": "x", "output": "y", "scores": {"s": 1.0}}],
            ["s"],
        )

        from backend.evals.eval_runner import write_result_csv

        csv_path = write_result_csv(
            eval_result,
            "sc",
            ["s"],
            tmp_path,
            experiment_name="sc_20260728_000000",
            git_sha="abc1234-dirty",
        )

        with csv_path.open("r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        assert rows[0]["experiment_name"] == "sc_20260728_000000"
        assert rows[0]["git_sha"] == "abc1234-dirty"
        # provenance columns repeat per row with a constant value
        assert all(r["git_sha"] == "abc1234-dirty" for r in rows)


# ---------------------------------------------------------------------------
# _git_sha
# ---------------------------------------------------------------------------


class TestGitSha:
    @patch("backend.evals.eval_runner.subprocess.run")
    def test_clean_tree_returns_bare_sha(self, mock_run: MagicMock) -> None:
        from backend.evals.eval_runner import _git_sha

        mock_run.side_effect = [
            SimpleNamespace(stdout="abc1234\n"),
            SimpleNamespace(stdout=""),
        ]
        assert _git_sha() == "abc1234"

    @patch("backend.evals.eval_runner.subprocess.run")
    def test_dirty_tree_appends_suffix(self, mock_run: MagicMock) -> None:
        from backend.evals.eval_runner import _git_sha

        mock_run.side_effect = [
            SimpleNamespace(stdout="abc1234\n"),
            SimpleNamespace(stdout=" M backend/evals/eval_runner.py\n"),
        ]
        assert _git_sha() == "abc1234-dirty"

    @patch("backend.evals.eval_runner.subprocess.run")
    def test_git_unavailable_returns_unknown(self, mock_run: MagicMock) -> None:
        from backend.evals.eval_runner import _git_sha

        mock_run.side_effect = FileNotFoundError("git not found")
        assert _git_sha() == "unknown"

    @patch("backend.evals.eval_runner.subprocess.run")
    def test_git_command_failure_returns_unknown(self, mock_run: MagicMock) -> None:
        from backend.evals.eval_runner import _git_sha

        mock_run.side_effect = subprocess.CalledProcessError(128, ["git"])
        assert _git_sha() == "unknown"


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
                    "function": "backend.evals.scenarios.language_policy.scorer.tool_arg_no_cjk",
                }
            ],
        }
        import yaml

        (scenario_dir / "eval_spec.yaml").write_text(yaml.dump(spec))

        csv_content = "prompt\nhello world\ngoodbye world\n"
        (scenario_dir / "dataset.csv").write_text(csv_content)

        return scenarios_dir, scenario_dir

    @patch("backend.evals.eval_runner._init_platform_tracing")
    @patch("backend.evals.eval_runner.resolve_scorers")
    @patch("backend.evals.eval_runner.resolve_function")
    def test_run_scenario_default_produces_result_csv_via_real_eval(
        self,
        mock_resolve_task: MagicMock,
        mock_resolve_scorers: MagicMock,
        mock_init_tracing: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Spec 1: Eval() is the sole executor, including the no-upload path."""
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
            upload=False,
            output_dir=output_dir,
            scenarios_dir=scenarios_dir,
        )

        mock_init_tracing.assert_not_called()
        assert result_path.exists()
        assert result_path.suffix == ".csv"

        with result_path.open("r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        assert len(rows) == 2
        assert "prompt" in reader.fieldnames
        assert "output" in reader.fieldnames
        assert "output_json" in reader.fieldnames
        assert "score_test_scorer" in reader.fieldnames
        assert "experiment_name" in reader.fieldnames
        assert "git_sha" in reader.fieldnames
        assert rows[0]["score_test_scorer"] == "0.9"
        assert rows[0]["experiment_name"].startswith("test_scenario_")
        assert rows[0]["git_sha"] != ""

    @patch("backend.evals.eval_runner._init_platform_tracing")
    @patch("backend.evals.eval_runner.Eval")
    @patch("backend.evals.eval_runner.resolve_scorers")
    @patch("backend.evals.eval_runner.resolve_function")
    def test_run_scenario_upload_sets_no_send_logs_false_and_inits_tracing(
        self,
        mock_resolve_task: MagicMock,
        mock_resolve_scorers: MagicMock,
        mock_eval: MagicMock,
        mock_init_tracing: MagicMock,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Spec 2-3: --upload flips no_send_logs and only then inits tracing."""
        monkeypatch.setenv("BRAINTRUST_API_KEY", "fake-key-for-test")
        scenarios_dir, _ = self._setup_scenario(tmp_path)
        output_dir = tmp_path / "results"

        fake_task = MagicMock(return_value="fake response")
        mock_resolve_task.return_value = fake_task
        fake_scorer = MagicMock(return_value=0.9)
        fake_scorer.__name__ = "test_scorer"
        mock_resolve_scorers.return_value = [fake_scorer]

        mock_eval.return_value = SimpleNamespace(
            results=[
                SimpleNamespace(
                    input="hello world",
                    output="fake response",
                    scores={"test_scorer": 0.9},
                    error=None,
                    metadata={},
                )
            ]
        )

        from backend.evals.eval_runner import run_scenario

        result_path = run_scenario(
            "test_scenario",
            upload=True,
            output_dir=output_dir,
            scenarios_dir=scenarios_dir,
        )

        mock_init_tracing.assert_called_once()
        _, call_kwargs = mock_eval.call_args
        assert call_kwargs["no_send_logs"] is False
        assert call_kwargs["max_concurrency"] == 10
        assert result_path.exists()

    @patch("backend.evals.eval_runner.Eval")
    @patch("backend.evals.eval_runner.resolve_scorers")
    @patch("backend.evals.eval_runner.resolve_function")
    def test_run_scenario_default_passes_max_concurrency(
        self,
        mock_resolve_task: MagicMock,
        mock_resolve_scorers: MagicMock,
        mock_eval: MagicMock,
        tmp_path: Path,
    ) -> None:
        """M-1.1: Eval() must bound row concurrency — braintrust's default is
        unlimited; the official KB recommends max_concurrency=10."""
        scenarios_dir, _ = self._setup_scenario(tmp_path)
        output_dir = tmp_path / "results"

        fake_task = MagicMock(return_value="fake response")
        mock_resolve_task.return_value = fake_task
        fake_scorer = MagicMock(return_value=0.9)
        fake_scorer.__name__ = "test_scorer"
        mock_resolve_scorers.return_value = [fake_scorer]

        mock_eval.return_value = SimpleNamespace(
            results=[
                SimpleNamespace(
                    input="hello world",
                    output="fake response",
                    scores={"test_scorer": 0.9},
                    error=None,
                    metadata={},
                )
            ]
        )

        from backend.evals.eval_runner import run_scenario

        run_scenario(
            "test_scenario",
            upload=False,
            output_dir=output_dir,
            scenarios_dir=scenarios_dir,
        )

        _, call_kwargs = mock_eval.call_args
        assert call_kwargs["max_concurrency"] == 10

    @patch("backend.evals.eval_runner.resolve_scorers")
    @patch("backend.evals.eval_runner.resolve_function")
    def test_run_scenario_upload_missing_key_fails_preflight(
        self,
        mock_resolve_task: MagicMock,
        mock_resolve_scorers: MagicMock,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Spec 15: missing key hard-fails before any scenario work happens
        (zero execution waste) — never silently falls back to local-only."""
        monkeypatch.delenv("BRAINTRUST_API_KEY", raising=False)
        scenarios_dir, _ = self._setup_scenario(tmp_path)

        from backend.evals.eval_runner import run_scenario

        with pytest.raises(RuntimeError, match="--upload"):
            run_scenario(
                "test_scenario",
                upload=True,
                output_dir=tmp_path / "results",
                scenarios_dir=scenarios_dir,
            )

        mock_resolve_task.assert_not_called()
        mock_resolve_scorers.assert_not_called()

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
                upload=False,
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
                upload=False,
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
    def test_all_flag_upload_missing_key_hard_fails_before_loop(
        self,
        mock_run: MagicMock,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Spec 15: --all must not swallow a missing --upload key as an
        ordinary per-scenario skip — every scenario would fail identically
        on the same global precondition, so it hard-fails up front instead."""
        monkeypatch.delenv("BRAINTRUST_API_KEY", raising=False)
        scenarios_dir = tmp_path / "scenarios"
        d = scenarios_dir / "some_scenario"
        d.mkdir(parents=True)
        (d / "eval_spec.yaml").write_text("name: some_scenario\n")

        from backend.evals.eval_runner import main

        with pytest.raises(RuntimeError, match="--upload"):
            main(
                ["--all", "--upload"],
                scenarios_dir=scenarios_dir,
                output_dir=tmp_path / "results",
            )

        mock_run.assert_not_called()

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

    @patch("backend.evals.eval_runner.run_scenario")
    def test_all_flag_upload_scenario_failure_exits_nonzero(
        self,
        mock_run: MagicMock,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """M-1.5/SP-1.1: a mid-run failure under --all --upload (e.g. invalid
        key rejected by init_experiment, network drop) must not be swallowed
        as an ordinary skip — the batch exits non-zero."""
        monkeypatch.setenv("BRAINTRUST_API_KEY", "fake-key-for-test")
        scenarios_dir = tmp_path / "scenarios"
        for name in ["good_one", "bad_one"]:
            d = scenarios_dir / name
            d.mkdir(parents=True)
            (d / "eval_spec.yaml").write_text(f"name: {name}\n")

        mock_run.side_effect = [
            RuntimeError("invalid api key"),
            tmp_path / "results" / "good_one_result.csv",
        ]

        from backend.evals.eval_runner import main

        with pytest.raises(SystemExit) as exc_info:
            main(
                ["--all", "--upload"],
                scenarios_dir=scenarios_dir,
                output_dir=tmp_path / "results",
            )

        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "1 succeeded" in captured.out
        assert "1 skipped" in captured.out
        assert "failed scenario" in captured.err


# ---------------------------------------------------------------------------
# _wrap_task
# ---------------------------------------------------------------------------


class TestWrapTask:
    def test_sync_task_returning_none_raises(self) -> None:
        from backend.evals.eval_runner import _wrap_task

        def bad_task(input: Any) -> None:
            return None

        wrapped = _wrap_task(bad_task)
        with pytest.raises(ValueError, match="returned None"):
            asyncio.run(wrapped("test"))

    def test_sync_task_exception_propagates(self) -> None:
        from backend.evals.eval_runner import _wrap_task

        def crashing_task(input: Any) -> str:
            raise TimeoutError("timed out")

        wrapped = _wrap_task(crashing_task)
        with pytest.raises(TimeoutError, match="timed out"):
            asyncio.run(wrapped("test"))

    def test_sync_task_normal_return_passes_through(self) -> None:
        from backend.evals.eval_runner import _wrap_task

        def ok_task(input: Any) -> str:
            return "result"

        wrapped = _wrap_task(ok_task)
        assert asyncio.run(wrapped("test")) == "result"

    def test_async_task_normal_return_passes_through(self) -> None:
        from backend.evals.eval_runner import _wrap_task

        async def ok_task(input: Any) -> str:
            return "async result"

        wrapped = _wrap_task(ok_task)
        assert asyncio.run(wrapped("test")) == "async result"

    def test_async_task_exception_propagates(self) -> None:
        from backend.evals.eval_runner import _wrap_task

        async def crashing_task(input: Any) -> str:
            raise RuntimeError("boom")

        wrapped = _wrap_task(crashing_task)
        with pytest.raises(RuntimeError, match="boom"):
            asyncio.run(wrapped("test"))

    def test_async_task_returning_none_raises(self) -> None:
        from backend.evals.eval_runner import _wrap_task

        async def bad_task(input: Any) -> None:
            return None

        wrapped = _wrap_task(bad_task)
        with pytest.raises(ValueError, match="returned None"):
            asyncio.run(wrapped("test"))

    def test_sync_task_with_timeout_rejected_at_wrap_time(self) -> None:
        """M-1.2: a thread running a sync task cannot be interrupted, so a
        per-task timeout would be advertised but not enforceable."""
        from backend.evals.eval_runner import _wrap_task

        def sync_task(input: Any) -> str:
            return "result"

        with pytest.raises(ValueError, match="not supported for sync"):
            _wrap_task(sync_task, timeout=5)

    def test_timeout_raises_timeout_error(self) -> None:
        from backend.evals.eval_runner import _wrap_task

        async def slow_task(input: Any) -> str:
            await asyncio.sleep(10)
            return "too slow"

        wrapped = _wrap_task(slow_task, timeout=0.01)
        with pytest.raises(asyncio.TimeoutError):
            asyncio.run(wrapped("test"))

    def test_sync_task_runs_off_event_loop_thread(self) -> None:
        """Spec 10: sync tasks run via asyncio.to_thread, not the hand-rolled
        thread+queue machinery this replaces."""
        from backend.evals.eval_runner import _wrap_task

        main_thread = threading.current_thread()
        seen: dict[str, threading.Thread] = {}

        def blocking_task(input: Any) -> str:
            seen["thread"] = threading.current_thread()
            return "done"

        wrapped = _wrap_task(blocking_task)
        assert asyncio.run(wrapped("test")) == "done"
        assert seen["thread"] is not main_thread


# ---------------------------------------------------------------------------
# _wrap_scorer
# ---------------------------------------------------------------------------


class TestWrapScorer:
    def test_scorer_crash_propagates(self) -> None:
        """Spec 9: scorer exceptions are no longer caught here — they flow to
        Braintrust's own per-scorer error channel."""
        from backend.evals.eval_runner import _wrap_scorer

        def bad_scorer(*, output: Any, expected: Any, **kw: Any) -> float:
            raise RuntimeError("boom")

        wrapped = _wrap_scorer(bad_scorer, "bad")
        with pytest.raises(RuntimeError, match="boom"):
            wrapped(output="a", expected="b")

    def test_scorer_normal_return_passes_through(self) -> None:
        from backend.evals.eval_runner import _wrap_scorer

        def ok_scorer(*, output: Any, expected: Any, **kw: Any) -> float:
            return 0.5

        wrapped = _wrap_scorer(ok_scorer, "ok")
        assert wrapped(output="a", expected="b") == 0.5

    def test_deliberate_skip_returns_none_unchanged(self) -> None:
        """A scorer's own None (deliberate skip) is Braintrust's native
        no-score signal already — no sentinel translation needed."""
        from backend.evals.eval_runner import _wrap_scorer

        def skipping_scorer(*, output: Any, expected: Any, **kw: Any) -> Any:
            return None

        wrapped = _wrap_scorer(skipping_scorer, "skip")
        assert wrapped(output="a", expected="b") is None

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
        from backend.evals.scenarios.language_policy.scorer import (
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
