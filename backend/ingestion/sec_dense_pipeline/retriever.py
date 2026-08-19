"""JIT retriever for the SEC dense pipeline (structured contract).

``search()`` is the single query entry point: cold (ticker not yet ingested
for the requested fiscal year) triggers parse -> ingest -> retrieve in one
call; hot hits Qdrant directly. Cache state is the commit-marker lifecycle
owned by :mod:`.vectorizer` (pending/complete), not a cache this module
manages itself.

Async end-to-end (``AsyncQdrantClient``) — unlike the frozen ``_html``
baseline's sync-client-inside-an-async-function shape, matching the
vectorizer's ingest side.
"""

from __future__ import annotations

import asyncio
import logging
import os

from pydantic import BaseModel
from qdrant_client import AsyncQdrantClient, models
from qdrant_client.http.exceptions import UnexpectedResponse

from backend.common.errors import FinLabError
from backend.common.sec_core import SECError, _resolve_latest_fiscal_year
from backend.ingestion.sec_dense_pipeline.collection_schema import (
    async_ensure_collection_and_indexes,
)
from backend.ingestion.sec_dense_pipeline.common import (
    async_check_commit_marker_complete,
    canonicalize_ticker,
    marker_status_condition,
)
from backend.ingestion.sec_dense_pipeline import vectorizer
from backend.ingestion.sec_dense_pipeline.vectorizer import (
    _EMBED_DIM,
    get_collection_name,
    ingest_filing_with_retry,
    parse_filing_with_retry,
)

logger = logging.getLogger(__name__)


class Chunk(BaseModel):
    """One retrieved chunk — mirrors the new Qdrant payload schema
    (:class:`backend.ingestion.sec_dense_pipeline.chunking.ChunkPayload`)
    plus the point's similarity ``score``. Citation fields
    (``accession_number`` / ``cik`` / ``primary_document``) are always
    present — the new payload denormalizes them onto every chunk, so
    callers never need an out-of-band filing-store lookup to build an
    EDGAR URL.
    """

    ticker: str
    fiscal_year: int
    filing_date: str
    filing_type: str
    accession_number: str
    cik: str
    primary_document: str
    item: str
    block_heading: str | None
    prelude: str | None
    header_path: str
    chunk_index: int
    text: str
    ingested_at: str
    score: float


class JITDisabledError(SECError):
    """JIT is disabled (``SEC_DISABLE_JIT=1``) and the requested ticker/year
    is not already ingested. Set in CI so no test can reach real EDGAR."""


class IngestionInProgressError(SECError):
    """A JIT ingest for this (ticker, fiscal_year) is already running in
    this process. Envelope §1 concurrent-JIT resolution: legible rejection,
    not coalescing or waiting."""


class EmbeddingServiceError(SECError):
    """Query embedding failed."""


class CorpusUnavailableError(SECError):
    """The vector store (or the requested collection within it) is
    unavailable, or a low-level Qdrant failure could not be classified
    more specifically."""


# In-process registry of (ticker, fiscal_year) pairs with a JIT ingest
# currently running. Single backend process assumed (envelope §1: ≤3
# concurrent users, 1 operator) — a multi-worker deployment would need a
# distributed lock instead.
_inflight_ingests: set[tuple[str, int]] = set()


def _try_claim_ingest_slot(key: tuple[str, int]) -> bool:
    """Atomically claim ``key`` for an in-flight ingest in this process.

    No ``await`` between the membership check and the insert, so this is
    a single, uninterruptible step on the asyncio event loop — no lock
    primitive needed. Returns True if claimed (caller must release it in a
    ``finally``); False if another coroutine already holds it.
    """
    if key in _inflight_ingests:
        return False
    _inflight_ingests.add(key)
    return True


def _release_ingest_slot(key: tuple[str, int]) -> None:
    _inflight_ingests.discard(key)


def _build_query_filter(
    ticker: str | None, fiscal_year: int | None
) -> tuple[models.Filter, dict]:
    """Build the Qdrant query filter for a search call.

    Pure and unit-testable in isolation: this is the single place that
    decides whether a ``ticker``/``fiscal_year`` filter actually reaches
    Qdrant. A caller-supplied ticker (or a JIT-resolved fiscal year) must
    always show up here as a ``must`` condition — a query that silently
    drops it would let cross-ticker bleed back into results the AC
    explicitly rules out.
    """
    must_conditions: list[models.Condition] = []
    applied: dict = {}
    if ticker is not None:
        must_conditions.append(
            models.FieldCondition(key="ticker", match=models.MatchValue(value=ticker))
        )
        applied["ticker"] = ticker
    if fiscal_year is not None:
        must_conditions.append(
            models.FieldCondition(
                key="fiscal_year", match=models.MatchValue(value=fiscal_year)
            )
        )
        applied["fiscal_year"] = fiscal_year
    query_filter = models.Filter(
        must=must_conditions or None,
        must_not=[marker_status_condition()],
    )
    return query_filter, applied


def _point_to_chunk(point) -> Chunk:
    payload = point.payload
    return Chunk(
        ticker=payload["ticker"],
        fiscal_year=payload["fiscal_year"],
        filing_date=payload["filing_date"],
        filing_type=payload["filing_type"],
        accession_number=payload["accession_number"],
        cik=payload["cik"],
        primary_document=payload["primary_document"],
        item=payload["item"],
        block_heading=payload.get("block_heading"),
        prelude=payload.get("prelude"),
        header_path=payload["header_path"],
        chunk_index=payload["chunk_index"],
        text=payload["text"],
        ingested_at=payload.get("ingested_at", ""),
        score=point.score,
    )


