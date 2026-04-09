import logging
from pathlib import Path

import pytest

from backend.ingestion.sec_filing_pipeline.markdown_cleaner import MarkdownCleaner

FIXTURE_ROOT = Path(__file__).parent / "fixtures" / "cleanup"


@pytest.fixture()
def cleaner() -> MarkdownCleaner:
    return MarkdownCleaner()


def _wrap_with_frontmatter(body: str, ticker: str = "TEST") -> str:
    return (
        "---\n"
        f"ticker: {ticker}\n"
        "filing_type: 10-K\n"
        "fiscal_year: 2025\n"
        "---\n"
        "\n"
        f"{body}"
    )


# ===========================================================================
# R1.1 Cover page stripping
# ===========================================================================


class TestStripCoverPage:
    def test_strips_content_between_frontmatter_and_part_i(self, cleaner):
        markdown = _wrap_with_frontmatter(
            "UNITED STATES SECURITIES AND EXCHANGE COMMISSION\n\n"
            "Some cover page noise.\n\n"
            "Check the box ☒\n\n"
            "# Part I\n\n"
            "## Item 1. Business\n\n"
            "We make widgets.\n"
        )
        result = cleaner._strip_cover_page(markdown)
        assert "UNITED STATES" not in result
        assert "Check the box" not in result
        assert "# Part I" in result
        assert "## Item 1. Business" in result
        assert "We make widgets" in result

    def test_strips_uppercase_part_i_anchor(self, cleaner):
        markdown = _wrap_with_frontmatter(
            "Cover noise here.\n\n# PART I\n\n## ITEM 1. BUSINESS\n"
        )
        result = cleaner._strip_cover_page(markdown)
        assert "Cover noise" not in result
        assert "# PART I" in result

    def test_falls_back_to_item_1_anchor_when_part_i_missing(self, cleaner):
        markdown = _wrap_with_frontmatter(
            "Cover page boilerplate here.\n\n"
            "Part I\n\n"  # plain text, not heading
            "## Item 1. Business\n\n"
            "Real content.\n"
        )
        result = cleaner._strip_cover_page(markdown)
        assert "boilerplate" not in result
        assert "## Item 1. Business" in result
        assert "Real content" in result

    def test_passes_through_when_no_anchor_found(self, cleaner, caplog):
        markdown = _wrap_with_frontmatter(
            "Plain text without any headings.\nNothing structured here.\n"
        )
        with caplog.at_level(logging.WARNING):
            result = cleaner._strip_cover_page(markdown)
        assert "Plain text" in result  # nothing was deleted
        assert any("anchor" in rec.message.lower() for rec in caplog.records)

    def test_preserves_frontmatter_unchanged(self, cleaner):
        markdown = _wrap_with_frontmatter("noise\n\n# Part I\n\nreal\n", ticker="NVDA")
        result = cleaner._strip_cover_page(markdown)
        assert result.startswith("---\nticker: NVDA\n")
        assert "noise" not in result

    def test_no_frontmatter_pass_through(self, cleaner):
        markdown = "Just some markdown without YAML frontmatter.\n# Part I\n"
        result = cleaner._strip_cover_page(markdown)
        assert result == markdown

    def test_empty_input(self, cleaner):
        assert cleaner._strip_cover_page("") == ""


# ===========================================================================
# R1.2 Page separator stripping
# ===========================================================================


