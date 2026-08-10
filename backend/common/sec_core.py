"""SEC filing domain core — types and helpers shared across subsystems.

Types: :class:`FilingType`, :class:`SECError` hierarchy,
``TENK_STANDARD_TITLES`` (SEC 17 CFR 229 canonical item map).
Helpers: :func:`parse_item_number` (agent-facing key normalization),
:func:`is_stub_section` (incorp-by-reference / reserved detection),
:func:`fetch_filing_obj` (LRU-cached ``edgartools.TenK`` fetch),
:func:`fetch_filing_bundle` (same fetch plus citation metadata),
:func:`fetch_filing_markdown` (filing-level markdown for block detection).

Shared by :mod:`backend.agent_engine.tools.sec_filing_tools` and
:mod:`backend.ingestion.sec_filing_pipeline_html`. Do not add agent-layer or
pipeline-layer concerns here — keep this module a thin, stateless core.
"""

import os
import re
import threading
from concurrent.futures import Future
from dataclasses import dataclass
from enum import StrEnum
from functools import lru_cache
from typing import TYPE_CHECKING

from backend.common.errors import (
    ConfigurationError,
    FinLabError,
    RateLimitError,
    TickerNotFoundError,
    TransientError,
)

if TYPE_CHECKING:
    from edgar.company_reports.ten_k import TenK  # noqa: F401


class FilingType(StrEnum):
    TEN_K = "10-K"
    # TEN_Q = "10-Q"  # reserved for future PR


class SECError(FinLabError):
    """SEC domain base exception."""


class FilingNotFoundError(SECError): ...


class UnsupportedFilingTypeError(SECError): ...


class SectionNotFoundError(SECError): ...


TENK_STANDARD_TITLES: dict[str, str] = {
    "1": "Business",
    "1a": "Risk Factors",
    "1b": "Unresolved Staff Comments",
    "1c": "Cybersecurity",
    "2": "Properties",
    "3": "Legal Proceedings",
    "4": "Mine Safety Disclosures",
    "5": "Market for Registrant's Common Equity, Related Stockholder Matters and Issuer Purchases of Equity Securities",
    "6": "[Reserved]",
    "7": "Management's Discussion and Analysis of Financial Condition and Results of Operations",
    "7a": "Quantitative and Qualitative Disclosures About Market Risk",
    "8": "Financial Statements and Supplementary Data",
    "9": "Changes in and Disagreements With Accountants on Accounting and Financial Disclosure",
    "9a": "Controls and Procedures",
    "9b": "Other Information",
    "9c": "Disclosure Regarding Foreign Jurisdictions that Prevent Inspections",
    "10": "Directors, Executive Officers and Corporate Governance",
    "11": "Executive Compensation",
    "12": "Security Ownership of Certain Beneficial Owners and Management and Related Stockholder Matters",
    "13": "Certain Relationships and Related Transactions, and Director Independence",
    "14": "Principal Accountant Fees and Services",
    "15": "Exhibits, Financial Statement Schedules",
    "16": "Form 10-K Summary",
}


_ITEM_PREFIX_RE = re.compile(r"^\s*item\s+", re.IGNORECASE)
_NORMALIZED_ITEM_RE = re.compile(r"^[0-9]{1,2}[a-c]?$")


def parse_item_number(section_key: str) -> str:
    raw = section_key if isinstance(section_key, str) else ""
    candidate = _ITEM_PREFIX_RE.sub("", raw.strip()).rstrip(".").strip()
    candidate = candidate.lower()
    if (
        not _NORMALIZED_ITEM_RE.match(candidate)
        or candidate not in TENK_STANDARD_TITLES
    ):
        raise SectionNotFoundError(
            f"Section key {section_key!r} is not a valid 10-K item number. "
            "Call sec_filing_list_sections first to see available section keys."
        )
    return candidate


_ITEM_BOUNDARY_RE = re.compile(r"(?i)(?<![A-Za-z])item\s+(\d{1,2}[a-c]?)\s*\.(?!\d)")


def trim_text_to_item_boundary(text: str, current_item: str) -> str:
    """Cut ``text`` at the first ``Item N.`` heading whose number differs
    from ``current_item`` (normalized item key, e.g. ``"11"``, ``"9c"``).

    Works around edgartools occasionally returning a section body that
    runs past its own item header into the next item(s) — observed for
    AAPL FY2025 Item 11 (bleeds 12/13/14) and Item 9C. The section's
    own leading heading is preserved; returns input unchanged when no
    second boundary is found.
    """
    matches = list(_ITEM_BOUNDARY_RE.finditer(text))
    if not matches:
        return text
    target = current_item.lower()
    # The first match is the section's own header; scan from the second.
    for m in matches[1:]:
        next_item = m.group(1).lower()
        if next_item != target:
            return text[: m.start()].rstrip()
    return text


