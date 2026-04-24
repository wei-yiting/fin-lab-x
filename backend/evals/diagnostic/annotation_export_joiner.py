"""Join Langfuse annotation score exports back to diagnostic dataset rows."""

from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from pathlib import Path

from backend.evals.dataset_loader import load_raw_csv_rows

ANNOTATION_OUTPUT_COLUMNS = [
    "observed_outcome",
    "observed_alignment_to_prompt",
    "review_confidence",
    "review_comment",
    "observed_primary_failure_mechanism",
    "observed_secondary_failure_mechanism",
    "observed_tuning_lever",
    "needs_followup",
    "followup_note",
    "langfuse_trace_id",
    "langfuse_session_id",
    "join_status",
]

_REQUIRED_ANNOTATION_FIELDS = [
    "observed_outcome",
    "observed_alignment_to_prompt",
    "review_confidence",
    "review_comment",
]

_SCORE_NAME_ALIASES = {
    "obs_secondary_failure_mechanism": "observed_secondary_failure_mechanism",
}


@dataclass(frozen=True)
class DiagnosticSessionIdentity:
    dataset_name: str
    run_label: str
    row_id: str


@dataclass(frozen=True)
class _SelectedScoreRow:
    trace_id: str
    session_id: str
    name: str
    value: str


def parse_diagnostic_session_id(session_id: str) -> DiagnosticSessionIdentity:
    parts = session_id.split("::")
    if len(parts) != 3 or any(not part for part in parts):
        raise ValueError(f"Invalid diagnostic session_id: {session_id}")
    return DiagnosticSessionIdentity(
        dataset_name=parts[0],
        run_label=parts[1],
        row_id=parts[2],
    )


def join_annotation_export(
    *,
    dataset_path: Path,
    scores_export_path: Path,
    dataset_name: str,
    run_label: str,
) -> list[dict[str, str]]:
    dataset_columns, dataset_rows = load_raw_csv_rows(dataset_path)
    selected_scores = _select_latest_annotation_scores(
        scores_export_path=scores_export_path,
        dataset_name=dataset_name,
        run_label=run_label,
    )

    output_rows: list[dict[str, str]] = []
    for dataset_row in dataset_rows:
        row_id = dataset_row["id"]
        row_scores = selected_scores.get(row_id, {})
        output_row = dict(dataset_row)
        for column in ANNOTATION_OUTPUT_COLUMNS:
            output_row[column] = ""

        for score_name, selected_score in row_scores.items():
            output_column = _normalize_score_name(score_name)
            output_row[output_column] = selected_score.value
            output_row["langfuse_trace_id"] = selected_score.trace_id
            output_row["langfuse_session_id"] = selected_score.session_id

        output_row["join_status"] = _build_join_status(output_row)
        output_rows.append(output_row)

    _validate_output_columns(dataset_columns, output_rows)
    return output_rows


def write_joined_annotation_csv(
    *,
    output_path: Path,
    joined_rows: list[dict[str, str]],
) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if not joined_rows:
        raise ValueError("joined_rows must not be empty")

    fieldnames = list(joined_rows[0].keys())
    with output_path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(joined_rows)
    return output_path


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="Join Langfuse diagnostic annotation export to dataset rows"
    )
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--scores-export", type=Path, required=True)
    parser.add_argument("--dataset-name", required=True)
    parser.add_argument("--run-label", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)

    joined_rows = join_annotation_export(
        dataset_path=args.dataset,
        scores_export_path=args.scores_export,
        dataset_name=args.dataset_name,
        run_label=args.run_label,
    )
    output_path = write_joined_annotation_csv(
        output_path=args.output,
        joined_rows=joined_rows,
    )
    print(f"Joined annotation export: {output_path}")


