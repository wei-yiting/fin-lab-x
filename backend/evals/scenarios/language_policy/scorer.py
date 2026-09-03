"""Programmatic scorers for language policy evaluation."""

from __future__ import annotations

import re
from collections.abc import Mapping
from typing import Any

from autoevals import Score  # pyright: ignore[reportMissingImports]
from opencc import OpenCC

from backend.evals.eval_helpers import contains_cjk, cjk_ratio

TICKER_PATTERN = re.compile(r"^[A-Z][A-Z0-9.\-]*$")

# Built once (loads OpenCC's conversion dictionaries) and reused across
# scorer calls rather than per-call.
_S2T_CONVERTER = OpenCC("s2t")


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

    for tool_output in tool_outputs:
        tool_output_mapping = _as_mapping(tool_output)
        current_tool = tool_output_mapping.get("tool")
        if tool_name is not None and current_tool != tool_name:
            continue

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

    return Score(name="tool_arg_no_cjk", score=1.0)


def expected_tool_called(output: Any, expected: Any, *, input: Any) -> Score | None:
    """Check the declared expect_tool was actually called at least once.

    Validity guard for tool_arg_no_cjk: with zero tool calls that scorer
    passes vacuously, so this one turns the scenario red instead. Rows that
    declare no expect_tool make no claim — return None (platform no-score).
    """
    expected_mapping = _as_mapping(expected)
    tool_name = expected_mapping.get("tool")
    if not tool_name:
        return None

    tool_outputs = _as_mapping(output).get("tool_outputs", [])
    if not isinstance(tool_outputs, list):
        tool_outputs = []

    for tool_output in tool_outputs:
        if _as_mapping(tool_output).get("tool") == tool_name:
            return Score(name="expected_tool_called", score=1.0)

    return Score(name="expected_tool_called", score=0.0)


def response_no_simplified_chars(
    output: Any, expected: Any, *, input: Any
) -> Score | None:
    """Check the response contains no Simplified Chinese characters.

    Only rows expecting a Chinese response (``cjk_min > 0``) make this
    claim — an English-expected row no-scores, matching
    ``expected_tool_called``'s no-claim convention. Catches a drift
    ``response_language``'s CJK-ratio check cannot: a fully Simplified
    response can still land inside the expected CJK ratio range.

    Detection converts the response through OpenCC's Simplified-to-
    Traditional table (``s2t``): any character that conversion touches is,
    by construction, a Simplified-form character that should not appear in
    a correct Traditional Chinese answer. Characters identical in both
    scripts pass through untouched, so this never flags valid Traditional
    text.
    """
    expected_mapping = _as_mapping(expected)
    if "cjk_min" not in expected_mapping:
        raise ValueError("response_no_simplified_chars requires cjk_min")

    if float(expected_mapping["cjk_min"]) <= 0:
        return None

    response = _as_mapping(output).get("response", "")
    if not isinstance(response, str):
        response = ""

    is_pure = _S2T_CONVERTER.convert(response) == response
    return Score(name="response_no_simplified_chars", score=1.0 if is_pure else 0.0)


def response_language(output: Any, expected: Any, *, input: Any) -> Score:
    """Check response CJK ratio is within the expected range."""
    expected_mapping = _as_mapping(expected)
    if "cjk_min" not in expected_mapping or "cjk_max" not in expected_mapping:
        raise ValueError("response_language requires cjk_min and cjk_max")

    response = _as_mapping(output).get("response", "")
    if not isinstance(response, str):
        response = ""

    ratio = cjk_ratio(response)
    cjk_min = float(expected_mapping["cjk_min"])
    cjk_max = float(expected_mapping["cjk_max"])
    is_in_range = cjk_min <= ratio <= cjk_max
    return Score(name="response_language", score=1.0 if is_in_range else 0.0)
