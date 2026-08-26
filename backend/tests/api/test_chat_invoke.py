"""Tests for chat invoke API endpoint."""

import uuid
from unittest.mock import AsyncMock, MagicMock

import httpx
import openai

from backend.agent_engine.byok import ByokKeyRejectedError
from backend.api import byok
from backend.api.main import app
from backend.api.routers.chat_invoke import get_orchestrator
from backend.scripts.generate_byok_keypair import generate_keypair
from backend.tests.api.conftest import encrypt_with_public_pem as _encrypt_with


def _auth_error(
    message: str = "Incorrect API key provided",
) -> openai.AuthenticationError:
    response = httpx.Response(
        401, request=httpx.Request("POST", "https://api.openai.com/v1/x")
    )
    return openai.AuthenticationError(message, response=response, body=None)


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


# --- BYOK wiring (DEV-189) ---


class TestChatInvokeByokWiring:
    def test_no_byok_header_passes_none_api_key(self, client):
        mock_orch = _make_mock_orchestrator()
        _override_orchestrator(mock_orch)
        try:
            response = client.post("/api/v1/chat/invoke", json={"message": "test"})
            assert response.status_code == 200
            assert mock_orch.arun.call_args.kwargs["api_key"] is None
        finally:
            _clear_overrides()

    def test_byok_header_decrypted_key_passed_to_arun(self, client, monkeypatch):
        private_pem, public_pem = generate_keypair()
        monkeypatch.setenv(byok._PRIVATE_KEY_ENV_VAR, private_pem.replace("\n", "\\n"))
        encrypted = _encrypt_with(public_pem, b"sk-proj-user-key")
        mock_orch = _make_mock_orchestrator()
        _override_orchestrator(mock_orch)
        try:
            response = client.post(
                "/api/v1/chat/invoke",
                json={"message": "test"},
                headers={byok.BYOK_KEY_HEADER: encrypted},
            )
            assert response.status_code == 200
            assert mock_orch.arun.call_args.kwargs["api_key"] == "sk-proj-user-key"
        finally:
            _clear_overrides()

    def test_malformed_byok_header_returns_401_before_reaching_orchestrator(
        self, client, monkeypatch
    ):
        private_pem, _ = generate_keypair()
        monkeypatch.setenv(byok._PRIVATE_KEY_ENV_VAR, private_pem.replace("\n", "\\n"))
        mock_orch = _make_mock_orchestrator()
        _override_orchestrator(mock_orch)
        try:
            response = client.post(
                "/api/v1/chat/invoke",
                json={"message": "test"},
                headers={byok.BYOK_KEY_HEADER: "not-valid-base64!!!"},
            )
            assert response.status_code == 401
            assert response.json()["detail"]["code"] == "byok_key_invalid"
            mock_orch.arun.assert_not_called()
        finally:
            _clear_overrides()

    def test_empty_byok_header_returns_401(self, client):
        mock_orch = _make_mock_orchestrator()
        _override_orchestrator(mock_orch)
        try:
            response = client.post(
                "/api/v1/chat/invoke",
                json={"message": "test"},
                headers={byok.BYOK_KEY_HEADER: ""},
            )
            assert response.status_code == 401
            assert response.json()["detail"]["code"] == "byok_key_invalid"
        finally:
            _clear_overrides()

    def test_byok_header_present_but_not_configured_returns_500(
        self, client, monkeypatch
    ):
        monkeypatch.delenv(byok._PRIVATE_KEY_ENV_VAR, raising=False)
        mock_orch = _make_mock_orchestrator()
        _override_orchestrator(mock_orch)
        try:
            response = client.post(
                "/api/v1/chat/invoke",
                json={"message": "test"},
                headers={byok.BYOK_KEY_HEADER: "c29tZS1jaXBoZXJ0ZXh0"},
            )
            assert response.status_code == 500
            assert response.json()["detail"]["code"] == "byok_not_configured"
        finally:
            _clear_overrides()

    def test_byok_key_rejected_by_provider_returns_401(self, client, monkeypatch):
        """The real ``Orchestrator.arun`` reclassifies a provider auth
        rejection into ``ByokKeyRejectedError`` when the request was BYOK
        (see test_orchestrator_byok.py) — the mock here stands in for that
        already-reclassified outcome, matching what the router actually
        receives."""
        private_pem, public_pem = generate_keypair()
        monkeypatch.setenv(byok._PRIVATE_KEY_ENV_VAR, private_pem.replace("\n", "\\n"))
        encrypted = _encrypt_with(public_pem, b"sk-proj-bad-key")
        mock = MagicMock()
        mock.arun = AsyncMock(side_effect=ByokKeyRejectedError())
        _override_orchestrator(mock)
        try:
            response = client.post(
                "/api/v1/chat/invoke",
                json={"message": "test"},
                headers={byok.BYOK_KEY_HEADER: encrypted},
            )
            assert response.status_code == 401
            assert response.json()["detail"]["code"] == "byok_key_rejected"
        finally:
            _clear_overrides()

    def test_server_key_rejected_by_provider_still_returns_500(self, client):
        """No BYOK header — an AuthenticationError here means the
        server's OWN key is broken, an operator problem. Must stay a
        generic 500, never the BYOK-specific 401 (that would tell a
        free-tier user their nonexistent key is invalid)."""
        mock = MagicMock()
        mock.arun = AsyncMock(side_effect=_auth_error())
        _override_orchestrator(mock)
        try:
            response = client.post("/api/v1/chat/invoke", json={"message": "test"})
            assert response.status_code == 500
        finally:
            _clear_overrides()