class TestStripPageSeparators:
    def test_strips_separator_with_toc_link(self, cleaner):
        markdown = (
            "Some content here.\n\n"
            "81\n"
            "---\n"
            "[Table of Contents](#toc1)\n"
            "More content.\n"
        )
        result = cleaner._strip_page_separators(markdown)
        assert "---" not in result
        assert "Table of Contents" not in result
        assert "Some content here" in result
        assert "More content" in result

    def test_strips_bare_separator_without_toc(self, cleaner):
        markdown = "Para one.\n\n\n---\n\nPara two.\n"
        result = cleaner._strip_page_separators(markdown)
        assert "---" not in result
        assert "Para one" in result
        assert "Para two" in result

    def test_strips_separator_with_whitespace_around_digits(self, cleaner):
        markdown = "Para one.\n  82  \n---\n\nPara two.\n"
        result = cleaner._strip_page_separators(markdown)
        assert "---" not in result
        assert "82" not in result

    def test_preserves_markdown_table_separator(self, cleaner):
        markdown = (
            "| Col1 | Col2 |\n"
            "| --- | --- |\n"
            "| a    | b    |\n"
        )
        result = cleaner._strip_page_separators(markdown)
        assert "| --- | --- |" in result
        assert "| a    | b    |" in result

    def test_preserves_dense_table_separator_no_spaces(self, cleaner):
        markdown = "| h1 | h2 |\n|---|---|\n| 1 | 2 |\n"
        result = cleaner._strip_page_separators(markdown)
        assert "|---|---|" in result

    def test_preserves_separator_with_paragraph_text_before(self, cleaner):
        # If the line above --- is not blank/digits, the regex shouldn't match.
        markdown = "Real paragraph text.\n---\nMore text.\n"
        result = cleaner._strip_page_separators(markdown)
        # The regex requires the prev line to be empty/digits, so this should NOT match
        assert "---" in result


# ===========================================================================
# R1.3 Part III stub stripping
# ===========================================================================


