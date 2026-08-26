"""Tests for the BYOK key validation router (DEV-189).

``POST /api/v1/byok/validate-key`` lets the frontend confirm a key works
before saving it, reusing the same encrypted-header transport as the chat
routes. The actual provider call (three-state status logic) is engine-side
(``backend.agent_engine.byok.validate_openai_api_key``, tested in
``backend/tests/agents/test_byok_validation.py``) — this file only tests
the router's own job: wiring the BYOK dependency and wrapping that
function's result, exactly as ``test_chat_invoke.py`` mocks
``orchestrator.arun`` rather than re-testing LangChain internals.
"""

from unittest.mock import AsyncMock, patch

from backend.api import byok
from backend.scripts.generate_byok_keypair import generate_keypair
from backend.tests.api.conftest import encrypt_with_public_pem as _encrypt_with


def _configured_key_header(monkeypatch, plaintext: bytes = b"sk-proj-test-key") -> str:
    private_pem, public_pem = generate_keypair()
    monkeypatch.setenv(byok._PRIVATE_KEY_ENV_VAR, private_pem.replace("\n", "\\n"))
    return _encrypt_with(public_pem, plaintext)


class TestValidateKeyRouterWiring:
    def test_returns_the_engine_functions_status_verbatim(self, client, monkeypatch):
        header = _configured_key_header(monkeypatch)
        with patch(
            "backend.api.routers.byok.validate_openai_api_key",
            new=AsyncMock(return_value="valid"),
        ):
            response = client.post(
                "/api/v1/byok/validate-key", headers={byok.BYOK_KEY_HEADER: header}
            )
        assert response.status_code == 200
        assert response.json() == {"status": "valid"}

    def test_passes_the_decrypted_key_to_the_engine_function(self, client, monkeypatch):
        header = _configured_key_header(monkeypatch, plaintext=b"sk-proj-exact-key")
        mock_validate = AsyncMock(return_value="valid")
        with patch(
            "backend.api.routers.byok.validate_openai_api_key", new=mock_validate
        ):
            client.post(
                "/api/v1/byok/validate-key", headers={byok.BYOK_KEY_HEADER: header}
            )
        mock_validate.assert_awaited_once_with("sk-proj-exact-key")


class TestValidateKeyTransportFailures:
    """Transport failures share the same 401 contract as the chat routes —
    the engine function is never reached when the header itself is bad."""

    def test_no_header_returns_401(self, client):
        response = client.post("/api/v1/byok/validate-key")
        assert response.status_code == 401
        assert response.json()["detail"]["code"] == "byok_key_invalid"

    def test_malformed_header_returns_401(self, client, monkeypatch):
        private_pem, _ = generate_keypair()
        monkeypatch.setenv(byok._PRIVATE_KEY_ENV_VAR, private_pem.replace("\n", "\\n"))
        response = client.post(
            "/api/v1/byok/validate-key",
            headers={byok.BYOK_KEY_HEADER: "not-valid-base64!!!"},
        )
        assert response.status_code == 401
        assert response.json()["detail"]["code"] == "byok_key_invalid"

    def test_not_configured_returns_500(self, client, monkeypatch):
        monkeypatch.delenv(byok._PRIVATE_KEY_ENV_VAR, raising=False)
        response = client.post(
            "/api/v1/byok/validate-key",
            headers={byok.BYOK_KEY_HEADER: "c29tZS1jaXBoZXJ0ZXh0"},
        )
        assert response.status_code == 500
        assert response.json()["detail"]["code"] == "byok_not_configured"
