"""Acceptance tests: detection results vs the 72-probe known outcomes.

``fixtures_detection_probes.json`` is recorded from the real latest 10-Ks
(CAT/WMT/JPM/DIS at the 2026-08-05 probe vintage; MSFT/GE and the 7A
sections added 2026-08-11 from the same accessions where the ticker
already existed) via edgartools: per ticker, the filing-level markdown
heading LINES (order- and duplicate-preserving; prose dropped), the raw
section text of the probed items, and the edgartools section shape
(``section_item_attr`` — whether ``Section.item`` was populated). Tests
run the full ``parse_filing`` path over fakes at the fetch seams — no
EDGAR.

Known results under test (DEV-133 + DEV-136 acceptance criteria; probe
evidence is recorded in the DEV-127 parent spec):

- CAT 7 / 1A: flagship true preludes (~2.5k chars) attached whole
- WMT 1A: markdown_h4 path, true prelude ~800 chars
- JPM 1A: pseudo-prelude (~6.4k) reclassified as heading-less leading block
- WMT 1 / CAT 1: markdown_h4 multi-block, heading-line-only prelude
  (no framing prose)
- DIS 7: false-valid prelude — recorded KNOWN LIMITATION, not fixed
- MSFT 1 / 1A / 7 / 7A: text fallback carries the whole filing
  (markdown renders no usable headings); GE 1A stays flat;
  WMT 7A / DIS 7A: markdown demoted by plausibility, fallback takes over
"""

import json
import re
from pathlib import Path

import pytest

