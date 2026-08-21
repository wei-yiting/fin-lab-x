"""Tests for the section-detection sweep's pure classification/aggregation logic.

``sweep_ticker`` (the network-touching fetch/parse orchestration) is
deliberately untested here — it only wires together two already-tested
production seams (``fetch_filing_bundle``, ``parse_filing``), and this repo's
precedent for one-shot ticker-sweep scripts
(``backend/evals/scenarios/sec_retrieval_ab/curation/ingest_tickers.py`` on
branch ``feat/sec-retrieval-eval-dataset``, ``backend/scripts/embed_sec_filings.py``)
leaves that orchestration untested too: correctness is proven by running it
against real tickers, not by mocking edgartools.
"""

from collections import Counter

from backend.scripts.sweep_section_detection import (
    SectionObservation,
    TickerSweepResult,
    classify_ticker,
    degraded_tickers,
    method_distribution,
    section_method_distribution,
    split_methods,
    standard_tickers,
    ticker_methods,
    undetermined_tickers,
)


def _section(method: str, item: str = "7") -> SectionObservation:
    return SectionObservation(
        name=f"item_{item}",
        item=item,
        part=None,
        detection_method=method,
        confidence=0.9,
    )


def _result(
    ticker: str,
    methods: list[str],
    *,
    fetch_error: str | None = None,
) -> TickerSweepResult:
    sections = tuple(_section(m, item=str(i)) for i, m in enumerate(methods))
    return TickerSweepResult(
        ticker=ticker,
        fiscal_year=2025,
        accession_number="0000000000-25-000001",
        sections=sections,
        fetch_error=fetch_error,
    )


class TestSplitMethods:
    def test_single_value(self):
        assert split_methods("toc") == frozenset({"toc"})

    def test_comma_joined_merge_value(self):
        # edgartools' hybrid detector dedup merge produces exactly this shape:
        # ','.join(sorted(methods)) — see hybrid_section_detector.py's
        # _deduplicate(). Not a hypothetical edge case.
        assert split_methods("heading,pattern") == frozenset({"heading", "pattern"})

    def test_whitespace_around_commas_tolerated(self):
        assert split_methods("heading, pattern") == frozenset({"heading", "pattern"})


class TestTickerMethods:
    def test_no_sections_yields_empty_set(self):
        assert ticker_methods(_result("EMPTY", [])) == frozenset()

    def test_union_across_sections_deduplicates(self):
        result = _result("MIX", ["toc", "toc", "heading"])
        assert ticker_methods(result) == frozenset({"toc", "heading"})

    def test_comma_joined_section_contributes_both_tokens(self):
        result = _result("MERGE", ["toc", "heading,pattern"])
        assert ticker_methods(result) == frozenset({"toc", "heading", "pattern"})


class TestClassifyTicker:
    def test_fetch_error_is_undetermined(self):
        result = _result("BADTICKER", [], fetch_error="TickerNotFoundError: no 10-K")
        assert classify_ticker(result) == "undetermined"

    def test_zero_sections_is_undetermined(self):
        # Fetched fine but edgartools produced no sections at all (e.g.
        # .document was None) — no detection-method evidence either way.
        assert classify_ticker(_result("NODOC", [])) == "undetermined"

    def test_all_toc_is_standard(self):
        assert classify_ticker(_result("NVDA", ["toc", "toc", "toc"])) == "standard"

    def test_all_heading_is_standard(self):
        assert classify_ticker(_result("WMT", ["heading", "heading"])) == "standard"

    def test_mixed_toc_and_heading_is_standard(self):
        # Both are non-degraded methods — mixing them is still a clean filing.
        assert classify_ticker(_result("MIX", ["toc", "heading"])) == "standard"

    def test_any_pattern_section_is_degraded(self):
        assert (
            classify_ticker(_result("PATTERNED", ["toc", "toc", "pattern"]))
            == "degraded"
        )

    def test_any_html_fallback_section_is_degraded(self):
        assert (
            classify_ticker(_result("HTMLFB", ["toc", "html_fallback"])) == "degraded"
        )

    def test_any_unknown_section_is_degraded(self):
        assert classify_ticker(_result("UNK", ["toc", "unknown"])) == "degraded"

    def test_comma_joined_degraded_component_is_degraded(self):
        # A merged "heading,pattern" section still carries pattern's risk —
        # splitting must not let it hide behind the safe component.
        assert classify_ticker(_result("MERGE", ["heading,pattern"])) == "degraded"

    def test_single_degraded_section_among_many_standard_is_degraded(self):
        # DEV-172: filing-level classification is deliberately inclusive —
        # one pattern-detected section means content loss somewhere in the
        # filing even if every other section is clean.
        result = _result("MOSTLY_OK", ["toc"] * 10 + ["pattern"])
        assert classify_ticker(result) == "degraded"


class TestDistributions:
    def test_method_distribution_counts_tickers_not_sections(self):
        results = [
            _result("A", ["toc"]),
            _result("B", ["toc", "pattern"]),
            _result("C", ["heading"]),
        ]
        assert method_distribution(results) == Counter(
            {"toc": 2, "pattern": 1, "heading": 1}
        )

    def test_method_distribution_ignores_tickers_with_no_evidence(self):
        results = [_result("A", [], fetch_error="boom")]
        assert method_distribution(results) == Counter()

    def test_section_method_distribution_counts_raw_sections(self):
        results = [
            _result("A", ["toc", "toc"]),
            _result("B", ["toc", "pattern"]),
        ]
        assert section_method_distribution(results) == Counter({"toc": 3, "pattern": 1})

    def test_section_method_distribution_splits_comma_joined(self):
        results = [_result("A", ["heading,pattern"])]
        assert section_method_distribution(results) == Counter(
            {"heading": 1, "pattern": 1}
        )


class TestTickerLists:
    def test_partitions_by_classification(self):
        results = [
            _result("STD", ["toc"]),
            _result("DEG", ["pattern"]),
            _result("BAD", [], fetch_error="boom"),
        ]
        assert degraded_tickers(results) == ["DEG"]
        assert standard_tickers(results) == ["STD"]
        assert undetermined_tickers(results) == ["BAD"]

    def test_lists_are_sorted_alphabetically(self):
        results = [_result("ZEBRA", ["pattern"]), _result("ALPHA", ["pattern"])]
        assert degraded_tickers(results) == ["ALPHA", "ZEBRA"]
