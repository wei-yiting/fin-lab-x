"""Throwaway BDD verification script — Round 2, Phase 1 (targeted re-verification).

Re-executes ONLY S-fallback-03 and S-fallback-04 (all rows) from
artifacts/current/executable-verification.md against the current
block_detection.py, after:
  - commit 0a83ace added `_FALLBACK_DIGITS_ONLY_RE` (fixes S-fallback-04 row 2)
  - S-fallback-03 row 2's scenario expectation was revised (user ruling) from
    "accept" to "reject" — no code change for that row.

Constructions deliberately mirror artifacts/current/temp/test_verification_round1.py's
S-fallback-03/04 tests (same candidate strings, same surrounding-heading shape)
for direct round-over-round comparability, but are independent of, and
supplementary to, the two pinned regression tests added in the fix commit
(test_item_prefixed_title_rejection_pinned_current_behavior and
test_digits_and_whitespace_line_rejected in
backend/tests/ingestion/sec_text_pipeline/test_block_detection.py), which use
a different surrounding-heading shape ("Company Overview"/"(1)ppt" pattern).

Not part of the permanent test suite.

Run with:  PYTHONPATH=. pytest artifacts/current/temp/test_verification_round2.py -v
(PYTHONPATH=. is required because this file lives outside backend/ and has no
__init__.py chain back to the repo root for pytest's import rootdir
resolution — backend/tests/ itself does not need this.)
"""

from backend.ingestion.sec_text_pipeline.block_detection import (
    HeadingCandidates,
    detect_blocks,
)

NO_CANDIDATES = HeadingCandidates(h3=(), h4=())

FILLER = "Sufficiently long body prose line for the block. " * 4


def _fb_text(*parts: str) -> str:
    """Blank-line-separated Item text, matching test_block_detection.py's
    _fb_text helper (real 10-K plain-text rendering shape)."""
    return "\n\n".join(parts)


# ---------------------------------------------------------------------------
# S-fallback-03: Item self-reference format tolerance (3 rows)
# ---------------------------------------------------------------------------


def test_s_fallback_03_row1_allcaps_emdash_self_reference_rejected():
    candidate = "ITEM 1A—RISK FACTORS"
    text = _fb_text(
        "Item 1. Business", "Overview", FILLER, candidate, FILLER, "Competition", FILLER
    )
    d = detect_blocks(text, NO_CANDIDATES)
    assert d is not None
    headings = [b.heading for b in d.blocks]
    assert candidate not in headings, (
        f"expected REJECT (self-reference) but code ACCEPTED {candidate!r}; "
        f"headings={headings}"
    )
    assert headings == ["Overview", "Competition"]


def test_s_fallback_03_row2_item_prefixed_independent_heading_now_rejected():
    """Round 2: expectation revised (user ruling, not a code change) from
    PASS to REJECT. Round 1 found the code already rejects this candidate
    (prefix-match self-reference regex `^item\\s+\\d+[a-c]?\\.?` has no `$`
    anchor, so any line starting "Item 1A" is caught regardless of what
    follows). The scenario's expected result was revised to match — ratified
    as intentional fail-safe behavior in
    artifacts/current/temp/bdd-verification-round-1-resolutions.md.
    """
    candidate = "Item 1A Compliance Program"
    text = _fb_text(
        "Item 1. Business", "Overview", FILLER, candidate, FILLER, "Competition", FILLER
    )
    d = detect_blocks(text, NO_CANDIDATES)
    assert d is not None
    headings = [b.heading for b in d.blocks]
    assert candidate not in headings, (
        f"expected REJECT (Round 2 revised expectation) but code ACCEPTED "
        f"{candidate!r}; headings={headings}"
    )
    assert headings == ["Overview", "Competition"]


def test_s_fallback_03_row3_duplicate_self_reference_both_rejected():
    text = _fb_text(
        "Item 1. Business",
        "Item 1A",
        FILLER,
        "Overview",
        FILLER,
        "Item 1A",
        FILLER,
        "Competition",
        FILLER,
    )
    d = detect_blocks(text, NO_CANDIDATES)
    assert d is not None
    headings = [b.heading for b in d.blocks]
    assert headings.count("Item 1A") == 0
    assert headings == ["Overview", "Competition"]
    all_text = d.prelude + "".join(f"\n{b.heading}\n{b.text}" for b in d.blocks)
    assert all_text.count("Item 1A") == 2, "both literal occurrences must survive"


# ---------------------------------------------------------------------------
# S-fallback-04: flattened-table numeric residue must not be misread as
# heading (2 rows)
# ---------------------------------------------------------------------------


def test_s_fallback_04_row1_comma_thousands_rejected():
    candidate = "Approximately 1,000 Employees Worldwide"
    text = _fb_text(
        "Item 1. Business", "Overview", FILLER, candidate, FILLER, "Competition", FILLER
    )
    d = detect_blocks(text, NO_CANDIDATES)
    assert d is not None
    headings = [b.heading for b in d.blocks]
    assert candidate not in headings, (
        f"expected REJECT (digit cluster '000' after comma) but code "
        f"ACCEPTED {candidate!r}; headings={headings}"
    )
    assert headings == ["Overview", "Competition"]


def test_s_fallback_04_row2_space_separated_short_digit_groups_rejected():
    """Round 2: re-verify after the _FALLBACK_DIGITS_ONLY_RE fix (commit
    0a83ace). Round 1 found the code ACCEPTED this candidate (spaces defeat
    isdigit(), and each 2-digit group is too short for the 3-digit cluster
    rule)."""
    candidate = "12  34  56  78"
    text = _fb_text(
        "Item 1. Business", "Overview", FILLER, candidate, FILLER, "Competition", FILLER
    )
    d = detect_blocks(text, NO_CANDIDATES)
    assert d is not None
    headings = [b.heading for b in d.blocks]
    assert candidate not in headings, (
        f"expected REJECT but code ACCEPTED {candidate!r}; headings={headings}"
    )
    assert headings == ["Overview", "Competition"]