_STUB_INCORP_RE = re.compile(
    r"incorporated\s+(?:\w+\s+)?(?:in|into|to|by)\s+(?:\w+\s+)?reference",
    re.IGNORECASE,
)
_STUB_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+(?=\S)")
_STUB_MARKDOWN_LINK_RE = re.compile(r"!?\[[^\]]*\]\([^)]*\)")
# Empirical calibration: real incorp-by-reference stubs (e.g. AAPL Item 11) leave
# <100 chars of residual prose after dropping the pointer sentence and markdown
# links. Above this threshold the item usually contains substantive commentary
# alongside the pointer, so we decline to classify it as a stub.
_STUB_REMAINING_THRESHOLD = 100
_RESERVED_RE = re.compile(r"\[\s*reserved\s*\]", re.IGNORECASE)


def classify_stub_section(
    text: str,
    extra_pointer_patterns: tuple[re.Pattern[str], ...] = (),
) -> tuple[bool, str | None]:
    """Classify an SEC 10-K item body as stub vs real, with a pluggable
    pointer-pattern set.

    Pointer-stub detection is a two-step mechanism, deliberately NOT a
    "phrase present => stub" check: (1) any pointer pattern anywhere in the
    body gates the check on; (2) sentences matching a pointer pattern are
    removed and the *remaining* content is measured — only a body that is
    essentially nothing but pointer sentences classifies as a stub. This
    keeps a 60k-char MD&A that merely says "Reference is made to Note 12"
    alive.

    ``extra_pointer_patterns`` extends the built-in incorporated-by-reference
    pattern (used by both steps). With no extras this function is exactly
    :func:`is_stub_section` — callers needing the frozen v1 behavior keep
    calling that; new callers (``sec_text_pipeline``) pass their own
    pseudo-stub patterns.
    """
    if not text or not text.strip():
        return (False, None)

    # Reserved/deprecated check wins classification — must precede incorp
    # check so "Item 6. [Reserved]" doesn't get classified as "incorporated".
    compact = re.sub(r"\s+", " ", text).strip()
    # Real reserved items are terse ("Item 6. [Reserved]" is 17 chars). 80 is an
    # intentionally generous upper bound so minor whitespace/punctuation variants
    # still match; anything longer is likely a section that happens to contain
    # the word "Reserved" in prose rather than an actual reserved sentinel.
    if len(compact) < 80 and _RESERVED_RE.search(compact):
        return (True, "section marked as reserved/deprecated")

    pointer_patterns = (_STUB_INCORP_RE, *extra_pointer_patterns)
    if not any(p.search(text) for p in pointer_patterns):
        return (False, None)

    sentences = _STUB_SENTENCE_SPLIT_RE.split(text)
    kept = [s for s in sentences if not any(p.search(s) for p in pointer_patterns)]
    remaining = " ".join(kept)
    remaining = _STUB_MARKDOWN_LINK_RE.sub("", remaining)
    cleaned = re.sub(r"[\s\-\|\*]+", "", remaining)
    if len(cleaned) < _STUB_REMAINING_THRESHOLD:
        if _STUB_INCORP_RE.search(text):
            return (True, "incorporated by reference from proxy statement")
        return (True, "cross-reference pointer stub")
    return (False, None)


def is_stub_section(text: str) -> tuple[bool, str | None]:
    """Classify an SEC 10-K item body as stub vs real.

    Stub types we care about:
    - Incorporated-by-reference stubs (body is essentially a pointer to the
      proxy statement or another filing). Reason: "incorporated by reference
      from proxy statement".
    - Reserved/deprecated items (Item 6 since 2021). The reserved check
      matches only the bracketed ``[Reserved]`` sentinel — that is the
      documented SEC convention and the deliberate contract here. Bare
      "Reserved" without brackets is not treated as a stub.
      Reason: "section marked as reserved/deprecated".

    Non-stub returns ``(False, None)``. Empty / whitespace-only input is
    treated as non-stub to keep upstream code defensively simple.

    Frozen v1 API: referenced by ``sec_filing_tools`` and the ``_html``
    A/B baseline, so its behavior must not drift while the two parse paths
    coexist. Delegates to :func:`classify_stub_section` with no extras,
    which is the bit-identical parameterization.
    """
    return classify_stub_section(text)


