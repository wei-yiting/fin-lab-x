import pytest

from backend.evals.experiments.tool_error_messages.analyze import (
    Scope,
    bootstrap_ci,
    gap_phrases,
    permanent_scope,
    used_alternative,
    wasted_calls,
)


def _run(tool, turn, seq, error=None, **args):
    return {"tool": tool, "turn": turn, "start_seq": seq, "error": error, "args": args}


_403 = "FinnhubAPIException(status_code: 403): You don't have access to this resource."
_20F = "Ticker TSM appears to be a foreign private issuer that files 20-F; only '10-K' is supported."


@pytest.mark.parametrize(
    ("error", "args", "expected"),
    [
        (_20F, {"ticker": "TSM"}, Scope("sec", "TSM")),
        (
            "Ticker 'RY' has no 10-K filings on SEC EDGAR.",
            {"ticker": "ry"},
            Scope("sec", "RY"),
        ),
        (
            "Ticker 'AIR.PA' not found on SEC EDGAR.",
            {"ticker": "AIR.PA"},
            Scope("sec", "AIR.PA"),
        ),
        (_403, {"ticker": "MC.PA"}, Scope("finnhub", "MC.PA")),
        (
            "No quote data for ticker 'SQ'. The symbol may be invalid.",
            {"ticker": "SQ"},
            Scope("finnhub", "SQ"),
        ),
        (
            "Section '7' not found in INTC 10-K FY2025. Call sec_filing_list_sections first.",
            {"ticker": "INTC", "section_key": "Item 7"},
            Scope("section", "INTC", section="7", fiscal_year=2025),
        ),
        (
            "TSLA has no 10-K filing history before FY2010; fiscal year 2008 could never have one.",
            {"ticker": "TSLA", "fiscal_year": 2008},
            Scope("year", "TSLA", fiscal_year=2008),
        ),
        ("SEC EDGAR returned 503 for AAPL.", {"ticker": "AAPL"}, None),
        ("Rate-limited by SEC EDGAR (AAPL)", {"ticker": "AAPL"}, None),
    ],
)
def test_permanent_scope_classifies_raw_errors(error, args, expected):
    assert (
        permanent_scope(
            {"tool": "sec_filing_get_section", "error": error, "args": args}
        )
        == expected
    )


def test_parallel_calls_in_the_failing_turn_are_not_wasted():
    runs = [
        _run("finnhub_stock_quote", 1, 0, _403, ticker="AIR.PA"),
        _run("finnhub_company_basic_financials", 1, 1, _403, ticker="AIR.PA"),
    ]
    assert wasted_calls(runs) == []


def test_later_call_to_failed_provider_and_ticker_is_wasted():
    runs = [
        _run("finnhub_stock_quote", 1, 0, _403, ticker="AIR.PA"),
        _run("finnhub_company_basic_financials", 2, 1, _403, ticker="AIR.PA"),
        _run("finnhub_stock_quote", 2, 2, None, ticker="EADSY"),
        _run("sec_filing_list_sections", 2, 3, None, ticker="AIR.PA"),
    ]
    assert [c["start_seq"] for c in wasted_calls(runs)] == [1]


def test_section_retry_with_reformatted_key_is_wasted_but_other_section_is_not():
    err = "Section '7' not found in INTC 10-K FY2025. Call sec_filing_list_sections first."
    runs = [
        _run(
            "sec_filing_get_section",
            2,
            1,
            err,
            ticker="INTC",
            section_key="7",
            fiscal_year=2025,
        ),
        _run(
            "sec_filing_get_section",
            3,
            2,
            err,
            ticker="INTC",
            section_key="Item 7",
            fiscal_year=2025,
        ),
        _run(
            "sec_filing_get_section",
            3,
            3,
            None,
            ticker="INTC",
            section_key="1a",
            fiscal_year=2025,
        ),
    ]
    assert [c["start_seq"] for c in wasted_calls(runs)] == [2]


def test_alternative_must_succeed_no_earlier_than_first_failure():
    runs = [
        _run("sec_filing_list_sections", 1, 0, None, ticker="INTC"),
        _run(
            "sec_filing_get_section",
            2,
            1,
            "Section '7' not found in INTC 10-K FY2025.",
            ticker="INTC",
        ),
    ]
    assert not used_alternative(runs, ["sec_filing_*", "tavily_financial_search"])
    runs.append(_run("tavily_financial_search", 2, 2, None, query="intel"))
    assert used_alternative(runs, ["sec_filing_*", "tavily_financial_search"])


def test_alternative_ticker_constraint():
    runs = [
        _run(
            "finnhub_stock_quote", 1, 0, "No quote data for ticker 'SQ'.", ticker="SQ"
        ),
        _run("finnhub_stock_quote", 2, 1, None, ticker="SQQQ"),
    ]
    assert not used_alternative(runs, ["finnhub_*:XYZ"])
    runs.append(_run("finnhub_company_basic_financials", 2, 2, None, ticker="xyz"))
    assert used_alternative(runs, ["finnhub_*:XYZ"])


@pytest.mark.parametrize(
    ("text", "hit"),
    [
        ("台積電申報 20-F，系統無法取得其 10-K 內容。", True),
        ("Finnhub 查不到 AIR.PA 的報價。", True),
        ("2027 財年的 10-K 尚未申報。", True),
        ("Live quotes for 0700.HK are not available here.", True),
        ("出口限制對艾司摩爾影響較大。", False),
        ("可口可樂連續 60 年調升股利。", False),
    ],
)
def test_gap_regex(text, hit):
    assert bool(gap_phrases(text)) is hit


def test_bootstrap_ci_brackets_the_mean():
    mean, lo, hi = bootstrap_ci([-1.0, 0.0, -2.0, -1.0, 0.0, -1.0])
    assert lo <= mean <= hi
    assert mean == pytest.approx(-5 / 6)
