from unittest.mock import MagicMock, patch

import pytest

from backend.ingestion.sec_filing_pipeline.filing_models import (
    FilingMetadata,
    FilingNotFoundError,
    FilingType,
    ParsedFiling,
    RawFiling,
    TransientError,
    UnsupportedFilingTypeError,
)
from backend.ingestion.sec_filing_pipeline.pipeline import BatchResult, SECFilingPipeline


@pytest.fixture()
def raw_filing():
    return RawFiling(
        raw_html="<html><body>10-K content</body></html>",
        ticker="AAPL",
        cik="0000320193",
        company_name="Apple Inc.",
        filing_date="2024-11-01",
        fiscal_year=2024,
        accession_number="0000320193-24-000123",
        source_url="https://www.sec.gov/Archives/edgar/data/320193/filing.htm",
    )


@pytest.fixture()
def parsed_filing():
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
def mock_downloader(raw_filing):
    downloader = MagicMock()
    downloader.download.return_value = raw_filing
    return downloader


@pytest.fixture()
def mock_preprocessor():
    preprocessor = MagicMock()
    preprocessor.preprocess.return_value = "<html><body>cleaned</body></html>"
    return preprocessor


@pytest.fixture()
def mock_converter():
    converter = MagicMock()
    converter.name = "test-primary"
    converter.convert.return_value = "# Markdown output"
    return converter


@pytest.fixture()
def mock_fallback_converter():
    converter = MagicMock()
    converter.name = "test-fallback"
    converter.convert.return_value = "# Fallback markdown"
    return converter


@pytest.fixture()
def mock_store():
    store = MagicMock()
    store.exists.return_value = False
    store.get.return_value = None
    return store


@pytest.fixture()
def pipeline(mock_downloader, mock_preprocessor, mock_converter, mock_fallback_converter, mock_store):
    return SECFilingPipeline(
        downloader=mock_downloader,
        preprocessor=mock_preprocessor,
        converter=mock_converter,
        fallback_converter=mock_fallback_converter,
        store=mock_store,
    )


class TestProcessCacheHit:
    def test_returns_cached_filing_when_fiscal_year_specified(
        self, pipeline, mock_store, mock_downloader, parsed_filing
    ):
        mock_store.get.return_value = parsed_filing

        result = pipeline.process("AAPL", "10-K", fiscal_year=2024)

        assert result is parsed_filing
        mock_downloader.download.assert_not_called()
        mock_store.get.assert_called_once_with("AAPL", FilingType.TEN_K, 2024)

    def test_cache_check_uses_resolved_fiscal_year_when_omitted(
        self, pipeline, mock_store, mock_downloader, raw_filing, parsed_filing
    ):
        mock_store.get.return_value = parsed_filing

        result = pipeline.process("AAPL", "10-K")

        mock_downloader.download.assert_called_once_with("AAPL", "10-K", None)
        mock_store.get.assert_called_once_with("AAPL", FilingType.TEN_K, raw_filing.fiscal_year)
        assert result is parsed_filing


class TestProcessCacheMiss:
    def test_downloads_and_processes_when_not_cached(
        self, pipeline, mock_downloader, mock_preprocessor, mock_converter, mock_store
    ):
        result = pipeline.process("AAPL", "10-K", fiscal_year=2024)

        mock_downloader.download.assert_called_once_with("AAPL", "10-K", 2024)
        mock_preprocessor.preprocess.assert_called_once()
        mock_store.save.assert_called_once()
        assert result.metadata.ticker == "AAPL"
        assert result.metadata.fiscal_year == 2024
        assert result.metadata.filing_type == FilingType.TEN_K

    def test_downloads_when_fiscal_year_omitted_and_not_cached(
        self, pipeline, mock_downloader, mock_preprocessor, mock_store
    ):
        result = pipeline.process("AAPL", "10-K")

        mock_downloader.download.assert_called_once_with("AAPL", "10-K", None)
        mock_preprocessor.preprocess.assert_called_once()
        mock_store.save.assert_called_once()
        assert result.metadata.fiscal_year == 2024


