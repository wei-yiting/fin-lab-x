"""Unit tests for the regression gate verdict core (ADR-0008 / ADR-0015).

Pure-function tests over mock data — no LLM, no Braintrust execution.
"""

from __future__ import annotations

from typing import Any

from backend.evals.eval_runner import CaseResult
from backend.evals.eval_spec_schema import ScenarioConfig
from backend.evals.regression.verdict import evaluate_gate


def _scorer(
    name: str = "s1", *, gate: bool = True, floor: float | None = None
) -> dict[str, Any]:
    spec: dict[str, Any] = {"name": name, "function": "pkg.mod.fn", "gate": gate}
    if floor is not None:
        spec["metric_floor"] = floor
    return spec


def _config(scorers: list[dict[str, Any]]) -> ScenarioConfig:
    return ScenarioConfig.model_validate(
        {
            "name": "demo",
            "regression": {"enabled": True},
            "task": {"function": "backend.evals.eval_tasks.run_profile"},
            "column_mapping": {"prompt": "input"},
            "scorers": scorers,
        }
    )


def _case(
    case_id: str,
    scores: dict[str, float | None],
    *,
    errors: frozenset[str] = frozenset(),
    task_error: str | None = None,
) -> CaseResult:
    return CaseResult(
        case_id=case_id,
        scores=scores,
        scorer_errors=errors,
        task_error=task_error,
    )


class TestFloorRules:
    def test_all_cases_at_default_floor_is_green(self) -> None:
        config = _config([_scorer()])
        cases = [_case("c1", {"s1": 1.0}), _case("c2", {"s1": 1.0})]

        gate = evaluate_gate(config, cases)

        assert gate.status == "green"
        assert gate.failures == []

    def test_default_floor_is_one(self) -> None:
        """No metric_floor declared → 1.0, so a 0.875 mean is red."""
        config = _config([_scorer()])
        cases = [_case(f"c{i}", {"s1": 1.0}) for i in range(7)]
        cases.append(_case("c8", {"s1": 0.0}))

        gate = evaluate_gate(config, cases)

        assert gate.status == "red"
        assert "0.875" in gate.failures[0]

    def test_floor_override_applies(self) -> None:
        config = _config([_scorer(floor=0.5)])
        cases = [_case("c1", {"s1": 0.4}), _case("c2", {"s1": 0.8})]

        gate = evaluate_gate(config, cases)

        assert gate.status == "green"
        assert gate.scorer_verdicts[0].aggregate == 0.6000000000000001

    def test_floor_breach_names_scenario_case_and_scorer(self) -> None:
        config = _config([_scorer(name="response_language")])
        cases = [_case(f"LP-0{i}", {"response_language": 1.0}) for i in range(1, 8)]
        cases.append(_case("LP-08", {"response_language": 0.0}))

        gate = evaluate_gate(config, cases)

        assert gate.status == "red"
        failure = gate.failures[0]
        assert "demo" in failure
        assert "response_language" in failure
        assert "LP-08" in failure
        assert "metric_floor 1" in failure

    def test_gate_false_scorer_is_excluded(self) -> None:
        config = _config([_scorer("gated"), _scorer("advisory", gate=False)])
        cases = [_case("c1", {"gated": 1.0, "advisory": 0.0})]

        gate = evaluate_gate(config, cases)

        assert gate.status == "green"
        assert [v.scorer for v in gate.scorer_verdicts] == ["gated"]


