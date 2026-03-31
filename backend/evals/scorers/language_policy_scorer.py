"""Programmatic scorers for language policy evaluation."""

from __future__ import annotations

import re
from collections.abc import Mapping
from typing import Any

from autoevals import Score

from backend.evals.eval_helpers import contains_cjk, cjk_ratio

TICKER_PATTERN = re.compile(r"^[A-Z][A-Z0-9.\-]*$")


def _as_mapping(value: Any) -> Mapping[str, Any]:
    if isinstance(value, Mapping):
        return value
    return {}


def tool_arg_no_cjk(output: Any, expected: Any, *, input: Any) -> Score:
    """Check tool arguments contain no CJK characters."""
    expected_mapping = _as_mapping(expected)
    if not expected_mapping.get("search_query_no_cjk"):
        return Score(name="tool_arg_no_cjk", score=1.0)

    tool_name = expected_mapping.get("tool")
    tool_outputs = _as_mapping(output).get("tool_outputs", [])
    if not isinstance(tool_outputs, list):
        tool_outputs = []

    matched_tool = False

    for tool_output in tool_outputs:
        tool_output_mapping = _as_mapping(tool_output)
        current_tool = tool_output_mapping.get("tool")
        if tool_name is not None and current_tool != tool_name:
            continue

        matched_tool = True
        args = _as_mapping(tool_output_mapping.get("args", {}))
        for arg_key, arg_value in args.items():
            if not isinstance(arg_value, str):
                continue
            if arg_key == "ticker":
                if not TICKER_PATTERN.match(arg_value):
                    return Score(name="tool_arg_no_cjk", score=0.0)
                continue
            if contains_cjk(arg_value):
                return Score(name="tool_arg_no_cjk", score=0.0)

    if tool_name is not None and not matched_tool:
        return Score(name="tool_arg_no_cjk", score=0.0)

    return Score(name="tool_arg_no_cjk", score=1.0)


def response_language(output: Any, expected: Any, *, input: Any) -> Score:
    """Check response CJK ratio is within the expected range."""
    expected_mapping = _as_mapping(expected)
    if "cjk_min" not in expected_mapping or "cjk_max" not in expected_mapping:
        raise ValueError("response_language requires cjk_min and cjk_max")

    response = _as_mapping(output).get("response", "")
    if not isinstance(response, str):
        response = ""

    ratio = cjk_ratio(response)
    is_in_range = expected_mapping["cjk_min"] <= ratio <= expected_mapping["cjk_max"]
    return Score(name="response_language", score=1.0 if is_in_range else 0.0)
