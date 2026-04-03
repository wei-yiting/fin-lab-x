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


@pytest.fixture()
def modern_filing_html():
    return (
        '<div style="display:none">'
        "<ix:header><ix:hidden>xbrl metadata</ix:hidden></ix:header>"
        "</div>"
        '<div style="font-family:Arial;font-size:10pt">'
        '<ix:nonNumeric contextRef="c-1">'
        '<div><span style="font-weight:700;font-size:10pt">Item 1. Business</span></div>'
        "<p>We design GPUs and accelerated computing platforms.</p>"
        "</ix:nonNumeric>"
        '<p>Revenue was <ix:nonFraction contextRef="c-2">47525000000</ix:nonFraction> for the fiscal year.</p>'
        "</div>"
    )


@pytest.fixture()
def older_filing_html():
    return (
        '<p><font style="font-family:Times New Roman" size="2">'
        "<b>Item 1. Business</b></font></p>"
        '<font style="font-family:Times New Roman" size="2">'
        "The Company designs, manufactures and markets mobile communication "
        "and media devices, personal computers, and portable digital music players."
        "</font>"
    )
