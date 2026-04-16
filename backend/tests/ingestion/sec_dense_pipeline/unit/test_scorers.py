import pytest
from autoevals import Score

from backend.evals.scorers.sec_retrieval_scorer import (
    _compute_map,
    _is_hit,
    header_path_recall_at_5,
    header_path_recall_at_10,
)


@pytest.mark.parametrize(
    "chunk_path,chunk_text,expected_paths,snippets,expected_hit",
    [
        (
            "NVDA / 2025 / Item 1A / Risks Related",
            "US export controls limit access to certain licenses",
            ["NVDA / 2025 / Item 1A"],
            ["export controls"],
            True,
        ),
        (
            "NVDA / 2025 / Item 1A / Risks Related",
            "Revenue grew significantly in Q4",
            ["NVDA / 2025 / Item 1A"],
            ["export controls"],
            False,
        ),
        (
            "NVDA / 2025 / Item 1A / Risks",
            "any text",
            ["NVDA / 2025 / Item 1A"],
            [],
            True,
        ),
    ],
)
def test_is_hit(
    chunk_path, chunk_text, expected_paths, snippets, expected_hit
) -> None:
    chunk = {"header_path": chunk_path, "text": chunk_text}
    expected = {"header_paths": expected_paths}
    if snippets is not None:
        expected["answer_snippets"] = snippets
    assert _is_hit(chunk, expected) == expected_hit


def test_recall_dedup_cross_company() -> None:
    output = {
        "retrieved_chunks": [
            {
                "header_path": "NVDA / 2025 / Item 1A / Risks X",
                "text": "export controls limit",
            },
            {
                "header_path": "NVDA / 2025 / Item 1A / Risks Y",
                "text": "export controls restrict",
            },
            {
                "header_path": "NVDA / 2025 / Item 1A / Risks Z",
                "text": "export controls prevent",
            },
            {
                "header_path": "AMD / 2025 / Item 1A / Competitive",
                "text": "export restrictions apply",
            },
            *[
                {"header_path": f"TSLA / 2025 / Item {i}", "text": "unrelated"}
                for i in range(6)
            ],
        ]
    }
    expected = {
        "header_paths": [
            "NVDA / 2025 / Item 1A",
            "AMD / 2025 / Item 1A",
            "INTC / 2025 / Item 1A",
        ],
        "answer_snippets": [
            "export controls",
            "export restrictions",
            "trade compliance",
        ],
        "match_mode": "startswith",
    }
    result = header_path_recall_at_10(
        output=output, expected=expected, input={"question": "test"}
    )
    assert isinstance(result, Score)
    assert abs(result.score - 2 / 3) < 0.01


def test_recall_cross_company_at_5_structural_ceiling() -> None:
    output = {
        "retrieved_chunks": [
            {
                "header_path": f"NVDA / 2025 / Item 1A / Section {i}",
                "text": "export controls info",
            }
            for i in range(5)
        ]
    }
    expected = {
        "header_paths": [
            "NVDA / 2025 / Item 1A",
            "AMD / 2025 / Item 1A",
            "INTC / 2025 / Item 1A",
            "AAPL / 2025 / Item 1A",
            "TSLA / 2025 / Item 1A",
        ],
        "answer_snippets": ["export controls"] * 5,
        "match_mode": "startswith",
    }
    result = header_path_recall_at_5(
        output=output, expected=expected, input={"question": "test"}
    )
    assert abs(result.score - 0.2) < 0.01


def test_map_canonical_ranks_1_and_3() -> None:
    """AP = (P@1 + P@3) / R = (1/1 + 2/3) / 2 = 0.8333 when R=2, hits at 1 and 3."""
    chunks = [
        {"header_path": "NVDA / 2025 / Item 1A / A", "text": "export controls"},
        {"header_path": "TSLA / 2025 / Item 2", "text": "unrelated"},
        {"header_path": "AMD / 2025 / Item 1A / B", "text": "export restrictions"},
        {"header_path": "TSLA / 2025 / Item 3", "text": "unrelated"},
    ]
    expected = {
        "header_paths": ["NVDA / 2025 / Item 1A", "AMD / 2025 / Item 1A"],
        "answer_snippets": ["export controls", "export restrictions"],
    }
    assert abs(_compute_map(chunks, expected) - (1.0 + 2 / 3) / 2) < 1e-6


def test_map_canonical_ranks_2_and_4() -> None:
    """AP = (P@2 + P@4) / R = (1/2 + 2/4) / 2 = 0.5 when R=2, hits at 2 and 4."""
    chunks = [
        {"header_path": "TSLA / 2025 / Item 2", "text": "unrelated"},
        {"header_path": "NVDA / 2025 / Item 1A / A", "text": "export controls"},
        {"header_path": "TSLA / 2025 / Item 3", "text": "unrelated"},
        {"header_path": "AMD / 2025 / Item 1A / B", "text": "export restrictions"},
    ]
    expected = {
        "header_paths": ["NVDA / 2025 / Item 1A", "AMD / 2025 / Item 1A"],
        "answer_snippets": ["export controls", "export restrictions"],
    }
    assert abs(_compute_map(chunks, expected) - 0.5) < 1e-6


def test_map_unmatched_expected_reduces_score() -> None:
    """R counts all expected entries even if some are never found.
    R=3, only one hit at rank 1 → AP = (1/1) / 3 = 0.333."""
    chunks = [
        {"header_path": "NVDA / 2025 / Item 1A / A", "text": "export controls"},
    ]
    expected = {
        "header_paths": [
            "NVDA / 2025 / Item 1A",
            "AMD / 2025 / Item 1A",
            "INTC / 2025 / Item 1A",
        ],
        "answer_snippets": ["export controls", "export restrictions", "trade compliance"],
    }
    assert abs(_compute_map(chunks, expected) - 1.0 / 3) < 1e-6


def test_map_single_expected_equals_reciprocal_rank() -> None:
    """With one expected entry, AP degenerates to 1/rank of first hit."""
    chunks = [
        {"header_path": "TSLA / 2025 / Item 2", "text": "unrelated"},
        {"header_path": "TSLA / 2025 / Item 3", "text": "unrelated"},
        {"header_path": "NVDA / 2025 / Item 1A / A", "text": "export controls"},
    ]
    expected = {
        "header_paths": ["NVDA / 2025 / Item 1A"],
        "answer_snippets": ["export controls"],
    }
    assert abs(_compute_map(chunks, expected) - 1.0 / 3) < 1e-6


def test_map_no_hits() -> None:
    """Zero relevant ranks → AP = 0."""
    chunks = [
        {"header_path": "TSLA / 2025 / Item 2", "text": "unrelated"},
    ]
    expected = {
        "header_paths": ["NVDA / 2025 / Item 1A"],
        "answer_snippets": ["export controls"],
    }
    assert _compute_map(chunks, expected) == 0.0
