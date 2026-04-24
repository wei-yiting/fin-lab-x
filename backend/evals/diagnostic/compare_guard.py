"""Local comparability guard for diagnostic run manifests."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

_REQUIRED_COLUMNS = {
    "row_id",
    "dataset_version",
    "selected_row_ids",
    "slice_label",
    "slice_type",
}


def compare_manifests(
    *,
    run_a_manifest: Path,
    run_b_manifest: Path,
) -> dict[str, Any]:
    run_a = _load_manifest(run_a_manifest)
    run_b = _load_manifest(run_b_manifest)

    row_ids_a = run_a["row_ids"]
    row_ids_b = run_b["row_ids"]
    intersection = sorted(row_ids_a & row_ids_b)
    added_row_ids = sorted(row_ids_b - row_ids_a)
    removed_row_ids = sorted(row_ids_a - row_ids_b)

    result: dict[str, Any] = {
        "status": "",
        "row_count_a": len(row_ids_a),
        "row_count_b": len(row_ids_b),
        "intersection_size": len(intersection),
        "added_row_ids": added_row_ids,
        "removed_row_ids": removed_row_ids,
        "warnings": [],
    }

    if not intersection:
        result["status"] = "empty_intersection"
        result["warnings"] = ["No shared row ids across the two diagnostic runs."]
        return result

    same_version = run_a["dataset_version"] == run_b["dataset_version"]
    same_row_set = run_a["selected_row_ids"] == run_b["selected_row_ids"]
    full_dataset_compare = _is_full_dataset(run_a) or _is_full_dataset(run_b)

    if same_version and same_row_set:
        result["status"] = "same_row_set"
        return result

    if same_version and not full_dataset_compare:
        result["status"] = "intersection"
        result["warnings"] = [
            "Only compare the overlapping rows across the two same-version subsets.",
        ]
        return result

    if not same_version:
        if _is_full_dataset(run_a) and _is_full_dataset(run_b):
            result["status"] = "overlap_only"
            result["warnings"] = [
                (
                    "dataset_version_drift: dataset versions differ, so only compare "
                    "the overlapping rows."
                ),
                "Do not read this as a full-dataset improvement.",
            ]
            return result

        result["status"] = "dataset_version_mismatch"
        result["warnings"] = [
            "Cross-version subset comparisons may not represent identical row content.",
        ]
        return result

    result["status"] = "overlap_only"
    result["warnings"] = [
        "Only compare the overlapping rows; do not read this as a full-dataset improvement.",
    ]
    return result


def write_compare_guard_json(
    *,
    output_path: Path,
    guard_result: dict[str, Any],
) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(guard_result, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return output_path


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Compare diagnostic run manifests")
    parser.add_argument("--run-a-manifest", type=Path, required=True)
    parser.add_argument("--run-b-manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)

    result = compare_manifests(
        run_a_manifest=args.run_a_manifest,
        run_b_manifest=args.run_b_manifest,
    )
    output_path = write_compare_guard_json(
        output_path=args.output,
        guard_result=result,
    )
    print(f"Diagnostic compare guard: {output_path}")


def _load_manifest(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8", newline="") as file:
        reader = csv.DictReader(file)
        fieldnames = set(reader.fieldnames or [])
        missing_columns = sorted(_REQUIRED_COLUMNS - fieldnames)
        if missing_columns:
            missing_list = ", ".join(missing_columns)
            raise ValueError(f"Manifest missing required columns: {missing_list}")
        rows = list(reader)
    if not rows:
        raise ValueError(f"Manifest has no rows: {path}")

    dataset_versions = {row["dataset_version"] for row in rows}
    if len(dataset_versions) != 1:
        raise ValueError(f"Manifest dataset_version must be stable: {path}")

    selected_row_ids_raw = rows[0]["selected_row_ids"]
    selected_row_ids = _parse_selected_row_ids(selected_row_ids_raw)
    row_ids = {row["row_id"] for row in rows if row.get("row_id")}
    if row_ids != selected_row_ids:
        raise ValueError(
            "Manifest selected_row_ids must match the row_id set in the manifest rows"
        )
    return {
        "dataset_version": dataset_versions.pop(),
        "row_ids": row_ids,
        "selected_row_ids": selected_row_ids,
        "slice_label": rows[0]["slice_label"],
        "slice_type": rows[0]["slice_type"],
    }


def _parse_selected_row_ids(raw_value: str) -> set[str]:
    if not raw_value:
        return set()
    parsed = json.loads(raw_value)
    if not isinstance(parsed, list):
        raise ValueError("selected_row_ids must be a JSON list")
    return {str(item) for item in parsed}


def _is_full_dataset(manifest: dict[str, Any]) -> bool:
    return manifest["slice_type"] == "full_dataset" or manifest["slice_label"] == "full"


if __name__ == "__main__":
    main()
