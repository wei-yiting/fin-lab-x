"""Throwaway BDD verification script — Round 1.

Executes S-fallback-01..10 and J-fallback-01/02 from
artifacts/current/executable-verification.md against the real
block_detection.py / parser.py code. Not part of the permanent suite.

Run with:  PYTHONPATH=. pytest artifacts/current/temp/test_verification_round1.py -v
(PYTHONPATH=. is required because this file lives outside backend/ and has
no __init__.py chain back to the repo root for pytest's import rootdir
resolution — backend/tests/ itself does not need this.)
"""

import re

import pytest

from backend.common.sec_core import FetchedFiling
from backend.ingestion.sec_text_pipeline import parser
from backend.ingestion.sec_text_pipeline.block_detection import (
    HeadingCandidates,
    detect_blocks,
)
from backend.ingestion.sec_text_pipeline.filing_models import Block, FlatItem
from backend.ingestion.sec_text_pipeline.filing_store import LocalFilingStore
from backend.tests.ingestion.sec_text_pipeline.conftest import FakeTenK, assert_tiles
from backend.tests.ingestion.sec_text_pipeline.test_detection_probes import (
    PROBES,
    get_structured,
)

NO_CANDIDATES = HeadingCandidates(h3=(), h4=())

FILLER = "Sufficiently long body prose line for the block. " * 4
LONG_BODY = FILLER * 50


def _fb_text(*parts: str) -> str:
    """Blank-line-separated Item text, matching test_block_detection.py's
    _fb_text helper (real 10-K plain-text rendering shape)."""
    return "\n\n".join(parts)


