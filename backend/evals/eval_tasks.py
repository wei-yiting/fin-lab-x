"""Braintrust task functions wrapping the agent engine.

Task functions use the async streaming path (astream_run) to match
the production API code path exactly.
"""

from __future__ import annotations

import functools
import uuid
from collections.abc import Mapping
from typing import Any

from langfuse import get_client, observe

from backend.agent_engine.agents.base import Orchestrator, OrchestratorResult
from backend.agent_engine.agents.config_loader import VersionConfigLoader
from backend.agent_engine.streaming.domain_events_schema import (
    Finish,
    StreamError,
    TextDelta,
    ToolCall,
    ToolError,
    ToolResult,
)


@functools.lru_cache(maxsize=4)
def _get_orchestrator(version: str) -> Orchestrator:
    """Return a cached Orchestrator for the given version to avoid repeated init."""
    config = VersionConfigLoader(version).load()
    return Orchestrator(config, checkpointer=None)


async def _astream_collect(orchestrator: Orchestrator, prompt: str) -> OrchestratorResult:
    """Run astream_run and collect domain events into OrchestratorResult."""
    session_id = f"eval-{uuid.uuid4()}"

    text_parts: list[str] = []
    tool_outputs: list[dict[str, Any]] = []
    tool_names: dict[str, str] = {}
    tool_args: dict[str, dict] = {}
    errors: list[str] = []

    async for event in orchestrator.astream_run(
        message=prompt,
        session_id=session_id,
    ):
        if isinstance(event, TextDelta):
            text_parts.append(event.delta)
        elif isinstance(event, ToolCall):
            tool_names[event.tool_call_id] = event.tool_name
            tool_args[event.tool_call_id] = event.args
        elif isinstance(event, ToolResult):
            tool_outputs.append({
                "tool": tool_names.get(event.tool_call_id, "unknown"),
                "args": tool_args.get(event.tool_call_id, {}),
                "result": event.result,
            })
        elif isinstance(event, ToolError):
            errors.append(event.error)
        elif isinstance(event, StreamError):
            errors.append(event.error_text)
        elif isinstance(event, Finish) and event.finish_reason == "error":
            if errors:
                raise RuntimeError(f"Stream error: {errors[-1]}")

    return OrchestratorResult(
        response="".join(text_parts),
        tool_outputs=tool_outputs,
        model=orchestrator.config.model.name,
        version=orchestrator.config.version,
    )


def pre_run_sec_retrieval() -> dict[str, Any]:
    """Validate Qdrant collection and return banner fields for startup output.

    Runs once before the eval loop — surfaces collection + content-point count
    in the startup banner so the reviewer never has to guess which Qdrant
    collection an experiment was scored against.
    """
    import os

    from qdrant_client import QdrantClient, models

    collection = os.environ.get(
        "SEC_QDRANT_COLLECTION", "sec_filings_openai_large_dense_baseline"
    )
    qdrant_url = os.environ.get("QDRANT_URL", "http://localhost:6333")
    client = QdrantClient(url=qdrant_url)

    if not client.collection_exists(collection):
        raise RuntimeError(
            f"Collection '{collection}' does not exist. "
            "Run the ingest pipeline before eval."
        )
    # Sentinel points (status pending/complete) are bookkeeping markers — exclude
    # them so the count reflects real chunk content.
    content_count = client.count(
        collection_name=collection,
        count_filter=models.Filter(
            must_not=[
                models.FieldCondition(
                    key="status",
                    match=models.MatchAny(any=["pending", "complete"]),
                ),
            ],
        ),
    ).count
    if content_count == 0:
        raise RuntimeError(
            f"Collection '{collection}' has 0 content points. "
            "Run the ingest pipeline before eval."
        )

    return {"Collection": collection, "Points": content_count}


async def run_sec_retrieval(input: Any) -> dict:
    """Retrieval-only eval task — calls search() directly, no agent, no filters."""
    from backend.ingestion.sec_dense_pipeline.retriever import search

    question = input["question"]
    chunks = await search(query=question, top_k=10)
    return {"retrieved_chunks": [chunk.model_dump() for chunk in chunks]}


# --- RAG Filter A/B experiment (article validation) ---------------------------
#
# JIT-free retrieval helper for the two-collection A/B. We bypass
# retriever.search() because its JIT path is tightly coupled with filters:
# any query carrying `filters={"ticker": ...}` triggers EDGAR year-resolve
# and potentially a re-ingest. For eval we want pure query-time filter
# semantics with no implicit network calls.

NAIVE_COLLECTION = "sec_filings_naive"


