"""CSV dataset loader for Braintrust eval input rows."""

import json
from csv import DictReader
from pathlib import Path
from typing import Any

ALLOWED_BUCKETS = {"input", "expected", "metadata"}
VALID_COLUMN_TYPES = {"json", "str", "float", "bool"}


def _convert_cell(value: str | None) -> Any:
    """Convert CSV cell text into the expected Braintrust data type.

    Rules:
    - None / empty string -> None
    - "true" / "false" (case-insensitive) -> bool
    - Any string parseable by float() -> float (e.g. "12" -> 12.0, "0.20" -> 0.2)
    - Everything else -> str

    All numeric-looking strings become float, including integers (e.g. "12" -> 12.0).
    Use column_mapping target naming or scorer logic to handle type expectations.
    """
    if value is None or value == "":
        return None

    lowered = value.lower()
    if lowered == "true":
        return True
    if lowered == "false":
        return False

    try:
        return float(value)
    except ValueError:
        return value


def _convert_cell_typed(value: str | None, col_type: str | None) -> Any:
    """Convert a CSV cell using an explicit per-column type when declared.

    A declared type pins how the cell is parsed instead of relying on
    :func:`_convert_cell` auto-detection. This is what keeps JSON list columns
    (e.g. ``["NVDA / 2026 / Part I / Item 1A"]``) from being stored as raw
    strings that downstream scorers then iterate character-by-character, and
    lets identifier columns stay strings even when they look like ``TRUE`` or a
    number.

    - ``col_type is None`` -> fall back to :func:`_convert_cell` auto-detection.
    - None / empty string -> None (regardless of declared type).
    - ``"json"`` -> ``json.loads`` (list/dict/scalar as encoded).
    - ``"str"`` -> the raw string, no coercion.
    - ``"float"`` -> ``float(value)``.
    - ``"bool"`` -> ``true``/``false`` (case-insensitive).
    """
    if col_type is None:
        return _convert_cell(value)

    if value is None or value == "":
        return None

    if col_type == "json":
        try:
            return json.loads(value)
        except (json.JSONDecodeError, TypeError) as exc:
            raise ValueError(
                f"column_type 'json' but value is not valid JSON: {value!r}"
            ) from exc

    if col_type == "str":
        return value

    if col_type == "float":
        try:
            return float(value)
        except ValueError as exc:
            raise ValueError(
                f"column_type 'float' but value is not numeric: {value!r}"
            ) from exc

    if col_type == "bool":
        lowered = value.lower()
        if lowered == "true":
            return True
        if lowered == "false":
            return False
        raise ValueError(f"column_type 'bool' but value is not true/false: {value!r}")

    raise ValueError(f"Unknown column_type: {col_type}")


def _set_nested_value(target: dict[str, Any], path: list[str], value: Any) -> None:
    """Assign a value into a nested dict path."""
    current: dict[str, Any] = target
    for key in path[:-1]:
        next_value = current.get(key)
        if not isinstance(next_value, dict):
            next_value = {}
            current[key] = next_value
        current = next_value
    current[path[-1]] = value


def _validate_target_path(target_path: str) -> None:
    """Reject unsupported or malformed target paths before row processing."""
    if not target_path:
        raise ValueError("column_mapping target cannot be empty")

    target_parts = target_path.split(".")
    if any(part == "" for part in target_parts):
        raise ValueError(f"Invalid column_mapping target: {target_path}")
    if any(part != part.strip() for part in target_parts):
        raise ValueError(f"Invalid column_mapping target: {target_path}")

    bucket_name = target_parts[0]
    if bucket_name not in ALLOWED_BUCKETS:
        raise ValueError(f"Unsupported column_mapping target bucket: {bucket_name}")


def _validate_column_mapping(column_mapping: dict[str, str]) -> None:
    """Validate target paths before row processing begins."""
    for target_path in column_mapping.values():
        _validate_target_path(target_path)


def _validate_column_types(
    column_mapping: dict[str, str], column_types: dict[str, str]
) -> None:
    """Validate that declared column types reference mapped columns with known types."""
    for source_column, col_type in column_types.items():
        if source_column not in column_mapping:
            raise ValueError(
                f"column_types references unmapped column: {source_column}"
            )
        if col_type not in VALID_COLUMN_TYPES:
            allowed = ", ".join(sorted(VALID_COLUMN_TYPES))
            raise ValueError(
                f"Unsupported column_type '{col_type}' for column "
                f"'{source_column}' (allowed: {allowed})"
            )


