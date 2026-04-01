"""Tests for eval task functions."""

from typing import Any
from unittest.mock import MagicMock, patch

from backend.agent_engine.agents.base import OrchestratorResult, ToolOutput


def _make_orchestrator_result(**overrides: Any) -> OrchestratorResult:
    defaults: OrchestratorResult = {
        "response": "Test response",
        "tool_outputs": [],
        "model": "gpt-4o-mini",
        "version": "v1_baseline",
    }
    defaults.update(overrides)
    return defaults


@patch("backend.evals.eval_tasks._get_orchestrator")
def test_run_v1_string_input_passes_to_orchestrator(
    mock_get_orch: MagicMock,
) -> None:
    expected_result = _make_orchestrator_result()
    mock_orchestrator = MagicMock()
    mock_orchestrator.run.return_value = expected_result
    mock_get_orch.return_value = mock_orchestrator

    from backend.evals.eval_tasks import run_v1

    result = run_v1("微軟最近有什麼新聞？")

    mock_get_orch.assert_called_once_with("v1_baseline")
    mock_orchestrator.run.assert_called_once_with("微軟最近有什麼新聞？")
    assert result == expected_result


@patch("backend.evals.eval_tasks._get_orchestrator")
def test_run_v1_dict_input_extracts_prompt(
    mock_get_orch: MagicMock,
) -> None:
    expected_result = _make_orchestrator_result()
    mock_orchestrator = MagicMock()
    mock_orchestrator.run.return_value = expected_result
    mock_get_orch.return_value = mock_orchestrator

    from backend.evals.eval_tasks import run_v1

    result = run_v1({"prompt": "test query"})

    mock_orchestrator.run.assert_called_once_with("test query")
    assert result == expected_result


@patch("backend.evals.eval_tasks._get_orchestrator")
def test_run_v1_returns_orchestrator_result_structure(
    mock_get_orch: MagicMock,
) -> None:
    expected_result = _make_orchestrator_result(
        response="蘋果公司最新財報表現良好",
        tool_outputs=[
            ToolOutput(
                tool="tavily_financial_search",
                args={"query": "AAPL latest earnings"},
                result="Earnings beat expectations...",
            )
        ],
        model="gpt-4o",
        version="v1_baseline",
    )
    mock_orchestrator = MagicMock()
    mock_orchestrator.run.return_value = expected_result
    mock_get_orch.return_value = mock_orchestrator

    from backend.evals.eval_tasks import run_v1

    result = run_v1("蘋果公司最新的財報表現如何？")

    assert result["response"] == "蘋果公司最新財報表現良好"
    assert len(result["tool_outputs"]) == 1
    assert result["tool_outputs"][0]["tool"] == "tavily_financial_search"
    assert result["model"] == "gpt-4o"
    assert result["version"] == "v1_baseline"


@patch("backend.evals.eval_tasks._get_orchestrator")
def test_run_v1_scalar_input_converted_to_string(
    mock_get_orch: MagicMock,
) -> None:
    """Scalar (non-str, non-dict) input should be str()-converted, not crash."""
    expected_result = _make_orchestrator_result()
    mock_orchestrator = MagicMock()
    mock_orchestrator.run.return_value = expected_result
    mock_get_orch.return_value = mock_orchestrator

    from backend.evals.eval_tasks import run_v1

    result = run_v1(42)

    mock_orchestrator.run.assert_called_once_with("42")
    assert result == expected_result


@patch("backend.evals.eval_tasks._get_orchestrator")
def test_run_v1_float_input_converted_to_string(
    mock_get_orch: MagicMock,
) -> None:
    """Float input should be str()-converted without AttributeError."""
    expected_result = _make_orchestrator_result()
    mock_orchestrator = MagicMock()
    mock_orchestrator.run.return_value = expected_result
    mock_get_orch.return_value = mock_orchestrator

    from backend.evals.eval_tasks import run_v1

    result = run_v1(3.14)

    mock_orchestrator.run.assert_called_once_with("3.14")
    assert result == expected_result


@patch("backend.evals.eval_tasks._get_orchestrator")
def test_run_v1_list_input_converted_to_string(
    mock_get_orch: MagicMock,
) -> None:
    """List input (non-Mapping) should be str()-converted."""
    expected_result = _make_orchestrator_result()
    mock_orchestrator = MagicMock()
    mock_orchestrator.run.return_value = expected_result
    mock_get_orch.return_value = mock_orchestrator

    from backend.evals.eval_tasks import run_v1

    result = run_v1(["a", "b"])

    mock_orchestrator.run.assert_called_once_with("['a', 'b']")
    assert result == expected_result
