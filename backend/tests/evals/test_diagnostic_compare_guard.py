from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest

from backend.evals.diagnostic.compare_guard import compare_manifests, main


def _write_manifest(
    path: Path,
    *,
    dataset_version: str,
    row_ids: list[str],
    selected_row_ids: list[str] | None = None,
    slice_label: str | None = None,
    slice_type: str | None = None,
) -> None:
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=[
                "row_id",
                "dataset_version",
                "selected_row_ids",
                "slice_label",
                "slice_type",
                "run_label",
            ],
        )
        writer.writeheader()
        manifest_selected_ids = selected_row_ids or row_ids
        for row_id in row_ids:
            writer.writerow(
                {
                    "row_id": row_id,
                    "dataset_version": dataset_version,
                    "selected_row_ids": json.dumps(manifest_selected_ids),
                    "slice_label": slice_label
                    or f"rows-{'-'.join(manifest_selected_ids)}",
                    "slice_type": slice_type or "row_ids",
                    "run_label": "smoke",
                }
            )


def test_compare_manifests_reports_same_row_set(tmp_path: Path) -> None:
    run_a = tmp_path / "run-a.csv"
    run_b = tmp_path / "run-b.csv"
    _write_manifest(
        run_a,
        dataset_version="2026-04-24",
        row_ids=["1", "2"],
        slice_label="full",
        slice_type="full_dataset",
    )
    _write_manifest(
        run_b,
        dataset_version="2026-04-24",
        row_ids=["1", "2"],
        slice_label="full",
        slice_type="full_dataset",
    )

    result = compare_manifests(run_a_manifest=run_a, run_b_manifest=run_b)

    assert result["status"] == "same_row_set"
    assert result["intersection_size"] == 2
    assert result["warnings"] == []


def test_compare_manifests_reports_overlap_only_for_full_vs_subset(
    tmp_path: Path,
) -> None:
    run_a = tmp_path / "run-a.csv"
    run_b = tmp_path / "run-b.csv"
    _write_manifest(
        run_a,
        dataset_version="2026-04-24",
        row_ids=["1", "2", "3"],
        selected_row_ids=["1", "2", "3"],
        slice_label="full",
        slice_type="full_dataset",
    )
    _write_manifest(
        run_b,
        dataset_version="2026-04-24",
        row_ids=["1", "2"],
        selected_row_ids=["1", "2"],
    )

    result = compare_manifests(run_a_manifest=run_a, run_b_manifest=run_b)

    assert result["status"] == "overlap_only"
    assert result["intersection_size"] == 2
    assert result["warnings"]


def test_compare_manifests_reports_intersection_for_same_version_overlapping_subsets(
    tmp_path: Path,
) -> None:
    run_a = tmp_path / "run-a.csv"
    run_b = tmp_path / "run-b.csv"
    _write_manifest(
        run_a,
        dataset_version="2026-04-24",
        row_ids=["1", "2"],
        selected_row_ids=["1", "2"],
    )
    _write_manifest(
        run_b,
        dataset_version="2026-04-24",
        row_ids=["2", "3"],
        selected_row_ids=["2", "3"],
    )

    result = compare_manifests(run_a_manifest=run_a, run_b_manifest=run_b)

    assert result["status"] == "intersection"
    assert result["intersection_size"] == 1
    assert result["added_row_ids"] == ["3"]
    assert result["removed_row_ids"] == ["1"]


def test_compare_manifests_reports_overlap_only_for_cross_version_full_vs_full(
    tmp_path: Path,
) -> None:
    run_a = tmp_path / "run-a.csv"
    run_b = tmp_path / "run-b.csv"
    _write_manifest(
        run_a,
        dataset_version="2026-04-24",
        row_ids=["1", "2"],
        slice_label="full",
        slice_type="full_dataset",
    )
    _write_manifest(
        run_b,
        dataset_version="2026-05-01",
        row_ids=["1", "2", "3"],
        slice_label="full",
        slice_type="full_dataset",
    )

    result = compare_manifests(run_a_manifest=run_a, run_b_manifest=run_b)

    assert result["status"] == "overlap_only"
    assert result["added_row_ids"] == ["3"]
    assert result["removed_row_ids"] == []
    assert "dataset_version_drift" in result["warnings"][0]


