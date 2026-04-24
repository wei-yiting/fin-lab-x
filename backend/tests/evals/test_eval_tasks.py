"""Tests for eval task functions.

Verifies that run_v1 uses the async streaming path (astream_run) and
correctly collects domain events into OrchestratorResult.
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

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
def test_run_v1_string_input_calls_astream_run(mock_get_orch: MagicMock) -> None:
    mock_orchestrator = MagicMock()
    mock_orchestrator.config.model.name = "gpt-4o-mini"
    mock_orchestrator.config.version = "v1_baseline"
    mock_orchestrator.astream_run = MagicMock(
        return_value=_async_gen(_mock_astream_events())
    )
    mock_get_orch.return_value = mock_orchestrator

    from backend.evals.eval_tasks import run_v1

    result = asyncio.run(run_v1("微軟最近有什麼新聞？"))

    mock_get_orch.assert_called_once_with("v1_baseline")
    mock_orchestrator.astream_run.assert_called_once()
    call_kwargs = mock_orchestrator.astream_run.call_args[1]
    assert call_kwargs["message"] == "微軟最近有什麼新聞？"
    assert result["response"] == "Test response"


@patch("backend.evals.eval_tasks._get_orchestrator")
def test_run_v1_dict_input_extracts_prompt(mock_get_orch: MagicMock) -> None:
    mock_orchestrator = MagicMock()
    mock_orchestrator.config.model.name = "gpt-4o-mini"
    mock_orchestrator.config.version = "v1_baseline"
    mock_orchestrator.astream_run = MagicMock(
        return_value=_async_gen(_mock_astream_events())
    )
    mock_get_orch.return_value = mock_orchestrator

    from backend.evals.eval_tasks import run_v1

    result = asyncio.run(run_v1({"prompt": "test query"}))

    call_kwargs = mock_orchestrator.astream_run.call_args[1]
    assert call_kwargs["message"] == "test query"
    assert result["response"] == "Test response"


@patch("backend.evals.eval_tasks._get_orchestrator")
def test_run_v1_collects_tool_outputs(mock_get_orch: MagicMock) -> None:
    events = _mock_astream_events(
        text="蘋果公司最新財報表現良好",
        tool_name="tavily_financial_search",
        tool_result="Earnings beat expectations...",
    )
    mock_orchestrator = MagicMock()
    mock_orchestrator.config.model.name = "gpt-4o"
    mock_orchestrator.config.version = "v1_baseline"
    mock_orchestrator.astream_run = MagicMock(return_value=_async_gen(events))
    mock_get_orch.return_value = mock_orchestrator

    from backend.evals.eval_tasks import run_v1

    result = asyncio.run(run_v1("蘋果公司最新的財報表現如何？"))

    assert result["response"] == "蘋果公司最新財報表現良好"
    assert len(result["tool_outputs"]) == 1
    assert result["tool_outputs"][0]["tool"] == "tavily_financial_search"
    assert "result" in result["tool_outputs"][0]
    assert result["tool_outputs"][0]["result"] == "Earnings beat expectations..."
    assert result["model"] == "gpt-4o"
    assert result["version"] == "v1_baseline"


@patch("backend.evals.eval_tasks._get_orchestrator")
def test_run_v1_scalar_input_converted_to_string(mock_get_orch: MagicMock) -> None:
    mock_orchestrator = MagicMock()
    mock_orchestrator.config.model.name = "gpt-4o-mini"
    mock_orchestrator.config.version = "v1_baseline"
    mock_orchestrator.astream_run = MagicMock(
        return_value=_async_gen(_mock_astream_events())
    )
    mock_get_orch.return_value = mock_orchestrator

    from backend.evals.eval_tasks import run_v1

    asyncio.run(run_v1(42))

    call_kwargs = mock_orchestrator.astream_run.call_args[1]
    assert call_kwargs["message"] == "42"


@patch("backend.evals.eval_tasks._get_orchestrator")
def test_run_v1_float_input_converted_to_string(mock_get_orch: MagicMock) -> None:
    mock_orchestrator = MagicMock()
    mock_orchestrator.config.model.name = "gpt-4o-mini"
    mock_orchestrator.config.version = "v1_baseline"
    mock_orchestrator.astream_run = MagicMock(
        return_value=_async_gen(_mock_astream_events())
    )
    mock_get_orch.return_value = mock_orchestrator

    from backend.evals.eval_tasks import run_v1

    asyncio.run(run_v1(3.14))

    call_kwargs = mock_orchestrator.astream_run.call_args[1]
    assert call_kwargs["message"] == "3.14"


@patch("backend.evals.eval_tasks._get_orchestrator")
def test_run_v1_list_input_converted_to_string(mock_get_orch: MagicMock) -> None:
    mock_orchestrator = MagicMock()
    mock_orchestrator.config.model.name = "gpt-4o-mini"
    mock_orchestrator.config.version = "v1_baseline"
    mock_orchestrator.astream_run = MagicMock(
        return_value=_async_gen(_mock_astream_events())
    )
    mock_get_orch.return_value = mock_orchestrator

    from backend.evals.eval_tasks import run_v1

    asyncio.run(run_v1(["a", "b"]))

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
    mock_orchestrator.config.version = "v1_baseline"
    mock_orchestrator.astream_run = MagicMock(return_value=_async_gen(events))
    mock_get_orch.return_value = mock_orchestrator

    from backend.evals.eval_tasks import run_near_v1_diagnostic

    result = asyncio.run(run_near_v1_diagnostic({"question": "UNH 發生什麼事？"}))

    assert result["tool_outputs"] == [
        {
            "tool": "tavily_financial_search",
            "args": {"query": "UNH news"},
            "error": "timeout",
        }
    ]


@patch("backend.evals.eval_tasks._get_orchestrator")
def test_run_near_v1_diagnostic_extracts_question_field(
    mock_get_orch: MagicMock,
) -> None:
    mock_orchestrator = MagicMock()
    mock_orchestrator.config.model.name = "gpt-4o-mini"
    mock_orchestrator.config.version = "v1_baseline"
    mock_orchestrator.astream_run = MagicMock(
        return_value=_async_gen(_mock_astream_events())
    )
    mock_get_orch.return_value = mock_orchestrator

    from backend.evals.eval_tasks import run_near_v1_diagnostic

    asyncio.run(run_near_v1_diagnostic({"question": "Disney 最近怎麼了？"}))

    call_kwargs = mock_orchestrator.astream_run.call_args[1]
    assert call_kwargs["message"] == "Disney 最近怎麼了？"


@patch("backend.evals.eval_tasks._get_orchestrator")
def test_run_near_v1_diagnostic_forwards_session_and_trace_metadata(
    mock_get_orch: MagicMock,
) -> None:
    mock_orchestrator = MagicMock()
    mock_orchestrator.config.model.name = "gpt-4o-mini"
    mock_orchestrator.config.version = "v1_baseline"
    mock_orchestrator.astream_run = MagicMock(
        return_value=_async_gen(_mock_astream_events())
    )
    mock_get_orch.return_value = mock_orchestrator

    from backend.evals.eval_tasks import run_near_v1_diagnostic

    asyncio.run(
        run_near_v1_diagnostic(
            {
                "question": "AMD 最近怎麼了？",
                "session_id": "near_v1_diagnostic::baseline::17",
                "trace_metadata": {
                    "row_id": "17",
                    "reference_expected_behavior": "may_pass_with_tuning",
                },
            }
        )
    )

    call_kwargs = mock_orchestrator.astream_run.call_args[1]
    assert call_kwargs["message"] == "AMD 最近怎麼了？"
    assert call_kwargs["session_id"] == "near_v1_diagnostic::baseline::17"
    assert call_kwargs["trace_metadata"] == {
        "row_id": "17",
        "reference_expected_behavior": "may_pass_with_tuning",
    }


def test_astream_collect_uses_default_session_id_when_none_provided() -> None:
    mock_orchestrator = MagicMock()
    mock_orchestrator.config.model.name = "gpt-4o-mini"
    mock_orchestrator.config.version = "v1_baseline"
    mock_orchestrator.astream_run = MagicMock(
        return_value=_async_gen(_mock_astream_events())
    )

    from backend.evals.eval_tasks import _astream_collect

    asyncio.run(
        _astream_collect(
            mock_orchestrator,
            "NVDA 最近怎麼了？",
            session_id="sess-123",
            trace_metadata=None,
        )
    )

    assert mock_orchestrator.astream_run.call_args.kwargs == {
        "message": "NVDA 最近怎麼了？",
        "session_id": "sess-123",
    }


@patch("backend.evals.eval_tasks._get_orchestrator")
def test_run_near_v1_diagnostic_forwards_trace_metadata_and_session_id(
    mock_get_orch: MagicMock,
) -> None:
    mock_orchestrator = MagicMock()
    mock_get_orch.return_value = mock_orchestrator

    from backend.evals.eval_tasks import run_near_v1_diagnostic

    expected_result = {
        "response": "ok",
        "tool_outputs": [],
        "model": "gpt-4o-mini",
        "version": "v1_baseline",
    }

    with patch(
        "backend.evals.eval_tasks._astream_collect",
        new=AsyncMock(return_value=expected_result),
    ) as mock_collect:
        result = asyncio.run(
            run_near_v1_diagnostic(
                {
                    "question": "UNH 發生什麼事？",
                    "session_id": "near_v1_diagnostic::baseline::1",
                    "trace_metadata": {"reference_best_source": "mixed"},
                }
            )
        )

    mock_get_orch.assert_called_once_with("v1_baseline")
    mock_collect.assert_awaited_once_with(
        mock_orchestrator,
        "UNH 發生什麼事？",
        session_id="near_v1_diagnostic::baseline::1",
        trace_metadata={"reference_best_source": "mixed"},
    )
    assert result == expected_result


def test_astream_collect_omits_trace_metadata_when_none() -> None:
    mock_orchestrator = MagicMock()
    mock_orchestrator.config.model.name = "gpt-4o-mini"
    mock_orchestrator.config.version = "v1_baseline"
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
    mock_orchestrator.config.version = "v1_baseline"
    mock_orchestrator.astream_run = MagicMock(
        return_value=_async_gen(_mock_astream_events())
    )

    from backend.evals.eval_tasks import _astream_collect

    asyncio.run(
        _astream_collect(
            mock_orchestrator,
            "hello",
            session_id="near_v1_diagnostic::baseline::1",
            trace_metadata={"reference_best_source": "mixed"},
        )
    )

    mock_orchestrator.astream_run.assert_called_once_with(
        message="hello",
        session_id="near_v1_diagnostic::baseline::1",
        trace_metadata={"reference_best_source": "mixed"},
    )
