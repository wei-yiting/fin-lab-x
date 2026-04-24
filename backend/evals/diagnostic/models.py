"""Shared models for diagnostic evaluation helpers."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import subprocess
from typing import Literal


@dataclass(frozen=True)
class DiagnosticSliceIdentity:
    """Stable identity for a selected diagnostic dataset slice."""

    slice_label: str
    slice_type: Literal["full_dataset", "row_ids", "field_filter", "manifest"]
    slice_selector: str
    selected_row_ids: tuple[str, ...]
    slice_hash: str


def resolve_git_commit(cwd: Path | None = None) -> str:
    """Return the current short git commit, or ``unknown`` when unavailable."""
    try:
        completed = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True,
            check=False,
            cwd=cwd,
            text=True,
        )
    except (FileNotFoundError, OSError, subprocess.SubprocessError):
        return "unknown"

    if completed.returncode != 0:
        return "unknown"

    commit = completed.stdout.strip()
    return commit or "unknown"