def test_compare_manifests_reports_dataset_version_mismatch_for_cross_version_subsets(
    tmp_path: Path,
) -> None:
    run_a = tmp_path / "run-a.csv"
    run_b = tmp_path / "run-b.csv"
    _write_manifest(
        run_a,
        dataset_version="2026-04-24",
        row_ids=["1", "2"],
        selected_row_ids=["1", "2"],
    )
    _write_manifest(
        run_b,
        dataset_version="2026-05-01",
        row_ids=["1"],
        selected_row_ids=["1"],
    )

    result = compare_manifests(run_a_manifest=run_a, run_b_manifest=run_b)

    assert result["status"] == "dataset_version_mismatch"
    assert result["intersection_size"] == 1


def test_compare_manifests_reports_empty_intersection(tmp_path: Path) -> None:
    run_a = tmp_path / "run-a.csv"
    run_b = tmp_path / "run-b.csv"
    _write_manifest(
        run_a,
        dataset_version="2026-04-24",
        row_ids=["1", "2"],
        slice_label="full",
        slice_type="full_dataset",
    )
    _write_manifest(
        run_b,
        dataset_version="2026-04-24",
        row_ids=["7", "8"],
        slice_label="full",
        slice_type="full_dataset",
    )

    result = compare_manifests(run_a_manifest=run_a, run_b_manifest=run_b)

    assert result["status"] == "empty_intersection"
    assert result["intersection_size"] == 0


def test_compare_manifests_rejects_missing_required_columns(tmp_path: Path) -> None:
    manifest = tmp_path / "run-a.csv"
    with manifest.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=["row_id", "dataset_version", "slice_label", "slice_type"],
        )
        writer.writeheader()
        writer.writerow(
            {
                "row_id": "1",
                "dataset_version": "2026-04-24",
                "slice_label": "full",
                "slice_type": "full_dataset",
            }
        )

    with pytest.raises(ValueError, match="missing required columns"):
        compare_manifests(run_a_manifest=manifest, run_b_manifest=manifest)


def test_compare_manifests_rejects_selected_row_id_drift(tmp_path: Path) -> None:
    run_a = tmp_path / "run-a.csv"
    run_b = tmp_path / "run-b.csv"
    _write_manifest(
        run_a,
        dataset_version="2026-04-24",
        row_ids=["1", "2"],
        selected_row_ids=["1", "2", "3"],
    )
    _write_manifest(
        run_b,
        dataset_version="2026-04-24",
        row_ids=["1", "2"],
        selected_row_ids=["1", "2"],
    )

    with pytest.raises(ValueError, match="selected_row_ids must match"):
        compare_manifests(run_a_manifest=run_a, run_b_manifest=run_b)


def test_compare_guard_cli_writes_json(tmp_path: Path) -> None:
    run_a = tmp_path / "run-a.csv"
    run_b = tmp_path / "run-b.csv"
    output = tmp_path / "guard.json"
    _write_manifest(
        run_a,
        dataset_version="2026-04-24",
        row_ids=["1", "2"],
        slice_label="full",
        slice_type="full_dataset",
    )
    _write_manifest(
        run_b,
        dataset_version="2026-04-24",
        row_ids=["1", "2"],
        slice_label="full",
        slice_type="full_dataset",
    )

    main(
        [
            "--run-a-manifest",
            str(run_a),
            "--run-b-manifest",
            str(run_b),
            "--output",
            str(output),
        ]
    )

    data = json.loads(output.read_text(encoding="utf-8"))
    assert data["status"] == "same_row_set"
    assert data["intersection_size"] == 2
