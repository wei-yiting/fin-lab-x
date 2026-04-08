from bs4 import BeautifulSoup

from backend.ingestion.sec_filing_pipeline.sec_heading_promoter import (
    extract_dominant_font_size,
    has_table_ancestor,
    is_bold_only_block,
)


def _parse(html: str):
    return BeautifulSoup(html, "html.parser")


# ---------- has_table_ancestor ----------


class TestHasTableAncestor:
    def test_has_table_ancestor_direct_table(self):
        soup = _parse("<table><tr><td><div>x</div></td></tr></table>")
        inner_div = soup.find("div")
        assert has_table_ancestor(inner_div) is True

    def test_has_table_ancestor_no_table(self):
        soup = _parse("<div><span>x</span></div>")
        span = soup.find("span")
        assert has_table_ancestor(span) is False

    def test_has_table_ancestor_nested_div_in_td(self):
        soup = _parse("<table><tr><td><div><span>text</span></div></td></tr></table>")
        span = soup.find("span")
        assert has_table_ancestor(span) is True

    def test_has_table_ancestor_table_is_sibling_not_ancestor(self):
        soup = _parse("<div><table><tr><td>cell</td></tr></table></div><p>para</p>")
        p = soup.find("p")
        assert has_table_ancestor(p) is False

    def test_has_table_ancestor_top_level_tag(self):
        soup = _parse("<div>top level</div>")
        div = soup.find("div")
        assert has_table_ancestor(div) is False


# ---------- extract_dominant_font_size ----------


class TestExtractDominantFontSize:
    def test_extract_dominant_font_size_single_span(self):
        soup = _parse('<div><span style="font-size:12pt">hello</span></div>')
        div = soup.find("div")
        assert extract_dominant_font_size(div) == 12.0

    def test_extract_dominant_font_size_two_spans_char_weighted(self):
        # span1 = 12pt with "1" (1 char), span2 = 9pt with "Our Company" (11 chars)
        # 9pt wins by character count
        soup = _parse(
            '<div>'
            '<span style="font-size:12pt">1</span>'
            '<span style="font-size:9pt">Our Company</span>'
            '</div>'
        )
        div = soup.find("div")
        assert extract_dominant_font_size(div) == 9.0

    def test_extract_dominant_font_size_no_style(self):
        soup = _parse('<div><span>no font-size here</span></div>')
        div = soup.find("div")
        assert extract_dominant_font_size(div) is None

    def test_extract_dominant_font_size_footnote_marker(self):
        # heading "Critical Accounting Estimates" at 9pt (29 chars) wins over
        # footnote marker "1" at 6pt (1 char)
        soup = _parse(
            '<div>'
            '<span style="font-size:9pt">Critical Accounting Estimates</span>'
            '<span style="font-size:6pt">1</span>'
            '</div>'
        )
        div = soup.find("div")
        assert extract_dominant_font_size(div) == 9.0

    def test_extract_dominant_font_size_multiple_spans_same_size(self):
        # two spans at 10pt, one at 8pt — 10pt wins by total char count
        soup = _parse(
            '<div>'
            '<span style="font-size:10pt">Hello</span>'
            '<span style="font-size:10pt"> World</span>'
            '<span style="font-size:8pt">foot</span>'
            '</div>'
        )
        div = soup.find("div")
        assert extract_dominant_font_size(div) == 10.0

    def test_extract_dominant_font_size_ignores_non_pt_units(self):
        # px unit should be ignored
        soup = _parse('<div><span style="font-size:12px">text</span></div>')
        div = soup.find("div")
        assert extract_dominant_font_size(div) is None

    def test_extract_dominant_font_size_empty_div(self):
        soup = _parse('<div></div>')
        div = soup.find("div")
        assert extract_dominant_font_size(div) is None

    def test_extract_dominant_font_size_float_pt(self):
        soup = _parse('<div><span style="font-size:10.5pt">hello</span></div>')
        div = soup.find("div")
        assert extract_dominant_font_size(div) == 10.5


