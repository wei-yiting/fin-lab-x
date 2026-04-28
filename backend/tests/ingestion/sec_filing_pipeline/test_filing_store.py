from __future__ import annotations

import pytest

from backend.common.sec_core import FilingType
from backend.ingestion.sec_filing_pipeline.filing_models import (
    FilingMetadata,
    ParsedFiling,
)
from backend.ingestion.sec_filing_pipeline.filing_store import (
    FilingStore,
    LocalFilingStore,
)


@pytest.fixture()
def store(tmp_path) -> LocalFilingStore:
    return LocalFilingStore(base_dir=str(tmp_path))


@pytest.fixture()
def sample_filing(valid_metadata_kwargs) -> ParsedFiling:
    return ParsedFiling(
        metadata=FilingMetadata(**valid_metadata_kwargs),
        markdown_content="# Annual Report\n\nSome content here.",
    )


class TestLocalFilingStoreProtocol:
    def test_implements_filing_store_protocol(self, store):
        assert isinstance(store, FilingStore)


class TestSaveExistsGetRoundtrip:
    """S-store-01: save/exists/get/list_filings consistency."""

    def test_save_then_exists_returns_true(self, store, sample_filing):
        store.save(sample_filing)
        assert store.exists("AAPL", FilingType.TEN_K, 2024) is True

    def test_exists_returns_false_for_nonexistent(self, store):
        assert store.exists("AAPL", FilingType.TEN_K, 2024) is False

    def test_get_returns_none_for_nonexistent(self, store):
        assert store.get("AAPL", FilingType.TEN_K, 2024) is None

    def test_save_then_get_returns_equivalent_filing(self, store, sample_filing):
        store.save(sample_filing)
        result = store.get("AAPL", FilingType.TEN_K, 2024)
        assert result is not None
        assert result.metadata.ticker == sample_filing.metadata.ticker
        assert result.metadata.cik == sample_filing.metadata.cik
        assert result.metadata.company_name == sample_filing.metadata.company_name
        assert result.metadata.filing_type == sample_filing.metadata.filing_type
        assert result.metadata.filing_date == sample_filing.metadata.filing_date
        assert result.metadata.fiscal_year == sample_filing.metadata.fiscal_year
        assert (
            result.metadata.accession_number == sample_filing.metadata.accession_number
        )
        assert result.metadata.source_url == sample_filing.metadata.source_url
        assert result.metadata.parsed_at == sample_filing.metadata.parsed_at
        assert result.metadata.converter == sample_filing.metadata.converter
        assert result.markdown_content == sample_filing.markdown_content

    def test_list_filings_returns_saved_years(self, store, valid_metadata_kwargs):
        for year in [2022, 2024, 2023]:
            kwargs = {**valid_metadata_kwargs, "fiscal_year": year}
            filing = ParsedFiling(
                metadata=FilingMetadata(**kwargs),
                markdown_content=f"# Report {year}",
            )
            store.save(filing)

        years = store.list_filings("AAPL", FilingType.TEN_K)
        assert years == [2022, 2023, 2024]

    def test_list_filings_returns_empty_for_nonexistent_ticker(self, store):
        assert store.list_filings("AAPL", FilingType.TEN_K) == []


class TestAutoCreateDirectory:
    """S-store-02: first save auto-creates directory."""

    def test_save_creates_nested_directories(self, store, sample_filing, tmp_path):
        target_dir = tmp_path / "AAPL" / "10-K"
        assert not target_dir.exists()

        store.save(sample_filing)
        assert target_dir.exists()
        assert (target_dir / "2024.md").exists()


class TestListFilingsFiltering:
    """S-store-03: list_filings filters non-filing files."""

    def test_filters_ds_store_and_tmp_files(self, store, sample_filing, tmp_path):
        store.save(sample_filing)

        filing_dir = tmp_path / "AAPL" / "10-K"
        (filing_dir / ".DS_Store").touch()
        (filing_dir / ".filing_abc.tmp").touch()
        (filing_dir / "notes.txt").touch()
        (filing_dir / "readme.md").touch()

        years = store.list_filings("AAPL", FilingType.TEN_K)
        assert years == [2024]


