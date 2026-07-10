"""Join Langfuse annotation score exports back to diagnostic dataset rows."""

from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from pathlib import Path

from backend.evals.dataset_loader import load_raw_csv_rows

REVIEWER_SCORE_COLUMNS = [
    "observed_outcome",
    "observed_alignment_to_prompt",
    "review_confidence",
    "review_comment",
    "observed_primary_failure_mechanism",
    "obs_secondary_failure_mechanism",
    "observed_tuning_lever",
    "needs_followup",
    "followup_note",
]

ANNOTATION_OUTPUT_COLUMNS = [
    *REVIEWER_SCORE_COLUMNS,
    "langfuse_trace_id",
    "langfuse_session_id",
]


@dataclass(frozen=True)
class DiagnosticSessionIdentity:
    dataset_name: str
    run_label: str
    row_id: str


@dataclass(frozen=True)
class _SelectedScoreRow:
    trace_id: str
    session_id: str
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
    _, dataset_rows = load_raw_csv_rows(dataset_path)
    scores_by_row = _select_annotation_scores(
        scores_export_path=scores_export_path,
        dataset_name=dataset_name,
        run_label=run_label,
    )

    output_rows: list[dict[str, str]] = []
    for dataset_row in dataset_rows:
        output_row = dict(dataset_row)
        for column in ANNOTATION_OUTPUT_COLUMNS:
            output_row[column] = ""

        for score_name, score in scores_by_row.get(dataset_row["id"], {}).items():
            if score_name in REVIEWER_SCORE_COLUMNS:
                output_row[score_name] = score.value
            output_row["langfuse_trace_id"] = score.trace_id
            output_row["langfuse_session_id"] = score.session_id

        output_rows.append(output_row)

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


def _select_annotation_scores(
    *,
    scores_export_path: Path,
    dataset_name: str,
    run_label: str,
) -> dict[str, dict[str, _SelectedScoreRow]]:
    selected: dict[str, dict[str, _SelectedScoreRow]] = {}
    with scores_export_path.open("r", encoding="utf-8", newline="") as file:
        for row in csv.DictReader(file):
            if row.get("source") != "ANNOTATION":
                continue
            if not _is_trace_level_annotation(row.get("observation_id")):
                continue

            session_id = (row.get("session_id") or "").strip()
            try:
                identity = parse_diagnostic_session_id(session_id)
            except ValueError:
                continue
            if identity.dataset_name != dataset_name:
                continue
            if identity.run_label != run_label:
                continue

            score_name = (row.get("name") or "").strip()
            if not score_name:
                continue

            row_scores = selected.setdefault(identity.row_id, {})
            row_scores.setdefault(
                score_name,
                _SelectedScoreRow(
                    trace_id=(row.get("trace_id") or "").strip(),
                    session_id=session_id,
                    value=_extract_score_value(row),
                ),
            )
    return selected


def _extract_score_value(row: dict[str, str | None]) -> str:
    score_name = (row.get("name") or "").strip()
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


def _normalize_boolean_value(value: str) -> str:
    lowered = value.strip().lower()
    if lowered in {"1", "true", "t", "yes", "y", "high"}:
        return "true"
    if lowered in {"0", "false", "f", "no", "n", "low"}:
        return "false"
    return lowered


def _is_trace_level_annotation(observation_id: str | None) -> bool:
    return observation_id is None or observation_id.strip() == ""


if __name__ == "__main__":
    main()
