"""Row selection for diagnostic eval datasets.

Authoritative diagnostic runs use the whole dataset. ``--row-ids`` exists only
for smoke runs, debugging, and re-running a handful of failed rows; the selected
ids are recorded in experiment metadata so a subset run can never be mistaken
for a full one. Anything richer than an explicit id list — field filters, saved
manifests, slice hashing — is out of envelope.

``load_split_sidecar`` / ``apply_split`` are a separate, composable layer for
scenarios that additionally carry a frozen dev/holdout/reserve split (e.g. a
benchmark protocol's ``benchmark/split.json``). They guard against an
accidental holdout/reserve run before that split is frozen — not against
malicious misuse — by defaulting to dev rows only and requiring each other
tier's inclusion to be named explicitly.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import TypedDict


class SplitSidecar(TypedDict):
    """Parsed shape of a benchmark's dev/holdout/reserve split sidecar."""

    dev: list[str]
    holdout: list[str]
    reserve: list[str]


def select_diagnostic_rows(
    header_columns: list[str],
    raw_rows: list[dict[str, str]],
    row_ids: str | None = None,
) -> list[dict[str, str]]:
    """Return the whole dataset, or just the requested ids in requested order.

    Diagnostic datasets follow a fixed convention: row identity always lives in
    the ``id`` column (configurability was deliberately removed).
    """
    if "id" not in header_columns:
        raise ValueError("Diagnostic datasets must have an 'id' column")

    row_lookup = _build_row_lookup(raw_rows)

    if row_ids is None:
        return list(raw_rows)

    requested_ids = _split_row_ids(row_ids)
    missing_ids = [row_id for row_id in requested_ids if row_id not in row_lookup]
    if missing_ids:
        raise ValueError(f"Unknown row ids: {', '.join(missing_ids)}")

    return [row_lookup[row_id] for row_id in requested_ids]


def _build_row_lookup(raw_rows: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    row_lookup: dict[str, dict[str, str]] = {}
    for row in raw_rows:
        row_id = row.get("id")
        if not row_id:
            raise ValueError("All diagnostic rows must have a non-empty id")
        if row_id in row_lookup:
            raise ValueError(f"Duplicate dataset row id: {row_id}")
        row_lookup[row_id] = row
    return row_lookup


def _split_row_ids(row_ids: str) -> list[str]:
    if not row_ids.strip():
        raise ValueError("row_ids cannot be empty")

    parsed_ids = [row_id.strip() for row_id in row_ids.split(",")]
    if any(not row_id for row_id in parsed_ids):
        raise ValueError("row_ids must be a comma-separated list of ids")

    duplicates = _find_duplicates(parsed_ids)
    if duplicates:
        raise ValueError(f"Duplicate row ids: {', '.join(duplicates)}")
    return parsed_ids


def _find_duplicates(values: list[str]) -> list[str]:
    seen: set[str] = set()
    duplicates: list[str] = []
    for value in values:
        if value in seen and value not in duplicates:
            duplicates.append(value)
        seen.add(value)
    return duplicates


def load_split_sidecar(path: Path) -> SplitSidecar:
    """Load a dev/holdout/reserve split sidecar and check its integrity.

    Requires ``dev``/``holdout``/``reserve`` id lists and rejects a row id
    appearing in more than one tier — a corrupt sidecar must fail loudly
    rather than silently leak a holdout row into dev.
    """
    with open(path, "r") as f:
        data = json.load(f)

    for tier in ("dev", "holdout", "reserve"):
        if tier not in data or not isinstance(data[tier], list):
            raise ValueError(f"Split sidecar missing '{tier}' row-id list: {path}")

    all_ids = [*data["dev"], *data["holdout"], *data["reserve"]]
    duplicates = _find_duplicates(all_ids)
    if duplicates:
        raise ValueError(
            f"Row ids appear in more than one split tier: {', '.join(duplicates)}"
        )

    return SplitSidecar(
        dev=data["dev"], holdout=data["holdout"], reserve=data["reserve"]
    )


def apply_split(
    rows: list[dict[str, str]],
    split: SplitSidecar,
    *,
    include_holdout: bool = False,
    include_reserve: bool = False,
) -> list[dict[str, str]]:
    """Filter ``rows`` to the split-approved subset.

    Defaults to dev rows only; ``include_holdout``/``include_reserve`` are
    explicit per-tier opt-ins (never a single "unlock everything" flag) so a
    caller can never widen scope by accident. Every row in ``rows`` must
    appear in exactly one tier of ``split`` — a row absent from the sidecar
    (e.g. the dataset grew after the split was frozen) fails loudly instead
    of silently passing through or being silently dropped.
    """
    allowed = set(split["dev"])
    if include_holdout:
        allowed |= set(split["holdout"])
    if include_reserve:
        allowed |= set(split["reserve"])

    known = set(split["dev"]) | set(split["holdout"]) | set(split["reserve"])
    unknown = [row["id"] for row in rows if row.get("id") not in known]
    if unknown:
        raise ValueError(f"Rows not present in the split sidecar: {', '.join(unknown)}")

    return [row for row in rows if row["id"] in allowed]
