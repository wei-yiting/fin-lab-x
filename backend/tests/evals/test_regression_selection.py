"""Unit tests for regression run planning and the EVAL_PROFILE entry point."""

from __future__ import annotations

import pytest
from types import SimpleNamespace

from backend.evals.regression.conftest import resolve_profile
from backend.evals.regression.selection import plan_run


class TestPlanRun:
    def test_gate_selected_forces_full_dataset(self) -> None:
        plan = plan_run(gate_selected=True, selected_case_ids=["LP-07"])

        assert plan.full is True
        assert plan.case_ids is None

    def test_no_selection_defaults_to_full_dataset(self) -> None:
        plan = plan_run(gate_selected=False, selected_case_ids=[])

        assert plan.full is True

    def test_pure_case_selection_runs_subset(self) -> None:
        plan = plan_run(gate_selected=False, selected_case_ids=["LP-07", "LP-01"])

        assert plan.full is False
        assert plan.case_ids == ("LP-07", "LP-01")

    def test_duplicate_case_ids_deduplicated(self) -> None:
        plan = plan_run(gate_selected=False, selected_case_ids=["LP-07", "LP-07"])

        assert plan.case_ids == ("LP-07",)


class TestResolveProfile:
    def test_defaults_to_baseline_when_unset(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.delenv("EVAL_PROFILE", raising=False)

        assert resolve_profile() == "baseline"

    def test_reads_eval_profile_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("EVAL_PROFILE", "candidate_a")

        assert resolve_profile() == "candidate_a"

    def test_blank_env_falls_back_to_baseline(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("EVAL_PROFILE", "   ")

        assert resolve_profile() == "baseline"


class TestGateSkipReason:
    def test_full_dataset_proceeds(self) -> None:
        from backend.evals.regression.selection import gate_skip_reason

        assert gate_skip_reason(is_full_dataset=True) is None

    def test_partial_run_skips_with_reason(self) -> None:
        from backend.evals.regression.selection import gate_skip_reason

        reason = gate_skip_reason(is_full_dataset=False)

        assert reason is not None
        assert "full dataset" in reason


class TestValidatedProfile:
    def test_nonexistent_profile_fails_loudly(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        from backend.evals.regression.conftest import validated_profile

        monkeypatch.setenv("EVAL_PROFILE", "no_such_profile_xyz")

        with pytest.raises(FileNotFoundError, match="no_such_profile_xyz"):
            validated_profile()

    def test_default_baseline_profile_validates(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        from backend.evals.regression.conftest import validated_profile

        monkeypatch.delenv("EVAL_PROFILE", raising=False)

        assert validated_profile() == "baseline"


def _item(scenario: str, case_id: str | None = None) -> SimpleNamespace:
    params: dict[str, str] = {"scenario": scenario}
    if case_id is not None:
        params["case_id"] = case_id
    return SimpleNamespace(callspec=SimpleNamespace(params=params))


class TestScanSelectionAndGateRuns:
    def test_scan_selection_separates_gate_and_cases(self) -> None:
        from backend.evals.regression.conftest import _scan_selection

        session = SimpleNamespace(
            items=[
                _item("language_policy"),
                _item("language_policy", "LP-01"),
                _item("language_policy", "LP-07"),
                _item("other_scenario", "X-01"),
                SimpleNamespace(),  # non-parametrized item — ignored
            ]
        )

        gate_selected, case_ids = _scan_selection(session, "language_policy")  # type: ignore[arg-type]

        assert gate_selected is True
        assert case_ids == ["LP-01", "LP-07"]

    def test_gate_runs_subset_when_only_cases_selected(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        import backend.evals.regression.conftest as regression_conftest

        calls: list[dict[str, object]] = []

        def fake_run_scenario(scenario: str, **kwargs: object) -> str:
            calls.append({"scenario": scenario, **kwargs})
            return f"result-{scenario}"

        monkeypatch.setattr(regression_conftest, "run_scenario", fake_run_scenario)
        session = SimpleNamespace(items=[_item("language_policy", "LP-07")])
        runs = regression_conftest.GateRuns(session, "baseline")  # type: ignore[arg-type]

        first = runs.result("language_policy")
        second = runs.result("language_policy")

        assert first == second == "result-language_policy"
        assert len(calls) == 1  # cached: one Eval() execution per scenario
        assert calls[0]["case_ids"] == ["LP-07"]
        assert calls[0]["profile"] == "baseline"
        assert calls[0]["upload"] is False

    def test_gate_runs_full_dataset_when_gate_selected(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        import backend.evals.regression.conftest as regression_conftest

        calls: list[dict[str, object]] = []

        def fake_run_scenario(scenario: str, **kwargs: object) -> str:
            calls.append({"scenario": scenario, **kwargs})
            return f"result-{scenario}"

        monkeypatch.setattr(regression_conftest, "run_scenario", fake_run_scenario)
        session = SimpleNamespace(
            items=[_item("language_policy"), _item("language_policy", "LP-07")]
        )
        runs = regression_conftest.GateRuns(session, "baseline")  # type: ignore[arg-type]

        runs.result("language_policy")

        assert calls[0]["case_ids"] is None
