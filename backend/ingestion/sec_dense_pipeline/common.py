"""Shared utilities for the SEC dense pipeline (vectorizer + retriever + JIT).

Deliberately duplicates the marker/ticker helpers of the frozen
``sec_dense_pipeline_html`` baseline instead of importing them: the frozen
tree is deleted whole at sunset, and the two pipelines must stay independent
during the A/B coexistence window. The duplication expires with the sunset PR.
"""

from __future__ import annotations

from uuid import NAMESPACE_DNS, uuid5

from qdrant_client import AsyncQdrantClient, QdrantClient, models

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


def _marker_is_complete(points: list[models.Record]) -> bool:
    """Shared predicate for both the sync and async marker-check below —
    the one place that decides what a 'complete' commit-marker point looks
    like, so the two Qdrant-client variants can't drift apart on it."""
    return bool(points) and (points[0].payload or {}).get("status") == "complete"


def check_commit_marker_complete(
    client: QdrantClient, collection: str, ticker: str, fiscal_year: int
) -> bool:
    """Return True iff a 'complete' commit marker exists for (ticker, fiscal_year).

    Sync Qdrant client. Returns False only when the retrieve call succeeds
    and no complete marker is found (empty result, or a marker whose status
    isn't 'complete') — a genuine "not ingested yet" state. A Qdrant lookup
    failure (transport, HTTP, or response-validation) propagates to the
    caller instead of being folded into that same False, so a permanent
    failure is never silently treated as "nothing ingested" and driven into
    an unnecessary re-ingest. See :func:`async_check_commit_marker_complete`
    for the retriever's async counterpart.
    """
    points = client.retrieve(
        collection_name=collection,
        ids=[commit_marker_id(ticker, fiscal_year)],
        with_payload=True,
    )
    return _marker_is_complete(points)


async def async_check_commit_marker_complete(
    client: AsyncQdrantClient, collection: str, ticker: str, fiscal_year: int
) -> bool:
    """Async counterpart of :func:`check_commit_marker_complete`, same contract.

    The retriever's JIT path is async end-to-end (``AsyncQdrantClient``,
    matching the vectorizer's ingest side), unlike the frozen ``_html``
    baseline which mixed a sync Qdrant client into an async ``search()``.
    """
    points = await client.retrieve(
        collection_name=collection,
        ids=[commit_marker_id(ticker, fiscal_year)],
        with_payload=True,
    )
    return _marker_is_complete(points)
