"""Braintrust task functions wrapping the agent engine.

Task functions use the async streaming path (astream_run) to match
the production API code path exactly.
"""

from __future__ import annotations

import functools
import time
import uuid
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from backend.agent_engine.agents.base import (
    Orchestrator,
    OrchestratorResult,
    RunTiming,
    RunUsage,
    ToolOutput,
)
from backend.agent_engine.agents.config_loader import ProfileConfigLoader
from backend.agent_engine.streaming.domain_events_schema import (
    Finish,
    ReasoningDelta,
    StreamError,
    TextDelta,
    ToolCall,
    ToolError,
    ToolResult,
)


@functools.lru_cache(maxsize=4)
def _get_orchestrator(profile: str) -> Orchestrator:
    """Return a cached Orchestrator for the given profile to avoid repeated init."""
    config = ProfileConfigLoader(profile).load()
    return Orchestrator(config, checkpointer=None)


@functools.lru_cache(maxsize=8)
def _get_orchestrator_from_dir(
    config_dir: Path, prompt_path: Path | None
) -> Orchestrator:
    """Return a cached Orchestrator for a benchmark/experiment config directory.

    ``prompt_path`` is injected explicitly (see
    ``ProfileConfigLoader.load_from_dir``) — the caller decides which prompt
    a config directory runs with.
    """
    config = ProfileConfigLoader.load_from_dir(config_dir, prompt_path=prompt_path)
    return Orchestrator(config, checkpointer=None)


async def _astream_collect(
    orchestrator: Orchestrator,
    prompt: str,
    *,
    session_id: str | None = None,
    trace_metadata: Mapping[str, object] | None = None,
) -> OrchestratorResult:
    """Run astream_run and collect domain events into OrchestratorResult."""
    effective_session_id = session_id or f"eval-{uuid.uuid4()}"

    text_parts: list[str] = []
    tool_outputs: list[ToolOutput] = []
    tool_names: dict[str, str] = {}
    tool_args: dict[str, dict] = {}
    errors: list[str] = []
    finished_normally = False
    usage = RunUsage(input_tokens=0, output_tokens=0)
    started_at = time.perf_counter()
    first_event_s: float | None = None
    first_text_s: float | None = None

    if trace_metadata is None:
        stream = orchestrator.astream_run(
            message=prompt,
            session_id=effective_session_id,
        )
    else:
        stream = orchestrator.astream_run(
            message=prompt,
            session_id=effective_session_id,
            trace_metadata=trace_metadata,
        )

    async for event in stream:
        if isinstance(event, (ReasoningDelta, TextDelta, ToolCall)):
            elapsed = time.perf_counter() - started_at
            if first_event_s is None:
                first_event_s = elapsed
            if first_text_s is None and isinstance(event, TextDelta):
                first_text_s = elapsed
        if isinstance(event, TextDelta):
            text_parts.append(event.delta)
        elif isinstance(event, ToolCall):
            tool_names[event.tool_call_id] = event.tool_name
            tool_args[event.tool_call_id] = event.args
        elif isinstance(event, ToolResult):
            tool_outputs.append(
                ToolOutput(
                    tool=tool_names.get(event.tool_call_id, "unknown"),
                    args=tool_args.get(event.tool_call_id, {}),
                    result=event.result,
                )
            )
        elif isinstance(event, ToolError):
            tool_outputs.append(
                ToolOutput(
                    tool=tool_names.get(event.tool_call_id, "unknown"),
                    args=tool_args.get(event.tool_call_id, {}),
                    error=event.error,
                )
            )
            errors.append(event.error)
        elif isinstance(event, StreamError):
            errors.append(event.error_text)
        elif isinstance(event, Finish):
            usage = RunUsage(
                input_tokens=event.usage.input_tokens,
                output_tokens=event.usage.output_tokens,
            )
            if event.finish_reason == "error":
                if errors:
                    raise RuntimeError(f"Stream error: {errors[-1]}")
            else:
                finished_normally = True

    return OrchestratorResult(
        response="".join(text_parts),
        tool_outputs=tool_outputs,
        model=orchestrator.config.model.name,
        version=orchestrator.config.version,
        finished_normally=finished_normally,
        timing=RunTiming(
            first_event_s=first_event_s,
            first_text_s=first_text_s,
            total_s=time.perf_counter() - started_at,
        ),
        usage=usage,
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
    # Commit-marker points (status pending/complete) are bookkeeping records —
    # exclude them so the count reflects real chunk content.
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
    from backend.ingestion.sec_dense_pipeline_html.retriever import search

    question = input["question"]
    chunks = await search(query=question, top_k=10)
    return {"retrieved_chunks": [chunk.model_dump() for chunk in chunks]}


async def run_profile(input: Any, profile: str = "baseline") -> OrchestratorResult:
    """Braintrust task function: run the given Workflow Profile via async streaming.

    Uses astream_run() to match the production API code path.
    """
    orchestrator = _get_orchestrator(profile)
    if isinstance(input, str):
        prompt = input
    elif isinstance(input, Mapping):
        prompt = input.get("prompt", str(input))
    else:
        prompt = str(input)
    return await _astream_collect(orchestrator, prompt)


async def run_baseline_behavior_diagnostic(
    input: Any,
    profile: str | None = None,
    *,
    config_dir: Path | None = None,
    prompt_path: Path | None = None,
) -> OrchestratorResult:
    """Task wrapper for baseline behavior diagnostic scenario rows.

    Extracts the eval prompt from ``question`` and runs it against one
    config: the ``baseline`` profile by default, another Workflow Profile
    via ``profile``, or a benchmark/experiment config directory via
    ``config_dir`` (with ``prompt_path`` as its explicitly injected prompt).
    ``profile`` and ``config_dir`` are mutually exclusive.
    """
    if config_dir is not None and profile is not None:
        raise ValueError("Pass either profile or config_dir, not both")
    if config_dir is None and prompt_path is not None:
        raise ValueError("prompt_path is only valid together with config_dir")

    if config_dir is not None:
        orchestrator = _get_orchestrator_from_dir(config_dir, prompt_path)
    else:
        orchestrator = _get_orchestrator(profile or "baseline")
    if not isinstance(input, Mapping):
        raise TypeError("baseline_behavior_diagnostic input must be a mapping")

    prompt = str(input["question"])
    session_id_value = input.get("session_id")
    session_id = str(session_id_value) if session_id_value is not None else None
    trace_metadata_value = input.get("trace_metadata")
    if trace_metadata_value is not None and not isinstance(
        trace_metadata_value, Mapping
    ):
        raise TypeError("trace_metadata must be a mapping")

    return await _astream_collect(
        orchestrator,
        prompt,
        session_id=session_id,
        trace_metadata=(
            dict(trace_metadata_value) if trace_metadata_value is not None else None
        ),
    )
