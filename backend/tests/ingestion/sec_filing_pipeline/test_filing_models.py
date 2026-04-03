import pytest
from pydantic import ValidationError

from backend.ingestion.sec_filing_pipeline.filing_models import (
    FilingMetadata,
    FilingNotFoundError,
    FilingType,
    ParsedFiling,
    SECPipelineError,
    TickerNotFoundError,
    TransientError,
    UnsupportedFilingTypeError,
)


class TestFilingType:
    def test_ten_k_value(self):
        assert FilingType.TEN_K == "10-K"
        assert FilingType.TEN_K.value == "10-K"

    def test_is_str_subclass(self):
        assert isinstance(FilingType.TEN_K, str)


class TestFilingMetadata:
    def test_valid_metadata(self, valid_metadata_kwargs):
        metadata = FilingMetadata(**valid_metadata_kwargs)
        assert metadata.ticker == "AAPL"
        assert metadata.cik == "0000320193"
        assert metadata.company_name == "Apple Inc."
        assert metadata.filing_type == FilingType.TEN_K
        assert metadata.filing_date == "2024-11-01"
        assert metadata.fiscal_year == 2024
        assert metadata.accession_number == "0000320193-24-000123"
        assert metadata.converter == "html-to-markdown"

    def test_filing_type_from_string(self, valid_metadata_kwargs):
        valid_metadata_kwargs["filing_type"] = "10-K"
        metadata = FilingMetadata(**valid_metadata_kwargs)
        assert metadata.filing_type == FilingType.TEN_K

    def test_invalid_filing_type_rejected(self, valid_metadata_kwargs):
        valid_metadata_kwargs["filing_type"] = "10-Q"
        with pytest.raises(ValidationError):
            FilingMetadata(**valid_metadata_kwargs)

    @pytest.mark.parametrize("field", [
        "ticker",
        "cik",
        "company_name",
        "filing_type",
        "filing_date",
        "fiscal_year",
        "accession_number",
        "source_url",
        "parsed_at",
        "converter",
    ])
    def test_missing_required_field(self, valid_metadata_kwargs, field):
        del valid_metadata_kwargs[field]
        with pytest.raises(ValidationError):
            FilingMetadata(**valid_metadata_kwargs)

    def test_fiscal_year_must_be_int(self, valid_metadata_kwargs):
        valid_metadata_kwargs["fiscal_year"] = "not-a-number"
        with pytest.raises(ValidationError):
            FilingMetadata(**valid_metadata_kwargs)


class TestParsedFiling:
    def test_valid_parsed_filing(self, valid_metadata_kwargs):
        metadata = FilingMetadata(**valid_metadata_kwargs)
        filing = ParsedFiling(metadata=metadata, markdown_content="# Annual Report")
        assert filing.metadata.ticker == "AAPL"
        assert filing.markdown_content == "# Annual Report"

    def test_missing_markdown_content(self, valid_metadata_kwargs):
        metadata = FilingMetadata(**valid_metadata_kwargs)
        with pytest.raises(ValidationError):
            ParsedFiling(metadata=metadata)


class TestExceptionHierarchy:
    def test_all_exceptions_inherit_from_sec_pipeline_error(self):
        assert issubclass(TickerNotFoundError, SECPipelineError)
        assert issubclass(FilingNotFoundError, SECPipelineError)
        assert issubclass(UnsupportedFilingTypeError, SECPipelineError)
        assert issubclass(TransientError, SECPipelineError)

    def test_sec_pipeline_error_inherits_from_exception(self):
        assert issubclass(SECPipelineError, Exception)

    def test_exceptions_are_catchable_as_sec_pipeline_error(self):
        for exc_cls in [
            TickerNotFoundError,
            FilingNotFoundError,
            UnsupportedFilingTypeError,
            TransientError,
        ]:
            with pytest.raises(SECPipelineError):
                raise exc_cls("test")

    def test_exception_preserves_message(self):
        err = TickerNotFoundError("INVALID ticker not found")
        assert str(err) == "INVALID ticker not found"
