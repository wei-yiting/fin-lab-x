"""parse_filing — fetch + parse orchestration for the SEC text pipeline.

Single public entry point; edgartools types never leak to callers.
Non-stub Items run through the block detection chain
(:mod:`block_detection`: markdown H3, H4, then the Title-Case text
fallback): a plausibly-anchored Item becomes a :class:`StructuredItem`
(prelude + blocks + detection_source), everything else stays a
:class:`FlatItem`.

Degraded ingest (DEV-172): when upstream section detection ran a fallback
strategy (filing-level detection method outside {toc, heading}), the
section structure is not trusted — the filing ingests as the noise-cleaned
full-document markdown (:mod:`degraded`) with ``items=[]`` and the
detection method recorded in metadata.
"""

from __future__ import annotations

import re
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from backend.common.retry import retry_transient
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
from backend.ingestion.sec_text_pipeline.degraded import clean_degraded_markdown
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
    from edgar.documents.document import Section


class EmptyFilingError(SECError):
    """The degraded path produced no text at all — even the full-document
    markdown came out empty after noise cleaning.

    Every zero-item parse falls through to degraded ingest first, so this
    is the single truly-empty case left. Raised instead of caching/returning
    an empty ParsedFiling: a silent empty ingestion would look like a
    successful parse to every downstream consumer, so the failure must be
    legible at the point it happens.
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
    :class:`EmptyFilingError` when even the degraded path's full-document
    text comes out empty (nothing is saved to the store in that case).
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

    if _is_degraded_method(metadata.section_detection_method):
        return _ingest_degraded(metadata, markdown, store)

    candidates = collect_heading_candidates(markdown, bundle.company_name)
    items = _parse_items(bundle.tenk, candidates)
    if not items:
        # Zero substantive items under a nominally trusted structure means
        # the structure was not trustworthy after all — same remedy as a
        # fallback detection: ingest the full document.
        return _ingest_degraded(metadata, markdown, store)
    filing = ParsedFiling(metadata=metadata, items=items)
    store.save(filing)
    return filing


@retry_transient
def parse_filing_with_retry(
    ticker: str, fiscal_year: int, force: bool = False
) -> ParsedFiling:
    """:func:`parse_filing` with a single retry on ``TransientError``.

    The EDGAR fetch inside ``parse_filing`` is the one genuinely retryable
    step of the pipeline's cold path (design-envelope §2 single-retry
    policy, applied via the shared ``retry_transient`` decorator, ADR-0013).
    Wraps the sync ``parse_filing`` directly; async callers run this via
    ``asyncio.to_thread``.
    """
    return parse_filing(ticker, fiscal_year, force)


#: Upstream detection strategies whose section structure the item parser
#: trusts. Anything else ("pattern", "html_fallback", "unknown", future
#: values) is a degraded detection: its sections carry semantic names with
#: empty item metadata and cover only a fraction of the filing.
_STANDARD_DETECTION_METHODS = frozenset({"toc", "heading"})


def _filing_detection_method(tenk: TenK) -> str:
    """The filing-level section detection method, passed through upstream.

    Upstream runs a single strategy per filing, so one unique value is the
    norm; a mixed filing (contract broken upstream) reports every method
    in first-seen order, comma-joined, and reads as degraded. No sections
    at all is "unknown".
    """
    methods: list[str] = []
    for section in tenk.sections.values():
        method = getattr(section, "detection_method", None) or "unknown"
        if method not in methods:
            methods.append(method)
    if not methods:
        return "unknown"
    return ",".join(methods)


def _is_degraded_method(method: str) -> bool:
    return not all(m in _STANDARD_DETECTION_METHODS for m in method.split(","))


def _ingest_degraded(
    metadata: FilingMetadata, markdown: str, store: FilingStore
) -> ParsedFiling:
    """Ingest the noise-cleaned full-document markdown as a degraded filing."""
    text = clean_degraded_markdown(markdown)
    if not text:
        raise EmptyFilingError(
            f"Degraded ingest for {metadata.ticker} FY{metadata.fiscal_year} "
            f"(accession {metadata.accession_number}, section detection "
            f"method {metadata.section_detection_method!r}) produced no text "
            f"after noise cleaning; refusing to cache an empty filing."
        )
    filing = ParsedFiling(metadata=metadata, items=[], degraded_text=text)
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

# edgartools names sections two ways: part-aware ("part_ii_item_7a", with
# Section.item populated) and spaced ("Item 7A", with Section.item None —
# its parse_section_name only understands the underscore shape; upstream
# inconsistency recorded on DEV-147). This matches the spaced shape so the
# item key can be derived when the metadata is missing.
_SECTION_NAME_ITEM_RE = re.compile(r"^item\s+(\d{1,2}[a-c]?)$", re.IGNORECASE)


def _section_item_key(section: object) -> str | None:
    """The section's item identifier, tolerant of both edgartools shapes.

    Prefers the ``item`` attribute; when the library left it unset, derives
    it from the section name. Returns None for non-item sections.
    """
    raw_item = getattr(section, "item", None)
    if raw_item:
        return str(raw_item)
    name = getattr(section, "name", None) or ""
    match = _SECTION_NAME_ITEM_RE.match(name.strip())
    return match.group(1) if match else None


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


def _build_item(key: str, text: str, candidates: HeadingCandidates) -> ParsedItem:
    """One item from an already-trimmed, non-stub body: structured when the
    detection chain (markdown H3/H4, then the Title-Case text fallback) finds
    a plausibly-anchored structure, flat otherwise."""
    title = TENK_STANDARD_TITLES[key]
    detected = detect_blocks(text, candidates)
    if detected is None:
        return FlatItem(item=key, title=title, text=text)
    return StructuredItem(
        item=key,
        title=title,
        prelude=detected.prelude,
        blocks=detected.blocks,
        detection_source=detected.detection_source,
    )


def _parse_items(tenk: TenK, candidates: HeadingCandidates) -> list[ParsedItem]:
    """Emit one parsed item per substantive 10-K item, in canonical Item order.

    edgartools iterates its ``Sections`` dict in the order its own detection
    happened to populate it, which is neither canonical nor the filing's
    document order (``Section.start_offset`` is 0 throughout under the ``toc``
    method, so document order is not observable here). The order is therefore
    taken from ``TENK_STANDARD_TITLES``: the registry is walked and each key's
    sections looked up. ``sec_filing_tools`` walks the registry the same way;
    only the walk is shared — the dedup rule below is this module's own.

    Each section body is trimmed to its own Item boundary before stub
    classification — a bled tail would otherwise both corrupt the emitted
    text and push a pure pointer stub (AAPL FY2025 Item 11) over the
    remaining-content threshold so it wrongly survives.

    Surviving bodies run through the block detection chain (markdown H3/H4,
    then the Title-Case text fallback): a plausibly-anchored Item is
    emitted as a StructuredItem, the rest as FlatItems.

    Skips: entries that are not standard items (signatures, unknown keys),
    empty bodies, stub items (v2 classifier), and duplicate item keys
    (first surviving occurrence wins — a stub first occurrence yields to a
    substantive later one).
    """
    sections_by_key: dict[str, list[Section]] = {}
    for section in tenk.sections.values():
        raw_item = _section_item_key(section)
        if not raw_item:
            continue
        key = raw_item.lower()
        if key not in TENK_STANDARD_TITLES:
            continue
        sections_by_key.setdefault(key, []).append(section)

    items: list[ParsedItem] = []
    for key in TENK_STANDARD_TITLES:
        for section in sections_by_key.get(key, []):
            text = section.text()
            if not text or not text.strip():
                continue
            text = _trim_section_text(text, key)
            is_stub, _reason = is_stub_section_v2(text)
            if is_stub:
                continue
            items.append(_build_item(key, text, candidates))
            break
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
        section_detection_method=_filing_detection_method(bundle.tenk),
    )
