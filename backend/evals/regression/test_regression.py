"""Regression Suite wrapper — thin by contract.

Zero questions and zero judgment rules of its own: datasets, scorers, and
gate declarations come from scenario assets; the verdict comes from
``verdict.evaluate_gate``. Run with:

    pytest backend/evals/regression/ -m eval

Burns real LLM/API calls; the ``eval`` marker plus the testpaths exclusion
keep it out of every default pytest invocation.
"""

from __future__ import annotations

import sys

import pytest

from backend.evals.eval_runner import (
    SCENARIOS_DIR,
    case_identifier,
    discover_scenarios,
)
from backend.evals.dataset_loader import load_raw_csv_rows
from backend.evals.eval_spec_schema import ScenarioConfig, load_scenario_config
from backend.evals.regression.conftest import GateRuns
from backend.evals.regression.selection import gate_skip_reason
from backend.evals.regression.verdict import evaluate_gate

pytestmark = pytest.mark.eval


def _collect_scenarios() -> tuple[dict[str, ScenarioConfig], list[tuple[str, str]]]:
    """Load every scenario config and enumerate enabled scenarios' case ids."""
    configs: dict[str, ScenarioConfig] = {}
    case_params: list[tuple[str, str]] = []
    for name in discover_scenarios(SCENARIOS_DIR):
        config = load_scenario_config(SCENARIOS_DIR / name / "eval_spec.yaml")
        configs[name] = config
        if not config.regression.enabled:
            continue
        _, rows = load_raw_csv_rows(SCENARIOS_DIR / name / config.csv)
        case_params.extend(
            (name, case_identifier(row, idx)) for idx, row in enumerate(rows)
        )
    return configs, case_params


_CONFIGS, _CASE_PARAMS = _collect_scenarios()


@pytest.mark.parametrize("scenario", sorted(_CONFIGS))
def test_gate(scenario: str, gate_runs: GateRuns) -> None:
    """Aggregate red/green verdict for one scenario — the gate itself."""
    config = _CONFIGS[scenario]
    if not config.regression.enabled:
        pytest.skip(f"regression.enabled: false for scenario '{scenario}'")

    result = gate_runs.result(scenario)
    skip_reason = gate_skip_reason(is_full_dataset=result.is_full_dataset)
    if skip_reason is not None:
        pytest.skip(skip_reason)

    gate = evaluate_gate(config, result.case_results)
    assert gate.status == "green", "\n".join(gate.failures)


@pytest.mark.parametrize(("scenario", "case_id"), _CASE_PARAMS)
def test_case(scenario: str, case_id: str, gate_runs: GateRuns) -> None:
    """Debug magnifier for one case: fails only on a task crash.

    Prints the case's per-scorer scores (visible with ``-s``); score-level
    judgment stays with ``test_gate`` — a single case has no aggregate.
    """
    result = gate_runs.result(scenario)
    matches = [c for c in result.case_results if c.case_id == case_id]
    if not matches:
        pytest.fail(f"case '{case_id}' missing from the run results for '{scenario}'")
    case = matches[0]

    lines = [f"── {scenario} / {case_id} scores ──"]
    for name in result.scorer_names:
        score = case.scores.get(name)
        if score is not None:
            lines.append(f"  {name}: {score:g}")
        elif name in case.scorer_errors:
            lines.append(f"  {name}: ERROR")
        else:
            lines.append(f"  {name}: SKIPPED")
    lines.append(f"  full output: {result.csv_path}")
    print("\n".join(lines), file=sys.stderr)

    assert case.task_error is None, (
        f"{scenario} / {case_id}: task crashed on the production streaming "
        f"path — {case.task_error}"
    )
