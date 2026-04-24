"""Deterministic raw-row selection for diagnostic eval datasets."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import re
from typing import Literal

from backend.evals.diagnostic.models import DiagnosticSliceIdentity

SliceType = Literal["full_dataset", "row_ids", "field_filter", "manifest"]

_SLUG_PATTERN = re.compile(r"[^a-zA-Z0-9_]+")


@dataclass(frozen=True)
class DiagnosticSliceArgs:
    """Normalized slice-selection arguments parsed from CLI strings."""

    slice_type: SliceType
    slice_selector: str
    slice_label: str | None = None


def parse_diagnostic_slice_args(
    *,
    row_ids: str | None = None,
    field_filter: str | None = None,
    manifest: str | None = None,
    slice_label: str | None = None,
) -> DiagnosticSliceArgs:
    """Normalize mutually exclusive slice arguments into a selector config."""
    normalized_row_ids = _normalize_optional_arg(row_ids)
    normalized_field_filter = _normalize_optional_arg(field_filter)
    normalized_manifest = _normalize_optional_arg(manifest)
    normalized_slice_label = _normalize_optional_arg(slice_label)

    active_modes = [
        value is not None
        for value in (
            normalized_row_ids,
            normalized_field_filter,
            normalized_manifest,
        )
    ]
    if sum(active_modes) > 1:
        raise ValueError("Exactly one slice selector mode may be active")

    if normalized_row_ids is not None:
        return DiagnosticSliceArgs(
            slice_type="row_ids",
            slice_selector=",".join(_split_row_ids(normalized_row_ids)),
            slice_label=normalized_slice_label,
        )

    if normalized_field_filter is not None:
        column, value = _parse_field_filter(normalized_field_filter)
        return DiagnosticSliceArgs(
            slice_type="field_filter",
            slice_selector=f"{column}={value}",
            slice_label=normalized_slice_label,
        )

    if normalized_manifest is not None:
        return DiagnosticSliceArgs(
            slice_type="manifest",
            slice_selector=normalized_manifest,
            slice_label=normalized_slice_label,
        )

    return DiagnosticSliceArgs(
        slice_type="full_dataset",
        slice_selector="full_dataset",
        slice_label=normalized_slice_label,
    )


def select_diagnostic_slice(
    header_columns: list[str],
    raw_rows: list[dict[str, str]],
    slice_args: DiagnosticSliceArgs,
    *,
    row_id_column: str,
) -> tuple[list[dict[str, str]], DiagnosticSliceIdentity]:
    """Select deterministic raw CSV rows and emit a stable slice identity."""
    if row_id_column not in header_columns:
        raise ValueError(f"Unknown row id column: {row_id_column}")

    row_lookup = _build_row_lookup(raw_rows, row_id_column=row_id_column)
    hash_selector = slice_args.slice_selector

    if slice_args.slice_type == "full_dataset":
        selected_rows = list(raw_rows)
        selected_row_ids = tuple(row[row_id_column] for row in selected_rows)
        slice_label = slice_args.slice_label or "full"
    elif slice_args.slice_type == "row_ids":
        requested_ids = _split_row_ids(slice_args.slice_selector)
        _raise_for_missing_row_ids(requested_ids, row_lookup)
        selected_rows = [row_lookup[row_id] for row_id in requested_ids]
        selected_row_ids = tuple(requested_ids)
        slice_label = slice_args.slice_label or f"rows-{'-'.join(requested_ids)}"
    elif slice_args.slice_type == "field_filter":
        column, value = _parse_field_filter(slice_args.slice_selector)
        if column not in header_columns:
            raise ValueError(f"Unknown filter column: {column}")
        selected_rows = [row for row in raw_rows if row.get(column) == value]
        if not selected_rows:
            raise ValueError("field_filter matched no rows")
        selected_row_ids = tuple(row[row_id_column] for row in selected_rows)
        slice_label = (
            slice_args.slice_label
            or f"filter-{_slugify(column)}-{_slugify(value)}"
        )
    else:
        manifest_path = Path(slice_args.slice_selector)
        requested_ids = _read_manifest_row_ids(manifest_path)
        _raise_for_missing_row_ids(requested_ids, row_lookup)
        selected_rows = [row_lookup[row_id] for row_id in requested_ids]
        selected_row_ids = tuple(requested_ids)
        slice_label = slice_args.slice_label or f"manifest-{_slugify(manifest_path.stem)}"
        hash_selector = _build_manifest_hash_selector(selected_row_ids)

    return selected_rows, DiagnosticSliceIdentity(
        slice_label=slice_label,
        slice_type=slice_args.slice_type,
        slice_selector=slice_args.slice_selector,
        selected_row_ids=selected_row_ids,
        slice_hash=_build_slice_hash(
            slice_type=slice_args.slice_type,
            slice_selector=hash_selector,
            selected_row_ids=selected_row_ids,
        ),
    )


def _normalize_optional_arg(value: str | None) -> str | None:
    if value is None:
        return None
    stripped = value.strip()
    if not stripped:
        raise ValueError("Slice selector values cannot be empty")
    return stripped


def _build_row_lookup(
    raw_rows: list[dict[str, str]],
    *,
    row_id_column: str,
) -> dict[str, dict[str, str]]:
    row_lookup: dict[str, dict[str, str]] = {}
    for row in raw_rows:
        row_id = row.get(row_id_column)
        if row_id is None or row_id == "":
            raise ValueError(
                f"All diagnostic rows must have a non-empty {row_id_column}"
            )
        if row_id in row_lookup:
            raise ValueError(f"Duplicate dataset row id: {row_id}")
        row_lookup[row_id] = row
    return row_lookup


def _split_row_ids(row_ids: str) -> list[str]:
    parsed_ids = [row_id.strip() for row_id in row_ids.split(",")]
    if any(not row_id for row_id in parsed_ids):
        raise ValueError("row_ids must be a comma-separated list of ids")

    duplicates = _find_duplicates(parsed_ids)
    if duplicates:
        duplicate_list = ", ".join(duplicates)
        raise ValueError(f"Duplicate row ids: {duplicate_list}")
    return parsed_ids


def _parse_field_filter(field_filter: str) -> tuple[str, str]:
    if field_filter.count("=") != 1:
        raise ValueError("field_filter must use column=value syntax")

    column, value = (part.strip() for part in field_filter.split("=", 1))
    if not column or not value:
        raise ValueError("field_filter must use column=value syntax")
    return column, value


def _read_manifest_row_ids(manifest_path: Path) -> list[str]:
    row_ids: list[str] = []
    try:
        manifest_text = manifest_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ValueError(f"Unable to read manifest: {manifest_path}") from exc

    for line in manifest_text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        row_ids.append(stripped)

    if not row_ids:
        raise ValueError("Manifest must include at least one row id")

    duplicates = _find_duplicates(row_ids)
    if duplicates:
        duplicate_list = ", ".join(duplicates)
        raise ValueError(f"Duplicate row ids: {duplicate_list}")
    return row_ids


def _find_duplicates(values: list[str]) -> list[str]:
    seen: set[str] = set()
    duplicates: list[str] = []
    for value in values:
        if value in seen and value not in duplicates:
            duplicates.append(value)
        seen.add(value)
    return duplicates


def _raise_for_missing_row_ids(
    requested_ids: list[str],
    row_lookup: dict[str, dict[str, str]],
) -> None:
    missing_ids = [row_id for row_id in requested_ids if row_id not in row_lookup]
    if missing_ids:
        missing_list = ", ".join(missing_ids)
        raise ValueError(f"Unknown row ids: {missing_list}")


def _slugify(value: str) -> str:
    slug = _SLUG_PATTERN.sub("-", value.strip()).strip("-").lower()
    return slug or "empty"


def _build_slice_hash(
    *,
    slice_type: SliceType,
    slice_selector: str,
    selected_row_ids: tuple[str, ...],
) -> str:
    encoded = json.dumps(
        {
            "selected_row_ids": list(selected_row_ids),
            "slice_selector": slice_selector,
            "slice_type": slice_type,
        },
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()[:12]


def _build_manifest_hash_selector(selected_row_ids: tuple[str, ...]) -> str:
    return f"manifest:{','.join(selected_row_ids)}"