class TestStripPartIIIStubs:
    def test_strips_pure_item_10_stub(self, cleaner):
        markdown = (
            "## Item 10. Directors, Executive Officers and Corporate Governance\n\n"
            "The information required by this Item is incorporated herein by reference "
            "to the Proxy Statement.\n\n"
            "## Item 11. Executive Compensation\n\n"
            "Real compensation discussion paragraph with substantial content. "
            "Our CEO compensation comprises base salary, annual bonus, and long-term "
            "incentive awards in the form of restricted stock units and performance "
            "share units that vest over a multi-year schedule.\n"
        )
        result = cleaner._strip_part_iii_stubs(markdown)
        assert "## Item 10." not in result
        assert "Directors, Executive Officers" not in result
        assert "## Item 11." in result
        assert "Real compensation discussion" in result

    def test_strips_uppercase_item_11_stub(self, cleaner):
        markdown = (
            "## ITEM 11. EXECUTIVE COMPENSATION\n\n"
            "The information required is incorporated by reference to our Proxy Statement.\n\n"
            "## ITEM 12. SECURITY OWNERSHIP\n\n"
            "Detailed ownership information follows below in the section that lists "
            "the holdings of each beneficial owner with five percent or greater equity "
            "interest in the company as of the most recent fiscal year-end disclosure.\n"
        )
        result = cleaner._strip_part_iii_stubs(markdown)
        assert "## ITEM 11." not in result
        assert "EXECUTIVE COMPENSATION" not in result
        assert "## ITEM 12." in result
        assert "Detailed ownership information" in result

    def test_handles_incorporated_herein_variant(self, cleaner):
        markdown = (
            "## Item 12. Security Ownership\n\n"
            "The information is incorporated herein by reference to the Proxy.\n"
        )
        result = cleaner._strip_part_iii_stubs(markdown)
        assert "## Item 12." not in result

    def test_handles_incorporated_by_reference_into_variant(self, cleaner):
        markdown = (
            "## Item 13. Certain Relationships\n\n"
            "Information is incorporated by reference into this report from the Proxy.\n"
        )
        result = cleaner._strip_part_iii_stubs(markdown)
        assert "## Item 13." not in result

    def test_preserves_item_1c_cybersecurity(self, cleaner):
        # NVDA case — must NOT be touched even though regex could be tempted
        markdown = (
            "## Item 1C. Cybersecurity\n\n"
            "We maintain a comprehensive cybersecurity program. Risk assessment is "
            "performed quarterly. Our CISO reports directly to the Board.\n\n"
            "## Item 2. Properties\n"
        )
        result = cleaner._strip_part_iii_stubs(markdown)
        assert "## Item 1C." in result
        assert "cybersecurity program" in result

    def test_preserves_item_9a_controls(self, cleaner):
        markdown = (
            "## Item 9A. Controls and Procedures\n\n"
            "Management evaluated the effectiveness of disclosure controls. "
            "Our principal executive officer concluded that controls are effective.\n\n"
            "## Item 10. Directors\n"
        )
        result = cleaner._strip_part_iii_stubs(markdown)
        assert "## Item 9A." in result
        assert "Management evaluated" in result

    def test_preserves_hybrid_section_with_real_content(self, cleaner):
        # AMT-style: real exec biographies + ref sentence at end
        markdown = (
            "## ITEM 10.\n\n"
            "- DIRECTORS, EXECUTIVE OFFICERS AND CORPORATE GOVERNANCE\n\n"
            "Steven O. Vondran is our President and Chief Executive Officer. "
            "Mr. Vondran joined us in 2000 as a member of our corporate legal team. "
            "He served as Senior Vice President in multiple roles. He earned his J.D. "
            "from the University of Arkansas. He currently serves on the board of "
            "Ameren Corporation.\n\n"
            "Rodney M. Smith is our Chief Financial Officer. Mr. Smith joined us in "
            "October 2009. He previously held the role of Treasurer. He earned his "
            "M.B.A from Suffolk University and a Bachelor of Science from Merrimack.\n\n"
            "The information under \"Election of Directors\" from the Definitive Proxy "
            "Statement is incorporated herein by reference.\n\n"
            "## ITEM 11. EXECUTIVE COMPENSATION\n"
        )
        result = cleaner._strip_part_iii_stubs(markdown)
        # Real content must survive
        assert "Steven O. Vondran" in result
        assert "Rodney M. Smith" in result
        assert "Suffolk University" in result
        # Section must NOT have been stripped
        assert "## ITEM 10." in result

    def test_preserves_item_with_real_content_no_ref(self, cleaner):
        markdown = (
            "## Item 10. Directors\n\n"
            "Detailed bio of CEO Jane Smith. She graduated from MIT in 1995 and "
            "joined our company in 2010. She previously worked at McKinsey for ten "
            "years across multiple sectors including healthcare and financial services.\n\n"
            "## Item 11. Compensation\n"
        )
        result = cleaner._strip_part_iii_stubs(markdown)
        assert "## Item 10." in result
        assert "Jane Smith" in result

    def test_word_boundary_protects_item_1a_1b_1c(self, cleaner):
        # These should not be touched even if they contain incorporated-by-reference text
        # (which they wouldn't normally, but defensive test)
        markdown = (
            "## Item 1A. Risk Factors\n\n"
            "Some real content. Then some incorporated by reference language for show.\n\n"
            "## Item 1B. Unresolved Staff Comments\n\n"
            "More content. Also incorporated herein by reference here.\n\n"
            "## Item 1C. Cybersecurity\n\n"
            "Cybersecurity content here.\n"
        )
        result = cleaner._strip_part_iii_stubs(markdown)
        assert "## Item 1A." in result
        assert "## Item 1B." in result
        assert "## Item 1C." in result

    def test_strips_empty_body_item_heading(self, cleaner):
        # CRM TOC pseudo-heading case: ## Item 10. with no body
        markdown = (
            "## Item 10.\n\n"
            "## Item 11.\n\n"
            "## Item 12.\n"
        )
        result = cleaner._strip_part_iii_stubs(markdown)
        # All three are empty-body → stripped
        assert "## Item 10." not in result
        assert "## Item 11." not in result
        assert "## Item 12." not in result


# ===========================================================================
# R2 Heading normalization
# ===========================================================================


