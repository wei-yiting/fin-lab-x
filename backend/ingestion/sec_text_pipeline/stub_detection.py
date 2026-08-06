"""Stub detection v2 — v1 patterns plus pseudo-stub pointer patterns.

The v2 patterns cover items whose whole substance is a cross-reference to
another part of the annual report (observed on JPM Items 7/7A and XOM
Item 7, which point at the glossy Annual Report pages instead of using
incorporated-by-reference wording). They plug into
:func:`backend.common.sec_core.classify_stub_section` — the shared
remove-matching-sentences-then-measure-remainder mechanism — because
pattern presence alone must never classify a stub: a 60k-char MD&A can
casually contain one pointer sentence and has to survive. The frozen v1
:func:`is_stub_section` never sees these patterns.
"""

import re

from backend.common.sec_core import classify_stub_section

PSEUDO_STUB_PATTERNS: tuple[re.Pattern[str], ...] = (
    # XOM Item 7: "Reference is made to the section entitled Financial Review..."
    re.compile(r"reference\s+is\s+made\s+to", re.IGNORECASE),
    # JPM Item 7: "...appears on pages 46-160 of the Annual Report."
    re.compile(r"appears\s+on\s+pages?\s+\d+", re.IGNORECASE),
    # JPM Item 7A: "Refer to the Market Risk Management section..."
    # Section names are multi-word ("Market Risk Management"), so allow
    # 1-6 words — bounded so the gate cannot span arbitrary prose.
    re.compile(r"refer\s+to\s+the\s+(?:\S+\s+){1,6}section", re.IGNORECASE),
)


def is_stub_section_v2(text: str) -> tuple[bool, str | None]:
    """Classify a 10-K item body as stub vs real, v2 pattern set."""
    return classify_stub_section(text, extra_pointer_patterns=PSEUDO_STUB_PATTERNS)
