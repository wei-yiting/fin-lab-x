"""Tests for backend/agent_engine/byok.py — engine-side BYOK concerns
(DEV-189): validating a key against the provider, and classifying a
provider auth failure as a BYOK key rejection vs. an unrelated failure.

Kept in the engine (not backend/api/) because both concerns require
knowing about the provider SDK's own exception types — AGENTS.md §4
reserves that knowledge for backend/agent_engine/.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import openai
import pytest

from backend.agent_engine.byok import (
    ByokKeyRejectedError,
    is_byok_auth_rejection,
    validate_openai_api_key,
)


def _auth_error() -> openai.AuthenticationError:
    response = httpx.Response(
        401, request=httpx.Request("POST", "https://api.openai.com/v1/models")
    )
    return openai.AuthenticationError(
        "Incorrect API key provided", response=response, body=None
    )


def _mock_openai_client(**model_list_kwargs) -> MagicMock:
    mock_client = MagicMock()
    mock_client.models.list = AsyncMock(**model_list_kwargs)
    return mock_client


class TestValidateOpenaiApiKey:
    @pytest.mark.asyncio
    async def test_valid_key_returns_valid(self):
        with patch(
            "backend.agent_engine.byok.AsyncOpenAI",
            return_value=_mock_openai_client(return_value=MagicMock()),
        ):
            assert await validate_openai_api_key("sk-proj-x") == "valid"

    @pytest.mark.asyncio
    async def test_invalid_key_returns_invalid(self):
        with patch(
            "backend.agent_engine.byok.AsyncOpenAI",
            return_value=_mock_openai_client(side_effect=_auth_error()),
        ):
            assert await validate_openai_api_key("sk-proj-x") == "invalid"

    @pytest.mark.asyncio
    async def test_network_error_returns_unexpected_error(self):
        with patch(
            "backend.agent_engine.byok.AsyncOpenAI",
            return_value=_mock_openai_client(
                side_effect=httpx.ConnectError("network down")
            ),
        ):
            assert await validate_openai_api_key("sk-proj-x") == "unexpected_error"

    @pytest.mark.asyncio
    async def test_client_constructed_with_the_given_key(self):
        with patch(
            "backend.agent_engine.byok.AsyncOpenAI",
            return_value=_mock_openai_client(return_value=MagicMock()),
        ) as mock_cls:
            await validate_openai_api_key("sk-proj-exact-key")
        assert mock_cls.call_args.kwargs["api_key"] == "sk-proj-exact-key"

    @pytest.mark.asyncio
    async def test_client_configured_with_ten_second_timeout(self):
        with patch(
            "backend.agent_engine.byok.AsyncOpenAI",
            return_value=_mock_openai_client(return_value=MagicMock()),
        ) as mock_cls:
            await validate_openai_api_key("sk-proj-x")
        assert mock_cls.call_args.kwargs["timeout"] == 10.0


class TestIsByokAuthRejection:
    def test_byok_request_with_auth_error_is_true(self):
        assert is_byok_auth_rejection(_auth_error(), api_key="sk-proj-x") is True

    def test_byok_request_with_other_error_is_false(self):
        assert (
            is_byok_auth_rejection(RuntimeError("boom"), api_key="sk-proj-x") is False
        )

    def test_server_key_with_auth_error_is_false(self):
        """No api_key (server-key path) — never classified as a BYOK
        rejection, even though the exception type matches. A rejected
        server key is an operator problem, not a signal to tell a
        free-tier user their nonexistent key is invalid."""
        assert is_byok_auth_rejection(_auth_error(), api_key=None) is False


class TestByokKeyRejectedError:
    def test_is_a_plain_exception(self):
        assert isinstance(ByokKeyRejectedError(), Exception)
