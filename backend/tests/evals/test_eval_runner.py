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
            "regression": {"enabled": True},
            "task": {"function": "backend.evals.eval_tasks.run_profile"},
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

    def _setup_diagnostic_scenario_contract_csv(
        self, tmp_path: Path, scenario_name: str = "baseline_behavior_diagnostic"
    ) -> tuple[Path, Path]:
        scenarios_dir = tmp_path / "scenarios"
        scenario_dir = scenarios_dir / scenario_name
        scenario_dir.mkdir(parents=True)

        spec = {
            "name": scenario_name,
            "csv": "dataset.csv",
            "regression": {"enabled": False},
            "diagnostic": {
                "dataset_name": "baseline_behavior_diagnostic",
                "dataset_version": "2026-04-24",
                "agent_version": "baseline",
            },
            "task": {
                "function": "backend.evals.eval_tasks.run_baseline_behavior_diagnostic"
            },
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
            "id,question,capability_band,category,expected_baseline_behavior,"
            "primary_failure_mechanism,secondary_failure_mechanism,expected_best_source,"
            "likely_tuning_lever,draft_pass_signals\n"
            "1,First question,boundary,regulatory_or_legal_risk,may_pass_with_tuning,"
            'tool_routing_error,evidence_synthesis_limit,mixed,tool_description,"[""signal1""]"\n'
            "2,Second question,boundary,regulatory_or_legal_risk,may_pass_with_tuning,"
            'tool_routing_error,,mixed,tool_description,"[""signal2""]"\n'
        )

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

        run_result = run_scenario(
            "test_scenario",
            upload=False,
            output_dir=output_dir,
            scenarios_dir=scenarios_dir,
        )

        mock_init_tracing.assert_not_called()
        assert run_result.csv_path.exists()
        assert run_result.csv_path.suffix == ".csv"

        with run_result.csv_path.open("r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        assert len(rows) == 2
        assert reader.fieldnames is not None
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

        run_result = run_scenario(
            "test_scenario",
            upload=True,
            output_dir=output_dir,
            scenarios_dir=scenarios_dir,
        )

        mock_init_tracing.assert_called_once()
        _, call_kwargs = mock_eval.call_args
        assert call_kwargs["no_send_logs"] is False
        assert call_kwargs["max_concurrency"] == 10
        assert run_result.csv_path.exists()

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
                upload=False,
                output_dir=tmp_path / "results",
                scenarios_dir=scenarios_dir,
                row_ids="1,2",
            )

    @patch("backend.evals.eval_runner._git_sha", return_value="12f85db")
    @patch("backend.evals.eval_runner.resolve_scorers")
    @patch("backend.evals.eval_runner.resolve_function")
    def test_run_scenario_diagnostic_default_runs_selected_rows_and_aligns_csv_contract_csv(
        self,
        mock_resolve_task: MagicMock,
        mock_resolve_scorers: MagicMock,
        mock_git_sha: MagicMock,
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

        run_result = run_scenario(
            "baseline_behavior_diagnostic",
            upload=False,
            output_dir=output_dir,
            scenarios_dir=scenarios_dir,
            run_label="slice-run",
            row_ids="2,1",
        )

        with run_result.csv_path.open("r", encoding="utf-8") as file:
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

    @patch("backend.evals.eval_runner._git_sha", return_value="12f85db")
    @patch("backend.evals.eval_runner._init_platform_tracing")
    @patch("backend.evals.eval_runner.resolve_scorers")
    @patch("backend.evals.eval_runner.resolve_function")
    def test_run_scenario_diagnostic_upload_uses_eval_once_and_writes_result_csv(
        self,
        mock_resolve_task: MagicMock,
        mock_resolve_scorers: MagicMock,
        mock_init_platform_tracing: MagicMock,
        mock_git_sha: MagicMock,
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

        eval_calls: list[dict[str, Any]] = []

        def fake_eval(project: str, **kwargs: Any) -> SimpleNamespace:
            eval_calls.append({"project": project, **kwargs})
            results = [
                SimpleNamespace(
                    input=case.input,
                    output={"response": "ok"},
                    scores={"diagnostic_execution_health": 1.0},
                    error=None,
                    metadata={},
                )
                for case in kwargs["data"]
            ]
            return SimpleNamespace(results=results, summary=SimpleNamespace())

        from backend.evals.eval_runner import run_scenario

        with patch("backend.evals.eval_runner.Eval", side_effect=fake_eval):
            run_result = run_scenario(
                "baseline_behavior_diagnostic",
                upload=True,
                output_dir=output_dir,
                scenarios_dir=scenarios_dir,
                run_label="slice-run",
                row_ids="2",
            )

        assert run_result.csv_path.exists()
        assert len(eval_calls) == 1
        mock_init_platform_tracing.assert_called_once()

        eval_call = eval_calls[0]
        assert eval_call["project"] == "finlab-x"
        assert eval_call["experiment_name"].startswith("baseline_behavior_diagnostic_")
        assert eval_call["metadata"]["dataset_name"] == "baseline_behavior_diagnostic"
        assert eval_call["metadata"]["dataset_version"] == "2026-04-24"
        assert eval_call["metadata"]["run_label"] == "slice-run"
        # A subset run must be self-identifying in the experiment record.
        assert eval_call["metadata"]["selected_row_ids"] == ["2"]
        assert eval_call["metadata"]["is_full_dataset"] is False
        assert eval_call["metadata"]["agent_version"] == "baseline"
        assert eval_call["metadata"]["git_commit"] == "12f85db"
        assert "slice_hash" not in eval_call["metadata"]

        eval_cases = eval_call["data"]
        assert len(eval_cases) == 1
        assert eval_cases[0].id == "2"
        braintrust_metadata = eval_cases[0].metadata
        assert braintrust_metadata["row_id"] == "2"
        assert braintrust_metadata["run_label"] == "slice-run"
        # Identity separation: Braintrust metadata carries observed identity +
        # category/capability_band, never the reference_* projection.
        assert braintrust_metadata["category"] == "regulatory_or_legal_risk"
        assert braintrust_metadata["capability_band"] == "boundary"
        assert not any(key.startswith("reference_") for key in braintrust_metadata)

        with run_result.csv_path.open("r", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            rows = list(reader)

        assert reader.fieldnames is not None
        assert "output.response" in reader.fieldnames
        assert "score_diagnostic_execution_health" in reader.fieldnames
        assert len(rows) == 1
        assert rows[0]["id"] == "2"
        assert rows[0]["output.response"] == "ok"

    def _setup_diagnostic_scenario(
        self, tmp_path: Path, scenario_name: str = "baseline_behavior_diagnostic"
    ) -> tuple[Path, Path]:
        scenarios_dir = tmp_path / "scenarios"
        scenario_dir = scenarios_dir / scenario_name
        scenario_dir.mkdir(parents=True)

        spec = {
            "name": scenario_name,
            "csv": "dataset.csv",
            "regression": {"enabled": False},
            "diagnostic": {
                "dataset_name": scenario_name,
                "dataset_version": "2026-04-24",
                "agent_version": "baseline",
            },
            "task": {
                "function": "backend.evals.eval_tasks.run_baseline_behavior_diagnostic"
            },
            "column_mapping": {"question": "input.question"},
            "scorers": [{"name": "diagnostic_execution_health", "function": "x.y"}],
        }
        import yaml

        (scenario_dir / "eval_spec.yaml").write_text(yaml.dump(spec))
        (scenario_dir / "dataset.csv").write_text(
            "\n".join(
                [
                    "id,question,category,capability_band,expected_baseline_behavior,primary_failure_mechanism,secondary_failure_mechanism,expected_best_source,likely_tuning_lever,draft_pass_signals",
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
                upload=False,
                output_dir=tmp_path / "results",
                scenarios_dir=scenarios_dir,
                row_ids="1,2",
            )

    @patch("backend.evals.eval_runner._git_sha", return_value="abc1234")
    @patch("backend.evals.eval_runner.resolve_scorers")
    @patch("backend.evals.eval_runner.resolve_function")
    def test_run_scenario_diagnostic_default_runs_selected_rows_and_writes_result_csv(
        self,
        mock_resolve_task: MagicMock,
        mock_resolve_scorers: MagicMock,
        mock_git_sha: MagicMock,
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

        run_result = run_scenario(
            "baseline_behavior_diagnostic",
            upload=False,
            output_dir=tmp_path / "results",
            scenarios_dir=scenarios_dir,
            run_label="baseline",
            row_ids="2",
        )

        with run_result.csv_path.open("r", encoding="utf-8") as file:
            rows = list(csv.DictReader(file))

        assert len(rows) == 1
        assert rows[0]["id"] == "2"
        assert len(task_calls) == 1
        assert task_calls[0]["question"] == "Second question"
        assert (
            task_calls[0]["session_id"] == "baseline_behavior_diagnostic::baseline::2"
        )
        trace_metadata = task_calls[0]["trace_metadata"]
        assert trace_metadata["row_id"] == "2"
        assert trace_metadata["reference_capability_band"] == "boundary"
        assert trace_metadata["reference_expected_behavior"] == "may_pass_with_tuning"
        assert (
            trace_metadata["reference_primary_failure_mechanism"]
            == "tool_routing_error"
        )
        assert (
            trace_metadata["reference_secondary_failure_mechanism"]
            == "evidence_synthesis_limit"
        )
        assert trace_metadata["reference_best_source"] == "mixed"
        assert trace_metadata["reference_likely_tuning_lever"] == "max_tool_calls"
        assert trace_metadata["reference_pass_signals"] == ["b"]
        assert trace_metadata["experiment_name"].startswith(
            "baseline_behavior_diagnostic_"
        )
        # Identity separation: raw dataset columns are not projected into the
        # Langfuse trace metadata (only reference_* prefixed copies).
        assert "expected_baseline_behavior" not in trace_metadata
        assert "category" not in trace_metadata


# ---------------------------------------------------------------------------
# main CLI
# ---------------------------------------------------------------------------


def _stub_run_result(csv_path: Path) -> "object":
    from backend.evals.eval_runner import ScenarioRunResult

    return ScenarioRunResult(
        scenario_name="stub",
        scorer_names=[],
        case_results=[],
        csv_path=csv_path,
        is_full_dataset=True,
    )


class TestMainCli:
    @patch("backend.evals.eval_runner.run_scenario")
    def test_main_forwards_diagnostic_cli_flags(
        self,
        mock_run_scenario: MagicMock,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        scenarios_dir = tmp_path / "scenarios"
        scenario_dir = scenarios_dir / "baseline_behavior_diagnostic"
        scenario_dir.mkdir(parents=True)
        (scenario_dir / "eval_spec.yaml").write_text(
            "name: baseline_behavior_diagnostic\n"
        )
        mock_run_scenario.return_value = _stub_run_result(
            tmp_path / "results" / "manifest.csv"
        )

        from backend.evals.eval_runner import main

        main(
            [
                "baseline_behavior_diagnostic",
                "--run-label",
                "slice-run",
                "--row-ids",
                "2,1",
            ],
            scenarios_dir=scenarios_dir,
            output_dir=tmp_path / "results",
        )

        kwargs = mock_run_scenario.call_args.kwargs
        assert kwargs["run_label"] == "slice-run"
        assert kwargs["row_ids"] == "2,1"

    @patch("backend.evals.eval_runner.run_scenario")
    def test_main_rejects_all_combined_with_diagnostic_flags(
        self,
        mock_run_scenario: MagicMock,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """M-1.2: --all with diagnostic-only flags must fail at argparse
        instead of silently skipping non-diagnostic scenarios with exit 0."""
        scenarios_dir = tmp_path / "scenarios"
        scenario_dir = scenarios_dir / "baseline_behavior_diagnostic"
        scenario_dir.mkdir(parents=True)
        (scenario_dir / "eval_spec.yaml").write_text(
            "name: baseline_behavior_diagnostic\n"
        )

        from backend.evals.eval_runner import main

        with pytest.raises(SystemExit) as exc_info:
            main(
                ["--all", "--row-ids", "2"],
                scenarios_dir=scenarios_dir,
                output_dir=tmp_path / "results",
            )

        assert exc_info.value.code == 2
        mock_run_scenario.assert_not_called()
        captured = capsys.readouterr()
        assert "Diagnostic flags cannot be combined with --all" in captured.err

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
                "regression": {"enabled": True},
                "task": {"function": "backend.evals.eval_tasks.run_profile"},
                "column_mapping": {"prompt": "input"},
                "scorers": [{"name": "s", "function": "some.func"}],
            }
            (d / "eval_spec.yaml").write_text(yaml.dump(spec))

        mock_run.side_effect = [
            _stub_run_result(tmp_path / "results" / "r1.csv"),
            _stub_run_result(tmp_path / "results" / "r2.csv"),
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
            _stub_run_result(tmp_path / "results" / "good_one_result.csv"),
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
            _stub_run_result(tmp_path / "results" / "good_one_result.csv"),
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


# ---------------------------------------------------------------------------
# profile injection + case subset (regression gate support)
# ---------------------------------------------------------------------------


class TestProfileInjectionAndSubset:
    def _setup_scenario_with_ids(self, tmp_path: Path) -> Path:
        import yaml

        scenarios_dir = tmp_path / "scenarios"
        scenario_dir = scenarios_dir / "test_scenario"
        scenario_dir.mkdir(parents=True)
        spec = {
            "name": "test_scenario",
            "csv": "dataset.csv",
            "regression": {"enabled": True},
            "task": {"function": "backend.evals.eval_tasks.run_profile"},
            "column_mapping": {"prompt": "input"},
            "scorers": [
                {"name": "test_scorer", "function": "pkg.mod.fn"},
            ],
        }
        (scenario_dir / "eval_spec.yaml").write_text(yaml.dump(spec))
        (scenario_dir / "dataset.csv").write_text(
            "id,prompt\nLP-01,hello\nLP-02,goodbye\n"
        )
        return scenarios_dir

    def _run(
        self,
        tmp_path: Path,
        task_fn: object,
        *,
        profile: str | None = None,
        case_ids: list[str] | None = None,
    ) -> object:
        scenarios_dir = self._setup_scenario_with_ids(tmp_path)

        fake_scorer = MagicMock(return_value=1.0)
        fake_scorer.__name__ = "test_scorer"

        from backend.evals.eval_runner import run_scenario

        with (
            patch(
                "backend.evals.eval_runner.resolve_function",
                return_value=task_fn,
            ),
            patch(
                "backend.evals.eval_runner.resolve_scorers",
                return_value=[fake_scorer],
            ),
        ):
            return run_scenario(
                "test_scenario",
                upload=False,
                output_dir=tmp_path / "results",
                scenarios_dir=scenarios_dir,
                profile=profile,
                case_ids=case_ids,
            )

    def test_profile_passed_when_signature_accepts(self, tmp_path: Path) -> None:
        seen: list[str] = []

        def task(input: object, profile: str = "baseline") -> str:
            seen.append(profile)
            return "response"

        self._run(tmp_path, task, profile="candidate_a")

        assert seen == ["candidate_a", "candidate_a"]

    def test_profile_not_passed_when_signature_lacks_it(self, tmp_path: Path) -> None:
        calls: list[object] = []

        def task(input: object) -> str:
            calls.append(input)
            return "response"

        result = self._run(tmp_path, task, profile="candidate_a")

        assert len(calls) == 2
        assert all(case.task_error is None for case in result.case_results)

    def test_profile_none_leaves_task_default(self, tmp_path: Path) -> None:
        seen: list[str] = []

        def task(input: object, profile: str = "baseline") -> str:
            seen.append(profile)
            return "response"

        self._run(tmp_path, task, profile=None)

        assert seen == ["baseline", "baseline"]

    def test_case_ids_runs_subset_and_flags_partial(self, tmp_path: Path) -> None:
        prompts: list[object] = []

        def task(input: object) -> str:
            prompts.append(input)
            return "response"

        result = self._run(tmp_path, task, case_ids=["LP-02"])

        assert prompts == ["goodbye"]
        assert result.is_full_dataset is False
        assert [case.case_id for case in result.case_results] == ["LP-02"]

    def test_full_run_reports_full_dataset_and_case_ids(self, tmp_path: Path) -> None:
        def task(input: object) -> str:
            return "response"

        result = self._run(tmp_path, task)

        assert result.is_full_dataset is True
        assert [case.case_id for case in result.case_results] == ["LP-01", "LP-02"]
        assert result.scorer_names == ["test_scorer"]
        assert all(case.scores == {"test_scorer": 1.0} for case in result.case_results)

    def test_unknown_case_ids_raise(self, tmp_path: Path) -> None:
        def task(input: object) -> str:
            return "response"

        with pytest.raises(ValueError, match="Unknown case ids"):
            self._run(tmp_path, task, case_ids=["NOPE-99"])

    def test_task_crash_recorded_as_case_task_error(self, tmp_path: Path) -> None:
        def task(input: object) -> str:
            if input == "goodbye":
                raise RuntimeError("stream died")
            return "response"

        result = self._run(tmp_path, task)

        errors = {case.case_id: case.task_error for case in result.case_results}
        assert errors["LP-01"] is None
        assert errors["LP-02"] is not None
        assert "stream died" in errors["LP-02"]
