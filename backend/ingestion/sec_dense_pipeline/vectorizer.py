import os
import re
from datetime import datetime, timezone
from uuid import NAMESPACE_DNS, uuid5

from langchain_text_splitters import RecursiveCharacterTextSplitter
from llama_index.core import Document
from llama_index.core.node_parser import LangchainNodeParser, MarkdownNodeParser
from llama_index.embeddings.openai import OpenAIEmbedding
from qdrant_client import AsyncQdrantClient, models

from backend.ingestion.sec_dense_pipeline.collection_schema import (
    _async_ensure_collection,
)
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
            embeddings = await _embed_texts(texts)
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
