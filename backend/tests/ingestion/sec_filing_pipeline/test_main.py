"""Tests for the SEC filing pipeline CLI entry point."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest

from backend.ingestion.sec_filing_pipeline.__main__ import main
from backend.ingestion.sec_filing_pipeline.filing_models import (
    FilingMetadata,
    FilingType,
    ParsedFiling,
    TickerNotFoundError,
)
from backend.ingestion.sec_filing_pipeline.pipeline import BatchResult


@pytest.fixture()
def sample_filing():
    return ParsedFiling(
        metadata=FilingMetadata(
            ticker="AAPL",
            cik="0000320193",
            company_name="Apple Inc.",
            filing_type=FilingType.TEN_K,
            filing_date="2024-11-01",
            fiscal_year=2024,
            accession_number="0000320193-24-000123",
            source_url="https://www.sec.gov/Archives/edgar/data/320193/filing.htm",
            parsed_at="2026-04-03T10:30:00+00:00",
            converter="html-to-markdown",
        ),
        markdown_content="# 10-K content",
    )


@pytest.fixture()
def mock_pipeline(sample_filing):
    pipeline = MagicMock()
    pipeline.process.return_value = sample_filing
    return pipeline


# --- Single mode ---


def test_single_basic(mock_pipeline, capsys):
    with patch(
        "backend.ingestion.sec_filing_pipeline.__main__.SECFilingPipeline"
    ) as cls:
        cls.create.return_value = mock_pipeline
        main(["AAPL", "10-K"])

    out = capsys.readouterr().out
    assert "AAPL" in out
    assert "FY2024" in out
    assert "data/sec_filings/AAPL/10-K/2024.md" in out
    mock_pipeline.process.assert_called_once_with("AAPL", "10-K", None, False)


def test_single_fiscal_year_and_force(mock_pipeline):
    with patch(
        "backend.ingestion.sec_filing_pipeline.__main__.SECFilingPipeline"
    ) as cls:
        cls.create.return_value = mock_pipeline
        main(["AAPL", "10-K", "--fiscal-year", "2023", "--force"])

    mock_pipeline.process.assert_called_once_with("AAPL", "10-K", 2023, True)


def test_single_verbose(mock_pipeline, capsys):
    with patch(
        "backend.ingestion.sec_filing_pipeline.__main__.SECFilingPipeline"
    ) as cls:
        cls.create.return_value = mock_pipeline
        main(["AAPL", "10-K", "--verbose"])

    out = capsys.readouterr().out
    assert "ticker:" in out
    assert "company_name:" in out
    assert "cik:" in out
    assert "accession_number:" in out
    assert "source_url:" in out
    assert "converter:" in out
    assert "file_path:" in out


def test_single_json(mock_pipeline, capsys):
    with patch(
        "backend.ingestion.sec_filing_pipeline.__main__.SECFilingPipeline"
    ) as cls:
        cls.create.return_value = mock_pipeline
        main(["AAPL", "10-K", "--json"])

    out = capsys.readouterr().out
    data = json.loads(out)
    assert data["metadata"]["ticker"] == "AAPL"
    assert data["content_length"] == len("# 10-K content")
    assert data["file_path"] == "data/sec_filings/AAPL/10-K/2024.md"


def test_single_error(capsys):
    pipeline = MagicMock()
    pipeline.process.side_effect = TickerNotFoundError("Ticker ZZZZ not found")

    with patch(
        "backend.ingestion.sec_filing_pipeline.__main__.SECFilingPipeline"
    ) as cls:
        cls.create.return_value = pipeline
        with pytest.raises(SystemExit, match="1"):
            main(["ZZZZ", "10-K"])

    err = capsys.readouterr().err
    assert "TickerNotFoundError" in err
    assert "ZZZZ" in err


# --- Batch mode ---


def test_batch_basic(sample_filing, capsys):
    results = {
        "AAPL": BatchResult(
            status="success", filing=sample_filing, error=None, from_cache=False
        ),
    }
    pipeline = MagicMock()
    pipeline.process_batch.return_value = results

    with patch(
        "backend.ingestion.sec_filing_pipeline.__main__.SECFilingPipeline"
    ) as cls:
        cls.create.return_value = pipeline
        main(["batch", "AAPL", "--filing-type", "10-K"])

    out = capsys.readouterr().out
    assert "AAPL" in out
    assert "ok" in out
    pipeline.process_batch.assert_called_once_with(["AAPL"], "10-K")


def test_batch_partial_failure(sample_filing):
    results = {
        "AAPL": BatchResult(
            status="success", filing=sample_filing, error=None, from_cache=False
        ),
        "ZZZZ": BatchResult(
            status="error", filing=None, error=TickerNotFoundError("Ticker not found"), from_cache=False
        ),
    }
    pipeline = MagicMock()
    pipeline.process_batch.return_value = results

    with patch(
        "backend.ingestion.sec_filing_pipeline.__main__.SECFilingPipeline"
    ) as cls:
        cls.create.return_value = pipeline
        with pytest.raises(SystemExit, match="1"):
            main(["batch", "AAPL", "ZZZZ", "--filing-type", "10-K"])


def test_batch_all_success(sample_filing):
    results = {
        "AAPL": BatchResult(
            status="success", filing=sample_filing, error=None, from_cache=False
        ),
    }
    pipeline = MagicMock()
    pipeline.process_batch.return_value = results

    with patch(
        "backend.ingestion.sec_filing_pipeline.__main__.SECFilingPipeline"
    ) as cls:
        cls.create.return_value = pipeline
        main(["batch", "AAPL", "--filing-type", "10-K"])


def test_batch_json(sample_filing, capsys):
    results = {
        "AAPL": BatchResult(
            status="success", filing=sample_filing, error=None, from_cache=False
        ),
        "ZZZZ": BatchResult(
            status="error", filing=None, error=TickerNotFoundError("Ticker not found"), from_cache=False
        ),
    }
    pipeline = MagicMock()
    pipeline.process_batch.return_value = results

    with patch(
        "backend.ingestion.sec_filing_pipeline.__main__.SECFilingPipeline"
    ) as cls:
        cls.create.return_value = pipeline
        with pytest.raises(SystemExit, match="1"):
            main(["batch", "AAPL", "ZZZZ", "--filing-type", "10-K", "--json"])

    out = capsys.readouterr().out
    data = json.loads(out)
    assert data["AAPL"]["status"] == "success"
    assert data["AAPL"]["file_path"] == "data/sec_filings/AAPL/10-K/2024.md"
    assert data["ZZZZ"]["status"] == "error"


# --- Help / no args ---


def test_help_no_crash(capsys):
    main(["--help"])
    out = capsys.readouterr().out
    assert "batch" in out
    assert "TICKER" in out


def test_no_args_shows_usage(capsys):
    main([])
    out = capsys.readouterr().out
    assert "usage:" in out
