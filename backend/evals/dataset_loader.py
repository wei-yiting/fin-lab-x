"""CSV dataset loader for Braintrust eval input rows."""

from csv import DictReader
from pathlib import Path
from typing import Any

ALLOWED_BUCKETS = {"input", "expected", "metadata"}


def _convert_cell(value: str | None) -> Any:
    """Convert CSV cell text into the expected Braintrust data type."""
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

    bucket_name = target_parts[0]
    if bucket_name not in ALLOWED_BUCKETS:
        raise ValueError(
            f"Unsupported column_mapping target bucket: {bucket_name}"
        )


def load_dataset(csv_path: Path, column_mapping: dict[str, str]) -> list[dict[str, Any]]:
    """Read CSV and transform it into Braintrust Eval() data format."""
    for target_path in column_mapping.values():
        _validate_target_path(target_path)

    with csv_path.open("r", encoding="utf-8-sig", newline="") as file:
        reader = DictReader(file)
        header_columns = reader.fieldnames or []
        missing_columns = [
            column for column in column_mapping if column not in header_columns
        ]
        if missing_columns:
            missing_list = ", ".join(missing_columns)
            raise ValueError(f"CSV missing columns: {missing_list}")

        object_buckets = {
            target.split(".", 1)[0]
            for target in column_mapping.values()
            if "." in target
        }

        rows: list[dict[str, Any]] = []
        saw_data_row = False

        for source_row in reader:
            saw_data_row = True
            row_data: dict[str, Any] = {
                "input": {},
                "expected": {},
                "metadata": {},
            }
            scalar_input: Any = None
            has_scalar_input = False

            for source_column, target_path in column_mapping.items():
                converted_value = _convert_cell(source_row.get(source_column))
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
                row_data["input"] = row_data["input"] if isinstance(row_data["input"], dict) else {}
            elif has_scalar_input:
                row_data["input"] = scalar_input

            rows.append(row_data)

        if not saw_data_row:
            raise ValueError("CSV has no data rows")

    return rows