def _find_by_fiscal_year(filings, fiscal_year: int):
    """Iterate edgartools Filings and return the filing whose
    period_of_report year matches ``fiscal_year``, else None.
    Does NOT raise — caller decides.
    """
    for filing in filings:
        pr = getattr(filing, "period_of_report", None)
        if pr and str(pr)[:4] == str(fiscal_year):
            return filing
    return None


def _classify_edgar_error(exc: Exception, ticker: str) -> FinLabError:
    """Map a raw edgartools / HTTP exception to a FinLabError subclass.

    Returns the mapped exception (caller uses ``raise mapped from exc``).

    Rules:
    - edgartools ``TooManyRequestsError`` or HTTP 429 → ``RateLimitError``
      (carries ``retry_after`` when SEC provides the header).
    - HTTP 5xx (``httpx.HTTPStatusError`` or ``requests.HTTPError``) →
      ``TransientError``.
    - Existing ``FinLabError`` (e.g. already-classified ``SECError``) →
      pass through unchanged.
    - Anything else → ``TickerNotFoundError`` (empty-filings template).
    """
    try:
        from edgar.httprequests import TooManyRequestsError

        if isinstance(exc, TooManyRequestsError):
            return RateLimitError(
                f"SEC EDGAR ({ticker})", retry_after=getattr(exc, "retry_after", None)
            )
    except ImportError:
        pass

    try:
        import httpx

        if isinstance(exc, httpx.HTTPStatusError):
            status = getattr(getattr(exc, "response", None), "status_code", None)
            if status == 429:
                return RateLimitError(
                    f"SEC EDGAR ({ticker})",
                    retry_after=_parse_retry_after_seconds_header(exc.response),
                )
            if status is not None and 500 <= status < 600:
                return TransientError(f"SEC EDGAR returned {status} for {ticker}.")
    except ImportError:
        pass

    try:
        import requests

        if isinstance(exc, requests.HTTPError):
            status = getattr(getattr(exc, "response", None), "status_code", None)
            if status == 429:
                return RateLimitError(
                    f"SEC EDGAR ({ticker})",
                    retry_after=_parse_retry_after_seconds_header(exc.response),
                )
            if status is not None and 500 <= status < 600:
                return TransientError(f"SEC EDGAR returned {status} for {ticker}.")
    except ImportError:
        pass

    if isinstance(exc, FinLabError):
        return exc
    return TickerNotFoundError(f"Ticker {ticker!r} not found on SEC EDGAR.")


def _parse_retry_after_seconds_header(response) -> int | None:
    """Parse a SEC EDGAR ``Retry-After`` header as integer seconds.

    The name encodes the contract: this helper intentionally accepts only
    the integer-seconds form of ``Retry-After``. Returns the parsed number
    of seconds, or ``None`` when the header is absent or cannot be parsed
    as an integer.

    Per RFC 7231 ``Retry-After`` may also be an HTTP-date (e.g.
    ``Wed, 21 Oct 2015 07:28:00 GMT``), but SEC EDGAR is observed to emit
    integer seconds exclusively. Date-form headers deliberately fall back
    to ``None`` — SEC does not use them in practice and supporting the
    format would complicate the hot path for no observed benefit. If a
    future SEC-adjacent caller begins relying on date-form ``Retry-After``
    headers, broaden the parser rather than silently changing its name.
    """
    headers = getattr(response, "headers", None) or {}
    raw = headers.get("Retry-After") if hasattr(headers, "get") else None
    if not raw:
        return None
    try:
        return int(str(raw).strip())
    except ValueError:
        return None


@lru_cache(maxsize=16)
def _resolve_latest_fiscal_year_cached(ticker_upper: str) -> int:
    identity = os.getenv("EDGAR_IDENTITY")
    if not identity:
        raise ConfigurationError("EDGAR_IDENTITY environment variable is not set.")

    from edgar import Company, set_identity

    set_identity(identity)

    try:
        company = Company(ticker_upper)
        filings = company.get_filings(form="10-K")
    except Exception as exc:
        raise _classify_edgar_error(exc, ticker_upper) from exc

    if filings is None or len(filings) == 0:
        try:
            alt_filings = company.get_filings(form="20-F")
        except Exception:
            alt_filings = None
        if alt_filings is not None and len(alt_filings) > 0:
            raise UnsupportedFilingTypeError(
                f"Ticker {ticker_upper} appears to be a foreign private issuer "
                f"that files 20-F; only '10-K' is supported."
            )
        raise TickerNotFoundError(
            f"Ticker {ticker_upper!r} has no 10-K filings on SEC EDGAR."
        )

    latest = filings.latest()
    return int(str(latest.period_of_report)[:4])