def _exact_len(base: str, n: int) -> str:
    """A string of exactly n stripped chars built from `base`, safe under
    every fallback content rule except length: letters/spaces only (no
    digits/punctuation introduced), never starts/ends on whitespace."""
    s = (base * (n // len(base) + 2))[:n]
    if s[-1].isspace():
        s = s[:-1] + "x"
    if s[0].isspace():
        s = "x" + s[1:]
    return s


@pytest.fixture
def parse_probe(monkeypatch, tmp_path):
    """Self-contained copy of test_detection_probes.py's parse_probe fixture
    (that file's version depends on conftest.py's `store` fixture, which
    isn't auto-discovered for a test file outside backend/tests/), so this
    inlines the same LocalFilingStore(tmp_path) construction directly."""
    store = LocalFilingStore(base_dir=str(tmp_path))

    def _parse(ticker: str):
        data = PROBES[ticker]
        section_item_attr = data["section_item_attr"]
        assert section_item_attr in ("missing", "populated")
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
        fiscal_year = int(data["period_of_report"][:4])
        return parser.parse_filing(ticker, fiscal_year=fiscal_year, store=store)

    return _parse


# ---------------------------------------------------------------------------
# S-fallback-01: candidate must pass all 7 rejection rules, precise boundaries
# ---------------------------------------------------------------------------

CONTENT_ROWS = [
    pytest.param("Sales", True, id="len_5_lower_bound"),
    pytest.param("Debt", False, id="len_4_below_min"),
    pytest.param(
        _exact_len("Alpha Regional Segment Detail ", 120), True, id="len_120_upper_bound"
    ),
    pytest.param(
        _exact_len("Alpha Regional Segment Detail ", 121), False, id="len_121_above_max"
    ),
    pytest.param(
        "Fiscal Year 2026 Highlights", False, id="digit_cluster_fiscal_year"
    ),
    pytest.param("Item 1A", False, id="item_self_reference"),
    pytest.param("(1)ppt", False, id="footnote_label"),
    pytest.param("Revenue Growth %", False, id="special_char_percent"),
    pytest.param("Key Risks:", False, id="trailing_colon"),
]


@pytest.mark.parametrize("candidate,expect_pass", CONTENT_ROWS)
def test_s_fallback_01_content_rules(candidate, expect_pass):
    text = _fb_text(
        "Item 1. Business",
        "Overview",
        FILLER,
        candidate,
        FILLER,
        "Competition",
        FILLER,
    )
    d = detect_blocks(text, NO_CANDIDATES)
    assert d is not None, "plausibility should hold via Overview/Competition"
    headings = [b.heading for b in d.blocks]
    if expect_pass:
        assert candidate in headings, (
            f"expected PASS: {candidate!r} should be a block heading, got {headings}"
        )
    else:
        assert candidate not in headings, (
            f"expected REJECT: {candidate!r} should NOT be a block heading, "
            f"got {headings}"
        )


CONTEXT_CANDIDATE = "Regional Segment"


def test_s_fallback_01_prev_line_sentence_end_rejected():
    # Row: previous physical line ends with a period (no blank line between);
    # next line is a 95-char paragraph (long enough on its own).
    text = "\n".join(
        [
            "Item 1. Business",
            "",
            "Overview",
            "",
            FILLER,
            "",
            FILLER,  # ends with '.', glued directly above the candidate
            CONTEXT_CANDIDATE,
            "Y" * 95,
            "",
            "Competition",
            "",
            FILLER,
        ]
    )
    d = detect_blocks(text, NO_CANDIDATES)
    assert d is not None
    assert CONTEXT_CANDIDATE not in [b.heading for b in d.blocks]


def test_s_fallback_01_next_line_exactly_80_rejected():
    text = "\n".join(
        [
            "Item 1. Business",
            "",
            "Overview",
            "",
            FILLER,
            "",
            "Segment notes continue without a terminal stop mark",
            CONTEXT_CANDIDATE,
            "Y" * 80,
            "",
            "Competition",
            "",
            FILLER,
        ]
    )
    d = detect_blocks(text, NO_CANDIDATES)
    assert d is not None
    assert CONTEXT_CANDIDATE not in [b.heading for b in d.blocks]


def test_s_fallback_01_next_line_exactly_81_passes():
    text = "\n".join(
        [
            "Item 1. Business",
            "",
            "Overview",
            "",
            FILLER,
            "",
            "Segment notes continue without a terminal stop mark",
            CONTEXT_CANDIDATE,
            "Y" * 81,
            "",
            "Competition",
            "",
            FILLER,
        ]
    )
    d = detect_blocks(text, NO_CANDIDATES)
    assert d is not None
    assert CONTEXT_CANDIDATE in [b.heading for b in d.blocks]


# ---------------------------------------------------------------------------
# S-fallback-02: context judgement around blank/short neighboring lines
# ---------------------------------------------------------------------------


def test_s_fallback_02_blank_line_before_candidate_passes():
    text = "\n".join(
        [
            "Item 1. Business",
            "",
            "Overview",
            "",
            FILLER,
            "",
            FILLER,  # ends with '.'
            "",  # blank line directly before candidate
            "Regional Segment",
            "",
            FILLER,
            "",
            "Competition",
            "",
            FILLER,
        ]
    )
    d = detect_blocks(text, NO_CANDIDATES)
    assert d is not None
    assert "Regional Segment" in [b.heading for b in d.blocks]


def test_s_fallback_02_no_blank_line_before_candidate_rejected():
    text = "\n".join(
        [
            "Item 1. Business",
            "",
            "Overview",
            "",
            FILLER,
            "",
            "This sentence ends with a period directly above the candidate.",
            "Regional Segment",
            "",
            FILLER,
            "",
            "Competition",
            "",
            FILLER,
        ]
    )
    d = detect_blocks(text, NO_CANDIDATES)
    assert d is not None
    assert "Regional Segment" not in [b.heading for b in d.blocks]


def test_s_fallback_02_blank_line_after_then_long_prose_passes():
    text = "\n".join(
        [
            "Item 1. Business",
            "",
            "Overview",
            "",
            FILLER,
            "",
            "",
            "Regional Segment",
            "",  # blank line directly after candidate
            "Y" * 96,
            "",
            "Competition",
            "",
            FILLER,
        ]
    )
    d = detect_blocks(text, NO_CANDIDATES)
    assert d is not None
    assert "Regional Segment" in [b.heading for b in d.blocks]


def test_s_fallback_02_short_dollar_annotation_next_rejected():
    short_annotation = "Cash of $10 million this quarter here"
    short_annotation = (short_annotation + "z" * 50)[:42]
    assert len(short_annotation) == 42
    assert "$" in short_annotation
    text = "\n".join(
        [
            "Item 1. Business",
            "",
            "Overview",
            "",
            FILLER,
            "",
            "",
            "Regional Segment",
            short_annotation,  # immediately next line, no blank
            "",
            FILLER,  # a long paragraph further down must NOT rescue it
            "",
            "Competition",
            "",
            FILLER,
        ]
    )
    d = detect_blocks(text, NO_CANDIDATES)
    assert d is not None
    assert "Regional Segment" not in [b.heading for b in d.blocks]


# ---------------------------------------------------------------------------
# S-fallback-03: Item self-reference format tolerance
# ---------------------------------------------------------------------------


def test_s_fallback_03_row1_allcaps_emdash_self_reference_rejected():
    candidate = "ITEM 1A—RISK FACTORS"
    text = _fb_text(
        "Item 1. Business", "Overview", FILLER, candidate, FILLER, "Competition", FILLER
    )
    d = detect_blocks(text, NO_CANDIDATES)
    assert d is not None
    assert candidate not in [b.heading for b in d.blocks]


def test_s_fallback_03_row2_item_prefixed_independent_heading_should_pass():
    candidate = "Item 1A Compliance Program"
    text = _fb_text(
        "Item 1. Business", "Overview", FILLER, candidate, FILLER, "Competition", FILLER
    )
    d = detect_blocks(text, NO_CANDIDATES)
    assert d is not None
    headings = [b.heading for b in d.blocks]
    # Plan expects this to PASS (not a self-reference, just a heading that
    # happens to start with "Item 1A"). Report actual behavior as-is.
    assert candidate in headings, (
        f"plan expects PASS but code REJECTED {candidate!r}; headings={headings}. "
        f"_FALLBACK_ITEM_SELF_RE = r'^item\\s+\\d+[a-c]?\\.?' is unanchored at the "
        f"end, so re.match() accepts any line whose PREFIX looks like "
        f"'Item <n><letter>' regardless of trailing text."
    )


def test_s_fallback_03_row3_duplicate_self_reference_both_rejected():
    text = _fb_text(
        "Item 1. Business",
        "Item 1A",
        FILLER,
        "Overview",
        FILLER,
        "Item 1A",
        FILLER,
        "Competition",
        FILLER,
    )
    d = detect_blocks(text, NO_CANDIDATES)
    assert d is not None
    headings = [b.heading for b in d.blocks]
    assert headings.count("Item 1A") == 0
    all_text = d.prelude + "".join(f"\n{b.heading}\n{b.text}" for b in d.blocks)
    assert all_text.count("Item 1A") == 2, "both literal occurrences must survive"


# ---------------------------------------------------------------------------
# S-fallback-04: flattened-table numeric residue must not be misread as heading
# ---------------------------------------------------------------------------


def test_s_fallback_04_row1_comma_thousands_rejected():
    candidate = "Approximately 1,000 Employees Worldwide"
    text = _fb_text(
        "Item 1. Business", "Overview", FILLER, candidate, FILLER, "Competition", FILLER
    )
    d = detect_blocks(text, NO_CANDIDATES)
    assert d is not None
    assert candidate not in [b.heading for b in d.blocks]


def test_s_fallback_04_row2_space_separated_short_digit_groups_should_be_rejected():
    candidate = "12  34  56  78"
    text = _fb_text(
        "Item 1. Business", "Overview", FILLER, candidate, FILLER, "Competition", FILLER
    )
    d = detect_blocks(text, NO_CANDIDATES)
    assert d is not None
    headings = [b.heading for b in d.blocks]
    assert candidate not in headings, (
        f"plan expects REJECT but code ACCEPTED {candidate!r}; headings={headings}. "
        f"None of the 7 rules catch space-separated short digit groups: "
        f"'12  34  56  78'.isdigit() is False (spaces present), and "
        f"_FALLBACK_DIGIT_CLUSTER_RE (\\d{{3,}}) finds no run of 3+ consecutive "
        f"digits since each group is only 2 digits wide."
    )


# ---------------------------------------------------------------------------
# S-fallback-05: rejected candidates still survive verbatim in the output
# ---------------------------------------------------------------------------


def test_s_fallback_05_rejected_candidates_retain_text_verbatim():
    self_ref = "Item 7A. Market Risk"
    pipe_line = "Revenue | $1,234 | $1,100"
    too_short = "Tax"
    text = _fb_text(
        self_ref,
        "Overview",
        FILLER,
        pipe_line,
        FILLER,
        "Competition",
        FILLER,
        too_short,
        FILLER,
    )
    d = detect_blocks(text, NO_CANDIDATES)
    assert d is not None
    assert_tiles(d.prelude, d.blocks, text)
    all_text = d.prelude + "".join(f"\n{b.heading}\n{b.text}" for b in d.blocks)
    for rejected in (self_ref, pipe_line, too_short):
        assert rejected in all_text, f"{rejected!r} missing from reconstructed output"
    assert "|" in all_text


# ---------------------------------------------------------------------------
# S-fallback-06: plausibility is an AND of two independent sub-conditions
# ---------------------------------------------------------------------------


def test_s_fallback_06_case1_position_fails_despite_count_passing():
    tail_text = _fb_text(
        "Segment Alpha", FILLER, "Segment Beta", FILLER, "Segment Gamma", FILLER
    )
    target_prefix_len = int(0.45 / 0.55 * len(tail_text))
    prefix = _exact_len(
        "Filler prose with no heading shaped lines whatsoever here ",
        target_prefix_len,
    )
    text = prefix + "\n\n" + tail_text
    ratio = target_prefix_len / len(text)
    assert ratio > 0.30, f"sanity check: prefix ratio {ratio:.3f} must exceed 0.30"
    d = detect_blocks(text, NO_CANDIDATES)
    assert d is None, f"expected None (position fails); got {d!r}, ratio={ratio:.3f}"


def test_s_fallback_06_case2_wmt_7a_real_filing(parse_probe):
    market_risk = get_structured(parse_probe("WMT"), "7a")
    assert market_risk.detection_source == "text_fallback"
    assert len(market_risk.blocks) == 5


# ---------------------------------------------------------------------------
# S-fallback-07: anchor count and prelude length precise boundaries
# ---------------------------------------------------------------------------


def test_s_fallback_07_step1_exactly_two_early_candidates_is_plausible():
    text = _fb_text("Alpha Heading", FILLER, "Beta Heading", FILLER)
    d = detect_blocks(text, NO_CANDIDATES)
    assert d is not None


PRELUDE_BASE = "Prelude filler text with no headings whatsoever here "


def test_s_fallback_07_step2_prelude_exactly_3000_chars_attached_whole():
    prelude = _exact_len(PRELUDE_BASE, 3000)
    text = prelude + "\n" + "\n\n".join(["HeadingOne", LONG_BODY, "HeadingTwo", LONG_BODY])
    d = detect_blocks(text, NO_CANDIDATES)
    assert d is not None
    assert len(d.prelude) == 3000
    assert d.prelude == prelude
    assert [b.heading for b in d.blocks] == ["HeadingOne", "HeadingTwo"]


def test_s_fallback_07_step2_prelude_exactly_3001_chars_reclassified():
    prelude = _exact_len(PRELUDE_BASE, 3001)
    text = prelude + "\n" + "\n\n".join(["HeadingOne", LONG_BODY, "HeadingTwo", LONG_BODY])
    d = detect_blocks(text, NO_CANDIDATES)
    assert d is not None
    assert d.prelude == ""
    assert d.blocks[0].heading == ""
    assert d.blocks[0].text == prelude


def test_s_fallback_07_step3_dis_7_prelude_length_reference(parse_probe):
    """Reference case; same fact already covered by
    test_detection_probes.py::TestKnownLimitations::test_dis_7_false_valid_prelude_current_behavior
    (confirmed PASSING in baseline run)."""
    md_and_a = get_structured(parse_probe("DIS"), "7")
    assert 2500 <= len(md_and_a.prelude) <= 3000


# ---------------------------------------------------------------------------
# S-fallback-08: detection chain tries in order, stops at first trusted path
# ---------------------------------------------------------------------------


def test_s_fallback_08_detection_chain_stops_at_first_trusted_path(parse_probe):
    cat = parse_probe("CAT")
    cat7 = get_structured(cat, "7")
    assert cat7.detection_source == "markdown_h3"
    assert [b.heading for b in cat7.blocks[:2]] == [
        "OVERVIEW",
        "CONSOLIDATED SALES AND REVENUES",
    ]

    wmt = parse_probe("WMT")
    wmt1a = get_structured(wmt, "1a")
    assert wmt1a.detection_source == "markdown_h4"
    assert [b.heading for b in wmt1a.blocks] == ["Strategic Risks", "Operational Risks"]

    wmt7a = get_structured(wmt, "7a")
    assert wmt7a.detection_source == "text_fallback"
    assert len(wmt7a.blocks) == 5

    dis = parse_probe("DIS")
    dis7a = get_structured(dis, "7a")
    assert dis7a.detection_source == "text_fallback"
    assert len(dis7a.blocks) == 2

    msft = parse_probe("MSFT")
    expected_blocks = {"1": 27, "1a": 14, "7": 38, "7a": 5}
    for key, n in expected_blocks.items():
        item = get_structured(msft, key)
        assert item.detection_source == "text_fallback", key
        assert len(item.blocks) == n, key


# ---------------------------------------------------------------------------
# S-fallback-09: StructuredItem prelude+blocks tile the original Item text
# ---------------------------------------------------------------------------


def test_s_fallback_09_msft_1a_prelude_blocks_tile_original(parse_probe):
    msft = parse_probe("MSFT")
    risk = get_structured(msft, "1a")
    trimmed = parser._trim_section_text(PROBES["MSFT"]["sections"]["1a"], "1a")
    assert_tiles(risk.prelude, risk.blocks, trimmed)


def test_s_fallback_09_dis_7_prelude_blocks_tile_original(parse_probe):
    dis = parse_probe("DIS")
    item7 = get_structured(dis, "7")
    trimmed = parser._trim_section_text(PROBES["DIS"]["sections"]["7"], "7")
    assert_tiles(item7.prelude, item7.blocks, trimmed)


# ---------------------------------------------------------------------------
# S-fallback-10: FlatItem content faithfully reconstructs the original Item
# ---------------------------------------------------------------------------


def test_s_fallback_10_ge_1a_flatitem_content_matches_trimmed_original(parse_probe):
    ge = parse_probe("GE")
    flat = next(i for i in ge.items if i.item == "1a")
    assert isinstance(flat, FlatItem)
    raw = PROBES["GE"]["sections"]["1a"]
    trimmed = parser._trim_section_text(raw, "1a")
    assert len(trimmed) == 61747
    assert flat.text.strip() == trimmed.strip()
    assert_tiles("", [Block(heading="", text=flat.text)], trimmed)


# ---------------------------------------------------------------------------
# J-fallback-01: two markdown paths demote, fallback runs the full chain
# ---------------------------------------------------------------------------


def test_j_fallback_01_wmt_7a_full_chain_produces_structured_item(parse_probe):
    wmt = parse_probe("WMT")
    market_risk = get_structured(wmt, "7a")
    assert market_risk.detection_source == "text_fallback"
    trimmed = parser._trim_section_text(PROBES["WMT"]["sections"]["7a"], "7a")
    assert_tiles(market_risk.prelude, market_risk.blocks, trimmed)


# ---------------------------------------------------------------------------
# J-fallback-02: all three paths untrusted, Item degrades gracefully to FlatItem
# ---------------------------------------------------------------------------


def test_j_fallback_02_ge_no_exception_graceful_flatitem_degradation(parse_probe):
    try:
        ge = parse_probe("GE")
    except Exception as e:  # noqa: BLE001 - verification script, want to catch all
        pytest.fail(f"parse_probe('GE') raised {type(e).__name__}: {e}")

    item = next((i for i in ge.items if i.item == "1a"), None)
    assert item is not None, "item '1a' missing from GE filing.items"
    assert isinstance(item, FlatItem)

    raw = PROBES["GE"]["sections"]["1a"]
    trimmed = parser._trim_section_text(raw, "1a")
    assert item.text.strip() == trimmed.strip()
    assert_tiles("", [Block(heading="", text=item.text)], trimmed)
