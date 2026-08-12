"""Pure verdict core for the Regression Suite gate.

Maps (regression declaration, per-case per-scorer scores, per-case task
errors) to a red/green verdict with failure detail. Contract: ADR-0008
(explicit gate declaration, empty metric is red) and ADR-0015
(partial-absence semantics — subject failure is signal, instrument failure
is noise until it removes all evidence).
"""

from __future__ import annotations

from dataclasses import dataclass
from statistics import fmean
from typing import Literal

from backend.evals.eval_runner import CaseResult
from backend.evals.eval_spec_schema import ScenarioConfig

GateStatus = Literal["green", "red", "skipped"]


@dataclass(frozen=True)
class ScorerVerdict:
    """Per-scorer aggregate outcome over the dataset."""

    scorer: str
    metric_floor: float
    aggregate: float | None
    produced: int
    skipped: int
    errored: int
    failure: str | None


@dataclass(frozen=True)
class GateVerdict:
    """Scenario-level gate outcome: red/green plus failure detail."""

    scenario: str
    status: GateStatus
    failures: list[str]
    scorer_verdicts: list[ScorerVerdict]


def evaluate_gate(config: ScenarioConfig, cases: list[CaseResult]) -> GateVerdict:
    """Evaluate the regression gate for one scenario run."""
    scenario = config.name

    if not config.regression.enabled:
        return GateVerdict(
            scenario=scenario,
            status="skipped",
            failures=[],
            scorer_verdicts=[],
        )

    failures: list[str] = []

    gated = [scorer for scorer in config.scorers if scorer.gate]
    if not gated:
        failures.append(
            f"{scenario}: regression.enabled is true but no scorer has "
            "gate: true — give at least one scorer a gate, or set "
            "regression.enabled: false"
        )

    if gated and not cases:
        failures.append(
            f"{scenario}: no cases executed — an empty run cannot support "
            "'no regression' (ADR-0008)"
        )

    crashed = [case for case in cases if case.task_error is not None]
    if crashed:
        crash_detail = "; ".join(
            f"{case.case_id}: {case.task_error}" for case in crashed
        )
        failures.append(
            f"{scenario}: task crashed on {len(crashed)} case(s) — the "
            f"production streaming path failed ({crash_detail})"
        )

    scored_cases = [case for case in cases if case.task_error is None]
    scorer_verdicts: list[ScorerVerdict] = []
    for scorer in gated:
        verdict = _evaluate_scorer(
            scenario=scenario,
            scorer_name=scorer.name,
            metric_floor=scorer.metric_floor,
            cases=scored_cases,
        )
        scorer_verdicts.append(verdict)
        if verdict.failure is not None:
            failures.append(verdict.failure)

    status: GateStatus = "red" if failures else "green"
    return GateVerdict(
        scenario=scenario,
        status=status,
        failures=failures,
        scorer_verdicts=scorer_verdicts,
    )


def _evaluate_scorer(
    *,
    scenario: str,
    scorer_name: str,
    metric_floor: float,
    cases: list[CaseResult],
) -> ScorerVerdict:
    """Aggregate one gated scorer over the non-crashed cases."""
    produced: dict[str, float] = {}
    errored = 0
    skipped = 0
    for case in cases:
        score = case.scores.get(scorer_name)
        if score is not None:
            produced[case.case_id] = score
        elif scorer_name in case.scorer_errors:
            errored += 1
        else:
            skipped += 1

    if not produced:
        if cases:
            if errored and not skipped:
                cause = "all cases errored"
            elif skipped and not errored:
                cause = "all cases skipped"
            else:
                cause = "every case errored or skipped"
            failure = (
                f"{scenario} / {scorer_name}: no scores produced across the "
                f"dataset ({cause}) — an unmeasured guard cannot support "
                "'no regression' (ADR-0008)"
            )
        else:
            # Every case crashed; the task-crash failure already covers red.
            failure = None
        return ScorerVerdict(
            scorer=scorer_name,
            metric_floor=metric_floor,
            aggregate=None,
            produced=0,
            skipped=skipped,
            errored=errored,
            failure=failure,
        )

    aggregate = fmean(produced.values())
    failure = None
    if aggregate < metric_floor:
        below = [
            f"{case_id} ({score:g})"
            for case_id, score in produced.items()
            if score < metric_floor
        ]
        absence = (
            f"; excluded from denominator: {skipped} skipped, {errored} errored"
            if skipped or errored
            else ""
        )
        failure = (
            f"{scenario} / {scorer_name}: aggregate {aggregate:g} < "
            f"metric_floor {metric_floor:g}; below-floor cases: "
            f"{', '.join(below)}{absence}"
        )
    return ScorerVerdict(
        scorer=scorer_name,
        metric_floor=metric_floor,
        aggregate=aggregate,
        produced=len(produced),
        skipped=skipped,
        errored=errored,
        failure=failure,
    )
