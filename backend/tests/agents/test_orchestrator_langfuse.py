"""Tests for Langfuse CallbackHandler injection in Orchestrator."""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from contextlib import nullcontext
from typing import Any, cast
from langchain_core.messages import AIMessage, AIMessageChunk, HumanMessage, RemoveMessage

from backend.agent_engine.agents.base import Orchestrator
from backend.agent_engine.agents.config_loader import VersionConfig, ModelConfig
from backend.agent_engine.streaming.domain_events_schema import (
    Finish,
    MessageStart,
    StreamError,
    TextDelta,
    TextEnd,
    TextStart,
)


def _make_config() -> VersionConfig:
    """Create minimal test config."""
    return VersionConfig(
        version="0.1.0",
        name="v1_baseline",
        description="Test version",
        tools=[],
        model=ModelConfig(name="gpt-4o-mini", temperature=0.0),
    )


def _mock_agent_response() -> dict:
    """Standard agent response for tests."""
    return {
        "messages": [
            HumanMessage(content="test"),
            AIMessage(content="Test response"),
        ]
    }


def _create_orchestrator(config: VersionConfig) -> Orchestrator:
    """Create orchestrator with all external deps mocked."""
    with (
        patch("backend.agent_engine.agents.base.get_tools_by_names") as mock_get_tools,
        patch("backend.agent_engine.agents.base.create_agent") as mock_create,
        patch("backend.agent_engine.agents.base.init_chat_model"),
        patch("backend.agent_engine.agents.base.ToolCallLimitMiddleware"),
        patch("backend.agent_engine.agents.base.handle_tool_errors", new=MagicMock()),
    ):
        mock_get_tools.return_value = []
        mock_agent = MagicMock()
        mock_create.return_value = mock_agent
        orch = Orchestrator(config, checkpointer=MagicMock())
        return orch


class TestRunInjectsLangfuseCallback:
    def test_run_injects_langfuse_callback(self):
        config = _make_config()
        orch = _create_orchestrator(config)
        agent = cast(Any, orch.agent)
        agent.invoke.return_value = _mock_agent_response()

        with (
            patch(
                "backend.agent_engine.agents.base.CallbackHandler"
            ) as mock_handler_cls,
            patch(
                "backend.agent_engine.agents.base.propagate_attributes",
                return_value=nullcontext(),
            ) as mock_propagate_attributes,
        ):
            mock_handler = MagicMock()
            mock_handler_cls.return_value = mock_handler

            orch.run("test prompt", request_id="req-abc")

            mock_handler_cls.assert_called_once()
            # trace_name is always set; session_id only when present
            prop_kwargs = mock_propagate_attributes.call_args.kwargs
            assert prop_kwargs["trace_name"] == "v1_baseline_invoke"
            assert "session_id" not in prop_kwargs
            call_args = agent.invoke.call_args
            config_arg = call_args[1].get("config")
            assert config_arg is not None, "agent.invoke was not called with config="
            assert "callbacks" in config_arg
            assert mock_handler in config_arg["callbacks"]

    def test_run_without_session_id(self):
        config = _make_config()
        orch = _create_orchestrator(config)
        agent = cast(Any, orch.agent)
        agent.invoke.return_value = _mock_agent_response()

        with (
            patch(
                "backend.agent_engine.agents.base.CallbackHandler"
            ) as mock_handler_cls,
            patch(
                "backend.agent_engine.agents.base.propagate_attributes",
                return_value=nullcontext(),
            ) as mock_propagate_attributes,
        ):
            mock_handler_cls.return_value = MagicMock()

            result = orch.run("test prompt", request_id="req-abc")

            assert result["response"] == "Test response"
            prop_kwargs = mock_propagate_attributes.call_args.kwargs
            assert prop_kwargs == {"trace_name": "v1_baseline_invoke"}
            call_args = agent.invoke.call_args
            config_arg = call_args[1].get("config")
            assert "callbacks" in config_arg

    def test_run_passes_session_id_via_propagate_attributes(self):
        config = _make_config()
        orch = _create_orchestrator(config)
        agent = cast(Any, orch.agent)
        agent.invoke.return_value = _mock_agent_response()

        with (
            patch(
                "backend.agent_engine.agents.base.CallbackHandler"
            ) as mock_handler_cls,
            patch(
                "backend.agent_engine.agents.base.propagate_attributes",
                return_value=nullcontext(),
            ) as mock_propagate_attributes,
        ):
            mock_handler_cls.return_value = MagicMock()

            orch.run("test prompt", session_id="sess-456", request_id="req-abc")

            prop_kwargs = mock_propagate_attributes.call_args.kwargs
            assert prop_kwargs == {
                "trace_name": "v1_baseline_invoke",
                "session_id": "sess-456",
            }
            call_args = agent.invoke.call_args
            config_arg = call_args[1].get("config")
            assert "callbacks" in config_arg