def _resolve_latest_fiscal_year(ticker: str) -> int:
    """Resolve the latest 10-K fiscal year for ``ticker`` using ONLY
    filing-index metadata. Does NOT call ``filing.obj()`` — does NOT
    download/parse the 10-K.

    Same classification rules as ``fetch_filing_obj``'s empty-filings branch:
    ``TickerNotFoundError`` if no 10-K exists, ``UnsupportedFilingTypeError``
    if the ticker files 20-F instead.

    Normalizes ``ticker`` (strip + upper) before delegating to the cached
    inner function so the cache key space is canonical.
    """
    return _resolve_latest_fiscal_year_cached(ticker.strip().upper())


@dataclass(frozen=True)
class FetchedFiling:
    """A fetched ``TenK`` plus its citation metadata, captured from the
    public edgartools ``Filing`` API at fetch time so downstream callers
    never need to reach into edgartools private attributes."""

    tenk: "TenK"
    accession_number: str
    cik: str
    company_name: str
    primary_document: str


@lru_cache(maxsize=64)
def _locate_filing_cached(
    ticker_upper: str,
    filing_type: FilingType,
    fiscal_year: int | None,
):
    """Locate the target ``Filing`` on SEC EDGAR (index metadata only).

    Company lookup + filings listing + fiscal-year pick; does NOT call
    ``filing.obj()`` and does NOT touch ``filing.document`` — callers
    decide which (if any) of those extra fetches they need.
    """
    identity = os.getenv("EDGAR_IDENTITY")
    if not identity:
        raise ConfigurationError("EDGAR_IDENTITY environment variable is not set.")

    from edgar import Company, set_identity

    set_identity(identity)

    try:
        company = Company(ticker_upper)
        filings = company.get_filings(form=str(filing_type))
    except Exception as exc:
        raise _classify_edgar_error(exc, ticker_upper) from exc

    if filings is None or len(filings) == 0:
        try:
            alt_filings = company.get_filings(form="20-F")
        except Exception:
            alt_filings = None
        if alt_filings is not None and len(alt_filings) > 0:
            raise UnsupportedFilingTypeError(
                f"Ticker {ticker_upper} appears to be a foreign private issuer "
                f"that files 20-F; only '10-K' is supported."
            )
        raise TickerNotFoundError(
            f"Ticker {ticker_upper!r} has no 10-K filings on SEC EDGAR."
        )

    if fiscal_year is None:
        filing = filings.latest()
    else:
        filing = _find_by_fiscal_year(filings, fiscal_year)
        if filing is None:
            raise FilingNotFoundError(
                f"No {filing_type} filing for {ticker_upper} in fiscal year {fiscal_year}."
            )
    return filing


@lru_cache(maxsize=64)
def _fetch_filing_obj_cached(
    ticker_upper: str,
    filing_type: FilingType,
    fiscal_year: int | None,
) -> "TenK":
    """Locate the filing and parse it into a ``TenK``.

    Deliberately does NOT read ``filing.document`` — that is an extra
    SGML/homepage network fetch which the legacy ``fetch_filing_obj``
    contract never performed; only the bundle path pays for it.
    """
    from edgar.company_reports import TenK

    filing = _locate_filing_cached(ticker_upper, filing_type, fiscal_year)

    try:
        obj = filing.obj()
    except Exception as exc:
        raise _classify_edgar_error(exc, ticker_upper) from exc

    if not isinstance(obj, TenK):
        raise SECError(f"Expected TenK, got {type(obj).__name__}")
    return obj


@lru_cache(maxsize=64)
def _fetch_filing_bundle_cached(
    ticker_upper: str,
    filing_type: FilingType,
    fiscal_year: int | None,
) -> FetchedFiling:
    filing = _locate_filing_cached(ticker_upper, filing_type, fiscal_year)

    # Capture citation metadata from the public Filing API. ``filing.document``
    # may trigger an extra SGML/homepage fetch inside edgartools — acceptable,
    # it happens once per cached key — so its failures must go through the
    # same FinLabError classification as the primary fetches.
    try:
        accession_number = filing.accession_number
        cik = str(filing.cik)
        company_name = filing.company
        document = filing.document
        primary_document = (
            getattr(document, "document", None) if document is not None else None
        )
    except Exception as exc:
        raise _classify_edgar_error(exc, ticker_upper) from exc

    if not primary_document:
        raise SECError(
            f"Filing {accession_number} for {ticker_upper} has no primary "
            f"document on SEC EDGAR; cannot build citation metadata."
        )

    tenk = _fetch_filing_obj_cached(ticker_upper, filing_type, fiscal_year)
    return FetchedFiling(
        tenk=tenk,
        accession_number=accession_number,
        cik=cik,
        company_name=company_name,
        primary_document=primary_document,
    )


