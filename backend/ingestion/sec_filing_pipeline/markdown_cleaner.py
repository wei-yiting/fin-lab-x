"""Strip 10-K boilerplate and normalize Part / Item headings.

Operates on the markdown output of the html→markdown converter to remove
content with zero RAG value (cover pages, page separators, Part III stubs
that are pure references to the Proxy Statement) and to normalize
inconsistent Item / Part heading formats produced by SEC EDGAR.

Designed conservatively: every rule prefers leaving noise over risking
deletion of real content. Once content is dropped from the cleaned
markdown it cannot be recovered downstream.

Wired into ``SECFilingPipeline._process_internal`` as the step
immediately after ``convert_with_fallback()``.
"""

from __future__ import annotations

import logging
import re

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Cover page anchors
# ---------------------------------------------------------------------------

_PART_I_ANCHOR_RE = re.compile(r"^# (?:PART|Part) I\b", re.MULTILINE)
_ITEM_1_ANCHOR_RE = re.compile(r"^## (?:ITEM|Item) 1\b", re.MULTILINE)


# ---------------------------------------------------------------------------
# Page separator
# ---------------------------------------------------------------------------

# Match: empty-or-numeric line + bare `---` line + optional TOC link line.
# Markdown table separators (`| --- | --- |`) are pipe-flanked and never
# match this pattern. The trailing newlines are ``(?:\n|\Z)`` so the
# separator still strips when it sits at end-of-file without a final
# newline (``81\n---`` or ``81\n---\n[Table of Contents](#x)`` at EOF).
_PAGE_SEP_RE = re.compile(
    r"^[ \t]*\d*[ \t]*\n"
    r"---[ \t]*(?:\n|\Z)"
    r"(?:\[Table of Contents\]\([^)]+\)[ \t]*(?:\n|\Z))?",
    re.MULTILINE,
)


# ---------------------------------------------------------------------------
# Part III stub
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

# Approximate sentence boundary — split on sentence-ending punctuation
# followed by whitespace + any non-whitespace char (letter, digit,
# quote, paren, etc.). Over-splitting is harmless (e.g. ``Mr. Smith``
# → two halves, neither contains the ref phrase, both kept and joined
# back into the remainder). Under-splitting was the real bug: a
# narrower splitter like ``(?=[A-Z])`` silently glues the next real
# sentence onto the ref sentence when it starts with a digit
# (``2025 saw growth...``), a quote (``"Executive..."``), or a paren
# (``(See Item 11...)``), causing the whole chunk to be dropped as
# part of the ref sentence — that violates the "prefer noise over
# deletion" principle.
_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+(?=\S)")

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

