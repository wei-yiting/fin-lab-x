import asyncio
import logging
import os

from langfuse import Langfuse, get_client, observe
from pydantic import BaseModel
from qdrant_client import QdrantClient, models

from backend.ingestion.sec_dense_pipeline.common import (
    canonicalize_ticker,
    check_sentinel_complete,
)
from backend.ingestion.sec_dense_pipeline.vectorizer import (
    _ensure_collection,
    embed_query,
    ingest_filing,
)
from backend.ingestion.sec_filing_pipeline.filing_models import (
    FilingNotFoundError,
    FilingType,
    TickerNotFoundError,
)
from backend.ingestion.sec_filing_pipeline.filing_store import LocalFilingStore
from backend.ingestion.sec_filing_pipeline.pipeline import SECFilingPipeline

logger = logging.getLogger(__name__)


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


@observe(name="check_sec_cache", capture_output=False)
def check_sec_cache(
    ticker: str, year: int, qdrant_client, collection: str
) -> bool:
    """Check if a 'complete' embedding sentinel exists for (ticker, year)."""
    embedding_hit = check_sentinel_complete(qdrant_client, collection, ticker, year)
    get_client().update_current_span(
        input={"ticker": ticker, "year": year},
        output={"embedding_cache_hit": embedding_hit},
    )
    return embedding_hit


async def _resolve_year(
    pipeline: SECFilingPipeline, ticker: str, year: int | None, loop
) -> int:
    """Return the fiscal year to use. EDGAR is the source of truth when year=None."""
    if year is not None:
        return year
    try:
        return await loop.run_in_executor(
            None, pipeline.resolve_latest_year, ticker, "10-K"
        )
    except (TickerNotFoundError, FilingNotFoundError) as exc:
        raise JITTickerNotFoundError(f"No 10-K filing for ticker={ticker}") from exc


async def _ensure_filing_locally(
    pipeline: SECFilingPipeline,
    ticker: str,
    year: int,
    loop,
    lf: Langfuse,
):
    """Return ParsedFiling for (ticker, year). Fetches from EDGAR if not cached locally."""
    filing = LocalFilingStore().get(ticker, FilingType.TEN_K, year)
    if filing is not None:
        return filing

    with lf.start_as_current_observation(
        name="sec_filing_pipeline",
        input={"ticker": ticker, "year": year},
    ) as pipeline_span:
        try:
            with lf.start_as_current_observation(
                name="sec_edgar_download",
                input={"ticker": ticker, "year": year},
            ) as dl_span:
                try:
                    raw = await loop.run_in_executor(
                        None, pipeline.download_raw, ticker, "10-K", year
                    )
                except (TickerNotFoundError, FilingNotFoundError) as exc:
                    raise JITTickerNotFoundError(
                        f"No 10-K filing for ticker={ticker}, year={year}"
                    ) from exc
                dl_span.update(output={
                    "status": "complete",
                    "fiscal_year": raw.fiscal_year,
                })

            with lf.start_as_current_observation(
                name="sec_html_to_markdown",
                input={"ticker": ticker, "fiscal_year": raw.fiscal_year},
            ) as parse_span:
                filing = await loop.run_in_executor(
                    None, pipeline.parse_raw, raw, "10-K"
                )
                parse_span.update(output={
                    "status": "complete",
                    "markdown_length": len(filing.markdown_content),
                })

            pipeline_span.update(output={
                "fiscal_year": filing.metadata.fiscal_year,
                "status": "complete",
            })
        except Exception:
            pipeline_span.update(output={"status": "error"})
            raise

    return filing


@observe(name="sec_retrieval")
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
        client = QdrantClient(url=qdrant_url)
        lf = Langfuse()

        if filters and "ticker" in filters:
            ticker = canonicalize_ticker(filters["ticker"])

            if os.environ.get("SEC_DISABLE_JIT") == "1":
                raise JITDisabledError(
                    f"JIT disabled by SEC_DISABLE_JIT=1; "
                    f"pre-load ticker={ticker} via batch script"
                )

            _ensure_collection(client, collection)
            year_filter = filters.get("year")

            # Fast path: caller supplied a year and embeddings are already
            # complete for it — no EDGAR call (and no SECFilingPipeline
            # construction) needed. SECFilingPipeline.create() requires
            # EDGAR_IDENTITY, so deferring it here also makes search() usable
            # in environments without EDGAR access for already-ingested data.
            if year_filter is not None and check_sec_cache(
                ticker, year_filter, client, collection
            ):
                pass
            else:
                loop = asyncio.get_event_loop()
                pipeline = SECFilingPipeline.create()

                resolved_year = await _resolve_year(
                    pipeline, ticker, year_filter, loop
                )

                if not check_sec_cache(ticker, resolved_year, client, collection):
                    filing = await _ensure_filing_locally(
                        pipeline, ticker, resolved_year, loop, lf
                    )
                    await ingest_filing(
                        ticker, resolved_year,
                        filing.markdown_content, filing.metadata,
                    )

        try:
            query_vector = await embed_query(query)
        except Exception as e:
            raise EmbeddingServiceError(
                f"Embedding failed: {e}"
            ) from e

        with lf.start_as_current_observation(
            name="sec_vector_search",
            input={"query": query, "top_k": top_k, "collection": collection},
        ) as search_span:
            results = client.query_points(
                collection_name=collection,
                query=query_vector,
                limit=top_k,
                with_payload=True,
                query_filter=models.Filter(
                    must_not=[
                        models.FieldCondition(
                            key="status",
                            match=models.MatchAny(any=["pending", "complete"]),
                        )
                    ]
                ),
            )
            search_span.update(output={
                "num_results": len(results.points),
                "top_scores": [round(p.score, 4) for p in results.points[:3]],
                "top_headers": [p.payload.get("header_path", "") for p in results.points[:3]],
            })

        chunks = []
        for point in results.points:
            payload = point.payload
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
        get_client().update_current_span(
            metadata={
                "collection_name": collection,
                "embed_model": os.environ.get("SEC_EMBED_MODEL", "text-embedding-3-large"),
                "filters_applied": False,
            }
        )
        return chunks
    except (
        ValueError,
        JITDisabledError,
        JITTickerNotFoundError,
        EmbeddingServiceError,
    ):
        raise
    except Exception as e:
        # ConfigurationError from the filing pipeline should surface as-is
        # so callers receive a clear signal about missing env vars.
        if type(e).__name__ == "ConfigurationError":
            raise
        if "not found" in str(e).lower() or "doesn't exist" in str(e).lower():
            raise CorpusUnavailableError(
                f"Collection unavailable: {e}"
            ) from e
        raise CorpusUnavailableError(f"Search failed: {e}") from e
