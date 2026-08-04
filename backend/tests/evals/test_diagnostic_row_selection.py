"""Tests for diagnostic dataset row selection."""

from __future__ import annotations

from pathlib import Path

import pytest

from backend.evals.dataset_loader import load_raw_csv_rows
from backend.evals.diagnostic.row_selection import select_diagnostic_rows

DATASET_PATH = Path("backend/evals/scenarios/baseline_behavior_diagnostic/dataset.csv")


def load_fixture_rows() -> tuple[list[str], list[dict[str, str]]]:
    """Load the shared diagnostic fixture dataset as raw CSV rows."""
    return load_raw_csv_rows(DATASET_PATH)


def test_select_diagnostic_rows_defaults_to_full_dataset() -> None:
    header_columns, raw_rows = load_fixture_rows()

    selected_rows = select_diagnostic_rows(header_columns, raw_rows)

    assert selected_rows == raw_rows


def test_select_diagnostic_rows_supports_row_ids_in_requested_order() -> None:
    header_columns, raw_rows = load_fixture_rows()

    selected_rows = select_diagnostic_rows(header_columns, raw_rows, "3,1,7")

    assert [row["id"] for row in selected_rows] == ["3", "1", "7"]


def test_select_diagnostic_rows_tolerates_whitespace_around_ids() -> None:
    header_columns, raw_rows = load_fixture_rows()

    selected_rows = select_diagnostic_rows(header_columns, raw_rows, " 3 , 1 ")

    assert [row["id"] for row in selected_rows] == ["3", "1"]


def test_select_diagnostic_rows_rejects_duplicate_row_ids() -> None:
    header_columns, raw_rows = load_fixture_rows()

    with pytest.raises(ValueError, match="Duplicate row ids: 3"):
        select_diagnostic_rows(header_columns, raw_rows, "3,1,3")


def test_select_diagnostic_rows_rejects_missing_row_ids() -> None:
    header_columns, raw_rows = load_fixture_rows()

    with pytest.raises(ValueError, match="Unknown row ids: 999"):
        select_diagnostic_rows(header_columns, raw_rows, "1,999")


def test_select_diagnostic_rows_rejects_empty_row_ids() -> None:
    header_columns, raw_rows = load_fixture_rows()

    with pytest.raises(ValueError, match="row_ids cannot be empty"):
        select_diagnostic_rows(header_columns, raw_rows, "   ")


def test_select_diagnostic_rows_rejects_blank_id_in_list() -> None:
    header_columns, raw_rows = load_fixture_rows()

    with pytest.raises(ValueError, match="comma-separated list of ids"):
        select_diagnostic_rows(header_columns, raw_rows, "1,,3")


def test_select_diagnostic_rows_rejects_dataset_without_id_column() -> None:
    """Fixed convention: diagnostic datasets must carry an ``id`` column."""
    header_columns = ["row_key", "capability_band"]
    raw_rows = [{"row_key": "alpha", "capability_band": "core"}]

    with pytest.raises(ValueError, match="must have an 'id' column"):
        select_diagnostic_rows(header_columns, raw_rows)


def test_select_diagnostic_rows_rejects_duplicate_dataset_row_ids() -> None:
    header_columns = ["id", "capability_band"]
    raw_rows = [
        {"id": "1", "capability_band": "core"},
        {"id": "1", "capability_band": "boundary"},
    ]

    with pytest.raises(ValueError, match="Duplicate dataset row id: 1"):
        select_diagnostic_rows(header_columns, raw_rows)


def test_select_diagnostic_rows_rejects_missing_dataset_row_id() -> None:
    header_columns = ["id", "capability_band"]
    raw_rows = [
        {"id": "1", "capability_band": "core"},
        {"id": "", "capability_band": "boundary"},
    ]

    with pytest.raises(ValueError, match="non-empty id"):
        select_diagnostic_rows(header_columns, raw_rows)
