import pytest

from backend.ingestion.sec_filing_pipeline.filing_models import FilingType


@pytest.fixture()
def valid_metadata_kwargs():
    return {
        "ticker": "AAPL",
        "cik": "0000320193",
        "company_name": "Apple Inc.",
        "filing_type": FilingType.TEN_K,
        "filing_date": "2024-11-01",
        "fiscal_year": 2024,
        "accession_number": "0000320193-24-000123",
        "source_url": "https://www.sec.gov/Archives/edgar/data/320193/000032019324000123/aapl-20240928.htm",
        "parsed_at": "2026-04-03T10:30:00Z",
        "converter": "html-to-markdown",
    }
