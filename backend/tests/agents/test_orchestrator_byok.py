"""Tests for BYOK per-request key wiring on Orchestrator (DEV-189).

Covers the three points where the design lands on the Orchestrator itself:
``context_schema``/middleware registration at construction, and ``api_key``
threading through ``arun``/``astream_run`` into ``BYOKContext``. ``run()``
(the sync eval runner path) is explicitly untouched — see
``TestRunSyncPathUnaffected``.
"""

from contextlib import nullcontext
from typing import Any, cast
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import openai
import pytest
from langchain_core.messages import AIMessage, HumanMessage

from backend.agent_engine.agents.base import (
    BYOKContext,
    ByokModelOverrideMiddleware,
    Orchestrator,
)
from backend.agent_engine.agents.config_loader import ModelConfig, WorkflowProfileConfig
from backend.agent_engine.byok import ByokKeyRejectedError
from backend.agent_engine.streaming.domain_events_schema import Finish, StreamError


def _make_auth_error(message: str = "Incorrect API key provided: sk-proj-***xyz"):
    response = httpx.Response(
        401, request=httpx.Request("POST", "https://api.openai.com/v1/x")
    )
    return openai.AuthenticationError(message, response=response, body=None)


def _make_config() -> WorkflowProfileConfig:
    return WorkflowProfileConfig(
        version="0.1.0",
        name="baseline",
        description="Test version",
        tools=[],
        model=ModelConfig(name="gpt-4o-mini", temperature=0.0),
    )


def _mock_agent_response() -> dict:
    return {
        "messages": [
            HumanMessage(content="test"),
            AIMessage(content="Test response"),
        ]
    }


def _create_orchestrator(
    config: WorkflowProfileConfig,
) -> tuple[Orchestrator, MagicMock]:
    """Create an Orchestrator with all external deps mocked, returning the
    orchestrator plus the ``create_agent`` mock so callers can inspect how
    it was invoked (context_schema, middleware list)."""
    with (
        patch("backend.agent_engine.agents.base.get_tools_by_names") as mock_get_tools,
        patch("backend.agent_engine.agents.base.create_agent") as mock_create,
        patch("backend.agent_engine.agents.base.init_chat_model"),
        patch("backend.agent_engine.agents.base.RunBudgetMiddleware"),
        patch("backend.agent_engine.agents.base.handle_tool_errors", new=MagicMock()),
    ):
        mock_get_tools.return_value = []
        mock_agent = MagicMock()
        mock_create.return_value = mock_agent
        orch = Orchestrator(config, checkpointer=MagicMock())
        return orch, mock_create


class TestOrchestratorConstructionRegistersByok:
    def test_context_schema_is_byok_context(self):
        _orch, mock_create = _create_orchestrator(_make_config())
        assert mock_create.call_args.kwargs["context_schema"] is BYOKContext

    def test_middleware_list_includes_byok_override(self):
        _orch, mock_create = _create_orchestrator(_make_config())
        middleware = mock_create.call_args.kwargs["middleware"]
        assert any(isinstance(m, ByokModelOverrideMiddleware) for m in middleware)


class TestArunApiKeyWiring:
    @pytest.mark.asyncio
    async def test_no_api_key_passes_context_with_none_byok_model(self):
        orch, _ = _create_orchestrator(_make_config())
        agent = cast(Any, orch.agent)
        agent.ainvoke = AsyncMock(return_value=_mock_agent_response())

        with (
            patch("backend.agent_engine.agents.base.CallbackHandler"),
            patch(
                "backend.agent_engine.agents.base.propagate_attributes",
                return_value=nullcontext(),
            ),
        ):
            await orch.arun("test prompt", request_id="req-1")

        context_arg = agent.ainvoke.call_args.kwargs["context"]
        assert context_arg == BYOKContext(byok_model=None)

    @pytest.mark.asyncio
    async def test_api_key_builds_byok_model_via_init_model_and_passes_via_context(
        self,
    ):
        orch, _ = _create_orchestrator(_make_config())
        agent = cast(Any, orch.agent)
        agent.ainvoke = AsyncMock(return_value=_mock_agent_response())

        with (
            patch("backend.agent_engine.agents.base.CallbackHandler"),
            patch(
                "backend.agent_engine.agents.base.propagate_attributes",
                return_value=nullcontext(),
            ),
            patch(
                "backend.agent_engine.agents.base._init_model",
                side_effect=lambda cfg, api_key=None: f"model-for-{api_key}",
            ) as mock_init_model,
        ):
            await orch.arun(
                "test prompt", request_id="req-1", api_key="sk-proj-user-key"
            )

        mock_init_model.assert_called_once_with(
            orch.config.model, api_key="sk-proj-user-key"
        )
        context_arg = agent.ainvoke.call_args.kwargs["context"]
        assert context_arg.byok_model == "model-for-sk-proj-user-key"