class TestNormalizePartHeadings:
    def test_normalizes_uppercase_part_with_period(self, cleaner):
        result = cleaner._normalize_headings("# PART I.\n")
        assert "# Part I" in result
        assert "# PART" not in result

    def test_normalizes_uppercase_part_no_period(self, cleaner):
        result = cleaner._normalize_headings("# PART II\n")
        assert "# Part II" in result

    def test_preserves_already_standard_part(self, cleaner):
        result = cleaner._normalize_headings("# Part III\n")
        assert "# Part III" in result


class TestNormalizeItemHeadings:
    def test_uppercase_no_space_after_period(self, cleaner):
        # GOOGL: ## ITEM 1.BUSINESS
        result = cleaner._normalize_headings("## ITEM 1.BUSINESS\n")
        assert "## Item 1. Business" in result

    def test_uppercase_with_space(self, cleaner):
        # TSLA: ## ITEM 1. BUSINESS
        result = cleaner._normalize_headings("## ITEM 1. BUSINESS\n")
        assert "## Item 1. Business" in result

    def test_uppercase_long_title(self, cleaner):
        result = cleaner._normalize_headings(
            "## ITEM 7. MANAGEMENT'S DISCUSSION AND ANALYSIS\n"
        )
        assert "## Item 7. Management's Discussion and Analysis" in result

    def test_lowercase_title_jnj_case(self, cleaner):
        # JNJ: ## Item 1A. Risk factors
        result = cleaner._normalize_headings("## Item 1A. Risk factors\n")
        assert "## Item 1A. Risk Factors" in result

    def test_preserves_already_standard(self, cleaner):
        # Mixed case stays as-is
        result = cleaner._normalize_headings("## Item 1. Business\n")
        assert "## Item 1. Business" in result

    def test_preserves_known_abbreviation_md_a(self, cleaner):
        # The abbreviation MD&A should stay uppercase
        result = cleaner._normalize_headings("## ITEM 7. MD&A SUMMARY\n")
        assert "MD&A" in result
        assert "Md&A" not in result and "Md&a" not in result

    def test_item_heading_with_letter_suffix(self, cleaner):
        result = cleaner._normalize_headings("## ITEM 7A. QUANTITATIVE DISCLOSURES\n")
        assert "## Item 7A. Quantitative Disclosures" in result


class TestSplitTitleMerge:
    def test_amzn_plain_text_next_line(self, cleaner):
        markdown = "## Item 1.\nBusiness Description\n"
        result = cleaner._merge_split_titles(markdown)
        assert "## Item 1. Business Description" in result
        assert "\nBusiness Description\n" not in result

    def test_amzn_with_blank_line_separator(self, cleaner):
        markdown = "## Item 1.\n\nBusiness Description\n"
        result = cleaner._merge_split_titles(markdown)
        assert "## Item 1. Business Description" in result

    def test_amt_dash_prefix_uppercase_title(self, cleaner):
        markdown = "## ITEM 10.\n\n- DIRECTORS, EXECUTIVE OFFICERS\n"
        result = cleaner._merge_split_titles(markdown)
        assert "## ITEM 10. DIRECTORS, EXECUTIVE OFFICERS" in result

    def test_amt_dash_prefix_title_case(self, cleaner):
        markdown = "## Item 10.\n\n- Directors and Officers\n"
        result = cleaner._merge_split_titles(markdown)
        assert "## Item 10. Directors and Officers" in result

    def test_dash_prefix_lowercase_not_merged(self, cleaner):
        # Real bullet point should NOT be merged
        markdown = "## Item 10.\n\n- some lowercase bullet point text\n"
        result = cleaner._merge_split_titles(markdown)
        # Heading stays bare, bullet stays as bullet
        assert "## Item 10." in result
        assert "- some lowercase" in result

    def test_no_merge_when_next_line_is_heading(self, cleaner):
        markdown = "## Item 10.\n\n## Item 11.\n"
        result = cleaner._merge_split_titles(markdown)
        # Both stay bare
        assert "## Item 10." in result
        assert "## Item 11." in result

    def test_no_merge_when_next_line_is_table(self, cleaner):
        markdown = "## Item 10.\n\n| Col1 | Col2 |\n| --- | --- |\n"
        result = cleaner._merge_split_titles(markdown)
        assert "## Item 10." in result
        assert "| Col1 |" in result

    def test_truncated_heading_logs_warning(self, cleaner, caplog):
        markdown = "## ITEM 1. B\n"
        with caplog.at_level(logging.WARNING):
            result = cleaner._normalize_headings(markdown)
        assert "## Item 1. B" in result
        assert any("truncated" in rec.message.lower() for rec in caplog.records)


