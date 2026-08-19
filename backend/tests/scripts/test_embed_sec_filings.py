"""Unit tests for the batch ingest script — parse_filing_with_retry and
ingest_filing_with_retry are mocked throughout; nothing here touches EDGAR,
OpenAI, or Qdrant.
"""

from unittest.mock import AsyncMock, patch

import pytest

from backend.scripts.embed_sec_filings import _parse_and_ingest, main
from backend.tests.ingestion.sec_dense_pipeline.conftest import make_toy_filing


@pytest.mark.asyncio
async def test_parse_and_ingest_calls_parse_then_ingest_with_given_year():
    """_parse_and_ingest takes an already-resolved concrete fiscal_year —
    latest-year resolution is main()'s responsibility, exercised separately
    below via the main()-level tests."""
    toy = make_toy_filing()
    with (
        patch(
            "backend.scripts.embed_sec_filings.parse_filing_with_retry",
            return_value=toy,
        ) as mock_parse,
        patch(
            "backend.scripts.embed_sec_filings.ingest_filing_with_retry",
            new=AsyncMock(),
        ) as mock_ingest,
    ):
        await _parse_and_ingest("AAPL", 2024)

    mock_parse.assert_called_once_with("AAPL", 2024, False)
    mock_ingest.assert_awaited_once_with(toy)


def test_main_reports_success_for_all_tickers(capsys):
    toy = make_toy_filing()
    with (
        patch(
            "backend.scripts.embed_sec_filings.parse_filing_with_retry",
            return_value=toy,
        ),
        patch(
            "backend.scripts.embed_sec_filings.ingest_filing_with_retry",
            new=AsyncMock(),
        ),
    ):
        exit_code = main(["aapl", "msft", "--fiscal-year", "2024"])

    assert exit_code == 0
    out = capsys.readouterr().out
    assert "AAPL" in out and "MSFT" in out
    assert "success" in out
    assert "failed" not in out
    # Explicit --fiscal-year must show up in the summary too, not just the
    # resolved-latest case.
    assert out.count("2024") == 2


def test_main_reports_resolved_fiscal_year_when_flag_omitted(capsys):
    """The operator must be able to tell which year was picked when
    --fiscal-year is omitted and latest-year resolution runs."""
    toy = make_toy_filing()
    with (
        patch(
            "backend.scripts.embed_sec_filings.resolve_latest_fiscal_year_with_retry",
            return_value=2025,
        ) as mock_resolve,
        patch(
            "backend.scripts.embed_sec_filings.parse_filing_with_retry",
            return_value=toy,
        ),
        patch(
            "backend.scripts.embed_sec_filings.ingest_filing_with_retry",
            new=AsyncMock(),
        ),
    ):
        exit_code = main(["AAPL"])

    assert exit_code == 0
    mock_resolve.assert_called_once_with("AAPL")
    out = capsys.readouterr().out
    assert "AAPL" in out
    assert "2025" in out


def test_main_continues_past_a_failing_ticker_and_reports_it(capsys):
    toy = make_toy_filing()

    def parse_side_effect(ticker, fiscal_year, force):
        if ticker == "ZZZZ":
            raise ValueError("Ticker 'ZZZZ' not found in SEC EDGAR")
        return toy

    with (
        patch(
            "backend.scripts.embed_sec_filings.parse_filing_with_retry",
            side_effect=parse_side_effect,
        ),
        patch(
            "backend.scripts.embed_sec_filings.ingest_filing_with_retry",
            new=AsyncMock(),
        ),
    ):
        exit_code = main(["AAPL", "ZZZZ", "--fiscal-year", "2024"])

    assert exit_code == 1
    out = capsys.readouterr().out
    assert "AAPL" in out and "success" in out
    assert "ZZZZ" in out and "failed" in out
    assert "not found" in out


def test_main_reports_resolved_year_when_ingest_fails_after_resolution(capsys):
    """If latest-year resolution succeeds but a later step (parse or ingest)
    fails, the summary must still show the real resolved year, not fall
    back to the omitted --fiscal-year (None) and print '?'."""
    toy = make_toy_filing()
    with (
        patch(
            "backend.scripts.embed_sec_filings.resolve_latest_fiscal_year_with_retry",
            return_value=2025,
        ) as mock_resolve,
        patch(
            "backend.scripts.embed_sec_filings.parse_filing_with_retry",
            return_value=toy,
        ),
        patch(
            "backend.scripts.embed_sec_filings.ingest_filing_with_retry",
            new=AsyncMock(side_effect=RuntimeError("Qdrant unavailable")),
        ),
    ):
        exit_code = main(["AAPL"])

    assert exit_code == 1
    mock_resolve.assert_called_once_with("AAPL")
    out = capsys.readouterr().out
    aapl_line = next(line for line in out.splitlines() if line.startswith("AAPL"))
    assert "2025" in aapl_line
    assert "failed" in aapl_line
    assert "?" not in aapl_line
