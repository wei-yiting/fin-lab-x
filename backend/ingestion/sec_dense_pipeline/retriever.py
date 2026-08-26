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
from typing import NotRequired, TypedDict

from pydantic import BaseModel
from qdrant_client import AsyncQdrantClient, models
from qdrant_client.http.exceptions import UnexpectedResponse

from backend.common.errors import FinLabError
from backend.common.sec_core import SECError, resolve_latest_fiscal_year
from backend.ingestion.sec_dense_pipeline.collection_schema import (
    async_ensure_collection_and_indexes,
)
from backend.ingestion.sec_dense_pipeline.common import (
    EmbeddingServiceError,
    async_check_commit_marker_complete,
    canonicalize_ticker,
    marker_status_condition,
)
from backend.ingestion.sec_dense_pipeline import vectorizer
from backend.ingestion.sec_dense_pipeline.vectorizer import (
    _EMBED_DIM,
    get_collection_name,
    ingest_filing_with_retry,
)
from backend.ingestion.sec_text_pipeline.parser import parse_filing_with_retry

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


class SearchFilters(TypedDict):
    """Required shape for ``search()``'s required ``filters`` argument:
    mandatory ``ticker``, optional ``fiscal_year`` (omitted resolves to the
    ticker's latest 10-K).

    A ``TypedDict`` is a static-typing construct only — it is not enforced
    by Python at runtime, so a value that doesn't match this shape (missing
    entirely, extra keys, wrong value types) can still reach ``search()`` at
    runtime, e.g. from untyped caller code or deserialized JSON. See
    :func:`_validate_filters` for the runtime check that closes that gap.
    """

    ticker: str
    fiscal_year: NotRequired[int]


class JITDisabledError(SECError):
    """JIT is disabled (``SEC_DISABLE_JIT=1``) and the requested ticker/year
    is not already ingested. Set in CI so no test can reach real EDGAR."""


class IngestionInProgressError(SECError):
    """A JIT ingest for this (ticker, fiscal_year) is already running in
    this process. Envelope §1 concurrent-JIT resolution: legible rejection,
    not coalescing or waiting."""


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


_ALLOWED_FILTER_KEYS = frozenset({"ticker", "fiscal_year"})


def _validate_filters(filters: SearchFilters) -> None:
    """Validate the shape/types of a present ``filters`` dict.

    Called before any Qdrant client or EDGAR work runs. Presence of
    ``filters`` and its ``ticker`` key is checked separately by ``search()``
    itself first (that ``ValueError`` is the legible rejection path for a
    caller who omitted filters entirely); this function only runs once
    ``filters`` and its ``ticker`` key are already known to be present, and
    validates the rest of the shape:

    - Unknown keys (e.g. a leftover legacy ``year`` key from the old filter
      contract) are rejected outright rather than silently ignored — an
      ignored key can silently change query results, e.g. a caller passing
      ``{"ticker": ..., "year": 2024}`` would otherwise have ``year`` dropped
      and resolve the latest fiscal year instead of the one requested.
    - ``ticker`` must be a ``str``. A non-string value would otherwise reach
      ``canonicalize_ticker`` as a ``TypeError``, which the generic exception
      handler at the bottom of ``search()`` would misreport as a
      vector-store failure instead of a caller-input error.
    - ``fiscal_year``, if given, must be an ``int`` (excluding ``bool``,
      which is technically an ``int`` subclass in Python but not a
      meaningful fiscal year).
    """
    unknown_keys = set(filters) - _ALLOWED_FILTER_KEYS
    if unknown_keys:
        raise ValueError(
            f"search() filters has unsupported key(s) {sorted(unknown_keys)}; "
            f"only {sorted(_ALLOWED_FILTER_KEYS)} are supported."
        )
    ticker = filters["ticker"]
    if not isinstance(ticker, str):
        raise ValueError(
            f"search() filters['ticker'] must be a str, got {type(ticker).__name__}."
        )
    if "fiscal_year" in filters:
        fiscal_year = filters["fiscal_year"]
        if isinstance(fiscal_year, bool) or not isinstance(fiscal_year, int):
            raise ValueError(
                f"search() filters['fiscal_year'] must be an int, got "
                f"{type(fiscal_year).__name__}."
            )


