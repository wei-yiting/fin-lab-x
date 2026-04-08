"""Heading extraction from preprocessor output and longest-common-subsequence helper.

The HTMLPreprocessor returns HTML, not markdown — we extract heading
levels by parsing `<h1>` … `<h6>` tags. This module also exposes a
small LCS implementation for R-13 ordering checks.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Sequence

from bs4 import BeautifulSoup

_HEADING_TAGS = ("h1", "h2", "h3", "h4", "h5", "h6")
_PART_RE = re.compile(r"^\s*PART\s+(I{1,3}V?|IV)\b", re.IGNORECASE)
_ITEM_RE = re.compile(r"^\s*Item\s+\d+[A-Z]?[.\s]", re.IGNORECASE)
_ITEM_NUM_RE = re.compile(r"^\s*Item\s+(\d+)([A-Z]?)", re.IGNORECASE)
_WHITESPACE_RE = re.compile(r"\s+")


def _normalize_text(raw: str) -> str:
    """Collapse all internal whitespace to single ASCII spaces and strip."""
    return _WHITESPACE_RE.sub(" ", raw).strip()


@dataclass(frozen=True)
class Heading:
    level: int          # 1..6
    text: str           # collapsed inner text
    parent_path: tuple[str, ...]  # ancestor heading texts (h1, h2, ... down to one level above self)


def extract_headings(html: str) -> list[Heading]:
    """Return all headings from preprocessed HTML in document order.

    Each heading carries its parent path (the chain of higher-level
    heading texts that precede it in document order). This is enough
    for R-8 path-aware dedup checks at report time.
    """
    soup = BeautifulSoup(html, "html.parser")
    headings: list[Heading] = []
    # Track current ancestor text per level (1..6).
    current: list[str | None] = [None] * 7  # index by level
    for tag in soup.find_all(_HEADING_TAGS):
        level = int(tag.name[1])
        text = _normalize_text(tag.get_text(" ", strip=True))
        # Reset deeper levels — when we see a new h2, h3+ ancestors are gone.
        for deeper in range(level + 1, 7):
            current[deeper] = None
        parent_path = tuple(t for t in current[1:level] if t is not None)
        headings.append(Heading(level=level, text=text, parent_path=parent_path))
        current[level] = text
    return headings


def headings_at_level(headings: Sequence[Heading], level: int) -> list[str]:
    return [h.text for h in headings if h.level == level]


def headings_in_region(
    headings: Sequence[Heading], parent_h2: str
) -> list[Heading]:
    """Return all sub-headings (level >= 3) directly under the given h2.

    A heading belongs to the region if its parent_path contains parent_h2
    at the h2 slot (index 1).
    """
    result: list[Heading] = []
    for h in headings:
        if h.level <= 2:
            continue
        if len(h.parent_path) >= 2 and h.parent_path[1] == parent_h2:
            result.append(h)
    return result


def is_part_heading(text: str) -> bool:
    return bool(_PART_RE.match(text))


def is_item_heading(text: str) -> bool:
    return bool(_ITEM_RE.match(text))


def item_number(text: str) -> tuple[int, str] | None:
    """Parse an Item heading text to (number, suffix).

    e.g. 'Item 1A. Risk Factors' → (1, 'A'); 'Item 7. MD&A' → (7, '').
    Returns None if text does not match.
    """
    m = _ITEM_NUM_RE.match(text)
    if not m:
        return None
    return int(m.group(1)), (m.group(2) or "").upper()


def items_in_monotonic_order(item_texts: Sequence[str]) -> bool:
    """Return True iff item numbers are non-decreasing in the given order.

    Used to detect R-2 reordering. Suffix letters break ties:
    1 < 1A < 1B < 2 < 2A < 3.
    """
    last: tuple[int, str] | None = None
    for text in item_texts:
        parsed = item_number(text)
        if parsed is None:
            continue
        if last is not None and parsed < last:
            return False
        last = parsed
    return True


def longest_common_subsequence(
    new_seq: Sequence[str], baseline_seq: Sequence[str]
) -> list[str]:
    """Return the LCS of new_seq with baseline_seq, restricted to baseline order.

    R-13 use: take baseline_seq as the canonical order, then check that
    new_seq's intersection with baseline preserves that order. The result
    is the longest baseline_seq subsequence that appears in new_seq.
    Equality of result with baseline means full order preservation.
    """
    if not baseline_seq or not new_seq:
        return []
    n = len(new_seq)
    m = len(baseline_seq)
    # dp[i][j] = LCS length for new_seq[:i] vs baseline_seq[:j]
    dp = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            if new_seq[i - 1] == baseline_seq[j - 1]:
                dp[i][j] = dp[i - 1][j - 1] + 1
            else:
                dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])
    # Reconstruct.
    i, j = n, m
    out: list[str] = []
    while i > 0 and j > 0:
        if new_seq[i - 1] == baseline_seq[j - 1]:
            out.append(new_seq[i - 1])
            i -= 1
            j -= 1
        elif dp[i - 1][j] >= dp[i][j - 1]:
            i -= 1
        else:
            j -= 1
    return list(reversed(out))


def detect_vendor(raw_html: str) -> str:
    """Heuristic vendor detection from raw EDGAR HTML.

    Looks at <meta name="generator"> first, then a fallback fingerprint
    based on visible markers. Returns one of:
        'workiva', 'donnelley', 'activedisclosure', 'toppan', 'unknown'
    """
    head = raw_html[:8192].lower()
    if 'name="generator"' in head:
        m = re.search(r'name="generator"\s+content="([^"]+)"', head)
        if m:
            value = m.group(1)
            if "workiva" in value:
                return "workiva"
            if "donnelley" in value or "rrd" in value:
                return "donnelley"
            if "activedisclosure" in value:
                return "activedisclosure"
            if "toppan" in value:
                return "toppan"
            return f"other:{value[:32]}"
    if "workiva" in head or "wdesk" in head:
        return "workiva"
    if "rrdonnelley" in head or "rrdactivedisclosure" in head:
        return "activedisclosure"
    if "toppan" in head:
        return "toppan"
    return "unknown"