class TestSpecialCharacterRoundtrip:
    """S-store-04: special characters YAML roundtrip."""

    @pytest.mark.parametrize(
        "company_name",
        [
            "Moody's Corporation",
            "AT&T Inc.",
            "T. Rowe Price Group",
            'Company "Quoted" Name',
        ],
    )
    def test_special_chars_in_company_name(
        self, store, valid_metadata_kwargs, company_name
    ):
        kwargs = {**valid_metadata_kwargs, "company_name": company_name}
        filing = ParsedFiling(
            metadata=FilingMetadata(**kwargs),
            markdown_content="# Content",
        )
        store.save(filing)

        result = store.get("AAPL", FilingType.TEN_K, 2024)
        assert result is not None
        assert result.metadata.company_name == company_name


class TestMetadataFieldTypes:
    """S-store-05: all metadata fields have correct types after roundtrip."""

    def test_field_types_preserved(self, store, sample_filing):
        store.save(sample_filing)
        result = store.get("AAPL", FilingType.TEN_K, 2024)
        assert result is not None

        m = result.metadata
        assert isinstance(m.ticker, str)
        assert isinstance(m.cik, str)
        assert isinstance(m.company_name, str)
        assert isinstance(m.filing_type, FilingType)
        assert m.filing_type == FilingType.TEN_K
        assert isinstance(m.filing_date, str)
        assert isinstance(m.fiscal_year, int)
        assert isinstance(m.accession_number, str)
        assert isinstance(m.source_url, str)
        assert isinstance(m.parsed_at, str)
        assert isinstance(m.converter, str)


class TestTickerNormalization:
    """S-dl-06: ticker normalized to uppercase in store layer."""

    def test_lowercase_ticker_normalized_on_save(self, store, valid_metadata_kwargs):
        kwargs = {**valid_metadata_kwargs, "ticker": "aapl"}
        filing = ParsedFiling(
            metadata=FilingMetadata(**kwargs),
            markdown_content="# Content",
        )
        store.save(filing)

        assert store.exists("AAPL", FilingType.TEN_K, 2024) is True
        result = store.get("AAPL", FilingType.TEN_K, 2024)
        assert result is not None
        assert result.metadata.ticker == "AAPL"

    def test_mixed_case_ticker_normalized_on_save(self, store, valid_metadata_kwargs):
        kwargs = {**valid_metadata_kwargs, "ticker": "Aapl"}
        filing = ParsedFiling(
            metadata=FilingMetadata(**kwargs),
            markdown_content="# Content",
        )
        store.save(filing)

        assert store.exists("aapl", FilingType.TEN_K, 2024) is True


class TestTickerValidation:
    """Reject tickers with path traversal or invalid characters."""

    @pytest.mark.parametrize(
        "bad_ticker",
        [
            "../../etc",
            "foo/bar",
            "A\\B",
            "../passwd",
            "AAPL/../../etc",
            "",
            "  ",
            "AAPL MSFT",
        ],
    )
    def test_rejects_invalid_ticker_on_exists(self, store, bad_ticker):
        with pytest.raises(ValueError, match="Invalid ticker"):
            store.exists(bad_ticker, FilingType.TEN_K, 2024)

    @pytest.mark.parametrize(
        "bad_ticker",
        [
            "../../etc",
            "foo/bar",
            "A\\B",
        ],
    )
    def test_rejects_invalid_ticker_on_get(self, store, bad_ticker):
        with pytest.raises(ValueError, match="Invalid ticker"):
            store.get(bad_ticker, FilingType.TEN_K, 2024)

    @pytest.mark.parametrize(
        "bad_ticker",
        [
            "../../etc",
            "foo/bar",
            "A\\B",
        ],
    )
    def test_rejects_invalid_ticker_on_list_filings(self, store, bad_ticker):
        with pytest.raises(ValueError, match="Invalid ticker"):
            store.list_filings(bad_ticker, FilingType.TEN_K)

    @pytest.mark.parametrize(
        "valid_ticker",
        ["AAPL", "BRK.B", "BF-B", "X", "A123"],
    )
    def test_accepts_valid_tickers(self, store, valid_ticker):
        assert store.exists(valid_ticker, FilingType.TEN_K, 2024) is False


class TestAtomicWrite:
    """S-dl-07: atomic write prevents corruption."""

    def test_file_written_atomically(self, store, sample_filing, tmp_path):
        store.save(sample_filing)

        filing_dir = tmp_path / "AAPL" / "10-K"
        tmp_files = list(filing_dir.glob("*.tmp"))
        assert tmp_files == [], "No .tmp files should remain after save"

        result = store.get("AAPL", FilingType.TEN_K, 2024)
        assert result is not None
