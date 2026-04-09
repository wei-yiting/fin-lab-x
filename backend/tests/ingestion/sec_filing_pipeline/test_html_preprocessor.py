import pytest
from bs4 import BeautifulSoup

from backend.ingestion.sec_filing_pipeline.html_preprocessor import (
    HTMLPreprocessor,
    _is_isolated_item_block,
)


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

    def test_toc_part_headings_not_double_promoted(self, preprocessor):
        # Workiva-style 10-K layout: TOC region lists PART I, body region
        # repeats PART I. After preprocess only the body occurrence must be
        # promoted to <h1>, keeping the TOC entry unpromoted.
        html = (
            "<html><body>"
            '<div><span style="font-weight:700">PART I</span></div>'
            "<p>Item 1 ... 1</p>"
            "<p>Item 1A ... 5</p>"
            '<div><span style="font-weight:700">PART I</span></div>'
            "<p>Actual Part I body content here.</p>"
            "</body></html>"
        )
        result = preprocessor.preprocess(html)
        result_soup = BeautifulSoup(result, "html.parser")
        h1_tags = result_soup.find_all("h1")
        assert len(h1_tags) == 1
        assert h1_tags[0].get_text(strip=True) == "PART I"

    def test_item_promotion_ssot_skips_toc_duplicate(self, preprocessor):
        # CRM/BAC-style 10-K layout: TOC table contains <td>Item 1.</td> and
        # body has its own <div>Item 1. Business</div>. Both are bold.
        # detect_item_regions picks the body div (last occurrence) as the
        # region anchor, so only the body div should become <h2>; the TOC
        # <td> must remain a <td>.
        html = (
            "<html><body>"
            "<table><tr>"
            '<td><span style="font-weight:700">Item 1.</span></td>'
            "</tr></table>"
            '<div><span style="font-weight:700">Item 1. Business</span></div>'
            "<p>Body text describing the business.</p>"
            "</body></html>"
        )
        result = preprocessor.preprocess(html)
        result_soup = BeautifulSoup(result, "html.parser")
        h2_tags = result_soup.find_all("h2")
        assert len(h2_tags) == 1
        assert h2_tags[0].get_text(strip=True) == "Item 1. Business"
        # TOC td must remain unchanged
        toc_td = result_soup.find("td")
        assert toc_td is not None
        assert toc_td.get_text(strip=True) == "Item 1."

    def test_item_promotion_ssot_multiple_items(self, preprocessor):
        # 5 Items in TOC + 5 Items in body, all bold. After preprocess,
        # exactly 5 <h2>s, all from the body region.
        toc_rows = "".join(
            f'<tr><td><span style="font-weight:700">Item {n}.</span></td></tr>'
            for n in (1, "1A", 2, 3, 4)
        )
        body_blocks = "".join(
            f'<div><span style="font-weight:700">Item {n}. Section {n}</span></div>'
            f"<p>Body content for section {n}.</p>"
            for n in (1, "1A", 2, 3, 4)
        )
        html = f"<html><body><table>{toc_rows}</table>{body_blocks}</body></html>"
        result = preprocessor.preprocess(html)
        result_soup = BeautifulSoup(result, "html.parser")
        h2_tags = result_soup.find_all("h2")
        assert len(h2_tags) == 5
        # All h2s should be the body "Item N. Section N" form, not the
        # TOC "Item N." form
        for h2 in h2_tags:
            assert "Section" in h2.get_text(strip=True)


# ---------- Isolated item block sibling scan ----------


