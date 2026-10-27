"""SEC dense pipeline — structured ingest contract over :class:`ParsedFiling`.

Replaces the ingest stage of the frozen HTML pipeline (A/B baseline):
``ingest_filing`` consumes the typed :class:`ParsedFiling` structure directly
(no markdown intermediate), chunks per block, and upserts into the new-contract
Qdrant collection with the full payload schema (citation fields included) under
the per-(ticker, fiscal_year) commit-marker lifecycle.

Public surface: :func:`ingest_filing` plus :class:`EmptyIngestError` and the
marker helpers consumed by the retrieval side.
"""

from backend.ingestion.sec_dense_pipeline.common import (
    async_check_commit_marker_complete,
    commit_marker_id,
    marker_status_condition,
)
from backend.ingestion.sec_dense_pipeline.vectorizer import (
    EmptyIngestError,
    ingest_filing,
)

__all__ = [
    "EmptyIngestError",
    "async_check_commit_marker_complete",
    "commit_marker_id",
    "ingest_filing",
    "marker_status_condition",
]
