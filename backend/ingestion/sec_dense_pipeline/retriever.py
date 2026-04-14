import asyncio
import logging
import os

from langfuse import Langfuse, get_client, observe
from pydantic import BaseModel

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


def _canonicalize_ticker(raw: str) -> str:
    if not isinstance(raw, str):
        raise TypeError(f"Expected str, got {type(raw).__name__}")
    stripped = raw.strip()
    if not stripped:
        raise ValueError("Empty ticker")
    return stripped.upper()


@observe(name="check_sec_cache", capture_output=False)
def check_sec_cache(ticker: str, year: int | None, qdrant_client, collection: str):
    """Check filing cache and embedding sentinel. Returns (filing, year, filing_hit, embedding_hit)."""
    from backend.ingestion.sec_filing_pipeline.filing_models import FilingType
    from backend.ingestion.sec_filing_pipeline.filing_store import LocalFilingStore

    store = LocalFilingStore()
    resolved_year = year
    filing = None

    if year is None:
        years = store.list_filings(ticker, FilingType.TEN_K)
        if years:
            resolved_year = max(years)

    if resolved_year is not None:
        filing = store.get(ticker, FilingType.TEN_K, resolved_year)

    filing_hit = filing is not None
    embedding_hit = (
        resolved_year is not None
        and _check_sentinel(qdrant_client, collection, ticker, resolved_year)
    )

    get_client().update_current_span(
        input={"ticker": ticker, "year": year},
        output={
            "filing_cache_hit": filing_hit,
            "embedding_cache_hit": embedding_hit,
            "resolved_year": resolved_year,
        },
    )
    return filing, resolved_year, filing_hit, embedding_hit


def _edgar_download_raw(ticker: str, year: int | None = None):
    """Call EDGAR API to download raw filing. Returns (RawFiling, SECFilingPipeline)."""
    from backend.ingestion.sec_filing_pipeline import (
        ConfigurationError,
        SECPipelineError,
    )
    from backend.ingestion.sec_filing_pipeline.filing_models import FilingType
    from backend.ingestion.sec_filing_pipeline.pipeline import SECFilingPipeline

    pipeline = SECFilingPipeline.create()

    try:
        raw = pipeline._downloader.download(ticker, str(FilingType.TEN_K), year)
    except ConfigurationError:
        raise
    except SECPipelineError as exc:
        raise JITTickerNotFoundError(
            f"No 10-K filing for ticker={ticker}"
            + (f", year={year}" if year else "")
        ) from exc

    return raw, pipeline


def _parse_raw_filing(raw, pipeline):
    """Parse raw HTML to markdown and store locally. Returns ParsedFiling."""
    from datetime import UTC, datetime

    from backend.ingestion.sec_filing_pipeline.filing_models import (
        FilingMetadata,
        FilingType,
        ParsedFiling,
    )
    from backend.ingestion.sec_filing_pipeline.html_to_md_converter import (
        convert_with_fallback,
    )

    cleaned_html = pipeline._preprocessor.preprocess(raw.raw_html)
    markdown, converter_name = convert_with_fallback(
        cleaned_html, pipeline._converter, pipeline._fallback_converter
    )
    markdown = pipeline._markdown_cleaner.clean(markdown)

    metadata = FilingMetadata(
        ticker=raw.ticker,
        cik=raw.cik,
        company_name=raw.company_name,
        filing_type=FilingType.TEN_K,
        filing_date=raw.filing_date,
        fiscal_year=raw.fiscal_year,
        accession_number=raw.accession_number,
        source_url=raw.source_url,
        parsed_at=datetime.now(UTC).isoformat(),
        converter=converter_name,
    )
    filing = ParsedFiling(metadata=metadata, markdown_content=markdown)
    pipeline._store.save(filing)
    return filing


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
        from qdrant_client import QdrantClient

        from backend.ingestion.sec_dense_pipeline.vectorizer import (
            embed_query,
            ingest_filing,
        )

        client = QdrantClient(url=qdrant_url)
        lf = Langfuse()

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

            loop = asyncio.get_event_loop()
            year = filters.get("year")

            filing, resolved_year, filing_hit, embedding_hit = check_sec_cache(
                ticker, year, client, collection
            )

            if not filing_hit:
                with lf.start_as_current_observation(
                    name="sec_filing_pipeline",
                    input={"ticker": ticker, "year": year},
                ) as pipeline_span:
                    try:
                        with lf.start_as_current_observation(
                            name="sec_edgar_download",
                            input={"ticker": ticker, "year": year},
                        ) as dl_span:
                            raw, pipeline_obj = await loop.run_in_executor(
                                None, _edgar_download_raw, ticker, year
                            )
                            dl_span.update(output={
                                "status": "complete",
                                "fiscal_year": raw.fiscal_year,
                            })

                        with lf.start_as_current_observation(
                            name="sec_html_to_markdown",
                            input={"ticker": ticker, "fiscal_year": raw.fiscal_year},
                        ) as parse_span:
                            filing = await loop.run_in_executor(
                                None, _parse_raw_filing, raw, pipeline_obj
                            )
                            parse_span.update(output={
                                "status": "complete",
                                "markdown_length": len(filing.markdown_content),
                            })

                        resolved_year = filing.metadata.fiscal_year
                        pipeline_span.update(output={
                            "resolved_year": resolved_year,
                            "status": "complete",
                        })
                    except Exception:
                        pipeline_span.update(output={"status": "error"})
                        raise

            if not embedding_hit:
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
            )
            content_points = [p for p in results.points if "status" not in p.payload]
            search_span.update(output={
                "num_results": len(content_points),
                "top_scores": [round(p.score, 4) for p in content_points[:3]],
                "top_headers": [p.payload.get("header_path", "") for p in content_points[:3]],
            })

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
