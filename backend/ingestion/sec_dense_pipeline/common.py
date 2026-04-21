"""Shared utilities for the SEC dense pipeline (vectorizer + retriever)."""

from __future__ import annotations

from uuid import NAMESPACE_DNS, uuid5


def canonicalize_ticker(raw: str) -> str:
    """Normalize a ticker to upper-case stripped form. Raises on invalid input."""
    if not isinstance(raw, str):
        raise TypeError(f"Expected str, got {type(raw).__name__}")
    stripped = raw.strip()
    if not stripped:
        raise ValueError("Empty ticker")
    return stripped.upper()


def sentinel_id(ticker: str, year: int) -> str:
    """Deterministic sentinel point ID for (ticker, year)."""
    return str(uuid5(NAMESPACE_DNS, f"{ticker}:{year}:_status"))


def check_sentinel_complete(client, collection: str, ticker: str, year: int) -> bool:
    """Return True iff a 'complete' sentinel point exists for (ticker, year).

    Sync Qdrant client only — the vector-search and JIT paths use the sync
    client. Catches all exceptions and returns False so that a transient lookup
    failure is treated as a cache miss (caller will re-ingest), not as an
    error that aborts the search.
    """
    try:
        points = client.retrieve(
            collection_name=collection,
            ids=[sentinel_id(ticker, year)],
            with_payload=True,
        )
        return (
            len(points) > 0
            and points[0].payload.get("status") == "complete"
        )
    except Exception:
        return False
