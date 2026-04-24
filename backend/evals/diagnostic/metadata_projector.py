"""Projection helpers for diagnostic execution metadata."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from typing import Mapping

from backend.evals.diagnostic.models import DiagnosticSliceIdentity


@dataclass(frozen=True)
class DiagnosticMetadataProjection:
    """Projected metadata shared across execution and tracing systems."""

    session_id: str
    braintrust_metadata: dict[str, object]
    langfuse_metadata: dict[str, object]


def build_diagnostic_session_id(
    *, dataset_name: str, run_label: str, row_id: str
) -> str:
    """Build a deterministic session id for one diagnostic row execution."""
    _validate_session_component("dataset_name", dataset_name)
    _validate_session_component("run_label", run_label)
    _validate_session_component("row_id", row_id)
    return f"{dataset_name}::{run_label}::{row_id}"


def project_diagnostic_metadata(
    *,
    row: Mapping[str, object],
    dataset_name: str,
    dataset_version: str,
    run_label: str,
    run_group: str,
    agent_version: str,
    experiment_name: str,
    slice_identity: DiagnosticSliceIdentity,
) -> DiagnosticMetadataProjection:
    """Project one canonical metadata bundle for diagnostic execution."""
    row_id = _require_str(row, "id")
    capability_band = _require_str(row, "capability_band")

    identity_metadata: dict[str, object] = {
        "row_id": row_id,
        "dataset_name": dataset_name,
        "dataset_version": dataset_version,
        "run_label": run_label,
        "run_group": run_group,
        "agent_version": agent_version,
        "slice_label": slice_identity.slice_label,
        "slice_type": slice_identity.slice_type,
    }

    braintrust_metadata = {
        **identity_metadata,
        "category": _require_str(row, "category"),
        "capability_band": capability_band,
    }
    langfuse_metadata = {
        **identity_metadata,
        "experiment_name": experiment_name,
        "slice_selector": slice_identity.slice_selector,
        "reference_capability_band": capability_band,
        "reference_expected_behavior": _require_str(
            row, "expected_near_v1_behavior"
        ),
        "reference_primary_failure_mechanism": _require_str(
            row, "primary_failure_mechanism"
        ),
        "reference_secondary_failure_mechanism": _optional_str(
            row, "secondary_failure_mechanism"
        ),
        "reference_best_source": _require_str(row, "expected_best_source"),
        "reference_likely_tuning_lever": _require_str(
            row, "likely_tuning_lever"
        ),
        "reference_pass_signals": deepcopy(row["draft_pass_signals"]),
    }

    return DiagnosticMetadataProjection(
        session_id=build_diagnostic_session_id(
            dataset_name=dataset_name,
            run_label=run_label,
            row_id=row_id,
        ),
        braintrust_metadata=braintrust_metadata,
        langfuse_metadata=langfuse_metadata,
    )


def _validate_session_component(field_name: str, value: str) -> None:
    if "::" in value:
        raise ValueError(f"{field_name} must not contain '::'")


def _require_str(row: Mapping[str, object], key: str) -> str:
    value = row[key]
    if not isinstance(value, str):
        raise TypeError(f"{key} must be a string")
    return value


def _optional_str(row: Mapping[str, object], key: str) -> str | None:
    value = row.get(key)
    if value is None:
        return None
    if not isinstance(value, str):
        raise TypeError(f"{key} must be a string when provided")
    return value