from backend.common.sec_core import FetchedFiling
from backend.ingestion.sec_text_pipeline import parser
from backend.ingestion.sec_text_pipeline.filing_models import (
    FlatItem,
    ParsedFiling,
    StructuredItem,
)
from backend.tests.ingestion.sec_text_pipeline.conftest import (
    FakeTenK,
    assert_tiles,
)

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
        # Mirror the recorded edgartools section shape: "missing" replays
        # the spaced-name shape (Section.item unset — live MSFT/GE/DIS
        # reality) so these probes exercise the parser's name-derivation
        # path with real filings, not just the synthetic unit tests.
        section_item_attr = data["section_item_attr"]
        assert section_item_attr in ("missing", "populated"), (
            f"{ticker}: section_item_attr must be 'missing' or 'populated', "
            f"got {section_item_attr!r}"
        )
        degraded = section_item_attr == "missing"
        tenk = FakeTenK(
            sections_data={
                (f"Item {key.upper()}" if degraded else f"item_{key}"): {
                    "item": "" if degraded else key,
                    "text": text,
                }
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
        # Fiscal year follows the recorded filing (WMT's fiscal year ends in
        # late January, so its FY label is the period_of_report's year).
        fiscal_year = int(data["period_of_report"][:4])
        return parser.parse_filing(ticker, fiscal_year=fiscal_year, store=store)

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
        # The leading block + named blocks must tile the entire trimmed Item
        # body in order (prelude is empty here, so blocks carry it all) — an
        # ordered-tiling check, so a dropped block cannot hide behind
        # repeated text elsewhere in the filing.
        risk = get_structured(parse_probe("JPM"), "1a")
        raw = PROBES["JPM"]["sections"]["1a"]
        trimmed = parser._trim_section_text(raw, "1a")
        assert_tiles(risk.prelude, risk.blocks, trimmed)


class TestNoPreludeMultiBlock:
    """The heading-line-only prelude cases: no framing prose before the
    first block.

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


class TestTextFallbackPath:
    """DEV-136 acceptance: the Title-Case text fallback on recorded filings.

    MSFT is the load-bearing case — its filing markdown renders no usable
    H3/H4 headings at all, so every structured item below exists only
    because of the fallback. Recorded at the 2026-08-11 vintage (MSFT
    FY2026, GE FY2025, plus 7A sections added to the existing WMT/DIS
    recordings — same accessions as the 2026-08-05 probe vintage).
    """

    def test_msft_items_structure_via_fallback(self, parse_probe):
        # Block counts reproduce the 72-probe evidence (27/14/41/5) minus
        # the three Item 7 "(1)ppt" table-footnote anchors removed by the
        # M-1.1 footnote-label rejection rule (41 -> 38; their text merges
        # into the preceding blocks).
        filing = parse_probe("MSFT")
        expected_blocks = {"1": 27, "1a": 14, "7": 38, "7a": 5}
        for key, n_blocks in expected_blocks.items():
            item = get_structured(filing, key)
            assert item.detection_source == "text_fallback", key
            assert len(item.blocks) == n_blocks, key
            # No footnote-label line ("(1)ppt" shape) may anchor a block.
            for block in item.blocks:
                assert not re.match(r"^\(\d+\)", block.heading), (
                    f"item {key}: footnote label promoted to heading: {block.heading!r}"
                )

    def test_msft_1a_zero_content_loss_via_fallback(self, parse_probe):
        # The fallback path honors the same tiling invariant as the
        # markdown paths: prelude + blocks reassemble the trimmed body.
        risk = get_structured(parse_probe("MSFT"), "1a")
        raw = PROBES["MSFT"]["sections"]["1a"]
        trimmed = parser._trim_section_text(raw, "1a")
        assert_tiles(risk.prelude, risk.blocks, trimmed)

    def test_ge_1a_unstructured_stays_flat(self, parse_probe):
        # 61k chars of continuous risk-factor prose with no heading-shaped
        # standalone lines: the fallback must not invent structure.
        filing = parse_probe("GE")
        risk = next(i for i in filing.items if i.item == "1a")
        assert isinstance(risk, FlatItem)
        assert len(risk.text) > 50_000

    def test_wmt_7a_demoted_markdown_hands_over_to_fallback(self, parse_probe):
        # Full-chain demotion case: the same candidate set structures
        # WMT 1/1A via markdown_h4 (pinned above), but 7A anchors only a
        # single H4 heading — below the plausibility minimum — so the
        # chain falls through to the fallback instead of giving up.
        filing = parse_probe("WMT")
        market_risk = get_structured(filing, "7a")
        assert market_risk.detection_source == "text_fallback"
        assert len(market_risk.blocks) == 5

    def test_dis_7a_demoted_markdown_hands_over_to_fallback(self, parse_probe):
        # Sibling demotion case: DIS 7A's markdown anchors are one H3 plus
        # one H4 at 63% depth — each level implausible on its own — and
        # the fallback takes over.
        filing = parse_probe("DIS")
        market_risk = get_structured(filing, "7a")
        assert market_risk.detection_source == "text_fallback"
        assert len(market_risk.blocks) == 2


class TestKnownLimitations:
    def test_dis_7_false_valid_prelude_current_behavior(self, parse_probe):
        """KNOWN LIMITATION (spec Known Limitations #1) — deliberately NOT fixed.

        DIS Item 7 hides ~2.6k chars of disguised body content (summary
        tables) under the validity threshold, so it is classified as a
        "valid" prelude when it is really tabular data, not framing prose.
        Since DEV-135, a valid prelude also enters the chunk flow as its own
        searchable leading chunk, so this is no longer a content-loss bug —
        the text is indexed and findable either way. The residual harm is a
        metadata mislabel: on this item's block chunks, the `prelude`
        payload field carries a summary table under a field named for
        framing text. Size cannot discriminate here (true preludes reach
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

    def test_msft_1_officer_table_cell_heading_current_behavior(self, parse_probe):
        """KNOWN LIMITATION (DEV-136 review round 1) — deliberately NOT fixed.

        MSFT Item 1 promotes "Vice Chair and President" — an officer-table
        cell, not a section heading — to a block heading: the officer table
        sits between the real heading and the following prose, so the cell
        line inherits a heading-shaped context (standalone line, prose
        follows) that every current rejection rule accepts. The user
        deliberately declined rule changes for it: no safe structural rule
        distinguishes this cell from a real heading, and any casing or
        word-shape heuristic would risk rejecting real headings.
        Arbitration is deferred to A/B failure mining (same precedent as
        DEV-133 DIS-7 above). This test records the current behavior; if it
        ever fails, detection behavior changed — re-read the review record
        before "fixing" it.
        """
        business = get_structured(parse_probe("MSFT"), "1")
        assert "Vice Chair and President" in [b.heading for b in business.blocks]