class TestArunInjectsLangfuseCallback:
    @pytest.mark.asyncio
    async def test_arun_injects_langfuse_callback(self):
        config = _make_config()
        orch = _create_orchestrator(config)
        agent = cast(Any, orch.agent)
        agent.ainvoke = AsyncMock(return_value=_mock_agent_response())

        with (
            patch(
                "backend.agent_engine.agents.base.CallbackHandler"
            ) as mock_handler_cls,
            patch(
                "backend.agent_engine.agents.base.propagate_attributes",
                return_value=nullcontext(),
            ) as mock_propagate_attributes,
        ):
            mock_handler = MagicMock()
            mock_handler_cls.return_value = mock_handler

            await orch.arun("test prompt", request_id="req-abc")

            mock_handler_cls.assert_called_once()
            prop_kwargs = mock_propagate_attributes.call_args.kwargs
            assert prop_kwargs == {"trace_name": "v1_baseline_invoke"}
            call_args = agent.ainvoke.call_args
            config_arg = call_args[1].get("config")
            assert config_arg is not None
            assert "callbacks" in config_arg
            assert mock_handler in config_arg["callbacks"]

    @pytest.mark.asyncio
    async def test_arun_passes_session_id_via_propagate_attributes(self):
        config = _make_config()
        orch = _create_orchestrator(config)
        agent = cast(Any, orch.agent)
        agent.ainvoke = AsyncMock(return_value=_mock_agent_response())

        with (
            patch(
                "backend.agent_engine.agents.base.CallbackHandler"
            ) as mock_handler_cls,
            patch(
                "backend.agent_engine.agents.base.propagate_attributes",
                return_value=nullcontext(),
            ) as mock_propagate_attributes,
        ):
            mock_handler_cls.return_value = MagicMock()

            await orch.arun("test prompt", session_id="sess-123", request_id="req-abc")

            prop_kwargs = mock_propagate_attributes.call_args.kwargs
            assert prop_kwargs == {
                "trace_name": "v1_baseline_invoke",
                "session_id": "sess-123",
            }
            call_args = agent.ainvoke.call_args
            config_arg = call_args[1].get("config")
            assert "callbacks" in config_arg


