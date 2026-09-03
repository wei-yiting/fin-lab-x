"""Row selection for diagnostic eval datasets.

Authoritative diagnostic runs use the whole dataset. ``--row-ids`` exists only
for smoke runs, debugging, and re-running a handful of failed rows; the selected
ids are recorded in experiment metadata so a subset run can never be mistaken
for a full one. Anything richer than an explicit id list — field filters, saved
manifests, slice hashing — is out of envelope.

``load_split_sidecar`` / ``apply_split`` are a deliberate, narrow exception to
the paragraph above: a benchmark protocol needs a real leakage guard (dev
rows only, until the split is frozen), which is richer than a plain id list.
They guard against an accidental holdout/reserve run before that split is
frozen — not against malicious misuse — by defaulting to dev rows only and
requiring each other tier's inclusion to be named explicitly. Nothing in the
run path calls them yet; the next ticket in this benchmark protocol's
sequence is the one that actually executes runs against the frozen split, so
it is also the one that wires this in. Author-accepted as reachable-soon
rather than reachable-now, not a standing exception.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import TypedDict


class SplitSidecar(TypedDict):
    """Parsed shape of a benchmark's dev/holdout/reserve split sidecar."""

    status: str
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

    Requires a ``status`` string plus ``dev``/``holdout``/``reserve`` id lists,
    and rejects a row id appearing in more than one tier — a corrupt sidecar
    must fail loudly rather than silently leak a holdout row into dev. Every
    id must be a non-empty (post-strip) string; a malformed element is
    rejected here, naming the tier and value, instead of surfacing later as
    an incidental ``TypeError`` inside duplicate-checking. ``status`` gates
    ``apply_split``'s holdout/reserve opt-in — only ``"frozen"`` unlocks
    them (see ``apply_split``).
    """
    with open(path, "r") as f:
        data = json.load(f)

    if not isinstance(data, dict):
        raise ValueError(
            "Split sidecar must be a JSON object with 'status'/'dev'/'holdout'/"
            f"'reserve' keys, got {type(data).__name__}: {path}"
        )

    if (
        "status" not in data
        or not isinstance(data["status"], str)
        or not data["status"].strip()
    ):
        raise ValueError(f"Split sidecar missing a non-empty 'status' string: {path}")

    for tier in ("dev", "holdout", "reserve"):
        if tier not in data or not isinstance(data[tier], list):
            raise ValueError(f"Split sidecar missing '{tier}' row-id list: {path}")
        for row_id in data[tier]:
            if not isinstance(row_id, str) or not row_id.strip():
                raise ValueError(
                    f"Split sidecar tier '{tier}' has a malformed row id "
                    f"(must be a non-empty string): {row_id!r}"
                )

    all_ids = [*data["dev"], *data["holdout"], *data["reserve"]]
    duplicates = _find_duplicates(all_ids)
    if duplicates:
        raise ValueError(
            f"Row ids appear in more than one split tier: {', '.join(duplicates)}"
        )

    return SplitSidecar(
        status=data["status"],
        dev=data["dev"],
        holdout=data["holdout"],
        reserve=data["reserve"],
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
    caller can never widen scope by accident. Requesting either opt-in
    additionally requires ``split["status"] == "frozen"`` — holdout/reserve
    rows must never be readable before the split is actually frozen (dev
    rows stay available regardless of status). Every row in ``rows`` must
    have a well-formed, unique ``id`` and appear in exactly one tier of
    ``split`` — a malformed/duplicate row id, or a row absent from the
    sidecar (e.g. the dataset grew after the split was frozen), fails
    loudly instead of silently passing through, skewing downstream
    aggregation, or being silently dropped.
    """
    if include_holdout and split.get("status") != "frozen":
        raise ValueError(
            "include_holdout requires a frozen split sidecar "
            f"(status={split.get('status')!r})"
        )
    if include_reserve and split.get("status") != "frozen":
        raise ValueError(
            "include_reserve requires a frozen split sidecar "
            f"(status={split.get('status')!r})"
        )

    allowed = set(split["dev"])
    if include_holdout:
        allowed |= set(split["holdout"])
    if include_reserve:
        allowed |= set(split["reserve"])

    known = set(split["dev"]) | set(split["holdout"]) | set(split["reserve"])

    row_ids: list[str] = []
    unknown: list[str] = []
    for row in rows:
        row_id = row.get("id")
        if not isinstance(row_id, str) or not row_id.strip():
            raise ValueError(
                f"Dataset row has a malformed id (must be a non-empty string): "
                f"{row_id!r}"
            )
        row_ids.append(row_id)
        if row_id not in known:
            unknown.append(row_id)

    duplicates = _find_duplicates(row_ids)
    if duplicates:
        raise ValueError(f"Duplicate row ids in dataset rows: {', '.join(duplicates)}")

    if unknown:
        raise ValueError(f"Rows not present in the split sidecar: {', '.join(unknown)}")

    return [row for row in rows if row["id"] in allowed]
