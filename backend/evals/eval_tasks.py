"""Braintrust task functions wrapping the agent engine.

Task functions use the async streaming path (astream_run) to match
the production API code path exactly.
"""

from __future__ import annotations

import functools
import uuid
from collections.abc import Mapping
from typing import Any

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


async def run_sec_retrieval(input: Any) -> dict:
    """Retrieval-only eval task — calls search() directly, no agent, no filters."""
    import os

    from qdrant_client import QdrantClient, models

    from backend.ingestion.sec_dense_pipeline.retriever import search

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

    question = input["question"]
    chunks = await search(query=question, top_k=10)
    return {"retrieved_chunks": [chunk.model_dump() for chunk in chunks]}


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
