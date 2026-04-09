"""Strip 10-K boilerplate and normalize Part / Item headings.

Operates on the markdown output of the html→markdown converter to remove
content with zero RAG value (cover pages, page separators, Part III stubs
that are pure references to the Proxy Statement) and to normalize
inconsistent Item / Part heading formats produced by SEC EDGAR.

Designed conservatively: every rule prefers leaving noise over risking
deletion of real content. Once content is dropped from the cleaned
markdown it cannot be recovered downstream — see
``feedback_cleanup_conservative`` user guidance and the validation
report at ``artifacts/current/validation_cleanup_patterns.md``.

Wired into ``SECFilingPipeline._process_internal`` as the step
immediately after ``convert_with_fallback()``.
"""

from __future__ import annotations

import logging
import re

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# R1.1 Cover page anchors
# ---------------------------------------------------------------------------

_PART_I_ANCHOR_RE = re.compile(r"^# (?:PART|Part) I\b", re.MULTILINE)
_ITEM_1_ANCHOR_RE = re.compile(r"^## (?:ITEM|Item) 1\b", re.MULTILINE)


# ---------------------------------------------------------------------------
# R1.2 Page separator
# ---------------------------------------------------------------------------

# Match: empty-or-numeric line + bare `---` line + optional TOC link line.
# Markdown table separators (`| --- | --- |`) are pipe-flanked and never
# match this pattern.
_PAGE_SEP_RE = re.compile(
    r"^[ \t]*\d*[ \t]*\n"
    r"---[ \t]*\n"
    r"(?:\[Table of Contents\]\([^)]+\)[ \t]*\n)?",
    re.MULTILINE,
)


# ---------------------------------------------------------------------------
# R1.3 Part III stub
# ---------------------------------------------------------------------------

# Match `## Item 10` through `## Item 14` (NOT `1A`, `1B`, `1C` — `\b`
# word boundary stops digit consumption at the alphabetic suffix).
_PART_III_HEADING_RE = re.compile(
    r"^## (?:ITEM|Item) 1[0-4]\b[^\n]*$",
    re.MULTILINE,
)

# Find the next heading line (## or # at start of line) — used to bound
# the section body of a Part III item.
_NEXT_HEADING_RE = re.compile(r"^#{1,2} ", re.MULTILINE)

# Match "incorporated by reference" plus common adverb-injected variants
# ("incorporated herein by reference", "incorporated by reference into",
# "incorporated by reference herein to", etc.). Validation found that the
# vast majority of real 10-Ks use "incorporated herein by reference" so
# the original spec regex missed almost everything.
_INCORP_BY_REF_RE = re.compile(
    r"incorporated\s+(?:\w+\s+)?(?:in|into|to|by)\s+(?:\w+\s+)?reference",
    re.IGNORECASE,
)

# Approximate sentence boundary — split only when the punctuation is
# preceded by a LETTER (not a digit) and followed by whitespace + a
# capital letter. The letter constraint avoids splitting at numeric
# references like ``Item 1.`` or ``Item 14.`` inside a stub sentence,
# which would otherwise let the second half escape ref-detection. The
# capital-letter lookahead is a soft sentence-start hint. Still naive
# enough to over-split on ``Mr. Vondran`` (harmless — both halves are
# kept since neither contains the ref phrase).
_SENTENCE_SPLIT_RE = re.compile(r"(?<=[A-Za-z][.!?])\s+(?=[A-Z])")

# Markdown link / image syntax. We strip these before counting remaining
# content because image filenames and URL-strings are not prose — a
# trailing image inside a stub section shouldn't inflate the char count
# enough to keep the section alive.
_MARKDOWN_LINK_RE = re.compile(r"!?\[[^\]]*\]\([^)]*\)")

# If the section body, after dropping ref sentences and whitespace, is
# below this many non-whitespace chars, treat it as a pure stub and
# remove the section. Tight threshold (a single short sentence is
# typically 80-200 chars) to favor leaving content alone.
_PURE_STUB_REMAINING_THRESHOLD = 100


# ---------------------------------------------------------------------------
# R2 Heading normalization
# ---------------------------------------------------------------------------

_PART_HEADING_RE = re.compile(
    r"^# (?:PART|Part)\s+([IVX]+)\b\.?[ \t]*$",
    re.MULTILINE,
)

_ITEM_HEADING_RE = re.compile(
    r"^## (?:ITEM|Item)\s+(\d+[A-Z]?)\.?[ \t]*([^\n]*)$",
    re.MULTILINE,
)