class TestAstreamRunApiKeyWiring:
    @pytest.mark.asyncio
    async def test_no_api_key_passes_context_with_none_byok_model(self):
        orch, _ = _create_orchestrator(_make_config())
        agent = cast(Any, orch.agent)
        captured_kwargs: dict = {}

        async def mock_astream(*args, **kwargs):
            captured_kwargs.update(kwargs)
            return
            yield  # pragma: no cover - makes this an async generator

        agent.astream = mock_astream

        with (
            patch("backend.agent_engine.agents.base.CallbackHandler"),
            patch(
                "backend.agent_engine.agents.base.propagate_attributes",
                return_value=nullcontext(),
            ),
        ):
            async for _ in orch.astream_run(message="test", session_id="sess-1"):
                pass

        assert captured_kwargs["context"] == BYOKContext(byok_model=None)

    @pytest.mark.asyncio
    async def test_api_key_builds_byok_model_via_init_model_and_passes_via_context(
        self,
    ):
        orch, _ = _create_orchestrator(_make_config())
        agent = cast(Any, orch.agent)
        captured_kwargs: dict = {}

        async def mock_astream(*args, **kwargs):
            captured_kwargs.update(kwargs)
            return
            yield  # pragma: no cover - makes this an async generator

        agent.astream = mock_astream

        with (
            patch("backend.agent_engine.agents.base.CallbackHandler"),
            patch(
                "backend.agent_engine.agents.base.propagate_attributes",
                return_value=nullcontext(),
            ),
            patch(
                "backend.agent_engine.agents.base._init_model",
                side_effect=lambda cfg, api_key=None: f"model-for-{api_key}",
            ) as mock_init_model,
        ):
            async for _ in orch.astream_run(
                message="test", session_id="sess-1", api_key="sk-proj-user-key"
            ):
                pass

        mock_init_model.assert_called_once_with(
            orch.config.model, api_key="sk-proj-user-key"
        )
        assert captured_kwargs["context"].byok_model == "model-for-sk-proj-user-key"


class TestApiKeyNeverReachesLangfuseConfig:
    """The AC "user key never appears in ... trace (Langfuse)" is only
    fully provable against a real Langfuse project (spec's Testing
    Decisions scope that to manual verification) — but the structural half
    is testable here: ``context`` (carrying the BYOK model) and ``config``
    (what ``CallbackHandler`` actually reads for trace metadata) are two
    separate kwargs built by separate code paths, so the key can't leak
    into the metadata dict Langfuse sees."""

    @pytest.mark.asyncio
    async def test_arun_config_dict_contains_no_trace_of_the_api_key(self):
        orch, _ = _create_orchestrator(_make_config())
        agent = cast(Any, orch.agent)
        agent.ainvoke = AsyncMock(return_value=_mock_agent_response())

        with (
            patch("backend.agent_engine.agents.base.CallbackHandler"),
            patch(
                "backend.agent_engine.agents.base.propagate_attributes",
                return_value=nullcontext(),
            ),
        ):
            await orch.arun(
                "test prompt", request_id="req-1", api_key="sk-proj-must-not-leak"
            )

        config_arg = agent.ainvoke.call_args.kwargs["config"]
        assert "sk-proj-must-not-leak" not in str(config_arg)

    @pytest.mark.asyncio
    async def test_astream_config_dict_contains_no_trace_of_the_api_key(self):
        orch, _ = _create_orchestrator(_make_config())
        agent = cast(Any, orch.agent)
        captured_kwargs: dict = {}

        async def mock_astream(*args, **kwargs):
            captured_kwargs.update(kwargs)
            return
            yield  # pragma: no cover - makes this an async generator

        agent.astream = mock_astream

        with (
            patch("backend.agent_engine.agents.base.CallbackHandler"),
            patch(
                "backend.agent_engine.agents.base.propagate_attributes",
                return_value=nullcontext(),
            ),
        ):
            async for _ in orch.astream_run(
                message="test",
                session_id="sess-1",
                api_key="sk-proj-must-not-leak",
            ):
                pass

        assert "sk-proj-must-not-leak" not in str(captured_kwargs["config"])


