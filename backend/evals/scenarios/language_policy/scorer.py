"""Programmatic scorers for language policy evaluation."""

from __future__ import annotations

import re
from collections.abc import Mapping
from pathlib import Path
from typing import Any

# Only used to locate the package's bundled dictionary file below; OpenCC
# itself (the conversion class) still comes from `from opencc import OpenCC`.
import opencc as _opencc_pkg
from autoevals import Score  # pyright: ignore[reportMissingImports]
from opencc import OpenCC

from backend.evals.eval_helpers import CJK_PATTERN, contains_cjk, cjk_ratio

TICKER_PATTERN = re.compile(r"^[A-Z][A-Z0-9.\-]*$")

# Built once (loads OpenCC's conversion dictionaries) and reused across
# scorer calls rather than per-call.
_S2T_CONVERTER = OpenCC("s2t")

# OpenCC's s2t table treats some characters as ambiguous — e.g. 台's entry
# is "臺 檯 颱 台": it lists itself as a candidate because 台 is genuinely
# dual-status (a Simplified merge of 臺/檯/颱, but also correct standalone
# Traditional, as in 台灣/台積電). convert() picks the non-self candidate,
# so unfiltered s2t-diffing flags correct Traditional text as
# contamination. No public API exposes this data, so this module parses
# the same dictionary file OpenCC loads internally (below) instead of
# hand-picking characters as false positives surface — `zhon`/
# `hanzidentifier` hit the same ambiguity and aren't a better fix.
assert _opencc_pkg.__file__ is not None, (
    "opencc package has no __file__ (unexpected for a normally pip-installed package)"
)
_STCHARACTERS_PATH = (
    Path(_opencc_pkg.__file__).parent / "dictionary" / "STCharacters.txt"
)


def _load_dual_status_traditional_chars(path: Path) -> frozenset[str]:
    """Derive dual-status characters from OpenCC's own s2t table (see module comment).

    Each line is `simplified_char\\tcandidate1 candidate2 ...`; a line where
    the key also appears in its own candidate list is OpenCC's signal that
    the character is valid Traditional as-is. Catches the whole class (170
    characters as of opencc-python-reimplemented 0.1.7), not just discovered examples.
    """
    dual_status: set[str] = set()
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.rstrip("\n")
            if not line:
                continue
            key, _, values = line.partition("\t")
            if key in values.split(" "):
                dual_status.add(key)
    return frozenset(dual_status)


_DUAL_STATUS_TRADITIONAL_CHARS = _load_dual_status_traditional_chars(_STCHARACTERS_PATH)
assert len(_DUAL_STATUS_TRADITIONAL_CHARS) > 100, (
    "Expected roughly 170 dual-status characters derived from "
    f"{_STCHARACTERS_PATH}, got only {len(_DUAL_STATUS_TRADITIONAL_CHARS)} — "
    "the file may be empty, missing, or its format may have changed."
)

# Empirical, not precisely derived: dense-but-correct Traditional text
# measured ~12% "changed"; genuinely-Simplified samples measured 21%-43%.
# 15% sits with margin. May need tuning after DEV-206's real dev-set runs.
_MAX_SIMPLIFIED_RATIO = 0.15

# Independent of ratio: shared vocabulary (股票, 成交量...) can keep the ratio
# misleadingly low even for a wholly-Simplified response (one such case
# measured ~11% and wrongly passed). 3 tolerates an occasional 1-2-character
# mistake while catching anything more sustained.
_MAX_GENUINE_CHANGES = 3


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
    """Check the response is not substantially written in Simplified Chinese.

    Catches what ``response_language``'s CJK-ratio check can't: a fully
    Simplified response can still land inside the expected ratio range.
    Judges overall language, not character-perfect purity — an occasional
    mistake is tolerated (see ``_MAX_SIMPLIFIED_RATIO`` /
    ``_MAX_GENUINE_CHANGES``). No-scores English-expected rows
    (``cjk_min == 0``). Diffs against the s2t conversion char-by-char,
    ignoring ``_DUAL_STATUS_TRADITIONAL_CHARS`` (see module comment).
    """
    expected_mapping = _as_mapping(expected)
    if "cjk_min" not in expected_mapping:
        raise ValueError("response_no_simplified_chars requires cjk_min")

    if float(expected_mapping["cjk_min"]) <= 0:
        return None

    response = _as_mapping(output).get("response", "")
    if not isinstance(response, str):
        response = ""

    converted = _S2T_CONVERTER.convert(response)
    if len(converted) != len(response):
        # s2t conversion is length-preserving for every entry in OpenCC's
        # own dictionaries (verified empirically); a mismatch means that
        # invariant broke, so fail loudly here rather than silently
        # misaligning the per-character diff below.
        raise ValueError("OpenCC s2t conversion changed response length unexpectedly")

    total_cjk = 0
    genuine_changes = 0
    for orig, conv in zip(response, converted):
        if not CJK_PATTERN.match(orig):
            continue
        total_cjk += 1
        if orig != conv and orig not in _DUAL_STATUS_TRADITIONAL_CHARS:
            genuine_changes += 1

    if total_cjk == 0:
        # Vacuous case: no CJK characters means no Simplified contamination.
        is_pure = True
    else:
        is_pure = (
            genuine_changes <= _MAX_GENUINE_CHANGES
            and (genuine_changes / total_cjk) <= _MAX_SIMPLIFIED_RATIO
        )

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
