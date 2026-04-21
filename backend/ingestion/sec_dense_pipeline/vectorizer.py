import os
import re
from datetime import datetime, timezone
from uuid import NAMESPACE_DNS, uuid5

from langchain_text_splitters import RecursiveCharacterTextSplitter
from llama_index.core import Document
from llama_index.core.node_parser import LangchainNodeParser, MarkdownNodeParser
from llama_index.embeddings.openai import OpenAIEmbedding
from qdrant_client import AsyncQdrantClient, models
from qdrant_client.http.exceptions import UnexpectedResponse

from backend.ingestion.sec_dense_pipeline.common import (
    canonicalize_ticker,
    sentinel_id,
)
from backend.ingestion.sec_dense_pipeline.tracing import traced_span


def parse_item(raw_header_path: str) -> str:
    """Extract Item number from raw header_path BEFORE ticker/year prefix."""
    if not raw_header_path:
        return "_unknown"
    for level in raw_header_path.split(" / "):
        match = re.match(r"^(Item \d+[A-Z]?(?:\(T\))?)\.?", level.strip())
        if match:
            return match.group(1)
    return "_unknown"


def create_text_splitter() -> RecursiveCharacterTextSplitter:
    return RecursiveCharacterTextSplitter.from_tiktoken_encoder(
        encoding_name="cl100k_base",
        chunk_size=int(os.environ.get("SEC_CHUNK_SIZE", "512")),
        chunk_overlap=int(os.environ.get("SEC_CHUNK_OVERLAP", "50")),
    )


_EMBED_MODEL = os.environ.get("SEC_EMBED_MODEL", "text-embedding-3-large")
_EMBED_DIM = int(os.environ.get("SEC_EMBED_DIM", "3072"))


async def _embed_texts(texts: list[str]) -> list[list[float]]:
    """Low-level embedding via OpenAI. Patchable for testing."""
    embed_model = OpenAIEmbedding(model=_EMBED_MODEL, dimensions=_EMBED_DIM)
    return await embed_model.aget_text_embedding_batch(texts)


async def embed_query(query: str) -> list[float]:
    """Embed a single query string for vector search."""
    result = await _embed_texts([query])
    return result[0]


async def embed_chunks(texts: list[str]) -> list[list[float]]:
    """Embed document chunks for dense ingestion."""
    return await _embed_texts(texts)


def _build_header_path(node) -> str:
    """Build a human-readable header path from MarkdownNodeParser metadata.

    MarkdownNodeParser stores header_path as '/Level1/Level2/' format.
    We convert to 'Level1 / Level2' format, and for nodes at root ('/')
    we extract the heading from the node text.
    """
    raw_path = node.metadata.get("header_path", "/")
    segments = [s for s in raw_path.strip("/").split("/") if s]

    text = node.get_content()
    heading_match = re.match(r"^(#{1,6})\s+(.+?)(?:\n|$)", text)
    if heading_match:
        heading_text = heading_match.group(2).strip()
        if segments:
            if segments[-1] != heading_text:
                segments.append(heading_text)
        else:
            segments.append(heading_text)

    return " / ".join(segments)


_TICKER_INDEX_SCHEMA = models.KeywordIndexParams(
    type=models.KeywordIndexType.KEYWORD,
    is_tenant=True,
)


def _payload_schema(client, collection: str) -> dict:
    """Read existing payload indexes. Only a 404 (missing collection) is
    treated as "no schema"; other errors surface so the caller sees the
    real root cause instead of blindly reissuing CREATE_INDEX calls."""
    try:
        info = client.get_collection(collection)
    except UnexpectedResponse as exc:
        if getattr(exc, "status_code", None) == 404:
            return {}
        raise
    return getattr(info, "payload_schema", {}) or {}


async def _async_payload_schema(client, collection: str) -> dict:
    try:
        info = await client.get_collection(collection)
    except UnexpectedResponse as exc:
        if getattr(exc, "status_code", None) == 404:
            return {}
        raise
    return getattr(info, "payload_schema", {}) or {}


def _is_tenant_index(entry) -> bool:
    params = getattr(entry, "params", None)
    return bool(params and getattr(params, "is_tenant", False))


def _is_already_exists_error(exc: BaseException) -> bool:
    """Detect Qdrant's already-exists response from a concurrent CREATE_INDEX.

    Qdrant returns 400 with an 'already exists' message; the exact wording has
    varied across server versions, so we match on status_code + message body.
    """
    if not isinstance(exc, UnexpectedResponse):
        return False
    status = getattr(exc, "status_code", None)
    if status not in (400, 409):
        return False
    body = getattr(exc, "content", b"") or b""
    if isinstance(body, bytes):
        body = body.decode("utf-8", errors="replace")
    text = f"{body} {exc}".lower()
    return "already exists" in text or "already has" in text


