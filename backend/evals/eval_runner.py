"""Eval Runner: scenario discovery + Braintrust Eval() assembly + result CSV output.

Usage:
    python -m backend.evals.eval_runner language_policy
    python -m backend.evals.eval_runner --all
    python -m backend.evals.eval_runner language_policy --upload
    python -m backend.evals.eval_runner language_policy --output-dir ./results
"""

from __future__ import annotations

import asyncio
import csv
import functools
import inspect
import json
import logging
import os
import re
import subprocess
import sys
from collections.abc import Sequence
from copy import deepcopy
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from braintrust import Eval, EvalCase
from dotenv import load_dotenv

from backend.evals.dataset_loader import (
    apply_column_mapping,
    load_dataset,
    load_raw_csv_rows,
)
from backend.evals.diagnostic.row_selection import select_diagnostic_rows
from backend.evals.eval_spec_schema import (
    BraintrustConfig,
    load_braintrust_config,
    load_scenario_config,
)
from backend.evals.scorer_registry import resolve_function, resolve_scorers

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

SCENARIOS_DIR = Path(__file__).parent / "scenarios"
DEFAULT_RESULTS_DIR = Path(__file__).parent / "results"
BRAINTRUST_CONFIG_PATH = Path(__file__).parent / "braintrust_config.yaml"

_VALID_SCENARIO_DIR_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]*$")

# Braintrust's default is unbounded concurrency (every dataset row at once);
# the official KB ("Controlling Concurrency to Prevent Resource Exhaustion")
# recommends 10-20, starting with 10, to avoid provider rate limits.
MAX_CONCURRENCY = 10


logger = logging.getLogger(__name__)

# CSV sentinels: written only at the write_result_csv layer. In memory, scores
# and outputs stay in the SDK's own vocabulary (a number, None, or a raised
# exception) all the way through Eval().
_ERROR_MARKER = "ERROR"
_SKIPPED_MARKER = "SKIPPED"


@dataclass(frozen=True)
class CaseResult:
    """Per-case outcome of a scenario run, in the SDK's own vocabulary.

    ``scores`` maps scorer name to its score, with ``None`` covering both a
    deliberate skip and a scorer error — ``scorer_errors`` names which of the
    two it was. ``task_error`` is set when the task function itself raised,
    in which case every scorer is absent for the case.
    """

    case_id: str
    scores: dict[str, float | None] = field(default_factory=dict)
    scorer_errors: frozenset[str] = frozenset()
    task_error: str | None = None


@dataclass(frozen=True)
class ScenarioRunResult:
    """Structured result of ``run_scenario`` — scores stay in memory.

    Downstream verdicts (the regression gate) consume ``case_results``
    directly instead of re-parsing the result CSV, whose ERROR/SKIPPED
    sentinels are a human-facing report format, not an API.
    """

    scenario_name: str
    scorer_names: list[str]
    case_results: list[CaseResult]
    csv_path: Path
    is_full_dataset: bool


def case_identifier(row: dict[str, str], index: int) -> str:
    """Stable case identifier: the dataset's ``id`` column, else 1-based index."""
    row_id = row.get("id", "").strip()
    return row_id if row_id else f"case-{index + 1:02d}"


def _accepts_profile(fn: Any) -> bool:
    """True when *fn* declares an explicit ``profile`` parameter.

    Deliberately ignores ``**kwargs``: profile injection is opt-in by
    signature (``run_profile`` accepts, ``run_sec_retrieval`` does not).
    """
    try:
        sig = inspect.signature(fn)
    except (ValueError, TypeError):
        return False
    param = sig.parameters.get("profile")
    return param is not None and param.kind in (
        inspect.Parameter.POSITIONAL_OR_KEYWORD,
        inspect.Parameter.KEYWORD_ONLY,
    )


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


