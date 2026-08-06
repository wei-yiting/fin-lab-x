"""Unit tests for the markdown H3/H4 block detection path (DEV-133).

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
        assert d.prelude == "Short framing prelude for every block below."
        assert all(FILLER.strip() in b.text for b in d.blocks)

    def test_item_self_heading_excluded_from_prelude(self):
        text = _item_text("Item 7A. Market Risk", "Overview", FILLER, "Rates", FILLER)
        c = HeadingCandidates(h3=("Overview", "Rates"), h4=())
        d = detect_blocks(text, c)
        assert d is not None
        assert d.prelude == ""

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
        # Every non-heading line of the item body must survive somewhere in
        # the chunkable content (leading block + named blocks).
        pseudo = "Swallowed body text. " * 300
        text = _item_text(pseudo, "Overview", LONG_BODY, "Competition", LONG_BODY)
        c = HeadingCandidates(h3=("Overview", "Competition"), h4=())
        d = detect_blocks(text, c)
        assert d is not None
        chunkable = "\n".join(
            part for b in d.blocks for part in (b.heading, b.text) if part
        )
        for line in text.splitlines():
            assert line.strip() in chunkable

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
        preserved = "\n".join(
            [d.prelude] + [part for b in d.blocks for part in (b.heading, b.text)]
        )
        for line in text.splitlines()[1:]:  # self-heading lives in title
            assert line.strip() in preserved
