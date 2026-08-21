"""Direct unit tests for the degraded-ingest noise-cleaning rules.

Rule-by-rule positive/negative cases (DEV-172 testing decision #2; prior
art: the trim-section tests in test_parser.py). Shapes mirror the real
edgartools filing-level markdown render — see AMD FY2025, where the cover
page runs until "#### INDEX", the body starts at "# PART I", and the
signature block opens with "### SIGNATURES".
"""

from backend.ingestion.sec_text_pipeline.degraded import (
    _collapse_blank_lines,
    _strip_cover_and_toc,
    _strip_page_artifacts,
    _strip_signatures,
    clean_degraded_markdown,
)


class TestStripCoverAndToc:
    def test_content_before_first_part_heading_is_cut(self):
        text = (
            "### UNITED STATES SECURITIES AND EXCHANGE COMMISSION\n"
            "#### FORM 10-K\n"
            "#### INDEX\n"
            "| ITEM 1. |     | Business |     | 1 |\n"
            "# PART I\n"
            "## ITEM 1.\n"
            "Real business discussion.\n"
        )
        cleaned = _strip_cover_and_toc(text)
        assert cleaned.startswith("# PART I")
        assert "FORM 10-K" not in cleaned
        assert "INDEX" not in cleaned
        assert "Real business discussion." in cleaned

    def test_no_part_heading_leaves_text_unchanged(self):
        # Conservative: with no recognizable body start, keep everything —
        # leftover noise is acceptable, deleted content is not.
        text = "Some document without any part headings.\nMore text.\n"
        assert _strip_cover_and_toc(text) == text

    def test_part_mention_in_prose_is_not_a_cut_point(self):
        text = (
            "The registrant discusses PART I obligations in prose here.\n"
            "See PART II of this report for details.\n"
        )
        assert _strip_cover_and_toc(text) == text

    def test_lower_level_part_heading_is_a_cut_point(self):
        # Degraded renders may emit part headings at h2/h3 instead of h1.
        text = "Cover text.\n### PART I\nBody text.\n"
        assert _strip_cover_and_toc(text) == "### PART I\nBody text.\n"


class TestStripSignatures:
    def test_signature_heading_to_end_is_cut(self):
        text = (
            "# PART I\nSubstantive body.\n"
            "### SIGNATURES\n"
            "Pursuant to the requirements of Section 13 or 15(d)...\n"
            "| /s/Jane Doe | Chief Executive Officer |\n"
        )
        cleaned = _strip_signatures(text)
        assert "Substantive body." in cleaned
        assert "SIGNATURES" not in cleaned
        assert "/s/Jane Doe" not in cleaned

    def test_bare_all_caps_signatures_line_is_cut(self):
        # Degraded renders may not mark the signature block as a heading.
        text = "Body text.\nSIGNATURES\nPursuant to the requirements...\n"
        cleaned = _strip_signatures(text)
        assert "Body text." in cleaned
        assert "Pursuant to the requirements" not in cleaned

    def test_last_occurrence_wins(self):
        # Cutting at an early false anchor would delete real content; the
        # signature block is always at the end, so the last match is the cut.
        text = (
            "## SIGNATURES\nEarly section that happens to carry the title.\n"
            "Real body continues here.\n"
            "### SIGNATURES\nActual signature table.\n"
        )
        cleaned = _strip_signatures(text)
        assert "Real body continues here." in cleaned
        assert "Actual signature table." not in cleaned

    def test_signatures_in_prose_is_preserved(self):
        text = (
            "The report requires signatures from all officers.\n"
            "More discussion of Signatures follows in prose.\n"
        )
        assert _strip_signatures(text) == text

    def test_toc_table_row_is_not_a_cut_point(self):
        # The INDEX table names the signature page ("| SIGNATURES. | ... |")
        # — a table row, not the block itself.
        text = "| SIGNATURES. |     |  | 106 |\nBody after the TOC row.\n"
        assert _strip_signatures(text) == text


class TestStripPageArtifacts:
    def test_table_of_contents_page_header_removed(self):
        text = "Body line one.\nTable of Contents\nBody line two.\n"
        cleaned = _strip_page_artifacts(text)
        assert "Table of Contents" not in cleaned
        assert "Body line one." in cleaned
        assert "Body line two." in cleaned

    def test_broken_glyph_variant_removed(self):
        # Real render artifact (AMD FY2025): "Table of Conten t s" — the
        # page-break header comes through with shattered glyph spacing.
        text = "Body line one.\nTable of Conten t s\nBody line two.\n"
        cleaned = _strip_page_artifacts(text)
        assert "Conten t s" not in cleaned

    def test_table_of_contents_in_prose_is_preserved(self):
        text = "The table of contents on page 1 lists every item.\n"
        assert _strip_page_artifacts(text) == text

    def test_centered_page_number_div_removed(self):
        text = "Body line.\n<div align='center'>106</div>\nNext line.\n"
        cleaned = _strip_page_artifacts(text)
        assert "<div" not in cleaned
        assert "Body line." in cleaned

    def test_centered_text_div_is_preserved(self):
        # Only pure page numbers are artifacts; centered prose is content
        # (e.g. "See accompanying notes to the Consolidated...").
        text = "<div align='center'>See accompanying notes</div>\n"
        assert _strip_page_artifacts(text) == text


class TestCollapseBlankLines:
    def test_three_plus_blank_lines_collapse_to_one(self):
        text = "Line one.\n\n\n\n\nLine two.\n"
        assert _collapse_blank_lines(text) == "Line one.\n\nLine two.\n"

    def test_single_blank_line_preserved(self):
        text = "Line one.\n\nLine two.\n"
        assert _collapse_blank_lines(text) == text


class TestCleanDegradedMarkdown:
    def test_full_pipeline_on_realistic_shape(self):
        text = (
            "### UNITED STATES SECURITIES AND EXCHANGE COMMISSION\n"
            "#### FORM 10-K\n"
            "#### INDEX\n"
            "| ITEM 1. |  | Business |  | 1 |\n"
            "| SIGNATURES. |  |  | 106 |\n"
            "# PART I\n"
            "## ITEM 1. BUSINESS\n"
            "We design high-performance processors.\n"
            "Table of Conten t s\n"
            "<div align='center'>14</div>\n"
            "## ITEM 1A. RISK FACTORS\n"
            "Our business depends on markets.\n"
            "### SIGNATURES\n"
            "Pursuant to the requirements...\n"
            "| /s/Jane Doe | CEO |\n"
        )
        cleaned = clean_degraded_markdown(text)
        assert cleaned.startswith("# PART I")
        assert "We design high-performance processors." in cleaned
        assert "Our business depends on markets." in cleaned
        assert "FORM 10-K" not in cleaned
        assert "Conten t s" not in cleaned
        assert "<div align='center'>14</div>" not in cleaned
        assert "/s/Jane Doe" not in cleaned

    def test_empty_input_returns_empty(self):
        assert clean_degraded_markdown("") == ""

    def test_whitespace_only_input_returns_empty(self):
        assert clean_degraded_markdown("  \n \n\t\n") == ""

    def test_unrecognizable_document_survives_mostly_intact(self):
        # A document with none of the known anchors loses nothing: the
        # rules are opt-in cuts, never "keep only what I recognize".
        text = "Opening paragraph.\nSecond paragraph with substance.\n"
        assert clean_degraded_markdown(text) == text.strip()
