"""Replay stand-in for ``tavily_financial_search``.

Same name, description and args schema as the live tool, so the agent sees
an identical tool contract; the body ignores the live query and returns the
frozen fixture for the current (row, condition). The k-th call in a run gets
the k-th recorded call's results, cycling if the agent calls more often than
the recorded run did.
"""

from __future__ import annotations

from contextvars import ContextVar
from dataclasses import dataclass, field
from typing import Any

from langchain_core.tools import StructuredTool

from backend.agent_engine.tools import setup_tools
from backend.agent_engine.tools.news_search import (
    TavilyFinancialSearchInput,
    tavily_financial_search,
)
from backend.agent_engine.tools.registry import register_tool


@dataclass
class ReplayState:
    calls: list[dict[str, Any]]
    served: list[dict[str, Any]] = field(default_factory=list)


replay_state: ContextVar[ReplayState | None] = ContextVar("replay_state", default=None)


async def _replay(query: str, ticker: str) -> dict[str, Any]:
    state = replay_state.get()
    if state is None:
        raise RuntimeError("tavily replay called without a fixture in context")
    index = len(state.served) % len(state.calls)
    results = state.calls[index]["results"]
    full_query = f"{ticker.strip().upper()} {query}".strip()
    state.served.append(
        {
            "fixture_call": index,
            "query": query,
            "ticker": ticker,
            "n_results": len(results),
        }
    )
    return {"query": full_query, "results": results}


replay_tavily = StructuredTool.from_function(
    coroutine=_replay,
    name=tavily_financial_search.name,
    description=tavily_financial_search.description,
    args_schema=TavilyFinancialSearchInput,
)


def install() -> None:
    """Swap the registry entry; orchestrators built afterwards get the replay."""
    setup_tools()
    register_tool(tavily_financial_search.name, replay_tavily)