# Bare Item heading with no inline title — used by split-title merge to look at the
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
    # Cover page stripping
    # ------------------------------------------------------------------

    def _strip_cover_page(self, markdown: str) -> str:
        """Remove boilerplate between the document start and the first Part I.

        Production contract: the cleaner runs on raw converter output,
        which has no YAML frontmatter (``HtmlToMarkdownAdapter.convert``
        strips any leading frontmatter). Frontmatter is only attached
        later by ``LocalFilingStore.save()``. This method therefore
        operates on the plain markdown body by default.

        Defensively, the method still handles the stored-file shape
        (leading ``---\\n...\\n---\\n`` frontmatter) so it stays robust
        when called from tests or downstream re-processing. In that
        case the frontmatter block is preserved verbatim and the anchor
        search runs against the body portion only.

        Anchor logic:

        1. Primary: first ``# Part I`` (case-insensitive keyword).
        2. Fallback: first ``## Item 1`` (BAC, JNJ have no Part heading
           at all but do have Item 1).
        3. Neither found (GE 2008, INTC 2025, BRK.B 2025 — non-standard
           formats) → log warning, pass through unchanged. The
           conservative principle wins: prefer leaving boilerplate over
           risking deletion of real content.
        """
        prefix = ""
        body = markdown

        if markdown.startswith("---\n"):
            fm_end = markdown.find("\n---\n", 4)
            if fm_end != -1:
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
    # Page separator stripping
    # ------------------------------------------------------------------

    def _strip_page_separators(self, markdown: str) -> str:
        """Remove standalone ``---`` page separators with optional TOC link.

        The regex requires the ``---`` line to be bare (not pipe-flanked)
        and the previous line to be empty or all-digits, so markdown
        table separators (``| --- | --- |``) are never matched.
        """
        return _PAGE_SEP_RE.sub("", markdown)

    # ------------------------------------------------------------------
    # Part III stub stripping
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

            section_end = _find_next_heading(markdown, heading_line_end + 1)
            section_body = markdown[heading_line_end + 1 : section_end]

            body_stripped = section_body.strip()
            if not body_stripped or (
                _INCORP_BY_REF_RE.search(section_body)
                and is_pure_part_iii_stub(section_body)
            ):
                result_parts.append(markdown[last_end:heading_start])
                last_end = section_end
            # Hybrid / real content (or short section with no ref phrase):
            # leave the section in place by not advancing last_end.

        result_parts.append(markdown[last_end:])
        return "".join(result_parts)

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
        """Pull AMZN-style and AMT-style next-line titles into the heading.

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
        code block, a markdown table, a bullet/plain line that doesn't
        look like a title, or otherwise ordinary body prose.

        Both branches (AMZN plain-text, AMT ``- `` bullet prefix) require
        the content to look like a title — ALL CAPS or Title Case — so
        that body prose such as ``The company operates in multiple
        segments and ...`` is never merged into a heading.
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

        # AMZN branch: plain text — require ALL CAPS or Title Case so
        # ordinary body prose (``The company operates in ...``) never
        # gets merged into a heading. This matches the dash-prefix
        # branch's safety contract.
        if stripped.isupper() or _looks_like_title_case(stripped):
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

        # Defensive: log if heading title is suspiciously short.
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


def _find_next_heading(markdown: str, start: int) -> int:
    """Return the index of the next ``^#{1,2} `` heading after ``start``, or end-of-string."""
    match = _NEXT_HEADING_RE.search(markdown, start)
    if match is None:
        return len(markdown)
    return match.start()


def is_pure_part_iii_stub(section_body: str) -> bool:
    """Decide whether a Part III item section body is a pure ref-to-Proxy stub.

    Exported at module level so both :class:`MarkdownCleaner` and the
    ``validate_sec_md_cleanup`` script share the exact same decision
    rule — otherwise the validator silently drifts from production
    semantics and reports bad stub/real counts.

    Splits on approximate sentence boundaries, drops sentences that
    contain the incorporated-by-reference pattern, strips markdown
    link/image syntax (filenames and URLs are not prose), then counts
    non-whitespace, non-structural chars. Below the threshold ⇒ pure
    stub.

    Naive sentence splitting is fine because the split is only used to
    identify which sentences to drop; kept sentences still contribute
    their full character count toward the preservation decision.
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


def _capitalize_word(word: str) -> str:
    """Capitalize a word, handling possessives and hyphenated tokens.

    - Possessives (``MANAGEMENT'S`` → ``Management's``): split on the
      first apostrophe, capitalize the head, lowercase the tail.
    - Hyphenated tokens (``10-K`` → ``10-K``, ``ALL-CAPS-TITLE`` →
      ``All-Caps-Title``): split on ``-``, capitalize each segment,
      rejoin. Without this, ``str.capitalize()`` lowercases everything
      after the first character and corrupts canonical SEC terms like
      ``10-K`` into ``10-k``.
    """
    if "'" in word:
        head, _, tail = word.partition("'")
        return _capitalize_word(head) + "'" + tail.lower()
    if "-" in word:
        return "-".join(segment.capitalize() for segment in word.split("-"))
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
