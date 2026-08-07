"""Acceptance tests: detection results vs the 72-probe known outcomes.

``fixtures_detection_probes.json`` is recorded from the real latest 10-Ks
(2026-08-05 probe vintage) via edgartools: per ticker, the filing-level
markdown heading LINES (order- and duplicate-preserving; prose dropped) and
the raw section text of the probed items. Tests run the full
``parse_filing`` path over fakes at the fetch seams — no EDGAR.

Known results under test (DEV-133 acceptance criteria, from
``research_prelude_size_v3.md``):

- CAT 7 / 1A: flagship true preludes (~2.5k chars) attached whole
- WMT 1A: markdown_h4 path, true prelude ~800 chars
- JPM 1A: pseudo-prelude (~6.4k) reclassified as heading-less leading block
- WMT 1 / CAT 1: markdown_h4 multi-block, prelude absent
- DIS 7: false-valid prelude — recorded KNOWN LIMITATION, not fixed
"""

import json
from pathlib import Path

import pytest

from backend.common.sec_core import FetchedFiling
from backend.ingestion.sec_text_pipeline import parser
from backend.ingestion.sec_text_pipeline.filing_models import (
    ParsedFiling,
    StructuredItem,
)
from backend.tests.ingestion.sec_text_pipeline.conftest import FakeTenK

PROBES = json.loads(
    (Path(__file__).parent / "fixtures_detection_probes.json").read_text(
        encoding="utf-8"
    )
)


@pytest.fixture
def parse_probe(monkeypatch, store):
    """Parse one recorded probe filing through the real parse_filing path."""

    def _parse(ticker: str) -> ParsedFiling:
        data = PROBES[ticker]
        tenk = FakeTenK(
            sections_data={
                f"item_{key}": {"item": key, "text": text}
                for key, text in data["sections"].items()
            },
            period_of_report=data["period_of_report"],
            filing_date=data["filing_date"],
        )
        bundle = FetchedFiling(
            tenk=tenk,
            accession_number=data["accession_number"],
            cik=data["cik"],
            company_name=data["company"],
            primary_document="primary.htm",
        )
        monkeypatch.setattr(parser, "fetch_filing_bundle", lambda *a, **k: bundle)
        monkeypatch.setattr(
            parser,
            "fetch_filing_markdown",
            lambda *a, **k: "\n".join(data["heading_lines"]),
        )
        return parser.parse_filing(ticker, fiscal_year=2025, store=store)

    return _parse


def get_structured(filing: ParsedFiling, item: str) -> StructuredItem:
    found = next(i for i in filing.items if i.item == item)
    assert isinstance(found, StructuredItem), (
        f"item {item} expected structured, got {type(found).__name__}"
    )
    return found


class TestFlagshipTruePreludes:
    def test_cat_7_prelude_attached_whole(self, parse_probe):
        md_and_a = get_structured(parse_probe("CAT"), "7")
        assert md_and_a.detection_source == "markdown_h3"
        # ~2.5k flagship true prelude, attached whole — not truncated.
        assert 2400 <= len(md_and_a.prelude) <= 2650
        assert "should be read in conjunction" in md_and_a.prelude
        assert [b.heading for b in md_and_a.blocks[:2]] == [
            "OVERVIEW",
            "CONSOLIDATED SALES AND REVENUES",
        ]

    def test_cat_1a_prelude_attached_whole(self, parse_probe):
        risk = get_structured(parse_probe("CAT"), "1a")
        assert risk.detection_source == "markdown_h4"
        # The largest true prelude in the 72-probe sample (~2.5k chars,
        # verbatim — the Item's own heading line stays in it).
        assert 2400 <= len(risk.prelude) <= 2650
        assert risk.prelude.startswith("Item 1A.Risk Factors.")
        assert "The statements in this section" in risk.prelude
        assert [b.heading for b in risk.blocks] == [
            "MACROECONOMIC RISKS",
            "OPERATIONAL RISKS",
            "FINANCIAL RISKS",
            "LEGAL & REGULATORY RISKS",
        ]

    def test_wmt_1a_h4_path_with_true_prelude(self, parse_probe):
        risk = get_structured(parse_probe("WMT"), "1a")
        assert risk.detection_source == "markdown_h4"
        # True prelude ~800 chars (framing text, not swallowed body).
        assert 700 <= len(risk.prelude) <= 900
        assert "The risks described below" in risk.prelude
        assert [b.heading for b in risk.blocks] == [
            "Strategic Risks",
            "Operational Risks",
        ]


