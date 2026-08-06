"""parse_filing — fetch + parse orchestration for the SEC text pipeline.

Single public entry point (DEV-127 spec): edgartools types never leak to
callers. Detection is currently degenerate — every non-stub Item is emitted
as a :class:`FlatItem`; the markdown H3/H4 detection chain lands in the
next ticket and upgrades qualifying Items to :class:`StructuredItem`.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from backend.common.sec_core import (
    TENK_STANDARD_TITLES,
    FilingType,
    fetch_filing_obj,
)
from backend.ingestion.sec_text_pipeline.filing_models import (
    FilingMetadata,
    FlatItem,
    ParsedFiling,
    ParsedItem,
)
from backend.ingestion.sec_text_pipeline.filing_store import (
    FilingStore,
    LocalFilingStore,
)
from backend.ingestion.sec_text_pipeline.stub_detection import is_stub_section_v2

if TYPE_CHECKING:
    from edgar.company_reports.ten_k import TenK


def parse_filing(
    ticker: str,
    fiscal_year: int | None = None,
    force: bool = False,
    store: FilingStore | None = None,
) -> ParsedFiling:
    """Fetch and parse one 10-K into a :class:`ParsedFiling`.

    Filing-store cache first (unless ``force``), EDGAR via
    :func:`fetch_filing_obj` on miss, and the parse result is persisted
    back to the store. ``fiscal_year=None`` resolves to the latest filing —
    that resolution needs EDGAR, so the cache can only be consulted after
    the fetch derives the year.

    Raises the :class:`backend.common.sec_core.SECError` family on fetch
    failures (ticker unknown, no 10-K, rate limit, ...).
    """
    store = store if store is not None else LocalFilingStore()
    ticker_norm = ticker.strip().upper()

    if fiscal_year is not None and not force:
        cached = store.get(ticker_norm, FilingType.TEN_K, fiscal_year)
        if cached is not None:
            return cached

    tenk = fetch_filing_obj(ticker_norm, FilingType.TEN_K, fiscal_year)
    derived_fy = int(str(tenk.period_of_report)[:4])

    if not force:
        cached = store.get(ticker_norm, FilingType.TEN_K, derived_fy)
        if cached is not None:
            return cached

    filing = ParsedFiling(
        metadata=_build_metadata(tenk, ticker_norm, derived_fy),
        items=_parse_items(tenk),
    )
    store.save(filing)
    return filing


def _parse_items(tenk: TenK) -> list[ParsedItem]:
    """Emit one FlatItem per substantive 10-K item, in filing order.

    Skips: entries that are not standard items (signatures, unknown keys),
    empty bodies, stub items (v2 classifier), and duplicate item keys
    (first occurrence wins).
    """
    items: list[ParsedItem] = []
    seen: set[str] = set()
    for section in tenk.sections.values():
        raw_item = getattr(section, "item", None)
        if not raw_item:
            continue
        key = raw_item.lower()
        if key not in TENK_STANDARD_TITLES or key in seen:
            continue
        text = section.text()
        if not text or not text.strip():
            continue
        is_stub, _reason = is_stub_section_v2(text)
        if is_stub:
            continue
        seen.add(key)
        items.append(FlatItem(item=key, title=TENK_STANDARD_TITLES[key], text=text))
    return items


def _build_metadata(tenk: TenK, ticker_norm: str, fiscal_year: int) -> FilingMetadata:
    # CompanyReport has no public accessor for its underlying Filing, and the
    # citation-chain fields (accession_number / cik / primary_document) only
    # live there — this is the sole, contained private access.
    filing = tenk._filing
    return FilingMetadata(
        ticker=ticker_norm,
        cik=str(filing.cik),
        company_name=filing.company,
        filing_type=FilingType.TEN_K,
        filing_date=str(tenk.filing_date),
        fiscal_year=fiscal_year,
        accession_number=filing.accession_number,
        primary_document=filing.document.document,
        parsed_at=datetime.now(UTC).isoformat(),
    )
