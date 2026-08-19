"""Embedding + Qdrant ingestion for the SEC dense pipeline (structured contract).

``ingest_filing`` consumes a :class:`ParsedFiling` directly — no markdown
intermediate, no node abstraction: chunk payloads come from
:mod:`.chunking`, embeddings from OpenAI, and points go straight to Qdrant
as ``PointStruct``.

Integrity is the per-(ticker, fiscal_year) commit-marker lifecycle: a
``pending`` marker is (over)written first, all chunk points are upserted,
and only then does the marker flip to ``complete``. The retrieval side
treats anything but ``complete`` as absent, so a failed ingest is
indistinguishable from no ingest (committed or absent). No retry wrapper
here: the embedding client retries transient upstream failures internally,
and re-running a failed ingest is the recovery path.
"""

import os
from datetime import UTC, datetime

import httpx
from llama_index.embeddings.openai import OpenAIEmbedding
from qdrant_client import AsyncQdrantClient, models
from qdrant_client.http.exceptions import ResponseHandlingException, UnexpectedResponse

from backend.common.errors import TransientError
from backend.common.retry import retry_transient
from backend.common.sec_core import SECError, _resolve_latest_fiscal_year
from backend.ingestion.sec_dense_pipeline.chunking import (
    build_chunk_payloads,
    chunk_point_id,
)
from backend.ingestion.sec_dense_pipeline.collection_schema import (
    async_ensure_collection_and_indexes,
)
from backend.ingestion.sec_dense_pipeline.common import (
    canonicalize_ticker,
    commit_marker_id,
    marker_status_condition,
)
from backend.ingestion.sec_text_pipeline.filing_models import ParsedFiling
from backend.ingestion.sec_text_pipeline.parser import parse_filing

# Fixed embedding configuration — not runtime knobs: the A/B experiment
# holds the embedding model constant across both pipelines, and changing the
# dimension without wiping the collection would break every upsert against
# the existing vector size.
_EMBED_MODEL = "text-embedding-3-large"
_EMBED_DIM = 3072

DEFAULT_COLLECTION = "sec_filings_openai_large_dense_text"
_UPSERT_BATCH_SIZE = 100


class EmptyIngestError(SECError):
    """A filing produced zero chunk payloads — nothing to commit.

    Raised before any marker/wipe mutation so the retrieval side keeps
    seeing the filing as absent (committed or absent, never silently empty).
    """


def get_collection_name() -> str:
    """New-contract collection; the frozen baseline keeps its own env var."""
    return os.environ.get("SEC_TEXT_QDRANT_COLLECTION", DEFAULT_COLLECTION)


async def _embed_texts(texts: list[str]) -> list[list[float]]:
    """Low-level embedding via OpenAI. Patchable for testing."""
    # Inject a caller-owned async HTTP client and close it explicitly.
    # Without this, GC finalizes the client after asyncio.run() has
    # closed the event loop, raising "Event loop is closed" from
    # httpx's AsyncClient.aclose() — visible as task-exception spam
    # when eval_runner runs the local loop and Braintrust's loop
    # back-to-back.
    async_client = httpx.AsyncClient()
    try:
        embed_model = OpenAIEmbedding(
            model=_EMBED_MODEL,
            dimensions=_EMBED_DIM,
            async_http_client=async_client,
        )
        return await embed_model.aget_text_embedding_batch(texts)
    finally:
        await async_client.aclose()


async def ingest_filing(filing: ParsedFiling) -> None:
    """Chunk, embed, and upsert one parsed filing into Qdrant.

    Wipe-before-rerun: any previous content points for the same
    (ticker, fiscal_year) are deleted before the new upsert, and the
    previous ``complete`` marker is overwritten to ``pending`` up front —
    so a rerun in progress is already invisible to the retrieval side.
    """
    meta = filing.metadata
    ticker = canonicalize_ticker(meta.ticker)
    fiscal_year = meta.fiscal_year

    # Guard before any marker/wipe mutation: a filing that chunks to nothing
    # must stay absent to readers, never become a committed empty corpus.
    payloads = build_chunk_payloads(filing)
    if not payloads:
        raise EmptyIngestError(
            f"Filing {ticker} FY{fiscal_year} produced zero chunk payloads; "
            "refusing to ingest an empty corpus."
        )

    collection = get_collection_name()
    qdrant_url = os.environ.get("QDRANT_URL", "http://localhost:6333")

    client = AsyncQdrantClient(url=qdrant_url)
    try:
        await async_ensure_collection_and_indexes(
            client, collection, vector_size=_EMBED_DIM
        )

        marker_point_id = commit_marker_id(ticker, fiscal_year)
        marker_vector = [0.0] * _EMBED_DIM
        await client.upsert(
            collection_name=collection,
            points=[
                models.PointStruct(
                    id=marker_point_id,
                    vector=marker_vector,
                    payload={
                        "ticker": ticker,
                        "fiscal_year": fiscal_year,
                        "status": "pending",
                    },
                )
            ],
        )

        await client.delete(
            collection_name=collection,
            points_selector=models.Filter(
                must=[
                    models.FieldCondition(
                        key="ticker",
                        match=models.MatchValue(value=ticker),
                    ),
                    models.FieldCondition(
                        key="fiscal_year",
                        match=models.MatchValue(value=fiscal_year),
                    ),
                ],
                must_not=[marker_status_condition()],
            ),
        )

        ingested_at = datetime.now(UTC).isoformat()
        for payload in payloads:
            payload["ingested_at"] = ingested_at

        embeddings = await _embed_texts([p["text"] for p in payloads])

        points = [
            models.PointStruct(
                id=chunk_point_id(ticker, fiscal_year, payload["chunk_index"]),
                vector=embedding,
                payload=payload,
            )
            for payload, embedding in zip(payloads, embeddings, strict=True)
        ]
        for i in range(0, len(points), _UPSERT_BATCH_SIZE):
            await client.upsert(
                collection_name=collection,
                points=points[i : i + _UPSERT_BATCH_SIZE],
            )

        await client.upsert(
            collection_name=collection,
            points=[
                models.PointStruct(
                    id=marker_point_id,
                    vector=marker_vector,
                    payload={
                        "ticker": ticker,
                        "fiscal_year": fiscal_year,
                        "status": "complete",
                    },
                )
            ],
        )
    finally:
        await client.close()


