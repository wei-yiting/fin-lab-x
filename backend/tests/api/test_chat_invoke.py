"""Tests for chat invoke API endpoint."""

import uuid
from unittest.mock import AsyncMock, MagicMock

from backend.api.main import app
from backend.api.routers.chat_invoke import get_orchestrator


def _make_mock_orchestrator(**overrides):
    mock = MagicMock()
    mock.arun = AsyncMock(
        return_value={
            "response": overrides.get("response", "Test response"),
            "tool_outputs": overrides.get("tool_outputs", []),
            "model": overrides.get("model", "test-model"),
            "version": overrides.get("version", "0.1.0"),
        }
    )
    return mock


def _override_orchestrator(mock_orchestrator: MagicMock):
    app.dependency_overrides[get_orchestrator] = lambda: mock_orchestrator


def _clear_overrides():
    app.dependency_overrides.clear()


def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_chat_endpoint_exists(client):
    _override_orchestrator(_make_mock_orchestrator())
    try:
        response = client.post("/api/v1/chat/invoke", json={"message": "test"})
        assert response.status_code != 404
    finally:
        _clear_overrides()


def test_chat_returns_valid_response(client):
    _override_orchestrator(
        _make_mock_orchestrator(
            tool_outputs=[
                {"tool": "tool_a", "args": {"ticker": "AAPL"}, "result": "ok"}
            ]
        )
    )
    try:
        response = client.post("/api/v1/chat/invoke", json={"message": "test"})
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data["response"], str)
        assert isinstance(data["tool_outputs"], list)
        assert isinstance(data["session_id"], str)
        assert isinstance(data["version"], str)
    finally:
        _clear_overrides()


def test_chat_missing_message_field(client):
    response = client.post("/api/v1/chat/invoke", json={})
    assert response.status_code == 422


def test_chat_empty_body(client):
    response = client.post("/api/v1/chat/invoke")
    assert response.status_code == 422


def test_chat_empty_message(client):
    _override_orchestrator(_make_mock_orchestrator(response="Empty message response"))
    try:
        response = client.post("/api/v1/chat/invoke", json={"message": ""})
        assert response.status_code == 200
        assert response.json()["response"] == "Empty message response"
    finally:
        _clear_overrides()


def test_chat_with_session_id(client):
    mock_orch = _make_mock_orchestrator()
    _override_orchestrator(mock_orch)
    try:
        response = client.post(
            "/api/v1/chat/invoke", json={"message": "test", "session_id": "sess_123"}
        )
        assert response.status_code == 200
        assert response.json()["session_id"] == "sess_123"
        # request_id is generated per-request; only assert stable kwargs
        call = mock_orch.arun.await_args
        assert call.args == ("test",)
        assert call.kwargs["session_id"] == "sess_123"
        assert isinstance(call.kwargs.get("request_id"), str)
        assert call.kwargs["request_id"]
    finally:
        _clear_overrides()


def test_chat_default_session_id(client):
    _override_orchestrator(_make_mock_orchestrator())
    try:
        response = client.post("/api/v1/chat/invoke", json={"message": "test"})
        assert response.status_code == 200
        session_id = response.json()["session_id"]
        uuid.UUID(session_id)
    finally:
        _clear_overrides()


def test_chat_orchestrator_error_returns_500(client):
    mock = MagicMock()
    mock.arun = AsyncMock(side_effect=RuntimeError("boom"))
    _override_orchestrator(mock)
    try:
        response = client.post("/api/v1/chat/invoke", json={"message": "test"})
        assert response.status_code == 500
        assert "detail" in response.json()
    finally:
        _clear_overrides()


def test_health_returns_version(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "version" in data
    assert "status" in data
