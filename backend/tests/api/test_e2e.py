"""End-to-end tests for chat flow."""

from unittest.mock import AsyncMock, MagicMock, patch

from fastapi.testclient import TestClient
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

from backend.agent_engine.agents.config_loader import VersionConfigLoader
from backend.api.main import app


def test_e2e_chat_flow():
    mock_agent = MagicMock()
    mock_agent.ainvoke = AsyncMock(
        return_value={
            "messages": [
                HumanMessage(content="Analyze AAPL"),
                AIMessage(
                    content="",
                    tool_calls=[
                        {
                            "id": "call_1",
                            "name": "yfinance_stock_quote",
                            "args": {"ticker": "AAPL"},
                        }
                    ],
                ),
                ToolMessage(
                    content="price=100",
                    tool_call_id="call_1",
                    name="yfinance_stock_quote",
                ),
                AIMessage(content="AAPL analysis", tool_calls=[]),
            ]
        }
    )

    with (
        patch("backend.agent_engine.agents.base.init_chat_model"),
        patch("backend.agent_engine.agents.base.ToolCallLimitMiddleware"),
        patch(
            "backend.agent_engine.agents.base.create_agent",
            return_value=mock_agent,
        ),
        patch("backend.agent_engine.agents.base.handle_tool_errors", new=MagicMock()),
        patch("backend.api.main.AsyncSqliteSaver") as mock_sqlite_cls,
    ):
        mock_ctx = MagicMock()
        mock_ctx.__aenter__ = AsyncMock(return_value=MagicMock())
        mock_ctx.__aexit__ = AsyncMock(return_value=False)
        mock_sqlite_cls.from_conn_string.return_value = mock_ctx

        config = VersionConfigLoader("v1_baseline").load()
        with TestClient(app) as client:
            response = client.post(
                "/api/v1/chat/invoke", json={"message": "Analyze AAPL"}
            )

    assert response.status_code == 200
    data = response.json()
    assert data["response"] == "AAPL analysis"
    assert data["tool_outputs"]
    assert data["version"] == config.version


def test_e2e_tool_registry_populated():
    from backend.agent_engine.tools.registry import get_tools_by_names

    config = VersionConfigLoader("v1_baseline").load()
    tools = get_tools_by_names(config.tools)

    assert tools