class TestProcessTickerNormalization:
    def test_lowercase_ticker_normalized_to_uppercase(
        self, pipeline, mock_downloader, mock_store
    ):
        pipeline.process("aapl", "10-K", fiscal_year=2024)

        mock_store.get.assert_called_with("AAPL", FilingType.TEN_K, 2024)
        mock_downloader.download.assert_called_once_with("AAPL", "10-K", 2024)

    def test_mixed_case_ticker_normalized(
        self, pipeline, mock_downloader, mock_store
    ):
        pipeline.process("AaPl", "10-K", fiscal_year=2024)

        mock_store.get.assert_called_with("AAPL", FilingType.TEN_K, 2024)


class TestProcessForceBypassesCache:
    def test_force_skips_cache_check_and_downloads(
        self, pipeline, mock_store, mock_downloader
    ):
        mock_store.get.return_value = MagicMock()
        mock_store.exists.return_value = True

        pipeline.process("AAPL", "10-K", fiscal_year=2024, force=True)

        mock_store.get.assert_not_called()
        mock_downloader.download.assert_called_once()
        mock_store.save.assert_called_once()


class TestProcessValidation:
    def test_unsupported_filing_type_raises(self, pipeline):
        with pytest.raises(UnsupportedFilingTypeError, match="10-Q"):
            pipeline.process("AAPL", "10-Q")


class TestProcessDataFlow:
    def test_preprocessor_receives_raw_html(
        self, pipeline, mock_preprocessor, raw_filing
    ):
        pipeline.process("AAPL", "10-K", fiscal_year=2024)

        mock_preprocessor.preprocess.assert_called_once_with(raw_filing.raw_html)

    def test_converter_receives_preprocessed_html(
        self, pipeline, mock_preprocessor, mock_converter
    ):
        mock_preprocessor.preprocess.return_value = "<cleaned/>"

        pipeline.process("AAPL", "10-K", fiscal_year=2024)

        mock_converter.convert.assert_called_once_with("<cleaned/>")

    def test_metadata_assembled_from_raw_filing(self, pipeline, raw_filing):
        result = pipeline.process("AAPL", "10-K", fiscal_year=2024)

        assert result.metadata.ticker == raw_filing.ticker
        assert result.metadata.cik == raw_filing.cik
        assert result.metadata.company_name == raw_filing.company_name
        assert result.metadata.filing_date == raw_filing.filing_date
        assert result.metadata.accession_number == raw_filing.accession_number
        assert result.metadata.source_url == raw_filing.source_url
        assert result.metadata.parsed_at is not None

    def test_store_save_called_with_assembled_filing(self, pipeline, mock_store):
        pipeline.process("AAPL", "10-K", fiscal_year=2024)

        mock_store.save.assert_called_once()
        saved = mock_store.save.call_args[0][0]
        assert isinstance(saved, ParsedFiling)


class TestProcessBatch:
    def test_batch_returns_results_for_all_tickers(self, pipeline):
        results = pipeline.process_batch(["AAPL", "MSFT"], "10-K")

        assert "AAPL" in results
        assert "MSFT" in results
        assert len(results) == 2

    def test_batch_success_results(self, pipeline):
        results = pipeline.process_batch(["AAPL"], "10-K")

        result = results["AAPL"]
        assert result.status == "success"
        assert result.filing is not None
        assert result.error is None

    def test_batch_normalizes_ticker_keys(self, pipeline):
        results = pipeline.process_batch(["aapl"], "10-K")

        assert "AAPL" in results
        assert "aapl" not in results

    def test_batch_mixed_outcomes(self, pipeline, mock_downloader, raw_filing):
        call_count = 0

        def download_side_effect(ticker, filing_type, fiscal_year=None):
            nonlocal call_count
            call_count += 1
            if ticker == "INVALID":
                raise FilingNotFoundError(f"No filing for {ticker}")
            return raw_filing

        mock_downloader.download.side_effect = download_side_effect

        results = pipeline.process_batch(["AAPL", "MSFT", "INVALID"], "10-K")

        assert results["AAPL"].status == "success"
        assert results["MSFT"].status == "success"
        assert results["INVALID"].status == "error"
        assert results["INVALID"].error is not None


