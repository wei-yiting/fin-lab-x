import os
import re
from datetime import datetime, timezone
from uuid import NAMESPACE_DNS, uuid5

from langchain_text_splitters import RecursiveCharacterTextSplitter


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


_EMBED_MODEL = "text-embedding-3-large"
_EMBED_DIM = 3072  # tied to _EMBED_MODEL; change both together


async def embed_texts(texts: list[str]) -> list[list[float]]:
    """Embed texts using OpenAI. Patchable for testing."""
    from llama_index.embeddings.openai import OpenAIEmbedding

    embed_model = OpenAIEmbedding(model=_EMBED_MODEL)
    return await embed_model.aget_text_embedding_batch(texts)


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


def _sentinel_id(ticker: str, year: int) -> str:
    """Deterministic sentinel point ID for (ticker, year)."""
    return str(uuid5(NAMESPACE_DNS, f"{ticker}:{year}:_status"))


def ingest_filing(
    ticker: str, year: int, markdown: str, filing_metadata=None
) -> None:
    import asyncio

    from llama_index.core import Document
    from llama_index.core.node_parser import LangchainNodeParser, MarkdownNodeParser
    from qdrant_client import QdrantClient, models

    ticker = _canonicalize_ticker(ticker)
    collection = os.environ.get(
        "SEC_QDRANT_COLLECTION", "sec_filings_openai_large_dense_baseline"
    )
    qdrant_url = os.environ.get("QDRANT_URL", "http://localhost:6333")

    client = QdrantClient(url=qdrant_url)
    _ensure_collection(client, collection, vector_size=_EMBED_DIM)
    _ensure_indexes(client, collection)

    # Upsert sentinel as "pending" before any content processing
    sentinel_point_id = _sentinel_id(ticker, year)
    sentinel_vector = [0.0] * _EMBED_DIM
    client.upsert(
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

    doc = Document(text=markdown)
    section_nodes = MarkdownNodeParser().get_nodes_from_documents([doc])

    splitter = LangchainNodeParser(create_text_splitter())
    chunk_nodes = splitter.get_nodes_from_documents(section_nodes)

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

    # Delete stale content chunks for this (ticker, year) before upserting.
    # Sentinel points (which have a "status" field) are excluded from deletion.
    client.delete(
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
    embeddings = asyncio.run(embed_texts(texts))

    qdrant_points = []
    for (point_id, payload), embedding in zip(points, embeddings):
        qdrant_points.append(
            models.PointStruct(
                id=point_id,
                vector=embedding,
                payload=payload,
            )
        )

    BATCH_SIZE = 100
    for i in range(0, len(qdrant_points), BATCH_SIZE):
        client.upsert(collection_name=collection, points=qdrant_points[i : i + BATCH_SIZE])

    # Mark sentinel as "complete" after all content is upserted
    client.upsert(
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
