"""Unit tests for regression run planning and the EVAL_PROFILE entry point."""

from __future__ import annotations

import pytest

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
