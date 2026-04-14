import os
import re
from datetime import datetime, timezone
from uuid import NAMESPACE_DNS, uuid5

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langfuse import Langfuse, observe


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


def _canonicalize_ticker(raw: str) -> str:
    if not isinstance(raw, str):
        raise TypeError(f"Expected str, got {type(raw).__name__}")
    stripped = raw.strip()
    if not stripped:
        raise ValueError("Empty ticker")
    return stripped.upper()


_EMBED_MODEL = os.environ.get("SEC_EMBED_MODEL", "text-embedding-3-large")
_EMBED_DIM = int(os.environ.get("SEC_EMBED_DIM", "3072"))


async def _embed_texts(texts: list[str]) -> list[list[float]]:
    """Low-level embedding via OpenAI. Patchable for testing."""
    from llama_index.embeddings.openai import OpenAIEmbedding

    embed_model = OpenAIEmbedding(model=_EMBED_MODEL, dimensions=_EMBED_DIM)
    return await embed_model.aget_text_embedding_batch(texts)


@observe(name="sec_query_embedding", capture_output=False)
async def embed_query(query: str) -> list[float]:
    """Embed a single query string for vector search."""
    from langfuse import get_client
    get_client().update_current_span(
        input={"query": query, "model": _EMBED_MODEL},
    )
    result = await _embed_texts([query])
    get_client().update_current_span(
        output={"dimensions": len(result[0])},
    )
    return result[0]


@observe(name="sec_chunk_embedding", capture_output=False)
async def embed_chunks(texts: list[str]) -> list[list[float]]:
    """Embed document chunks for dense ingestion."""
    from langfuse import get_client
    get_client().update_current_span(
        input={"num_chunks": len(texts), "model": _EMBED_MODEL},
    )
    result = await _embed_texts(texts)
    get_client().update_current_span(
        output={"num_embedded": len(result), "dimensions": len(result[0]) if result else 0},
    )
    return result


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


def _ensure_collection(client, collection: str, vector_size: int = _EMBED_DIM) -> None:
    from qdrant_client import models

    if not client.collection_exists(collection):
        client.create_collection(
            collection_name=collection,
            vectors_config=models.VectorParams(
                size=vector_size,
                distance=models.Distance.COSINE,
            ),
        )


async def _async_ensure_collection(client, collection: str, vector_size: int = _EMBED_DIM) -> None:
    from qdrant_client import models

    if not await client.collection_exists(collection):
        await client.create_collection(
            collection_name=collection,
            vectors_config=models.VectorParams(
                size=vector_size,
                distance=models.Distance.COSINE,
            ),
        )


def _ensure_indexes(client, collection: str) -> None:
    from qdrant_client import models

    client.create_payload_index(
        collection_name=collection,
        field_name="ticker",
        field_schema=models.PayloadSchemaType.KEYWORD,
    )
    client.create_payload_index(
        collection_name=collection,
        field_name="year",
        field_schema=models.PayloadSchemaType.INTEGER,
    )
    client.create_payload_index(
        collection_name=collection,
        field_name="item",
        field_schema=models.PayloadSchemaType.KEYWORD,
    )


async def _async_ensure_indexes(client, collection: str) -> None:
    from qdrant_client import models

    await client.create_payload_index(
        collection_name=collection,
        field_name="ticker",
        field_schema=models.PayloadSchemaType.KEYWORD,
    )
    await client.create_payload_index(
        collection_name=collection,
        field_name="year",
        field_schema=models.PayloadSchemaType.INTEGER,
    )
    await client.create_payload_index(
        collection_name=collection,
        field_name="item",
        field_schema=models.PayloadSchemaType.KEYWORD,
    )


def _sentinel_id(ticker: str, year: int) -> str:
    """Deterministic sentinel point ID for (ticker, year)."""
    return str(uuid5(NAMESPACE_DNS, f"{ticker}:{year}:_status"))


@observe(name="sec_dense_ingestion")
async def ingest_filing(
    ticker: str, year: int, markdown: str, filing_metadata=None
) -> None:
    from langfuse import get_client
    from llama_index.core import Document
    from llama_index.core.node_parser import LangchainNodeParser, MarkdownNodeParser
    from qdrant_client import AsyncQdrantClient, models

    ticker = _canonicalize_ticker(ticker)
    get_client().update_current_span(
        input={"ticker": ticker, "year": year, "markdown_length": len(markdown)},
    )
    collection = os.environ.get(
        "SEC_QDRANT_COLLECTION", "sec_filings_openai_large_dense_baseline"
    )
    qdrant_url = os.environ.get("QDRANT_URL", "http://localhost:6333")

    client = AsyncQdrantClient(url=qdrant_url)
    try:
        await _async_ensure_collection(client, collection, vector_size=_EMBED_DIM)
        await _async_ensure_indexes(client, collection)

        sentinel_point_id = _sentinel_id(ticker, year)
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

        lf = Langfuse()

        with lf.start_as_current_observation(
            name="sec_chunking",
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
        embeddings = await embed_chunks(texts)

        qdrant_points = []
        for (point_id, payload), embedding in zip(points, embeddings):
            qdrant_points.append(
                models.PointStruct(
                    id=point_id,
                    vector=embedding,
                    payload=payload,
                )
            )

        with lf.start_as_current_observation(
            name="sec_qdrant_upsert",
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
        get_client().update_current_span(
            output={"num_chunks": len(qdrant_points), "status": "complete"},
        )
    finally:
        await client.close()
