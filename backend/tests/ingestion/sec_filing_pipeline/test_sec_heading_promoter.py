from bs4 import BeautifulSoup

from backend.ingestion.sec_filing_pipeline.sec_heading_promoter import (
    ItemRegion,
    build_noise_tokens,
    detect_item_regions,
    detect_part_anchors,
    extract_dominant_font_size,
    has_table_ancestor,
    is_bold_only_block,
    is_self_reference,
    promote_subsections,
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


# ---------- detect_item_regions ----------


class TestDetectItemRegions:
    def test_detect_item_regions_basic(self):
        # 3 Items, no TOC — returns 3 ItemRegions in order, end_tag chain correct
        soup = _parse(
            '<html><body>'
            '<p>Item 1. Business</p>'
            '<p>Some business text</p>'
            '<p>Item 2. Risk Factors</p>'
            '<p>Some risk text</p>'
            '<p>Item 3. Properties</p>'
            '<p>Some property text</p>'
            '</body></html>'
        )
        regions = detect_item_regions(soup)
        assert len(regions) == 3
        assert all(isinstance(r, ItemRegion) for r in regions)
        assert regions[0].item_num == "1"
        assert regions[1].item_num == "2"
        assert regions[2].item_num == "3"
        # end_tag chain: each region's end_tag is next region's start_tag
        assert regions[0].end_tag is regions[1].start_tag
        assert regions[1].end_tag is regions[2].start_tag
        assert regions[2].end_tag is None

    def test_detect_item_regions_with_toc(self):
        # Same item_num appears twice (TOC + body) — last occurrence (body) is selected
        soup = _parse(
            '<html><body>'
            '<p>Item 1. Business</p>'
            '<p>Item 2. Risk Factors</p>'
            '<p>--- TOC end ---</p>'
            '<div>Item 1. Business</div>'
            '<p>actual business content</p>'
            '<div>Item 2. Risk Factors</div>'
            '<p>actual risk content</p>'
            '</body></html>'
        )
        regions = detect_item_regions(soup)
        assert len(regions) == 2
        # body occurrence is a <div>, TOC occurrence is a <p>
        assert regions[0].start_tag.name == "div"
        assert regions[1].start_tag.name == "div"

    def test_detect_item_regions_empty_html(self):
        soup = _parse('<html></html>')
        assert detect_item_regions(soup) == []

    def test_detect_item_regions_xom_table_cell(self):
        # XOM-style: Item heading inside a <td>
        soup = _parse(
            '<html><body>'
            '<table><tr><td>Item 1. Business</td></tr></table>'
            '<p>Business content</p>'
            '<table><tr><td>Item 2. Risk Factors</td></tr></table>'
            '<p>Risk content</p>'
            '</body></html>'
        )
        regions = detect_item_regions(soup)
        assert len(regions) == 2
        assert regions[0].item_num == "1"
        assert regions[0].start_tag.name == "td"
        assert regions[1].item_num == "2"

    def test_detect_item_regions_preserves_order(self):
        # Items in non-numeric document order: 5, 1, 10, 2 — must preserve document order
        soup = _parse(
            '<html><body>'
            '<p>Item 5. Selected Data</p>'
            '<p>Item 1. Business</p>'
            '<p>Item 10. Directors</p>'
            '<p>Item 2. Risk Factors</p>'
            '</body></html>'
        )
        regions = detect_item_regions(soup)
        assert len(regions) == 4
        assert [r.item_num for r in regions] == ["5", "1", "10", "2"]

    def test_drops_toc_only_items_before_body_start(self):
        # BRK.A/B-style: Items 10/11 only exist in TOC <table>; body has
        # only Items 1 and 15. The TOC anchors must be dropped so the
        # final region order is monotonic and limited to body anchors.
        soup = _parse(
            '<html><body>'
            '<table><tr>'
            '<td>Item 1.</td>'
            '<td>Item 10.</td>'
            '<td>Item 11.</td>'
            '</tr></table>'
            '<div>Item 1. Business</div>'
            '<p>Business content</p>'
            '<div>Item 15. Exhibits</div>'
            '<p>Exhibits content</p>'
            '</body></html>'
        )
        regions = detect_item_regions(soup)
        item_nums = [r.item_num for r in regions]
        assert item_nums == ["1", "15"]
        for r in regions:
            assert r.start_tag.name == "div"

    def test_keeps_all_when_fully_table_layout(self):
        # Hypothetical filing where all Items live inside <table> cells
        # (no body anchors at all). non_table_positions is empty, so the
        # drop pass falls through and every item is kept.
        soup = _parse(
            '<html><body>'
            '<table>'
            '<tr><td>Item 1. Business</td></tr>'
            '<tr><td>Item 2. Properties</td></tr>'
            '<tr><td>Item 3. Legal</td></tr>'
            '</table>'
            '</body></html>'
        )
        regions = detect_item_regions(soup)
        assert [r.item_num for r in regions] == ["1", "2", "3"]

    def test_keeps_body_table_items_after_non_table_start(self):
        # Mixed: first body Item is non-table; a later Item lives inside
        # a body layout table. The table-ancestor item is AFTER body_start
        # so the drop rule does not apply and both are kept.
        soup = _parse(
            '<html><body>'
            '<div>Item 1. Business</div>'
            '<p>Business content</p>'
            '<table><tr><td>Item 2. Properties</td></tr></table>'
            '<p>Properties content</p>'
            '</body></html>'
        )
        regions = detect_item_regions(soup)
        assert [r.item_num for r in regions] == ["1", "2"]

    def test_keeps_non_table_toc_and_body(self):
        # TOC entry is a non-table <div> followed by the body <div>.
        # last-occurrence dedup picks the body anchor; the C1 drop rule
        # does not interfere because neither tag has a table ancestor.
        soup = _parse(
            '<html><body>'
            '<div>Item 1.</div>'
            '<p>cover content</p>'
            '<div>Item 1. Business</div>'
            '<p>actual business content</p>'
            '</body></html>'
        )
        regions = detect_item_regions(soup)
        assert len(regions) == 1
        assert regions[0].item_num == "1"
        assert regions[0].start_tag.get_text(strip=True) == "Item 1. Business"

    def test_detect_item_regions_subnumbered(self):
        # Items 1, 1A, 1B, 1C, 2 — 5 distinct regions in order
        soup = _parse(
            '<html><body>'
            '<p>Item 1. Business</p>'
            '<p>Item 1A. Risk Factors</p>'
            '<p>Item 1B. Unresolved Staff Comments</p>'
            '<p>Item 1C. Cybersecurity</p>'
            '<p>Item 2. Properties</p>'
            '</body></html>'
        )
        regions = detect_item_regions(soup)
        assert len(regions) == 5
        assert [r.item_num for r in regions] == ["1", "1A", "1B", "1C", "2"]
        # verify end_tag chain
        for i in range(len(regions) - 1):
            assert regions[i].end_tag is regions[i + 1].start_tag
        assert regions[-1].end_tag is None

    def test_detect_item_regions_text_split_across_spans(self):
        # Donnelley/Workiva sometimes split heading text across adjacent
        # spans, with the whitespace living in a separate text node:
        # <span>Item</span><span>&nbsp;7.</span><span> MD&A</span>.
        # get_text(strip=True) would collapse this to "Item7.MD&A" and
        # break the Item regex; the normalized path must still detect it.
        soup = _parse(
            '<html><body>'
            '<div><span>Item</span><span>&nbsp;7.</span><span> MD&A</span></div>'
            '</body></html>'
        )
        regions = detect_item_regions(soup)
        assert len(regions) == 1
        assert regions[0].item_num == "7"


# ---------- detect_part_anchors ----------


class TestDetectPartAnchors:
    def test_single_part_kept(self):
        soup = _parse('<html><body><div>PART I</div></body></html>')
        anchors = detect_part_anchors(soup)
        assert len(anchors) == 1
        assert anchors[0].get_text(strip=True) == "PART I"

    def test_no_parts_returns_empty(self):
        soup = _parse(
            '<html><body><p>no part text here</p><div>just business</div></body></html>'
        )
        assert detect_part_anchors(soup) == []

    def test_toc_and_body_keeps_last(self):
        soup = _parse(
            '<html><body>'
            '<div id="toc">PART I</div>'
            '<p>table of contents stuff</p>'
            '<div id="body">PART I</div>'
            '<p>actual body content</p>'
            '</body></html>'
        )
        anchors = detect_part_anchors(soup)
        assert len(anchors) == 1
        assert anchors[0].get("id") == "body"

    def test_three_occurrences_keeps_last(self):
        soup = _parse(
            '<html><body>'
            '<div id="toc">PART I</div>'
            '<p>as defined in PART I earlier</p>'
            '<div id="xref">PART I</div>'
            '<div id="body">PART I</div>'
            '</body></html>'
        )
        anchors = detect_part_anchors(soup)
        assert len(anchors) == 1
        assert anchors[0].get("id") == "body"

    def test_multiple_part_numerals_kept(self):
        soup = _parse(
            '<html><body>'
            '<div id="toc-1">PART I</div>'
            '<div id="toc-2">PART II</div>'
            '<div id="toc-3">PART III</div>'
            '<div id="toc-4">PART IV</div>'
            '<p>--- body begins ---</p>'
            '<div id="body-1">PART I</div>'
            '<div id="body-2">PART II</div>'
            '<div id="body-3">PART III</div>'
            '<div id="body-4">PART IV</div>'
            '</body></html>'
        )
        anchors = detect_part_anchors(soup)
        assert len(anchors) == 4
        assert [a.get("id") for a in anchors] == [
            "body-1",
            "body-2",
            "body-3",
            "body-4",
        ]

    def test_split_span_part_text(self):
        soup = _parse(
            '<html><body>'
            '<div><span>PART</span><span> I</span></div>'
            '</body></html>'
        )
        anchors = detect_part_anchors(soup)
        assert len(anchors) == 1
        # normalized text equals "PART I" when using " ".join(split())
        assert " ".join(anchors[0].get_text().split()) == "PART I"

    def test_case_insensitive_part_text(self):
        soup = _parse('<html><body><div>part i</div></body></html>')
        anchors = detect_part_anchors(soup)
        assert len(anchors) == 1

    def test_eligibility_filter_keeps_last_eligible(self):
        # Body PART I is non-bold; eligibility predicate rejects it.
        # The earlier (TOC) tag passes the predicate, so it must be kept
        # instead of the body tag silently dropping out. This mirrors
        # JNJ/MSFT-style filings where body PART dividers are non-bold.
        soup = _parse(
            '<html><body>'
            '<div id="toc"><b>PART I</b></div>'
            '<p>cover content</p>'
            '<div id="body">PART I</div>'
            '</body></html>'
        )

        def is_bold(tag):
            return tag.find("b") is not None or tag.name == "b"

        anchors = detect_part_anchors(soup, is_eligible=is_bold)
        assert len(anchors) == 1
        assert anchors[0].get("id") == "toc"

    def test_eligibility_filter_picks_last_among_eligible(self):
        # Three body PART I occurrences, only the middle one passes the
        # eligibility check; that's the anchor that must be kept.
        soup = _parse(
            '<html><body>'
            '<div id="first">PART I</div>'
            '<div id="middle"><b>PART I</b></div>'
            '<div id="last">PART I</div>'
            '</body></html>'
        )

        def is_bold(tag):
            return tag.find("b") is not None

        anchors = detect_part_anchors(soup, is_eligible=is_bold)
        assert len(anchors) == 1
        assert anchors[0].get("id") == "middle"


# ---------- promote_subsections ----------


class TestPromoteSubsections:
    def test_promote_subsections_single_font_size_all_h3(self):
        # 3 bold blocks all same font-size → all become h3
        soup = _parse(
            '<html><body>'
            '<p style="font-weight:700">Item 1. Business</p>'
            '<div><span style="font-weight:700;font-size:10pt">Our Company</span></div>'
            '<div><span style="font-weight:700;font-size:10pt">Our Products</span></div>'
            '<div><span style="font-weight:700;font-size:10pt">Our Markets</span></div>'
            '</body></html>'
        )
        item_tag = soup.find("p")
        regions = [ItemRegion(item_num="1", start_tag=item_tag, end_tag=None)]
        promote_subsections(soup, regions)
        headings = [t.name for t in soup.find_all(["h3", "h4", "h5"])]
        assert headings == ["h3", "h3", "h3"]
        texts = [t.get_text(strip=True) for t in soup.find_all("h3")]
        assert texts == ["Our Company", "Our Products", "Our Markets"]

    def test_promote_subsections_two_sizes_h3_h4(self):
        # 2 unique font-sizes: largest → h3, smaller → h4
        soup = _parse(
            '<html><body>'
            '<p style="font-weight:700">Item 1. Business</p>'
            '<div><span style="font-weight:700;font-size:12pt">Big Heading</span></div>'
            '<div><span style="font-weight:700;font-size:10pt">Small Heading</span></div>'
            '</body></html>'
        )
        item_tag = soup.find("p")
        regions = [ItemRegion(item_num="1", start_tag=item_tag, end_tag=None)]
        promote_subsections(soup, regions)
        h3_texts = [t.get_text(strip=True) for t in soup.find_all("h3")]
        h4_texts = [t.get_text(strip=True) for t in soup.find_all("h4")]
        assert h3_texts == ["Big Heading"]
        assert h4_texts == ["Small Heading"]

    def test_promote_subsections_three_sizes_h3_h4_h5(self):
        # 3 unique sizes → largest h3, middle h4, smallest h5
        soup = _parse(
            '<html><body>'
            '<p style="font-weight:700">Item 1. Business</p>'
            '<div><span style="font-weight:700;font-size:12pt">Level One</span></div>'
            '<div><span style="font-weight:700;font-size:10pt">Level Two</span></div>'
            '<div><span style="font-weight:700;font-size:8pt">Level Three</span></div>'
            '</body></html>'
        )
        item_tag = soup.find("p")
        assert item_tag is not None
        regions = [ItemRegion(item_num="1", start_tag=item_tag, end_tag=None)]
        promote_subsections(soup, regions)
        h3_texts = [t.get_text(strip=True) for t in soup.find_all("h3")]
        h4_texts = [t.get_text(strip=True) for t in soup.find_all("h4")]
        h5_texts = [t.get_text(strip=True) for t in soup.find_all("h5")]
        assert h3_texts == ["Level One"]
        assert h4_texts == ["Level Two"]
        assert h5_texts == ["Level Three"]

    def test_promote_subsections_four_sizes_caps_at_h5(self):
        # 4 unique sizes: idx0→h3, idx1→h4, idx2+→h5 (cap)
        soup = _parse(
            '<html><body>'
            '<p style="font-weight:700">Item 1. Business</p>'
            '<div><span style="font-weight:700;font-size:14pt">Alpha</span></div>'
            '<div><span style="font-weight:700;font-size:12pt">Beta</span></div>'
            '<div><span style="font-weight:700;font-size:10pt">Gamma</span></div>'
            '<div><span style="font-weight:700;font-size:8pt">Delta</span></div>'
            '</body></html>'
        )
        item_tag = soup.find("p")
        assert item_tag is not None
        regions = [ItemRegion(item_num="1", start_tag=item_tag, end_tag=None)]
        promote_subsections(soup, regions)
        h3_texts = [t.get_text(strip=True) for t in soup.find_all("h3")]
        h4_texts = [t.get_text(strip=True) for t in soup.find_all("h4")]
        h5_texts = [t.get_text(strip=True) for t in soup.find_all("h5")]
        assert h3_texts == ["Alpha"]
        assert h4_texts == ["Beta"]
        assert h5_texts == ["Gamma", "Delta"]

    def test_promote_subsections_excludes_blocks_in_tables(self):
        # bold block inside a <td> must not be promoted
        soup = _parse(
            '<html><body>'
            '<p style="font-weight:700">Item 1. Business</p>'
            '<table><tr><td>'
            '<div><span style="font-weight:700;font-size:10pt">Table Header</span></div>'
            '</td></tr></table>'
            '</body></html>'
        )
        item_tag = soup.find("p")
        regions = [ItemRegion(item_num="1", start_tag=item_tag, end_tag=None)]
        promote_subsections(soup, regions)
        assert soup.find("h3") is None
        assert soup.find("h4") is None
        assert soup.find("h5") is None

    def test_promote_subsections_outside_item_region_untouched(self):
        # bold block outside any ItemRegion (before first Item) must not be promoted
        soup = _parse(
            '<html><body>'
            '<div><span style="font-weight:700;font-size:10pt">Cover Page Heading</span></div>'
            '<p style="font-weight:700">Item 1. Business</p>'
            '<div><span style="font-weight:700;font-size:10pt">Inside Region</span></div>'
            '</body></html>'
        )
        item_tag = soup.find("p")
        regions = [ItemRegion(item_num="1", start_tag=item_tag, end_tag=None)]
        promote_subsections(soup, regions)
        # "Cover Page Heading" is OUTSIDE the region — must remain <div>
        all_divs = soup.find_all("div")
        cover_div = next(
            (d for d in all_divs if "Cover Page Heading" in d.get_text()), None
        )
        assert cover_div is not None, "Cover Page Heading div should still exist as div"
        # "Inside Region" should be promoted
        assert soup.find("h3") is not None

    def test_promote_subsections_footnote_marker_ignored_in_ranking(self):
        # Heading text at 9pt (many chars) wins over footnote "1" at 6pt (1 char).
        # All headings land on h3 since there is only one effective size.
        soup = _parse(
            '<html><body>'
            '<p style="font-weight:700">Item 1. Business</p>'
            '<div>'
            '<span style="font-weight:700;font-size:9pt">Critical Accounting Estimates</span>'
            '<span style="font-weight:700;font-size:6pt">1</span>'
            '</div>'
            '</body></html>'
        )
        item_tag = soup.find("p")
        regions = [ItemRegion(item_num="1", start_tag=item_tag, end_tag=None)]
        promote_subsections(soup, regions)
        # The dominant size is 9pt; heading should be h3
        h3 = soup.find("h3")
        assert h3 is not None
        assert "Critical Accounting Estimates" in h3.get_text()


# ---------- build_noise_tokens ----------


class TestBuildNoiseTokens:
    def test_build_noise_tokens_page_header(self):
        # "Part I" repeated 20 times across block elements → must be in noise set
        repeated = '<p>Part I</p>' * 20
        soup = _parse(f'<html><body>{repeated}</body></html>')
        noise = build_noise_tokens(soup)
        assert "Part I" in noise

    def test_build_noise_tokens_infrequent_text_not_noise(self):
        # "Our Company" appears only once → not a noise token
        soup = _parse('<html><body><p>Our Company</p></body></html>')
        noise = build_noise_tokens(soup)
        assert "Our Company" not in noise

    def test_build_noise_tokens_boundary_below_threshold(self):
        # Text appearing exactly 3 times (threshold is 4) → not in noise set
        repeated = '<p>Section Header</p>' * 3
        soup = _parse(f'<html><body>{repeated}</body></html>')
        noise = build_noise_tokens(soup)
        assert "Section Header" not in noise

    def test_build_noise_tokens_long_text_excluded(self):
        # Text longer than 50 chars must not be included even if repeated many times
        long_text = "A" * 51
        repeated = f'<p>{long_text}</p>' * 20
        soup = _parse(f'<html><body>{repeated}</body></html>')
        noise = build_noise_tokens(soup)
        assert long_text not in noise


# ---------- is_self_reference ----------


class TestIsSelfReference:
    def test_is_self_reference_item_7a_body(self):
        assert is_self_reference("Item 7A Risk") is True

    def test_is_self_reference_non_item_text(self):
        assert is_self_reference("Critical Accounting Estimates") is False


# ---------- promote_subsections with false positive filters ----------


class TestPromoteSubsectionsFilters:
    def test_promote_subsections_skips_noise_token_blocks(self):
        # "Part I" appears 5 times across the document → qualifies as noise → not promoted
        repeated_headers = '<div style="font-weight:700"><span style="font-size:10pt">Part I</span></div>' * 5
        soup = _parse(
            '<html><body>'
            f'{repeated_headers}'
            '<p style="font-weight:700">Item 1. Business</p>'
            '<div style="font-weight:700"><span style="font-size:10pt">Part I</span></div>'
            '</body></html>'
        )
        item_tag = soup.find("p")
        regions = [ItemRegion(item_num="1", start_tag=item_tag, end_tag=None)]
        promote_subsections(soup, regions)
        # "Part I" should not be promoted to any heading level
        all_headings = soup.find_all(["h3", "h4", "h5"])
        heading_texts = [h.get_text(strip=True) for h in all_headings]
        assert "Part I" not in heading_texts

    def test_promote_subsections_skips_self_reference(self):
        # Inside Item 7 region, a bold block starting with "Item 7A." should not be promoted
        soup = _parse(
            '<html><body>'
            '<p style="font-weight:700">Item 7. Management Discussion</p>'
            '<div><span style="font-weight:700;font-size:10pt">Item 7A. Quantitative</span></div>'
            '<div><span style="font-weight:700;font-size:10pt">Critical Accounting Estimates</span></div>'
            '</body></html>'
        )
        item_tag = soup.find("p")
        regions = [ItemRegion(item_num="7", start_tag=item_tag, end_tag=None)]
        promote_subsections(soup, regions)
        all_headings = soup.find_all(["h3", "h4", "h5"])
        heading_texts = [h.get_text(strip=True) for h in all_headings]
        # self-reference "Item 7A. Quantitative" must not be promoted
        assert not any(t.startswith("Item 7A") for t in heading_texts)
        # the legitimate sub-section heading should still be promoted
        assert "Critical Accounting Estimates" in heading_texts
