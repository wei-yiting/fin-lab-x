"""Tests for the Regression Suite wrapper's operator output.

Drives ``test_gate`` directly with a stubbed run result — no LLM, no
Braintrust execution.
"""

from __future__ import annotations

import contextlib
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

import backend.evals.regression.test_regression as wrapper
from backend.evals.eval_runner import CaseResult, ScenarioRunResult
from backend.evals.eval_spec_schema import ScenarioConfig


def _config(scorer_name: str = "s1", *, enabled: bool = True) -> ScenarioConfig:
    spec: dict[str, Any] = {
        "name": "demo",
        "regression": {"enabled": enabled},
        "task": {"function": "backend.evals.eval_tasks.run_profile"},
        "column_mapping": {"prompt": "input"},
        "scorers": [{"name": scorer_name, "function": "pkg.mod.fn", "gate": True}],
    }
    return ScenarioConfig.model_validate(spec)


def _run_result(cases: list[CaseResult], scorer_name: str) -> ScenarioRunResult:
    return ScenarioRunResult(
        scorer_names=[scorer_name],
        case_results=cases,
        csv_path=Path("results/demo.csv"),
    )


def _stub_capsys() -> SimpleNamespace:
    """Stand-in for pytest's ``capsys`` whose ``disabled()`` does nothing.

    The no-op keeps the summary on ``sys.stderr``, where the outer test's own
    ``capsys`` can still capture it.
    """
    return SimpleNamespace(disabled=contextlib.nullcontext)


class TestGateSummaryOutput:
    def test_green_verdict_still_reports_absence_counts(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """A green gate must not hide a scorer that fell over (ADR-0015)."""
        monkeypatch.setitem(wrapper._CONFIGS, "demo", _config())
        cases = [
            CaseResult(case_id="c1", scores={"s1": 1.0}),
            CaseResult(
                case_id="c2", scores={"s1": None}, scorer_errors=frozenset({"s1"})
            ),
            CaseResult(case_id="c3", scores={"s1": 1.0}),
        ]
        gate_runs = SimpleNamespace(result=lambda scenario: _run_result(cases, "s1"))

        wrapper.test_gate("demo", gate_runs, _stub_capsys())  # type: ignore[arg-type]

        err = capsys.readouterr().err
        assert "[green]" in err
        assert "s1: aggregate=1 floor=1 produced=2 skipped=0 errored=1 (c2)" in err

    def test_red_verdict_reports_counts_before_failing(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        monkeypatch.setitem(wrapper._CONFIGS, "demo", _config())
        cases = [
            CaseResult(case_id="c1", scores={"s1": 0.0}),
            CaseResult(case_id="c2", scores={"s1": None}),
        ]
        gate_runs = SimpleNamespace(result=lambda scenario: _run_result(cases, "s1"))

        with pytest.raises(AssertionError):
            wrapper.test_gate("demo", gate_runs, _stub_capsys())  # type: ignore[arg-type]

        err = capsys.readouterr().err
        assert "[red]" in err
        assert "s1: aggregate=0 floor=1 produced=1 skipped=1 (c2) errored=0" in err

    def test_no_scores_produced_renders_aggregate_legibly(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        monkeypatch.setitem(wrapper._CONFIGS, "demo", _config())
        cases = [CaseResult(case_id="c1", scores={"s1": None})]
        gate_runs = SimpleNamespace(result=lambda scenario: _run_result(cases, "s1"))

        with pytest.raises(AssertionError):
            wrapper.test_gate("demo", gate_runs, _stub_capsys())  # type: ignore[arg-type]

        err = capsys.readouterr().err
        assert "s1: aggregate=n/a floor=1 produced=0 skipped=1 (c1) errored=0" in err


class TestDisabledScenario:
    def test_disabled_scenario_skips_without_running(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """``regression.enabled: false`` must skip before any run is executed."""
        monkeypatch.setitem(wrapper._CONFIGS, "demo", _config(enabled=False))
        calls: list[str] = []
        gate_runs = SimpleNamespace(result=lambda scenario: calls.append(scenario))

        with pytest.raises(pytest.skip.Exception, match="regression.enabled: false"):
            wrapper.test_gate("demo", gate_runs, _stub_capsys())  # type: ignore[arg-type]

        assert calls == []
