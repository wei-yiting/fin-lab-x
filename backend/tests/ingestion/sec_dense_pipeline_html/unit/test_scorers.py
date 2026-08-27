"""Unit tests for the sec_retrieval scorers (OR-set semantics).

Per the DEV-162 round-2/3 ruling, expected `header_paths` /
`answer_snippets` are index-aligned ALTERNATIVES: a chunk matching any
(header_path, snippet) pair satisfies the row. recall@k is 0/1 per row and
MAP degenerates to MRR.
"""

import pytest
from autoevals import Score

from backend.evals.scenarios.sec_retrieval.scorer import (
    _chunk_hits_any,
    _first_hit_rank,
    header_path_recall_at_5,
    header_path_recall_at_10,
    mean_average_precision,
    mean_reciprocal_rank,
)

NVDA_1A = "NVDA / 2025 / Item 1A"
NVDA_7 = "NVDA / 2025 / Item 7"


@pytest.mark.parametrize(
    "chunk_path,chunk_text,alternatives,expected_hit",
    [
        # path + snippet both match
        (
            f"{NVDA_1A} / Risks Related",
            "US export controls limit access to certain licenses",
            [(NVDA_1A, "export controls")],
            True,
        ),
        # path matches, snippet does not
        (
            f"{NVDA_1A} / Risks Related",
            "Revenue grew significantly in Q4",
            [(NVDA_1A, "export controls")],
            False,
        ),
        # snippet matches but path does not (e.g. an unlisted Note copy):
        # containment alone never scores a hit
        (
            "NVDA / 2025 / Item 8. Financial Statements / Note 16",
            "US export controls limit access to certain licenses",
            [(NVDA_1A, "export controls")],
            False,
        ),
        # legacy path-only alternative (no snippet)
        (f"{NVDA_1A} / Risks", "any text", [(NVDA_1A, None)], True),
        # second alternative carries the hit
        (
            f"{NVDA_7} / Results",
            "sales to one direct customer represented 22% of total revenue",
            [(NVDA_1A, "no such text"), (NVDA_7, "one direct customer")],
            True,
        ),
    ],
)
def test_chunk_hits_any(chunk_path, chunk_text, alternatives, expected_hit) -> None:
    chunk = {"header_path": chunk_path, "text": chunk_text}
    assert _chunk_hits_any(chunk, alternatives) == expected_hit


def _output(*chunks: dict) -> dict:
    return {"retrieved_chunks": list(chunks)}


UNRELATED = {"header_path": "TSLA / 2025 / Item 2", "text": "unrelated"}
HIT_1A = {"header_path": f"{NVDA_1A} / Risks / A", "text": "export controls limit"}
HIT_7 = {
    "header_path": f"{NVDA_7} / Results",
    "text": "one direct customer represented 22% of total revenue",
}
EXPECTED_OR = {
    "header_paths": [NVDA_1A, NVDA_7],
    "answer_snippets": ["export controls", "one direct customer"],
}


def test_recall_is_binary_any_alternative() -> None:
    output = _output(UNRELATED, HIT_7, UNRELATED)
    result = header_path_recall_at_5(
        output=output, expected=EXPECTED_OR, input={"question": "q"}
    )
    assert isinstance(result, Score)
    assert result.score == 1.0


def test_recall_k_boundary() -> None:
    output = _output(*([UNRELATED] * 5), HIT_1A)  # first hit at rank 6
    at5 = header_path_recall_at_5(
        output=output, expected=EXPECTED_OR, input={"question": "q"}
    )
    at10 = header_path_recall_at_10(
        output=output, expected=EXPECTED_OR, input={"question": "q"}
    )
    assert at5.score == 0.0
    assert at10.score == 1.0


def test_recall_no_hit() -> None:
    output = _output(*([UNRELATED] * 10))
    result = header_path_recall_at_10(
        output=output, expected=EXPECTED_OR, input={"question": "q"}
    )
    assert result.score == 0.0


def test_mrr_first_hit_rank() -> None:
    output = _output(UNRELATED, UNRELATED, HIT_1A, HIT_7)
    result = mean_reciprocal_rank(
        output=output, expected=EXPECTED_OR, input={"question": "q"}
    )
    assert abs(result.score - 1 / 3) < 1e-6


def test_map_equals_mrr_under_or_set() -> None:
    output = _output(UNRELATED, HIT_7)
    mrr = mean_reciprocal_rank(
        output=output, expected=EXPECTED_OR, input={"question": "q"}
    )
    map_ = mean_average_precision(
        output=output, expected=EXPECTED_OR, input={"question": "q"}
    )
    assert mrr.score == map_.score == 0.5


def test_no_hit_scores_zero() -> None:
    output = _output(UNRELATED)
    assert (
        mean_reciprocal_rank(
            output=output, expected=EXPECTED_OR, input={"question": "q"}
        ).score
        == 0.0
    )
    assert (
        mean_average_precision(
            output=output, expected=EXPECTED_OR, input={"question": "q"}
        ).score
        == 0.0
    )


def test_empty_expected_scores_zero() -> None:
    assert _first_hit_rank([HIT_1A], {"header_paths": []}) is None
    result = header_path_recall_at_5(
        output=_output(HIT_1A), expected={"header_paths": []}, input={"question": "q"}
    )
    assert result.score == 0.0


def test_legacy_cross_company_row_scores_any_hit() -> None:
    """The old 10-row placeholder's cross-company rows relied on AND
    semantics; under OR-set they score as any-hit (accepted, see scorer
    module docstring)."""
    output = _output(HIT_1A, *([UNRELATED] * 9))
    expected = {
        "header_paths": [NVDA_1A, "AMD / 2025 / Item 1A", "INTC / 2025 / Item 1A"],
        "answer_snippets": ["export controls", "export restrictions", "trade"],
    }
    result = header_path_recall_at_10(
        output=output, expected=expected, input={"question": "q"}
    )
    assert result.score == 1.0
