"""Tests for diagnostic dataset slice selection."""

from __future__ import annotations

from pathlib import Path

import pytest

from backend.evals.dataset_loader import load_raw_csv_rows
from backend.evals.diagnostic.dataset_selector import (
    parse_diagnostic_slice_args,
    select_diagnostic_slice,
)
from backend.evals.diagnostic.models import resolve_git_commit

DATASET_PATH = Path(
    "backend/evals/scenarios/near_v1_diagnostic/dataset.csv"
)


def load_fixture_rows() -> tuple[list[str], list[dict[str, str]]]:
    """Load the shared diagnostic fixture dataset as raw CSV rows."""
    return load_raw_csv_rows(DATASET_PATH)


def test_select_diagnostic_slice_defaults_to_full_dataset() -> None:
    header_columns, raw_rows = load_fixture_rows()

    selected_rows, identity = select_diagnostic_slice(
        header_columns,
        raw_rows,
        parse_diagnostic_slice_args(),
        row_id_column="id",
    )

    assert selected_rows == raw_rows
    assert identity.slice_label == "full"
    assert identity.slice_type == "full_dataset"
    assert identity.slice_selector == "full_dataset"
    assert identity.selected_row_ids == tuple(row["id"] for row in raw_rows)
    assert len(identity.slice_hash) == 12


def test_select_diagnostic_slice_supports_row_ids_in_requested_order() -> None:
    header_columns, raw_rows = load_fixture_rows()

    selected_rows, identity = select_diagnostic_slice(
        header_columns,
        raw_rows,
        parse_diagnostic_slice_args(row_ids="3,1,7"),
        row_id_column="id",
    )

    assert [row["id"] for row in selected_rows] == ["3", "1", "7"]
    assert identity.slice_label == "rows-3-1-7"
    assert identity.slice_type == "row_ids"
    assert identity.slice_selector == "3,1,7"
    assert identity.selected_row_ids == ("3", "1", "7")


def test_select_diagnostic_slice_rejects_duplicate_row_ids() -> None:
    header_columns, raw_rows = load_fixture_rows()

    with pytest.raises(ValueError, match="Duplicate row ids: 3"):
        select_diagnostic_slice(
            header_columns,
            raw_rows,
            parse_diagnostic_slice_args(row_ids="3,1,3"),
            row_id_column="id",
        )


def test_select_diagnostic_slice_rejects_missing_row_ids() -> None:
    header_columns, raw_rows = load_fixture_rows()

    with pytest.raises(ValueError, match="Unknown row ids: 999"):
        select_diagnostic_slice(
            header_columns,
            raw_rows,
            parse_diagnostic_slice_args(row_ids="1,999"),
            row_id_column="id",
        )


def test_select_diagnostic_slice_supports_single_field_filter() -> None:
    header_columns, raw_rows = load_fixture_rows()

    selected_rows, identity = select_diagnostic_slice(
        header_columns,
        raw_rows,
        parse_diagnostic_slice_args(field_filter="capability_band=boundary"),
        row_id_column="id",
    )

    assert selected_rows
    assert all(row["capability_band"] == "boundary" for row in selected_rows)
    assert identity.slice_label == "filter-capability_band-boundary"
    assert identity.slice_type == "field_filter"
    assert identity.slice_selector == "capability_band=boundary"
    assert identity.selected_row_ids == tuple(row["id"] for row in selected_rows)


@pytest.mark.parametrize(
    ("field_filter", "expected_error"),
    [
        ("capability_band", "field_filter must use column=value syntax"),
        ("capability_band=boundary=extra", "field_filter must use column=value syntax"),
        ("missing_column=boundary", "Unknown filter column: missing_column"),
        ("capability_band=not-a-real-band", "field_filter matched no rows"),
    ],
)
def test_select_diagnostic_slice_rejects_invalid_field_filters(
    field_filter: str,
    expected_error: str,
) -> None:
    header_columns, raw_rows = load_fixture_rows()

    with pytest.raises(ValueError, match=expected_error):
        select_diagnostic_slice(
            header_columns,
            raw_rows,
            parse_diagnostic_slice_args(field_filter=field_filter),
            row_id_column="id",
        )


