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


def _chunk_key(chunk: dict) -> tuple:
    """Stable identity for a chunk so the same chunk can't satisfy multiple expected entries.

    Real Qdrant chunks carry (ticker, year, chunk_index) — use that. Synthetic
    test chunks may omit those, so fall back to (header_path, text) which is
    unique per row and stable across calls.
    """
    if "chunk_index" in chunk and "ticker" in chunk and "year" in chunk:
        return ("by_id", chunk["ticker"], chunk["year"], chunk["chunk_index"])
    return ("by_payload", chunk.get("header_path"), chunk.get("text"))


def _compute_recall_at_k(
    chunks: list[dict], expected: dict, k: int
) -> float:
    """Compute recall@k. A single chunk can satisfy at most one expected entry."""
    top_k = chunks[:k]
    expected_paths = expected["header_paths"]
    snippets = expected.get("answer_snippets") or []

    matched_paths: set[int] = set()
    used_chunks: set[tuple] = set()
    for path_idx, exp_path in enumerate(expected_paths):
        exp_entry = {
            "header_paths": [exp_path],
            "answer_snippets": [snippets[path_idx]]
            if path_idx < len(snippets)
            else [],
        }
        for c in top_k:
            key = _chunk_key(c)
            if key in used_chunks:
                continue
            if _is_hit(c, exp_entry):
                matched_paths.add(path_idx)
                used_chunks.add(key)
                break

    total_expected = len(expected_paths)
    if total_expected == 0:
        return 0.0
    return len(matched_paths) / total_expected


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
    """Average Precision with fixed denominator R = total expected entries.

    Each chunk greedily binds to the first unmatched expected entry it hits,
    so unmatched entries pull AP down.
    """
    expected_paths = expected["header_paths"]
    snippets = expected.get("answer_snippets") or []
    total_expected = len(expected_paths)

    if total_expected == 0:
        return 0.0

    matched_entries: set[int] = set()
    used_chunks: set[tuple] = set()
    relevant_ranks: list[int] = []

    for rank, c in enumerate(chunks, start=1):
        key = _chunk_key(c)
        if key in used_chunks:
            continue
        for path_idx, exp_path in enumerate(expected_paths):
            if path_idx in matched_entries:
                continue
            exp_entry = {
                "header_paths": [exp_path],
                "answer_snippets": [snippets[path_idx]]
                if path_idx < len(snippets)
                else [],
            }
            if _is_hit(c, exp_entry):
                matched_entries.add(path_idx)
                used_chunks.add(key)
                relevant_ranks.append(rank)
                break

    if not relevant_ranks:
        return 0.0

    ap = 0.0
    for i, k in enumerate(relevant_ranks, start=1):
        precision_at_k = i / k
        ap += precision_at_k
    return ap / total_expected


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
