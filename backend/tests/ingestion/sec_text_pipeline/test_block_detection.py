"""Unit tests for the block detection chain (markdown H3/H4 + text fallback).

External behavior only: canonicalize is the shared anchoring/scorer helper
(a public seam in its own right), candidate collection and detection are
asserted through their returned structures.
"""

from backend.ingestion.sec_text_pipeline.block_detection import (
    PRELUDE_VALIDITY_CHARS,
    HeadingCandidates,
    canonicalize,
    collect_heading_candidates,
    detect_blocks,
)
from backend.tests.ingestion.sec_text_pipeline.conftest import assert_tiles


class TestCanonicalize:
    def test_curly_quotes_unified(self):
        assert canonicalize("The Company’s “Strategy”") == 'The Company\'s "Strategy"'

    def test_dash_variants_unified(self):
        assert canonicalize("Risk – Market — Credit") == "Risk - Market - Credit"

    def test_whitespace_collapsed_and_stripped(self):
        assert canonicalize("  Human Capital\t\tResources ") == (
            "Human Capital Resources"
        )

    def test_nfkc_normalization(self):
        # Fullwidth and ligature forms fold to their plain equivalents.
        assert canonicalize("Ｏﬃce Ｄepot") == "Office Depot"

    def test_case_is_preserved(self):
        # Anchoring is deliberately case-sensitive: folding case widens the
        # net toward false anchors (worse than a miss).
        assert canonicalize("OVERVIEW") != canonicalize("Overview")


class TestCollectHeadingCandidates:
    def test_levels_split_and_order_preserved(self):
        md = "### Alpha\nbody\n#### Sub One\n### Beta\n#### Sub Two\n## Ignored H2\n"
        c = collect_heading_candidates(md, "Example Corp.")
        assert c.h3 == ("Alpha", "Beta")
        assert c.h4 == ("Sub One", "Sub Two")

    def test_literal_blacklist_filtered(self):
        md = "### TABLE OF CONTENTS\n### FORM 10-K\n### Human Capital\n"
        c = collect_heading_candidates(md, "Example Corp.")
        assert c.h3 == ("Human Capital",)

    def test_literal_blacklist_matches_canonical_variants(self):
        # A curly-dash / doubled-space variant of a blacklisted literal must
        # not slip past the filter — literals match on the canonical form.
        md = "### FORWARD–LOOKING  STATEMENTS\n### Human Capital\n"
        c = collect_heading_candidates(md, "Example Corp.")
        assert c.h3 == ("Human Capital",)

    def test_literal_blacklist_matches_casing_variants(self):
        # Recorded JPM reality: "Table of contents" (lowercase c) appears
        # once — below the repeat threshold — so only casefolded literal
        # matching keeps it out of the candidates.
        md = "### Table of contents\n### Signatures\n### Human Capital\n"
        c = collect_heading_candidates(md, "Example Corp.")
        assert c.h3 == ("Human Capital",)

    def test_chapter_divider_filtered(self):
        md = "### PART I\n### PART II\n### part iv\n### Competition\n"
        c = collect_heading_candidates(md, "Example Corp.")
        assert c.h3 == ("Competition",)

    def test_item_heading_filtered(self):
        md = "### Item 1A. Risk Factors\n### Competition\n"
        c = collect_heading_candidates(md, "Example Corp.")
        assert c.h3 == ("Competition",)

    def test_registrant_name_filtered_case_insensitive(self):
        md = "### CATERPILLAR INC.\n### Caterpillar Inc.\n### Raw Materials\n"
        c = collect_heading_candidates(md, "Caterpillar Inc.")
        assert c.h3 == ("Raw Materials",)

    def test_repeated_heading_is_noise_across_levels(self):
        # A running header repeating >= 4 times across the whole filing is
        # noise even when its occurrences straddle heading levels.
        md = (
            "### 2025 Annual Review\n#### 2025 Annual Review\n"
            "### 2025 Annual Review\n#### 2025 Annual Review\n"
            "### Competition\n#### Pricing\n"
        )
        c = collect_heading_candidates(md, "Example Corp.")
        assert c.h3 == ("Competition",)
        assert c.h4 == ("Pricing",)

    def test_three_repeats_survive(self):
        md = "### Overview One\n" + "### Recurring\n" * 3
        c = collect_heading_candidates(md, "Example Corp.")
        assert "Recurring" in c.h3

    def test_duplicates_deduped_order_preserving(self):
        md = "### Alpha\n### Beta\n### Alpha\n"
        c = collect_heading_candidates(md, "Example Corp.")
        assert c.h3 == ("Alpha", "Beta")

    def test_empty_markdown_yields_no_candidates(self):
        c = collect_heading_candidates("", "Example Corp.")
        assert c == HeadingCandidates(h3=(), h4=())


