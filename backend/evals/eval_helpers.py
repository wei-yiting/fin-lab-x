"""Language detection helpers for evaluation tests."""

import re

CJK_PATTERN = re.compile(r"[\u4e00-\u9fff\u3400-\u4dbf]")


def contains_cjk(text: str) -> bool:
    """Return True if text contains any CJK characters."""
    return bool(CJK_PATTERN.search(text))


def cjk_ratio(text: str) -> float:
    """Return the ratio of CJK characters to total non-whitespace characters."""
    non_ws = re.sub(r"\s", "", text)
    if not non_ws:
        return 0.0
    return len(CJK_PATTERN.findall(non_ws)) / len(non_ws)
