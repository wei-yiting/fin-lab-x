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
    ):
        from backend.api.main import app

        with TestClient(app) as c:
            yield c