def test_select_diagnostic_slice_supports_manifest_files(tmp_path: Path) -> None:
    header_columns, raw_rows = load_fixture_rows()
    manifest_path = tmp_path / "smoke.manifest"
    manifest_path.write_text(
        "\n".join(
            [
                "# keep this tiny",
                "",
                "7",
                "1",
            ]
        ),
        encoding="utf-8",
    )

    selected_rows, identity = select_diagnostic_slice(
        header_columns,
        raw_rows,
        parse_diagnostic_slice_args(manifest=str(manifest_path)),
        row_id_column="id",
    )

    assert [row["id"] for row in selected_rows] == ["7", "1"]
    assert identity.slice_label == "manifest-smoke"
    assert identity.slice_type == "manifest"
    assert identity.slice_selector == str(manifest_path)
    assert identity.selected_row_ids == ("7", "1")


def test_select_diagnostic_slice_rejects_missing_manifest_ids(
    tmp_path: Path,
) -> None:
    header_columns, raw_rows = load_fixture_rows()
    manifest_path = tmp_path / "missing.manifest"
    manifest_path.write_text("1\n999\n", encoding="utf-8")

    with pytest.raises(ValueError, match="Unknown row ids: 999"):
        select_diagnostic_slice(
            header_columns,
            raw_rows,
            parse_diagnostic_slice_args(manifest=str(manifest_path)),
            row_id_column="id",
        )


def test_parse_diagnostic_slice_args_rejects_multiple_selector_modes() -> None:
    with pytest.raises(ValueError, match="Exactly one slice selector mode may be active"):
        parse_diagnostic_slice_args(
            row_ids="1,2",
            field_filter="capability_band=core",
        )


def test_select_diagnostic_slice_hash_is_deterministic() -> None:
    header_columns, raw_rows = load_fixture_rows()

    _, first_identity = select_diagnostic_slice(
        header_columns,
        raw_rows,
        parse_diagnostic_slice_args(row_ids="3,1,7"),
        row_id_column="id",
    )
    _, second_identity = select_diagnostic_slice(
        header_columns,
        raw_rows,
        parse_diagnostic_slice_args(row_ids="3,1,7"),
        row_id_column="id",
    )
    _, different_identity = select_diagnostic_slice(
        header_columns,
        raw_rows,
        parse_diagnostic_slice_args(row_ids="1,3,7"),
        row_id_column="id",
    )

    assert first_identity.slice_hash == second_identity.slice_hash
    assert first_identity.slice_hash != different_identity.slice_hash


def test_resolve_git_commit_returns_unknown_when_git_is_unavailable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def raise_file_not_found(*args: object, **kwargs: object) -> object:
        raise FileNotFoundError

    monkeypatch.setattr("subprocess.run", raise_file_not_found)

    assert resolve_git_commit() == "unknown"


def test_select_diagnostic_slice_supports_custom_row_id_column() -> None:
    header_columns = ["row_key", "capability_band"]
    raw_rows = [
        {"row_key": "alpha", "capability_band": "core"},
        {"row_key": "beta", "capability_band": "boundary"},
        {"row_key": "gamma", "capability_band": "core"},
    ]

    selected_rows, identity = select_diagnostic_slice(
        header_columns,
        raw_rows,
        parse_diagnostic_slice_args(row_ids="gamma,alpha"),
        row_id_column="row_key",
    )

    assert [row["row_key"] for row in selected_rows] == ["gamma", "alpha"]
    assert identity.selected_row_ids == ("gamma", "alpha")


def test_select_diagnostic_slice_manifest_hash_ignores_path_when_content_matches(
    tmp_path: Path,
) -> None:
    header_columns, raw_rows = load_fixture_rows()
    first_manifest = tmp_path / "one" / "smoke.manifest"
    second_manifest = tmp_path / "two" / "copied.manifest"
    first_manifest.parent.mkdir()
    second_manifest.parent.mkdir()

    manifest_content = "7\n1\n"
    first_manifest.write_text(manifest_content, encoding="utf-8")
    second_manifest.write_text(manifest_content, encoding="utf-8")

    _, first_identity = select_diagnostic_slice(
        header_columns,
        raw_rows,
        parse_diagnostic_slice_args(manifest=str(first_manifest)),
        row_id_column="id",
    )
    _, second_identity = select_diagnostic_slice(
        header_columns,
        raw_rows,
        parse_diagnostic_slice_args(manifest=str(second_manifest)),
        row_id_column="id",
    )

    assert first_identity.selected_row_ids == ("7", "1")
    assert first_identity.slice_hash == second_identity.slice_hash


