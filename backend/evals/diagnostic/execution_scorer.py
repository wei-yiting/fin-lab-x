"""Deterministic execution-health scorer for diagnostic scenarios."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

RUNNER_ERROR_MARKERS = {"ERROR", "__ERROR__"}


def _as_mapping(value: Any) -> Mapping[str, Any]:
    if isinstance(value, Mapping):
        return value
    return {}


def _tool_error_name(tool_output: Any) -> str | None:
    tool_output_mapping = _as_mapping(tool_output)
    tool_name = tool_output_mapping.get("tool")
    if not isinstance(tool_name, str) or not tool_name:
        return None

    error_value = tool_output_mapping.get("error")
    if error_value not in (None, ""):
        return tool_name

    result_value = tool_output_mapping.get("result")
    if isinstance(result_value, str) and result_value in RUNNER_ERROR_MARKERS:
        return tool_name

    return None


def execution_health(output: Any, expected: Any, *, input: Any = None) -> dict[str, Any]:
    """Record whether the run completed and whether tool calls all succeeded."""
    output_mapping = _as_mapping(output)
    response = output_mapping.get("response")
    execution_complete = bool(response) and response not in RUNNER_ERROR_MARKERS

    tool_outputs = output_mapping.get("tool_outputs", [])
    if not isinstance(tool_outputs, list):
        tool_outputs = []

    tool_error_names = [
        tool_name
        for tool_output in tool_outputs
        if (tool_name := _tool_error_name(tool_output)) is not None
    ]
    tool_call_all_successful = len(tool_error_names) == 0

    return {
        "name": "diagnostic_execution_health",
        "score": 1.0 if execution_complete and tool_call_all_successful else 0.0,
        "metadata": {
            "execution_complete": execution_complete,
            "tool_call_all_successful": tool_call_all_successful,
            "tool_error_names": tool_error_names,
        },
    }
