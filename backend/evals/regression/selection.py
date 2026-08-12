"""Run planning: map pytest's selected items (-k) to a dataset subset.

A gate item in the selection forces the full dataset (the aggregate verdict
is only meaningful over all cases); a pure case selection runs just those
cases, so a `-k LP-07` debug loop burns one agent call, not the dataset.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass


@dataclass(frozen=True)
class RunPlan:
    """What to execute for one scenario in this pytest session."""

    full: bool
    case_ids: tuple[str, ...] | None


def plan_run(*, gate_selected: bool, selected_case_ids: Sequence[str]) -> RunPlan:
    """Decide the dataset subset from the session's selected items."""
    if gate_selected or not selected_case_ids:
        return RunPlan(full=True, case_ids=None)
    return RunPlan(full=False, case_ids=tuple(dict.fromkeys(selected_case_ids)))


def gate_skip_reason(*, is_full_dataset: bool) -> str | None:
    """Why ``test_gate`` must skip for this run, or ``None`` to proceed.

    A subset run has no aggregate verdict — its mean over selected cases
    must never impersonate the gate's red/green.
    """
    if is_full_dataset:
        return None
    return "partial run — the aggregate verdict requires the full dataset"