def _row_object_buckets(column_mapping: dict[str, str]) -> set[str]:
    """Buckets that receive at least one dot-path target (object form)."""
    return {
        target.split(".", 1)[0] for target in column_mapping.values() if "." in target
    }


def _map_source_row(
    source_row: dict[str, str],
    column_mapping: dict[str, str],
    column_types: dict[str, str],
    object_buckets: set[str],
) -> dict[str, Any]:
    """Transform one raw CSV row into a ``{input, expected, metadata}`` dict."""
    row_data: dict[str, Any] = {"input": {}, "expected": {}, "metadata": {}}
    scalar_input: Any = None
    has_scalar_input = False

    for source_column, target_path in column_mapping.items():
        converted_value = _convert_cell_typed(
            source_row.get(source_column), column_types.get(source_column)
        )
        target_parts = target_path.split(".")
        bucket_name = target_parts[0]

        if len(target_parts) == 1:
            if bucket_name == "input":
                if bucket_name not in object_buckets:
                    scalar_input = converted_value
                    has_scalar_input = True
            else:
                if bucket_name not in object_buckets:
                    row_data[bucket_name] = converted_value
            continue

        bucket_value = row_data.get(bucket_name)
        if not isinstance(bucket_value, dict):
            bucket_value = {}
            row_data[bucket_name] = bucket_value
        _set_nested_value(bucket_value, target_parts[1:], converted_value)

    if "input" in object_buckets:
        if not isinstance(row_data["input"], dict):
            row_data["input"] = {}
    elif has_scalar_input:
        row_data["input"] = scalar_input

    return row_data


def apply_column_mapping(
    source_row: dict[str, str],
    column_mapping: dict[str, str],
    column_types: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Map one raw CSV row into Braintrust ``{input, expected, metadata}`` form.

    Public entry point so callers that build eval rows outside
    :func:`load_dataset` (e.g. diagnostic eval paths) reuse the same
    column-mapping and type-pinning logic instead of duplicating it.

    Enforces the same mapping contract as :func:`load_dataset`: the column
    mapping and declared types are validated, and a mapped source column that
    is absent from ``source_row`` is rejected instead of silently becoming
    ``None``.
    """
    _validate_column_mapping(column_mapping)
    resolved_types = column_types or {}
    _validate_column_types(column_mapping, resolved_types)

    missing_columns = [column for column in column_mapping if column not in source_row]
    if missing_columns:
        missing_list = ", ".join(missing_columns)
        raise ValueError(f"CSV missing columns: {missing_list}")

    return _map_source_row(
        source_row,
        column_mapping,
        resolved_types,
        _row_object_buckets(column_mapping),
    )


def load_raw_csv_rows(csv_path: Path) -> tuple[list[str], list[dict[str, str]]]:
    """Read CSV and return (header_columns, raw_rows) with original string values."""
    with csv_path.open("r", encoding="utf-8-sig", newline="") as file:
        reader = DictReader(file)
        header_columns = list(reader.fieldnames or [])
        return header_columns, [dict(row) for row in reader]


def load_dataset(
    csv_path: Path,
    column_mapping: dict[str, str],
    column_types: dict[str, str] | None = None,
) -> list[dict[str, Any]]:
    """Read CSV and transform it into Braintrust Eval() data format."""
    _validate_column_mapping(column_mapping)
    resolved_types = column_types or {}
    _validate_column_types(column_mapping, resolved_types)

    with csv_path.open("r", encoding="utf-8-sig", newline="") as file:
        reader = DictReader(file)
        header_columns = reader.fieldnames or []
        missing_columns = [
            column for column in column_mapping if column not in header_columns
        ]
        if missing_columns:
            missing_list = ", ".join(missing_columns)
            raise ValueError(f"CSV missing columns: {missing_list}")

        object_buckets = _row_object_buckets(column_mapping)

        rows: list[dict[str, Any]] = []
        saw_data_row = False

        for source_row in reader:
            saw_data_row = True
            rows.append(
                _map_source_row(
                    source_row, column_mapping, resolved_types, object_buckets
                )
            )

        if not saw_data_row:
            raise ValueError("CSV has no data rows")

    return rows
