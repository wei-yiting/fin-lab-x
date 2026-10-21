"""Tests for eval task functions.

Verifies that run_profile uses the async streaming path (astream_run) and
correctly collects domain events into OrchestratorResult.
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from backend.agent_engine.streaming.domain_events_schema import (
    Finish,
    MessageStart,
    TextDelta,
    TextEnd,
    TextStart,
    ToolCall,
    ToolError,
    ToolResult,
    Usage,
)


def _mock_astream_events(
    *,
    text: str = "Test response",
    tool_name: str | None = None,
    tool_result: str | None = None,
) -> list:
    """Build a list of domain events for mocking astream_run."""
    events: list = [
        MessageStart(message_id="msg-1", session_id="sess-1"),
        TextStart(text_id="t-1"),
    ]
    for char in text:
        events.append(TextDelta(text_id="t-1", delta=char))
    events.append(TextEnd(text_id="t-1"))

    if tool_name and tool_result:
        events.extend(
            [
                ToolCall(tool_call_id="tc-1", tool_name=tool_name, args={}),
                ToolResult(tool_call_id="tc-1", result=tool_result),
            ]
        )

    events.append(
        Finish(finish_reason="stop", usage=Usage(input_tokens=10, output_tokens=20))
    )
    return events


async def _async_gen(events: list):
    for e in events:
        yield e


@patch("backend.evals.eval_tasks._get_orchestrator")
def test_run_profile_string_input_calls_astream_run(mock_get_orch: MagicMock) -> None:
    mock_orchestrator = MagicMock()
    mock_orchestrator.config.model.name = "gpt-4o-mini"
    mock_orchestrator.config.version = "baseline"
    mock_orchestrator.astream_run = MagicMock(
        return_value=_async_gen(_mock_astream_events())
    )
    mock_get_orch.return_value = mock_orchestrator

    from backend.evals.eval_tasks import run_profile

    result = asyncio.run(run_profile("微軟最近有什麼新聞？"))

    mock_get_orch.assert_called_once_with("baseline")
    mock_orchestrator.astream_run.assert_called_once()
    call_kwargs = mock_orchestrator.astream_run.call_args[1]
    assert call_kwargs["message"] == "微軟最近有什麼新聞？"
    assert result["response"] == "Test response"


@patch("backend.evals.eval_tasks._get_orchestrator")
def test_run_profile_explicit_profile_selects_orchestrator(
    mock_get_orch: MagicMock,
) -> None:
    mock_orchestrator = MagicMock()
    mock_orchestrator.config.model.name = "gpt-4o-mini"
    mock_orchestrator.config.version = "candidate"
    mock_orchestrator.astream_run = MagicMock(
        return_value=_async_gen(_mock_astream_events())
    )
    mock_get_orch.return_value = mock_orchestrator

    from backend.evals.eval_tasks import run_profile

    asyncio.run(run_profile("test query", profile="candidate"))

    mock_get_orch.assert_called_once_with("candidate")


@patch("backend.evals.eval_tasks._get_orchestrator")
def test_run_profile_dict_input_extracts_prompt(mock_get_orch: MagicMock) -> None:
    mock_orchestrator = MagicMock()
    mock_orchestrator.config.model.name = "gpt-4o-mini"
    mock_orchestrator.config.version = "baseline"
    mock_orchestrator.astream_run = MagicMock(
        return_value=_async_gen(_mock_astream_events())
    )
    mock_get_orch.return_value = mock_orchestrator

    from backend.evals.eval_tasks import run_profile

    result = asyncio.run(run_profile({"prompt": "test query"}))

    call_kwargs = mock_orchestrator.astream_run.call_args[1]
    assert call_kwargs["message"] == "test query"
    assert result["response"] == "Test response"


@patch("backend.evals.eval_tasks._get_orchestrator")
def test_run_profile_collects_tool_outputs(mock_get_orch: MagicMock) -> None:
    events = _mock_astream_events(
        text="蘋果公司最新財報表現良好",
        tool_name="tavily_financial_search",
        tool_result="Earnings beat expectations...",
    )
    mock_orchestrator = MagicMock()
    mock_orchestrator.config.model.name = "gpt-4o"
    mock_orchestrator.config.version = "baseline"
    mock_orchestrator.astream_run = MagicMock(return_value=_async_gen(events))
    mock_get_orch.return_value = mock_orchestrator

    from backend.evals.eval_tasks import run_profile

    result = asyncio.run(run_profile("蘋果公司最新的財報表現如何？"))

    assert result["response"] == "蘋果公司最新財報表現良好"
    assert len(result["tool_outputs"]) == 1
    assert result["tool_outputs"][0]["tool"] == "tavily_financial_search"
    assert "result" in result["tool_outputs"][0]
    assert result["tool_outputs"][0]["result"] == "Earnings beat expectations..."
    assert result["model"] == "gpt-4o"
    assert result["version"] == "baseline"


@patch("backend.evals.eval_tasks._get_orchestrator")
def test_run_profile_scalar_input_converted_to_string(mock_get_orch: MagicMock) -> None:
    mock_orchestrator = MagicMock()
    mock_orchestrator.config.model.name = "gpt-4o-mini"
    mock_orchestrator.config.version = "baseline"
    mock_orchestrator.astream_run = MagicMock(
        return_value=_async_gen(_mock_astream_events())
    )
    mock_get_orch.return_value = mock_orchestrator

    from backend.evals.eval_tasks import run_profile

    asyncio.run(run_profile(42))

    call_kwargs = mock_orchestrator.astream_run.call_args[1]
    assert call_kwargs["message"] == "42"


@patch("backend.evals.eval_tasks._get_orchestrator")
def test_run_profile_float_input_converted_to_string(mock_get_orch: MagicMock) -> None:
    mock_orchestrator = MagicMock()
    mock_orchestrator.config.model.name = "gpt-4o-mini"
    mock_orchestrator.config.version = "baseline"
    mock_orchestrator.astream_run = MagicMock(
        return_value=_async_gen(_mock_astream_events())
    )
    mock_get_orch.return_value = mock_orchestrator

    from backend.evals.eval_tasks import run_profile

    asyncio.run(run_profile(3.14))

    call_kwargs = mock_orchestrator.astream_run.call_args[1]
    assert call_kwargs["message"] == "3.14"


@patch("backend.evals.eval_tasks._get_orchestrator")
def test_run_profile_list_input_converted_to_string(mock_get_orch: MagicMock) -> None:
    mock_orchestrator = MagicMock()
    mock_orchestrator.config.model.name = "gpt-4o-mini"
    mock_orchestrator.config.version = "baseline"
    mock_orchestrator.astream_run = MagicMock(
        return_value=_async_gen(_mock_astream_events())
    )
    mock_get_orch.return_value = mock_orchestrator

    from backend.evals.eval_tasks import run_profile

    asyncio.run(run_profile(["a", "b"]))

    call_kwargs = mock_orchestrator.astream_run.call_args[1]
    assert call_kwargs["message"] == "['a', 'b']"


@patch("backend.evals.eval_tasks._get_orchestrator")
def test_astream_collect_records_tool_errors_in_tool_outputs(
    mock_get_orch: MagicMock,
) -> None:
    events = [
        MessageStart(message_id="msg-1", session_id="sess-1"),
        ToolCall(
            tool_call_id="tc-1",
            tool_name="tavily_financial_search",
            args={"query": "UNH news"},
        ),
        ToolError(tool_call_id="tc-1", error="timeout"),
        Finish(finish_reason="stop", usage=Usage(input_tokens=1, output_tokens=1)),
    ]
    mock_orchestrator = MagicMock()
    mock_orchestrator.config.model.name = "gpt-4o-mini"
    mock_orchestrator.config.version = "baseline"
    mock_orchestrator.astream_run = MagicMock(return_value=_async_gen(events))
    mock_get_orch.return_value = mock_orchestrator

    from backend.evals.eval_tasks import run_baseline_behavior_diagnostic

    result = asyncio.run(
        run_baseline_behavior_diagnostic({"question": "What happened with UNH?"})
    )

    assert result["tool_outputs"] == [
        {
            "tool": "tavily_financial_search",
            "args": {"query": "UNH news"},
            "error": "timeout",
        }
    ]


@patch("backend.evals.eval_tasks._get_orchestrator")
def test_run_baseline_behavior_diagnostic_extracts_question_field(
    mock_get_orch: MagicMock,
) -> None:
    mock_orchestrator = MagicMock()
    mock_orchestrator.config.model.name = "gpt-4o-mini"
    mock_orchestrator.config.version = "baseline"
    mock_orchestrator.astream_run = MagicMock(
        return_value=_async_gen(_mock_astream_events())
    )
    mock_get_orch.return_value = mock_orchestrator

    from backend.evals.eval_tasks import run_baseline_behavior_diagnostic

    asyncio.run(
        run_baseline_behavior_diagnostic(
            {"question": "What's going on with Disney lately?"}
        )
    )

    call_kwargs = mock_orchestrator.astream_run.call_args[1]
    assert call_kwargs["message"] == "What's going on with Disney lately?"


@patch("backend.evals.eval_tasks._get_orchestrator")
def test_run_baseline_behavior_diagnostic_forwards_session_and_trace_metadata(
    mock_get_orch: MagicMock,
) -> None:
    mock_orchestrator = MagicMock()
    mock_orchestrator.config.model.name = "gpt-4o-mini"
    mock_orchestrator.config.version = "baseline"
    mock_orchestrator.astream_run = MagicMock(
        return_value=_async_gen(_mock_astream_events())
    )
    mock_get_orch.return_value = mock_orchestrator

    from backend.evals.eval_tasks import run_baseline_behavior_diagnostic

    asyncio.run(
        run_baseline_behavior_diagnostic(
            {
                "question": "What's going on with AMD lately?",
                "session_id": "baseline_behavior_diagnostic::baseline::17",
                "trace_metadata": {
                    "row_id": "17",
                    "reference_expected_behavior": "may_pass_with_tuning",
                },
            }
        )
    )

    call_kwargs = mock_orchestrator.astream_run.call_args[1]
    assert call_kwargs["message"] == "What's going on with AMD lately?"
    assert call_kwargs["session_id"] == "baseline_behavior_diagnostic::baseline::17"
    assert call_kwargs["trace_metadata"] == {
        "row_id": "17",
        "reference_expected_behavior": "may_pass_with_tuning",
    }


def test_astream_collect_uses_default_session_id_when_none_provided() -> None:
    mock_orchestrator = MagicMock()
    mock_orchestrator.config.model.name = "gpt-4o-mini"
    mock_orchestrator.config.version = "baseline"
    mock_orchestrator.astream_run = MagicMock(
        return_value=_async_gen(_mock_astream_events())
    )

    from backend.evals.eval_tasks import _astream_collect

    asyncio.run(
        _astream_collect(
            mock_orchestrator,
            "What's going on with NVDA lately?",
            session_id="sess-123",
            trace_metadata=None,
        )
    )

    assert mock_orchestrator.astream_run.call_args.kwargs == {
        "message": "What's going on with NVDA lately?",
        "session_id": "sess-123",
    }


@patch("backend.evals.eval_tasks._get_orchestrator")
def test_run_baseline_behavior_diagnostic_forwards_trace_metadata_and_session_id(
    mock_get_orch: MagicMock,
) -> None:
    mock_orchestrator = MagicMock()
    mock_get_orch.return_value = mock_orchestrator

    from backend.evals.eval_tasks import run_baseline_behavior_diagnostic

    expected_result = {
        "response": "ok",
        "tool_outputs": [],
        "model": "gpt-4o-mini",
        "version": "baseline",
    }

    with patch(
        "backend.evals.eval_tasks._astream_collect",
        new=AsyncMock(return_value=expected_result),
    ) as mock_collect:
        result = asyncio.run(
            run_baseline_behavior_diagnostic(
                {
                    "question": "What happened with UNH?",
                    "session_id": "baseline_behavior_diagnostic::baseline::1",
                    "trace_metadata": {"reference_best_source": "mixed"},
                }
            )
        )

    mock_get_orch.assert_called_once_with("baseline")
    mock_collect.assert_awaited_once_with(
        mock_orchestrator,
        "What happened with UNH?",
        session_id="baseline_behavior_diagnostic::baseline::1",
        trace_metadata={"reference_best_source": "mixed"},
    )
    assert result == expected_result


def test_astream_collect_omits_trace_metadata_when_none() -> None:
    mock_orchestrator = MagicMock()
    mock_orchestrator.config.model.name = "gpt-4o-mini"
    mock_orchestrator.config.version = "baseline"
    mock_orchestrator.astream_run = MagicMock(
        return_value=_async_gen(_mock_astream_events())
    )

    from backend.evals.eval_tasks import _astream_collect

    with patch("backend.evals.eval_tasks.uuid.uuid4", return_value="fixed-uuid"):
        asyncio.run(_astream_collect(mock_orchestrator, "hello"))

    mock_orchestrator.astream_run.assert_called_once_with(
        message="hello",
        session_id="eval-fixed-uuid",
    )


def test_astream_collect_forwards_explicit_session_id_and_trace_metadata() -> None:
    mock_orchestrator = MagicMock()
    mock_orchestrator.config.model.name = "gpt-4o-mini"
    mock_orchestrator.config.version = "baseline"
    mock_orchestrator.astream_run = MagicMock(
        return_value=_async_gen(_mock_astream_events())
    )

    from backend.evals.eval_tasks import _astream_collect

    asyncio.run(
        _astream_collect(
            mock_orchestrator,
            "hello",
            session_id="baseline_behavior_diagnostic::baseline::1",
            trace_metadata={"reference_best_source": "mixed"},
        )
    )

    mock_orchestrator.astream_run.assert_called_once_with(
        message="hello",
        session_id="baseline_behavior_diagnostic::baseline::1",
        trace_metadata={"reference_best_source": "mixed"},
    )


def test_astream_collect_sets_finished_normally_on_normal_finish() -> None:
    mock_orchestrator = MagicMock()
    mock_orchestrator.config.model.name = "gpt-4o-mini"
    mock_orchestrator.config.version = "baseline"
    mock_orchestrator.astream_run = MagicMock(
        return_value=_async_gen(_mock_astream_events())
    )

    from backend.evals.eval_tasks import _astream_collect

    result = asyncio.run(_astream_collect(mock_orchestrator, "hello"))

    assert result["finished_normally"] is True


def test_astream_collect_finished_normally_false_without_finish_event() -> None:
    """A stream that dies before emitting Finish must not count as complete."""
    events = [
        MessageStart(message_id="msg-1", session_id="sess-1"),
        TextStart(text_id="t-1"),
        TextDelta(text_id="t-1", delta="partial text"),
    ]
    mock_orchestrator = MagicMock()
    mock_orchestrator.config.model.name = "gpt-4o-mini"
    mock_orchestrator.config.version = "baseline"
    mock_orchestrator.astream_run = MagicMock(return_value=_async_gen(events))

    from backend.evals.eval_tasks import _astream_collect

    result = asyncio.run(_astream_collect(mock_orchestrator, "hello"))

    assert result["response"] == "partial text"
    assert result.get("finished_normally") is False


@patch("backend.evals.eval_tasks._get_orchestrator")
def test_run_baseline_behavior_diagnostic_defaults_to_baseline_profile(
    mock_get_orch: MagicMock,
) -> None:
    mock_orchestrator = MagicMock()
    mock_orchestrator.config.model.name = "gpt-4o-mini"
    mock_orchestrator.config.version = "baseline"
    mock_orchestrator.astream_run = MagicMock(
        return_value=_async_gen(_mock_astream_events())
    )
    mock_get_orch.return_value = mock_orchestrator

    from backend.evals.eval_tasks import run_baseline_behavior_diagnostic

    asyncio.run(run_baseline_behavior_diagnostic({"question": "q"}))

    mock_get_orch.assert_called_once_with("baseline")


@patch("backend.evals.eval_tasks._get_orchestrator")
def test_run_baseline_behavior_diagnostic_explicit_profile_selects_orchestrator(
    mock_get_orch: MagicMock,
) -> None:
    mock_orchestrator = MagicMock()
    mock_orchestrator.config.model.name = "gpt-5.6-luna"
    mock_orchestrator.config.version = "0.2.0"
    mock_orchestrator.astream_run = MagicMock(
        return_value=_async_gen(_mock_astream_events())
    )
    mock_get_orch.return_value = mock_orchestrator

    from backend.evals.eval_tasks import run_baseline_behavior_diagnostic

    asyncio.run(run_baseline_behavior_diagnostic({"question": "q"}, profile="reader"))

    mock_get_orch.assert_called_once_with("reader")


def test_run_baseline_behavior_diagnostic_accepts_profile_injection() -> None:
    from backend.evals.eval_runner import _accepts_profile
    from backend.evals.eval_tasks import run_baseline_behavior_diagnostic

    assert _accepts_profile(run_baseline_behavior_diagnostic)


@patch("backend.evals.eval_tasks._get_orchestrator")
@patch("backend.evals.eval_tasks._get_orchestrator_from_dir")
def test_run_baseline_behavior_diagnostic_config_dir_selects_dir_orchestrator(
    mock_get_dir_orch: MagicMock,
    mock_get_orch: MagicMock,
    tmp_path,
) -> None:
    mock_orchestrator = MagicMock()
    mock_orchestrator.config.model.name = "openai:gpt-5.6-luna"
    mock_orchestrator.config.version = "0.1.0"
    mock_orchestrator.astream_run = MagicMock(
        return_value=_async_gen(_mock_astream_events())
    )
    mock_get_dir_orch.return_value = mock_orchestrator
    config_dir = tmp_path / "luna_medium"
    prompt_path = tmp_path / "system_prompt.md"

    from backend.evals.eval_tasks import run_baseline_behavior_diagnostic

    asyncio.run(
        run_baseline_behavior_diagnostic(
            {"question": "q"}, config_dir=config_dir, prompt_path=prompt_path
        )
    )

    mock_get_dir_orch.assert_called_once_with(config_dir, prompt_path)
    mock_get_orch.assert_not_called()


def test_run_baseline_behavior_diagnostic_rejects_profile_with_config_dir(
    tmp_path,
) -> None:
    from backend.evals.eval_tasks import run_baseline_behavior_diagnostic

    with pytest.raises(ValueError, match="profile"):
        asyncio.run(
            run_baseline_behavior_diagnostic(
                {"question": "q"}, profile="reader", config_dir=tmp_path
            )
        )


def test_run_baseline_behavior_diagnostic_rejects_prompt_path_without_config_dir(
    tmp_path,
) -> None:
    from backend.evals.eval_tasks import run_baseline_behavior_diagnostic

    with pytest.raises(ValueError, match="prompt_path"):
        asyncio.run(
            run_baseline_behavior_diagnostic(
                {"question": "q"}, prompt_path=tmp_path / "system_prompt.md"
            )
        )


@patch("backend.evals.eval_tasks.Orchestrator")
def test_get_orchestrator_from_dir_injects_given_prompt(
    mock_orchestrator_cls: MagicMock, tmp_path
) -> None:
    config_dir = tmp_path / "arm"
    config_dir.mkdir()
    (config_dir / "orchestrator_config.yaml").write_text(
        'version: "0.1.0"\nname: "arm"\ndescription: "d"\n'
        'model:\n  name: "openai:gpt-5.6-luna"\n  reasoning: "on"\n'
        '  reasoning_effort: "medium"\n'
    )
    prompt_path = tmp_path / "system_prompt.md"
    prompt_path.write_text("You are the arm prompt.\n")

    from backend.evals.eval_tasks import _get_orchestrator_from_dir

    _get_orchestrator_from_dir.cache_clear()
    _get_orchestrator_from_dir(config_dir, prompt_path)

    config = mock_orchestrator_cls.call_args[0][0]
    assert config.name == "arm"
    assert config.system_prompt == "You are the arm prompt."
    assert config.model.reasoning_effort == "medium"


def test_astream_collect_records_timing_and_usage() -> None:
    events = [
        MessageStart(message_id="msg-1", session_id="sess-1"),
        ToolCall(tool_call_id="tc-1", tool_name="finnhub_stock_quote", args={}),
        ToolResult(tool_call_id="tc-1", result="{}"),
        TextStart(text_id="t-1"),
        TextDelta(text_id="t-1", delta="hi"),
        TextEnd(text_id="t-1"),
        Finish(finish_reason="stop", usage=Usage(input_tokens=11, output_tokens=7)),
    ]
    mock_orchestrator = MagicMock()
    mock_orchestrator.config.model.name = "gpt-4o-mini"
    mock_orchestrator.config.version = "baseline"
    mock_orchestrator.astream_run = MagicMock(return_value=_async_gen(events))

    from backend.evals.eval_tasks import _astream_collect

    result = asyncio.run(_astream_collect(mock_orchestrator, "hello"))

    timing = result["timing"]
    assert timing["first_event_s"] is not None
    assert timing["first_text_s"] is not None
    assert 0 <= timing["first_event_s"] <= timing["first_text_s"] <= timing["total_s"]
    assert result["usage"] == {"input_tokens": 11, "output_tokens": 7}


def test_astream_collect_timing_without_visible_events() -> None:
    events = [
        MessageStart(message_id="msg-1", session_id="sess-1"),
        Finish(finish_reason="stop"),
    ]
    mock_orchestrator = MagicMock()
    mock_orchestrator.config.model.name = "gpt-4o-mini"
    mock_orchestrator.config.version = "baseline"
    mock_orchestrator.astream_run = MagicMock(return_value=_async_gen(events))

    from backend.evals.eval_tasks import _astream_collect

    result = asyncio.run(_astream_collect(mock_orchestrator, "hello"))

    assert result["timing"]["first_event_s"] is None
    assert result["timing"]["first_text_s"] is None
    assert result["timing"]["total_s"] >= 0