def _item_text(*parts: str) -> str:
    return "\n".join(parts)


FILLER = "Sufficiently long body prose line for the block. " * 4


class TestDetectBlocks:
    def test_h3_anchoring_produces_blocks_and_prelude(self):
        text = _item_text(
            "Item 1. Business",
            "Short framing prelude for every block below.",
            "Overview",
            FILLER,
            "Competition",
            FILLER,
        )
        c = HeadingCandidates(h3=("Overview", "Competition"), h4=())
        d = detect_blocks(text, c)
        assert d is not None
        assert d.detection_source == "markdown_h3"
        assert [b.heading for b in d.blocks] == ["Overview", "Competition"]
        # The prelude is verbatim text before the first anchor — the Item's
        # own heading line stays in it (harmless repetition of title; spec
        # defines prelude with no carve-outs).
        assert d.prelude == (
            "Item 1. Business\nShort framing prelude for every block below."
        )
        assert all(FILLER.strip() in b.text for b in d.blocks)

    def test_prelude_is_verbatim_including_self_heading_line(self):
        text = _item_text("Item 7A. Market Risk", "Overview", FILLER, "Rates", FILLER)
        c = HeadingCandidates(h3=("Overview", "Rates"), h4=())
        d = detect_blocks(text, c)
        assert d is not None
        assert d.prelude == "Item 7A. Market Risk"

    def test_h3_preferred_over_h4(self):
        text = _item_text("Overview", FILLER, "Competition", FILLER)
        c = HeadingCandidates(
            h3=("Overview", "Competition"), h4=("Overview", "Competition")
        )
        d = detect_blocks(text, c)
        assert d is not None
        assert d.detection_source == "markdown_h3"

    def test_h4_used_when_h3_implausible(self):
        text = _item_text("Overview", FILLER, "Competition", FILLER)
        c = HeadingCandidates(h3=("Unrelated H3",), h4=("Overview", "Competition"))
        d = detect_blocks(text, c)
        assert d is not None
        assert d.detection_source == "markdown_h4"

    def test_single_anchor_is_implausible(self):
        # A lone anchored heading must not be trusted (< 2 anchors).
        text = _item_text("Overview", FILLER, FILLER, FILLER)
        c = HeadingCandidates(h3=("Overview",), h4=())
        assert detect_blocks(text, c) is None

    def test_single_deep_heading_is_implausible(self):
        # The 72-probe disaster shape: one stray heading deep in the Item
        # would swallow everything before it as "prelude". Two anchors but
        # the first sits far past the 30% mark -> untrusted.
        body = FILLER * 30
        text = _item_text(body, "Miscellaneous", FILLER, "Other Matters", FILLER)
        c = HeadingCandidates(h3=("Miscellaneous", "Other Matters"), h4=())
        assert detect_blocks(text, c) is None

    def test_anchoring_matches_canonicalized_lines(self):
        # Candidate uses curly quotes/em-dash; body line uses straight
        # ASCII with doubled spaces. Both canonicalize to the same form.
        text = _item_text(
            'The Company\'s "Strategy" - Overview',
            FILLER,
            "Competition",
            FILLER,
        )
        c = HeadingCandidates(
            h3=("The Company’s “Strategy” — Overview", "Competition"), h4=()
        )
        d = detect_blocks(text, c)
        assert d is not None
        assert d.blocks[0].heading == 'The Company\'s "Strategy" - Overview'

    def test_no_candidates_yields_none(self):
        assert detect_blocks(FILLER, HeadingCandidates(h3=(), h4=())) is None


#: Long block bodies keep the first anchor inside the 30% plausibility
#: window even when a sizable prelude precedes it (matching the real
#: proportions of the probe cases these tests model).
LONG_BODY = FILLER * 50


