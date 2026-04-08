import pytest
from bs4 import BeautifulSoup

from backend.ingestion.sec_filing_pipeline.html_preprocessor import HTMLPreprocessor


@pytest.fixture()
def preprocessor():
    return HTMLPreprocessor()


def _normalize(html: str) -> str:
    return str(BeautifulSoup(html, "html.parser"))


# ---------- S-prep-01: XBRL tag stripping ----------


class TestStripXBRLTags:
    def test_simple_xbrl_tag_unwrapped(self, preprocessor):
        html = "<p>Revenue was <ix:nonFraction>47525000000</ix:nonFraction> million</p>"
        result = preprocessor.preprocess(html)
        assert "ix:" not in result
        assert "47525000000" in result
        assert "<p>" in result

    def test_nested_xbrl_tags_unwrapped(self, preprocessor):
        html = (
            "<ix:nonNumeric>"
            "<p>Revenue was <ix:nonFraction>47525</ix:nonFraction> million</p>"
            "</ix:nonNumeric>"
        )
        result = preprocessor.preprocess(html)
        assert "ix:" not in result
        assert "<p>Revenue was 47525 million</p>" in result

    def test_section_wrapping_xbrl_preserves_children(self, preprocessor):
        html = (
            '<ix:nonNumeric contextRef="c-1">'
            "<h2>Business</h2>"
            "<p>We make things.</p>"
            "</ix:nonNumeric>"
        )
        result = preprocessor.preprocess(html)
        assert "ix:" not in result
        assert "<h2>" in result
        assert "<p>We make things.</p>" in result


# ---------- S-prep-02: Decorative style removal + hidden element removal ----------


class TestDecorativeStyleRemoval:
    def test_decorative_styles_removed(self, preprocessor):
        html = '<p style="font-family:Times New Roman; color:#000">text</p>'
        result = preprocessor.preprocess(html)
        assert result == _normalize("<p>text</p>")

    def test_text_align_preserved(self, preprocessor):
        html = '<td style="text-align:right; padding-left:4px">$47,525</td>'
        result = preprocessor.preprocess(html)
        assert "text-align" in result
        assert "padding-left" not in result

    def test_mixed_styles_keeps_functional(self, preprocessor):
        html = '<div style="font-size:10pt; text-align:center; color:blue">hello</div>'
        result = preprocessor.preprocess(html)
        assert "text-align:center" in result
        assert "font-size" not in result
        assert "color" not in result


class TestHiddenElementRemoval:
    def test_display_none_removed(self, preprocessor):
        html = '<div style="display:none">hidden</div><p>visible</p>'
        result = preprocessor.preprocess(html)
        assert "hidden" not in result
        assert "visible" in result

    def test_xbrl_header_block_removed(self, preprocessor):
        html = (
            '<div style="display:none">'
            "<ix:header>"
            "<ix:hidden>metadata stuff</ix:hidden>"
            "</ix:header>"
            "</div>"
            "<p>content</p>"
        )
        result = preprocessor.preprocess(html)
        assert "metadata" not in result
        assert "content" in result


# ---------- S-prep-03: <font> tag unwrapping ----------


class TestFontTagUnwrapping:
    def test_font_tag_unwrapped_preserves_content(self, preprocessor):
        html = '<font style="font-family:Times New Roman" size="4"><b>Item 1</b></font>'
        result = preprocessor.preprocess(html)
        assert "<font" not in result
        assert "<b>Item 1</b>" in result

    def test_multiple_font_tags_unwrapped(self, preprocessor):
        html = (
            '<font style="font-size:10pt"><b>Heading</b></font>'
            "<font>body text here</font>"
        )
        result = preprocessor.preprocess(html)
        assert "<font" not in result
        assert "Heading" in result
        assert "body text here" in result


# ---------- Text whitespace normalization ----------


class TestTextWhitespaceNormalization:
    def test_hard_linebreak_inside_text_collapsed(self, preprocessor):
        html = "<p>United\nStates Securities and Exchange Commission</p>"
        result = preprocessor.preprocess(html)
        assert "United States Securities and Exchange Commission" in result
        assert "United\nStates" not in result

    def test_item_pattern_with_embedded_newline_promoted(self, preprocessor):
        html = "<p><b>Item\n1A. Risk Factors.</b></p>"
        result = preprocessor.preprocess(html)
        assert "<h2>" in result
        assert "Item 1A. Risk Factors." in result

    def test_multiple_internal_whitespace_collapsed(self, preprocessor):
        html = "<p>foo\n\n  bar\t\tbaz</p>"
        result = preprocessor.preprocess(html)
        assert "foo bar baz" in result

    def test_pre_block_preserves_whitespace(self, preprocessor):
        html = "<pre>line one\nline two\n  indented</pre>"
        result = preprocessor.preprocess(html)
        assert "line one\nline two\n  indented" in result

    def test_code_block_preserves_whitespace(self, preprocessor):
        html = "<code>def f():\n    return 1</code>"
        result = preprocessor.preprocess(html)
        assert "def f():\n    return 1" in result


# ---------- Heading promotion ----------


