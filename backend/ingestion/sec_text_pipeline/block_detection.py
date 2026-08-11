"""Markdown H3/H4 block detection for the SEC text pipeline.

The filing-level markdown (edgartools ``filing.markdown()``) supplies H3/H4
heading candidates; each Item's plain-text body is then searched for lines
that exactly equal a candidate after both sides pass the same
:func:`canonicalize`. An anchored result is only trusted if it passes the
plausibility check — otherwise this path yields nothing and the Item stays
flat (the Title-Case text fallback is a separate, later detection path).

Prelude semantics: the text before the first anchored heading is a
valid prelude only when it is short enough to plausibly be framing text
(<= :data:`PRELUDE_VALIDITY_CHARS`); it is then attached whole, never
truncated. Anything larger is body text swallowed by a detection miss, so
it is reclassified as a heading-less leading block and stays in the
chunkable content — zero content loss in either branch.

All thresholds and noise lists are deliberately hardcoded module-level
constants (config indirection waits for real churn).
"""

from __future__ import annotations

import re
import unicodedata
from collections import Counter
from dataclasses import dataclass
from typing import Literal

from backend.ingestion.sec_text_pipeline.filing_models import Block

# --- tuning constants (72-probe validated; evidence recorded in the DEV-127
# spec's prelude section) -----------------------------------------------------

#: <= this many chars before the first heading: valid prelude, attached whole.
#: Larger: not a prelude — reclassified as a heading-less leading block.
PRELUDE_VALIDITY_CHARS = 3000
#: An anchored markdown result is plausible only with at least this many
#: anchored headings...
PLAUSIBILITY_MIN_ANCHORS = 2
#: ...and the first anchor within this fraction of the Item's text. A lone
#: (or late-starting) match is a stray miscellaneous heading that would
#: swallow most of the Item into its "prelude".
PLAUSIBILITY_MAX_FIRST_POS = 0.30
#: A heading text recurring at least this often across the whole filing's
#: markdown is running-header noise (company name, "Table of Contents", ...).
HEADING_REPEAT_NOISE_THRESHOLD = 4

# --- noise filter (literal blacklist + patterns), hardcoded by design -------

#: Compared casefolded — one entry covers every casing variant of a heading.
NOISE_HEADING_LITERALS: frozenset[str] = frozenset(
    {
        "TABLE OF CONTENTS",
        "FORM 10-K",
        "FORWARD-LOOKING STATEMENTS",
        "FORWARD-LOOKING INFORMATION",
        "Cautionary Note About Forward-Looking Statements",
        "Cautionary Note on Forward-Looking Statements",
        "DOCUMENTS INCORPORATED BY REFERENCE",
        "SIGNATURES",
        "POWER OF ATTORNEY",
        "AVAILABLE INFORMATION",
        "UNITED STATES",
        "SECURITIES AND EXCHANGE COMMISSION",
        "Washington, D.C. 20549",
        "•",
        "or",
    }
)

#: Chapter dividers ("PART I".."PART IV") plus other non-content heading
#: shapes observed across the 72-probe sample.
NOISE_HEADING_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"^PART\s+[IVX]+$", re.IGNORECASE),
    re.compile(r"^\d+$"),
    re.compile(r"^[•\-]+$"),
    re.compile(r"^Commission File", re.IGNORECASE),
    re.compile(r"^For the (fiscal year|transition period)", re.IGNORECASE),
    re.compile(r"^\d{4}\s+(annual|form\s*10[-\s]?k|annual report)", re.IGNORECASE),
    re.compile(r"^Item\s+\d+[a-c]?\b", re.IGNORECASE),
    re.compile(r"^[A-Z\s.,&]+(?:INC|CORP|CORPORATION|COMPANY|LLC|LP)\.?$"),
    re.compile(r"^Index to", re.IGNORECASE),
    re.compile(r"^Notes to (the )?consolidated financial statements", re.IGNORECASE),
    re.compile(r"^Consolidated Statements? of", re.IGNORECASE),
    re.compile(r"^Consolidated Balance Sheets?", re.IGNORECASE),
    re.compile(r"^Report of Independent", re.IGNORECASE),
)

_MD_HEADING_RE = re.compile(r"^(#{1,6}) (.+)$")


def canonicalize(text: str) -> str:
    """Normalize a line for exact-equality anchoring (both sides pass this).

    NFKC + curly-quote/dash unification + whitespace collapse + strip.
    Comparison stays case-sensitive: real headings reproduce their markdown
    form verbatim, and case-folding would widen the net toward the
    false-anchor failure mode (anchoring a prose line is worse than a miss).
    Shared with the A/B scorer's snippet normalization.
    """
    text = unicodedata.normalize("NFKC", text)
    text = text.replace("‘", "'").replace("’", "'")
    text = text.replace("“", '"').replace("”", '"')
    text = text.replace("–", "-").replace("—", "-")
    return re.sub(r"\s+", " ", text).strip()


@dataclass(frozen=True)
class HeadingCandidates:
    """Noise-filtered, order-preserving H3/H4 heading texts of one filing."""

    h3: tuple[str, ...]
    h4: tuple[str, ...]