class TestPseudoPreludeReclassification:
    def test_jpm_1a_reclassified_as_leading_block(self, parse_probe):
        risk = get_structured(parse_probe("JPM"), "1a")
        assert risk.detection_source == "markdown_h4"
        assert risk.prelude == ""  # pseudo-prelude is NOT prelude metadata
        lead = risk.blocks[0]
        assert lead.heading == ""  # heading-less leading block
        # ~6.4k chars of swallowed body text, kept chunkable.
        assert 6000 <= len(lead.text) <= 7000
        assert len(risk.blocks) >= 10  # real risk-category blocks follow
        assert risk.blocks[1].heading == "Legal and Regulatory"

    def test_jpm_1a_zero_content_loss(self, parse_probe):
        # Every substantive line of the Item body must survive in the
        # chunkable content (prelude is empty here, so blocks carry it all).
        risk = get_structured(parse_probe("JPM"), "1a")
        chunkable = "\n".join(
            part for b in risk.blocks for part in (b.heading, b.text) if part
        )
        raw = PROBES["JPM"]["sections"]["1a"]
        trimmed = parser._trim_section_text(raw, "1a")
        missing = [
            line.strip()
            for line in trimmed.splitlines()[1:]  # self-heading -> title
            if line.strip() and line.strip() not in chunkable
        ]
        assert missing == []


class TestNoPreludeMultiBlock:
    """The "prelude 0" probe cases: no framing prose before the first block.

    Since the prelude is verbatim (no carve-outs), the Item's own heading
    line — the only text before the first anchor — remains as a tiny
    prelude; the assertions pin "heading line only, no prose".
    """

    def test_wmt_1_h4_multi_block_no_prelude_prose(self, parse_probe):
        business = get_structured(parse_probe("WMT"), "1")
        assert business.detection_source == "markdown_h4"
        assert business.prelude.upper().startswith("ITEM")
        assert len(business.prelude) < 40  # the heading line, nothing else
        assert len(business.blocks) >= 5
        assert business.blocks[0].heading == "General"

    def test_cat_1_h4_multi_block_no_prelude_prose(self, parse_probe):
        business = get_structured(parse_probe("CAT"), "1")
        assert business.detection_source == "markdown_h4"
        assert business.prelude.startswith("Item 1.")
        assert len(business.prelude) < 40
        assert len(business.blocks) >= 15
        assert business.blocks[0].heading == "General"


class TestKnownLimitations:
    def test_dis_7_false_valid_prelude_current_behavior(self, parse_probe):
        """KNOWN LIMITATION (spec Known Limitations #1) — deliberately NOT fixed.

        DIS Item 7 hides ~2.6k chars of disguised body content (summary
        tables) under the validity threshold, so it is attached as a
        "valid" prelude and stays out of the index: bounded content loss,
        <= 3,000 chars. Size cannot discriminate here (true preludes reach
        2,532; this false one is 2,610), so threshold tuning would overfit
        a single sample. If A/B failure mining surfaces more of this shape,
        the fix is a content signal (digit/table density), not a threshold
        change. This test records the current behavior; if it ever fails,
        detection behavior changed — re-read the spec before "fixing" it.
        """
        md_and_a = get_structured(parse_probe("DIS"), "7")
        assert md_and_a.detection_source == "markdown_h3"
        # False-valid: passes the size gate...
        assert 2500 <= len(md_and_a.prelude) <= 3000
        # ...but the content is tabular summary data, not framing prose.
        assert "TABLE OF CONTENTS" in md_and_a.prelude
