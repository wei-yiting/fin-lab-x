"""Tests for diagnostic dataset row selection."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from backend.evals.dataset_loader import load_raw_csv_rows
from backend.evals.diagnostic.row_selection import (
    apply_split,
    load_split_sidecar,
    select_diagnostic_rows,
)

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


# ---------------------------------------------------------------------------
# load_split_sidecar / apply_split: dev/holdout/reserve split guard.
# Dev-only by default; holdout/reserve are explicit per-tier opt-ins.
# ---------------------------------------------------------------------------


def _write_sidecar(
    tmp_path: Path, *, status: str = "frozen", **tiers: list[str]
) -> Path:
    path = tmp_path / "split.json"
    payload: dict[str, object] = {"status": status, **tiers}
    path.write_text(json.dumps(payload))
    return path


def _rows_for(ids: list[str]) -> list[dict[str, str]]:
    return [{"id": rid, "capability_band": "core"} for rid in ids]


class TestLoadSplitSidecar:
    def test_loads_dev_holdout_reserve(self, tmp_path: Path) -> None:
        path = _write_sidecar(tmp_path, dev=["1", "2"], holdout=["3"], reserve=["4"])

        split = load_split_sidecar(path)

        assert split == {
            "status": "frozen",
            "dev": ["1", "2"],
            "holdout": ["3"],
            "reserve": ["4"],
        }

    def test_rejects_missing_tier(self, tmp_path: Path) -> None:
        path = tmp_path / "split.json"
        path.write_text(
            json.dumps({"status": "frozen", "dev": ["1"], "holdout": ["2"]})
        )

        with pytest.raises(ValueError, match="missing 'reserve'"):
            load_split_sidecar(path)

    def test_rejects_missing_status(self, tmp_path: Path) -> None:
        path = tmp_path / "split.json"
        path.write_text(json.dumps({"dev": ["1"], "holdout": ["2"], "reserve": ["3"]}))

        with pytest.raises(ValueError, match="non-empty 'status'"):
            load_split_sidecar(path)

    def test_rejects_empty_status(self, tmp_path: Path) -> None:
        path = tmp_path / "split.json"
        path.write_text(
            json.dumps(
                {"status": "  ", "dev": ["1"], "holdout": ["2"], "reserve": ["3"]}
            )
        )

        with pytest.raises(ValueError, match="non-empty 'status'"):
            load_split_sidecar(path)

    def test_rejects_row_id_in_multiple_tiers(self, tmp_path: Path) -> None:
        path = _write_sidecar(tmp_path, dev=["1", "2"], holdout=["2"], reserve=["3"])

        with pytest.raises(ValueError, match="more than one split tier: 2"):
            load_split_sidecar(path)

    def test_rejects_non_object_root(self, tmp_path: Path) -> None:
        path = tmp_path / "split.json"
        path.write_text(json.dumps(["1", "2", "3"]))

        with pytest.raises(ValueError, match="must be a JSON object"):
            load_split_sidecar(path)

    @pytest.mark.parametrize(
        "malformed_id",
        [
            pytest.param("", id="empty-string"),
            pytest.param("   ", id="whitespace-only"),
            pytest.param(1, id="non-string"),
            pytest.param(None, id="null"),
        ],
    )
    def test_rejects_malformed_row_id(
        self, tmp_path: Path, malformed_id: object
    ) -> None:
        path = tmp_path / "split.json"
        path.write_text(
            json.dumps(
                {
                    "status": "frozen",
                    "dev": ["1", malformed_id],
                    "holdout": ["2"],
                    "reserve": ["3"],
                }
            )
        )

        with pytest.raises(ValueError, match="tier 'dev' has a malformed row id"):
            load_split_sidecar(path)


class TestApplySplit:
    def test_defaults_to_dev_only(self) -> None:
        split = {"dev": ["1", "2"], "holdout": ["3"], "reserve": ["4"]}
        rows = _rows_for(["1", "2", "3", "4"])

        selected = apply_split(rows, split)

        assert [r["id"] for r in selected] == ["1", "2"]

    def test_include_holdout_requires_explicit_opt_in(self) -> None:
        split = {"status": "frozen", "dev": ["1"], "holdout": ["2"], "reserve": ["3"]}
        rows = _rows_for(["1", "2", "3"])

        selected = apply_split(rows, split, include_holdout=True)

        assert {r["id"] for r in selected} == {"1", "2"}

    def test_include_reserve_requires_explicit_opt_in(self) -> None:
        split = {"status": "frozen", "dev": ["1"], "holdout": ["2"], "reserve": ["3"]}
        rows = _rows_for(["1", "2", "3"])

        selected = apply_split(rows, split, include_reserve=True)

        assert {r["id"] for r in selected} == {"1", "3"}

    def test_include_holdout_does_not_also_leak_reserve(self) -> None:
        split = {"status": "frozen", "dev": ["1"], "holdout": ["2"], "reserve": ["3"]}
        rows = _rows_for(["1", "2", "3"])

        selected = apply_split(rows, split, include_holdout=True)

        assert "3" not in {r["id"] for r in selected}

    def test_rejects_row_not_present_in_any_tier(self) -> None:
        split = {"dev": ["1"], "holdout": [], "reserve": []}
        rows = _rows_for(["1", "999"])

        with pytest.raises(ValueError, match="not present in the split sidecar: 999"):
            apply_split(rows, split)

    # -----------------------------------------------------------------
    # Freeze-state gate: holdout/reserve opt-in additionally requires
    # status == "frozen". Dev-only default is unaffected by status.
    # -----------------------------------------------------------------

    def test_include_holdout_with_proposed_status_raises(self) -> None:
        split = {
            "status": "proposed",
            "dev": ["1"],
            "holdout": ["2"],
            "reserve": ["3"],
        }
        rows = _rows_for(["1", "2", "3"])

        with pytest.raises(ValueError, match="include_holdout requires a frozen split"):
            apply_split(rows, split, include_holdout=True)

    def test_include_holdout_with_frozen_status_succeeds(self) -> None:
        split = {"status": "frozen", "dev": ["1"], "holdout": ["2"], "reserve": ["3"]}
        rows = _rows_for(["1", "2", "3"])

        selected = apply_split(rows, split, include_holdout=True)

        assert {r["id"] for r in selected} == {"1", "2"}

    def test_include_reserve_with_proposed_status_raises(self) -> None:
        split = {
            "status": "proposed",
            "dev": ["1"],
            "holdout": ["2"],
            "reserve": ["3"],
        }
        rows = _rows_for(["1", "2", "3"])

        with pytest.raises(ValueError, match="include_reserve requires a frozen split"):
            apply_split(rows, split, include_reserve=True)

    def test_include_reserve_with_frozen_status_succeeds(self) -> None:
        split = {"status": "frozen", "dev": ["1"], "holdout": ["2"], "reserve": ["3"]}
        rows = _rows_for(["1", "2", "3"])

        selected = apply_split(rows, split, include_reserve=True)

        assert {r["id"] for r in selected} == {"1", "3"}

    def test_dev_only_default_ignores_proposed_status(self) -> None:
        """Dev is always allowed regardless of freeze state — only the
        holdout/reserve opt-ins are gated."""
        split = {"status": "proposed", "dev": ["1"], "holdout": ["2"], "reserve": []}
        rows = _rows_for(["1", "2"])

        selected = apply_split(rows, split)

        assert [r["id"] for r in selected] == ["1"]

    def test_dev_only_default_ignores_missing_status(self) -> None:
        split = {"dev": ["1"], "holdout": ["2"], "reserve": []}
        rows = _rows_for(["1", "2"])

        selected = apply_split(rows, split)

        assert [r["id"] for r in selected] == ["1"]

    # -----------------------------------------------------------------
    # Dataset-side row validation: a malformed or duplicate id in the
    # dataset rows themselves (not the sidecar) must fail loudly instead
    # of raising an incidental KeyError/TypeError or silently skewing
    # aggregation with a duplicate.
    # -----------------------------------------------------------------

    def test_rejects_row_missing_id(self) -> None:
        split = {"dev": ["1"], "holdout": [], "reserve": []}
        rows = [{"capability_band": "core"}]

        with pytest.raises(ValueError, match="malformed id"):
            apply_split(rows, split)

    def test_rejects_row_with_non_string_id(self) -> None:
        split = {"dev": ["1"], "holdout": [], "reserve": []}
        rows = [{"id": 1, "capability_band": "core"}]

        with pytest.raises(ValueError, match="malformed id"):
            apply_split(rows, split)

    def test_rejects_duplicate_ids_in_rows(self) -> None:
        split = {"dev": ["1"], "holdout": [], "reserve": []}
        rows = _rows_for(["1", "1"])

        with pytest.raises(ValueError, match="Duplicate row ids in dataset rows: 1"):
            apply_split(rows, split)
