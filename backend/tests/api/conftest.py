"""Shared fixtures for API tests.

Patches LLM dependencies so the FastAPI lifespan can initialize
an Orchestrator without real API keys (OpenAI, etc.).
"""

import base64
import pytest
from unittest.mock import MagicMock, AsyncMock, patch

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.primitives.hashes import SHA256
from fastapi.testclient import TestClient

from backend.api import byok


def encrypt_with_public_key(public_key: rsa.RSAPublicKey, plaintext: bytes) -> str:
    """Mirror what the frontend's Web Crypto ``encrypt`` call produces —
    the single source of truth for the RSA-OAEP params every BYOK test
    encrypts against (design-envelope §5 rule 3: don't re-implement this
    per file)."""
    ciphertext = public_key.encrypt(
        plaintext,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=SHA256()), algorithm=SHA256(), label=None
        ),
    )
    return base64.b64encode(ciphertext).decode("ascii")


def encrypt_with_public_pem(public_pem: str, plaintext: bytes) -> str:
    """Same as :func:`encrypt_with_public_key`, for callers that only have
    the PEM string (the common case — most tests only generate a keypair
    and set the private half into env, never loading the public half)."""
    public_key = serialization.load_pem_public_key(public_pem.encode("utf-8"))
    return encrypt_with_public_key(public_key, plaintext)


@pytest.fixture(autouse=True)
def _reset_byok_private_key_cache():
    """``byok._load_private_key`` is process-cached (lru_cache) by design —
    any test across this directory that sets/unsets BYOK_RSA_PRIVATE_KEY
    must not leak its cached result into the next test."""
    byok._load_private_key.cache_clear()
    yield
    byok._load_private_key.cache_clear()


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
        patch("backend.agent_engine.agents.base.RunBudgetMiddleware"),
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