class TestIsolatedItemBlock:
    def test_skips_empty_prev_spacer(self):
        # JPM/Workiva pattern: empty <div> spacer precedes the Item div.
        # The spacer must be skipped so isolation succeeds.
        soup = BeautifulSoup(
            "<html><body>"
            '<div style="margin-bottom:6pt"></div>'
            '<div><span style="font-size:12pt">Item 1.</span></div>'
            "<p>Body paragraph after item.</p>"
            "</body></html>",
            "html.parser",
        )
        item_div = soup.find_all("div")[1]
        assert _is_isolated_item_block(item_div, body_font_size=10.0) is True

    def test_blocked_by_text_prev_div(self):
        # Real (non-empty) prev div sibling must still block isolation.
        soup = BeautifulSoup(
            "<html><body>"
            "<div>real content here</div>"
            '<div><span style="font-size:12pt">Item 1.</span></div>'
            "<p>Body paragraph after item.</p>"
            "</body></html>",
            "html.parser",
        )
        item_div = soup.find_all("div")[1]
        assert _is_isolated_item_block(item_div, body_font_size=10.0) is False

    def test_walks_past_multiple_empty_siblings(self):
        # Two empty spacer divs followed by a real text div — the third
        # sibling is the blocker.
        soup = BeautifulSoup(
            "<html><body>"
            "<div>real text</div>"
            '<div style="margin-bottom:3pt"></div>'
            '<div style="margin-bottom:3pt"></div>'
            '<div><span style="font-size:12pt">Item 1.</span></div>'
            "<p>Body paragraph after item.</p>"
            "</body></html>",
            "html.parser",
        )
        item_div = soup.find_all("div")[3]
        assert _is_isolated_item_block(item_div, body_font_size=10.0) is False

    def test_all_siblings_empty_returns_true(self):
        # Both prev and next siblings are empty Tags — isolation passes.
        soup = BeautifulSoup(
            "<html><body>"
            '<div style="margin-bottom:6pt"></div>'
            '<div><span style="font-size:12pt">Item 1.</span></div>'
            '<div style="margin-bottom:6pt"></div>'
            "</body></html>",
            "html.parser",
        )
        item_div = soup.find_all("div")[1]
        assert _is_isolated_item_block(item_div, body_font_size=10.0) is True

    def test_strong_signal_promotes_non_bold_item_with_size_jump(self, preprocessor):
        # JPM-style: non-bold Item with 12pt span over 10pt body. The next
        # sibling is a real body <div> that blocks _is_isolated_item_block.
        # The strong-signal path should bypass the sibling check and
        # promote based on the >10% font-size jump alone.
        html = (
            "<html><body>"
            '<p><span style="font-size:10pt">Body paragraph one establishing the body font size baseline.</span></p>'
            "<div>"
            '<span style="font-size:12pt;font-weight:400">Item 1. Business.</span>'
            "</div>"
            '<div><span style="font-size:10pt">Real body paragraph in a div that would normally block isolation.</span></div>'
            "</body></html>"
        )
        result = preprocessor.preprocess(html)
        result_soup = BeautifulSoup(result, "html.parser")
        h2_tags = result_soup.find_all("h2")
        assert len(h2_tags) == 1
        assert h2_tags[0].get_text(strip=True) == "Item 1. Business."

    def test_strong_signal_rejects_long_text(self, preprocessor):
        # Item-regex match but text length >= 100 → strong-signal path
        # rejects to avoid promoting body paragraphs.
        long_tail = (
            "This is a very long paragraph of text that describes the company's "
            "business operations in detail and mentions many specific subsidiaries "
            "and product lines that we sell."
        )
        html = (
            "<html><body>"
            '<p><span style="font-size:10pt">Body paragraph one establishing the body font size baseline value.</span></p>'
            "<div>"
            f'<span style="font-size:12pt;font-weight:400">Item 1. {long_tail}</span>'
            "</div>"
            '<div><span style="font-size:10pt">Real body paragraph after.</span></div>'
            "</body></html>"
        )
        result = preprocessor.preprocess(html)
        result_soup = BeautifulSoup(result, "html.parser")
        assert result_soup.find_all("h2") == []

    def test_strong_signal_rejects_small_size_jump(self, preprocessor):
        # font-size 10.5pt vs body 10pt → ratio 1.05 < 1.1 → rejected.
        html = (
            "<html><body>"
            '<p><span style="font-size:10pt">Body paragraph one establishing the body font size baseline value here.</span></p>'
            "<div>"
            '<span style="font-size:10.5pt;font-weight:400">Item 1. Business.</span>'
            "</div>"
            '<div><span style="font-size:10pt">Real body paragraph after.</span></div>'
            "</body></html>"
        )
        result = preprocessor.preprocess(html)
        result_soup = BeautifulSoup(result, "html.parser")
        assert result_soup.find_all("h2") == []

    def test_strong_signal_rejects_equal_font_size(self, preprocessor):
        # font-size equal to body → no jump → rejected.
        html = (
            "<html><body>"
            '<p><span style="font-size:10pt">Body paragraph one establishing the body font size baseline value here.</span></p>'
            "<div>"
            '<span style="font-size:10pt;font-weight:400">Item 1. Business.</span>'
            "</div>"
            '<div><span style="font-size:10pt">Real body paragraph after.</span></div>'
            "</body></html>"
        )
        result = preprocessor.preprocess(html)
        result_soup = BeautifulSoup(result, "html.parser")
        assert result_soup.find_all("h2") == []

    def test_strong_signal_does_not_override_bold_path(self, preprocessor):
        # Bold Item with no font-size jump must still promote via the
        # bold-signal path even though the strong-signal path would
        # reject (no body font-size info, no size jump).
        html = (
            "<html><body>"
            "<div>"
            '<span style="font-weight:700">Item 1. Business</span>'
            "</div>"
            "</body></html>"
        )
        result = preprocessor.preprocess(html)
        result_soup = BeautifulSoup(result, "html.parser")
        h2_tags = result_soup.find_all("h2")
        assert len(h2_tags) == 1
        assert h2_tags[0].get_text(strip=True) == "Item 1. Business"

    def test_jpm_style_non_bold_item_with_spacer_promotes(self, preprocessor):
        # Integration test combining Fix A + Fix B: JPM-like fragment with
        # a non-bold body Item heading preceded by a Workiva spacer and a
        # TOC <td>. The TOC lives in a separate outer wrapper so it is not
        # a direct sibling of the body Item div (mirrors real Workiva
        # output where TOC and body sit in different sections). Only the
        # body div should become <h2>.
        html = (
            "<html><body>"
            "<div>"
            "<table><tr>"
            '<td><span style="font-size:10pt">Item 1.</span></td>'
            "</tr></table>"
            "</div>"
            "<section>"
            '<div style="margin-bottom:6pt"></div>'
            "<div>"
            '<span style="font-size:12pt;font-weight:400">Item 1. Business.</span>'
            "</div>"
            '<p><span style="font-size:10pt">Body paragraph describing the business of the registrant.</span></p>'
            "</section>"
            "</body></html>"
        )
        result = preprocessor.preprocess(html)
        result_soup = BeautifulSoup(result, "html.parser")
        h2_tags = result_soup.find_all("h2")
        assert len(h2_tags) == 1
        assert h2_tags[0].get_text(strip=True) == "Item 1. Business."
        # TOC td must remain unchanged
        toc_td = result_soup.find("td")
        assert toc_td is not None
        assert toc_td.get_text(strip=True) == "Item 1."


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


