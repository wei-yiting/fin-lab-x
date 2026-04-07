"""Shared fixtures for API tests.

Patches LLM dependencies so the FastAPI lifespan can initialize
an Orchestrator without real API keys (OpenAI, etc.).
"""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch

from fastapi.testclient import TestClient


@pytest.fixture()
def client():
    """TestClient with mocked LLM dependencies for lifespan."""
    mock_agent = MagicMock()
    mock_agent.invoke = MagicMock(return_value={"messages": []})
    mock_agent.ainvoke = AsyncMock(return_value={"messages": []})

    with (
        patch("backend.agent_engine.agents.base.init_chat_model"),
        patch(
            "backend.agent_engine.agents.base.create_agent",
            return_value=mock_agent,
        ),
        patch("backend.agent_engine.agents.base.ToolCallLimitMiddleware"),
        patch("backend.agent_engine.agents.base.handle_tool_errors", new=MagicMock()),
        patch("backend.api.main.AsyncSqliteSaver") as mock_sqlite_cls,
    ):
        mock_ctx = MagicMock()
        mock_ctx.__aenter__ = AsyncMock(return_value=MagicMock())
        mock_ctx.__aexit__ = AsyncMock(return_value=False)
        mock_sqlite_cls.from_conn_string.return_value = mock_ctx

        from backend.api.main import app

        with TestClient(app) as c:
            yield c
