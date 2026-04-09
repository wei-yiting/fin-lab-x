"""Retrieval-level eval scorers for SEC dense pipeline.

Four sync scorers: recall@5, recall@10, MRR, MAP.
Composite hit logic: header_path startswith + answer snippet contains.
"""

from __future__ import annotations

from typing import Any

from autoevals import Score  # pyright: ignore[reportMissingImports]


def _is_hit(chunk: dict, expected_entry: dict) -> bool:
    path_match = any(
        chunk["header_path"].startswith(p)
        for p in expected_entry["header_paths"]
    )
    snippets = expected_entry.get("answer_snippets")
    if not snippets:
        return path_match
    snippet_match = any(
        s.lower() in chunk["text"].lower() for s in snippets
    )
    return path_match and snippet_match


def _compute_recall_at_k(
    chunks: list[dict], expected: dict, k: int
) -> float:
    """Compute recall@k with per-expected dedup."""
    top_k = chunks[:k]
    expected_paths = expected["header_paths"]
    snippets = expected.get("answer_snippets") or []

    matched = set()
    for path_idx, exp_path in enumerate(expected_paths):
        exp_entry = {
            "header_paths": [exp_path],
            "answer_snippets": [snippets[path_idx]]
            if path_idx < len(snippets)
            else [],
        }
        for c in top_k:
            if _is_hit(c, exp_entry):
                matched.add(path_idx)
                break

    total_expected = len(expected_paths)
    if total_expected == 0:
        return 0.0
    return len(matched) / total_expected


def _compute_mrr(chunks: list[dict], expected: dict) -> float:
    """MRR = 1 / rank of first hit (min rank across all expected entries)."""
    expected_paths = expected["header_paths"]
    snippets = expected.get("answer_snippets") or []

    min_rank = None
    for path_idx, exp_path in enumerate(expected_paths):
        exp_entry = {
            "header_paths": [exp_path],
            "answer_snippets": [snippets[path_idx]]
            if path_idx < len(snippets)
            else [],
        }
        for rank, c in enumerate(chunks, start=1):
            if _is_hit(c, exp_entry):
                if min_rank is None or rank < min_rank:
                    min_rank = rank
                break

    if min_rank is None:
        return 0.0
    return 1.0 / min_rank


def _compute_map(chunks: list[dict], expected: dict) -> float:
    """MAP = mean over expected entries of (1 / rank of first match), 0 for unmatched."""
    expected_paths = expected["header_paths"]
    snippets = expected.get("answer_snippets") or []

    if not expected_paths:
        return 0.0

    reciprocal_ranks = []
    for path_idx, exp_path in enumerate(expected_paths):
        exp_entry = {
            "header_paths": [exp_path],
            "answer_snippets": [snippets[path_idx]]
            if path_idx < len(snippets)
            else [],
        }
        found = False
        for rank, c in enumerate(chunks, start=1):
            if _is_hit(c, exp_entry):
                reciprocal_ranks.append(1.0 / rank)
                found = True
                break
        if not found:
            reciprocal_ranks.append(0.0)

    return sum(reciprocal_ranks) / len(reciprocal_ranks)


def header_path_recall_at_5(
    output: Any, expected: Any, *, input: Any
) -> Score:
    chunks = output.get("retrieved_chunks", []) if isinstance(output, dict) else []
    recall = _compute_recall_at_k(chunks, expected, k=5)
    return Score(name="header_path_recall_at_5", score=recall)


def header_path_recall_at_10(
    output: Any, expected: Any, *, input: Any
) -> Score:
    chunks = output.get("retrieved_chunks", []) if isinstance(output, dict) else []
    recall = _compute_recall_at_k(chunks, expected, k=10)
    return Score(name="header_path_recall_at_10", score=recall)


def mean_reciprocal_rank(
    output: Any, expected: Any, *, input: Any
) -> Score:
    chunks = output.get("retrieved_chunks", []) if isinstance(output, dict) else []
    mrr = _compute_mrr(chunks, expected)
    return Score(name="mrr", score=mrr)


def mean_average_precision(
    output: Any, expected: Any, *, input: Any
) -> Score:
    chunks = output.get("retrieved_chunks", []) if isinstance(output, dict) else []
    map_score = _compute_map(chunks, expected)
    return Score(name="map", score=map_score)
