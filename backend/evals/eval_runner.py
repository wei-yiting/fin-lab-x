"""Eval Runner: scenario discovery + Braintrust Eval() assembly + result CSV output.

Usage:
    python -m backend.evals.eval_runner language_policy
    python -m backend.evals.eval_runner --all
    python -m backend.evals.eval_runner language_policy --local-only
    python -m backend.evals.eval_runner language_policy --output-dir ./results
"""

from __future__ import annotations

import asyncio
import csv
import inspect
import json
import logging
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

from backend.evals.dataset_loader import (
    _convert_cell,
    _set_nested_value,
    _validate_column_mapping,
    load_dataset,
    load_raw_csv_rows,
)
from backend.evals.diagnostic.dataset_selector import (
    parse_diagnostic_slice_args,
    select_diagnostic_slice,
)
from backend.evals.diagnostic.metadata_projector import project_diagnostic_metadata
from backend.evals.diagnostic.models import resolve_git_commit
from backend.evals.diagnostic.run_manifest_writer import (
    write_run_manifest_csv as write_diagnostic_run_manifest,
)
from backend.evals.eval_spec_schema import (
    load_braintrust_config,
    load_scenario_config,
)
from backend.evals.scorer_registry import resolve_function, resolve_scorers

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

SCENARIOS_DIR = Path(__file__).parent / "scenarios"
DEFAULT_RESULTS_DIR = Path(__file__).parent / "results"
BRAINTRUST_CONFIG_PATH = Path(__file__).parent / "braintrust_config.yaml"

_VALID_SCENARIO_DIR_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]*$")


class _SuppressContextDetach(logging.Filter):
    """Filter out 'Failed to detach context' noise from OpenTelemetry.

    asyncio.run() creates a fresh ContextVar scope, so OTel tokens created
    inside cannot be detached after the loop exits.  This is harmless — traces
    are already flushed — but produces noisy tracebacks on stderr.
    """

    def filter(self, record: logging.LogRecord) -> bool:
        return "Failed to detach context" not in record.getMessage()

logger = logging.getLogger(__name__)

_ERROR_MARKER = "ERROR"
_SKIPPED_MARKER = "SKIPPED"


def discover_scenarios(scenarios_dir: Path) -> list[str]:
    """Scan scenarios/ for subdirectories containing eval_spec.yaml.

    Raises ValueError for directory names with invalid characters (e.g. spaces).
    """
    if not scenarios_dir.is_dir():
        return []

    names: list[str] = []
    for entry in sorted(scenarios_dir.iterdir()):
        if not entry.is_dir():
            continue
        if not (entry / "eval_spec.yaml").is_file():
            continue
        if not _VALID_SCENARIO_DIR_RE.match(entry.name):
            suggestion = re.sub(r"[^A-Za-z0-9_-]", "_", entry.name)
            raise ValueError(
                f"Scenario directory name '{entry.name}' contains invalid characters. "
                f"Use only alphanumerics, hyphens, and underscores. "
                f"Suggestion: '{suggestion}'"
            )
        names.append(entry.name)

    return names


def _serialize_value(value: Any) -> str:
    """Serialize a value for CSV output."""
    if isinstance(value, dict):
        if "response" in value:
            return str(value["response"])
        return json.dumps(value, ensure_ascii=False)
    return str(value)


def _flatten_output(output: Any) -> dict[str, str]:
    """Flatten an output value into output.* columns.

    If output is a dict, each key becomes output.{key}.
    Otherwise, a single output column is used.
    """
    if isinstance(output, dict):
        return {
            f"output.{key}": _serialize_value(val)
            if isinstance(val, dict)
            else str(val)
            for key, val in output.items()
        }
    return {"output": str(output)}


_TIMEOUT_MARKER = "TIMEOUT"