def _build_query_filter(ticker: str, fiscal_year: int) -> models.Filter:
    """Build the Qdrant query filter for a search call.

    Pure and unit-testable in isolation: this is the single place that
    decides what reaches Qdrant as a ``must`` condition. By the time
    ``search()`` calls this, ``ticker`` is a mandatory search() filter and
    ``fiscal_year`` has always been resolved (explicit or latest) — so both
    are always concrete values here and both always become ``must``
    conditions. A query that silently dropped either would let cross-ticker
    or cross-year bleed back into results — exactly what this filter exists
    to prevent.
    """
    query_filter = models.Filter(
        must=[
            models.FieldCondition(key="ticker", match=models.MatchValue(value=ticker)),
            models.FieldCondition(
                key="fiscal_year", match=models.MatchValue(value=fiscal_year)
            ),
        ],
        must_not=[marker_status_condition()],
    )
    return query_filter


def _point_to_chunk(point: models.ScoredPoint) -> Chunk:
    """Convert one Qdrant search result into a :class:`Chunk`.

    ``models.ScoredPoint.payload`` is typed ``dict[str, Any] | None`` by
    qdrant-client (verified against the installed 1.17.1 package) — Qdrant
    does not guarantee every point carries a payload. Raises ``ValueError``
    (not a bare ``TypeError``) on a missing payload, and lets
    ``pydantic.ValidationError`` (itself a ``ValueError`` subclass) surface
    when the payload doesn't match :class:`Chunk`'s shape — missing or
    wrong-typed required fields alike; extra payload keys are ignored
    (pydantic v2 default) — both are caught by the caller and mapped to
    :class:`CorpusUnavailableError`.
    """
    payload = point.payload
    if payload is None:
        raise ValueError(f"Qdrant point {point.id!r} has no payload")
    return Chunk(**payload, score=point.score)


async def _ensure_ingested(
    client: AsyncQdrantClient, collection: str, ticker: str, fiscal_year: int
) -> bool:
    """Ensure (ticker, fiscal_year) is ingested and committed, JIT if not.

    Returns ``cache_hit``: True if a complete commit marker already existed
    (no work done), False if this call performed the JIT ingest. Raises
    :class:`IngestionInProgressError` if another in-process call is already
    ingesting the same (ticker, fiscal_year) — see the module-level
    ``_inflight_ingests`` registry. Raises :class:`JITDisabledError` if
    ``SEC_DISABLE_JIT=1`` and no complete marker exists yet — an
    already-ingested hit is never blocked by the flag, only genuine JIT work.
    """
    embedding_hit = await async_check_commit_marker_complete(
        client, collection, ticker, fiscal_year
    )
    if embedding_hit:
        return True

    if os.environ.get("SEC_DISABLE_JIT") == "1":
        raise JITDisabledError(
            f"JIT disabled by SEC_DISABLE_JIT=1; ticker={ticker} "
            f"fiscal_year={fiscal_year} is not yet ingested. Pre-load via "
            f"backend/scripts/embed_sec_filings.py"
        )

    key = (ticker, fiscal_year)
    if not _try_claim_ingest_slot(key):
        raise IngestionInProgressError(
            f"Ingestion for {ticker} FY{fiscal_year} is already in progress "
            f"in this process; retry shortly."
        )
    try:
        # Re-check after claiming the slot: the marker can flip to complete
        # between the fast check above and claiming the slot — e.g. a
        # concurrent caller committed this same (ticker, fiscal_year) in
        # that window. Without this, a stale miss would cause a redundant
        # re-parse/re-embed/re-commit of data that is already complete.
        already_complete = await async_check_commit_marker_complete(
            client, collection, ticker, fiscal_year
        )
        if already_complete:
            return True
        filing = await asyncio.to_thread(
            parse_filing_with_retry, ticker, fiscal_year, False
        )
        await ingest_filing_with_retry(filing)
    finally:
        _release_ingest_slot(key)
    return False


