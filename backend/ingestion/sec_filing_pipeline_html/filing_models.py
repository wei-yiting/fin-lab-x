from dataclasses import dataclass
from typing import Protocol

from pydantic import BaseModel

from backend.common.sec_core import FilingType, TransientError


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


class RetryCallback(Protocol):
    def __call__(
        self, attempt: int, max_attempts: int, error: TransientError
    ) -> None: ...
