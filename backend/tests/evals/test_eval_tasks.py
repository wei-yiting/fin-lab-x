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


@patch("backend.evals.eval_tasks.Orchestrator")
@patch("backend.evals.eval_tasks.VersionConfigLoader")
def test_run_v1_string_input_passes_to_orchestrator(
    mock_loader_cls: MagicMock,
    mock_orchestrator_cls: MagicMock,
) -> None:
    expected_result = _make_orchestrator_result()
    mock_orchestrator = MagicMock()
    mock_orchestrator.run.return_value = expected_result
    mock_orchestrator_cls.return_value = mock_orchestrator

    mock_config = MagicMock()
    mock_loader_cls.return_value.load.return_value = mock_config

    from backend.evals.eval_tasks import run_v1

    result = run_v1("微軟最近有什麼新聞？")

    mock_loader_cls.assert_called_once_with("v1_baseline")
    mock_orchestrator_cls.assert_called_once_with(mock_config)
    mock_orchestrator.run.assert_called_once_with("微軟最近有什麼新聞？")
    assert result == expected_result


@patch("backend.evals.eval_tasks.Orchestrator")
@patch("backend.evals.eval_tasks.VersionConfigLoader")
def test_run_v1_dict_input_extracts_prompt(
    mock_loader_cls: MagicMock,
    mock_orchestrator_cls: MagicMock,
) -> None:
    expected_result = _make_orchestrator_result()
    mock_orchestrator = MagicMock()
    mock_orchestrator.run.return_value = expected_result
    mock_orchestrator_cls.return_value = mock_orchestrator

    mock_config = MagicMock()
    mock_loader_cls.return_value.load.return_value = mock_config

    from backend.evals.eval_tasks import run_v1

    result = run_v1({"prompt": "test query"})

    mock_orchestrator.run.assert_called_once_with("test query")
    assert result == expected_result


@patch("backend.evals.eval_tasks.Orchestrator")
@patch("backend.evals.eval_tasks.VersionConfigLoader")
def test_run_v1_returns_orchestrator_result_structure(
    mock_loader_cls: MagicMock,
    mock_orchestrator_cls: MagicMock,
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
    mock_orchestrator_cls.return_value = mock_orchestrator
    mock_loader_cls.return_value.load.return_value = MagicMock()

    from backend.evals.eval_tasks import run_v1

    result = run_v1("蘋果公司最新的財報表現如何？")

    assert result["response"] == "蘋果公司最新財報表現良好"
    assert len(result["tool_outputs"]) == 1
    assert result["tool_outputs"][0]["tool"] == "tavily_financial_search"
    assert result["model"] == "gpt-4o"
    assert result["version"] == "v1_baseline"
