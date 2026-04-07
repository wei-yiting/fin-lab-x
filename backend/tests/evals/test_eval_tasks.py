"""Tests for eval task functions.

Verifies that run_v1 uses the async streaming path (astream_run) and
correctly collects domain events into OrchestratorResult.
"""

import asyncio
from unittest.mock import MagicMock, patch

from backend.agent_engine.streaming.domain_events_schema import (
    Finish,
    MessageStart,
    TextDelta,
    TextEnd,
    TextStart,
    ToolCall,
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
        events.extend([
            ToolCall(tool_call_id="tc-1", tool_name=tool_name, args={}),
            ToolResult(tool_call_id="tc-1", result=tool_result),
        ])

    events.append(Finish(finish_reason="stop", usage=Usage(input_tokens=10, output_tokens=20)))
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
