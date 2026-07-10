from __future__ import annotations

import csv
from pathlib import Path

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


def _score_row(**overrides: str) -> dict[str, str]:
    row = {
        "trace_id": "trace-1",
        "session_id": "near_v1_diagnostic::smoke-local::1",
        "name": "observed_outcome",
        "source": "ANNOTATION",
        "observation_id": "",
        "data_type": "CATEGORICAL",
        "value": "",
        "string_value": "",
        "comment": "",
        "created_at": "2026-04-24T12:00:00Z",
        "updated_at": "",
    }
    row.update(overrides)
    return row


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
        writer.writerows(rows)


def _join(tmp_path: Path, rows: list[dict[str, str]]) -> list[dict[str, str]]:
    dataset_path = tmp_path / "dataset.csv"
    scores_path = tmp_path / "scores.csv"
    _write_dataset_csv(dataset_path)
    _write_scores_csv(scores_path, rows)
    return join_annotation_export(
        dataset_path=dataset_path,
        scores_export_path=scores_path,
        dataset_name="near_v1_diagnostic",
        run_label="smoke-local",
    )


def test_join_pivots_trace_level_annotations_and_preserves_order(
    tmp_path: Path,
) -> None:
    joined = _join(
        tmp_path,
        [
            _score_row(name="observed_outcome", string_value="acceptable_answer"),
            _score_row(name="review_comment", data_type="TEXT", comment="good enough"),
        ],
    )

    assert [row["id"] for row in joined] == ["1", "2"]
    assert joined[0]["observed_outcome"] == "acceptable_answer"
    assert joined[0]["review_comment"] == "good enough"
    assert joined[0]["langfuse_trace_id"] == "trace-1"
    assert joined[0]["langfuse_session_id"] == "near_v1_diagnostic::smoke-local::1"
    # Rows without any annotation keep empty reviewer columns.
    assert joined[1]["observed_outcome"] == ""
    assert joined[1]["langfuse_trace_id"] == ""


def test_join_keeps_first_score_for_duplicate_session_and_name(
    tmp_path: Path,
) -> None:
    joined = _join(
        tmp_path,
        [
            _score_row(trace_id="trace-1", string_value="partial_answer"),
            _score_row(trace_id="trace-2", string_value="strong_answer"),
        ],
    )

    assert joined[0]["observed_outcome"] == "partial_answer"
    assert joined[0]["langfuse_trace_id"] == "trace-1"


def test_join_normalizes_boolean_and_filters_non_annotation_rows(
    tmp_path: Path,
) -> None:
    joined = _join(
        tmp_path,
        [
            _score_row(name="needs_followup", data_type="BOOLEAN", value="1"),
            _score_row(name="observed_outcome", source="MODEL", string_value="failed_cleanly"),
        ],
    )

    assert joined[0]["needs_followup"] == "true"
    assert joined[0]["observed_outcome"] == ""


def test_join_outputs_short_langfuse_score_name_as_is(tmp_path: Path) -> None:
    joined = _join(
        tmp_path,
        [
            _score_row(
                name="obs_secondary_failure_mechanism",
                string_value="source_coverage_gap",
            ),
        ],
    )

    assert joined[0]["obs_secondary_failure_mechanism"] == "source_coverage_gap"
    assert "observed_secondary_failure_mechanism" not in joined[0]


def test_join_does_not_fallback_to_comment_for_non_review_text_fields(
    tmp_path: Path,
) -> None:
    joined = _join(
        tmp_path,
        [
            _score_row(
                name="observed_primary_failure_mechanism",
                data_type="TEXT",
                comment="tool_routing_error",
            ),
        ],
    )

    assert joined[0]["observed_primary_failure_mechanism"] == ""


def test_join_requires_trace_level_annotations(tmp_path: Path) -> None:
    joined = _join(
        tmp_path,
        [_score_row(observation_id="obs-123", string_value="acceptable_answer")],
    )

    assert joined[0]["observed_outcome"] == ""


def test_join_ignores_non_matching_and_malformed_sessions(tmp_path: Path) -> None:
    joined = _join(
        tmp_path,
        [
            _score_row(session_id="broken-session-id", string_value="failed_cleanly"),
            _score_row(
                session_id="other_dataset::smoke-local::1",
                string_value="failed_cleanly",
            ),
            _score_row(string_value="acceptable_answer"),
        ],
    )

    assert joined[0]["observed_outcome"] == "acceptable_answer"


def test_join_cli_writes_discussion_csv(tmp_path: Path) -> None:
    dataset_path = tmp_path / "dataset.csv"
    scores_path = tmp_path / "scores.csv"
    output_path = tmp_path / "discussion.csv"
    _write_dataset_csv(dataset_path)
    _write_scores_csv(scores_path, [_score_row(string_value="acceptable_answer")])

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
    assert rows[1]["observed_outcome"] == ""