_NOISE_LITERALS_CANON: frozenset[str] = frozenset(
    canonicalize(literal).casefold() for literal in NOISE_HEADING_LITERALS
)


def _is_noise_heading(
    heading: str,
    registrant_canon: str,
    repeat_counts: Counter[str],
) -> bool:
    """Noise checks compare casefolded canonical forms: "Table of contents"
    is the same running-header noise as "TABLE OF CONTENTS". Item-body
    anchoring deliberately stays case-sensitive — the looser folding is
    safe here because a wrongly-dropped candidate costs a miss, never a
    false anchor."""
    stripped = heading.strip()
    if not stripped:
        return True
    canon_fold = canonicalize(stripped).casefold()
    if canon_fold in _NOISE_LITERALS_CANON:
        return True
    if any(p.match(stripped) for p in NOISE_HEADING_PATTERNS):
        return True
    if registrant_canon and canon_fold == registrant_canon:
        return True
    return repeat_counts[canon_fold] >= HEADING_REPEAT_NOISE_THRESHOLD


def collect_heading_candidates(
    markdown: str, registrant_name: str
) -> HeadingCandidates:
    """Extract noise-filtered H3/H4 candidates from filing-level markdown.

    Repetition is counted across ALL heading levels of the whole filing
    before filtering, so a running header that renders at varying levels
    still trips :data:`HEADING_REPEAT_NOISE_THRESHOLD`. Duplicates are
    dropped order-preserving; anchoring is set-membership so order only
    aids inspectability.
    """
    by_level: dict[int, list[str]] = {}
    repeat_counts: Counter[str] = Counter()
    for line in markdown.splitlines():
        m = _MD_HEADING_RE.match(line)
        if not m:
            continue
        level, text = len(m.group(1)), m.group(2).strip()
        by_level.setdefault(level, []).append(text)
        repeat_counts[canonicalize(text).casefold()] += 1

    registrant_canon = canonicalize(registrant_name).casefold()

    def clean(level: int) -> tuple[str, ...]:
        kept = [
            h
            for h in by_level.get(level, [])
            if not _is_noise_heading(h, registrant_canon, repeat_counts)
        ]
        return tuple(dict.fromkeys(kept))

    return HeadingCandidates(h3=clean(3), h4=clean(4))


@dataclass(frozen=True)
class DetectedBlocks:
    """A trusted (plausibility-passing) markdown detection result."""

    detection_source: Literal["markdown_h3", "markdown_h4"]
    prelude: str  # "" = no prelude (absent, or reclassified as leading block)
    blocks: list[Block]


def detect_blocks(
    item_text: str, candidates: HeadingCandidates
) -> DetectedBlocks | None:
    """Run the markdown detection path (H3 first, then H4) on one Item body.

    Returns ``None`` when neither level anchors plausibly — the caller
    keeps the Item flat. Never returns an implausible anchoring: a single
    deep stray heading must not swallow the Item's body into its prelude.
    """
    lines = item_text.splitlines()
    lines_canon = [canonicalize(line) for line in lines]
    offsets: list[int] = []
    pos = 0
    for line in lines:
        offsets.append(pos)
        pos += len(line) + 1

    attempts: tuple[tuple[Literal["markdown_h3", "markdown_h4"], tuple[str, ...]], ...]
    attempts = (
        ("markdown_h3", candidates.h3),
        ("markdown_h4", candidates.h4),
    )
    for source, level_candidates in attempts:
        targets = {canonicalize(c) for c in level_candidates}
        anchor_idxs = [
            i for i, canon in enumerate(lines_canon) if canon and canon in targets
        ]
        if _is_plausible(anchor_idxs, offsets, len(item_text)):
            return _assemble(source, lines, anchor_idxs)
    return None


def _is_plausible(anchor_idxs: list[int], offsets: list[int], total_chars: int) -> bool:
    if len(anchor_idxs) < PLAUSIBILITY_MIN_ANCHORS:
        return False
    return offsets[anchor_idxs[0]] <= PLAUSIBILITY_MAX_FIRST_POS * total_chars


def _assemble(
    source: Literal["markdown_h3", "markdown_h4"],
    lines: list[str],
    anchor_idxs: list[int],
) -> DetectedBlocks:
    blocks: list[Block] = []
    for n, idx in enumerate(anchor_idxs):
        end = anchor_idxs[n + 1] if n + 1 < len(anchor_idxs) else len(lines)
        blocks.append(
            Block(
                heading=lines[idx].strip(),
                text="\n".join(lines[idx + 1 : end]).strip(),
            )
        )

    # The prelude is the verbatim text before the first anchor — no carve-outs.
    # The Item's own heading line stays in it when present: harmless repetition
    # of StructuredItem.title, and dropping lines is what zero-content-loss
    # forbids (spec defines prelude with no exclusions).
    prelude_raw = "\n".join(lines[: anchor_idxs[0]]).strip()

    if len(prelude_raw) > PRELUDE_VALIDITY_CHARS:
        # Not a prelude — body text swallowed by a detection miss. Keep it
        # chunkable as a heading-less leading block; prelude metadata empty.
        blocks.insert(0, Block(heading="", text=prelude_raw))
        prelude_raw = ""
    return DetectedBlocks(detection_source=source, prelude=prelude_raw, blocks=blocks)
