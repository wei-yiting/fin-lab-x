"""Tests for CSV dataset loading and column mapping."""

from pathlib import Path

import pytest

from backend.evals.dataset_loader import _convert_cell, load_dataset


def write_csv(tmp_path: Path, content: str) -> Path:
    """Write CSV content to a temporary file."""
    csv_path = tmp_path / "dataset.csv"
    csv_path.write_text(content, encoding="utf-8")
    return csv_path


def test_load_dataset_maps_scalar_input_and_ignores_unmapped_columns(
    tmp_path: Path,
) -> None:
    csv_path = write_csv(
        tmp_path,
        "\n".join(
            [
                "prompt,category,unused",
                "Hello world,news,drop-me",
            ]
        ),
    )

    rows = load_dataset(
        csv_path,
        {"prompt": "input", "category": "metadata.category"},
    )

    assert rows == [
        {
            "input": "Hello world",
            "expected": {},
            "metadata": {"category": "news"},
        }
    ]


def test_load_dataset_maps_dotpaths_into_nested_dicts(tmp_path: Path) -> None:
    csv_path = write_csv(
        tmp_path,
        "\n".join(
            [
                "prompt,answer,category",
                "問候,您好,greeting",
            ]
        ),
    )

    rows = load_dataset(
        csv_path,
        {
            "prompt": "input.text",
            "answer": "expected.response",
            "category": "metadata.category",
        },
    )

    assert rows == [
        {
            "input": {"text": "問候"},
            "expected": {"response": "您好"},
            "metadata": {"category": "greeting"},
        }
    ]


def test_load_dataset_converts_numeric_bool_and_empty_values(tmp_path: Path) -> None:
    csv_path = write_csv(
        tmp_path,
        "\n".join(
            [
                "prompt,count,enabled,notes",
                "Run evaluation,12.5,TRUE,",
            ]
        ),
    )

    rows = load_dataset(
        csv_path,
        {
            "prompt": "input",
            "count": "expected.count",
            "enabled": "expected.enabled",
            "notes": "metadata.notes",
        },
    )

    assert rows == [
        {
            "input": "Run evaluation",
            "expected": {"count": 12.5, "enabled": True},
            "metadata": {"notes": None},
        }
    ]


def test_load_dataset_uses_object_form_when_input_and_input_field_mixed(
    tmp_path: Path,
) -> None:
    csv_path = write_csv(
        tmp_path,
        "\n".join(
            [
                "prompt,title",
                "hello,world",
            ]
        ),
    )

    rows = load_dataset(
        csv_path,
        {
            "prompt": "input",
            "title": "input.title",
        },
    )

    assert rows == [
        {
            "input": {"title": "world"},
            "expected": {},
            "metadata": {},
        }
    ]


def test_load_dataset_rejects_missing_mapped_csv_column(tmp_path: Path) -> None:
    csv_path = write_csv(
        tmp_path,
        "\n".join(
            [
                "prompt",
                "hello",
            ]
        ),
    )

    with pytest.raises(ValueError, match="missing.*answer"):
        load_dataset(csv_path, {"answer": "expected.response"})


def test_load_dataset_rejects_header_only_csv(tmp_path: Path) -> None:
    csv_path = write_csv(tmp_path, "prompt,answer\n")

    with pytest.raises(ValueError, match="no data rows"):
        load_dataset(csv_path, {"prompt": "input", "answer": "expected.response"})


@pytest.mark.parametrize(
    "target_path,expected_error",
    [
        ("", "column_mapping target cannot be empty"),
        ("foo", "Unsupported column_mapping target bucket: foo"),
        ("foo.bar", "Unsupported column_mapping target bucket: foo"),
        ("input.", "Invalid column_mapping target: input."),
        ("expected..response", "Invalid column_mapping target: expected..response"),
    ],
)
def test_load_dataset_rejects_invalid_target_paths(
    tmp_path: Path,
    target_path: str,
    expected_error: str,
) -> None:
    csv_path = write_csv(
        tmp_path,
        "\n".join(
            [
                "prompt",
                "hello",
            ]
        ),
    )

    with pytest.raises(ValueError, match=expected_error):
        load_dataset(csv_path, {"prompt": target_path})


def test_load_dataset_supports_bom_prefixed_headers(tmp_path: Path) -> None:
    csv_path = tmp_path / "dataset.csv"
    csv_path.write_text(
        "\ufeffprompt,answer\nHello world,ok\n",
        encoding="utf-8",
    )

    rows = load_dataset(
        csv_path,
        {"prompt": "input", "answer": "expected.response"},
    )

    assert rows == [
        {
            "input": "Hello world",
            "expected": {"response": "ok"},
            "metadata": {},
        }
    ]


def test_load_dataset_preserves_cjk_content(tmp_path: Path) -> None:
    csv_path = write_csv(
        tmp_path,
        "\n".join(
            [
                "prompt,answer",
                "請用繁體中文回答,好的",
            ]
        ),
    )

    rows = load_dataset(csv_path, {"prompt": "input", "answer": "expected.response"})

    assert rows == [
        {
            "input": "請用繁體中文回答",
            "expected": {"response": "好的"},
            "metadata": {},
        }
    ]


def test_load_dataset_parses_rfc4180_cells_correctly(tmp_path: Path) -> None:
    csv_path = write_csv(
        tmp_path,
        'prompt,answer,category\n"Hello, world","Line 1\nLine 2 with ""quotes""",news\n',
    )

    rows = load_dataset(
        csv_path,
        {"prompt": "input", "answer": "expected.response", "category": "metadata.category"},
    )

    assert rows == [
        {
            "input": "Hello, world",
            "expected": {"response": 'Line 1\nLine 2 with "quotes"'},
            "metadata": {"category": "news"},
        }
    ]


@pytest.mark.parametrize(
    "raw,expected",
    [
        (None, None),
        ("", None),
        ("true", True),
        ("FALSE", False),
        ("12", 12.0),
        ("12.5", 12.5),
        ("0.02", 0.02),
        ("0.20", 0.2),
        ("1.0", 1.0),
        ("3.10", 3.1),
        ("hello", "hello"),
        ("001", 1.0),
    ],
)
def test_convert_cell_numeric_coercion(raw: str | None, expected: object) -> None:
    result = _convert_cell(raw)
    assert result == expected
    assert type(result) is type(expected)