# ---------- Sub-section promotion integration ----------


class TestSubsectionPromotion:
    def test_preprocess_promotes_nvda_style_subsection(self, preprocessor):
        # NVDA-style: Item heading followed by bold-only div with font-size →
        # the bold div inside the item region becomes <h3>
        html = (
            '<div><span style="font-weight:700;font-size:10pt">Item 1. Business</span></div>'
            '<div><span style="font-weight:700;font-size:10pt">Our Company</span></div>'
            '<p>We design GPUs.</p>'
        )
        result = preprocessor.preprocess(html)
        assert "<h2>" in result
        assert "Item 1. Business" in result
        assert "<h3>Our Company</h3>" in result

    def test_preprocess_subsection_below_item_untouched(self, preprocessor):
        # Bold block BEFORE the first Item must not be promoted to h3/h4/h5
        html = (
            '<div><span style="font-weight:700;font-size:10pt">Cover Page Heading</span></div>'
            '<div><span style="font-weight:700;font-size:10pt">Item 1. Business</span></div>'
            '<div><span style="font-weight:700;font-size:10pt">Inside Region</span></div>'
        )
        result = preprocessor.preprocess(html)
        result_soup = BeautifulSoup(result, "html.parser")
        # Cover Page Heading must NOT be promoted — it's outside any item region
        promoted_texts = [
            t.get_text(strip=True) for t in result_soup.find_all(["h3", "h4", "h5"])
        ]
        assert "Cover Page Heading" not in promoted_texts
        # Inside Region should be promoted
        assert "Inside Region" in promoted_texts


