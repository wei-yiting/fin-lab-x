"""Eval Runner: scenario discovery + Braintrust Eval() assembly + result CSV output.

Usage:
    python -m backend.evals.eval_runner language_policy
    python -m backend.evals.eval_runner --all
    python -m backend.evals.eval_runner language_policy --local-only
    python -m backend.evals.eval_runner language_policy --output-dir ./results
"""

from __future__ import annotations

import csv
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from braintrust import Eval

from backend.evals.dataset_loader import load_dataset
from backend.evals.scenario_config import (
    load_braintrust_config,
    load_scenario_config,
)
from backend.evals.scorer_registry import resolve_function, resolve_scorers

SCENARIOS_DIR = Path(__file__).parent / "scenarios"
DEFAULT_RESULTS_DIR = Path(__file__).parent / "results"
BRAINTRUST_CONFIG_PATH = Path(__file__).parent / "braintrust_config.yaml"


def discover_scenarios(scenarios_dir: Path) -> list[str]:
    """Scan scenarios/ for subdirectories containing eval_spec.yaml."""
    if not scenarios_dir.is_dir():
        return []

    return sorted(
        entry.name
        for entry in scenarios_dir.iterdir()
        if entry.is_dir() and (entry / "eval_spec.yaml").is_file()
    )



def _serialize_value(value: Any) -> str:
    """Serialize a value for CSV output."""
    if isinstance(value, dict):
        if "response" in value:
            return str(value["response"])
        return json.dumps(value, ensure_ascii=False)
    return str(value)


def write_result_csv(
    eval_result: Any,
    scenario_name: str,
    scorer_names: list[str],
    output_dir: Path,
) -> Path:
    """Write eval results to a timestamped CSV file.

    CSV columns: input, output, score_{name} for each scorer.
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(tz=timezone.utc).strftime("%Y%m%d_%H%M%S_%f")
    filename = f"{scenario_name}_{timestamp}.csv"
    csv_path = output_dir / filename

    score_columns = [f"score_{name}" for name in scorer_names]
    fieldnames = ["input", "output", *score_columns]

    with csv_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for result in eval_result.results:
            row: dict[str, str] = {
                "input": _serialize_value(result.input),
                "output": _serialize_value(result.output),
            }
            for name in scorer_names:
                score_val = result.scores.get(name)
                if score_val is None:
                    row[f"score_{name}"] = ""
                elif isinstance(score_val, (int, float)):
                    row[f"score_{name}"] = str(score_val)
                else:
                    row[f"score_{name}"] = str(score_val.score)

            writer.writerow(row)

    return csv_path


def run_scenario(
    scenario_name: str,
    *,
    local_only: bool,
    output_dir: Path,
    scenarios_dir: Path = SCENARIOS_DIR,
) -> Path:
    """Execute a single evaluation scenario.

    Steps:
    1. Load eval_spec.yaml -> ScenarioConfig
    2. Validate CSV exists
    3. load_dataset() -> data list
    4. resolve_scorers() -> scorer callables
    5. Dynamic import task function
    6. If not local_only: validate API key, init tracing
    7. Eval() call
    8. write_result_csv() -> result CSV path
    """
    scenario_dir = scenarios_dir / scenario_name
    config_path = scenario_dir / "eval_spec.yaml"
    config = load_scenario_config(config_path)

    csv_path = scenario_dir / config.csv
    if not csv_path.is_file():
        raise FileNotFoundError(f"CSV file not found: {csv_path}")

    data = load_dataset(csv_path, config.column_mapping)
    scorers = resolve_scorers(config.scorers)
    task_fn = resolve_function(config.task.function, label="task")

    bt_config = load_braintrust_config(BRAINTRUST_CONFIG_PATH)
    experiment_name = f"{config.name}_{datetime.now(tz=timezone.utc).strftime('%Y%m%d_%H%M%S')}"

    if not local_only:
        api_key = os.environ.get(bt_config.api_key_env)
        if not api_key:
            raise RuntimeError(
                f"API key not found in environment variable '{bt_config.api_key_env}'. "
                "Set the key or use --local-only."
            )
        _init_platform_tracing(bt_config.project, api_key)

    eval_result = Eval(
        bt_config.project,
        data=data,
        task=task_fn,
        scores=scorers,
        experiment_name=experiment_name,
        no_send_logs=local_only,
    )

    scorer_names = [s.name for s in config.scorers]
    return write_result_csv(eval_result, scenario_name, scorer_names, output_dir)


def _init_platform_tracing(project: str, api_key: str) -> None:
    """Initialize Braintrust platform tracing for non-local mode."""
    from braintrust import init_logger

    init_logger(project=project, api_key=api_key)

    from braintrust_langchain import BraintrustCallbackHandler
    from langchain_core.globals import set_global_handler

    set_global_handler(BraintrustCallbackHandler())


def main(
    argv: list[str] | None = None,
    *,
    scenarios_dir: Path = SCENARIOS_DIR,
    output_dir: Path = DEFAULT_RESULTS_DIR,
) -> None:
    """CLI entry point with argparse."""
    import argparse

    parser = argparse.ArgumentParser(description="Run Braintrust evaluations")
    parser.add_argument("scenario", nargs="?", help="Scenario name to run")
    parser.add_argument("--all", action="store_true", help="Run all scenarios")
    parser.add_argument("--local-only", action="store_true", help="Skip platform logging")
    parser.add_argument("--output-dir", type=Path, default=None, help="Output directory for results")

    args = parser.parse_args(argv)

    if args.output_dir is not None:
        output_dir = args.output_dir

    if not args.all and not args.scenario:
        parser.error("Provide a scenario name or use --all")

    available = discover_scenarios(scenarios_dir)

    if args.all:
        if not available:
            print("No scenarios found.", file=sys.stderr)
            raise SystemExit(1)

        succeeded = 0
        skipped = 0
        for name in available:
            try:
                result_path = run_scenario(
                    name,
                    local_only=args.local_only,
                    output_dir=output_dir,
                    scenarios_dir=scenarios_dir,
                )
                print(f"  {name}: {result_path}")
                succeeded += 1
            except Exception as exc:
                print(f"  {name}: SKIPPED ({exc})", file=sys.stderr)
                skipped += 1

        print(f"{succeeded} succeeded, {skipped} skipped")
        return

    if args.scenario not in available:
        print(
            f"Scenario '{args.scenario}' not found. Available: {', '.join(available)}",
            file=sys.stderr,
        )
        raise SystemExit(1)

    result_path = run_scenario(
        args.scenario,
        local_only=args.local_only,
        output_dir=output_dir,
        scenarios_dir=scenarios_dir,
    )
    print(f"Result: {result_path}")


if __name__ == "__main__":
    main()