# ---------- is_bold_only_block ----------


class TestIsBoldOnlyBlock:
    def test_is_bold_only_block_pure_bold_div(self):
        # NVDA-style: single bold span in a div
        soup = _parse(
            '<div><span style="font-weight:700;font-size:10pt">Critical Accounting Estimates</span></div>'
        )
        div = soup.find("div")
        assert is_bold_only_block(div) is True

    def test_is_bold_only_block_rejects_td(self):
        soup = _parse('<td><span style="font-weight:700">Heading</span></td>')
        td = soup.find("td")
        assert is_bold_only_block(td) is False

    def test_is_bold_only_block_rejects_th(self):
        soup = _parse('<th><span style="font-weight:700">Heading</span></th>')
        th = soup.find("th")
        assert is_bold_only_block(th) is False

    def test_is_bold_only_block_rejects_table_descendant(self):
        soup = _parse(
            '<table><tr><td>'
            '<div><span style="font-weight:700">Bold Text In Table</span></div>'
            '</td></tr></table>'
        )
        div = soup.find("div")
        assert is_bold_only_block(div) is False

    def test_is_bold_only_block_rejects_nested_block(self):
        # div contains a nested p — should be rejected
        soup = _parse(
            '<div><p><span style="font-weight:700">Nested</span></p></div>'
        )
        div = soup.find("div")
        assert is_bold_only_block(div) is False

    def test_is_bold_only_block_rejects_nested_div(self):
        soup = _parse(
            '<div><div><span style="font-weight:700">Inner</span></div></div>'
        )
        outer_div = soup.find("div")
        assert is_bold_only_block(outer_div) is False

    def test_is_bold_only_block_rejects_nested_table(self):
        soup = _parse(
            '<div>'
            '<span style="font-weight:700">Text</span>'
            '<table><tr><td>cell</td></tr></table>'
            '</div>'
        )
        div = soup.find("div")
        assert is_bold_only_block(div) is False

    def test_is_bold_only_block_rejects_numeric(self):
        # purely numeric text — page number guard
        soup = _parse('<div><span style="font-weight:700">42</span></div>')
        div = soup.find("div")
        assert is_bold_only_block(div) is False

    def test_is_bold_only_block_rejects_too_short(self):
        # text length < _MIN_HEADING_TEXT_LEN (3)
        soup = _parse('<div><span style="font-weight:700">Hi</span></div>')
        div = soup.find("div")
        assert is_bold_only_block(div) is False

    def test_is_bold_only_block_rejects_too_long(self):
        # text length > _MAX_HEADING_TEXT_LEN (200)
        long_text = "A" * 201
        soup = _parse(f'<div><span style="font-weight:700">{long_text}</span></div>')
        div = soup.find("div")
        assert is_bold_only_block(div) is False

    def test_is_bold_only_block_rejects_sentence_ending(self):
        # text > 30 chars ending with "."
        text = "This is a long sentence that ends with a period."
        assert len(text) > 30
        soup = _parse(f'<div><span style="font-weight:700">{text}</span></div>')
        div = soup.find("div")
        assert is_bold_only_block(div) is False

    def test_is_bold_only_block_rejects_sentence_ending_exclamation(self):
        text = "This is a very long heading that ends with exclamation!"
        assert len(text) > 30
        soup = _parse(f'<div><span style="font-weight:700">{text}</span></div>')
        div = soup.find("div")
        assert is_bold_only_block(div) is False

    def test_is_bold_only_block_rejects_sentence_ending_question(self):
        text = "This is a very long heading that ends with question mark?"
        assert len(text) > 30
        soup = _parse(f'<div><span style="font-weight:700">{text}</span></div>')
        div = soup.find("div")
        assert is_bold_only_block(div) is False

    def test_is_bold_only_block_allows_short_dot_ending(self):
        # text <= 30 chars ending with "." is allowed (sentence-end rule only applies when len > 30)
        # "Item 1A." is 8 chars — passes sentence-end rule but is too short if < 3, or here it passes
        soup = _parse(
            '<div><span style="font-weight:700">Note 1. Summary</span></div>'
        )
        div = soup.find("div")
        # "Note 1. Summary" = 15 chars, <= 30 → sentence-end rule does NOT apply
        assert is_bold_only_block(div) is True

    def test_is_bold_only_block_rejects_mixed_bold_plain(self):
        # one span is bold, one has no bold styling — plain text mixing
        soup = _parse(
            '<div>'
            '<span style="font-weight:700">Bold part</span>'
            '<span>plain part</span>'
            '</div>'
        )
        div = soup.find("div")
        assert is_bold_only_block(div) is False

    def test_is_bold_only_block_p_tag_accepted(self):
        soup = _parse(
            '<p><span style="font-weight:700">Market Risk Management</span></p>'
        )
        p = soup.find("p")
        assert is_bold_only_block(p) is True

    def test_is_bold_only_block_allows_bold_keyword(self):
        # font-weight:bold (not 700) should also count
        soup = _parse(
            '<div><span style="font-weight:bold">Revenue Recognition Policy</span></div>'
        )
        div = soup.find("div")
        assert is_bold_only_block(div) is True

    def test_is_bold_only_block_multiple_bold_spans(self):
        # multiple bold spans, all bold — should pass
        soup = _parse(
            '<div>'
            '<span style="font-weight:700">Critical </span>'
            '<span style="font-weight:700">Accounting Policies</span>'
            '</div>'
        )
        div = soup.find("div")
        assert is_bold_only_block(div) is True

    def test_is_bold_only_block_rejects_div_with_non_bold_span_among_bold(self):
        # mixed: second span has no bold
        soup = _parse(
            '<div>'
            '<span style="font-weight:700">Critical</span>'
            '<span style="font-weight:400"> Accounting Policies</span>'
            '</div>'
        )
        div = soup.find("div")
        assert is_bold_only_block(div) is False

    def test_is_bold_only_block_inherited_bold_from_parent_div(self):
        # Real SEC 10-K pattern: bold on container div, font-size only on inner span
        soup = _parse(
            '<div style="font-weight:700">'
            '<span style="font-size:10pt">Critical Accounting Estimates</span>'
            '</div>'
        )
        div = soup.find("div")
        assert is_bold_only_block(div) is True

    def test_is_bold_only_block_inherited_bold_from_b_tag(self):
        soup = _parse(
            '<div><b><span style="font-size:10pt">Market Risk Management</span></b></div>'
        )
        div = soup.find("div")
        assert is_bold_only_block(div) is True

    def test_is_bold_only_block_no_spans_only_text(self):
        # div with bold style and direct text node (no inner spans)
        soup = _parse('<div style="font-weight:700">Plain Heading Text</div>')
        div = soup.find("div")
        assert is_bold_only_block(div) is True

    def test_is_bold_only_block_rejects_empty_bold_div(self):
        # bold div but no text — must return False
        soup = _parse('<div style="font-weight:700"></div>')
        div = soup.find("div")
        assert is_bold_only_block(div) is False


# ---------- extract_dominant_font_size (nested spans) ----------


class TestExtractDominantFontSizeNestedSpans:
    def test_extract_dominant_font_size_nested_spans_no_double_count(self):
        # 10pt has 5 chars (hello), 12pt has 6 chars (winner) — 12pt wins
        soup = _parse(
            '<div>'
            '<span style="font-size:10pt"><span style="font-size:10pt">hello</span></span>'
            '<span style="font-size:12pt">winner</span>'
            '</div>'
        )
        div = soup.find("div")
        assert extract_dominant_font_size(div) == 12.0
