import asyncio
import os

from pydantic import BaseModel


class Chunk(BaseModel):
    ticker: str
    year: int
    filing_date: str
    filing_type: str
    accession_number: str | None
    item: str
    header_path: str
    chunk_index: int
    text: str
    ingested_at: str
    score: float


class JITTickerNotFoundError(Exception): ...


class EmbeddingServiceError(Exception): ...


class CorpusUnavailableError(Exception): ...


class JITDisabledError(Exception): ...


def _canonicalize_ticker(raw: str) -> str:
    if not isinstance(raw, str):
        raise TypeError(f"Expected str, got {type(raw).__name__}")
    stripped = raw.strip()
    if not stripped:
        raise ValueError("Empty ticker")
    return stripped.upper()


def fetch_filing(ticker: str, year: int | None = None):
    """Fetch filing from local store. Patchable for testing."""
    from backend.ingestion.sec_filing_pipeline.filing_models import FilingType
    from backend.ingestion.sec_filing_pipeline.filing_store import LocalFilingStore

    store = LocalFilingStore()
    if year is None:
        years = store.list_filings(ticker, FilingType.TEN_K)
        if not years:
            raise JITTickerNotFoundError(
                f"No filings found for ticker={ticker}"
            )
        year = max(years)

    filing = store.get(ticker, FilingType.TEN_K, year)
    if filing is None:
        raise JITTickerNotFoundError(
            f"No 10-K filing for ticker={ticker}, year={year}"
        )
    return filing, year


def _check_sentinel(client, collection: str, ticker: str, year: int) -> bool:
    """Check if (ticker, year) sentinel is 'complete' in Qdrant."""
    from backend.ingestion.sec_dense_pipeline.vectorizer import _sentinel_id

    try:
        points = client.retrieve(
            collection_name=collection,
            ids=[_sentinel_id(ticker, year)],
            with_payload=True,
        )
        return (
            len(points) > 0
            and points[0].payload.get("status") == "complete"
        )
    except Exception:
        return False


def _has_any_complete_sentinel(
    client, collection: str, ticker: str
) -> bool:
    """Check if the ticker has any sentinel with status='complete'."""
    from qdrant_client import models

    try:
        result = client.count(
            collection_name=collection,
            count_filter=models.Filter(
                must=[
                    models.FieldCondition(
                        key="ticker",
                        match=models.MatchValue(value=ticker),
                    ),
                    models.FieldCondition(
                        key="status",
                        match=models.MatchValue(value="complete"),
                    ),
                ]
            ),
        )
        return result.count > 0
    except Exception:
        return False


async def search(
    query: str, filters: dict | None = None, top_k: int = 10
) -> list[Chunk]:
    if not 1 <= top_k <= 100:
        raise ValueError(f"top_k must be between 1 and 100, got {top_k}")

    collection = os.environ.get(
        "SEC_QDRANT_COLLECTION", "sec_filings_openai_large_dense_baseline"
    )
    qdrant_url = os.environ.get("QDRANT_URL", "http://localhost:6333")

    try:
        from qdrant_client import QdrantClient

        from backend.ingestion.sec_dense_pipeline.vectorizer import (
            embed_texts,
            ingest_filing,
        )

        client = QdrantClient(url=qdrant_url)

        if filters and "ticker" in filters:
            ticker = _canonicalize_ticker(filters["ticker"])

            if os.environ.get("SEC_DISABLE_JIT") == "1":
                raise JITDisabledError(
                    f"JIT disabled by SEC_DISABLE_JIT=1; "
                    f"pre-load ticker={ticker} via batch script"
                )

            from backend.ingestion.sec_dense_pipeline.vectorizer import (
                _ensure_collection,
            )

            _ensure_collection(client, collection)

            year = filters.get("year")
            if year is not None:
                if not _check_sentinel(client, collection, ticker, year):
                    filing, resolved_year = fetch_filing(ticker, year)
                    loop = asyncio.get_event_loop()
                    await loop.run_in_executor(
                        None,
                        ingest_filing,
                        ticker,
                        resolved_year,
                        filing.markdown_content,
                        filing.metadata,
                    )
            else:
                if not _has_any_complete_sentinel(
                    client, collection, ticker
                ):
                    filing, resolved_year = fetch_filing(ticker, None)
                    if not _check_sentinel(
                        client, collection, ticker, resolved_year
                    ):
                        loop = asyncio.get_event_loop()
                        await loop.run_in_executor(
                            None,
                            ingest_filing,
                            ticker,
                            resolved_year,
                            filing.markdown_content,
                            filing.metadata,
                        )

        embeddings = await embed_texts([query])
        query_vector = embeddings[0]

        results = client.query_points(
            collection_name=collection,
            query=query_vector,
            limit=top_k,
            with_payload=True,
        )

        chunks = []
        for point in results.points:
            payload = point.payload
            if "status" in payload:
                continue
            chunks.append(
                Chunk(
                    ticker=payload["ticker"],
                    year=payload["year"],
                    filing_date=payload.get("filing_date", "unknown"),
                    filing_type=payload.get("filing_type", "10-K"),
                    accession_number=payload.get("accession_number"),
                    item=payload.get("item", "_unknown"),
                    header_path=payload.get("header_path", ""),
                    chunk_index=payload.get("chunk_index", 0),
                    text=payload.get("text", ""),
                    ingested_at=payload.get("ingested_at", ""),
                    score=point.score,
                )
            )
        return chunks
    except (ValueError, JITDisabledError, JITTickerNotFoundError):
        raise
    except Exception as e:
        if "not found" in str(e).lower() or "doesn't exist" in str(e).lower():
            raise CorpusUnavailableError(
                f"Collection unavailable: {e}"
            ) from e
        raise CorpusUnavailableError(f"Search failed: {e}") from e