class TestEmptyMetric:
    def test_all_errored_is_red_with_cause(self) -> None:
        config = _config([_scorer()])
        cases = [
            _case("c1", {"s1": None}, errors=frozenset({"s1"})),
            _case("c2", {"s1": None}, errors=frozenset({"s1"})),
        ]

        gate = evaluate_gate(config, cases)

        assert gate.status == "red"
        assert "all cases errored" in gate.failures[0]

    def test_all_skipped_is_red_with_cause(self) -> None:
        config = _config([_scorer()])
        cases = [_case("c1", {"s1": None}), _case("c2", {"s1": None})]

        gate = evaluate_gate(config, cases)

        assert gate.status == "red"
        assert "all cases skipped" in gate.failures[0]

    def test_mixed_absence_is_red_with_combined_cause(self) -> None:
        config = _config([_scorer()])
        cases = [
            _case("c1", {"s1": None}, errors=frozenset({"s1"})),
            _case("c2", {"s1": None}),
        ]

        gate = evaluate_gate(config, cases)

        assert gate.status == "red"
        assert "errored or skipped" in gate.failures[0]

    def test_partial_skip_with_rest_above_floor_is_green(self) -> None:
        config = _config([_scorer()])
        cases = [
            _case("c1", {"s1": 1.0}),
            _case("c2", {"s1": None}),
            _case("c3", {"s1": 1.0}),
        ]

        gate = evaluate_gate(config, cases)

        assert gate.status == "green"
        verdict = gate.scorer_verdicts[0]
        assert verdict.produced == 2
        assert verdict.skipped_cases == ("c2",)
        assert verdict.errored_cases == ()

    def test_gate_false_scorer_fully_dead_has_no_effect(self) -> None:
        config = _config([_scorer("gated"), _scorer("advisory", gate=False)])
        cases = [
            _case(
                "c1", {"gated": 1.0, "advisory": None}, errors=frozenset({"advisory"})
            ),
            _case(
                "c2", {"gated": 1.0, "advisory": None}, errors=frozenset({"advisory"})
            ),
        ]

        gate = evaluate_gate(config, cases)

        assert gate.status == "green"


class TestAbsenceSemantics:
    def test_task_crash_on_any_case_is_red(self) -> None:
        config = _config([_scorer()])
        cases = [
            _case("c1", {"s1": 1.0}),
            _case("c2", {}, task_error="RuntimeError: stream died"),
            _case("c3", {"s1": 1.0}),
        ]

        gate = evaluate_gate(config, cases)

        assert gate.status == "red"
        assert "task crashed" in gate.failures[0]
        assert "c2" in gate.failures[0]
        assert "RuntimeError: stream died" in gate.failures[0]

    def test_crashed_cases_leave_scorer_denominator(self) -> None:
        """The crash is its own failure; remaining scores still aggregate."""
        config = _config([_scorer()])
        cases = [
            _case("c1", {"s1": 1.0}),
            _case("c2", {}, task_error="boom"),
        ]

        gate = evaluate_gate(config, cases)

        assert gate.status == "red"
        assert len(gate.failures) == 1  # crash only — the aggregate is clean
        assert gate.scorer_verdicts[0].aggregate == 1.0

    def test_all_cases_crashed_reports_crash_not_empty_metric(self) -> None:
        config = _config([_scorer()])
        cases = [
            _case("c1", {}, task_error="boom"),
            _case("c2", {}, task_error="boom"),
        ]

        gate = evaluate_gate(config, cases)

        assert gate.status == "red"
        assert len(gate.failures) == 1
        assert "task crashed" in gate.failures[0]

    def test_partial_scorer_error_excluded_and_counted(self) -> None:
        config = _config([_scorer()])
        cases = [
            _case("c1", {"s1": 0.5}),
            _case("c2", {"s1": None}, errors=frozenset({"s1"})),
        ]

        gate = evaluate_gate(config, cases)

        assert gate.status == "red"
        assert "aggregate 0.5" in gate.failures[0]
        assert "errored=1 (c2)" in gate.failures[0]
        assert gate.scorer_verdicts[0].errored_cases == ("c2",)

    def test_enabled_with_zero_gated_scorers_is_red(self) -> None:
        config = _config([_scorer(gate=False)])

        gate = evaluate_gate(config, [_case("c1", {"s1": 1.0})])

        assert gate.status == "red"
        assert "no scorer has" in gate.failures[0]

    def test_enabled_with_gated_scorers_but_no_cases_is_red(self) -> None:
        """An empty run produced zero scores — it cannot support green."""
        config = _config([_scorer()])

        gate = evaluate_gate(config, [])

        assert gate.status == "red"
        assert "no cases executed" in gate.failures[0]
