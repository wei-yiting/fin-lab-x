"""Write diagnostic platform-mode run manifests."""

from __future__ import annotations

import csv
from datetime import datetime, timezone
from pathlib import Path
from typing import Mapping

_REQUIRED_COLUMNS = [
    "row_id",
    "session_id",
    "experiment_name",
    "run_label",
    "slice_label",
    "git_commit",
    "braintrust_project",
]


def write_run_manifest_csv(
    *,
    scenario_name: str,
    output_dir: Path,
    original_columns: list[str] | None = None,
    original_rows: list[dict[str, str]] | None = None,
    manifest_rows: list[Mapping[str, object]],
) -> Path:
    """Write a platform-mode run manifest without any output columns."""
    output_dir.mkdir(parents=True, exist_ok=True)
    if original_rows is not None and len(original_rows) != len(manifest_rows):
        raise ValueError("original_rows and manifest_rows must have the same length")

    timestamp = datetime.now(tz=timezone.utc).strftime("%Y%m%d_%H%M%S_%f")
    csv_path = output_dir / f"{scenario_name}_run_manifest_{timestamp}.csv"

    fieldnames = list(original_columns or [])
    for required_column in _REQUIRED_COLUMNS:
        if required_column not in fieldnames:
            fieldnames.append(required_column)

    for manifest_row in manifest_rows:
        for key in manifest_row:
            if key.startswith("output."):
                raise ValueError("run manifest rows must not include output.* columns")
            if key not in fieldnames:
                fieldnames.append(key)

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
    return str(value)
