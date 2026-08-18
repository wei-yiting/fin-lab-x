"""Shared utilities for the SEC dense pipeline (vectorizer + retriever).

Deliberately duplicates the marker/ticker helpers of the frozen
``sec_dense_pipeline_html`` baseline instead of importing them: the frozen
tree is deleted whole at sunset, and the two pipelines must stay independent
during the A/B coexistence window. The duplication expires with the sunset PR.
"""

from __future__ import annotations

from uuid import NAMESPACE_DNS, uuid5

from qdrant_client import QdrantClient, models

# Payload ``status`` values that mark a commit-marker point. Content chunks
# never carry a ``status`` field, so matching on these values identifies
# marker points in any filter.
MARKER_STATUSES = ("pending", "complete")


def canonicalize_ticker(raw: str) -> str:
    """Normalize a ticker to upper-case stripped form. Raises on invalid input."""
    if not isinstance(raw, str):
        raise TypeError(f"Expected str, got {type(raw).__name__}")
    stripped = raw.strip()
    if not stripped:
        raise ValueError("Empty ticker")
    return stripped.upper()


def commit_marker_id(ticker: str, fiscal_year: int) -> str:
    """Deterministic commit-marker point ID for (ticker, fiscal_year)."""
    return str(uuid5(NAMESPACE_DNS, f"{ticker}:{fiscal_year}:_status"))


def marker_status_condition() -> models.FieldCondition:
    """Condition matching commit-marker points.

    Put it in a filter's ``must_not`` to exclude markers from content
    queries and content wipes — the single definition both the ingest wipe
    and the retrieval query build on, so the two sides can never disagree
    about what a marker looks like.
    """
    return models.FieldCondition(
        key="status",
        match=models.MatchAny(any=list(MARKER_STATUSES)),
    )


def check_commit_marker_complete(
    client: QdrantClient, collection: str, ticker: str, fiscal_year: int
) -> bool:
    """Return True iff a 'complete' commit marker exists for (ticker, fiscal_year).

    Sync Qdrant client only — the vector-search and JIT paths use the sync
    client. Catches all exceptions and returns False so that a transient lookup
    failure is treated as a cache miss (caller will re-ingest), not as an
    error that aborts the search.
    """
    try:
        points = client.retrieve(
            collection_name=collection,
            ids=[commit_marker_id(ticker, fiscal_year)],
            with_payload=True,
        )
        return len(points) > 0 and points[0].payload.get("status") == "complete"
    except Exception:
        return False
