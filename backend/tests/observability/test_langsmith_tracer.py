"""Tests for LangSmith tracing decorator."""

from unittest.mock import patch, MagicMock
from backend.agent_engine.observability.langsmith_tracer import trace_step


def test_trace_step_decorator_returns_original_result():
    """Test trace_step decorator returns the original function result."""

    @trace_step(step_name="test_step", tags=["version:0.1.0"])
    def sample_function(x: int) -> int:
        return x * 2

    with patch(
        "backend.agent_engine.observability.langsmith_tracer.RunTree"
    ) as mock_run_tree:
        mock_run_instance = MagicMock()
        mock_run_tree.return_value = mock_run_instance

        result = sample_function(5)

        assert result == 10


def test_trace_step_decorator_calls_run_tree():
    """Test trace_step decorator creates RunTree with correct parameters."""

    @trace_step(step_name="test_step", run_type="tool", tags=["version:0.1.0"])
    def sample_function(x: int) -> int:
        return x * 2

    with patch(
        "backend.agent_engine.observability.langsmith_tracer.RunTree"
    ) as mock_run_tree:
        mock_run_instance = MagicMock()
        mock_run_tree.return_value = mock_run_instance

        sample_function(5)

        mock_run_tree.assert_called_once()
        call_kwargs = mock_run_tree.call_args[1]
        assert call_kwargs["name"] == "test_step"
        assert call_kwargs["run_type"] == "tool"
        assert "version:0.1.0" in call_kwargs["tags"]
