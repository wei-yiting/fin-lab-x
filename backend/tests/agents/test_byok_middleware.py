"""Tests for the BYOK per-request model override middleware (DEV-189).

``ByokModelOverrideMiddleware`` is the seam that makes "no BYOK header ->
zero behavior change" a structural guarantee rather than a tested
convention: when ``BYOKContext.byok_model`` is absent, both hooks must call
the handler with the request completely unmodified.
"""

import pytest
from unittest.mock import MagicMock

from backend.agent_engine.agents.base import BYOKContext, ByokModelOverrideMiddleware


@pytest.fixture()
def middleware():
    return ByokModelOverrideMiddleware()


def _request_with_context(context) -> MagicMock:
    request = MagicMock()
    request.runtime.context = context
    return request


class TestWrapModelCallSync:
    def test_no_context_calls_handler_with_original_request(self, middleware):
        request = _request_with_context(None)
        handler = MagicMock()

        middleware.wrap_model_call(request, handler)

        handler.assert_called_once_with(request)
        request.override.assert_not_called()

    def test_context_without_byok_model_calls_handler_with_original_request(
        self, middleware
    ):
        request = _request_with_context(BYOKContext(byok_model=None))
        handler = MagicMock()

        middleware.wrap_model_call(request, handler)

        handler.assert_called_once_with(request)
        request.override.assert_not_called()

    def test_byok_model_present_overrides_model_before_calling_handler(
        self, middleware
    ):
        byok_model = MagicMock(name="byok_model")
        request = _request_with_context(BYOKContext(byok_model=byok_model))
        overridden = MagicMock(name="overridden_request")
        request.override.return_value = overridden
        handler = MagicMock()

        middleware.wrap_model_call(request, handler)

        request.override.assert_called_once_with(model=byok_model)
        handler.assert_called_once_with(overridden)


class TestAwrapModelCallAsync:
    @pytest.mark.asyncio
    async def test_no_context_calls_handler_with_original_request(self, middleware):
        request = _request_with_context(None)

        async def handler(req):
            handler.called_with = req
            return "response"

        result = await middleware.awrap_model_call(request, handler)

        assert handler.called_with is request
        assert result == "response"
        request.override.assert_not_called()

    @pytest.mark.asyncio
    async def test_byok_model_present_overrides_model_before_calling_handler(
        self, middleware
    ):
        byok_model = MagicMock(name="byok_model")
        request = _request_with_context(BYOKContext(byok_model=byok_model))
        overridden = MagicMock(name="overridden_request")
        request.override.return_value = overridden

        async def handler(req):
            handler.called_with = req
            return "response"

        result = await middleware.awrap_model_call(request, handler)

        request.override.assert_called_once_with(model=byok_model)
        assert handler.called_with is overridden
        assert result == "response"


class TestByokContextDefaults:
    def test_default_byok_model_is_none(self):
        assert BYOKContext().byok_model is None