# ===========================================================================
# End-to-end clean()
# ===========================================================================


class TestCleanEndToEnd:
    def test_clean_pipeline_runs_all_steps(self, cleaner):
        markdown = _wrap_with_frontmatter(
            "Cover page noise.\nUNITED STATES SEC.\n\n"
            "# PART I\n\n"
            "## ITEM 1. BUSINESS\n\n"
            "We make widgets.\n\n"
            "82\n---\n[Table of Contents](#toc)\n"
            "More widget content.\n\n"
            "## ITEM 1C. Cybersecurity\n\n"
            "We have a robust cybersecurity program with regular audits and "
            "comprehensive risk assessments performed by our internal team.\n\n"
            "## ITEM 10. DIRECTORS\n\n"
            "Information is incorporated herein by reference to the Proxy Statement.\n"
        )
        result = cleaner.clean(markdown)

        # Cover page stripped
        assert "UNITED STATES SEC" not in result
        # Page separator gone
        assert "82\n---" not in result
        assert "Table of Contents" not in result
        # Real Item 1 still there, normalized
        assert "## Item 1. Business" in result
        assert "We make widgets" in result
        # Item 1C preserved (NVDA-style)
        assert "## Item 1C. Cybersecurity" in result
        assert "cybersecurity program" in result
        # Item 10 stub stripped
        assert "## Item 10." not in result
        assert "## ITEM 10." not in result
        # Part heading normalized
        assert "# Part I" in result
        # Frontmatter preserved
        assert result.startswith("---\nticker: TEST\n")

    def test_clean_pure_passthrough_when_no_anchor(self, cleaner, caplog):
        markdown = _wrap_with_frontmatter(
            "Just plain content without any structure.\n"
            "More plain content here.\n"
        )
        with caplog.at_level(logging.WARNING):
            result = cleaner.clean(markdown)
        # All content preserved (cover page strip warned + skipped)
        assert "plain content" in result
        assert "More plain content" in result

    def test_clean_idempotent_on_already_clean_markdown(self, cleaner):
        clean_md = _wrap_with_frontmatter(
            "# Part I\n\n"
            "## Item 1. Business\n\n"
            "Clean content.\n\n"
            "## Item 1C. Cybersecurity\n\n"
            "Also clean.\n"
        )
        once = cleaner.clean(clean_md)
        twice = cleaner.clean(once)
        assert once == twice


# ===========================================================================
# Fixture-based integration tests against real 10-K snippets
# ===========================================================================


# Anchor tickers and the snippet variants (cover page strip + Part III stub)
# we hold raw + expected fixtures for in fixtures/cleanup/{ticker}/.
_FIXTURE_CASES = [
    ("nvda", "cover"),
    ("nvda", "part_iii"),
    ("amt", "cover"),
    ("amt", "part_iii"),
    ("crm", "cover"),
    ("crm", "part_iii"),
    ("jnj", "cover"),
    ("jnj", "part_iii"),
]