class TestAstreamRun:
    """Tests for Orchestrator.astream_run() streaming method."""

    @pytest.mark.asyncio
    async def test_happy_path_yields_domain_events(self):
        config = _make_config()
        orch = _create_orchestrator(config)
        agent = cast(Any, orch.agent)

        async def mock_astream(*args, **kwargs):
            # astream with version="v2" returns dicts {"type": ..., "data": ...}
            yield {
                "type": "messages",
                "data": (
                    AIMessageChunk(content="Hello", id="msg-1"),
                    {"langgraph_node": "agent"},
                ),
            }
            yield {
                "type": "messages",
                "data": (
                    AIMessageChunk(content=" world", id="msg-1"),
                    {"langgraph_node": "agent"},
                ),
            }

        agent.astream = mock_astream

        with (
            patch(
                "backend.agent_engine.agents.base.CallbackHandler"
            ) as mock_handler_cls,
            patch(
                "backend.agent_engine.agents.base.propagate_attributes",
                return_value=nullcontext(),
            ),
        ):
            mock_handler_cls.return_value = MagicMock()
            events = []
            async for event in orch.astream_run(
                message="test", session_id="sess-1"
            ):
                events.append(event)

        assert isinstance(events[0], MessageStart)
        assert events[0].session_id == "sess-1"
        assert isinstance(events[1], TextStart)
        assert isinstance(events[2], TextDelta)
        assert events[2].delta == "Hello"
        assert isinstance(events[3], TextDelta)
        assert events[3].delta == " world"
        assert isinstance(events[-2], TextEnd)
        assert isinstance(events[-1], Finish)
        assert events[-1].finish_reason == "stop"

    @pytest.mark.asyncio
    async def test_astream_called_with_thread_id_in_configurable(self):
        config = _make_config()
        orch = _create_orchestrator(config)
        agent = cast(Any, orch.agent)

        captured_kwargs: dict = {}

        async def mock_astream(*args, **kwargs):
            captured_kwargs.update(kwargs)
            return
            yield  # make it an async generator

        agent.astream = mock_astream

        with (
            patch(
                "backend.agent_engine.agents.base.CallbackHandler"
            ) as mock_handler_cls,
            patch(
                "backend.agent_engine.agents.base.propagate_attributes",
                return_value=nullcontext(),
            ),
        ):
            mock_handler_cls.return_value = MagicMock()
            async for _ in orch.astream_run(
                message="test", session_id="sess-42"
            ):
                pass

        config_arg = captured_kwargs.get("config", {})
        assert config_arg["configurable"]["thread_id"] == "sess-42"

    @pytest.mark.asyncio
    async def test_langfuse_callback_injected(self):
        config = _make_config()
        orch = _create_orchestrator(config)
        agent = cast(Any, orch.agent)

        captured_kwargs: dict = {}

        async def mock_astream(*args, **kwargs):
            captured_kwargs.update(kwargs)
            return
            yield

        agent.astream = mock_astream

        with (
            patch(
                "backend.agent_engine.agents.base.CallbackHandler"
            ) as mock_handler_cls,
            patch(
                "backend.agent_engine.agents.base.propagate_attributes",
                return_value=nullcontext(),
            ) as mock_propagate,
        ):
            mock_handler = MagicMock()
            mock_handler_cls.return_value = mock_handler
            async for _ in orch.astream_run(
                message="test", session_id="sess-99"
            ):
                pass

        mock_handler_cls.assert_called_once()
        prop_kwargs = mock_propagate.call_args.kwargs
        assert prop_kwargs == {
            "trace_name": "v1_baseline_stream",
            "session_id": "sess-99",
        }
        config_arg = captured_kwargs.get("config", {})
        assert mock_handler in config_arg["callbacks"]

    @pytest.mark.asyncio
    async def test_regenerate_truncates_state(self):
        config = _make_config()
        orch = _create_orchestrator(config)
        agent = cast(Any, orch.agent)

        state_mock = MagicMock()
        state_mock.values = {
            "messages": [
                HumanMessage(content="Hi", id="human-1"),
                AIMessage(content="Hello!", id="ai-1"),
            ]
        }
        agent.aget_state = AsyncMock(return_value=state_mock)
        agent.aupdate_state = AsyncMock()

        async def mock_astream(*args, **kwargs):
            yield {
                "type": "messages",
                "data": (
                    AIMessageChunk(content="Regenerated", id="msg-2"),
                    {"langgraph_node": "agent"},
                ),
            }

        agent.astream = mock_astream

        with (
            patch(
                "backend.agent_engine.agents.base.CallbackHandler"
            ) as mock_handler_cls,
            patch(
                "backend.agent_engine.agents.base.propagate_attributes",
                return_value=nullcontext(),
            ),
        ):
            mock_handler_cls.return_value = MagicMock()
            events = []
            async for event in orch.astream_run(
                session_id="sess-1",
                trigger="regenerate",
            ):
                events.append(event)

        agent.aget_state.assert_called_once()
        update_call = agent.aupdate_state.call_args
        remove_messages = update_call[0][1]["messages"]
        assert len(remove_messages) == 1
        assert isinstance(remove_messages[0], RemoveMessage)
        assert remove_messages[0].id == "ai-1"
        assert update_call[1].get("as_node") == "__start__"

    @pytest.mark.asyncio
    async def test_regenerate_message_id_mismatch_raises(self):
        config = _make_config()
        orch = _create_orchestrator(config)
        agent = cast(Any, orch.agent)

        state_mock = MagicMock()
        state_mock.values = {
            "messages": [
                HumanMessage(content="Hi", id="human-1"),
                AIMessage(content="Hello!", id="ai-1"),
            ]
        }
        agent.aget_state = AsyncMock(return_value=state_mock)

        with (
            patch(
                "backend.agent_engine.agents.base.CallbackHandler"
            ) as mock_handler_cls,
            patch(
                "backend.agent_engine.agents.base.propagate_attributes",
                return_value=nullcontext(),
            ),
        ):
            mock_handler_cls.return_value = MagicMock()
            events = []
            async for event in orch.astream_run(
                session_id="sess-1",
                trigger="regenerate",
                message_id="wrong-id",
            ):
                events.append(event)

        assert any(isinstance(e, StreamError) for e in events)
        assert any(
            isinstance(e, Finish) and e.finish_reason == "error" for e in events
        )

    @pytest.mark.asyncio
    async def test_exception_yields_stream_error_and_finish(self):
        config = _make_config()
        orch = _create_orchestrator(config)
        agent = cast(Any, orch.agent)

        async def mock_astream(*args, **kwargs):
            raise RuntimeError("connection lost")
            yield  # noqa: RET503

        agent.astream = mock_astream

        with (
            patch(
                "backend.agent_engine.agents.base.CallbackHandler"
            ) as mock_handler_cls,
            patch(
                "backend.agent_engine.agents.base.propagate_attributes",
                return_value=nullcontext(),
            ),
        ):
            mock_handler_cls.return_value = MagicMock()
            events = []
            async for event in orch.astream_run(
                message="test", session_id="sess-err"
            ):
                events.append(event)

        assert len(events) == 2
        assert isinstance(events[0], StreamError)
        assert "connection lost" in events[0].error_text
        assert isinstance(events[1], Finish)
        assert events[1].finish_reason == "error"

    @pytest.mark.asyncio
    async def test_checkpointer_passed_to_create_agent(self):
        config = _make_config()
        mock_checkpointer = MagicMock()

        with (
            patch(
                "backend.agent_engine.agents.base.get_tools_by_names"
            ) as mock_get_tools,
            patch("backend.agent_engine.agents.base.create_agent") as mock_create,
            patch("backend.agent_engine.agents.base.init_chat_model"),
            patch("backend.agent_engine.agents.base.ToolCallLimitMiddleware"),
            patch(
                "backend.agent_engine.agents.base.handle_tool_errors",
                new=MagicMock(),
            ),
        ):
            mock_get_tools.return_value = []
            mock_create.return_value = MagicMock()

            Orchestrator(config, checkpointer=mock_checkpointer)

            call_kwargs = mock_create.call_args[1]
            assert call_kwargs["checkpointer"] is mock_checkpointer

    @pytest.mark.asyncio
    async def test_stream_mode_parameters(self):
        config = _make_config()
        orch = _create_orchestrator(config)
        agent = cast(Any, orch.agent)

        captured_kwargs: dict = {}

        async def mock_astream(*args, **kwargs):
            captured_kwargs.update(kwargs)
            return
            yield

        agent.astream = mock_astream

        with (
            patch(
                "backend.agent_engine.agents.base.CallbackHandler"
            ) as mock_handler_cls,
            patch(
                "backend.agent_engine.agents.base.propagate_attributes",
                return_value=nullcontext(),
            ),
        ):
            mock_handler_cls.return_value = MagicMock()
            async for _ in orch.astream_run(
                message="test", session_id="sess-1"
            ):
                pass

        assert captured_kwargs["stream_mode"] == ["messages", "updates", "custom"]
        assert captured_kwargs.get("version") == "v2"

    @pytest.mark.asyncio
    async def test_astream_called_with_none_input_on_regenerate(self):
        config = _make_config()
        orch = _create_orchestrator(config)
        agent = cast(Any, orch.agent)

        state_mock = MagicMock()
        state_mock.values = {
            "messages": [
                HumanMessage(content="Hi", id="human-1"),
                AIMessage(content="Hello!", id="ai-1"),
            ]
        }
        agent.aget_state = AsyncMock(return_value=state_mock)
        agent.aupdate_state = AsyncMock()

        captured_args: list = []

        async def mock_astream(*args, **kwargs):
            captured_args.extend(args)
            return
            yield

        agent.astream = mock_astream

        with (
            patch(
                "backend.agent_engine.agents.base.CallbackHandler"
            ) as mock_handler_cls,
            patch(
                "backend.agent_engine.agents.base.propagate_attributes",
                return_value=nullcontext(),
            ),
        ):
            mock_handler_cls.return_value = MagicMock()
            async for _ in orch.astream_run(
                session_id="sess-1",
                trigger="regenerate",
            ):
                pass

        assert captured_args[0] is None