def _git_sha() -> str:
    """Resolve the current commit for the CSV provenance column.

    Appends ``-dirty`` when the working tree has uncommitted changes (the
    ``git describe --dirty`` naming convention), so a permanent result row
    honestly flags itself as not exactly replayable. Falls back to
    ``"unknown"`` when git is unavailable — a failed provenance lookup must
    never block a run.
    """

    def run_git(*args: str, cwd: Path) -> str:
        return subprocess.run(
            ["git", *args], capture_output=True, text=True, check=True, cwd=cwd
        ).stdout.strip()

    try:
        cwd = Path(__file__).parent
        sha = run_git("rev-parse", "HEAD", cwd=cwd)
        dirty = run_git("status", "--porcelain", cwd=cwd)
        return f"{sha}-dirty" if dirty else sha
    except (subprocess.CalledProcessError, OSError):
        return "unknown"


def _wrap_task(task_fn: Any, *, timeout: float | None = None) -> Any:
    """Wrap the task function with a per-task timeout (async tasks only).

    Always returns an async callable so Braintrust's ``Eval()`` awaits it
    directly; a sync ``task_fn`` runs via ``asyncio.to_thread``. Exceptions
    and a ``None`` return propagate unchanged — Braintrust's own per-row
    handling turns them into ``EvalResult.error``/``exc_info`` without
    aborting the run. A per-task timeout is needed here because
    ``Eval(timeout=...)`` bounds the whole run, not a single task.

    The per-task timeout is only supported for async task functions:
    ``asyncio.wait_for`` can cancel a coroutine, but a sync function running
    in a thread cannot be interrupted — the timeout would fire without
    actually stopping execution. Combining a sync ``task_fn`` with a timeout
    therefore raises ``ValueError`` at wrap time.
    """
    is_async = asyncio.iscoroutinefunction(task_fn)
    if not is_async and timeout is not None:
        raise ValueError(
            "Per-task timeout is not supported for sync task functions — "
            "Python threads cannot be interrupted, so the timeout could not "
            "actually stop execution. Make the task async (async def) to use "
            "task.timeout."
        )

    async def wrapped(input: Any) -> Any:
        coro = task_fn(input) if is_async else asyncio.to_thread(task_fn, input)
        if timeout is not None:
            result = await asyncio.wait_for(coro, timeout=timeout)
        else:
            result = await coro
        if result is None:
            raise ValueError(
                "Task function returned None. Ensure the function has a return statement."
            )
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
    """Wrap a scorer to filter kwargs it doesn't declare.

    Exceptions propagate to Braintrust's native per-scorer error handling:
    caught per-scorer, recorded in ``metadata["scorer_errors"]`` on the root
    span, the run continues, and that scorer's score is simply absent (not
    zero) for the row. A deliberate skip stays a plain ``None`` return, which
    Braintrust already treats as its native no-score signal.
    """

    def wrapped(*, output: Any, expected: Any, **kwargs: Any) -> Any:
        filtered = _filter_kwargs_for(scorer_fn, kwargs)
        result = scorer_fn(output=output, expected=expected, **filtered)
        if hasattr(result, "name"):
            result.name = scorer_name
        return result

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
    experiment_name: str = "",
    git_sha: str = "",
) -> Path:
    """Write eval results to a timestamped CSV file.

    The default output directory is gitignored; a run worth keeping becomes
    the permanent record only when the operator curates its CSV into a
    git-tracked location.

    Columns: original CSV columns (if provided) + output.* columns +
    output_json + score_{name} columns + experiment_name + git_sha.
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

    fieldnames = [
        *orig_cols,
        *all_output_keys,
        "output_json",
        *score_columns,
        "experiment_name",
        "git_sha",
    ]

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
            is_error_row = result.error is not None

            if is_error_row:
                for key in all_output_keys:
                    row[key] = _ERROR_MARKER
                # output_json is the replay source of truth; stuffing a
                # traceback in there would make it a union type (the same
                # skip/crash ambiguity this schema exists to avoid). The row
                # is reproducible from git_sha instead.
                row["output_json"] = ""
            else:
                for key in all_output_keys:
                    row[key] = flat_output.get(key, "")
                row["output_json"] = json.dumps(result.output, ensure_ascii=False)

            # Score columns
            scorer_errors = (result.metadata or {}).get("scorer_errors", {})
            for name in scorer_names:
                if is_error_row:
                    row[f"score_{name}"] = _ERROR_MARKER
                    continue
                score_val = result.scores.get(name)
                if score_val is None:
                    row[f"score_{name}"] = (
                        _ERROR_MARKER if name in scorer_errors else _SKIPPED_MARKER
                    )
                else:
                    row[f"score_{name}"] = str(score_val)

            row["experiment_name"] = experiment_name
            row["git_sha"] = git_sha

            writer.writerow(row)

    return csv_path


def _require_upload_key(bt_config: BraintrustConfig) -> str:
    """Return the Braintrust API key for --upload, or hard-fail if missing.

    Called both up front in ``main()`` (so ``--all`` can't swallow a missing
    key as a per-scenario skip) and again in ``run_scenario()`` (so direct
    callers get the same guarantee without going through the CLI).
    """
    api_key = os.environ.get(bt_config.api_key_env)
    if not api_key:
        raise RuntimeError(
            f"--upload requires the '{bt_config.api_key_env}' environment "
            "variable. Set the key or drop --upload."
        )
    return api_key


def run_scenario(
    scenario_name: str,
    *,
    upload: bool,
    output_dir: Path,
    scenarios_dir: Path = SCENARIOS_DIR,
    run_label: str | None = None,
    row_ids: str | None = None,
    profile: str | None = None,
    case_ids: Sequence[str] | None = None,
) -> ScenarioRunResult:
    """Execute a single evaluation scenario via Braintrust ``Eval()``.

    Steps:
    1. If uploading, preflight the API key and init platform tracing before
       doing any other work (zero wasted execution on a missing key).
    2. Load eval_spec.yaml -> ScenarioConfig
    3. Validate CSV exists, load_dataset() -> data list
    4. resolve_scorers() -> scorer callables, dynamic import task function
    5. Eval() call (no_send_logs=not upload)
    6. write_result_csv(), return ScenarioRunResult

    ``profile`` is forwarded to the task function only when its signature
    declares a ``profile`` parameter; ``None`` means the function's own
    default applies. ``case_ids`` restricts the run to those dataset cases
    (matched by ``id`` column, else positional ``case-NN``) — the result then
    reports ``is_full_dataset=False`` so aggregate consumers can refuse it.
    """
    bt_config = load_braintrust_config(BRAINTRUST_CONFIG_PATH)

    if upload:
        api_key = _require_upload_key(bt_config)
        _init_platform_tracing(bt_config.project, api_key)

    scenario_dir = scenarios_dir / scenario_name
    config_path = scenario_dir / "eval_spec.yaml"
    config = load_scenario_config(config_path)

    diagnostic_flags = [run_label, row_ids]
    if config.diagnostic is None and any(
        value is not None for value in diagnostic_flags
    ):
        raise ValueError("Diagnostic flags are only supported for diagnostic scenarios")
    if config.diagnostic is not None and case_ids is not None:
        raise ValueError(
            "case_ids is not supported for diagnostic scenarios — use row_ids"
        )

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
            f"⚠ Scenario '{config.name}' is draft "
            f"— results may be unreliable. "
            f"Curate dataset before trusting metrics.",
            file=sys.stderr,
        )

    csv_path = scenario_dir / config.csv
    if not csv_path.is_file():
        raise FileNotFoundError(f"CSV file not found: {csv_path}")

    original_columns, original_rows = load_raw_csv_rows(csv_path)

    scorers = resolve_scorers(config.scorers)
    task_fn = resolve_function(config.task.function, label="task")
    if profile is not None and _accepts_profile(task_fn):
        task_fn = functools.partial(task_fn, profile=profile)

    scorer_names = [s.name for s in config.scorers]
    wrapped_task = _wrap_task(task_fn, timeout=config.task.timeout)
    wrapped_scorers = [
        _wrap_scorer(scorer, name) for scorer, name in zip(scorers, scorer_names)
    ]

    experiment_name = (
        f"{config.name}_{datetime.now(tz=timezone.utc).strftime('%Y%m%d_%H%M%S')}"
    )
    git_sha = _git_sha()

    if config.diagnostic is None:
        raw_data = load_dataset(csv_path, config.column_mapping, config.column_types)
        all_case_ids = [
            case_identifier(row, idx) for idx, row in enumerate(original_rows)
        ]
        is_full_dataset = case_ids is None or set(case_ids) >= set(all_case_ids)
        if case_ids is not None:
            selected = set(case_ids)
            unknown = sorted(selected - set(all_case_ids))
            if unknown:
                raise ValueError(
                    f"Unknown case ids {unknown} for scenario '{config.name}'. "
                    f"Available: {all_case_ids}"
                )
            selected_indices = [
                idx for idx, cid in enumerate(all_case_ids) if cid in selected
            ]
            raw_data = [raw_data[idx] for idx in selected_indices]
            original_rows = [original_rows[idx] for idx in selected_indices]
            all_case_ids = [all_case_ids[idx] for idx in selected_indices]
            banner_line += f" | Cases: {len(selected_indices)} (subset)"
        print(banner_line, file=sys.stderr)

        eval_cases = [
            EvalCase(
                input=row["input"],
                expected=row.get("expected"),
                metadata=row.get("metadata"),
            )
            for row in raw_data
        ]
        eval_metadata: dict[str, Any] | None = None
        csv_rows = original_rows
        result_case_ids = all_case_ids
    else:
        diagnostic_config = config.diagnostic
        effective_run_label = run_label or _build_default_run_label()
        effective_agent_version = diagnostic_config.agent_version

        selected_rows = select_diagnostic_rows(
            original_columns,
            original_rows,
            row_ids,
        )
        selected_row_ids = [row["id"] for row in selected_rows]
        diagnostic_data = _build_diagnostic_eval_rows(
            selected_rows=selected_rows,
            column_mapping=config.column_mapping,
            column_types=config.column_types,
            dataset_name=diagnostic_config.dataset_name,
            dataset_version=diagnostic_config.dataset_version,
            run_label=effective_run_label,
            agent_version=effective_agent_version,
            experiment_name=experiment_name,
        )
        banner_line += (
            f" | Run label: {effective_run_label}"
            f" | Git commit: {git_sha}"
            f" | Rows: {len(selected_rows)}/{len(original_rows)}"
        )
        print(banner_line, file=sys.stderr)

        eval_cases = [
            EvalCase(
                id=row["id"],
                input=row["input"],
                expected={},
                metadata=row.get("metadata"),
            )
            for row in diagnostic_data
        ]
        is_full_dataset = len(selected_rows) == len(original_rows)
        eval_metadata = {
            "dataset_name": diagnostic_config.dataset_name,
            "dataset_version": diagnostic_config.dataset_version,
            "run_label": effective_run_label,
            # A subset run must never be mistaken for an authoritative one:
            # record exactly which rows ran and whether that was all of them.
            "selected_row_ids": selected_row_ids,
            "is_full_dataset": is_full_dataset,
            "agent_version": effective_agent_version,
            "git_commit": git_sha,
        }
        csv_rows = selected_rows
        result_case_ids = selected_row_ids

    eval_result = Eval(
        bt_config.project,
        data=eval_cases,
        task=wrapped_task,
        scores=wrapped_scorers,
        experiment_name=experiment_name,
        metadata=eval_metadata,
        no_send_logs=not upload,
        max_concurrency=MAX_CONCURRENCY,
    )

    result_csv_path = write_result_csv(
        eval_result,
        scenario_name,
        scorer_names,
        output_dir,
        original_columns=original_columns,
        original_rows=csv_rows,
        experiment_name=experiment_name,
        git_sha=git_sha,
    )

    case_results: list[CaseResult] = []
    for idx, result in enumerate(eval_result.results):
        scorer_errors = frozenset((result.metadata or {}).get("scorer_errors", {}))
        case_results.append(
            CaseResult(
                case_id=(
                    result_case_ids[idx]
                    if idx < len(result_case_ids)
                    else case_identifier({}, idx)
                ),
                scores={name: result.scores.get(name) for name in scorer_names},
                scorer_errors=scorer_errors,
                task_error=str(result.error) if result.error is not None else None,
            )
        )

    return ScenarioRunResult(
        scenario_name=config.name,
        scorer_names=scorer_names,
        case_results=case_results,
        csv_path=result_csv_path,
        is_full_dataset=is_full_dataset,
    )


@dataclass(frozen=True)
class _DiagnosticMetadataProjection:
    """Projected metadata shared across execution and tracing systems."""

    session_id: str
    braintrust_metadata: dict[str, object]
    langfuse_metadata: dict[str, object]


def _build_diagnostic_session_id(
    *, dataset_name: str, run_label: str, row_id: str
) -> str:
    """Build a deterministic session id for one diagnostic row execution."""
    for field_name, value in (
        ("dataset_name", dataset_name),
        ("run_label", run_label),
        ("row_id", row_id),
    ):
        if "::" in value:
            raise ValueError(f"{field_name} must not contain '::'")
    return f"{dataset_name}::{run_label}::{row_id}"


def _project_diagnostic_metadata(
    *,
    row: dict[str, object],
    dataset_name: str,
    dataset_version: str,
    run_label: str,
    agent_version: str,
    experiment_name: str,
) -> _DiagnosticMetadataProjection:
    """Project one canonical metadata bundle for diagnostic execution."""
    row_id = _require_diagnostic_str(row, "id")
    capability_band = _require_diagnostic_str(row, "capability_band")

    identity_metadata: dict[str, object] = {
        "row_id": row_id,
        "dataset_name": dataset_name,
        "dataset_version": dataset_version,
        "run_label": run_label,
        "agent_version": agent_version,
    }

    braintrust_metadata = {
        **identity_metadata,
        "category": _require_diagnostic_str(row, "category"),
        "capability_band": capability_band,
    }
    langfuse_metadata = {
        **identity_metadata,
        "experiment_name": experiment_name,
        "reference_capability_band": capability_band,
        "reference_expected_behavior": _require_diagnostic_str(
            row, "expected_baseline_behavior"
        ),
        "reference_primary_failure_mechanism": _require_diagnostic_str(
            row, "primary_failure_mechanism"
        ),
        "reference_secondary_failure_mechanism": _optional_diagnostic_str(
            row, "secondary_failure_mechanism"
        ),
        "reference_best_source": _require_diagnostic_str(row, "expected_best_source"),
        "reference_likely_tuning_lever": _require_diagnostic_str(
            row, "likely_tuning_lever"
        ),
        "reference_pass_signals": deepcopy(row["draft_pass_signals"]),
    }

    return _DiagnosticMetadataProjection(
        session_id=_build_diagnostic_session_id(
            dataset_name=dataset_name,
            run_label=run_label,
            row_id=row_id,
        ),
        braintrust_metadata=braintrust_metadata,
        langfuse_metadata=langfuse_metadata,
    )


def _require_diagnostic_str(row: dict[str, object], key: str) -> str:
    value = row[key]
    if not isinstance(value, str):
        raise TypeError(f"{key} must be a string")
    return value


def _optional_diagnostic_str(row: dict[str, object], key: str) -> str | None:
    value = row.get(key)
    if value is None:
        return None
    if not isinstance(value, str):
        raise TypeError(f"{key} must be a string when provided")
    return value


def _build_diagnostic_eval_rows(
    *,
    selected_rows: list[dict[str, str]],
    column_mapping: dict[str, str],
    column_types: dict[str, str] | None,
    dataset_name: str,
    dataset_version: str,
    run_label: str,
    agent_version: str,
    experiment_name: str,
) -> list[dict[str, Any]]:
    """Build Eval rows for a diagnostic scenario.

    Column mapping goes through the shared ``apply_column_mapping`` helper —
    the same path ``load_dataset`` uses — then each row is enriched with the
    projected diagnostic identity (deterministic session id, Braintrust row
    metadata, Langfuse trace metadata).
    """
    rows: list[dict[str, Any]] = []
    for raw_row in selected_rows:
        normalized_row = _normalize_diagnostic_row(raw_row)
        projection = _project_diagnostic_metadata(
            row=normalized_row,
            dataset_name=dataset_name,
            dataset_version=dataset_version,
            run_label=run_label,
            agent_version=agent_version,
            experiment_name=experiment_name,
        )
        row_data = apply_column_mapping(raw_row, column_mapping, column_types)
        if not isinstance(row_data.get("input"), dict):
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


def _init_platform_tracing(project: str, api_key: str) -> None:
    """Initialize Braintrust platform tracing for --upload runs.

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

    from braintrust.integrations.langchain import (
        BraintrustCallbackHandler,
        set_global_handler,
    )

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
        "--upload",
        action="store_true",
        help="Upload the run to Braintrust as an experiment (default: local only)",
    )
    parser.add_argument(
        "--output-dir", type=Path, default=None, help="Output directory for results"
    )
    parser.add_argument("--run-label", help="Diagnostic run label")
    parser.add_argument(
        "--row-ids",
        help=(
            "Diagnostic comma-separated row ids — for smoke runs, debugging, and "
            "failed-row reruns only. Authoritative runs use the full dataset."
        ),
    )

    args = parser.parse_args(argv)

    if args.output_dir is not None:
        output_dir = args.output_dir

    if not args.all and not args.scenario:
        parser.error("Provide a scenario name or use --all")

    diagnostic_only_flags = [args.run_label, args.row_ids]
    if args.all and any(value is not None for value in diagnostic_only_flags):
        # Without this guard the --all loop would swallow the per-scenario
        # ValueError as SKIPPED and exit 0.
        parser.error("Diagnostic flags cannot be combined with --all")

    if args.upload:
        # Checked once, up front: --all's per-scenario try/except below must
        # never swallow a missing key as an ordinary scenario skip.
        _require_upload_key(load_braintrust_config(BRAINTRUST_CONFIG_PATH))

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
                run_result = run_scenario(
                    name,
                    upload=args.upload,
                    output_dir=output_dir,
                    scenarios_dir=scenarios_dir,
                    run_label=args.run_label,
                    row_ids=args.row_ids,
                )
                print(f"  {name}: {run_result.csv_path}")
                succeeded += 1
            except Exception as exc:
                print(f"  {name}: SKIPPED ({exc})", file=sys.stderr)
                skipped += 1

        print(f"{succeeded} succeeded, {skipped} skipped")
        if args.upload and skipped > 0:
            print(
                f"--upload run had {skipped} failed scenario(s) — treating as "
                "failure (see 'SKIPPED' lines above)",
                file=sys.stderr,
            )
            raise SystemExit(1)
        return

    if args.scenario not in available:
        print(
            f"Scenario '{args.scenario}' not found. Available: {', '.join(available)}",
            file=sys.stderr,
        )
        raise SystemExit(1)

    run_result = run_scenario(
        args.scenario,
        upload=args.upload,
        output_dir=output_dir,
        scenarios_dir=scenarios_dir,
        run_label=args.run_label,
        row_ids=args.row_ids,
    )
    print(f"Result: {run_result.csv_path}")


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
