"""Shared models for diagnostic evaluation helpers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class DiagnosticSliceIdentity:
    """Stable identity for a selected diagnostic dataset slice."""

    slice_label: str
    slice_type: Literal["full_dataset", "row_ids"]
    slice_selector: str
    selected_row_ids: tuple[str, ...]
