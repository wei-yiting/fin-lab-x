"""Tests for the financial news search tool."""

import json
import os
import sys
from typing import Any, cast
from unittest.mock import MagicMock, patch

import pytest

from backend.agent_engine.tools.news_search import (
    TRUSTED_NEWS_DOMAINS,
    tavily_financial_search,
)


def _tool_call(tool_func, args: dict) -> dict:
    """Invoke a tool with a full ToolCall (required for InjectedToolCallId).

    Returns the parsed dict from the ToolMessage content.
    """
    msg = tool_func.invoke(
        {
            "args": args,
            "name": tool_func.name,
            "type": "tool_call",
            "id": "test-call-id",
        }
    )
    return json.loads(msg.content)


def test_tavily_tool_exists():
    assert tavily_financial_search is not None
    assert hasattr(tavily_financial_search, "invoke")


def test_tavily_financial_search_missing_api_key():
    with patch.dict(os.environ, {}, clear=True):
        with pytest.raises(ValueError, match="TAVILY_API_KEY"):
            _tool_call(
                tavily_financial_search,
                {"query": "earnings", "ticker": "AAPL"},
            )


@patch.dict(os.environ, {"TAVILY_API_KEY": "test-key"}, clear=True)
@patch.dict("sys.modules", {"tavily": MagicMock()})
@patch("backend.agent_engine.tools.news_search.TavilyClient", create=True)
def test_tavily_financial_search_results(tavily_client_mock):
    cast(Any, sys.modules["tavily"]).TavilyClient = tavily_client_mock
    tavily_client_mock.return_value.search.return_value = {
        "results": [
            {
                "title": "Title 1",
                "url": "https://example.com/1",
                "content": "Content 1",
                "published_date": "2024-01-01",
            },
            {
                "title": "Title 2",
                "url": "https://example.com/2",
                "content": "Content 2",
                "published_date": "2024-01-02",
            },
        ]
    }

    result = _tool_call(
        tavily_financial_search, {"query": "earnings", "ticker": "aapl"}
    )

    assert result["query"] == "AAPL earnings"
    assert len(result["results"]) == 2
    assert result["results"][0]["title"] == "Title 1"
    assert result["results"][1]["url"] == "https://example.com/2"
    tavily_client_mock.return_value.search.assert_called_once_with(
        query="AAPL earnings",
        include_domains=TRUSTED_NEWS_DOMAINS,
        max_results=5,
    )
