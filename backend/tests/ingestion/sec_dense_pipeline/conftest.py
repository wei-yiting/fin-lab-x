"""Shared fixtures for the SEC dense pipeline (structured contract) tests.

Toy :class:`ParsedFiling` construction only — seam-2 tests feed hand-built
structures and assert Qdrant-observable state (or the pure chunk payloads),
never the parser. Block bodies use numbered synthetic tokens
(``alpha0 alpha1 ...``) so chunk-boundary and overlap assertions can match
exact text without false positives from repeated words.
"""

import pytest

from backend.common.sec_core import FilingType
from backend.ingestion.sec_text_pipeline.filing_models import (
    Block,
    FilingMetadata,
    FlatItem,
    ParsedFiling,
    StructuredItem,
)


@pytest.fixture(autouse=True)
def _unset_disable_jit(monkeypatch):
    """Neutralize CI's global ``SEC_DISABLE_JIT=1`` so tests exercise the
    JIT path by default. Tests that pin the disabled behavior re-set the
    flag themselves via ``monkeypatch.setenv``, which runs after this
    autouse fixture and therefore still wins."""
    monkeypatch.delenv("SEC_DISABLE_JIT", raising=False)


def numbered_text(prefix: str, count: int) -> str:
    """``count`` unique tokens sharing ``prefix`` — long bodies, no repeats."""
    return " ".join(f"{prefix}{i}" for i in range(count))


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
        parsed_at="2026-08-10T12:00:00+00:00",
    )
    defaults.update(overrides)
    return FilingMetadata(**defaults)


PRELUDE_TEXT = (
    "This section contains forward-looking statements within the meaning "
    "of the Private Securities Litigation Reform Act."
)


def make_toy_filing(**metadata_overrides) -> ParsedFiling:
    """One filing exercising every payload branch.

    - Item 7: StructuredItem with a valid prelude and two headed blocks,
      each long enough to split into several chunks.
    - Item 1A: StructuredItem with a reclassified heading-less leading
      block (schema ``prelude == ""``, ``blocks[0].heading == ""``).
    - Item 8: FlatItem.
    """
    return ParsedFiling(
        metadata=make_metadata(**metadata_overrides),
        items=[
            StructuredItem(
                item="7",
                title=(
                    "Management's Discussion and Analysis of Financial "
                    "Condition and Results of Operations"
                ),
                prelude=PRELUDE_TEXT,
                blocks=[
                    Block(
                        heading="Results of Operations",
                        text=numbered_text("alpha", 1400),
                    ),
                    Block(
                        heading="Liquidity and Capital Resources",
                        text=numbered_text("bravo", 1400),
                    ),
                ],
                detection_source="markdown_h3",
            ),
            StructuredItem(
                item="1a",
                title="Risk Factors",
                prelude="",
                blocks=[
                    Block(heading="", text=numbered_text("charlie", 900)),
                    Block(heading="Competition", text=numbered_text("delta", 300)),
                ],
                detection_source="markdown_h4",
            ),
            FlatItem(
                item="8",
                title="Financial Statements and Supplementary Data",
                text=numbered_text("echo", 900),
            ),
        ],
    )


@pytest.fixture()
def toy_filing() -> ParsedFiling:
    return make_toy_filing()
