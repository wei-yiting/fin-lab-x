"""Recorded-filing fakes for Seam-1 tests.

The fakes mirror the exact slice of the edgartools surface that
``parse_filing`` consumes (``TenK.sections`` / ``Section.item`` /
``Section.text()`` / the underlying ``Filing`` metadata attributes), loaded
with item bodies condensed from real AAPL-shaped 10-K content. No test in
this package may hit EDGAR.
"""

from dataclasses import dataclass, field

import pytest

_SUBSTANTIVE_FILLER = (
    "Revenue increased year over year driven by demand across products and "
    "services. Gross margin expanded on favorable mix. Operating expenses "
    "reflected continued investment in research and development. "
) * 10


# Representative 10-K section bodies: substantive items, a v1 incorp stub
# (Item 11), a reserved item (Item 6), and a v2 pseudo-stub (Item 7A).
RECORDED_SECTIONS: dict[str, dict[str, str]] = {
    "part_i_item_1": {
        "item": "1",
        "text": (
            "Item 1. Business. The Company designs, manufactures and markets "
            "smartphones, personal computers, tablets, wearables and "
            "accessories, and sells a variety of related services. "
            + _SUBSTANTIVE_FILLER
        ),
    },
    "part_i_item_1a": {
        "item": "1A",
        "text": (
            "Item 1A. Risk Factors. The Company's business, reputation, "
            "results of operations and financial condition can be affected "
            "by a number of factors. " + _SUBSTANTIVE_FILLER
        ),
    },
    "part_ii_item_6": {
        "item": "6",
        "text": "Item 6. [Reserved]",
    },
    "part_ii_item_7": {
        "item": "7",
        "text": (
            "Item 7. Management's Discussion and Analysis of Financial "
            "Condition and Results of Operations. The following discussion "
            "should be read in conjunction with the consolidated financial "
            "statements. Reference is made to Note 12 for commitments. "
            + _SUBSTANTIVE_FILLER
        ),
    },
    "part_ii_item_7a": {
        "item": "7A",
        "text": (
            "Item 7A. Quantitative and Qualitative Disclosures About Market "
            "Risk. Refer to the Market Risk Management section on pages "
            "124-131 of the Annual Report."
        ),
    },
    "part_iii_item_11": {
        "item": "11",
        "text": (
            "Item 11. Executive Compensation. The information required by "
            "this Item is incorporated herein by reference from the Proxy "
            "Statement."
        ),
    },
    "part_iv_signatures": {
        "item": "",
        "text": "Signatures. Pursuant to the requirements of Section 13...",
    },
}


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
    cik: int = 320193
    company: str = "Apple Inc."
    accession_number: str = "0000320193-24-000123"
    document: FakeAttachment = field(
        default_factory=lambda: FakeAttachment(document="aapl-20240928.htm")
    )


class FakeTenK:
    def __init__(
        self,
        sections_data: dict[str, dict[str, str]] | None = None,
        period_of_report: str = "2024-09-28",
        filing_date: str = "2024-11-01",
        filing: FakeFiling | None = None,
    ) -> None:
        data = RECORDED_SECTIONS if sections_data is None else sections_data
        self.sections = {
            name: FakeSection(item=entry["item"] or None, _text=entry["text"])
            for name, entry in data.items()
        }
        self.period_of_report = period_of_report
        self.filing_date = filing_date
        self._filing = filing or FakeFiling()


@pytest.fixture
def fake_tenk() -> FakeTenK:
    return FakeTenK()