def _wrap_task(task_fn: Any, *, timeout: float | None = None) -> Any:
    """Wrap the task function to catch exceptions, None returns, and timeouts.

    Preserves async task functions so Braintrust Eval() can await them
    directly in the same event loop (avoiding thread + asyncio.run overhead).
    """

    if asyncio.iscoroutinefunction(task_fn):

        async def wrapped(input: Any) -> Any:
            try:
                if timeout is not None:
                    result = await asyncio.wait_for(
                        task_fn(input), timeout=timeout
                    )
                else:
                    result = await task_fn(input)
            except asyncio.TimeoutError:
                logger.error(
                    "Task function timed out after %.1f seconds", timeout
                )
                return _ERROR_MARKER
            except Exception:
                logger.error("Task function raised an exception", exc_info=True)
                return _ERROR_MARKER
            if result is None:
                logger.error(
                    "Task function returned None. "
                    "Ensure the function has a return statement."
                )
                return _ERROR_MARKER
            return result

        return wrapped

    def wrapped(input: Any) -> Any:
        if timeout is not None:
            import queue
            import threading

            result_q: queue.Queue[tuple[str, Any]] = queue.Queue()

            def _run() -> None:
                try:
                    result_q.put(("ok", task_fn(input)))
                except Exception as exc:
                    result_q.put(("error", exc))

            t = threading.Thread(target=_run, daemon=True)
            t.start()
            try:
                status, value = result_q.get(timeout=timeout)
            except queue.Empty:
                logger.error(
                    "Task function timed out after %.1f seconds", timeout
                )
                return _ERROR_MARKER
            if status == "error":
                logger.error("Task function raised an exception: %s", value)
                return _ERROR_MARKER
            result = value
        else:
            try:
                result = task_fn(input)
            except Exception:
                logger.error("Task function raised an exception", exc_info=True)
                return _ERROR_MARKER
        if result is None:
            logger.error(
                "Task function returned None. Ensure the function has a return statement."
            )
            return _ERROR_MARKER
        return result

    return wrapped


def _filter_kwargs_for(fn: Any, kwargs: dict[str, Any]) -> dict[str, Any]:
    """Return only the *kwargs* entries that *fn* actually accepts.

    If *fn* has a ``**kwargs`` (VAR_KEYWORD) parameter it is assumed to
    accept any keyword argument, so the full dict is returned unchanged.
    Otherwise only keys that match a declared parameter name are kept.
    """
    try:
        sig = inspect.signature(fn)
    except (ValueError, TypeError):
        # If we cannot introspect, pass everything and let the caller
        # handle any resulting TypeError via its own exception guard.
        return kwargs

    for param in sig.parameters.values():
        if param.kind == inspect.Parameter.VAR_KEYWORD:
            return kwargs  # fn accepts **kw – forward everything

    accepted = {
        name
        for name, p in sig.parameters.items()
        if p.kind
        in (
            inspect.Parameter.POSITIONAL_OR_KEYWORD,
            inspect.Parameter.KEYWORD_ONLY,
        )
    }
    return {k: v for k, v in kwargs.items() if k in accepted}


def _wrap_scorer(scorer_fn: Any, scorer_name: str) -> Any:
    """Wrap a scorer to isolate failures from other scorers."""

    def wrapped(*, output: Any, expected: Any, **kwargs: Any) -> Any:
        should_score_error_row = scorer_name == "diagnostic_execution_health"
        if output == _ERROR_MARKER and not should_score_error_row:
            return None
        try:
            filtered = _filter_kwargs_for(scorer_fn, kwargs)
            result = scorer_fn(output=output, expected=expected, **filtered)
            if result is None:
                return _SKIPPED_MARKER
            if hasattr(result, "name"):
                result.name = scorer_name
            return result
        except Exception:
            logger.warning(
                "Scorer '%s' raised an exception", scorer_name, exc_info=True
            )
            return None

    wrapped.__name__ = scorer_name
    return wrapped