class TestAstreamRunProviderAuthRejection:
    """When the provider rejects a BYOK key mid-run, the stream must
    surface a clean, actionable ``StreamError`` — never the provider's raw
    message, which can contain a key fragment (e.g. "Incorrect API key
    provided: sk-proj-***xyz")."""

    @pytest.mark.asyncio
    async def test_byok_auth_error_yields_clean_stream_error_not_provider_text(self):
        orch, _ = _create_orchestrator(_make_config())
        agent = cast(Any, orch.agent)

        async def mock_astream(*args, **kwargs):
            raise _make_auth_error()
            yield  # pragma: no cover - makes this an async generator

        agent.astream = mock_astream

        events = []
        with (
            patch("backend.agent_engine.agents.base.CallbackHandler"),
            patch(
                "backend.agent_engine.agents.base.propagate_attributes",
                return_value=nullcontext(),
            ),
            patch(
                "backend.agent_engine.agents.base._init_model",
                return_value="byok-model",
            ),
        ):
            async for event in orch.astream_run(
                message="test", session_id="sess-1", api_key="sk-proj-user-key"
            ):
                events.append(event)

        stream_errors = [e for e in events if isinstance(e, StreamError)]
        assert len(stream_errors) == 1
        assert "sk-proj" not in stream_errors[0].error_text
        assert isinstance(events[-1], Finish)
        assert events[-1].finish_reason == "error"

    @pytest.mark.asyncio
    async def test_server_key_auth_error_uses_generic_sanitized_message(self):
        """Not a BYOK request (no api_key) — must NOT get the BYOK-specific
        copy; server-key auth failures are an operator problem, not a
        signal to tell the free-tier user their key is invalid."""
        orch, _ = _create_orchestrator(_make_config())
        agent = cast(Any, orch.agent)

        async def mock_astream(*args, **kwargs):
            raise _make_auth_error("Incorrect API key provided")
            yield  # pragma: no cover - makes this an async generator

        agent.astream = mock_astream

        events = []
        with (
            patch("backend.agent_engine.agents.base.CallbackHandler"),
            patch(
                "backend.agent_engine.agents.base.propagate_attributes",
                return_value=nullcontext(),
            ),
        ):
            async for event in orch.astream_run(message="test", session_id="sess-1"):
                events.append(event)

        stream_errors = [e for e in events if isinstance(e, StreamError)]
        assert len(stream_errors) == 1
        # Redaction of provider key fragments is tool_error_sanitizer's own
        # concern (see its dedicated tests) — what THIS test guards is that
        # the BYOK-specific "check Settings" copy is not shown to a
        # free-tier user whose server key happens to be the one rejected.
        assert "Settings" not in stream_errors[0].error_text


class TestArunProviderAuthRejection:
    """Mirrors ``TestAstreamRunProviderAuthRejection`` for the blocking
    path: ``arun`` reclassifies a BYOK-request auth rejection into
    ``ByokKeyRejectedError`` — a domain exception ``chat_invoke.py``
    catches without needing to know about ``openai.AuthenticationError``
    itself. A server-key rejection is left completely unchanged."""

    @pytest.mark.asyncio
    async def test_byok_auth_error_is_reraised_as_byok_key_rejected_error(self):
        orch, _ = _create_orchestrator(_make_config())
        agent = cast(Any, orch.agent)
        agent.ainvoke = AsyncMock(side_effect=_make_auth_error())

        with (
            patch("backend.agent_engine.agents.base.CallbackHandler"),
            patch(
                "backend.agent_engine.agents.base.propagate_attributes",
                return_value=nullcontext(),
            ),
            patch(
                "backend.agent_engine.agents.base._init_model",
                return_value="byok-model",
            ),
        ):
            with pytest.raises(ByokKeyRejectedError):
                await orch.arun(
                    "test prompt", request_id="req-1", api_key="sk-proj-user-key"
                )

    @pytest.mark.asyncio
    async def test_server_key_auth_error_propagates_unchanged(self):
        orch, _ = _create_orchestrator(_make_config())
        agent = cast(Any, orch.agent)
        original_error = _make_auth_error("Incorrect API key provided")
        agent.ainvoke = AsyncMock(side_effect=original_error)

        with (
            patch("backend.agent_engine.agents.base.CallbackHandler"),
            patch(
                "backend.agent_engine.agents.base.propagate_attributes",
                return_value=nullcontext(),
            ),
        ):
            with pytest.raises(openai.AuthenticationError) as exc_info:
                await orch.arun("test prompt", request_id="req-1")

        assert exc_info.value is original_error


class TestRunSyncPathUnaffected:
    """``run()`` is the eval runner's sync path — deliberately not touched
    by BYOK. It must not pass ``context=`` at all — the BYOK context
    schema is registered on the agent, but omitting ``context=`` leaves
    ``runtime.context`` as plain ``None`` (verified against the real
    LangChain runtime, not just this mock), which is exactly what makes
    this path behave identically to before BYOK existed."""

    def test_run_does_not_pass_context_kwarg(self):
        orch, _ = _create_orchestrator(_make_config())
        agent = cast(Any, orch.agent)
        agent.invoke.return_value = _mock_agent_response()

        with (
            patch("backend.agent_engine.agents.base.CallbackHandler"),
            patch(
                "backend.agent_engine.agents.base.propagate_attributes",
                return_value=nullcontext(),
            ),
        ):
            orch.run("test prompt")

        assert "context" not in agent.invoke.call_args.kwargs
