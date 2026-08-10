"""Shared fixtures for the SEC text pipeline tests.

``fixtures_aapl_fy2025.json`` is recorded from the real AAPL 10-K FY2025 via
edgartools (bodies truncated to 1,500 chars — plenty to classify, small
enough to commit). The fakes mirror the exact slice of the edgartools
surface that ``parse_filing`` consumes (``TenK.sections`` /
``Section.item`` / ``Section.text()``), wrapped in the real
:class:`FetchedFiling` bundle with recorded citation metadata. No test in
this package may hit EDGAR.
"""

import json
from dataclasses import dataclass
from pathlib import Path

import pytest

from backend.common.sec_core import FetchedFiling, FilingType
from backend.ingestion.sec_text_pipeline import parser
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


class FakeTenK:
    def __init__(
        self,
        sections_data: dict[str, dict[str, str]] | None = None,
        period_of_report: str = RECORDED_FILING["period_of_report"],
        filing_date: str = RECORDED_FILING["filing_date"],
    ) -> None:
        data = RECORDED_FILING["sections"] if sections_data is None else sections_data
        self.sections = {
            name: FakeSection(item=entry["item"] or None, _text=entry["text"])
            for name, entry in data.items()
        }
        self.period_of_report = period_of_report
        self.filing_date = filing_date


def make_bundle(tenk: FakeTenK) -> FetchedFiling:
    """Wrap a FakeTenK in the real FetchedFiling with recorded metadata."""
    return FetchedFiling(
        tenk=tenk,
        accession_number=RECORDED_FILING["accession_number"],
        cik=str(RECORDED_FILING["cik"]),
        company_name=RECORDED_FILING["company"],
        primary_document=RECORDED_FILING["primary_document"],
    )


def assert_tiles(prelude: str, blocks, source_text: str) -> None:
    """Assert prelude + blocks tile the source Item text with zero content loss.

    Every non-empty segment (prelude, then each block's heading and text, in
    order) must be found in ``source_text`` at or after the previous segment's
    end — no overlap, no reordering — and everything between and after the
    segments must be pure whitespace. Unlike a "segment appears somewhere"
    substring check, this catches a dropped segment even when an identical
    copy of its text exists elsewhere in the document.
    """
    segments: list[str] = []
    if prelude:
        segments.append(prelude)
    for block in blocks:
        if block.heading:
            segments.append(block.heading)
        if block.text:
            segments.append(block.text)

    pos = 0
    for n, segment in enumerate(segments):
        found = source_text.find(segment, pos)
        assert found != -1, (
            f"segment {n} not found at/after offset {pos}: {segment[:60]!r}"
        )
        gap = source_text[pos:found]
        assert gap.strip() == "", (
            f"non-whitespace content lost before segment {n}: {gap[:80]!r}"
        )
        pos = found + len(segment)
    tail = source_text[pos:]
    assert tail.strip() == "", f"non-whitespace tail lost: {tail[:80]!r}"


@pytest.fixture(autouse=True)
def _markdown_seam(monkeypatch):
    """Default the filing-markdown fetch seam to empty so no test can hit
    EDGAR through it; detection tests re-patch with fixture markdown."""
    monkeypatch.setattr(parser, "fetch_filing_markdown", lambda *a, **k: "")


@pytest.fixture
def fake_tenk() -> FakeTenK:
    """The recorded AAPL FY2025 filing, faked at the edgartools seam."""
    return FakeTenK()


@pytest.fixture
def fake_bundle(fake_tenk) -> FetchedFiling:
    """The recorded AAPL FY2025 filing as a FetchedFiling bundle."""
    return make_bundle(fake_tenk)


@pytest.fixture
def store(tmp_path) -> LocalFilingStore:
    return LocalFilingStore(base_dir=str(tmp_path))
