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

from backend.common.sec_core import SECError
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
                # dict() widens the TypedDict to the plain mapping the client
                # declares; same contents, and it keeps ChunkPayload as the
                # checked shape everywhere upstream of this call.
                payload=dict(payload),
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
