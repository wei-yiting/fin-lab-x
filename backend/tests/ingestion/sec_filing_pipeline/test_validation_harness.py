"""Unit tests for the validation harness pure helpers.

Network-bound code (fetcher) and the CLI orchestrator have integration
tests via Phase 0c smoke run; here we only cover deterministic logic so
the harness can be trusted before the BDD sandbox runs.
"""

from __future__ import annotations

from backend.tests.ingestion.sec_filing_pipeline.validation import (
    extractor,
    tickers,
)
from backend.tests.ingestion.sec_filing_pipeline.validation.extractor import (
    Heading,
    detect_vendor,
    extract_headings,
    headings_at_level,
    headings_in_region,
    is_item_heading,
    is_part_heading,
    item_number,
    items_in_monotonic_order,
    longest_common_subsequence,
)


# ───── tickers ────────────────────────────────────────────────────────────


class TestTickerSets:
    def test_existing_23_count(self):
        assert len(tickers.EXISTING_23) == 23

    def test_discovery_5_picks(self):
        assert tickers.DISCOVERY_5 == ("PG", "USB", "ALL", "BRK.A", "SLB")

    def test_all_28_is_union(self):
        assert len(tickers.ALL_28) == 28
        assert set(tickers.ALL_28) == set(tickers.EXISTING_23) | set(
            tickers.DISCOVERY_5
        )

    def test_resolve_ticker_set_names(self):
        assert tickers.resolve_ticker_set("existing23") == tickers.EXISTING_23
        assert tickers.resolve_ticker_set("discovery5") == tickers.DISCOVERY_5
        assert tickers.resolve_ticker_set("all28") == tickers.ALL_28
        assert tickers.resolve_ticker_set("class_a") == tickers.CLASS_A_12

    def test_resolve_ticker_set_literal_list(self):
        assert tickers.resolve_ticker_set("NVDA,AAPL,MSFT") == (
            "NVDA",
            "AAPL",
            "MSFT",
        )

    def test_resolve_ticker_set_single(self):
        assert tickers.resolve_ticker_set("NVDA") == ("NVDA",)


# ───── extract_headings ───────────────────────────────────────────────────


class TestExtractHeadings:
    def test_extract_headings_simple(self):
        html = "<h1>PART I</h1><h2>Item 1.</h2><h3>Subsection</h3>"
        result = extract_headings(html)
        assert [(h.level, h.text) for h in result] == [
            (1, "PART I"),
            (2, "Item 1."),
            (3, "Subsection"),
        ]

    def test_extract_headings_parent_path(self):
        html = (
            "<h1>PART I</h1>"
            "<h2>Item 1. Business</h2>"
            "<h3>Critical Estimates</h3>"
            "<h4>Income Taxes</h4>"
        )
        result = extract_headings(html)
        assert result[3].text == "Income Taxes"
        assert result[3].parent_path == ("PART I", "Item 1. Business", "Critical Estimates")

    def test_extract_headings_resets_deeper_levels(self):
        html = (
            "<h2>Item 1.</h2>"
            "<h3>Sub A</h3>"
            "<h4>Detail A</h4>"
            "<h2>Item 2.</h2>"  # h3/h4 chain reset
            "<h3>Sub B</h3>"
        )
        result = extract_headings(html)
        # Last h3 belongs to Item 2., not Item 1.
        last_h3 = next(h for h in result if h.text == "Sub B")
        assert "Item 2." in last_h3.parent_path
        assert "Item 1." not in last_h3.parent_path

    def test_extract_headings_in_region_filters_by_h2(self):
        html = (
            "<h1>PART I</h1>"
            "<h2>Item 1.</h2>"
            "<h3>A1</h3>"
            "<h2>Item 2.</h2>"
            "<h3>A2</h3>"
            "<h4>B2</h4>"
        )
        result = extract_headings(html)
        in_item2 = headings_in_region(result, "Item 2.")
        assert [h.text for h in in_item2] == ["A2", "B2"]

    def test_extract_headings_collapses_inner_whitespace(self):
        html = "<h2>  Item   7. \n MD&A  </h2>"
        result = extract_headings(html)
        assert result[0].text == "Item 7. MD&A"