@retry_transient
def parse_filing_with_retry(
    ticker: str, fiscal_year: int, force: bool = False
) -> ParsedFiling:
    """``parse_filing`` with a single retry on ``TransientError``.

    The JIT and batch-ingest callers are the first production users of
    ``retry_transient`` (ADR-0013) — the EDGAR fetch inside ``parse_filing``
    is the one genuinely retryable step in the cold path. Wraps the sync
    ``parse_filing`` directly; async callers run this via
    ``asyncio.to_thread``.
    """
    return parse_filing(ticker, fiscal_year, force)


@retry_transient
def resolve_latest_fiscal_year_with_retry(ticker: str) -> int:
    """``_resolve_latest_fiscal_year`` with a single retry on ``TransientError``.

    Latest-year resolution is itself an EDGAR metadata call (see
    :func:`backend.common.sec_core._resolve_latest_fiscal_year`) and can
    raise ``TransientError`` on a 5xx blip, exactly like ``parse_filing``.
    The JIT retriever and the batch script both resolve an omitted fiscal
    year through this wrapper instead of calling the unretried resolver
    directly, so the cold path's single-retry policy (design-envelope §2)
    covers this EDGAR call too.
    """
    return _resolve_latest_fiscal_year(ticker)


# Qdrant's default REST transport (qdrant_client.http.api_client.ApiClient
# .send_inner / AsyncApiClient.send_inner, verified against the installed
# 1.17.1 package) wraps every exception the underlying httpx client raises
# while sending a request — including connection and timeout failures —
# into ResponseHandlingException(source=original_exc) before it can reach
# caller code. A bare `except httpx.ConnectError` etc. here would therefore
# be unreachable: this tuple is what ResponseHandlingException.source is
# checked against instead.
#
# httpx.TimeoutException (ConnectTimeout, ReadTimeout, WriteTimeout,
# PoolTimeout) and httpx.NetworkError (ConnectError, ReadError, WriteError,
# CloseError) are both "no usable request/response cycle happened at all"
# transport failures (verified against the installed 0.28.1 package's
# exception hierarchy) — the network blips a single retry (design-envelope
# §2) exists to smooth over.
#
# httpx.RemoteProtocolError is deliberately excluded: it means a response
# cycle *did* begin but broke HTTP framing mid-stream (e.g. the peer closed
# the connection mid-response), which is closer in kind to the
# ValidationError-wrapped "response received but malformed" branch below (a
# structural problem retrying is unlikely to fix, and may indicate a real
# incompatibility) than to a clean connection-refused/timeout signal. This
# is a judgment call, not a settled taxonomy fact — revisit if it proves
# wrong in practice.
_TRANSIENT_SOURCE_TYPES = (httpx.TimeoutException, httpx.NetworkError)


@retry_transient
async def ingest_filing_with_retry(filing: ParsedFiling) -> None:
    """``ingest_filing`` with a single retry on transient Qdrant failures.

    ``ingest_filing`` itself deliberately carries no retry wrapper — the
    embedding client already retries transient OpenAI failures internally,
    and wrapping the whole call would double up on that (the stacked-retry
    anti-pattern ADR-0013 exists to rule out). This wrapper targets Qdrant-
    side failure surfaces that ``ingest_filing`` does not classify itself:

    - ``ResponseHandlingException``: Qdrant's REST transport wraps *both*
      connection/timeout failures and successful-response schema validation
      failures (a wrapped ``pydantic.ValidationError``) in this same
      exception type. Only the former is retryable — a validation failure
      means the response was received but doesn't match the expected shape,
      a permanent problem retrying cannot fix — so ``exc.source`` is
      inspected and only connection/timeout-shaped causes are reclassified
      as ``TransientError``; anything else (e.g. a wrapped
      ``ValidationError``) propagates unchanged.
    - ``UnexpectedResponse``: an HTTP error status from Qdrant. Only 5xx
      (server-side) is retried; 4xx propagates unchanged as a permanent
      failure (bad request shape, not a transient blip).

    Everything else (e.g. ``EmptyIngestError``) propagates unchanged on the
    first attempt.
    """
    try:
        await ingest_filing(filing)
    except ResponseHandlingException as exc:
        if isinstance(exc.source, _TRANSIENT_SOURCE_TYPES):
            raise TransientError(
                f"Qdrant connection failure during ingest: {exc}"
            ) from exc
        raise
    except UnexpectedResponse as exc:
        if exc.status_code is not None and 500 <= exc.status_code < 600:
            raise TransientError(f"Qdrant server error during ingest: {exc}") from exc
        raise
