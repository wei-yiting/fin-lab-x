"""Tests for the SEC filing pipeline agent tool."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from pydantic import ValidationError

from backend.agent_engine.tools.sec_filing import sec_filing_downloader
from backend.ingestion.sec_filing_pipeline.filing_models import (
    FilingMetadata,
    FilingType,
    ParsedFiling,
    TickerNotFoundError,
)


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


def test_tool_exists():
    assert sec_filing_downloader is not None
    assert hasattr(sec_filing_downloader, "invoke")


def test_schema_validation_missing_ticker():
    with pytest.raises(ValidationError):
        sec_filing_downloader.invoke({})


def test_successful_download(sample_filing):
    mock_pipeline = MagicMock()
    mock_pipeline.process.return_value = sample_filing

    with patch(
        "backend.agent_engine.tools.sec_filing.SECFilingPipeline"
    ) as cls:
        cls.create.return_value = mock_pipeline
        result = sec_filing_downloader.invoke(
            {"ticker": "AAPL", "filing_type": "10-K"}
        )

    assert result["ticker"] == "AAPL"
    assert result["company_name"] == "Apple Inc."
    assert result["fiscal_year"] == 2024
    assert result["file_path"] == "data/sec_filings/AAPL/10-K/2024.md"
    assert "error" not in result


def test_pipeline_error_returns_error_dict():
    mock_pipeline = MagicMock()
    mock_pipeline.process.side_effect = TickerNotFoundError("Ticker ZZZZ not found")

    with patch(
        "backend.agent_engine.tools.sec_filing.SECFilingPipeline"
    ) as cls:
        cls.create.return_value = mock_pipeline
        result = sec_filing_downloader.invoke(
            {"ticker": "ZZZZ", "filing_type": "10-K"}
        )

    assert result["error"] is True
    assert "TickerNotFoundError" in result["message"]
