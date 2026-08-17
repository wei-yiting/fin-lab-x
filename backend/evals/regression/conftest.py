"""Regression gate fixtures.

This module is the ONLY place in the codebase that reads ``EVAL_PROFILE`` —
the Quality Track and the eval CLI stay env-free, so no other run can be
silently reconfigured by a stray environment variable.
"""

from __future__ import annotations

import os

import pytest

from backend.agent_engine.agents.config_loader import ProfileConfigLoader
from backend.evals.eval_runner import (
    DEFAULT_RESULTS_DIR,
    ScenarioRunResult,
    run_scenario,
)


def resolve_profile() -> str:
    """Read EVAL_PROFILE once; empty or unset means the baseline profile."""
    return os.environ.get("EVAL_PROFILE", "").strip() or "baseline"


def validated_profile() -> str:
    """Resolve the profile and validate it eagerly.

    A typo'd EVAL_PROFILE must fail here, loudly, before any LLM spend —
    ProfileConfigLoader raises for a profile directory that does not exist.
    """
    name = resolve_profile()
    ProfileConfigLoader(name).load()
    return name


@pytest.fixture(scope="session")
def profile() -> str:
    """The Workflow Profile under test."""
    return validated_profile()


class GateRuns:
    """Session-wide cache: one ``Eval()`` execution per scenario.

    ``test_gate`` and every ``test_case`` of a scenario share the same run.
    The dataset subset comes from the session's selected items: a selected
    gate item forces the full dataset; a pure ``-k`` case selection runs
    only those cases.
    """

    def __init__(self, session: pytest.Session, profile: str) -> None:
        self._session = session
        self._profile = profile
        self._cache: dict[str, ScenarioRunResult] = {}

    def result(self, scenario: str) -> ScenarioRunResult:
        if scenario not in self._cache:
            gate_selected, selected_case_ids = _scan_selection(self._session, scenario)
            # A selected gate item forces the full dataset: the aggregate verdict
            # is only meaningful over all cases. A pure case selection runs just
            # those cases, so a `-k LP-07` debug loop burns one agent call.
            case_ids = (
                None
                if gate_selected or not selected_case_ids
                else list(dict.fromkeys(selected_case_ids))
            )
            self._cache[scenario] = run_scenario(
                scenario,
                upload=False,
                output_dir=DEFAULT_RESULTS_DIR,
                profile=self._profile,
                case_ids=case_ids,
            )
        return self._cache[scenario]


@pytest.fixture(scope="session")
def gate_runs(request: pytest.FixtureRequest, profile: str) -> GateRuns:
    """Accessor for per-scenario run results, executed lazily on first use."""
    return GateRuns(request.session, profile)


def _scan_selection(session: pytest.Session, scenario: str) -> tuple[bool, list[str]]:
    """Collect which of this scenario's items survived -k deselection."""
    gate_selected = False
    case_ids: list[str] = []
    for item in session.items:
        callspec = getattr(item, "callspec", None)
        if callspec is None or callspec.params.get("scenario") != scenario:
            continue
        case_id = callspec.params.get("case_id")
        if case_id is None:
            gate_selected = True
        else:
            case_ids.append(case_id)
    return gate_selected, case_ids
