from datetime import date
from unittest.mock import MagicMock, patch

import pytest

from backend.ingestion.sec_filing_pipeline.filing_models import (
    ConfigurationError,
    FilingNotFoundError,
    RawFiling,
    TickerNotFoundError,
    UnsupportedFilingTypeError,
)
from backend.ingestion.sec_filing_pipeline.sec_downloader import SECDownloader


@pytest.fixture(autouse=True)
def _set_edgar_identity(monkeypatch):
    monkeypatch.setenv("EDGAR_IDENTITY", "Test User test@example.com")


@pytest.fixture()
def mock_filing():
    filing = MagicMock()
    filing.html.return_value = "<html><body>10-K content</body></html>"
    filing.period_of_report = date(2024, 9, 28)
    filing.filing_date = date(2024, 11, 1)
    filing.accession_number = "0000320193-24-000123"
    filing.filing_url = "https://www.sec.gov/Archives/edgar/data/320193/filing.htm"
    return filing


@pytest.fixture()
def mock_company(mock_filing):
    company = MagicMock()
    company.cik = 320193
    company.name = "Apple Inc."

    filings = MagicMock()
    filings.latest.return_value = mock_filing
    filings.filter.return_value = filings
    company.get_filings.return_value = filings

    return company


class TestSECDownloaderInit:
    @patch("backend.ingestion.sec_filing_pipeline.sec_downloader.set_identity")
    def test_sets_identity_from_env(self, mock_set_identity):
        SECDownloader()
        mock_set_identity.assert_called_once_with("Test User test@example.com")

    def test_raises_when_identity_missing(self, monkeypatch):
        monkeypatch.delenv("EDGAR_IDENTITY", raising=False)
        with pytest.raises(ConfigurationError, match="EDGAR_IDENTITY"):
            SECDownloader()


class TestDownloadHappyPath:
    @patch("backend.ingestion.sec_filing_pipeline.sec_downloader.Company")
    def test_returns_raw_filing_with_correct_metadata(
        self, mock_company_cls, mock_company, mock_filing
    ):
        mock_company_cls.return_value = mock_company
        downloader = SECDownloader()

        result = downloader.download("aapl", "10-K")

        assert isinstance(result, RawFiling)
        assert result.raw_html == "<html><body>10-K content</body></html>"
        assert result.ticker == "AAPL"
        assert result.cik == "320193"
        assert result.company_name == "Apple Inc."
        assert result.filing_date == "2024-11-01"
        assert result.fiscal_year == 2024
        assert result.accession_number == "0000320193-24-000123"
        assert (
            result.source_url
            == "https://www.sec.gov/Archives/edgar/data/320193/filing.htm"
        )

    @patch("backend.ingestion.sec_filing_pipeline.sec_downloader.Company")
    def test_normalizes_ticker_to_uppercase(self, mock_company_cls, mock_company):
        mock_company_cls.return_value = mock_company
        downloader = SECDownloader()

        result = downloader.download("aapl", "10-K")

        mock_company_cls.assert_called_once_with("AAPL")
        assert result.ticker == "AAPL"

    @patch("backend.ingestion.sec_filing_pipeline.sec_downloader.Company")
    def test_calls_get_filings_with_form(self, mock_company_cls, mock_company):
        mock_company_cls.return_value = mock_company
        downloader = SECDownloader()

        downloader.download("AAPL", "10-K")

        mock_company.get_filings.assert_called_once_with(form="10-K")


class TestDownloadWithFiscalYear:
    @patch("backend.ingestion.sec_filing_pipeline.sec_downloader.Company")
    def test_filters_by_fiscal_year_range(self, mock_company_cls, mock_company):
        mock_company_cls.return_value = mock_company
        downloader = SECDownloader()

        downloader.download("AAPL", "10-K", fiscal_year=2024)

        filings = mock_company.get_filings.return_value
        filings.filter.assert_called_once_with(date="2023-01-01:2025-01-01")

    @patch("backend.ingestion.sec_filing_pipeline.sec_downloader.Company")
    def test_raises_when_derived_fy_mismatches(
        self, mock_company_cls, mock_company, mock_filing
    ):
        mock_filing.period_of_report = date(2023, 9, 30)
        mock_company_cls.return_value = mock_company
        downloader = SECDownloader()

        with pytest.raises(FilingNotFoundError, match="fiscal year 2024"):
            downloader.download("AAPL", "10-K", fiscal_year=2024)

    @patch("backend.ingestion.sec_filing_pipeline.sec_downloader.Company")
    def test_no_filter_when_fiscal_year_omitted(self, mock_company_cls, mock_company):
        mock_company_cls.return_value = mock_company
        downloader = SECDownloader()

        downloader.download("AAPL", "10-K")

        filings = mock_company.get_filings.return_value
        filings.filter.assert_not_called()


class TestDownloadErrorMapping:
    @patch("backend.ingestion.sec_filing_pipeline.sec_downloader.Company")
    def test_company_not_found_raises_ticker_not_found(self, mock_company_cls):
        from edgar import CompanyNotFoundError

        mock_company_cls.side_effect = CompanyNotFoundError("INVALID")
        downloader = SECDownloader()

        with pytest.raises(TickerNotFoundError, match="INVALID"):
            downloader.download("INVALID", "10-K")

    def test_unsupported_filing_type_raises_error(self):
        downloader = SECDownloader()

        with pytest.raises(UnsupportedFilingTypeError, match="10-Q"):
            downloader.download("AAPL", "10-Q")

    @patch("backend.ingestion.sec_filing_pipeline.sec_downloader.Company")
    def test_no_filings_found_raises_filing_not_found(
        self, mock_company_cls, mock_company
    ):
        mock_company.get_filings.return_value.latest.return_value = None
        mock_company_cls.return_value = mock_company
        downloader = SECDownloader()

        with pytest.raises(FilingNotFoundError, match="AAPL"):
            downloader.download("AAPL", "10-K")

    @patch("backend.ingestion.sec_filing_pipeline.sec_downloader.Company")
    def test_no_filings_for_fiscal_year_raises_filing_not_found(
        self, mock_company_cls, mock_company
    ):
        filings = mock_company.get_filings.return_value
        filings.filter.return_value.latest.return_value = None
        mock_company_cls.return_value = mock_company
        downloader = SECDownloader()

        with pytest.raises(FilingNotFoundError, match="fiscal year 2020"):
            downloader.download("AAPL", "10-K", fiscal_year=2020)