def _ensure_collection(client, collection: str, vector_size: int = _EMBED_DIM) -> None:
    if client.collection_exists(collection):
        _ensure_indexes(client, collection)
        return

    try:
        client.create_collection(
            collection_name=collection,
            vectors_config=models.VectorParams(
                size=vector_size,
                distance=models.Distance.COSINE,
            ),
        )
    except UnexpectedResponse as exc:
        # Another worker won the create race. Reconcile against whatever schema
        # the winning side already installed.
        if not _is_already_exists_error(exc):
            raise
        _ensure_indexes(client, collection)
        return

    # Winning side: skip the schema read and create the full index set.
    # Avoids racing a get_collection against Qdrant's collection bootstrap.
    _create_all_indexes(client, collection)


async def _async_ensure_collection(client, collection: str, vector_size: int = _EMBED_DIM) -> None:
    if await client.collection_exists(collection):
        await _async_ensure_indexes(client, collection)
        return

    try:
        await client.create_collection(
            collection_name=collection,
            vectors_config=models.VectorParams(
                size=vector_size,
                distance=models.Distance.COSINE,
            ),
        )
    except UnexpectedResponse as exc:
        if not _is_already_exists_error(exc):
            raise
        await _async_ensure_indexes(client, collection)
        return

    await _async_create_all_indexes(client, collection)


def _create_all_indexes(client, collection: str) -> None:
    _create_index_if_missing(client, collection, "ticker", _TICKER_INDEX_SCHEMA)
    _create_index_if_missing(
        client, collection, "year", models.PayloadSchemaType.INTEGER
    )
    _create_index_if_missing(
        client, collection, "item", models.PayloadSchemaType.KEYWORD
    )


async def _async_create_all_indexes(client, collection: str) -> None:
    await _async_create_index_if_missing(
        client, collection, "ticker", _TICKER_INDEX_SCHEMA
    )
    await _async_create_index_if_missing(
        client, collection, "year", models.PayloadSchemaType.INTEGER
    )
    await _async_create_index_if_missing(
        client, collection, "item", models.PayloadSchemaType.KEYWORD
    )


def _create_index_if_missing(client, collection: str, field: str, schema) -> None:
    """Create a payload index, tolerating a concurrent create that wins the race."""
    try:
        client.create_payload_index(
            collection_name=collection,
            field_name=field,
            field_schema=schema,
        )
    except UnexpectedResponse as exc:
        if not _is_already_exists_error(exc):
            raise


async def _async_create_index_if_missing(client, collection: str, field: str, schema) -> None:
    try:
        await client.create_payload_index(
            collection_name=collection,
            field_name=field,
            field_schema=schema,
        )
    except UnexpectedResponse as exc:
        if not _is_already_exists_error(exc):
            raise


def _ensure_indexes(client, collection: str) -> None:
    schema = _payload_schema(client, collection)
    ticker_entry = schema.get("ticker")
    if ticker_entry is not None and not _is_tenant_index(ticker_entry):
        try:
            client.delete_payload_index(
                collection_name=collection, field_name="ticker"
            )
        except UnexpectedResponse as exc:
            # 404 means the index was already dropped by another worker.
            if getattr(exc, "status_code", None) != 404:
                raise
        ticker_entry = None

    if ticker_entry is None:
        _create_index_if_missing(client, collection, "ticker", _TICKER_INDEX_SCHEMA)
    if "year" not in schema:
        _create_index_if_missing(
            client, collection, "year", models.PayloadSchemaType.INTEGER
        )
    if "item" not in schema:
        _create_index_if_missing(
            client, collection, "item", models.PayloadSchemaType.KEYWORD
        )


async def _async_ensure_indexes(client, collection: str) -> None:
    schema = await _async_payload_schema(client, collection)
    ticker_entry = schema.get("ticker")
    if ticker_entry is not None and not _is_tenant_index(ticker_entry):
        try:
            await client.delete_payload_index(
                collection_name=collection, field_name="ticker"
            )
        except UnexpectedResponse as exc:
            if getattr(exc, "status_code", None) != 404:
                raise
        ticker_entry = None

    if ticker_entry is None:
        await _async_create_index_if_missing(
            client, collection, "ticker", _TICKER_INDEX_SCHEMA
        )
    if "year" not in schema:
        await _async_create_index_if_missing(
            client, collection, "year", models.PayloadSchemaType.INTEGER
        )
    if "item" not in schema:
        await _async_create_index_if_missing(
            client, collection, "item", models.PayloadSchemaType.KEYWORD
        )


