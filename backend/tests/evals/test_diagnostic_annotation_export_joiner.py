from __future__ import annotations

import csv
from pathlib import Path

import pytest

from backend.evals.diagnostic.annotation_export_joiner import (
    join_annotation_export,
    main,
)


def _write_dataset_csv(path: Path) -> None:
    path.write_text(
        "\n".join(
            [
                "id,question,category",
                '1,"Question one",news',
                '2,"Question two",boundary',
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def _write_scores_csv(path: Path, rows: list[dict[str, str]]) -> None:
    fieldnames = [
        "trace_id",
        "session_id",
        "name",
        "source",
        "observation_id",
        "data_type",
        "value",
        "string_value",
        "comment",
        "created_at",
        "updated_at",
    ]
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def test_join_annotation_export_pivots_trace_level_annotations_and_preserves_order(
    tmp_path: Path,
) -> None:
    dataset_path = tmp_path / "dataset.csv"
    scores_path = tmp_path / "scores.csv"
    _write_dataset_csv(dataset_path)
    _write_scores_csv(
        scores_path,
        [
            {
                "trace_id": "trace-1",
                "session_id": "near_v1_diagnostic::smoke-local::1",
                "name": "observed_outcome",
                "source": "ANNOTATION",
                "observation_id": "",
                "data_type": "CATEGORICAL",
                "value": "",
                "string_value": "acceptable_answer",
                "comment": "",
                "created_at": "2026-04-24T12:00:00Z",
                "updated_at": "2026-04-24T12:00:00Z",
            },
            {
                "trace_id": "trace-1",
                "session_id": "near_v1_diagnostic::smoke-local::1",
                "name": "review_comment",
                "source": "ANNOTATION",
                "observation_id": "",
                "data_type": "TEXT",
                "value": "",
                "string_value": "",
                "comment": "good enough",
                "created_at": "2026-04-24T12:00:01Z",
                "updated_at": "2026-04-24T12:00:01Z",
            },
        ],
    )

    joined = join_annotation_export(
        dataset_path=dataset_path,
        scores_export_path=scores_path,
        dataset_name="near_v1_diagnostic",
        run_label="smoke-local",
    )

    assert [row["id"] for row in joined] == ["1", "2"]
    assert joined[0]["observed_outcome"] == "acceptable_answer"
    assert joined[0]["review_comment"] == "good enough"
    assert joined[0]["langfuse_trace_id"] == "trace-1"
    assert joined[0]["langfuse_session_id"] == "near_v1_diagnostic::smoke-local::1"
    assert joined[0]["join_status"] == "partial_annotation"
    assert joined[1]["join_status"] == "missing_annotation"


def test_join_annotation_export_picks_latest_score_per_session_and_name(
    tmp_path: Path,
) -> None:
    dataset_path = tmp_path / "dataset.csv"
    scores_path = tmp_path / "scores.csv"
    _write_dataset_csv(dataset_path)
    _write_scores_csv(
        scores_path,
        [
            {
                "trace_id": "trace-1",
                "session_id": "near_v1_diagnostic::smoke-local::1",
                "name": "observed_outcome",
                "source": "ANNOTATION",
                "observation_id": "",
                "data_type": "CATEGORICAL",
                "value": "",
                "string_value": "partial_answer",
                "comment": "",
                "created_at": "2026-04-24T12:00:00Z",
                "updated_at": "2026-04-24T12:00:00Z",
            },
            {
                "trace_id": "trace-2",
                "session_id": "near_v1_diagnostic::smoke-local::1",
                "name": "observed_outcome",
                "source": "ANNOTATION",
                "observation_id": "",
                "data_type": "CATEGORICAL",
                "value": "",
                "string_value": "strong_answer",
                "comment": "",
                "created_at": "2026-04-24T12:00:00Z",
                "updated_at": "2026-04-24T12:05:00Z",
            },
        ],
    )

    joined = join_annotation_export(
        dataset_path=dataset_path,
        scores_export_path=scores_path,
        dataset_name="near_v1_diagnostic",
        run_label="smoke-local",
    )

    assert joined[0]["observed_outcome"] == "strong_answer"
    assert joined[0]["langfuse_trace_id"] == "trace-2"


def test_join_annotation_export_normalizes_boolean_and_filters_non_annotation_rows(
    tmp_path: Path,
) -> None:
    dataset_path = tmp_path / "dataset.csv"
    scores_path = tmp_path / "scores.csv"
    _write_dataset_csv(dataset_path)
    _write_scores_csv(
        scores_path,
        [
            {
                "trace_id": "trace-1",
                "session_id": "near_v1_diagnostic::smoke-local::1",
                "name": "needs_followup",
                "source": "ANNOTATION",
                "observation_id": "",
                "data_type": "BOOLEAN",
                "value": "1",
                "string_value": "",
                "comment": "",
                "created_at": "2026-04-24T12:00:00Z",
                "updated_at": "",
            },
            {
                "trace_id": "trace-1",
                "session_id": "near_v1_diagnostic::smoke-local::1",
                "name": "observed_outcome",
                "source": "MODEL",
                "observation_id": "",
                "data_type": "CATEGORICAL",
                "value": "",
                "string_value": "failed_cleanly",
                "comment": "",
                "created_at": "2026-04-24T12:00:00Z",
                "updated_at": "",
            },
        ],
    )

    joined = join_annotation_export(
        dataset_path=dataset_path,
        scores_export_path=scores_path,
        dataset_name="near_v1_diagnostic",
        run_label="smoke-local",
    )

    assert joined[0]["needs_followup"] == "true"
    assert joined[0]["observed_outcome"] == ""


def test_join_annotation_export_does_not_fallback_to_comment_for_non_review_text_fields(
    tmp_path: Path,
) -> None:
    dataset_path = tmp_path / "dataset.csv"
    scores_path = tmp_path / "scores.csv"
    _write_dataset_csv(dataset_path)
    _write_scores_csv(
        scores_path,
        [
            {
                "trace_id": "trace-1",
                "session_id": "near_v1_diagnostic::smoke-local::1",
                "name": "observed_primary_failure_mechanism",
                "source": "ANNOTATION",
                "observation_id": "",
                "data_type": "TEXT",
                "value": "",
                "string_value": "",
                "comment": "tool_routing_error",
                "created_at": "2026-04-24T12:00:00Z",
                "updated_at": "",
            },
        ],
    )

    joined = join_annotation_export(
        dataset_path=dataset_path,
        scores_export_path=scores_path,
        dataset_name="near_v1_diagnostic",
        run_label="smoke-local",
    )

    assert joined[0]["observed_primary_failure_mechanism"] == ""


def test_join_annotation_export_requires_trace_level_annotations(
    tmp_path: Path,
) -> None:
    dataset_path = tmp_path / "dataset.csv"
    scores_path = tmp_path / "scores.csv"
    _write_dataset_csv(dataset_path)
    _write_scores_csv(
        scores_path,
        [
            {
                "trace_id": "trace-1",
                "session_id": "near_v1_diagnostic::smoke-local::1",
                "name": "observed_outcome",
                "source": "ANNOTATION",
                "observation_id": "obs-123",
                "data_type": "CATEGORICAL",
                "value": "",
                "string_value": "acceptable_answer",
                "comment": "",
                "created_at": "2026-04-24T12:00:00Z",
                "updated_at": "",
            },
        ],
    )

    joined = join_annotation_export(
        dataset_path=dataset_path,
        scores_export_path=scores_path,
        dataset_name="near_v1_diagnostic",
        run_label="smoke-local",
    )

    assert joined[0]["join_status"] == "missing_annotation"


def test_join_annotation_export_rejects_malformed_target_session_ids(
    tmp_path: Path,
) -> None:
    dataset_path = tmp_path / "dataset.csv"
    scores_path = tmp_path / "scores.csv"
    _write_dataset_csv(dataset_path)
    _write_scores_csv(
        scores_path,
        [
            {
                "trace_id": "trace-1",
                "session_id": "near_v1_diagnostic::smoke-local",
                "name": "observed_outcome",
                "source": "ANNOTATION",
                "observation_id": "",
                "data_type": "CATEGORICAL",
                "value": "",
                "string_value": "acceptable_answer",
                "comment": "",
                "created_at": "2026-04-24T12:00:00Z",
                "updated_at": "",
            },
        ],
    )

    with pytest.raises(ValueError, match="Invalid diagnostic session_id"):
        join_annotation_export(
            dataset_path=dataset_path,
            scores_export_path=scores_path,
            dataset_name="near_v1_diagnostic",
            run_label="smoke-local",
        )


def test_join_annotation_export_ignores_unrelated_malformed_session_ids(
    tmp_path: Path,
) -> None:
    dataset_path = tmp_path / "dataset.csv"
    scores_path = tmp_path / "scores.csv"
    _write_dataset_csv(dataset_path)
    _write_scores_csv(
        scores_path,
        [
            {
                "trace_id": "trace-x",
                "session_id": "broken-session-id",
                "name": "observed_outcome",
                "source": "ANNOTATION",
                "observation_id": "",
                "data_type": "CATEGORICAL",
                "value": "",
                "string_value": "failed_cleanly",
                "comment": "",
                "created_at": "2026-04-24T12:00:00Z",
                "updated_at": "",
            },
            {
                "trace_id": "trace-1",
                "session_id": "near_v1_diagnostic::smoke-local::1",
                "name": "observed_outcome",
                "source": "ANNOTATION",
                "observation_id": "",
                "data_type": "CATEGORICAL",
                "value": "",
                "string_value": "acceptable_answer",
                "comment": "",
                "created_at": "2026-04-24T12:00:00Z",
                "updated_at": "",
            },
        ],
    )

    joined = join_annotation_export(
        dataset_path=dataset_path,
        scores_export_path=scores_path,
        dataset_name="near_v1_diagnostic",
        run_label="smoke-local",
    )

    assert joined[0]["observed_outcome"] == "acceptable_answer"
    assert joined[1]["join_status"] == "missing_annotation"


def test_join_annotation_export_ignores_malformed_rows_with_target_substring_noise(
    tmp_path: Path,
) -> None:
    dataset_path = tmp_path / "dataset.csv"
    scores_path = tmp_path / "scores.csv"
    _write_dataset_csv(dataset_path)
    _write_scores_csv(
        scores_path,
        [
            {
                "trace_id": "trace-x",
                "session_id": "notes-about-near_v1_diagnostic-smoke-local",
                "name": "observed_outcome",
                "source": "ANNOTATION",
                "observation_id": "",
                "data_type": "CATEGORICAL",
                "value": "",
                "string_value": "failed_cleanly",
                "comment": "",
                "created_at": "2026-04-24T12:00:00Z",
                "updated_at": "",
            },
            {
                "trace_id": "trace-1",
                "session_id": "near_v1_diagnostic::smoke-local::1",
                "name": "observed_outcome",
                "source": "ANNOTATION",
                "observation_id": "",
                "data_type": "CATEGORICAL",
                "value": "",
                "string_value": "acceptable_answer",
                "comment": "",
                "created_at": "2026-04-24T12:00:00Z",
                "updated_at": "",
            },
        ],
    )

    joined = join_annotation_export(
        dataset_path=dataset_path,
        scores_export_path=scores_path,
        dataset_name="near_v1_diagnostic",
        run_label="smoke-local",
    )

    assert joined[0]["observed_outcome"] == "acceptable_answer"


def test_join_annotation_export_marks_complete_annotation_as_annotated(
    tmp_path: Path,
) -> None:
    dataset_path = tmp_path / "dataset.csv"
    scores_path = tmp_path / "scores.csv"
    _write_dataset_csv(dataset_path)
    _write_scores_csv(
        scores_path,
        [
            {
                "trace_id": "trace-1",
                "session_id": "near_v1_diagnostic::smoke-local::1",
                "name": "observed_outcome",
                "source": "ANNOTATION",
                "observation_id": "",
                "data_type": "CATEGORICAL",
                "value": "",
                "string_value": "strong_answer",
                "comment": "",
                "created_at": "2026-04-24T12:00:00Z",
                "updated_at": "",
            },
            {
                "trace_id": "trace-1",
                "session_id": "near_v1_diagnostic::smoke-local::1",
                "name": "observed_alignment_to_prompt",
                "source": "ANNOTATION",
                "observation_id": "",
                "data_type": "CATEGORICAL",
                "value": "",
                "string_value": "high",
                "comment": "",
                "created_at": "2026-04-24T12:00:00Z",
                "updated_at": "",
            },
            {
                "trace_id": "trace-1",
                "session_id": "near_v1_diagnostic::smoke-local::1",
                "name": "review_confidence",
                "source": "ANNOTATION",
                "observation_id": "",
                "data_type": "CATEGORICAL",
                "value": "",
                "string_value": "high",
                "comment": "",
                "created_at": "2026-04-24T12:00:00Z",
                "updated_at": "",
            },
            {
                "trace_id": "trace-1",
                "session_id": "near_v1_diagnostic::smoke-local::1",
                "name": "review_comment",
                "source": "ANNOTATION",
                "observation_id": "",
                "data_type": "TEXT",
                "value": "",
                "string_value": "clear answer",
                "comment": "",
                "created_at": "2026-04-24T12:00:00Z",
                "updated_at": "",
            },
        ],
    )

    joined = join_annotation_export(
        dataset_path=dataset_path,
        scores_export_path=scores_path,
        dataset_name="near_v1_diagnostic",
        run_label="smoke-local",
    )

    assert joined[0]["join_status"] == "annotated"


def test_join_annotation_export_cli_writes_discussion_csv(tmp_path: Path) -> None:
    dataset_path = tmp_path / "dataset.csv"
    scores_path = tmp_path / "scores.csv"
    output_path = tmp_path / "discussion.csv"
    _write_dataset_csv(dataset_path)
    _write_scores_csv(
        scores_path,
        [
            {
                "trace_id": "trace-1",
                "session_id": "near_v1_diagnostic::smoke-local::1",
                "name": "observed_outcome",
                "source": "ANNOTATION",
                "observation_id": "",
                "data_type": "CATEGORICAL",
                "value": "",
                "string_value": "acceptable_answer",
                "comment": "",
                "created_at": "2026-04-24T12:00:00Z",
                "updated_at": "",
            },
        ],
    )

    main(
        [
            "--dataset",
            str(dataset_path),
            "--scores-export",
            str(scores_path),
            "--dataset-name",
            "near_v1_diagnostic",
            "--run-label",
            "smoke-local",
            "--output",
            str(output_path),
        ]
    )

    with output_path.open("r", encoding="utf-8") as file:
        rows = list(csv.DictReader(file))

    assert rows[0]["observed_outcome"] == "acceptable_answer"
    assert rows[1]["join_status"] == "missing_annotation"
