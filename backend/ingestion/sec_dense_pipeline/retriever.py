import asyncio
import logging
import os

from langfuse import get_client, observe
from pydantic import BaseModel
from qdrant_client import QdrantClient, models

from backend.ingestion.sec_dense_pipeline.common import (
    canonicalize_ticker,
    check_sentinel_complete,
)
from backend.ingestion.sec_dense_pipeline.tracing import traced_span
from backend.ingestion.sec_dense_pipeline.vectorizer import (
    _EMBED_MODEL,
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


def _check_caches(
    qdrant_client, collection: str, ticker: str, year: int
) -> tuple[bool, bool]:
    """Return (embedding_cache_hit, filing_cache_hit).

    Both checks are cheap: Qdrant sentinel lookup + local filesystem exists.
    Checking both unconditionally keeps the span's output schema uniform so
    the Langfuse UI always shows both flags side by side.
    """
    embedding_hit = check_sentinel_complete(qdrant_client, collection, ticker, year)
    filing_hit = LocalFilingStore().exists(ticker, FilingType.TEN_K, year)
    return embedding_hit, filing_hit


async def _resolve_latest_year(
    pipeline: SECFilingPipeline, ticker: str, loop
) -> int:
    """EDGAR metadata call to learn the latest 10-K fiscal year."""
    try:
        return await loop.run_in_executor(
            None, pipeline.resolve_latest_year, ticker, "10-K"
        )
    except (TickerNotFoundError, FilingNotFoundError) as exc:
        raise JITTickerNotFoundError(f"No 10-K filing for ticker={ticker}") from exc


async def _download_and_parse(
    pipeline: SECFilingPipeline, ticker: str, year: int, loop
):
    """Fetch raw filing from EDGAR and parse to markdown.

    Emits `sec_edgar_download` and `sec_html_to_markdown` child spans under
    whatever parent span is currently active.
    """
    with traced_span(
        "sec_edgar_download",
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

    with traced_span(
        "sec_html_to_markdown",
        input={"ticker": ticker, "fiscal_year": raw.fiscal_year},
    ) as parse_span:
        filing = await loop.run_in_executor(
            None, pipeline.parse_raw, raw, "10-K"
        )
        parse_span.update(output={
            "status": "complete",
            "markdown_length": len(filing.markdown_content),
        })

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

        if filters and "ticker" in filters:
            ticker = canonicalize_ticker(filters["ticker"])

            if os.environ.get("SEC_DISABLE_JIT") == "1":
                raise JITDisabledError(
                    f"JIT disabled by SEC_DISABLE_JIT=1; "
                    f"pre-load ticker={ticker} via batch script"
                )

            _ensure_collection(client, collection)
            year_filter = filters.get("year")
            loop = asyncio.get_event_loop()

            # Resolve fiscal year before any cache lookup so the single
            # check_sec_cache span reflects the actual year we will serve.
            if year_filter is None:
                pipeline = SECFilingPipeline.create()
                with traced_span(
                    "resolve_latest_year",
                    input={"ticker": ticker, "filing_type": "10-K"},
                ) as yr_span:
                    year_to_use = await _resolve_latest_year(pipeline, ticker, loop)
                    yr_span.update(output={"resolved_year": year_to_use})
            else:
                year_to_use = year_filter
                pipeline = None  # constructed lazily only if JIT needs it

            with traced_span(
                "check_sec_cache",
                input={"ticker": ticker, "year": year_to_use},
            ) as cache_span:
                embedding_hit, filing_hit = _check_caches(
                    client, collection, ticker, year_to_use
                )
                cache_span.update(output={
                    "embedding_cache_hit": embedding_hit,
                    "filing_cache_hit": filing_hit,
                })

            if not embedding_hit:
                if pipeline is None:
                    pipeline = SECFilingPipeline.create()

                if filing_hit:
                    filing = LocalFilingStore().get(
                        ticker, FilingType.TEN_K, year_to_use
                    )
                else:
                    with traced_span(
                        "sec_filing_pipeline",
                        input={"ticker": ticker, "year": year_to_use},
                    ) as pipeline_span:
                        try:
                            filing = await _download_and_parse(
                                pipeline, ticker, year_to_use, loop
                            )
                        except Exception:
                            pipeline_span.update(output={"status": "error"})
                            raise
                        pipeline_span.update(output={
                            "fiscal_year": filing.metadata.fiscal_year,
                            "status": "complete",
                        })

                with traced_span(
                    "sec_dense_ingestion",
                    input={
                        "ticker": ticker,
                        "year": year_to_use,
                        "markdown_length": len(filing.markdown_content),
                    },
                ) as ing_span:
                    await ingest_filing(
                        ticker, year_to_use,
                        filing.markdown_content, filing.metadata,
                    )
                    ing_span.update(output={"status": "complete"})

        with traced_span(
            "sec_query_embedding",
            input={"query": query, "model": _EMBED_MODEL},
        ) as embed_span:
            try:
                query_vector = await embed_query(query)
            except Exception as e:
                raise EmbeddingServiceError(
                    f"Embedding failed: {e}"
                ) from e
            embed_span.update(output={"dimensions": len(query_vector)})

        with traced_span(
            "sec_vector_search",
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