class TestPreludeValidity:
    def test_prelude_at_threshold_attached_whole_untruncated(self):
        prelude = "P" * PRELUDE_VALIDITY_CHARS
        text = _item_text(prelude, "Overview", LONG_BODY, "Competition", LONG_BODY)
        c = HeadingCandidates(h3=("Overview", "Competition"), h4=())
        d = detect_blocks(text, c)
        assert d is not None
        assert d.prelude == prelude  # attached whole, never truncated
        assert [b.heading for b in d.blocks] == ["Overview", "Competition"]

    def test_oversized_prelude_reclassified_as_leading_block(self):
        pseudo = "Swallowed body text. " * 300  # > 3,000 chars
        text = _item_text(pseudo, "Overview", LONG_BODY, "Competition", LONG_BODY)
        c = HeadingCandidates(h3=("Overview", "Competition"), h4=())
        d = detect_blocks(text, c)
        assert d is not None
        assert d.prelude == ""  # not a prelude
        assert d.blocks[0].heading == ""  # heading-less leading block
        assert d.blocks[0].text == pseudo.strip()

    def test_zero_content_loss_on_reclassify(self):
        # The reclassified leading block plus the named blocks must tile the
        # entire item body in order — a dropped block cannot hide behind an
        # identical copy of its text elsewhere (the block bodies here are
        # deliberately identical to make that failure mode detectable).
        pseudo = "Swallowed body text. " * 300
        text = _item_text(pseudo, "Overview", LONG_BODY, "Competition", LONG_BODY)
        c = HeadingCandidates(h3=("Overview", "Competition"), h4=())
        d = detect_blocks(text, c)
        assert d is not None
        assert_tiles(d.prelude, d.blocks, text)

    def test_zero_content_loss_on_valid_prelude(self):
        text = _item_text(
            "Item 1. Business",
            "Framing text ahead of all blocks.",
            "Overview",
            FILLER,
            "Competition",
            FILLER,
        )
        c = HeadingCandidates(h3=("Overview", "Competition"), h4=())
        d = detect_blocks(text, c)
        assert d is not None
        assert_tiles(d.prelude, d.blocks, text)


NO_CANDIDATES = HeadingCandidates(h3=(), h4=())


def _fb_text(*parts: str) -> str:
    """Item text whose headings are separated from prose by blank lines,
    as real 10-K plain-text renderings are — the fallback's previous-line
    signal (must not end a sentence) depends on that shape."""
    return "\n\n".join(parts)