def _select_latest_annotation_scores(
    *,
    scores_export_path: Path,
    dataset_name: str,
    run_label: str,
) -> dict[str, dict[str, _SelectedScoreRow]]:
    selected: dict[tuple[str, str], tuple[tuple[str, str, int], _SelectedScoreRow]] = {}
    with scores_export_path.open("r", encoding="utf-8", newline="") as file:
        reader = csv.DictReader(file)
        for index, row in enumerate(reader):
            if row.get("source") != "ANNOTATION":
                continue
            if not _is_trace_level_annotation(row.get("observation_id")):
                continue

            session_id = (row.get("session_id") or "").strip()
            if not session_id:
                continue
            try:
                session_identity = parse_diagnostic_session_id(session_id)
            except ValueError:
                if _looks_like_target_session(session_id, dataset_name, run_label):
                    raise
                continue
            if session_identity.dataset_name != dataset_name:
                continue
            if session_identity.run_label != run_label:
                continue

            score_name = (row.get("name") or "").strip()
            if not score_name:
                continue
            score_value = _extract_score_value(row)
            selected_row = _SelectedScoreRow(
                trace_id=(row.get("trace_id") or "").strip(),
                session_id=session_id,
                name=score_name,
                value=score_value,
            )
            sort_key = _score_sort_key(row, index)
            selected[(session_identity.row_id, score_name)] = max(
                selected.get(
                    (session_identity.row_id, score_name), (("", "", -1), selected_row)
                ),
                (sort_key, selected_row),
                key=lambda item: item[0],
            )

    pivoted: dict[str, dict[str, _SelectedScoreRow]] = {}
    for (row_id, score_name), (_, selected_row) in selected.items():
        pivoted.setdefault(row_id, {})[score_name] = selected_row
    return pivoted


def _extract_score_value(row: dict[str, str | None]) -> str:
    score_name = _normalize_score_name((row.get("name") or "").strip())
    data_type = (row.get("data_type") or "").strip().upper()
    raw_value = (row.get("value") or "").strip()
    string_value = (row.get("string_value") or "").strip()
    comment = (row.get("comment") or "").strip()

    if data_type == "BOOLEAN":
        return _normalize_boolean_value(raw_value or string_value or comment)
    if score_name == "review_comment":
        return string_value or comment
    if data_type in {"TEXT", "CATEGORICAL"}:
        return string_value
    return string_value or comment or raw_value


def _normalize_score_name(score_name: str) -> str:
    return _SCORE_NAME_ALIASES.get(score_name, score_name)


def _normalize_boolean_value(value: str) -> str:
    lowered = value.strip().lower()
    if lowered in {"1", "true", "t", "yes", "y", "high"}:
        return "true"
    if lowered in {"0", "false", "f", "no", "n", "low"}:
        return "false"
    return lowered


def _is_trace_level_annotation(observation_id: str | None) -> bool:
    return observation_id is None or observation_id.strip() == ""


def _score_sort_key(row: dict[str, str | None], index: int) -> tuple[str, str, int]:
    updated_at = (row.get("updated_at") or "").strip()
    created_at = (row.get("created_at") or "").strip()
    return (updated_at, created_at, index)


def _build_join_status(row: dict[str, str]) -> str:
    annotation_values = [
        row.get(column, "") for column in ANNOTATION_OUTPUT_COLUMNS[:-3]
    ]
    has_any_annotation = any(value != "" for value in annotation_values)
    if not has_any_annotation:
        return "missing_annotation"
    if all(row.get(field, "") != "" for field in _REQUIRED_ANNOTATION_FIELDS):
        return "annotated"
    return "partial_annotation"


def _looks_like_target_session(
    session_id: str,
    dataset_name: str,
    run_label: str,
) -> bool:
    return session_id.startswith(f"{dataset_name}::{run_label}")


def _validate_output_columns(
    dataset_columns: list[str],
    output_rows: list[dict[str, str]],
) -> None:
    expected_columns = [*dataset_columns, *ANNOTATION_OUTPUT_COLUMNS]
    for row in output_rows:
        if list(row.keys()) != expected_columns:
            raise ValueError("Joined annotation columns do not match expected order")


if __name__ == "__main__":
    main()