class TestHeadingPromotion:
    def test_item_pattern_bold_promoted_to_h2(self, preprocessor):
        html = '<div style="font-weight:700">Item 1. Business</div>'
        result = preprocessor.preprocess(html)
        assert "<h2>Item 1. Business</h2>" in result

    def test_item_with_b_tag_promoted(self, preprocessor):
        html = "<p><b>Item 7A. Quantitative and Qualitative Disclosures About Market Risk</b></p>"
        result = preprocessor.preprocess(html)
        assert "<h2>" in result
        assert "Item 7A." in result

    def test_item_with_strong_tag_promoted(self, preprocessor):
        html = "<div><strong>Item 15. Exhibits and Financial Statement Schedules</strong></div>"
        result = preprocessor.preprocess(html)
        assert "<h2>" in result

    def test_part_pattern_promoted_to_h1(self, preprocessor):
        html = "<p><b>PART I</b></p>"
        result = preprocessor.preprocess(html)
        assert "<h1>PART I</h1>" in result

    def test_part_iv_promoted(self, preprocessor):
        html = '<div style="font-weight:bold">PART IV</div>'
        result = preprocessor.preprocess(html)
        assert "<h1>PART IV</h1>" in result

    def test_bold_text_without_item_pattern_not_promoted(self, preprocessor):
        html = "<p><b>Some bold paragraph that is not a heading</b></p>"
        result = preprocessor.preprocess(html)
        assert "<h1>" not in result
        assert "<h2>" not in result
        assert "<p>" in result

    def test_item_pattern_without_bold_not_promoted(self, preprocessor):
        html = "<p>Item 1. Business</p>"
        result = preprocessor.preprocess(html)
        assert "<h2>" not in result
        assert "<p>" in result

    def test_modern_filing_styled_span_promoted(self, preprocessor):
        html = (
            "<div>"
            '<span style="font-weight:700;font-size:10pt">Item 1. Business</span>'
            "</div>"
        )
        result = preprocessor.preprocess(html)
        assert "<h2>" in result
        assert "Item 1. Business" in result

    def test_older_filing_font_b_promoted(self, preprocessor):
        html = (
            "<p>"
            '<font style="font-family:Times New Roman" size="2">'
            "<b>Item 1. Business</b>"
            "</font>"
            "</p>"
        )
        result = preprocessor.preprocess(html)
        assert "<h2>" in result
        assert "Item 1. Business" in result

    def test_part_split_across_adjacent_spans_promoted(self, preprocessor):
        # MSFT 2025 pattern: heading text broken at the space, with the space
        # living inside the second span: <span>PART</span><span> I</span>.
        html = (
            "<p>"
            '<span style="font-weight:bold">PART</span>'
            '<span style="font-weight:bold"> I</span>'
            "</p>"
        )
        result = preprocessor.preprocess(html)
        assert "<h1>PART I</h1>" in result

    def test_part_split_mid_word_across_spans_promoted(self, preprocessor):
        # MSFT 2025 PART II pattern: split mid-word across two bold spans
        # — <span>PAR</span><span>T II</span>.
        html = (
            "<p>"
            '<span style="font-weight:bold">PAR</span>'
            '<span style="font-weight:bold">T II</span>'
            "</p>"
        )
        result = preprocessor.preprocess(html)
        assert "<h1>PART II</h1>" in result

    def test_item_split_across_adjacent_spans_promoted(self, preprocessor):
        # Same XBRL exporter pattern applied to Item rows.
        html = (
            "<p>"
            '<span style="font-weight:bold">ITEM 1. B</span>'
            '<span style="font-weight:bold">USINESS</span>'
            "</p>"
        )
        result = preprocessor.preprocess(html)
        assert "<h2>ITEM 1. BUSINESS</h2>" in result


# ---------- Preprocessing order ----------


class TestPreprocessingOrder:
    def test_promote_headings_sees_font_size(self):
        """_promote_headings must see font-size before _strip_decorative_styles removes it."""

        class SpyPreprocessor(HTMLPreprocessor):
            def __init__(self):
                super().__init__()
                self.captured: str = ""

            def _promote_headings(self, soup):
                self.captured = str(soup)
                super()._promote_headings(soup)

        spy = SpyPreprocessor()
        html = '<div><span style="font-size:10pt;font-weight:700">Item 1. Business</span></div>'
        final = spy.preprocess(html)

        assert "font-size" in spy.captured, (
            "_promote_headings did not see font-size; strip_decorative ran too early"
        )
        assert "font-size" not in final, (
            "font-size leaked into final output; _strip_decorative_styles must run after promote"
        )


# ---------- Full pipeline integration ----------


class TestPreprocessorPipeline:
    def test_full_pipeline_modern_filing_fragment(self, preprocessor):
        html = (
            '<div style="display:none"><ix:header><ix:hidden>xbrl meta</ix:hidden></ix:header></div>'
            '<div style="font-family:Arial;font-size:10pt">'
            '<ix:nonNumeric contextRef="c-1">'
            '<div><span style="font-weight:700;font-size:10pt">Item 1. Business</span></div>'
            "<p>We design GPUs.</p>"
            "</ix:nonNumeric>"
            "</div>"
        )
        result = preprocessor.preprocess(html)
        assert "ix:" not in result
        assert "xbrl meta" not in result
        assert "font-family" not in result
        assert "<h2>Item 1. Business</h2>" in result
        assert "We design GPUs." in result

    def test_full_pipeline_older_filing_fragment(self, preprocessor):
        html = (
            '<p><font style="font-family:Times New Roman" size="2">'
            "<b>Item 1. Business</b></font></p>"
            '<font style="font-family:Times New Roman">The Company designs and manufactures.</font>'
        )
        result = preprocessor.preprocess(html)
        assert "<font" not in result
        assert "<h2>Item 1. Business</h2>" in result
        assert "The Company designs and manufactures." in result