class TestBatchRetryTransientErrors:
    @patch("backend.ingestion.sec_filing_pipeline.pipeline.time.sleep")
    def test_retries_transient_error_up_to_3_times(
        self, mock_sleep, pipeline, mock_downloader
    ):
        mock_downloader.download.side_effect = TransientError("503 Service Unavailable")

        results = pipeline.process_batch(["AAPL"], "10-K")

        assert results["AAPL"].status == "error"
        assert mock_downloader.download.call_count == 3
        assert mock_sleep.call_count == 2

    @patch("backend.ingestion.sec_filing_pipeline.pipeline.time.sleep")
    def test_retry_succeeds_on_second_attempt(
        self, mock_sleep, pipeline, mock_downloader, raw_filing
    ):
        mock_downloader.download.side_effect = [
            TransientError("503"),
            raw_filing,
        ]

        results = pipeline.process_batch(["AAPL"], "10-K")

        assert results["AAPL"].status == "success"
        assert mock_downloader.download.call_count == 2
        assert mock_sleep.call_count == 1

    @patch("backend.ingestion.sec_filing_pipeline.pipeline.time.sleep")
    def test_exponential_backoff_delays(
        self, mock_sleep, pipeline, mock_downloader
    ):
        mock_downloader.download.side_effect = TransientError("503")

        pipeline.process_batch(["AAPL"], "10-K")

        delays = [call.args[0] for call in mock_sleep.call_args_list]
        assert delays == [1.0, 2.0]


class TestBatchPermanentErrors:
    def test_permanent_error_not_retried(self, pipeline, mock_downloader):
        mock_downloader.download.side_effect = FilingNotFoundError("Not found")

        results = pipeline.process_batch(["AAPL"], "10-K")

        assert results["AAPL"].status == "error"
        assert mock_downloader.download.call_count == 1


class TestJITModeRaisesExceptions:
    def test_transient_error_raised_in_jit_mode(self, pipeline, mock_downloader):
        mock_downloader.download.side_effect = TransientError("503")

        with pytest.raises(TransientError):
            pipeline.process("AAPL", "10-K", fiscal_year=2024)

    def test_permanent_error_raised_in_jit_mode(self, pipeline, mock_downloader):
        mock_downloader.download.side_effect = FilingNotFoundError("Not found")

        with pytest.raises(FilingNotFoundError):
            pipeline.process("AAPL", "10-K", fiscal_year=2024)


class TestBatchFromCacheFlag:
    def test_from_cache_true_when_cache_hit(
        self, pipeline, mock_store, parsed_filing
    ):
        mock_store.get.return_value = parsed_filing

        results = pipeline.process_batch(["AAPL"], "10-K")

        assert results["AAPL"].from_cache is True

    def test_from_cache_false_when_cache_miss(self, pipeline, mock_store):
        mock_store.get.return_value = None

        results = pipeline.process_batch(["AAPL"], "10-K")

        assert results["AAPL"].from_cache is False


class TestCreateClassMethod:
    @patch("backend.ingestion.sec_filing_pipeline.pipeline.SECDownloader")
    @patch("backend.ingestion.sec_filing_pipeline.pipeline.HTMLPreprocessor")
    @patch("backend.ingestion.sec_filing_pipeline.pipeline.HtmlToMarkdownAdapter")
    @patch("backend.ingestion.sec_filing_pipeline.pipeline.MarkdownifyAdapter")
    @patch("backend.ingestion.sec_filing_pipeline.pipeline.LocalFilingStore")
    def test_create_assembles_default_dependencies(
        self, mock_store_cls, mock_fallback_cls, mock_converter_cls,
        mock_preprocessor_cls, mock_downloader_cls
    ):
        pipeline = SECFilingPipeline.create()

        assert isinstance(pipeline, SECFilingPipeline)
        mock_downloader_cls.assert_called_once()
        mock_preprocessor_cls.assert_called_once()
        mock_converter_cls.assert_called_once()
        mock_fallback_cls.assert_called_once()
        mock_store_cls.assert_called_once()
