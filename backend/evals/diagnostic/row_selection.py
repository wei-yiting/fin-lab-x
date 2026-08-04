"""Row selection for diagnostic eval datasets.

Authoritative diagnostic runs use the whole dataset. ``--row-ids`` exists only
for smoke runs, debugging, and re-running a handful of failed rows; the selected
ids are recorded in experiment metadata so a subset run can never be mistaken
for a full one. Anything richer than an explicit id list — field filters, saved
manifests, slice hashing — is out of envelope.
"""

from __future__ import annotations


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
