"""parse_filing — fetch + parse orchestration for the SEC text pipeline.

Single public entry point; edgartools types never leak to callers.
Detection is currently degenerate — every non-stub Item is emitted as a
:class:`FlatItem`; the markdown H3/H4 detection chain is the planned next
step and upgrades qualifying Items to :class:`StructuredItem`.
"""

from __future__ import annotations

import re
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from backend.common.sec_core import (
    TENK_STANDARD_TITLES,
    FetchedFiling,
    FilingType,
    SECError,
    fetch_filing_bundle,
    trim_text_to_item_boundary,
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


class EmptyFilingError(SECError):
    """A filing parsed to zero substantive items.

    Raised instead of caching/returning an empty ParsedFiling: a silent
    empty ingestion would look like a successful parse to every downstream
    consumer, so the failure must be legible at the point it happens.
    """


def parse_filing(
    ticker: str,
    fiscal_year: int,
    force: bool = False,
    *,
    store: FilingStore | None = None,
) -> ParsedFiling:
    """Fetch and parse one 10-K into a :class:`ParsedFiling`.

    Filing-store cache first (unless ``force``), EDGAR via
    :func:`backend.common.sec_core.fetch_filing_bundle` on miss, and the
    parse result is persisted back to the store.

    ``force=True`` bypasses the on-disk filing store: parsing re-runs and
    the stored JSON is overwritten. It does NOT invalidate the in-process
    EDGAR fetch cache — a filing for a given (ticker, fiscal year) is
    immutable on SEC's side (amendments arrive as separate filings), so
    ``force`` means "re-parse the same fetched data", not "re-download".

    ``store`` is a keyword-only test/advanced seam; the default is
    :class:`LocalFilingStore`.

    Raises the :class:`backend.common.sec_core.SECError` family on fetch
    failures (ticker unknown, no 10-K, rate limit, ...), and
    :class:`EmptyFilingError` when the filing parses to zero substantive
    items (nothing is saved to the store in that case).
    """
    store = store if store is not None else LocalFilingStore()
    ticker_norm = ticker.strip().upper()

    if not force:
        cached = store.get(ticker_norm, FilingType.TEN_K, fiscal_year)
        if cached is not None:
            return cached

    bundle = fetch_filing_bundle(ticker_norm, FilingType.TEN_K, fiscal_year)
    metadata = _build_metadata(bundle, ticker_norm, fiscal_year)
    items = _parse_items(bundle.tenk)
    if not items:
        raise EmptyFilingError(
            f"Parsed 0 substantive items for {ticker_norm} FY{fiscal_year} "
            f"(accession {metadata.accession_number}); refusing to cache "
            f"an empty filing."
        )
    filing = ParsedFiling(metadata=metadata, items=items)
    store.save(filing)
    return filing


# Same shape as sec_core's shared boundary regex, but the lookbehind rejects
# only lowercase letters: uppercase glue before "Item" ("PART IIIItem 10.",
# "53PART IVItem 15.") is a heading artifact of the observed bleed, while a
# real word ending right before "item" (e.g. "subitem") is lowercase.
_ITEM_HEADING_RE = re.compile(r"(?<![a-z])(?i:item\s+(\d{1,2}[a-c]?)\s*\.(?!\d))")
# A cut at a glued heading can leave the previous page's "PART <roman>"
# label dangling at the tail — it belongs to the bled next Part, not to the
# current Item's body.
_TRAILING_PART_RE = re.compile(r"PART\s+[IVX]+$")


def _trim_section_text(text: str, current_item: str) -> str:
    """Isolate ``current_item``'s own body from a bleeding section text.

    edgartools sometimes returns a section body that runs past its own item
    into later items (observed on AAPL FY2025: Item 11 carries Items 12-15,
    Item 9C carries PART III onward). The shared
    :func:`backend.common.sec_core.trim_text_to_item_boundary` cuts at
    boundaries preceded by a non-letter ("...reference.Item 12.") but its
    lookbehind rejects the uppercase-glued forms above, so a second local
    pass with :data:`_ITEM_HEADING_RE` finishes the cut. The section's own
    leading heading is preserved.
    """
    trimmed = trim_text_to_item_boundary(text, current_item)
    target = current_item.lower()
    matches = list(_ITEM_HEADING_RE.finditer(trimmed))
    # The first match is the section's own header; scan from the second.
    for m in matches[1:]:
        if m.group(1).lower() != target:
            trimmed = trimmed[: m.start()]
            break
    return _TRAILING_PART_RE.sub("", trimmed.rstrip()).rstrip()


def _parse_items(tenk: TenK) -> list[ParsedItem]:
    """Emit one FlatItem per substantive 10-K item, in filing order.

    Each section body is trimmed to its own Item boundary before stub
    classification — a bled tail would otherwise both corrupt the emitted
    text and push a pure pointer stub (AAPL FY2025 Item 11) over the
    remaining-content threshold so it wrongly survives.

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
        text = _trim_section_text(text, key)
        is_stub, _reason = is_stub_section_v2(text)
        if is_stub:
            continue
        seen.add(key)
        items.append(FlatItem(item=key, title=TENK_STANDARD_TITLES[key], text=text))
    return items


def _build_metadata(
    bundle: FetchedFiling, ticker_norm: str, fiscal_year: int
) -> FilingMetadata:
    return FilingMetadata(
        ticker=ticker_norm,
        cik=bundle.cik,
        company_name=bundle.company_name,
        filing_type=FilingType.TEN_K,
        filing_date=str(bundle.tenk.filing_date),
        fiscal_year=fiscal_year,
        accession_number=bundle.accession_number,
        primary_document=bundle.primary_document,
        parsed_at=datetime.now(UTC).isoformat(),
    )
