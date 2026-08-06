"""Stub detection v2 — v1 patterns plus pseudo-stub pointer patterns.

The v2 patterns cover items whose whole substance is a cross-reference to
another part of the annual report (design.md §4.6: JPM Item 7/7A, XOM
Item 7). They plug into :func:`backend.common.sec_core.classify_stub_section`
— the shared remove-matching-sentences-then-measure-remainder mechanism —
so a substantive item that merely *mentions* a cross-reference survives
(spec R8 red line). The frozen v1 :func:`is_stub_section` never sees these
patterns.
"""

import re

from backend.common.sec_core import classify_stub_section

PSEUDO_STUB_PATTERNS: tuple[re.Pattern[str], ...] = (
    # XOM Item 7: "Reference is made to the section entitled Financial Review..."
    re.compile(r"reference\s+is\s+made\s+to", re.IGNORECASE),
    # JPM Item 7: "...appears on pages 46-160 of the Annual Report."
    re.compile(r"appears\s+on\s+pages?\s+\d+", re.IGNORECASE),
    # JPM Item 7A: "Refer to the Market Risk Management section..."
    re.compile(r"refer\s+to\s+the\s+\S+(?:\s+\S+)*?\s+section", re.IGNORECASE),
)


def is_stub_section_v2(text: str) -> tuple[bool, str | None]:
    """Classify a 10-K item body as stub vs real, v2 pattern set."""
    return classify_stub_section(text, extra_pointer_patterns=PSEUDO_STUB_PATTERNS)