def test_select_diagnostic_slice_rejects_missing_manifest_file(tmp_path: Path) -> None:
    header_columns, raw_rows = load_fixture_rows()
    manifest_path = tmp_path / "missing.manifest"

    with pytest.raises(ValueError, match="Unable to read manifest"):
        select_diagnostic_slice(
            header_columns,
            raw_rows,
            parse_diagnostic_slice_args(manifest=str(manifest_path)),
            row_id_column="id",
        )


def test_select_diagnostic_slice_rejects_unreadable_manifest(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    header_columns, raw_rows = load_fixture_rows()
    manifest_path = tmp_path / "unreadable.manifest"
    manifest_path.write_text("1\n", encoding="utf-8")

    def raise_os_error(*args: object, **kwargs: object) -> str:
        raise OSError("permission denied")

    monkeypatch.setattr(Path, "read_text", raise_os_error)

    with pytest.raises(ValueError, match="Unable to read manifest"):
        select_diagnostic_slice(
            header_columns,
            raw_rows,
            parse_diagnostic_slice_args(manifest=str(manifest_path)),
            row_id_column="id",
        )


def test_select_diagnostic_slice_rejects_duplicate_dataset_row_ids() -> None:
    header_columns = ["id", "capability_band"]
    raw_rows = [
        {"id": "1", "capability_band": "core"},
        {"id": "1", "capability_band": "boundary"},
    ]

    with pytest.raises(ValueError, match="Duplicate dataset row id: 1"):
        select_diagnostic_slice(
            header_columns,
            raw_rows,
            parse_diagnostic_slice_args(),
            row_id_column="id",
        )


def test_select_diagnostic_slice_rejects_missing_dataset_row_id() -> None:
    header_columns = ["id", "capability_band"]
    raw_rows = [
        {"id": "1", "capability_band": "core"},
        {"id": "", "capability_band": "boundary"},
    ]

    with pytest.raises(ValueError, match="non-empty id"):
        select_diagnostic_slice(
            header_columns,
            raw_rows,
            parse_diagnostic_slice_args(),
            row_id_column="id",
        )


def test_select_diagnostic_slice_rejects_duplicate_manifest_ids(
    tmp_path: Path,
) -> None:
    header_columns, raw_rows = load_fixture_rows()
    manifest_path = tmp_path / "dupe.manifest"
    manifest_path.write_text("1\n7\n1\n", encoding="utf-8")

    with pytest.raises(ValueError, match="Duplicate row ids: 1"):
        select_diagnostic_slice(
            header_columns,
            raw_rows,
            parse_diagnostic_slice_args(manifest=str(manifest_path)),
            row_id_column="id",
        )


def test_select_diagnostic_slice_rejects_empty_manifest(tmp_path: Path) -> None:
    header_columns, raw_rows = load_fixture_rows()
    manifest_path = tmp_path / "empty.manifest"
    manifest_path.write_text("# comment only\n\n  \n", encoding="utf-8")

    with pytest.raises(ValueError, match="Manifest must include at least one row id"):
        select_diagnostic_slice(
            header_columns,
            raw_rows,
            parse_diagnostic_slice_args(manifest=str(manifest_path)),
            row_id_column="id",
        )


def test_resolve_git_commit_returns_unknown_on_non_zero_exit(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def return_non_zero(*args: object, **kwargs: object) -> object:
        return __import__("subprocess").CompletedProcess(
            args=["git"],
            returncode=1,
            stdout="deadbee\n",
        )

    monkeypatch.setattr("subprocess.run", return_non_zero)

    assert resolve_git_commit() == "unknown"


def test_resolve_git_commit_returns_unknown_on_empty_stdout(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def return_empty_stdout(*args: object, **kwargs: object) -> object:
        return __import__("subprocess").CompletedProcess(
            args=["git"],
            returncode=0,
            stdout=" \n",
        )

    monkeypatch.setattr("subprocess.run", return_empty_stdout)

    assert resolve_git_commit() == "unknown"