class TestLangfuseTraceMetadata:
    """Tests for the trace_name / run_name / metadata wiring on the LangChain config."""

    @pytest.mark.asyncio
    async def test_arun_config_carries_invoke_trace_metadata(self):
        config = _make_config()
        orch = _create_orchestrator(config)
        agent = cast(Any, orch.agent)
        agent.ainvoke = AsyncMock(return_value=_mock_agent_response())

        with (
            patch("backend.agent_engine.agents.base.CallbackHandler"),
            patch(
                "backend.agent_engine.agents.base.propagate_attributes",
                return_value=nullcontext(),
            ),
        ):
            await orch.arun("test", session_id="sess-1", request_id="req-1")

            config_arg = agent.ainvoke.call_args[1]["config"]
            assert config_arg["run_name"] == "chat-turn"
            metadata = config_arg["metadata"]
            assert metadata["langfuse_trace_name"] == "v1_baseline_invoke"
            assert metadata["request_id"] == "req-1"

    @pytest.mark.asyncio
    async def test_astream_config_carries_stream_trace_metadata(self):
        config = _make_config()
        orch = _create_orchestrator(config)
        agent = cast(Any, orch.agent)

        captured_kwargs: dict = {}

        async def mock_astream(*args, **kwargs):
            captured_kwargs.update(kwargs)
            return
            yield

        agent.astream = mock_astream

        with (
            patch("backend.agent_engine.agents.base.CallbackHandler"),
            patch(
                "backend.agent_engine.agents.base.propagate_attributes",
                return_value=nullcontext(),
            ),
        ):
            # submit path (trigger=None): prepare_regenerate is skipped and
            # astream receives the full config. trigger key is omitted from
            # metadata because the value is None.
            async for _ in orch.astream_run(
                message="test",
                session_id="sess-1",
                request_id="req-1",
            ):
                pass

        config_arg = captured_kwargs["config"]
        assert config_arg["run_name"] == "chat-turn"
        metadata = config_arg["metadata"]
        assert metadata["langfuse_trace_name"] == "v1_baseline_stream"
        assert metadata["request_id"] == "req-1"
        assert "trigger" not in metadata

    @pytest.mark.asyncio
    async def test_astream_regenerate_populates_trigger_metadata(self):
        config = _make_config()
        orch = _create_orchestrator(config)
        agent = cast(Any, orch.agent)

        state_mock = MagicMock()
        state_mock.values = {
            "messages": [
                HumanMessage(content="Hi", id="human-1"),
                AIMessage(content="Hello!", id="ai-1"),
            ]
        }
        agent.aget_state = AsyncMock(return_value=state_mock)
        agent.aupdate_state = AsyncMock()

        captured_kwargs: dict = {}

        async def mock_astream(*args, **kwargs):
            captured_kwargs.update(kwargs)
            return
            yield

        agent.astream = mock_astream

        with (
            patch("backend.agent_engine.agents.base.CallbackHandler"),
            patch(
                "backend.agent_engine.agents.base.propagate_attributes",
                return_value=nullcontext(),
            ),
        ):
            async for _ in orch.astream_run(
                session_id="sess-1",
                trigger="regenerate",
                request_id="req-1",
            ):
                pass

        metadata = captured_kwargs["config"]["metadata"]
        assert metadata["trigger"] == "regenerate"

    @pytest.mark.asyncio
    async def test_trace_name_follows_config_version_dynamically(self):
        """Swap in a v2 config — trace_name must track, no code change needed."""
        config = VersionConfig(
            version="0.2.0",
            name="v2_test",
            description="Hypothetical v2",
            tools=[],
            model=ModelConfig(name="gpt-4o-mini", temperature=0.0),
        )
        orch = _create_orchestrator(config)
        agent = cast(Any, orch.agent)
        agent.ainvoke = AsyncMock(return_value=_mock_agent_response())

        with (
            patch("backend.agent_engine.agents.base.CallbackHandler"),
            patch(
                "backend.agent_engine.agents.base.propagate_attributes",
                return_value=nullcontext(),
            ) as mock_propagate,
        ):
            await orch.arun("test", session_id="sess-1", request_id="req-1")

            config_arg = agent.ainvoke.call_args[1]["config"]
            assert (
                config_arg["metadata"]["langfuse_trace_name"] == "v2_test_invoke"
            )
            assert (
                mock_propagate.call_args.kwargs["trace_name"] == "v2_test_invoke"
            )