# Bare Item heading with no inline title — used by R2.1 to look at the
# next non-blank line for a split-off title.
_BARE_ITEM_HEADING_RE = re.compile(
    r"^(## (?:ITEM|Item)\s+\d+[A-Z]?)\.?[ \t]*$"
)

# Whitelisted abbreviations preserved during title-casing.
_ABBREVIATIONS = frozenset(
    {"MD&A", "SEC", "U.S.", "U.S", "R&D", "CEO", "CFO", "CTO", "ESG", "AI", "IT", "IPO"}
)

# Small words that stay lowercase in Title Case (after the first word).
_TITLE_CASE_SMALL_WORDS = frozenset(
    {"of", "the", "and", "for", "to", "in", "on", "at", "by", "a", "an", "or", "as", "is"}
)

_NEXT_LINE_TITLE_MAX_LEN = 100
_TRUNCATED_HEADING_TITLE_LEN = 5


# ---------------------------------------------------------------------------
# Public class
# ---------------------------------------------------------------------------


class MarkdownCleaner:
    """Strip 10-K boilerplate and normalize Part / Item headings.

    Stateless — instances are reusable across filings. The class mirrors
    the design of :class:`HTMLPreprocessor` from the same package: a
    single ``clean()`` entry point that runs a pipeline of private steps,
    each of which can be unit-tested in isolation.
    """

    def clean(self, markdown: str) -> str:
        """Apply all cleanup rules in order.

        Pipeline order matters:

        1. ``_strip_cover_page`` removes the registrant info / check
           marks / DOCUMENTS INCORPORATED BY REFERENCE narrative *before*
           the Part III stub stripper runs, so cover-page references to
           Part III items don't accidentally get parsed as Item sections.
        2. ``_strip_page_separators`` removes the ``---`` page-break
           noise that the html→markdown converter sprinkles throughout.
        3. ``_strip_part_iii_stubs`` removes pure-stub Item 10-14
           sections, preserving any section that has substantive real
           content (AMT exec biographies, CRM Code of Conduct, etc.).
        4. ``_normalize_headings`` standardizes Part / Item heading
           casing and merges split-line titles back into their headings.
        """
        markdown = self._strip_cover_page(markdown)
        markdown = self._strip_page_separators(markdown)
        markdown = self._strip_part_iii_stubs(markdown)
        markdown = self._normalize_headings(markdown)
        return markdown

    # ------------------------------------------------------------------
    # R1.1 Cover page stripping
    # ------------------------------------------------------------------

    def _strip_cover_page(self, markdown: str) -> str:
        """Remove boilerplate between the YAML frontmatter and the first Part I.

        Tries the primary anchor ``# Part I`` first, then falls back to
        ``## Item 1`` (BAC, JNJ have no Part heading at all but do have
        Item 1). If neither anchor is found (GE 2008, INTC 2025, BRK.B
        2025 — non-standard formats), the cleaner logs a warning and
        passes through unchanged. Frontmatter is always preserved.
        """
        if not markdown.startswith("---\n"):
            # No frontmatter — nothing to anchor against, leave unchanged.
            return markdown

        fm_end = markdown.find("\n---\n", 4)
        if fm_end == -1:
            return markdown

        body_start = fm_end + len("\n---\n")
        prefix = markdown[:body_start]
        body = markdown[body_start:]

        anchor = _PART_I_ANCHOR_RE.search(body)
        if anchor is None:
            anchor = _ITEM_1_ANCHOR_RE.search(body)
        if anchor is None:
            logger.warning(
                "MarkdownCleaner: no '# Part I' or '## Item 1' anchor found; "
                "skipping cover page strip (filing may use a non-standard format)"
            )
            return markdown

        return prefix + body[anchor.start() :]

    # ------------------------------------------------------------------
    # R1.2 Page separator stripping
    # ------------------------------------------------------------------

    def _strip_page_separators(self, markdown: str) -> str:
        """Remove standalone ``---`` page separators with optional TOC link.

        The regex requires the ``---`` line to be bare (not pipe-flanked)
        and the previous line to be empty or all-digits, so markdown
        table separators (``| --- | --- |``) are never matched.
        """
        return _PAGE_SEP_RE.sub("", markdown)

    # ------------------------------------------------------------------
    # R1.3 Part III stub stripping
    # ------------------------------------------------------------------

    def _strip_part_iii_stubs(self, markdown: str) -> str:
        """Remove Item 10-14 sections that are pure references to the Proxy Statement.

        Conservative algorithm: for each ``## Item 10-14`` section, drop
        the sentences containing "incorporated...by reference" and check
        what's left. If the remainder is < 100 non-whitespace chars, the
        section is a pure stub → remove. Otherwise the section has
        substantive real content (e.g. AMT's 7 exec officer biographies,
        CRM's Code of Conduct policy) → preserve unchanged.

        Item 1C / 9A / 9B / 9C are protected by the regex ``\\b`` word
        boundary on ``1[0-4]``.
        """
        result_parts: list[str] = []
        last_end = 0

        for heading_match in _PART_III_HEADING_RE.finditer(markdown):
            heading_start = heading_match.start()
            heading_line_end = markdown.find("\n", heading_start)
            if heading_line_end == -1:
                continue

            section_end = self._find_next_heading(markdown, heading_line_end + 1)
            section_body = markdown[heading_line_end + 1 : section_end]

            if self._is_pure_stub(section_body):
                result_parts.append(markdown[last_end:heading_start])
                last_end = section_end
            # Hybrid / real content: leave the section in place by not
            # advancing last_end. The next stub strip (or the final tail
            # append) will sweep this section into the output.

        result_parts.append(markdown[last_end:])
        return "".join(result_parts)

    @staticmethod
    def _find_next_heading(markdown: str, start: int) -> int:
        """Return the index of the next ``^#{1,2} `` heading after ``start``, or end-of-string."""
        match = _NEXT_HEADING_RE.search(markdown, start)
        if match is None:
            return len(markdown)
        return match.start()

    @staticmethod
    def _is_pure_stub(section_body: str) -> bool:
        """Decide whether a Part III item section body is a pure ref-to-Proxy stub.

        Splits on approximate sentence boundaries, drops sentences that
        contain the incorporated-by-reference pattern, strips markdown
        link/image syntax (filenames and URLs are not prose), then
        counts non-whitespace, non-structural chars. Below the threshold
        ⇒ pure stub.

        Naive sentence splitting is fine because the split is only used
        to identify which sentences to drop; kept sentences still cover
        the full character count of the original real content.
        """
        sentences = _SENTENCE_SPLIT_RE.split(section_body)
        kept = [s for s in sentences if not _INCORP_BY_REF_RE.search(s)]
        remaining = " ".join(kept)
        # Strip markdown links / images so trailing images / footer URLs
        # don't keep a stub section alive.
        remaining = _MARKDOWN_LINK_RE.sub("", remaining)
        # Strip whitespace plus markdown structural noise (---, |, *).
        cleaned = re.sub(r"[\s\-\|\*]+", "", remaining)
        return len(cleaned) < _PURE_STUB_REMAINING_THRESHOLD

    # ------------------------------------------------------------------
    # R2 Heading normalization
    # ------------------------------------------------------------------

    def _normalize_headings(self, markdown: str) -> str:
        """Normalize Part / Item heading format and merge split-line titles."""
        markdown = self._merge_split_titles(markdown)
        markdown = _PART_HEADING_RE.sub(self._part_replacement, markdown)
        markdown = _ITEM_HEADING_RE.sub(self._item_replacement, markdown)
        return markdown

    def _merge_split_titles(self, markdown: str) -> str:
        """R2.1 — pull AMZN-style and AMT-style next-line titles into the heading.

        - AMZN: ``## Item 1.\\nBusiness Description`` → ``## Item 1. Business Description``
        - AMT:  ``## ITEM 10.\\n\\n- DIRECTORS, ...`` → ``## ITEM 10. DIRECTORS, ...``

        The dash-prefix branch (AMT) requires the remaining text to be
        ALL CAPS or Title Case to avoid mis-merging real bullet points.
        """
        lines = markdown.split("\n")
        result_lines: list[str] = []
        i = 0
        while i < len(lines):
            line = lines[i]
            heading_match = _BARE_ITEM_HEADING_RE.match(line)
            if heading_match is None:
                result_lines.append(line)
                i += 1
                continue

            # Find next non-blank line
            j = i + 1
            while j < len(lines) and lines[j].strip() == "":
                j += 1

            if j >= len(lines):
                result_lines.append(line)
                i += 1
                continue

            candidate_title = self._extract_split_title(lines[j])
            if candidate_title is None:
                result_lines.append(line)
                i += 1
                continue

            heading_prefix = heading_match.group(1)
            result_lines.append(f"{heading_prefix}. {candidate_title}")
            # Skip the blank lines and the consumed title line
            i = j + 1

        return "\n".join(result_lines)

    @staticmethod
    def _extract_split_title(line: str) -> str | None:
        """Return the title text if ``line`` looks like a split-off Item title.

        Returns ``None`` if ``line`` is empty, too long, a heading, a
        code block, a markdown table, or (for the dash-prefix branch) a
        bullet that doesn't look like a title.
        """
        stripped = line.strip()
        if not stripped or len(stripped) >= _NEXT_LINE_TITLE_MAX_LEN:
            return None
        if stripped.startswith(("#", "```", "|")):
            return None

        if stripped.startswith("- "):
            content = stripped[2:].strip()
            if not content or len(content) >= _NEXT_LINE_TITLE_MAX_LEN:
                return None
            # Require ALL CAPS or Title Case to avoid merging real bullets.
            if content.isupper() or _looks_like_title_case(content):
                return content
            return None

        # AMZN branch: plain text, must start with alphanumeric.
        if stripped[0].isalnum():
            return stripped
        return None

    def _part_replacement(self, match: re.Match[str]) -> str:
        roman = match.group(1).upper()
        return f"# Part {roman}"

    def _item_replacement(self, match: re.Match[str]) -> str:
        num = match.group(1).upper()
        title = match.group(2).strip()

        if not title:
            return f"## Item {num}."

        cased = _title_case(title)

        # R2.2 defensive: log if heading title is suspiciously short.
        if 0 < len(cased) < _TRUNCATED_HEADING_TITLE_LEN:
            logger.warning(
                "MarkdownCleaner: truncated heading detected: %r — converter may have dropped chars",
                f"## Item {num}. {cased}",
            )

        return f"## Item {num}. {cased}"