# ───── PART / Item parsing ────────────────────────────────────────────────


class TestPartItemParsing:
    def test_is_part_heading(self):
        assert is_part_heading("PART I")
        assert is_part_heading("PART IV")
        assert is_part_heading("part ii")  # case-insensitive
        assert not is_part_heading("Particular")
        assert not is_part_heading("Item 1.")

    def test_is_item_heading(self):
        assert is_item_heading("Item 1. Business")
        assert is_item_heading("Item 1A. Risk Factors")
        assert is_item_heading("Item 7. MD&A")
        assert not is_item_heading("PART I")
        assert not is_item_heading("Items of business")

    def test_item_number_parses(self):
        assert item_number("Item 1. Business") == (1, "")
        assert item_number("Item 1A. Risk Factors") == (1, "A")
        assert item_number("Item 7A. Quant Disclosures") == (7, "A")

    def test_item_number_returns_none(self):
        assert item_number("PART I") is None
        assert item_number("Hello World") is None

    def test_items_in_monotonic_order_pass(self):
        assert items_in_monotonic_order(
            [
                "Item 1. Business",
                "Item 1A. Risk Factors",
                "Item 1B. Unresolved",
                "Item 2. Properties",
                "Item 7. MD&A",
                "Item 7A. Quant",
            ]
        )

    def test_items_in_monotonic_order_fail(self):
        # Item 1A before Item 1 — out of order.
        assert not items_in_monotonic_order(
            [
                "Item 1A. Risk Factors",
                "Item 1. Business",
            ]
        )


# ───── LCS ────────────────────────────────────────────────────────────────


class TestLCS:
    def test_lcs_identical(self):
        seq = ["a", "b", "c"]
        assert longest_common_subsequence(seq, seq) == seq

    def test_lcs_baseline_strict_subset(self):
        # baseline = a,b,c — new has extras but preserves order
        assert longest_common_subsequence(
            ["x", "a", "y", "b", "z", "c"],
            ["a", "b", "c"],
        ) == ["a", "b", "c"]

    def test_lcs_baseline_reordered(self):
        # baseline = a,b,c but new = a,c,b — LCS is a,b OR a,c (length 2)
        result = longest_common_subsequence(["a", "c", "b"], ["a", "b", "c"])
        assert len(result) == 2
        # Importantly: result != baseline, so caller knows order is broken
        assert result != ["a", "b", "c"]

    def test_lcs_baseline_missing_element(self):
        # baseline = a,b,c but new = a,c (missing b)
        assert longest_common_subsequence(["a", "c"], ["a", "b", "c"]) == [
            "a",
            "c",
        ]

    def test_lcs_empty_inputs(self):
        assert longest_common_subsequence([], ["a"]) == []
        assert longest_common_subsequence(["a"], []) == []


# ───── vendor heuristic ───────────────────────────────────────────────────


class TestDetectVendor:
    def test_workiva_meta_generator(self):
        html = '<meta name="generator" content="Workiva Wdesk Document">'
        assert detect_vendor(html) == "workiva"

    def test_workiva_fingerprint_fallback(self):
        html = "<html><body><!-- Wdesk export --></body></html>"
        assert detect_vendor(html) == "workiva"

    def test_donnelley_meta_generator(self):
        html = '<meta name="generator" content="RR Donnelley">'
        assert detect_vendor(html) == "donnelley"

    def test_unknown_vendor(self):
        html = "<html><head></head><body>10-K filing</body></html>"
        assert detect_vendor(html) == "unknown"


# ───── Heading dataclass behavior ─────────────────────────────────────────


class TestHeadingDataclass:
    def test_heading_is_frozen_hashable(self):
        h = Heading(level=2, text="Item 1.", parent_path=("PART I",))
        # Should be hashable (frozen dataclass)
        assert hash(h) is not None

    def test_headings_at_level_helper(self):
        html = "<h1>A</h1><h2>B</h2><h2>C</h2><h3>D</h3>"
        result = extract_headings(html)
        assert headings_at_level(result, 2) == ["B", "C"]