@observe(name="sec_eval_filter_search")
async def _eval_search(
    *,
    collection: str,
    query: str,
    ticker_filter: str | None,
    top_k: int = 10,
) -> dict:
    """Direct Qdrant query for eval use. No JIT, no EDGAR, no schema mutation.

    Emits a Langfuse trace per call with two child spans:
      - `sec_query_embedding`  (OpenAI embed_query)
      - `sec_vector_search`    (Qdrant query_points)
    The trace mode (naive / three-layer) is captured in the outer span metadata
    so the Langfuse UI can group runs.
    """
    import os

    from qdrant_client import AsyncQdrantClient, models

    from backend.ingestion.sec_dense_pipeline.tracing import traced_span
    from backend.ingestion.sec_dense_pipeline.vectorizer import (
        _EMBED_MODEL,
        embed_query,
    )

    qdrant_url = os.environ.get("QDRANT_URL", "http://localhost:6333")
    client = AsyncQdrantClient(url=qdrant_url)
    try:
        with traced_span(
            "sec_query_embedding",
            input={"query": query, "model": _EMBED_MODEL},
        ) as embed_span:
            query_vector = await embed_query(query)
            embed_span.update(output={"dimensions": len(query_vector)})

        must: list[models.Condition] = []
        if ticker_filter:
            must.append(
                models.FieldCondition(
                    key="ticker",
                    match=models.MatchValue(value=ticker_filter),
                )
            )

        query_filter = models.Filter(
            must=must or None,
            # Defensive: exclude sentinel markers if they happen to live in
            # the collection (three-layer collection carries them).
            must_not=[
                models.FieldCondition(
                    key="status",
                    match=models.MatchAny(any=["pending", "complete"]),
                ),
            ],
        )

        with traced_span(
            "sec_vector_search",
            input={
                "query": query,
                "top_k": top_k,
                "collection": collection,
                "ticker_filter": ticker_filter,
            },
        ) as search_span:
            results = await client.query_points(
                collection_name=collection,
                query=query_vector,
                limit=top_k,
                with_payload=True,
                query_filter=query_filter,
            )
            search_span.update(output={
                "num_results": len(results.points),
                "top_scores": [round(p.score, 4) for p in results.points[:3]],
                "top_tickers": [
                    (p.payload or {}).get("ticker") for p in results.points[:5]
                ],
            })

        chunks: list[dict] = []
        for point in results.points:
            payload = point.payload or {}
            chunks.append({
                "ticker": payload.get("ticker"),
                "year": payload.get("year"),
                "item": payload.get("item", "_unknown"),
                "header_path": payload.get("header_path", ""),
                "chunk_index": payload.get("chunk_index", 0),
                "text": payload.get("text", ""),
                "score": point.score,
            })

        # Mode is captured on the outer span so Langfuse UI can filter
        # naive vs three_layer runs without parsing collection name.
        mode = "naive" if collection == NAIVE_COLLECTION else "three_layer"
        get_client().update_current_span(
            metadata={
                "experiment": "rag_filter_ab",
                "mode": mode,
                "collection": collection,
                "ticker_filter": ticker_filter,
                "top_k": top_k,
            }
        )
        return {"retrieved_chunks": chunks}
    finally:
        await client.close()


async def run_rag_filter_naive(input: Any) -> dict:
    """A/B condition A — naive collection, no payload index, no filter.

    Demonstrates baseline cross-ticker contamination when the three-layer
    contract is absent.
    """
    return await _eval_search(
        collection=NAIVE_COLLECTION,
        query=input["question"],
        ticker_filter=None,
        top_k=10,
    )


async def run_rag_filter_three_layer(input: Any) -> dict:
    """A/B condition C — three-layer collection (Metadata + Index + Tenant),
    query carrying oracle ticker filter.
    """
    import os
    collection = os.environ.get(
        "SEC_QDRANT_COLLECTION", "sec_filings_openai_large_dense_baseline"
    )
    return await _eval_search(
        collection=collection,
        query=input["question"],
        ticker_filter=input["target_ticker"],
        top_k=10,
    )


def pre_run_rag_filter() -> dict[str, Any]:
    """Banner hook for the A/B scenarios — surface BOTH collection point counts.

    Runs once per scenario; if the naive collection is missing, surfaces a
    clear setup instruction instead of cryptic 404s mid-eval.
    """
    import os

    from qdrant_client import QdrantClient, models

    qdrant_url = os.environ.get("QDRANT_URL", "http://localhost:6333")
    three_layer = os.environ.get(
        "SEC_QDRANT_COLLECTION", "sec_filings_openai_large_dense_baseline"
    )
    client = QdrantClient(url=qdrant_url)

    sentinel_excl = models.Filter(
        must_not=[
            models.FieldCondition(
                key="status",
                match=models.MatchAny(any=["pending", "complete"]),
            ),
        ],
    )

    if not client.collection_exists(three_layer):
        raise RuntimeError(
            f"Three-layer collection '{three_layer}' does not exist. "
            "Run backend/scripts/embed_sec_filings.py first."
        )
    three_count = client.count(
        collection_name=three_layer,
        count_filter=sentinel_excl,
    ).count

    if not client.collection_exists(NAIVE_COLLECTION):
        raise RuntimeError(
            f"Naive collection '{NAIVE_COLLECTION}' does not exist. "
            "Run backend/scripts/setup_naive_collection.py first."
        )
    naive_count = client.count(
        collection_name=NAIVE_COLLECTION,
        count_filter=sentinel_excl,
    ).count

    return {
        "Three-layer": f"{three_layer} ({three_count} pts)",
        "Naive": f"{NAIVE_COLLECTION} ({naive_count} pts)",
    }


async def run_v1(input: Any) -> OrchestratorResult:
    """Braintrust task function: run v1_baseline agent via async streaming.

    Uses astream_run() to match the production API code path.
    """
    orchestrator = _get_orchestrator("v1_baseline")
    if isinstance(input, str):
        prompt = input
    elif isinstance(input, Mapping):
        prompt = input.get("prompt", str(input))
    else:
        prompt = str(input)
    return await _astream_collect(orchestrator, prompt)
