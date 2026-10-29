"""Retrieval-level eval scorers for SEC dense pipeline.

Four sync scorers: recall@5, recall@10, MRR, MAP.

OR-set semantics (DEV-162 round-2/3 ruling, 2026-08-27): the expected
`header_paths` / `answer_snippets` lists are index-aligned ALTERNATIVES —
a chunk hits the row when it matches ANY (header_path, snippet) pair
(header_path startswith + snippet containment). One hit anywhere in the
list satisfies the row.

Consequences of the semantic change:
- recall@k degenerates to 0/1 per row (was fractional under the old
  AND-across-entries semantics).
- MAP degenerates to MRR (a single relevant target means AP equals the
  reciprocal rank of the first hit). Both are kept for metric continuity;
  DEV-164 may consolidate them.
- The legacy 10-row placeholder dataset's 3 cross-company rows relied on
  the old AND semantics; under OR they score as any-hit. Accepted — that
  dataset is slated for replacement in DEV-164.
"""

from __future__ import annotations

from typing import Any

from autoevals import Score  # pyright: ignore[reportMissingImports]


def _alternatives(expected: dict) -> list[tuple[str, str | None]]:
    """Expected (header_path, snippet) alternative pairs, index-aligned.

    Rows without snippets (legacy path-only rows) yield None snippets, in
    which case the path match alone decides the hit.
    """
    paths = expected.get("header_paths") or []
    snippets = expected.get("answer_snippets") or []
    return [
        (path, snippets[i] if i < len(snippets) else None)
        for i, path in enumerate(paths)
    ]


def _chunk_hits_any(chunk: dict, alternatives: list[tuple[str, str | None]]) -> bool:
    for path, snippet in alternatives:
        if not chunk["header_path"].startswith(path):
            continue
        if snippet is None or snippet.lower() in chunk["text"].lower():
            return True
    return False


def _first_hit_rank(chunks: list[dict], expected: dict) -> int | None:
    """1-based rank of the first chunk matching any alternative, else None."""
    alternatives = _alternatives(expected)
    if not alternatives:
        return None
    for rank, chunk in enumerate(chunks, start=1):
        if _chunk_hits_any(chunk, alternatives):
            return rank
    return None


def header_path_recall_at_5(output: Any, expected: Any, *, input: Any) -> Score:
    chunks = output.get("retrieved_chunks", []) if isinstance(output, dict) else []
    rank = _first_hit_rank(chunks, expected)
    score = 1.0 if rank is not None and rank <= 5 else 0.0
    return Score(name="header_path_recall_at_5", score=score)


def header_path_recall_at_10(output: Any, expected: Any, *, input: Any) -> Score:
    chunks = output.get("retrieved_chunks", []) if isinstance(output, dict) else []
    rank = _first_hit_rank(chunks, expected)
    score = 1.0 if rank is not None and rank <= 10 else 0.0
    return Score(name="header_path_recall_at_10", score=score)


def mean_reciprocal_rank(output: Any, expected: Any, *, input: Any) -> Score:
    chunks = output.get("retrieved_chunks", []) if isinstance(output, dict) else []
    rank = _first_hit_rank(chunks, expected)
    return Score(name="mrr", score=1.0 / rank if rank is not None else 0.0)


def mean_average_precision(output: Any, expected: Any, *, input: Any) -> Score:
    # Under OR-set semantics there is a single relevant target per row, so
    # AP == reciprocal rank of the first hit. Kept as a separate scorer for
    # metric continuity until DEV-164 consolidates the metric set.
    chunks = output.get("retrieved_chunks", []) if isinstance(output, dict) else []
    rank = _first_hit_rank(chunks, expected)
    return Score(name="map", score=1.0 / rank if rank is not None else 0.0)
