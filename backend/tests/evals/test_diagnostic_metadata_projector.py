from __future__ import annotations

import pytest

from backend.evals.diagnostic.metadata_projector import (
    build_diagnostic_session_id,
    project_diagnostic_metadata,
)
from backend.evals.diagnostic.models import DiagnosticSliceIdentity


def _make_row() -> dict[str, object]:
    return {
        "id": "17",
        "category": "regulatory_or_legal_risk",
        "capability_band": "boundary",
        "expected_near_v1_behavior": "may_pass_with_tuning",
        "primary_failure_mechanism": "tool_routing_error",
        "secondary_failure_mechanism": "evidence_synthesis_limit",
        "expected_best_source": "mixed",
        "likely_tuning_lever": "tool_description",
        "draft_pass_signals": [
            "區分已發生行動與潛在壓力",
            "不要把媒體推測當成已落地結果",
        ],
        "why_near_v1_might_fail_or_pass": "should stay out of projected metadata",
    }


def _make_slice_identity() -> DiagnosticSliceIdentity:
    return DiagnosticSliceIdentity(
        slice_label="filter-capability-band-boundary",
        slice_type="field_filter",
        slice_selector="capability_band=boundary",
        selected_row_ids=("17",),
        slice_hash="abc123",
    )


def test_project_diagnostic_metadata_emits_exact_projection() -> None:
    projection = project_diagnostic_metadata(
        row=_make_row(),
        dataset_name="near_v1_diagnostic",
        dataset_version="2026-04-24",
        run_label="baseline",
        run_group="near-v1",
        agent_version="v1_baseline",
        experiment_name="near_v1_diagnostic_20260424_120000",
        slice_identity=_make_slice_identity(),
    )

    assert projection.session_id == "near_v1_diagnostic::baseline::17"
    assert projection.braintrust_metadata == {
        "row_id": "17",
        "dataset_name": "near_v1_diagnostic",
        "dataset_version": "2026-04-24",
        "run_label": "baseline",
        "run_group": "near-v1",
        "slice_label": "filter-capability-band-boundary",
        "slice_type": "field_filter",
        "agent_version": "v1_baseline",
        "category": "regulatory_or_legal_risk",
        "capability_band": "boundary",
    }
    assert projection.langfuse_metadata == {
        "row_id": "17",
        "dataset_name": "near_v1_diagnostic",
        "dataset_version": "2026-04-24",
        "run_label": "baseline",
        "run_group": "near-v1",
        "agent_version": "v1_baseline",
        "experiment_name": "near_v1_diagnostic_20260424_120000",
        "slice_label": "filter-capability-band-boundary",
        "slice_type": "field_filter",
        "slice_selector": "capability_band=boundary",
        "reference_capability_band": "boundary",
        "reference_expected_behavior": "may_pass_with_tuning",
        "reference_primary_failure_mechanism": "tool_routing_error",
        "reference_secondary_failure_mechanism": "evidence_synthesis_limit",
        "reference_best_source": "mixed",
        "reference_likely_tuning_lever": "tool_description",
        "reference_pass_signals": [
            "區分已發生行動與潛在壓力",
            "不要把媒體推測當成已落地結果",
        ],
    }
    assert "observed_capability_band" not in projection.langfuse_metadata
    assert "observed_expected_behavior" not in projection.langfuse_metadata
    assert (
        "why_near_v1_might_fail_or_pass"
        not in projection.langfuse_metadata
    )


def test_build_diagnostic_session_id_is_parseable() -> None:
    session_id = build_diagnostic_session_id(
        dataset_name="near_v1_diagnostic",
        run_label="baseline",
        row_id="42",
    )

    assert session_id.split("::") == ["near_v1_diagnostic", "baseline", "42"]


@pytest.mark.parametrize(
    ("field_name", "value"),
    [
        ("dataset_name", "near::v1"),
        ("run_label", "base::line"),
        ("row_id", "4::2"),
    ],
)
def test_build_diagnostic_session_id_rejects_reserved_delimiter(
    field_name: str, value: str
) -> None:
    kwargs = {
        "dataset_name": "near_v1_diagnostic",
        "run_label": "baseline",
        "row_id": "42",
    }
    kwargs[field_name] = value

    with pytest.raises(ValueError, match=r"must not contain '::'"):
        build_diagnostic_session_id(**kwargs)
