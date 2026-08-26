"""Tests for workflow-profile selection in the FastAPI app's lifespan."""

from unittest.mock import AsyncMock, MagicMock, patch

from fastapi.testclient import TestClient

from backend.agent_engine.agents.config_loader import ProfileConfigLoader


def _run_lifespan_with_profile_spy() -> MagicMock:
    """Enter the app's lifespan (via TestClient) with ProfileConfigLoader
    spied but still real — Orchestrator gets a genuine, valid config for
    whichever profile was resolved, while the spy records which profile
    name lifespan actually passed in."""
    mock_agent = MagicMock()
    mock_agent.invoke = MagicMock(return_value={"messages": []})
    mock_agent.ainvoke = AsyncMock(return_value={"messages": []})

    with (
        patch("backend.agent_engine.agents.base.init_chat_model"),
        patch(
            "backend.agent_engine.agents.base.create_agent",
            return_value=mock_agent,
        ),
        patch("backend.agent_engine.agents.base.RunBudgetMiddleware"),
        patch("backend.agent_engine.agents.base.handle_tool_errors", new=MagicMock()),
        patch("backend.api.main.AsyncSqliteSaver") as mock_sqlite_cls,
        patch(
            "backend.api.main.ProfileConfigLoader", wraps=ProfileConfigLoader
        ) as loader_spy,
    ):
        mock_ctx = MagicMock()
        mock_ctx.__aenter__ = AsyncMock(return_value=MagicMock())
        mock_ctx.__aexit__ = AsyncMock(return_value=False)
        mock_sqlite_cls.from_conn_string.return_value = mock_ctx

        from backend.api.main import app

        with TestClient(app):
            pass

    return loader_spy


def test_lifespan_defaults_to_baseline_profile(monkeypatch):
    monkeypatch.delenv("WORKFLOW_PROFILE", raising=False)
    loader_spy = _run_lifespan_with_profile_spy()
    loader_spy.assert_called_once_with("baseline")


def test_lifespan_respects_workflow_profile_env_override(monkeypatch):
    monkeypatch.setenv("WORKFLOW_PROFILE", "reader")
    loader_spy = _run_lifespan_with_profile_spy()
    loader_spy.assert_called_once_with("reader")
