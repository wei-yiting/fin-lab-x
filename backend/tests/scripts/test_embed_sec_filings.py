"""Unit tests for the batch ingest script — parse_filing_with_retry and
ingest_filing_with_retry are mocked throughout; nothing here touches EDGAR,
OpenAI, or Qdrant.
"""

from unittest.mock import AsyncMock, patch

import pytest

from backend.scripts.embed_sec_filings import _embed_one, main
from backend.tests.ingestion.sec_dense_pipeline.conftest import make_toy_filing


@pytest.mark.asyncio
async def test_embed_one_uses_explicit_fiscal_year_without_resolving_latest():
    toy = make_toy_filing()
    with (
        patch(
            "backend.scripts.embed_sec_filings._resolve_latest_fiscal_year"
        ) as mock_resolve,
        patch(
            "backend.scripts.embed_sec_filings.parse_filing_with_retry",
            return_value=toy,
        ) as mock_parse,
        patch(
            "backend.scripts.embed_sec_filings.ingest_filing_with_retry",
            new=AsyncMock(),
        ) as mock_ingest,
    ):
        resolved = await _embed_one("AAPL", 2024)

    mock_resolve.assert_not_called()
    mock_parse.assert_called_once_with("AAPL", 2024, False)
    mock_ingest.assert_awaited_once_with(toy)
    assert resolved == 2024


@pytest.mark.asyncio
async def test_embed_one_resolves_latest_fiscal_year_when_omitted():
    toy = make_toy_filing()
    with (
        patch(
            "backend.scripts.embed_sec_filings._resolve_latest_fiscal_year",
            return_value=2025,
        ) as mock_resolve,
        patch(
            "backend.scripts.embed_sec_filings.parse_filing_with_retry",
            return_value=toy,
        ) as mock_parse,
        patch(
            "backend.scripts.embed_sec_filings.ingest_filing_with_retry",
            new=AsyncMock(),
        ),
    ):
        resolved = await _embed_one("AAPL", None)

    mock_resolve.assert_called_once_with("AAPL")
    mock_parse.assert_called_once_with("AAPL", 2025, False)
    assert resolved == 2025


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
            "backend.scripts.embed_sec_filings._resolve_latest_fiscal_year",
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