async def search(query: str, filters: SearchFilters, top_k: int = 10) -> list[Chunk]:
    """Semantic search over the SEC dense collection.

    ``filters={"ticker": ..., "fiscal_year": ...}`` is required — ``ticker``
    is a mandatory key (``fiscal_year`` optional; omitted resolves to the
    ticker's latest 10-K). Triggers the JIT path: ingest the filing first if
    it is not already committed, then search. An unfiltered, collection-wide
    search is not a supported production path — naive-vs-filtered A/B eval
    measured naive search's ``ticker_precision@10`` as low as 0.00 with no
    legitimate production caller — so ``filters`` missing or lacking
    ``ticker`` raises ``ValueError`` instead of falling through to an
    unfiltered query. See :class:`SearchFilters` for the full shape and
    :func:`_validate_filters` for the runtime checks applied to it.

    Raises the shared :class:`~backend.common.errors.FinLabError` taxonomy
    directly on fetch/parse failures (``TickerNotFoundError``,
    ``RateLimitError``, ``TransientError``, ``ConfigurationError``,
    ``FilingNotFoundError``, ``UnsupportedFilingTypeError``,
    ``EmptyFilingError``) — never swallowed into a generic error, so a
    source-level gap (e.g. a filing with zero substantive items) surfaces
    as a legible, typed failure rather than a silent empty result. Also
    raises ``ValueError`` (bad ``top_k``, a non-dict ``filters`` value,
    missing ``ticker``, or a ``filters`` shape/type rejected by
    :func:`_validate_filters`), :class:`JITDisabledError`,
    :class:`IngestionInProgressError`, :class:`EmbeddingServiceError`, and
    :class:`CorpusUnavailableError` (vector-store failures, including a
    missing collection).
    """
    if not 1 <= top_k <= 100:
        raise ValueError(f"top_k must be between 1 and 100, got {top_k}")
    if filters and not isinstance(filters, dict):
        # A present-but-non-mapping filters (e.g. an int or a list) must be
        # rejected here, before the membership/indexing checks below ever
        # touch it — "ticker" not in 123 raises a raw TypeError, and
        # filters["ticker"] on a list raises a raw TypeError from list
        # indexing. An absent/falsy filters (None, {}) still falls through
        # to the check below unchanged, since `not filters` alone never
        # touches filters as a container.
        raise ValueError(
            f"search() requires filters to be a dict, got {type(filters).__name__}."
        )
    if not filters or "ticker" not in filters:
        raise ValueError(
            "search() requires filters={'ticker': ...}; unfiltered, "
            "collection-wide search is not supported (naive search is a "
            "proven-harmful retrieval mode with no legitimate production "
            "caller)."
        )
    _validate_filters(filters)

    collection = get_collection_name()
    qdrant_url = os.environ.get("QDRANT_URL", "http://localhost:6333")

    client = AsyncQdrantClient(url=qdrant_url)
    try:
        ticker = canonicalize_ticker(filters["ticker"])
        fiscal_year_filter = filters.get("fiscal_year")

        # An omitted fiscal_year requires resolving the latest year via
        # EDGAR before we even know which (ticker, fiscal_year) to check —
        # that resolution call itself must be blocked by the flag. An
        # explicit fiscal_year is NOT gated here: _ensure_ingested() below
        # only raises JITDisabledError for that case on an actual marker
        # miss, so an already-ingested hit still succeeds with the flag on.
        if fiscal_year_filter is None and os.environ.get("SEC_DISABLE_JIT") == "1":
            raise JITDisabledError(
                f"JIT disabled by SEC_DISABLE_JIT=1; omitted fiscal_year "
                f"for ticker={ticker} requires resolving the latest year "
                f"via EDGAR. Pass an explicit fiscal_year for an "
                f"already-ingested hit, or pre-load via "
                f"backend/scripts/embed_sec_filings.py"
            )

        await async_ensure_collection_and_indexes(
            client, collection, vector_size=_EMBED_DIM
        )

        if fiscal_year_filter is None:
            resolved_fiscal_year = await asyncio.to_thread(
                resolve_latest_fiscal_year, ticker
            )
        else:
            resolved_fiscal_year = fiscal_year_filter

        cache_hit = await _ensure_ingested(
            client, collection, ticker, resolved_fiscal_year
        )
        logger.info(
            "SEC JIT search ticker=%s fiscal_year=%s cache_hit=%s",
            ticker,
            resolved_fiscal_year,
            cache_hit,
        )

        try:
            # Module-qualified (not a bare imported name) so the shared
            # ``mock_openai_embed`` test fixture — which patches
            # ``vectorizer._embed_texts`` — takes effect here too.
            query_vector = await vectorizer._embed_texts([query])
        except Exception as e:
            raise EmbeddingServiceError(f"Embedding failed: {e}") from e

        query_filter = _build_query_filter(ticker, resolved_fiscal_year)

        results = await client.query_points(
            collection_name=collection,
            query=query_vector[0],
            limit=top_k,
            with_payload=True,
            query_filter=query_filter,
        )

        chunks = []
        for point in results.points:
            try:
                chunks.append(_point_to_chunk(point))
            except ValueError as e:
                # _point_to_chunk raises plain ValueError for a missing
                # payload and lets pydantic.ValidationError (a ValueError
                # subclass) through for a payload that doesn't match
                # Chunk's shape — including missing required fields. Either
                # way this is malformed vector-store data, not a
                # caller-input problem, so it must be mapped to
                # CorpusUnavailableError here, before the except (ValueError,
                # FinLabError) passthrough below would otherwise let a raw
                # pydantic.ValidationError escape unwrapped.
                raise CorpusUnavailableError(
                    f"Malformed Qdrant payload on point {point.id!r}: {e}"
                ) from e
        return chunks
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