async def ingest_filing(
    ticker: str, year: int, markdown: str, filing_metadata=None
) -> None:
    """Chunk, embed, and upsert a filing into Qdrant.

    No Langfuse spans are emitted unless the caller is already inside an
    active trace (see `tracing.traced_span`). Batch CLI and unit-test callers
    run silently; `search()`'s JIT path produces a nested span tree.
    """
    ticker = canonicalize_ticker(ticker)
    collection = os.environ.get(
        "SEC_QDRANT_COLLECTION", "sec_filings_openai_large_dense_baseline"
    )
    qdrant_url = os.environ.get("QDRANT_URL", "http://localhost:6333")

    client = AsyncQdrantClient(url=qdrant_url)
    try:
        await _async_ensure_collection(client, collection, vector_size=_EMBED_DIM)

        sentinel_point_id = sentinel_id(ticker, year)
        sentinel_vector = [0.0] * _EMBED_DIM
        await client.upsert(
            collection_name=collection,
            points=[
                models.PointStruct(
                    id=sentinel_point_id,
                    vector=sentinel_vector,
                    payload={
                        "ticker": ticker,
                        "year": year,
                        "status": "pending",
                    },
                )
            ],
        )

        with traced_span(
            "sec_chunking",
            input={"markdown_length": len(markdown)},
        ) as chunking_span:
            doc = Document(text=markdown)
            section_nodes = MarkdownNodeParser().get_nodes_from_documents([doc])
            splitter = LangchainNodeParser(create_text_splitter())
            chunk_nodes = splitter.get_nodes_from_documents(section_nodes)
            chunking_span.update(output={
                "num_sections": len(section_nodes),
                "num_chunks": len(chunk_nodes),
            })

        ingested_at = datetime.now(timezone.utc).isoformat()
        filing_date = (
            filing_metadata.filing_date if filing_metadata else "unknown"
        )
        filing_type = (
            str(filing_metadata.filing_type) if filing_metadata else "10-K"
        )
        accession_number = (
            filing_metadata.accession_number if filing_metadata else None
        )

        points = []
        for idx, node in enumerate(chunk_nodes):
            raw_header_path = _build_header_path(node)
            item = parse_item(raw_header_path)
            prefixed_header_path = (
                f"{ticker} / {year} / {raw_header_path}"
                if raw_header_path
                else f"{ticker} / {year}"
            )

            point_id = str(uuid5(NAMESPACE_DNS, f"{ticker}:{year}:{idx}"))

            payload = {
                "ticker": ticker,
                "year": year,
                "filing_date": filing_date,
                "filing_type": filing_type,
                "accession_number": accession_number,
                "item": item,
                "header_path": prefixed_header_path,
                "chunk_index": idx,
                "text": node.get_content(),
                "ingested_at": ingested_at,
            }
            points.append((point_id, payload))

        await client.delete(
            collection_name=collection,
            points_selector=models.Filter(
                must=[
                    models.FieldCondition(
                        key="ticker",
                        match=models.MatchValue(value=ticker),
                    ),
                    models.FieldCondition(
                        key="year",
                        match=models.MatchValue(value=year),
                    ),
                ],
                must_not=[
                    models.FieldCondition(
                        key="status",
                        match=models.MatchAny(any=["pending", "complete"]),
                    ),
                ],
            ),
        )

        texts = [p[1]["text"] for p in points]
        with traced_span(
            "sec_chunk_embedding",
            input={"num_chunks": len(texts), "model": _EMBED_MODEL},
        ) as embed_span:
            embeddings = await embed_chunks(texts)
            embed_span.update(output={
                "num_embedded": len(embeddings),
                "dimensions": len(embeddings[0]) if embeddings else 0,
            })

        qdrant_points = []
        for (point_id, payload), embedding in zip(points, embeddings):
            qdrant_points.append(
                models.PointStruct(
                    id=point_id,
                    vector=embedding,
                    payload=payload,
                )
            )

        with traced_span(
            "sec_qdrant_upsert",
            input={"num_points": len(qdrant_points), "batch_size": 100},
        ) as upsert_span:
            BATCH_SIZE = 100
            for i in range(0, len(qdrant_points), BATCH_SIZE):
                await client.upsert(collection_name=collection, points=qdrant_points[i : i + BATCH_SIZE])

            await client.upsert(
                collection_name=collection,
                points=[
                    models.PointStruct(
                        id=sentinel_point_id,
                        vector=sentinel_vector,
                        payload={
                            "ticker": ticker,
                            "year": year,
                            "status": "complete",
                        },
                    )
                ],
            )
            num_batches = (len(qdrant_points) + BATCH_SIZE - 1) // BATCH_SIZE
            upsert_span.update(output={
                "num_batches": num_batches,
                "status": "complete",
            })
    finally:
        await client.close()
