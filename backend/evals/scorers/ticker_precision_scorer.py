"""Ticker-precision@k scorer for the RAG filter A/B experiment.

Measures: of the top-k retrieved chunks, what fraction belong to the
caller-intended ticker (entity scope). The killer metric for the
"entity mismatch" narrative — naive vector search returns cross-ticker
results, three-layer filter forces 100%.
"""

from __future__ import annotations

from typing import Any

from autoevals import Score  # pyright: ignore[reportMissingImports]


def _precision_at_k(chunks: list[dict], target_ticker: str, k: int) -> float:
    top_k = chunks[:k]
    if not top_k:
        return 0.0
    hits = sum(1 for c in top_k if c.get("ticker") == target_ticker)
    return hits / len(top_k)


def _extract_target_ticker(input: Any) -> str | None:
    if isinstance(input, dict):
        ticker = input.get("target_ticker")
        if isinstance(ticker, str) and ticker:
            return ticker
    return None


def _extract_chunks(output: Any) -> list[dict]:
    if not isinstance(output, dict):
        return []
    chunks = output.get("retrieved_chunks", [])
    return chunks if isinstance(chunks, list) else []


def ticker_precision_at_5(output: Any, expected: Any, *, input: Any) -> Score | None:
    del expected  # contract param, ground truth lives in input.target_ticker
    target = _extract_target_ticker(input)
    if target is None:
        return None
    chunks = _extract_chunks(output)
    return Score(name="ticker_precision_at_5",
                 score=_precision_at_k(chunks, target, k=5))


def ticker_precision_at_10(output: Any, expected: Any, *, input: Any) -> Score | None:
    del expected
    target = _extract_target_ticker(input)
    if target is None:
        return None
    chunks = _extract_chunks(output)
    return Score(name="ticker_precision_at_10",
                 score=_precision_at_k(chunks, target, k=10))
