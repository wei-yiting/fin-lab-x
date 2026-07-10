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


def test_select_diagnostic_slice_honors_slice_label_override() -> None:
    header_columns, raw_rows = load_fixture_rows()

    _, identity = select_diagnostic_slice(
        header_columns,
        raw_rows,
        parse_diagnostic_slice_args(row_ids="3,1", slice_label="focused"),
        row_id_column="id",
    )

    assert identity.slice_label == "focused"


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


def test_parse_diagnostic_slice_args_rejects_empty_row_ids() -> None:
    with pytest.raises(ValueError, match="Slice selector values cannot be empty"):
        parse_diagnostic_slice_args(row_ids="   ")


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


def test_select_diagnostic_slice_rejects_unknown_row_id_column() -> None:
    header_columns, raw_rows = load_fixture_rows()

    with pytest.raises(ValueError, match="Unknown row id column: missing"):
        select_diagnostic_slice(
            header_columns,
            raw_rows,
            parse_diagnostic_slice_args(),
            row_id_column="missing",
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


def test_resolve_git_commit_returns_unknown_when_git_is_unavailable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def raise_file_not_found(*args: object, **kwargs: object) -> object:
        raise FileNotFoundError

    monkeypatch.setattr("subprocess.run", raise_file_not_found)

    assert resolve_git_commit() == "unknown"


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
