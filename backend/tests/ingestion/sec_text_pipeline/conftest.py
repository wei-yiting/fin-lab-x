"""Shared fixtures for the SEC text pipeline tests.

``fixtures_aapl_fy2025.json`` is recorded from the real AAPL 10-K FY2025 via
edgartools (bodies truncated to 1,500 chars — plenty to classify, small
enough to commit). The fakes mirror the exact slice of the edgartools
surface that ``parse_filing`` consumes (``TenK.sections`` /
``Section.item`` / ``Section.text()`` / the underlying ``Filing`` metadata
attributes). No test in this package may hit EDGAR.
"""

import json
from dataclasses import dataclass, field
from pathlib import Path

import pytest

from backend.common.sec_core import FilingType
from backend.ingestion.sec_text_pipeline.filing_models import (
    Block,
    FilingMetadata,
    StructuredItem,
)
from backend.ingestion.sec_text_pipeline.filing_store import LocalFilingStore

RECORDED_FILING = json.loads(
    (Path(__file__).parent / "fixtures_aapl_fy2025.json").read_text(encoding="utf-8")
)


def make_metadata(**overrides) -> FilingMetadata:
    defaults = dict(
        ticker="AAPL",
        cik="320193",
        company_name="Apple Inc.",
        filing_type=FilingType.TEN_K,
        filing_date="2024-11-01",
        fiscal_year=2024,
        accession_number="0000320193-24-000123",
        primary_document="aapl-20240928.htm",
        parsed_at="2026-08-06T12:00:00+00:00",
    )
    defaults.update(overrides)
    return FilingMetadata(**defaults)


def make_structured_item(**overrides) -> StructuredItem:
    defaults = dict(
        item="7",
        title="Management's Discussion and Analysis of Financial Condition and Results of Operations",
        prelude="The following discussion should be read in conjunction with...",
        blocks=[Block(heading="OVERVIEW", text="We are a global leader in...")],
        detection_source="markdown_h3",
    )
    defaults.update(overrides)
    return StructuredItem(**defaults)


@dataclass
class FakeSection:
    item: str | None
    _text: str

    def text(self) -> str:
        return self._text


@dataclass
class FakeAttachment:
    document: str


@dataclass
class FakeFiling:
    cik: int = int(RECORDED_FILING["cik"])
    company: str = RECORDED_FILING["company"]
    accession_number: str = RECORDED_FILING["accession_number"]
    document: FakeAttachment = field(
        default_factory=lambda: FakeAttachment(
            document=RECORDED_FILING["primary_document"]
        )
    )


class FakeTenK:
    def __init__(
        self,
        sections_data: dict[str, dict[str, str]] | None = None,
        period_of_report: str = RECORDED_FILING["period_of_report"],
        filing_date: str = RECORDED_FILING["filing_date"],
        filing: FakeFiling | None = None,
    ) -> None:
        data = RECORDED_FILING["sections"] if sections_data is None else sections_data
        self.sections = {
            name: FakeSection(item=entry["item"] or None, _text=entry["text"])
            for name, entry in data.items()
        }
        self.period_of_report = period_of_report
        self.filing_date = filing_date
        self._filing = filing or FakeFiling()


@pytest.fixture
def fake_tenk() -> FakeTenK:
    """The recorded AAPL FY2025 filing, faked at the edgartools seam."""
    return FakeTenK()


@pytest.fixture
def store(tmp_path) -> LocalFilingStore:
    return LocalFilingStore(base_dir=str(tmp_path))