class TestTextFallback:
    """The third detection path: Title-Case standalone-line detection.

    Reference behavior is the 72-probe-validated fallback (design §4.5);
    each rejection rule gets a positive/negative pair through the public
    detect_blocks seam.
    """

    def test_fallback_detects_standalone_heading_lines(self):
        text = _fb_text(
            "Item 1. Business",
            "Company Overview",
            FILLER,
            "Human Capital Resources",
            FILLER,
        )
        d = detect_blocks(text, NO_CANDIDATES)
        assert d is not None
        assert d.detection_source == "text_fallback"
        assert [b.heading for b in d.blocks] == [
            "Company Overview",
            "Human Capital Resources",
        ]
        assert d.prelude == "Item 1. Business"

    def test_markdown_path_preferred_over_fallback(self):
        # Both paths would anchor plausibly; the markdown result must win.
        text = _fb_text("Company Overview", FILLER, "Competition", FILLER)
        c = HeadingCandidates(h3=("Company Overview", "Competition"), h4=())
        d = detect_blocks(text, c)
        assert d is not None
        assert d.detection_source == "markdown_h3"

    def test_demoted_markdown_falls_through_to_fallback(self):
        # Markdown candidates anchor but implausibly (single anchor):
        # the chain must demote to the fallback, not give up.
        text = _fb_text("Company Overview", FILLER, "Competition", FILLER)
        c = HeadingCandidates(h3=("Competition",), h4=())
        d = detect_blocks(text, c)
        assert d is not None
        assert d.detection_source == "text_fallback"
        assert [b.heading for b in d.blocks] == ["Company Overview", "Competition"]

    def test_unstructured_text_stays_flat(self):
        # The GE 1A shape: long prose with no heading-shaped lines. The
        # fallback must not invent headings — detect_blocks yields None.
        text = _fb_text(*[FILLER for _ in range(20)])
        assert detect_blocks(text, NO_CANDIDATES) is None

    def test_length_window_rejects_short_and_long_lines(self):
        too_short = "Ops"
        too_long = "X" + "very long pseudo heading " * 5  # > 120 chars
        text = _fb_text(too_short, FILLER, too_long, FILLER)
        assert detect_blocks(text, NO_CANDIDATES) is None

    def test_digit_cluster_and_pure_number_rejected(self):
        # The VZ-style year-label failure shape: "2025" is a standalone
        # short line, and digit clusters mark table fragments.
        text = _fb_text("2025", FILLER, "Revenue in 2024 dollars", FILLER)
        assert detect_blocks(text, NO_CANDIDATES) is None

    def test_item_self_reference_rejected_as_candidate(self):
        # The Item's own heading line must not become a block anchor —
        # but it still lands in the verbatim prelude (no carve-outs).
        text = _fb_text(
            "Item 7A. Market Risk",
            "ITEM 7A. QUANTITATIVE DISCLOSURES",
            "Interest Rate Risk",
            FILLER,
            "Currency Exchange Risk",
            FILLER,
        )
        d = detect_blocks(text, NO_CANDIDATES)
        assert d is not None
        assert [b.heading for b in d.blocks] == [
            "Interest Rate Risk",
            "Currency Exchange Risk",
        ]
        assert d.prelude == (
            "Item 7A. Market Risk\n\nITEM 7A. QUANTITATIVE DISCLOSURES"
        )

    def test_footnote_label_rejected_but_real_heading_anchors(self):
        # The MSFT Item 7 table-footnote shape: "(1)ppt" is a standalone
        # short line that passes every other gate, but a parenthesized
        # footnote label at line start is never a heading (M-1.1).
        text = _fb_text(
            "Company Overview",
            FILLER,
            "(1)ppt",
            FILLER,
            "Competition",
            FILLER,
        )
        d = detect_blocks(text, NO_CANDIDATES)
        assert d is not None
        assert d.detection_source == "text_fallback"
        assert [b.heading for b in d.blocks] == [
            "Company Overview",
            "Competition",
        ]

    def test_table_characters_rejected(self):
        text = _fb_text(
            "Revenue | Cost | Margin",
            FILLER,
            "Growth of 5% annually",
            FILLER,
            "Cash of $10 million",
            FILLER,
        )
        assert detect_blocks(text, NO_CANDIDATES) is None

    def test_trailing_punctuation_rejected(self):
        text = _fb_text(
            "The factors are these:",
            FILLER,
            "A sentence fragment,",
            FILLER,
            "It was short.",
            FILLER,
        )
        assert detect_blocks(text, NO_CANDIDATES) is None

    def test_candidate_after_sentence_end_rejected(self):
        # Same candidate lines, but glued directly under a line that ends a
        # sentence — the previous-line signal must reject them.
        text = "\n".join(
            [
                "Some prose that ends the paragraph here.",
                "Company Overview",
                FILLER,
                "Short prose also ending in a period.",
                "Competition",
                FILLER,
            ]
        )
        assert detect_blocks(text, NO_CANDIDATES) is None

    def test_candidate_without_following_prose_rejected(self):
        # A heading-shaped line followed only by short fragments is a list
        # entry or table label, not a block heading.
        text = _fb_text(
            "Company Overview",
            "short line",
            "Competition Landscape",
            "another short line",
        )
        assert detect_blocks(text, NO_CANDIDATES) is None

    def test_plausibility_gate_applies_to_fallback(self):
        # Two valid candidates whose first sits past the 30% mark: the
        # fallback result is just as untrusted as a markdown one would be.
        long_head = _fb_text(*[FILLER for _ in range(20)])
        text = _fb_text(
            long_head,
            "Company Overview",
            FILLER,
            "Competition",
            FILLER,
        )
        assert detect_blocks(text, NO_CANDIDATES) is None

    def test_prelude_validity_applies_to_fallback(self):
        # An oversized pre-anchor span reclassifies as a heading-less
        # leading block on the fallback path too.
        pseudo = "Swallowed body text " * 200  # > 3,000 chars, no periods
        text = _fb_text(
            pseudo,
            "Company Overview",
            LONG_BODY,
            "Competition",
            LONG_BODY,
        )
        d = detect_blocks(text, NO_CANDIDATES)
        assert d is not None
        assert d.detection_source == "text_fallback"
        assert d.prelude == ""
        assert d.blocks[0].heading == ""
        assert d.blocks[0].text == pseudo.strip()

    def test_zero_content_loss_via_fallback(self):
        text = _fb_text(
            "Item 1. Business",
            "Company Overview",
            FILLER,
            "Competition",
            FILLER,
        )
        d = detect_blocks(text, NO_CANDIDATES)
        assert d is not None
        assert_tiles(d.prelude, d.blocks, text)