@lru_cache(maxsize=8)
def _fetch_filing_markdown_cached(
    ticker_upper: str,
    filing_type: FilingType,
    fiscal_year: int | None,
) -> str:
    filing = _locate_filing_cached(ticker_upper, filing_type, fiscal_year)
    try:
        return filing.markdown() or ""
    except Exception as exc:
        # The filing is already located, so _classify_edgar_error's
        # TickerNotFoundError fallback would be a lie here — an
        # unclassifiable render failure must say what actually broke.
        mapped = _classify_edgar_error(exc, ticker_upper)
        if isinstance(mapped, TickerNotFoundError):
            raise SECError(
                f"Failed to render markdown for {ticker_upper} {filing_type} "
                f"(fiscal year {fiscal_year if fiscal_year is not None else 'latest'}, "
                f"accession {filing.accession_number}): {exc}"
            ) from exc
        raise mapped from exc


def fetch_filing_markdown(
    ticker: str,
    filing_type: FilingType,
    fiscal_year: int | None = None,
) -> str:
    """Fetch the filing-level markdown rendering of a filing (additive API).

    The markdown's H3/H4 heading lines feed the text pipeline's block
    detection; nothing downstream stores the markdown itself. Shares
    :func:`_locate_filing_cached` with the other fetchers, so calling this
    alongside :func:`fetch_filing_bundle` costs one extra document render,
    not an extra EDGAR locate. Cache is smaller than the other LRUs because
    whole-filing markdown strings are MB-scale.

    Same exception family as :func:`fetch_filing_obj`.
    """
    return _fetch_filing_markdown_cached(
        ticker.strip().upper(), filing_type, fiscal_year
    )


_inflight_lock = threading.Lock()
_inflight: dict[tuple[str, FilingType, int | None], Future] = {}


def fetch_filing_obj(
    ticker: str,
    filing_type: FilingType,
    fiscal_year: int | None = None,
) -> "TenK":
    """Fetch and parse a 10-K via edgartools, normalizing ``ticker`` to upper.

    LRU-cached by ``(ticker_upper, filing_type, fiscal_year)``;
    ``fiscal_year=None`` resolves to the latest filing. A module-level
    single-flight registry collapses parallel races so SEC EDGAR is hit
    once even when concurrent callers race past the LRU.

    Raises ``ConfigurationError`` (no ``EDGAR_IDENTITY``),
    ``TickerNotFoundError``, ``UnsupportedFilingTypeError`` (20-F filer),
    ``FilingNotFoundError``, ``TransientError`` (5xx), or
    ``RateLimitError`` (429; surfaced immediately with ``retry_after`` —
    edgartools does not retry rate limits).
    """
    key = (ticker.strip().upper(), filing_type, fiscal_year)

    with _inflight_lock:
        existing = _inflight.get(key)
        if existing is not None:
            fut = existing
            am_winner = False
        else:
            fut = Future()
            _inflight[key] = fut
            am_winner = True

    if not am_winner:
        return fut.result()

    try:
        result = _fetch_filing_obj_cached(*key)
        fut.set_result(result)
        return result
    except BaseException as exc:
        fut.set_exception(exc)
        raise
    finally:
        with _inflight_lock:
            _inflight.pop(key, None)


def fetch_filing_bundle(
    ticker: str,
    filing_type: FilingType,
    fiscal_year: int | None = None,
) -> FetchedFiling:
    """Fetch a 10-K plus its citation metadata as a :class:`FetchedFiling`.

    Entry point for callers that need accession number / CIK / company name /
    primary document alongside the parsed ``TenK``, without touching
    edgartools private attributes.

    Delegates to :func:`fetch_filing_obj` first so the locate+parse fetch
    goes through the same single-flight de-dupe (which populates the shared
    locate/obj LRUs), then assembles the bundle from those caches plus one
    ``filing.document`` metadata read (an extra fetch only bundle callers
    pay for, once per cached key).

    Same cache key and raised exceptions as :func:`fetch_filing_obj`, plus
    ``SECError`` when the filing has no primary document.
    """
    fetch_filing_obj(ticker, filing_type, fiscal_year)
    return _fetch_filing_bundle_cached(ticker.strip().upper(), filing_type, fiscal_year)
