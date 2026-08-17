"""Structure assertions for the inspect render views.

All inputs are toy ParsedFiling objects built from the conftest factories —
no EDGAR access. The prelude-verdict inference (valid / reclassified /
absent) is the load-bearing render rule, so each state gets its own
assertion against the exact schema shape that produces it.
"""

import pytest

from backend.ingestion.sec_text_pipeline.filing_models import (
    Block,
    FlatItem,
    ParsedFiling,
)
from backend.ingestion.sec_text_pipeline.inspect_view import (
    to_inspect_markdown,
    to_section_text,
    to_summary_text,
)
from backend.tests.ingestion.sec_text_pipeline.conftest import (
    make_metadata,
    make_structured_item,
)

FLAT_BODY = "Flat item body text about risk factors, long enough to matter."


def make_filing(items) -> ParsedFiling:
    return ParsedFiling(metadata=make_metadata(), items=items)


@pytest.fixture
def valid_prelude_item():
    return make_structured_item()  # default: non-empty prelude, one block


@pytest.fixture
def reclassified_item():
    return make_structured_item(
        item="1",
        title="Business",
        prelude="",
        blocks=[
            Block(heading="", text="x" * 3500),
            Block(heading="OVERVIEW", text="Segment details..."),
        ],
        detection_source="markdown_h4",
    )


@pytest.fixture
def absent_prelude_item():
    return make_structured_item(
        item="7a",
        title="Quantitative and Qualitative Disclosures About Market Risk",
        prelude="",
        blocks=[Block(heading="INTEREST RATE RISK", text="We are exposed to...")],
    )


@pytest.fixture
def flat_item():
    return FlatItem(item="1a", title="Risk Factors", text=FLAT_BODY)


class TestInspectMarkdown:
    def test_metadata_header(self, valid_prelude_item):
        md = to_inspect_markdown(make_filing([valid_prelude_item]))
        m = make_metadata()
        assert f"# {m.ticker} 10-K FY{m.fiscal_year}" in md
        assert m.accession_number in md
        assert m.primary_document in md

    def test_structured_item_fields(self, valid_prelude_item):
        md = to_inspect_markdown(make_filing([valid_prelude_item]))
        assert f"## Item 7 — {valid_prelude_item.title}" in md
        assert "- kind: structured" in md
        assert "- detection_source: markdown_h3" in md
        assert f"- prelude: valid ({len(valid_prelude_item.prelude):,} chars)" in md
        assert "### [prelude]" in md
        assert valid_prelude_item.prelude in md
        assert "### Block 1/1 — OVERVIEW" in md
        assert valid_prelude_item.blocks[0].text in md

    def test_reclassified_verdict(self, reclassified_item):
        md = to_inspect_markdown(make_filing([reclassified_item]))
        assert "- prelude: reclassified leading block (3,500 chars in blocks[0])" in md
        assert "### [prelude]" not in md
        assert "### Block 1/2 — (reclassified leading block)" in md
        assert "x" * 3500 in md  # reclassified text stays fully rendered

    def test_absent_verdict(self, absent_prelude_item):
        md = to_inspect_markdown(make_filing([absent_prelude_item]))
        assert "- prelude: absent" in md
        assert "### [prelude]" not in md

    def test_flat_item_fields(self, flat_item):
        md = to_inspect_markdown(make_filing([flat_item]))
        assert "## Item 1a — Risk Factors" in md
        assert "- kind: flat" in md
        assert f"- text: {len(FLAT_BODY):,} chars" in md
        assert FLAT_BODY in md  # under the head+tail budget: shown in full
        assert "chars omitted" not in md  # no truncation marker on short text
        assert "detection_source" not in md.split("## Item 1a")[1]

    def test_flat_item_long_text_shows_head_and_tail(self):
        # A boundary bleed (parser._trim_section_text) only shows up at the
        # tail, so the preview must surface both ends, not just the head.
        long_text = "H" * 500 + "MIDDLE" * 100 + "T" * 500
        item = FlatItem(item="9b", title="Other Information", text=long_text)
        md = to_inspect_markdown(make_filing([item]))
        assert f"- text: {len(long_text):,} chars" in md  # count reflects the full text
        assert "H" * 500 in md  # head shown in full
        assert "T" * 500 in md  # tail shown in full
        assert "MIDDLE" not in md  # omitted middle doesn't leak through
        assert "600 chars omitted" in md  # explicit count, not a bare ellipsis


class TestSummaryText:
    def test_counts_and_rows(self, valid_prelude_item, flat_item):
        summary = to_summary_text(make_filing([valid_prelude_item, flat_item]))
        assert "2 items (structured 1 / flat 1)" in summary
        rows = summary.splitlines()
        item_rows = [r for r in rows if r.startswith(("7 ", "1a "))]
        assert len(item_rows) == 2
        assert "markdown_h3" in item_rows[0]
        assert "flat" in item_rows[1]

    def test_excludes_body_content(self, valid_prelude_item, flat_item):
        summary = to_summary_text(make_filing([valid_prelude_item, flat_item]))
        assert valid_prelude_item.blocks[0].text not in summary
        assert FLAT_BODY not in summary

    def test_reclassified_row_verdict_is_compact(self, reclassified_item):
        summary = to_summary_text(make_filing([reclassified_item]))
        assert "reclassified (3,500 chars)" in summary
        assert "blocks[0]" not in summary


class TestSectionText:
    def test_flat_section_is_raw_text(self, flat_item):
        assert to_section_text(make_filing([flat_item]), "1a") == FLAT_BODY

    def test_structured_section_keeps_all_content(self, valid_prelude_item):
        text = to_section_text(make_filing([valid_prelude_item]), "7")
        assert valid_prelude_item.prelude in text
        assert "OVERVIEW" in text
        assert valid_prelude_item.blocks[0].text in text
        assert "##" not in text  # plain text, no markdown headers

    def test_structured_section_blocks_stay_separated(self):
        item = make_structured_item(
            prelude="Overview of operations.",
            blocks=[
                Block(heading="RESULTS", text="Revenue ended continuing operations."),
                Block(heading="LIQUIDITY", text="Legal proceedings include claims."),
            ],
        )
        text = to_section_text(make_filing([item]), item.item)
        assert text == (
            "Overview of operations."
            "\n\nRESULTS\n\nRevenue ended continuing operations."
            "\n\nLIQUIDITY\n\nLegal proceedings include claims."
        )

    def test_key_is_case_insensitive(self, flat_item):
        filing = make_filing([flat_item])
        assert to_section_text(filing, "1A") == FLAT_BODY
        assert to_section_text(filing, " 1a ") == FLAT_BODY

    def test_unknown_key_lists_available(self, valid_prelude_item, flat_item):
        filing = make_filing([valid_prelude_item, flat_item])
        with pytest.raises(ValueError, match=r"available: 7, 1a"):
            to_section_text(filing, "99")
