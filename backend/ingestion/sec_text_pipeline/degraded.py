"""Noise cleaning for degraded-ingest full-document markdown (DEV-172).

When section detection ran a fallback strategy the item parser cannot
trust, the whole filing-level markdown is ingested instead of per-Item
sections. That render carries document furniture worth removing before
chunking: the cover page and INDEX table before the body, page-break
artifacts ("Table of Contents" headers, centered page numbers), and the
signature block at the end.

Every rule is an opt-in cut anchored on a shape observed in real renders
(AMD FY2025 is the reference sample); a document matching no anchor passes
through untouched. Leftover noise is acceptable — deleted content is not.
"""

from __future__ import annotations

import re

# The body opens with a part heading ("# PART I"); everything before it is
# cover page + INDEX. Degraded renders may demote the heading level, so any
# h1-h3 qualifies. Anchored to the line start and requiring the heading to
# end after the roman numeral, so prose mentions ("See PART II of this
# report") never match.
_PART_HEADING_RE = re.compile(r"^#{1,3}\s+PART\s+[IVX]+\s*$", re.MULTILINE)

# The signature block opens with a SIGNATURES heading — or, in renders that
# lose heading markup, a bare ALL-CAPS line. A TOC table row naming the
# signature page ("| SIGNATURES. | ... |") starts with "|" and cannot match.
_SIGNATURES_RE = re.compile(r"^(?:#{1,6}\s*)?SIGNATURES\.?\s*$", re.MULTILINE)

# Page-break artifacts: a standalone "Table of Contents" header line — the
# render can shatter its glyph spacing ("Table of Conten t s") — and
# centered page-number divs ("<div align='center'>106</div>").
_TOC_HEADER_LINE_RE = re.compile(
    r"^\s*Table\s+of\s+Conten\s*t\s*s?\s*$", re.MULTILINE | re.IGNORECASE
)
_PAGE_NUMBER_DIV_RE = re.compile(
    r"^\s*<div align='center'>\s*\d{1,4}\s*</div>\s*$", re.MULTILINE
)

_BLANK_RUN_RE = re.compile(r"\n{3,}")


def _strip_cover_and_toc(text: str) -> str:
    """Cut everything before the first part heading (cover page + INDEX).

    No part heading found → no cut.
    """
    match = _PART_HEADING_RE.search(text)
    return text[match.start() :] if match else text


def _strip_signatures(text: str) -> str:
    """Cut from the LAST signatures heading to the end of the document.

    The signature block always closes a 10-K, so the last match is the real
    one; an earlier false anchor must not delete body content. No match →
    no cut.
    """
    last = None
    for match in _SIGNATURES_RE.finditer(text):
        last = match
    return text[: last.start()] if last else text


def _strip_page_artifacts(text: str) -> str:
    """Drop standalone page-break artifact lines, keeping real content lines."""
    text = _TOC_HEADER_LINE_RE.sub("", text)
    return _PAGE_NUMBER_DIV_RE.sub("", text)


def _collapse_blank_lines(text: str) -> str:
    """Collapse runs of 3+ newlines (left behind by removed lines) to one
    blank line."""
    return _BLANK_RUN_RE.sub("\n\n", text)


def clean_degraded_markdown(markdown: str) -> str:
    """The degraded-ingest text: filing markdown with noise removed.

    Applies the rules in document order — cover/TOC first (so a signatures
    row inside the INDEX is already gone), then the signature block, then
    line-level artifacts — and returns the result stripped. An empty return
    means the filing had no retrievable text at all; the caller decides how
    loud that failure is.
    """
    text = _strip_cover_and_toc(markdown)
    text = _strip_signatures(text)
    text = _strip_page_artifacts(text)
    return _collapse_blank_lines(text).strip()
