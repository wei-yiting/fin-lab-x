"""Tests for the section-detection sweep's classification/aggregation logic,
plus a deliberately minimal set of ``sweep_ticker()`` orchestration tests.

Most of this file exercises the pure logic (``classify_ticker``,
``split_methods``, the distribution/report helpers) via the ``_result()``
fixture below. ``TestSweepTicker`` covers exactly three ``sweep_ticker()``
cases — happy path, one fetch-failure path, and the zero-sections
cross-check — by monkeypatching its imported seams (``fetch_filing_bundle``,
``parse_filing``, ``_resolve_latest_fiscal_year``). This is intentionally
not full branch/combination coverage: this repo's precedent for one-shot
ticker-sweep scripts
(``backend/scripts/embed_sec_filings.py``, which has no test file at all)
leaves this kind of orchestration lightly tested at most — deeper
correctness is proven by running it against real tickers, not by mocking
edgartools exhaustively.
"""

from collections import Counter
from types import SimpleNamespace
from unittest.mock import Mock

from backend.common.errors import TickerNotFoundError
from backend.scripts import sweep_section_detection as sweep_module
from backend.scripts.sweep_section_detection import (
    SWEEP_TICKERS,
    SectionObservation,
    TickerSweepResult,
    _parse_outcome_cell,
    classify_ticker,
    degraded_tickers,
    method_distribution,
    render_report,
    section_method_distribution,
    split_methods,
    sweep_ticker,
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
        # Filing-level classification is deliberately inclusive —
        # one pattern-detected section means content loss somewhere in the
        # filing even if every other section is clean.
        result = _result("MOSTLY_OK", ["toc"] * 10 + ["pattern"])
        assert classify_ticker(result) == "degraded"

    def test_unrecognized_method_value_is_degraded_not_standard(self):
        # Fails closed: a method string outside STANDARD_METHODS (e.g. a
        # strategy name a future edgartools version introduces) must never
        # be silently trusted just because it also isn't a known-degraded
        # value.
        result = _result("FUTURE_VERSION", ["some_new_strategy"])
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
    def test_excludes_standard_and_undetermined_tickers(self):
        results = [
            _result("STD", ["toc"]),
            _result("DEG", ["pattern"]),
            _result("BAD", [], fetch_error="boom"),
        ]
        assert degraded_tickers(results) == ["DEG"]
        assert undetermined_tickers(results) == ["BAD"]


class TestSweepTicker:
    """Deliberately minimal — exactly 3 cases, monkeypatching sweep_ticker()'s
    imported seams (fetch_filing_bundle, parse_filing,
    _resolve_latest_fiscal_year — patched on sweep_module, where sweep_ticker()
    actually looks them up, not at their original definition module). See the
    module docstring for why this stops short of full branch coverage."""

    def test_happy_path_records_sections_and_forces_cross_check(self, monkeypatch):
        monkeypatch.setattr(
            sweep_module, "_resolve_latest_fiscal_year", Mock(return_value=2025)
        )
        bundle = SimpleNamespace(tenk=SimpleNamespace(sections={"0": _section("toc")}))
        monkeypatch.setattr(
            sweep_module, "fetch_filing_bundle", Mock(return_value=bundle)
        )
        fake_parse_filing = Mock(return_value=SimpleNamespace(items=[object()] * 3))
        monkeypatch.setattr(sweep_module, "parse_filing", fake_parse_filing)

        result = sweep_ticker("nvda")

        assert len(result.sections) == 1
        assert result.filing_error is None
        assert result.parse_outcome == "ok"
        assert result.parse_item_count == 3
        # The cross-check must bypass the on-disk filing-store cache (a
        # fresh force=True read) and must never persist its result back to
        # it (a non-persisting store).
        fake_parse_filing.assert_called_once()
        call = fake_parse_filing.call_args
        assert call.args == ("NVDA", 2025)
        assert call.kwargs["force"] is True
        assert isinstance(call.kwargs["store"], sweep_module._NonPersistingStore)

    def test_fetch_failure_records_fetch_error_and_skips_parse(self, monkeypatch):
        monkeypatch.setattr(
            sweep_module,
            "_resolve_latest_fiscal_year",
            Mock(side_effect=TickerNotFoundError("no CIK for BADTICKER")),
        )
        fake_parse_filing = Mock()
        monkeypatch.setattr(sweep_module, "parse_filing", fake_parse_filing)

        result = sweep_ticker("BADTICKER")

        assert result.fetch_error is not None
        assert "TickerNotFoundError" in result.fetch_error
        fake_parse_filing.assert_not_called()

    def test_zero_sections_still_runs_parse_cross_check(self, monkeypatch):
        # A filing_error (zero observed sections) must not prevent
        # parse_filing()'s own outcome from being recorded — the two
        # signals are independent.
        monkeypatch.setattr(
            sweep_module, "_resolve_latest_fiscal_year", Mock(return_value=2025)
        )
        empty_bundle = SimpleNamespace(tenk=SimpleNamespace(sections={}))
        monkeypatch.setattr(
            sweep_module, "fetch_filing_bundle", Mock(return_value=empty_bundle)
        )
        fake_parse_filing = Mock(return_value=SimpleNamespace(items=[object()] * 5))
        monkeypatch.setattr(sweep_module, "parse_filing", fake_parse_filing)

        result = sweep_ticker("nodoc")

        assert result.filing_error is not None
        assert result.parse_outcome == "ok"
        assert result.parse_item_count == 5


class TestParseOutcomeCell:
    def test_fetch_error_takes_precedence(self):
        result = TickerSweepResult(ticker="X", fetch_error="TickerNotFoundError: nope")
        assert _parse_outcome_cell(result) == "fetch failed: TickerNotFoundError: nope"

    def test_filing_error_shown_distinctly_from_fetch_error(self):
        # The zero-sections case: the bundle fetch succeeded (no
        # fetch_error), but the filing itself produced no sections.
        # sweep_ticker() still runs the parse_filing() cross-check
        # afterward, so a realistic fixture has both filing_error AND a
        # populated parse_outcome — the cell must show its own filing-error
        # message AND the parse_filing() outcome, neither hiding the other
        # (previously the outcome branches were unreachable whenever
        # filing_error was set).
        result = TickerSweepResult(
            ticker="X",
            filing_error="fetched X FY2025 successfully but edgartools produced 0 sections",
            parse_outcome="ok",
            parse_item_count=18,
        )
        cell = _parse_outcome_cell(result)
        assert cell.startswith("filing error:")
        assert "0 sections" in cell
        assert "ok (18 items)" in cell

    def test_ok_outcome_reports_item_count(self):
        result = TickerSweepResult(ticker="X", parse_outcome="ok", parse_item_count=18)
        assert _parse_outcome_cell(result) == "ok (18 items)"

    def test_empty_filing_outcome_reports_parse_error(self):
        result = TickerSweepResult(
            ticker="X", parse_outcome="empty_filing", parse_error="0 substantive items"
        )
        assert _parse_outcome_cell(result) == "EmptyFilingError: 0 substantive items"

    def test_not_run_outcome(self):
        assert _parse_outcome_cell(TickerSweepResult(ticker="X")) == "not run"


class TestUndeterminedSection:
    def test_filing_error_ticker_shows_its_own_reason_not_none(self):
        # Same bug class as _parse_outcome_cell above, in the report's
        # "Undetermined" listing: a zero-sections ticker (filing_error set,
        # fetch_error unset) must show its own reason, not the literal
        # string "None" from a fetch_error fallback that was never set.
        result = TickerSweepResult(
            ticker="ZEROSEC",
            filing_error="fetched ZEROSEC FY2025 successfully but edgartools produced 0 sections",
        )
        report = render_report([result])
        assert "ZEROSEC: None" not in report
        assert "ZEROSEC: fetched ZEROSEC FY2025" in report


class TestRenderReportCurationNote:
    """The sweep-corpus curation-exclusions note describes the default
    16-ticker corpus's own curation history — it must not print for an ad
    hoc ticker subset, which has no such history to report."""

    def test_full_default_corpus_includes_curation_note(self):
        results = [_result(ticker, ["toc"]) for ticker in SWEEP_TICKERS]
        report = render_report(results)
        assert "Sweep-corpus curation exclusions" in report

    def test_ad_hoc_subset_omits_curation_note(self):
        results = [_result("AMD", ["toc"]), _result("NVDA", ["toc"])]
        report = render_report(results)
        assert "Sweep-corpus curation exclusions" not in report
