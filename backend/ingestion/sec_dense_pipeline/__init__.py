"""SEC dense pipeline — structured ingest contract over :class:`ParsedFiling`.

Replaces the ingest stage of the frozen HTML pipeline (A/B baseline):
``ingest_filing`` consumes the typed :class:`ParsedFiling` structure directly
(no markdown intermediate), chunks per block, and upserts into the new-contract
Qdrant collection with the full payload schema (citation fields included) under
the per-(ticker, fiscal_year) commit-marker lifecycle.

Public surface: :func:`ingest_filing` plus the marker helpers consumed by the
retrieval side.
"""

from backend.ingestion.sec_dense_pipeline.common import (
    check_commit_marker_complete,
    commit_marker_id,
    marker_status_condition,
)
from backend.ingestion.sec_dense_pipeline.vectorizer import ingest_filing

__all__ = [
    "check_commit_marker_complete",
    "commit_marker_id",
    "ingest_filing",
    "marker_status_condition",
]