# ---------------------------------------------------------------------------
# Title-casing helpers
# ---------------------------------------------------------------------------


def _title_case(text: str) -> str:
    """Convert ALL CAPS, all-lowercase, or sentence case titles to Title Case.

    Already-correct Title Case is left untouched. Sentence case (only the
    first word capitalized, rest lowercase — JNJ's `Risk factors` style)
    triggers re-casing because each significant word should start with a
    capital. Whitelisted abbreviations (MD&A, SEC, U.S., R&D) keep their
    uppercase form. Small connector words (of, the, and, ...) stay
    lowercase except as the first word.
    """
    words = text.split()
    if not words:
        return text

    if not _needs_recasing(words):
        return text

    out: list[str] = []
    for idx, word in enumerate(words):
        upper_form = word.upper()
        if upper_form in _ABBREVIATIONS:
            out.append(upper_form)
            continue

        bare = word.lower().strip(".,;:")
        if idx > 0 and bare in _TITLE_CASE_SMALL_WORDS:
            out.append(word.lower())
            continue

        out.append(_capitalize_word(word))

    return " ".join(out)


def _needs_recasing(words: list[str]) -> bool:
    """Decide whether `words` deviate from proper Title Case.

    Returns True if:
    - Title is ALL CAPS or all lowercase (every letter uniform case), OR
    - Any non-first significant word starts with a lowercase letter
      (sentence case — first word capitalized, rest lower).

    Returns False if every significant word already starts with a
    capital letter (proper Title Case — leave alone).
    """
    has_upper = False
    has_lower = False
    for word in words:
        for ch in word:
            if ch.isupper():
                has_upper = True
            elif ch.islower():
                has_lower = True
        if has_upper and has_lower:
            break

    if not (has_upper and has_lower):
        # ALL CAPS or all lowercase — definitely re-case
        return True

    # Mixed case — check whether every significant word is properly capitalized
    for idx, word in enumerate(words):
        if not word:
            continue
        bare = word.lower().strip(".,;:'\"")
        if idx > 0 and bare in _TITLE_CASE_SMALL_WORDS:
            continue
        if word.upper() in _ABBREVIATIONS:
            continue
        first = word[0]
        if first.isalpha() and not first.isupper():
            return True  # Sentence case detected (e.g. "Risk factors")
    return False


def _capitalize_word(word: str) -> str:
    """Capitalize a word, handling possessives like ``MANAGEMENT'S``."""
    if "'" in word:
        head, _, tail = word.partition("'")
        return head.capitalize() + "'" + tail.lower()
    return word.capitalize()


def _looks_like_title_case(text: str) -> bool:
    """Heuristic for the AMT dash-prefix branch — does ``text`` look like a title?"""
    words = text.split()
    if not words:
        return False
    for idx, word in enumerate(words):
        if not word:
            continue
        first = word[0]
        if idx == 0:
            if not first.isupper():
                return False
        elif word.lower() in _TITLE_CASE_SMALL_WORDS:
            continue
        elif not first.isupper():
            return False
    return True
