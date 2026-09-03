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

# OpenCC's Simplified-to-Traditional table treats a number of characters as
# ambiguous: its STCharacters.txt entry for a character can list that same
# character among its own Traditional candidates, alongside other
# Traditional characters it also maps from. 台 is the clearest example —
# its entry is "臺 檯 颱 台" — because 台 is genuinely dual-status: the
# Simplified merge of 臺/檯/颱 in mainland usage, AND a completely
# legitimate, extremely common standalone Traditional character in Taiwan
# usage (台灣, 台北, 台積電 — a common company name in Traditional Chinese
# financial answers). convert() always picks the first candidate (臺)
# rather than recognizing the input was already valid, so unfiltered
# s2t-diffing flags correct Taiwan-standard text as Simplified
# contamination.
#
# opencc-python-reimplemented (0.1.7) has no public API to query this
# ambiguity data directly (OpenCC.convert() is the only public surface), so
# this module parses the same STCharacters.txt dictionary file the library
# loads internally (see _load_dual_status_traditional_chars below) instead
# of hand-picking known-ambiguous characters one at a time as false
# positives are found by testing. A researched alternative — the `zhon`/
# `hanzidentifier` character-set libraries — hits the identical dual-status
# ambiguity and would add two new dependencies for a ~30-row eval dataset,
# so it is not a strictly better fix.
_STCHARACTERS_PATH = (
    Path(_opencc_pkg.__file__).parent / "dictionary" / "STCharacters.txt"
)


def _load_dual_status_traditional_chars(path: Path) -> frozenset[str]:
    """Derive the set of characters OpenCC's own s2t table treats as dual-status.

    Each STCharacters.txt line is `simplified_char\\tcandidate1 candidate2 ...`.
    A line where the key also appears in its own candidate list means OpenCC
    itself considers this character valid Traditional Chinese as-is (not only
    a simplified stand-in for something else) — e.g. `台\\t臺 檯 颱 台` (Taiwan's
    "台" is genuinely dual-status: mainland usage merges it with 臺/檯/颱, but
    Taiwan usage writes 台灣/台積電 with 台 correctly on its own). Deriving this
    from OpenCC's own data catches the whole class (170 characters as of
    opencc-python-reimplemented 0.1.7) instead of hand-picking examples as
    they're discovered by testing.
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

# Empirically-set threshold, not a precisely-derived constant: legitimate
# dense-but-correct Traditional text (repeated 台/占-style dual-status
# usage) measured up to ~12% "changed" under naive s2t diffing, while
# genuinely-Simplified samples measured 21%-43%. 15% sits with margin on
# both sides. May need tuning once DEV-206 runs real dev-set data.
_MAX_SIMPLIFIED_RATIO = 0.15


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

    Only rows expecting a Chinese response (``cjk_min > 0``) make this
    claim — an English-expected row no-scores, matching
    ``expected_tool_called``'s no-claim convention. Catches a drift
    ``response_language``'s CJK-ratio check cannot: a fully Simplified
    response can still land inside the expected CJK ratio range.

    This scorer's job is to judge whether the response is written in the
    wrong language overall, not to guarantee zero wrong characters: an
    occasional genuine mistake is tolerated, but a response substantially
    written in Simplified is not. Detection diffs the response
    character-by-character against its OpenCC Simplified-to-Traditional
    (``s2t``) conversion — s2t conversion is length-preserving (verified
    against every entry in OpenCC's own dictionaries), so index-aligned
    diffing is safe. Among the CJK characters (``CJK_PATTERN``) in the
    original response, a changed character counts as a genuine
    Simplified-contamination signal unless it is in
    ``_DUAL_STATUS_TRADITIONAL_CHARS`` (see that constant's comment for why
    whole-string conversion-equality incorrectly flags legitimate
    Traditional Chinese). The response scores pure (1.0) as long as the
    ratio of genuine changes to total CJK characters stays at or below
    ``_MAX_SIMPLIFIED_RATIO``.
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
        is_pure = (genuine_changes / total_cjk) <= _MAX_SIMPLIFIED_RATIO

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