def write_result_csv(
    eval_result: Any,
    scenario_name: str,
    scorer_names: list[str],
    output_dir: Path,
    *,
    original_columns: list[str] | None = None,
    original_rows: list[dict[str, str]] | None = None,
) -> Path:
    """Write eval results to a timestamped CSV file.

    CSV columns: original CSV columns (if provided) + output.* columns + score_{name} columns.
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(tz=timezone.utc).strftime("%Y%m%d_%H%M%S_%f")
    filename = f"{scenario_name}_{timestamp}.csv"
    csv_path = output_dir / filename

    score_columns = [f"score_{name}" for name in scorer_names]

    # Collect all output keys to determine columns
    all_output_keys: list[str] = []
    flattened_outputs: list[dict[str, str]] = []
    for result in eval_result.results:
        flat = _flatten_output(result.output)
        flattened_outputs.append(flat)
        for key in flat:
            if key not in all_output_keys:
                all_output_keys.append(key)

    orig_cols = original_columns or []

    # Rename generated output keys that conflict with original CSV columns
    conflict_keys = set(orig_cols) & set(all_output_keys)
    if conflict_keys:
        rename_map = {k: f"_generated.{k}" for k in conflict_keys}
        all_output_keys = [rename_map.get(k, k) for k in all_output_keys]
        flattened_outputs = [
            {rename_map.get(k, k): v for k, v in flat.items()}
            for flat in flattened_outputs
        ]

    fieldnames = [*orig_cols, *all_output_keys, *score_columns]

    with csv_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for idx, result in enumerate(eval_result.results):
            row: dict[str, str] = {}

            # Include original CSV columns
            if original_rows and idx < len(original_rows):
                for col in orig_cols:
                    row[col] = original_rows[idx].get(col, "")

            # Output columns
            flat_output = flattened_outputs[idx]
            is_error_row = result.output == _ERROR_MARKER

            if is_error_row:
                for key in all_output_keys:
                    row[key] = _ERROR_MARKER
            else:
                for key in all_output_keys:
                    row[key] = flat_output.get(key, "")

            # Score columns
            for name in scorer_names:
                score_val = result.scores.get(name)
                if is_error_row and score_val is None:
                    row[f"score_{name}"] = _ERROR_MARKER
                elif score_val is None:
                    row[f"score_{name}"] = _ERROR_MARKER
                elif score_val == _SKIPPED_MARKER:
                    row[f"score_{name}"] = _SKIPPED_MARKER
                elif isinstance(score_val, (int, float)):
                    row[f"score_{name}"] = str(score_val)
                elif isinstance(score_val, str):
                    row[f"score_{name}"] = score_val
                else:
                    row[f"score_{name}"] = str(getattr(score_val, "score", score_val))

            writer.writerow(row)

    return csv_path


def run_scenario(
    scenario_name: str,
    *,
    local_only: bool,
    output_dir: Path,
    scenarios_dir: Path = SCENARIOS_DIR,
    run_label: str | None = None,
    run_group: str | None = None,
    agent_version: str | None = None,
    slice_label: str | None = None,
    row_ids: str | None = None,
    field_filter: str | None = None,
    manifest: str | None = None,
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
    otel_filter = _SuppressContextDetach()
    otel_logger = logging.getLogger("opentelemetry.context")
    otel_logger.addFilter(otel_filter)

    try:
        scenario_dir = scenarios_dir / scenario_name
        config_path = scenario_dir / "eval_spec.yaml"
        config = load_scenario_config(config_path)

        banner_fields: dict[str, Any] = {}
        if config.pre_run is not None:
            pre_run_fn = resolve_function(config.pre_run.function, label="pre_run")
            result = pre_run_fn()
            if result is not None:
                banner_fields = dict(result)

        banner_line = f"Eval scenario: {config.name}"
        for key, value in banner_fields.items():
            banner_line += f" | {key}: {value}"
        if config.status == "draft":
            print(
                f"\u26a0 Scenario '{config.name}' is draft "
                f"\u2014 results may be unreliable. "
                f"Curate dataset before trusting metrics.",
                file=sys.stderr,
            )

        csv_path = scenario_dir / config.csv
        if not csv_path.is_file():
            raise FileNotFoundError(f"CSV file not found: {csv_path}")

        original_columns, original_rows = load_raw_csv_rows(csv_path)

        scorers = resolve_scorers(config.scorers)
        task_fn = resolve_function(config.task.function, label="task")

        scorer_names = [s.name for s in config.scorers]
        wrapped_task = _wrap_task(task_fn, timeout=config.task.timeout)
        wrapped_scorers = [
            _wrap_scorer(scorer, name) for scorer, name in zip(scorers, scorer_names)
        ]

        bt_config = load_braintrust_config(BRAINTRUST_CONFIG_PATH)
        timestamp = datetime.now(tz=timezone.utc).strftime("%Y%m%d_%H%M%S")
        experiment_name = f"{config.name}_{timestamp}"
        git_commit = resolve_git_commit()

        # Merge local_mode: CLI --local-only overrides config default
        effective_local = local_only or bt_config.local_mode

        diagnostic_flag_values = [
            run_label,
            run_group,
            agent_version,
            slice_label,
            row_ids,
            field_filter,
            manifest,
        ]

        if config.diagnostic is None:
            if any(value is not None for value in diagnostic_flag_values):
                raise ValueError(
                    "Diagnostic flags are only supported for diagnostic scenarios"
                )

            print(banner_line, file=sys.stderr)

            raw_data = load_dataset(csv_path, config.column_mapping)

            # Always run local eval first to guarantee local CSV output
            eval_result = _run_local_eval(raw_data, wrapped_task, wrapped_scorers)

            result_path = write_result_csv(
                eval_result,
                scenario_name,
                scorer_names,
                output_dir,
                original_columns=original_columns,
                original_rows=original_rows,
            )

            if not effective_local:
                try:
                    from braintrust import Eval, EvalCase

                    api_key = os.environ.get(bt_config.api_key_env)
                    if not api_key:
                        raise RuntimeError(
                            f"API key not found in environment variable "
                            f"'{bt_config.api_key_env}'. "
                            "Set the key or use --local-only."
                        )
                    _init_platform_tracing(bt_config.project, api_key)

                    eval_cases = [
                        EvalCase(
                            input=row["input"],
                            expected=row.get("expected"),
                            metadata=row.get("metadata"),
                        )
                        for row in raw_data
                    ]

                    Eval(
                        bt_config.project,
                        data=eval_cases,
                        task=wrapped_task,
                        scores=wrapped_scorers,
                        experiment_name=experiment_name,
                        no_send_logs=False,
                        max_concurrency=1,
                    )

                    import braintrust

                    braintrust.flush()
                except Exception:
                    logger.error("Braintrust upload failed", exc_info=True)

            return result_path

        diagnostic_config = config.diagnostic
        effective_run_label = run_label or _build_default_run_label()
        effective_run_group = run_group or "manual"
        effective_agent_version = agent_version or diagnostic_config.agent_version
        banner_line += (
            f" | Run label: {effective_run_label}"
            f" | Run group: {effective_run_group}"
            f" | Git commit: {git_commit}"
        )

        slice_args = parse_diagnostic_slice_args(
            row_ids=row_ids,
            field_filter=field_filter,
            manifest=manifest,
            slice_label=slice_label,
        )
        selected_rows, slice_identity = select_diagnostic_slice(
            original_columns,
            original_rows,
            slice_args,
            row_id_column=diagnostic_config.row_id_column,
        )
        diagnostic_data = _build_diagnostic_eval_rows(
            selected_rows=selected_rows,
            column_mapping=config.column_mapping,
            diagnostic_config=diagnostic_config,
            dataset_name=diagnostic_config.dataset_name,
            dataset_version=diagnostic_config.dataset_version,
            run_label=effective_run_label,
            run_group=effective_run_group,
            agent_version=effective_agent_version,
            experiment_name=experiment_name,
            slice_identity=slice_identity,
        )
        banner_line += (
            f" | Slice label: {slice_identity.slice_label}"
            f" | Slice type: {slice_identity.slice_type}"
            f" | Rows: {len(selected_rows)}"
        )
        print(banner_line, file=sys.stderr)

        if effective_local:
            eval_result = _run_local_eval(
                diagnostic_data,
                wrapped_task,
                wrapped_scorers,
            )

            return write_result_csv(
                eval_result,
                scenario_name,
                scorer_names,
                output_dir,
                original_columns=original_columns,
                original_rows=selected_rows,
            )

        if not effective_local:
            try:
                from braintrust import Eval, EvalCase

                api_key = os.environ.get(bt_config.api_key_env)
                if not api_key:
                    raise RuntimeError(
                        f"API key not found in environment variable "
                        f"'{bt_config.api_key_env}'. "
                        "Set the key or use --local-only."
                    )
                _init_platform_tracing(bt_config.project, api_key)

                eval_cases = [
                    EvalCase(
                        id=row["id"],
                        input=row["input"],
                        expected={},
                        metadata=row.get("metadata"),
                    )
                    for row in diagnostic_data
                ]

                Eval(
                    bt_config.project,
                    data=eval_cases,
                    task=wrapped_task,
                    scores=wrapped_scorers,
                    experiment_name=experiment_name,
                    metadata={
                        "dataset_name": diagnostic_config.dataset_name,
                        "dataset_version": diagnostic_config.dataset_version,
                        "run_label": effective_run_label,
                        "run_group": effective_run_group,
                        "slice_label": slice_identity.slice_label,
                        "slice_type": slice_identity.slice_type,
                        "selected_row_count": len(selected_rows),
                        "slice_hash": slice_identity.slice_hash,
                        "agent_version": effective_agent_version,
                        "git_commit": git_commit,
                    },
                    no_send_logs=False,
                    max_concurrency=1,
                )

                import braintrust

                braintrust.flush()
                manifest_rows = [
                    {
                        "row_id": row["metadata"]["row_id"],
                        "session_id": row["input"]["session_id"],
                        "experiment_name": experiment_name,
                        "run_label": effective_run_label,
                        "slice_label": slice_identity.slice_label,
                        "git_commit": git_commit,
                        "braintrust_project": bt_config.project,
                    }
                    for row in diagnostic_data
                ]
                return write_diagnostic_run_manifest(
                    scenario_name=scenario_name,
                    output_dir=output_dir,
                    original_columns=original_columns,
                    original_rows=selected_rows,
                    manifest_rows=manifest_rows,
                )
            except Exception:
                logger.error("Braintrust upload failed", exc_info=True)
                raise
    finally:
        otel_logger.removeFilter(otel_filter)


def _build_diagnostic_eval_rows(
    *,
    selected_rows: list[dict[str, str]],
    column_mapping: dict[str, str],
    diagnostic_config: Any,
    dataset_name: str,
    dataset_version: str,
    run_label: str,
    run_group: str,
    agent_version: str,
    experiment_name: str,
    slice_identity: Any,
) -> list[dict[str, Any]]:
    _validate_column_mapping(column_mapping)

    object_buckets = {
        target.split(".", 1)[0]
        for target in column_mapping.values()
        if "." in target
    }

    rows: list[dict[str, Any]] = []
    for raw_row in selected_rows:
        normalized_row = _normalize_diagnostic_row(raw_row)
        projection = project_diagnostic_metadata(
            row=normalized_row,
            dataset_name=dataset_name,
            dataset_version=dataset_version,
            run_label=run_label,
            run_group=run_group,
            agent_version=agent_version,
            experiment_name=experiment_name,
            slice_identity=slice_identity,
        )
        row_data: dict[str, Any] = {"input": {}, "expected": {}, "metadata": {}}
        scalar_input: Any = None
        has_scalar_input = False

        for source_column, target_path in column_mapping.items():
            converted_value = _convert_cell(raw_row.get(source_column))
            target_parts = target_path.split(".")
            bucket_name = target_parts[0]

            if len(target_parts) == 1:
                if bucket_name == "input":
                    if bucket_name not in object_buckets:
                        scalar_input = converted_value
                        has_scalar_input = True
                else:
                    if bucket_name not in object_buckets:
                        row_data[bucket_name] = converted_value
                continue

            bucket_value = row_data.get(bucket_name)
            if not isinstance(bucket_value, dict):
                bucket_value = {}
                row_data[bucket_name] = bucket_value
            _set_nested_value(bucket_value, target_parts[1:], converted_value)

        if "input" in object_buckets:
            if not isinstance(row_data["input"], dict):
                row_data["input"] = {}
        elif has_scalar_input:
            row_data["input"] = scalar_input

        if not isinstance(row_data["input"], dict):
            raise TypeError("Diagnostic task input must be a mapping")
        row_data["input"]["session_id"] = projection.session_id
        row_data["input"]["trace_metadata"] = projection.langfuse_metadata
        row_data["expected"] = {}
        row_data["metadata"] = projection.braintrust_metadata
        row_data["id"] = projection.braintrust_metadata["row_id"]
        rows.append(row_data)

    return rows


def _normalize_diagnostic_row(raw_row: dict[str, str]) -> dict[str, object]:
    normalized: dict[str, object] = {}
    for key, value in raw_row.items():
        if value == "":
            normalized[key] = None
            continue
        if key == "draft_pass_signals":
            normalized[key] = json.loads(value)
            continue
        normalized[key] = value
    return normalized


def _build_default_run_label() -> str:
    """Build the default manual diagnostic run label in UTC."""
    return f"manual-{datetime.now(tz=timezone.utc).strftime('%Y%m%d-%H%M%S')}"


def _run_local_eval(
    raw_data: list[dict[str, Any]],
    task_fn: Any,
    scorers: list[Any],
) -> Any:
    """Run evaluation locally without braintrust dependency.

    Iterates over *raw_data*, calls *task_fn* for each row, then runs every
    scorer.  Returns a ``SimpleNamespace`` whose ``.results`` list mirrors the
    shape produced by ``braintrust.Eval``.
    """
    from types import SimpleNamespace

    is_async_task = asyncio.iscoroutinefunction(task_fn)

    def _score_row(row: dict[str, Any], output: Any) -> SimpleNamespace:
        expected_val = row.get("expected")
        metadata_val = row.get("metadata")
        scores: dict[str, Any] = {}
        for scorer in scorers:
            name = getattr(scorer, "__name__", "unknown")
            score = scorer(
                output=output,
                expected=expected_val,
                input=row["input"],
                metadata=metadata_val,
            )
            if score == _SKIPPED_MARKER:
                scores[name] = _SKIPPED_MARKER
            elif score is not None and hasattr(score, "score"):
                scores[name] = score.score
            else:
                scores[name] = score
        return SimpleNamespace(input=row["input"], output=output, scores=scores)

    if is_async_task:

        async def _run_all() -> list[SimpleNamespace]:
            res: list[SimpleNamespace] = []
            for row in raw_data:
                output = await task_fn(row["input"])
                res.append(_score_row(row, output))
            return res

        return SimpleNamespace(results=asyncio.run(_run_all()))

    results: list[Any] = []
    for row in raw_data:
        output = task_fn(row["input"])
        results.append(_score_row(row, output))
    return SimpleNamespace(results=results)


def _init_platform_tracing(project: str, api_key: str) -> None:
    """Initialize Braintrust platform tracing for non-local mode.

    WARNING: set_global_handler() sets a process-level singleton. This means:
    - Eval scenarios MUST run sequentially (not in parallel).
    - Previous handler state is NOT restored after the call.
    - If this module is reused in the same process, traces from different
      experiments may leak into each other.
    Concurrent eval execution requires per-request trace isolation, which
    Braintrust's current API does not support.
    """
    from braintrust import init_logger

    init_logger(project=project, api_key=api_key)

    from braintrust_langchain import BraintrustCallbackHandler, set_global_handler

    handler = BraintrustCallbackHandler()
    set_global_handler(handler)


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
    parser.add_argument(
        "--local-only", action="store_true", help="Skip platform logging"
    )
    parser.add_argument(
        "--output-dir", type=Path, default=None, help="Output directory for results"
    )
    parser.add_argument("--run-label", help="Diagnostic run label")
    parser.add_argument("--run-group", help="Diagnostic run group")
    parser.add_argument("--agent-version", help="Diagnostic agent version")
    parser.add_argument("--slice-label", help="Diagnostic slice label override")
    parser.add_argument("--row-ids", help="Diagnostic comma-separated row ids")
    parser.add_argument("--field-filter", help="Diagnostic field filter column=value")
    parser.add_argument("--manifest", help="Diagnostic manifest file path")

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

        # Detect duplicate config names across scenarios
        _check_duplicate_config_names(available, scenarios_dir)

        succeeded = 0
        skipped = 0
        for name in available:
            try:
                result_path = run_scenario(
                    name,
                    local_only=args.local_only,
                    output_dir=output_dir,
                    scenarios_dir=scenarios_dir,
                    run_label=args.run_label,
                    run_group=args.run_group,
                    agent_version=args.agent_version,
                    slice_label=args.slice_label,
                    row_ids=args.row_ids,
                    field_filter=args.field_filter,
                    manifest=args.manifest,
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
        run_label=args.run_label,
        run_group=args.run_group,
        agent_version=args.agent_version,
        slice_label=args.slice_label,
        row_ids=args.row_ids,
        field_filter=args.field_filter,
        manifest=args.manifest,
    )
    print(f"Result: {result_path}")


def _check_duplicate_config_names(
    scenario_dirs: list[str], scenarios_dir: Path
) -> None:
    """Warn if multiple scenario directories share the same config name."""
    seen: dict[str, str] = {}
    for dir_name in scenario_dirs:
        config_path = scenarios_dir / dir_name / "eval_spec.yaml"
        try:
            config = load_scenario_config(config_path)
        except (ValueError, FileNotFoundError) as exc:
            logger.warning("Could not load config for scenario '%s': %s", dir_name, exc)
            continue
        if config.name in seen:
            logger.warning(
                "Duplicate experiment name '%s' found in scenarios '%s' and '%s'",
                config.name,
                seen[config.name],
                dir_name,
            )
        else:
            seen[config.name] = dir_name


if __name__ == "__main__":
    main()
