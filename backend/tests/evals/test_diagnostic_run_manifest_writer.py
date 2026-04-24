import csv
from pathlib import Path

import pytest

from backend.evals.diagnostic.run_manifest_writer import write_run_manifest_csv


def test_write_run_manifest_csv_preserves_original_columns_and_identity_fields(
    tmp_path: Path,
) -> None:
    csv_path = write_run_manifest_csv(
        scenario_name="near_v1_diagnostic",
        output_dir=tmp_path,
        original_columns=["id", "question"],
        original_rows=[{"id": "1", "question": "What happened?"}],
        manifest_rows=[
            {
                "row_id": "1",
                "session_id": "near_v1_diagnostic::smoke::1",
                "experiment_name": "near_v1_diagnostic_20260424_120000",
                "run_label": "smoke",
                "slice_label": "rows-1",
                "git_commit": "abc123",
                "braintrust_project": "finlab-x",
            }
        ],
    )

    with csv_path.open("r", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        rows = list(reader)

    assert reader.fieldnames == [
        "id",
        "question",
        "row_id",
        "session_id",
        "experiment_name",
        "run_label",
        "slice_label",
        "git_commit",
        "braintrust_project",
    ]
    assert rows == [
        {
            "id": "1",
            "question": "What happened?",
            "row_id": "1",
            "session_id": "near_v1_diagnostic::smoke::1",
            "experiment_name": "near_v1_diagnostic_20260424_120000",
            "run_label": "smoke",
            "slice_label": "rows-1",
            "git_commit": "abc123",
            "braintrust_project": "finlab-x",
        }
    ]


def test_write_run_manifest_csv_rejects_output_columns(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="must not include output"):
        write_run_manifest_csv(
            scenario_name="near_v1_diagnostic",
            output_dir=tmp_path,
            original_columns=["id"],
            original_rows=[{"id": "1"}],
            manifest_rows=[{"output.response": "should not be here"}],
        )


def test_write_run_manifest_csv_requires_matching_row_counts(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="same length"):
        write_run_manifest_csv(
            scenario_name="near_v1_diagnostic",
            output_dir=tmp_path,
            original_columns=["id"],
            original_rows=[{"id": "1"}],
            manifest_rows=[],
        )
