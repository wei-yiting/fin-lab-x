"""Write diagnostic platform-mode run manifests."""

from __future__ import annotations

import csv
import json
from collections.abc import Sequence
from datetime import datetime, timezone
from pathlib import Path
from typing import Mapping

_REQUIRED_COLUMNS = [
    "row_id",
    "session_id",
    "experiment_name",
    "run_label",
    "dataset_version",
    "slice_label",
    "slice_type",
    "selected_row_ids",
    "git_commit",
    "braintrust_project",
]
_OUTPUT_COLUMN_PREFIXES = ("output", "output.")


def write_run_manifest_csv(
    *,
    scenario_name: str,
    output_dir: Path,
    original_columns: Sequence[str] | None = None,
    original_rows: Sequence[dict[str, str]] | None = None,
    manifest_rows: Sequence[Mapping[str, object]],
) -> Path:
    """Write a platform-mode run manifest without any output columns."""
    output_dir.mkdir(parents=True, exist_ok=True)
    if original_rows is not None and len(original_rows) != len(manifest_rows):
        raise ValueError("original_rows and manifest_rows must have the same length")
    _validate_original_columns(original_columns or [])

    timestamp = datetime.now(tz=timezone.utc).strftime("%Y%m%d_%H%M%S_%f")
    csv_path = output_dir / f"{scenario_name}_run_manifest_{timestamp}.csv"

    fieldnames = list(original_columns or [])
    for required_column in _REQUIRED_COLUMNS:
        if required_column not in fieldnames:
            fieldnames.append(required_column)

    for manifest_row in manifest_rows:
        for key in manifest_row:
            if _is_output_column(key):
                raise ValueError("run manifest rows must not include output.* columns")
            if key not in fieldnames:
                fieldnames.append(key)
        _validate_required_columns(manifest_row)

    with csv_path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()

        for index, manifest_row in enumerate(manifest_rows):
            row = {key: "" for key in fieldnames}
            if original_rows is not None:
                for key in original_columns or []:
                    row[key] = original_rows[index].get(key, "")
            for key in manifest_row:
                row[key] = _serialize_manifest_value(manifest_row.get(key, ""))
            writer.writerow(row)

    return csv_path


def _serialize_manifest_value(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, (list, dict, tuple)):
        return json.dumps(value, ensure_ascii=False)
    return str(value)


def _validate_original_columns(original_columns: Sequence[str]) -> None:
    invalid_columns = [
        column for column in original_columns if _is_output_column(column)
    ]
    if invalid_columns:
        invalid_list = ", ".join(invalid_columns)
        raise ValueError(
            f"run manifest original columns must not include output columns: {invalid_list}"
        )


def _validate_required_columns(manifest_row: Mapping[str, object]) -> None:
    missing_columns = [
        column
        for column in _REQUIRED_COLUMNS
        if column not in manifest_row or manifest_row[column] in (None, "")
    ]
    if missing_columns:
        missing_list = ", ".join(missing_columns)
        raise ValueError(f"run manifest row missing required columns: {missing_list}")


def _is_output_column(column_name: str) -> bool:
    return column_name in _OUTPUT_COLUMN_PREFIXES or column_name.startswith("output.")