async def _ensure_ingested(
    client: AsyncQdrantClient, collection: str, ticker: str, fiscal_year: int
) -> bool:
    """Ensure (ticker, fiscal_year) is ingested and committed, JIT if not.

    Returns ``cache_hit``: True if a complete commit marker already existed
    (no work done), False if this call performed the JIT ingest. Raises
    :class:`IngestionInProgressError` if another in-process call is already
    ingesting the same (ticker, fiscal_year) — see the module-level
    ``_inflight_ingests`` registry.
    """
    embedding_hit = await async_check_commit_marker_complete(
        client, collection, ticker, fiscal_year
    )
    if embedding_hit:
        return True

    key = (ticker, fiscal_year)
    if not _try_claim_ingest_slot(key):
        raise IngestionInProgressError(
            f"Ingestion for {ticker} FY{fiscal_year} is already in progress "
            f"in this process; retry shortly."
        )
    try:
        filing = await asyncio.to_thread(
            parse_filing_with_retry, ticker, fiscal_year, False
        )
        await ingest_filing_with_retry(filing)
    finally:
        _release_ingest_slot(key)
    return False


async def search(
    query: str, filters: dict | None = None, top_k: int = 10
) -> list[Chunk]:
    """Semantic search over the SEC dense collection.

    ``filters={"ticker": ..., "fiscal_year": ...}`` (fiscal_year optional —
    omitted resolves to the ticker's latest 10-K) triggers the JIT path:
    ingest the filing first if it is not already committed, then search.
    Without a ``ticker`` filter, searches whatever is already in the
    collection with no JIT side effect.

    Raises the shared :class:`~backend.common.errors.FinLabError` taxonomy
    directly on fetch/parse failures (``TickerNotFoundError``,
    ``RateLimitError``, ``TransientError``, ``ConfigurationError``,
    ``FilingNotFoundError``, ``UnsupportedFilingTypeError``,
    ``EmptyFilingError``) — never swallowed into a generic error, so a
    source-level gap (e.g. a filing with zero substantive items) surfaces
    as a legible, typed failure rather than a silent empty result. Also
    raises ``ValueError`` (bad ``top_k``), :class:`JITDisabledError`,
    :class:`IngestionInProgressError`, :class:`EmbeddingServiceError`, and
    :class:`CorpusUnavailableError` (vector-store failures, including a
    missing collection).
    """
    if not 1 <= top_k <= 100:
        raise ValueError(f"top_k must be between 1 and 100, got {top_k}")

    collection = get_collection_name()
    qdrant_url = os.environ.get("QDRANT_URL", "http://localhost:6333")

    resolved_fiscal_year: int | None = None
    cache_hit: bool | None = None
    ticker: str | None = None

    client = AsyncQdrantClient(url=qdrant_url)
    try:
        if filters and "ticker" in filters:
            ticker = canonicalize_ticker(filters["ticker"])

            if os.environ.get("SEC_DISABLE_JIT") == "1":
                raise JITDisabledError(
                    f"JIT disabled by SEC_DISABLE_JIT=1; "
                    f"pre-load ticker={ticker} via backend/scripts/embed_sec_filings.py"
                )

            await async_ensure_collection_and_indexes(
                client, collection, vector_size=_EMBED_DIM
            )

            fiscal_year_filter = filters.get("fiscal_year")
            if fiscal_year_filter is None:
                resolved_fiscal_year = await asyncio.to_thread(
                    _resolve_latest_fiscal_year, ticker
                )
            else:
                resolved_fiscal_year = fiscal_year_filter
            assert resolved_fiscal_year is not None  # both branches above set it

            cache_hit = await _ensure_ingested(
                client, collection, ticker, resolved_fiscal_year
            )
            logger.info(
                "SEC JIT search ticker=%s fiscal_year=%s cache_hit=%s",
                ticker,
                resolved_fiscal_year,
                cache_hit,
            )

        if not await client.collection_exists(collection):
            raise CorpusUnavailableError(
                f"Collection '{collection}' does not exist. "
                f"Run backend/scripts/embed_sec_filings.py to ingest filings, "
                f"or call search() with filters={{'ticker': ...}} to trigger JIT."
            )

        try:
            # Module-qualified (not a bare imported name) so the shared
            # ``mock_openai_embed`` test fixture — which patches
            # ``vectorizer._embed_texts`` — takes effect here too.
            query_vector = await vectorizer._embed_texts([query])
        except Exception as e:
            raise EmbeddingServiceError(f"Embedding failed: {e}") from e

        query_filter, applied_filters = _build_query_filter(
            ticker, resolved_fiscal_year
        )

        results = await client.query_points(
            collection_name=collection,
            query=query_vector[0],
            limit=top_k,
            with_payload=True,
            query_filter=query_filter,
        )

        return [_point_to_chunk(point) for point in results.points]
    except (ValueError, FinLabError):
        raise
    except UnexpectedResponse as e:
        # Qdrant surfaces missing collections/resources as HTTP 404.
        # Anything else from the vector store is still treated as
        # corpus-level unavailability, but not derived from message text.
        if getattr(e, "status_code", None) == 404:
            raise CorpusUnavailableError(f"Qdrant resource missing: {e}") from e
        raise CorpusUnavailableError(f"Qdrant error: {e}") from e
    except Exception as e:
        raise CorpusUnavailableError(f"Search failed: {e}") from e
    finally:
        await client.close()