class TestFixtureSnippets:
    """End-to-end snapshot tests against real 10-K snippets.

    Each fixture is a real cached 10-K slice (cover page or Part III
    region) with the corresponding expected MarkdownCleaner output. If
    the cleaner's behavior changes intentionally, regenerate the
    expected files; if it changes unexpectedly, this test catches the
    regression.
    """

    @pytest.mark.parametrize(("ticker", "variant"), _FIXTURE_CASES)
    def test_cleanup_matches_expected(self, cleaner, ticker, variant):
        raw_path = FIXTURE_ROOT / ticker / f"{variant}_raw.md"
        expected_path = FIXTURE_ROOT / ticker / f"{variant}_expected.md"
        raw = raw_path.read_text()
        expected = expected_path.read_text()
        actual = cleaner.clean(raw)
        assert actual == expected, (
            f"\n{ticker}/{variant} cleanup output mismatched expected fixture.\n"
            f"  raw    : {raw_path} ({len(raw)} chars)\n"
            f"  expect : {expected_path} ({len(expected)} chars)\n"
            f"  actual : {len(actual)} chars\n"
            "Regenerate fixtures only if the change is intentional."
        )


class TestFixtureInvariants:
    """Hard safety invariants on the fixture-based outputs.

    These are independent of the snapshot equality test — they encode
    the user's "conservative cleanup" principle as direct assertions:
    real content must always survive, even if the snapshot drifts.
    """

    def test_amt_exec_biographies_preserved(self, cleaner):
        raw = (FIXTURE_ROOT / "amt" / "part_iii_raw.md").read_text()
        result = cleaner.clean(raw)
        # AMT Item 10 hybrid: 7 named exec officers must all survive
        assert "Steven O. Vondran" in result
        assert "Rodney M. Smith" in result
        assert "Ruth T. Dowling" in result

    def test_crm_code_of_conduct_preserved(self, cleaner):
        raw = (FIXTURE_ROOT / "crm" / "part_iii_raw.md").read_text()
        result = cleaner.clean(raw)
        # CRM Item 10 hybrid: Code of Conduct policy is real content
        assert "Code of Conduct" in result
        assert "Marc Benioff" in result

    def test_jnj_code_of_business_conduct_preserved(self, cleaner):
        raw = (FIXTURE_ROOT / "jnj" / "part_iii_raw.md").read_text()
        result = cleaner.clean(raw)
        # JNJ Item 10 hybrid: Code of Business Conduct is real content
        assert "Code of Business Conduct" in result

    def test_jnj_lowercase_titles_normalized(self, cleaner):
        raw = (FIXTURE_ROOT / "jnj" / "part_iii_raw.md").read_text()
        result = cleaner.clean(raw)
        # JNJ uses sentence case in raw — cleaner must Title Case them
        assert "## Item 9A. Controls and Procedures" in result
        assert "## Item 9B. Other Information" in result
        # Lowercase 'risk factors' style should be gone
        assert "Controls and procedures" not in result

    def test_jnj_pure_stubs_stripped(self, cleaner):
        raw = (FIXTURE_ROOT / "jnj" / "part_iii_raw.md").read_text()
        result = cleaner.clean(raw)
        # JNJ Item 11 / 13 / 14 are pure single-sentence stubs
        assert "## Item 11. Executive compensation" not in result
        assert "## Item 11. Executive Compensation" not in result
        assert "## Item 13" not in result
        assert "## Item 14" not in result

    def test_crm_pure_stubs_stripped(self, cleaner):
        raw = (FIXTURE_ROOT / "crm" / "part_iii_raw.md").read_text()
        result = cleaner.clean(raw)
        # CRM Item 11 / 12 / 13 / 14 are pure stubs
        assert "## ITEM 11" not in result
        assert "## ITEM 12" not in result

    def test_amt_item_1c_heading_preserved(self, cleaner):
        # AMT part_iii fixture is large enough to include Item 9C / 1C
        # check by looking for the heading anchor specifically.
        raw = (FIXTURE_ROOT / "amt" / "part_iii_raw.md").read_text()
        result = cleaner.clean(raw)
        # Verify word-boundary protection: Item 9A/9B/9C must survive
        # the Part III stub stripper even if their bodies happen to
        # contain incorporated-by-reference text.
        for marker in ("9A", "9B", "9C"):
            if f"## Item {marker}" in raw or f"## ITEM {marker}" in raw:
                assert (
                    f"## Item {marker}" in result or f"## ITEM {marker}" in result
                ), f"AMT Item {marker} was incorrectly stripped"