# ---------- Class C fallback: non-bold Item headings (R5) ----------


class TestClassCFallback:
    def test_intc_non_bold_item_promoted_when_larger_font_size(self, preprocessor):
        # INTC-style: font-weight:400 but larger font-size than body → should promote to h2
        html = (
            '<div><span style="font-weight:400;font-size:14pt">Item 1A. Risk Factors</span></div>'
            '<p><span style="font-size:10pt">Body text here with enough characters to establish body font size.</span></p>'
        )
        result = preprocessor.preprocess(html)
        assert "<h2>" in result
        assert "Item 1A. Risk Factors" in result

    def test_intc_non_bold_item_not_promoted_when_smaller_font_size(self, preprocessor):
        # font-size 9pt < body 10pt → should NOT promote
        html = (
            '<div><span style="font-weight:400;font-size:9pt">Item 1A. Risk Factors</span></div>'
            '<p><span style="font-size:10pt">Body text here with enough characters to establish body font size so we can compare properly.</span></p>'
        )
        result = preprocessor.preprocess(html)
        assert "<h2>" not in result

    def test_intc_non_bold_item_not_promoted_when_size_below_strong_signal(self, preprocessor):
        # Non-bold Item with sibling block. The strong-signal path now
        # bypasses sibling checks for clear font-size jumps, so the
        # rejection must come from a sub-threshold size ratio (10.5/10
        # = 1.05 < 1.1) rather than the isolation sibling guard.
        html = (
            '<div>'
            '<div><span style="font-weight:400;font-size:10.5pt">Item 1. Business</span></div>'
            '<div><span style="font-size:10pt">Some sibling block content here long enough to count.</span></div>'
            '</div>'
        )
        result = preprocessor.preprocess(html)
        result_soup = BeautifulSoup(result, "html.parser")
        h2_tags = result_soup.find_all("h2")
        assert len(h2_tags) == 0

    def test_intc_class_c_does_not_crash_without_subsections(self, preprocessor):
        # Entire HTML has only non-bold Item headings, no bold sub-sections → graceful degradation
        html = (
            '<p><span style="font-size:10pt">Annual Report on Form 10-K body text paragraph one with many words.</span></p>'
            '<div><span style="font-weight:400;font-size:14pt">Item 1. Business</span></div>'
            '<p><span style="font-size:10pt">Business description content goes here with sufficient length.</span></p>'
            '<div><span style="font-weight:400;font-size:14pt">Item 1A. Risk Factors</span></div>'
            '<p><span style="font-size:10pt">Risk factors description content here with sufficient length.</span></p>'
            '<div><span style="font-weight:400;font-size:14pt">Item 2. Properties</span></div>'
            '<p><span style="font-size:10pt">Properties description content here with sufficient length.</span></p>'
        )
        result = preprocessor.preprocess(html)
        result_soup = BeautifulSoup(result, "html.parser")
        h2_tags = result_soup.find_all("h2")
        h3_tags = result_soup.find_all("h3")
        h4_tags = result_soup.find_all("h4")
        # All three Item headings should be promoted to h2
        assert len(h2_tags) == 3
        # No sub-section headings (graceful degradation — Class C has no bold sub-sections)
        assert len(h3_tags) == 0
        assert len(h4_tags) == 0

    def test_existing_bold_item_still_promoted(self, preprocessor):
        # Regression guard: existing bold Item rule must still work after fallback is added
        html = '<div><span style="font-weight:700;font-size:10pt">Item 1. Business</span></div>'
        result = preprocessor.preprocess(html)
        assert "<h2>Item 1. Business</h2>" in result
