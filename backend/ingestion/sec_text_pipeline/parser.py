"""parse_filing — fetch + parse orchestration for the SEC text pipeline.

Single public entry point; edgartools types never leak to callers.
Non-stub Items run through the markdown H3/H4 detection chain
(:mod:`block_detection`): a plausibly-anchored Item becomes a
:class:`StructuredItem` (prelude + blocks + detection_source), everything
else stays a :class:`FlatItem`. The Title-Case text fallback path is the
planned next step and will pick up Items the markdown path rejects.
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
    fetch_filing_markdown,
)
from backend.ingestion.sec_text_pipeline.block_detection import (
    HeadingCandidates,
    collect_heading_candidates,
    detect_blocks,
)
from backend.ingestion.sec_text_pipeline.filing_models import (
    FilingMetadata,
    FlatItem,
    ParsedFiling,
    ParsedItem,
    StructuredItem,
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

    Raises the :class:`backend.common.errors.FinLabError` taxonomy on fetch
    failures — shared errors directly (``TickerNotFoundError``,
    ``RateLimitError``, ``TransientError``, ``ConfigurationError``) and
    SEC-specific ones via :class:`backend.common.sec_core.SECError`
    (``FilingNotFoundError``, ``UnsupportedFilingTypeError``) — plus
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
    markdown = fetch_filing_markdown(ticker_norm, FilingType.TEN_K, fiscal_year)
    candidates = collect_heading_candidates(markdown, bundle.company_name)
    items = _parse_items(bundle.tenk, candidates)
    if not items:
        raise EmptyFilingError(
            f"Parsed 0 substantive items for {ticker_norm} FY{fiscal_year} "
            f"(accession {metadata.accession_number}); refusing to cache "
            f"an empty filing."
        )
    filing = ParsedFiling(metadata=metadata, items=items)
    store.save(filing)
    return filing


# A candidate item heading: "Item" or ALL-CAPS "ITEM" (both appear as real
# heading forms in section text — e.g. ADSK renders "ITEM 1A. RISK FACTORS"),
# 1-2 digit number with optional sub-letter, then a period (not the start of
# a decimal like "5.4"). Lowercase "item" stays excluded: it only occurs in
# prose. Whether a candidate is a *structural* boundary depends on what
# precedes it — see _is_structural_boundary.
_ITEM_HEADING_RE = re.compile(r"(?:Item|ITEM)\s+(\d{1,2}[a-cA-C]?)\s*\.(?!\d)")
# A cut at a glued heading can leave the previous page's "PART <roman>"
# label dangling at the tail — it belongs to the bled next Part, not to the
# current Item's body.
_TRAILING_PART_RE = re.compile(r"PART\s+[IVX]+$")


def _is_structural_boundary(text: str, start: int) -> bool:
    """True when the ``Item N.`` match at ``start`` is a section heading
    rather than an inline cross-reference.

    Structural forms are: start of string; start of a line (a newline,
    optionally followed by horizontal whitespace); or glued directly onto
    non-letter text ("reference.Item 12.", "53PART IVItem 15.") or a
    "PART <roman>" label ("PART IIIItem 10."). The discriminator:
    legitimate inline cross-references ("...under Item 1A. Risk
    Factors...") always have a plain space before "Item", while glued
    bleed and line-start headings never do. A preceding letter that is
    NOT part of a "PART <roman>" label means the match sits inside a
    larger word ("SubItem 1.", "LineItem 1A.") — prose, not a heading.
    A preceding quote or opening bracket is a quoted/parenthesized
    cross-reference ('See "Item 1. Business" above', observed on WMT
    FY2025 Item 1A) — prose as well.
    """
    if start == 0:
        return True
    prev = text[start - 1]
    if not prev.isspace():
        if prev in "\"'“”‘’([":
            return False
        if prev.isalpha():
            return bool(_TRAILING_PART_RE.search(text[:start]))
        return True
    j = start
    while j > 0 and text[j - 1] in " \t":
        j -= 1
    return j == 0 or text[j - 1] == "\n"


def _trim_section_text(text: str, current_item: str) -> str:
    """Isolate ``current_item``'s own body from a bleeding section text.

    edgartools sometimes returns a section body that runs past its own item
    into later items (observed on AAPL FY2025: Item 11 carries Items 12-15,
    Item 9C carries PART III onward). Cuts at the FIRST *structural*
    foreign-item boundary (see :func:`_is_structural_boundary`); inline
    cross-references like "See Item 1A. Risk Factors" are prose, not
    boundaries, and must survive. Boundaries naming ``current_item`` itself
    (the section's own heading, self-references) are skipped.
    """
    target = current_item.lower()
    trimmed = text
    for m in _ITEM_HEADING_RE.finditer(text):
        if m.group(1).lower() == target:
            continue
        if _is_structural_boundary(text, m.start()):
            trimmed = text[: m.start()]
            break
    return _TRAILING_PART_RE.sub("", trimmed.rstrip()).rstrip()


def _parse_items(tenk: TenK, candidates: HeadingCandidates) -> list[ParsedItem]:
    """Emit one parsed item per substantive 10-K item, in filing order.

    Each section body is trimmed to its own Item boundary before stub
    classification — a bled tail would otherwise both corrupt the emitted
    text and push a pure pointer stub (AAPL FY2025 Item 11) over the
    remaining-content threshold so it wrongly survives.

    Surviving bodies run through the markdown H3/H4 detection chain: a
    plausibly-anchored Item is emitted as a StructuredItem, the rest as
    FlatItems.

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
        title = TENK_STANDARD_TITLES[key]
        detected = detect_blocks(text, candidates)
        if detected is not None:
            items.append(
                StructuredItem(
                    item=key,
                    title=title,
                    prelude=detected.prelude,
                    blocks=detected.blocks,
                    detection_source=detected.detection_source,
                )
            )
        else:
            items.append(FlatItem(item=key, title=title, text=text))
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
