from dataclasses import dataclass
from enum import StrEnum

from pydantic import BaseModel


class FilingType(StrEnum):
    TEN_K = "10-K"


@dataclass(frozen=True)
class RawFiling:
    raw_html: str
    ticker: str
    cik: str
    company_name: str
    filing_date: str
    fiscal_year: int
    accession_number: str
    source_url: str


class FilingMetadata(BaseModel):
    ticker: str
    cik: str
    company_name: str
    filing_type: FilingType
    filing_date: str
    fiscal_year: int
    accession_number: str
    source_url: str
    parsed_at: str
    converter: str


class ParsedFiling(BaseModel):
    metadata: FilingMetadata
    markdown_content: str


class SECPipelineError(Exception): ...


class TickerNotFoundError(SECPipelineError): ...


class FilingNotFoundError(SECPipelineError): ...


class UnsupportedFilingTypeError(SECPipelineError): ...


class TransientError(SECPipelineError): ...
