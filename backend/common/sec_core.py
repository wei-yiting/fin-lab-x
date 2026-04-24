"""SEC filing domain core — types and helpers shared across subsystems.

Types: :class:`FilingType`, :class:`SECError` hierarchy,
``TENK_STANDARD_TITLES`` (SEC 17 CFR 229 canonical item map).
Helpers: :func:`parse_item_number` (agent-facing key normalization),
:func:`is_stub_section` (incorp-by-reference / reserved detection),
:func:`fetch_filing_obj` (LRU-cached ``edgartools.TenK`` fetch).

Shared by :mod:`backend.agent_engine.tools.sec_filing_tools` and
:mod:`backend.ingestion.sec_filing_pipeline`. Do not add agent-layer or
pipeline-layer concerns here — keep this module a thin, stateless core.
"""

import os
import re
from enum import StrEnum
from functools import lru_cache
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from edgar.company_reports.ten_k import TenK  # noqa: F401


class FilingType(StrEnum):
    TEN_K = "10-K"
    # TEN_Q = "10-Q"  # reserved for future PR


class SECError(Exception):
    """SEC domain base exception."""


class TickerNotFoundError(SECError): ...


class FilingNotFoundError(SECError): ...


class UnsupportedFilingTypeError(SECError): ...


class TransientError(SECError): ...


class RateLimitError(SECError):
    """SEC EDGAR returned HTTP 429. Carries ``retry_after`` when SEC provides
    the ``Retry-After`` header; ``None`` means SEC did not tell us how long
    to wait (typically corresponds to the default 10-minute IP block).
    """

    def __init__(self, ticker: str, retry_after: int | None):
        self.retry_after = retry_after
        msg = f"SEC EDGAR rate-limited {ticker}"
        if retry_after is not None:
            msg += f" (Retry-After={retry_after}s)"
        super().__init__(msg)


class ConfigurationError(SECError): ...


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
    if not _NORMALIZED_ITEM_RE.match(candidate) or candidate not in TENK_STANDARD_TITLES:
        raise SectionNotFoundError(
            f"Section key {section_key!r} is not a valid 10-K item number. "
            "Call sec_filing_list_sections first to see available section keys."
        )
    return candidate


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

    if not _STUB_INCORP_RE.search(text):
        return (False, None)

    sentences = _STUB_SENTENCE_SPLIT_RE.split(text)
    kept = [s for s in sentences if not _STUB_INCORP_RE.search(s)]
    remaining = " ".join(kept)
    remaining = _STUB_MARKDOWN_LINK_RE.sub("", remaining)
    cleaned = re.sub(r"[\s\-\|\*]+", "", remaining)
    if len(cleaned) < _STUB_REMAINING_THRESHOLD:
        return (True, "incorporated by reference from proxy statement")
    return (False, None)


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


def _classify_edgar_error(exc: Exception, ticker: str) -> SECError:
    """Map a raw edgartools / HTTP exception to a SECError subclass.

    Returns the mapped exception (caller uses ``raise mapped from exc``).

    Rules:
    - edgartools ``TooManyRequestsError`` or HTTP 429 → ``RateLimitError``
      (carries ``retry_after`` when SEC provides the header).
    - HTTP 5xx (``httpx.HTTPStatusError`` or ``requests.HTTPError``) →
      ``TransientError``.
    - Existing ``SECError`` → pass through unchanged.
    - Anything else → ``TickerNotFoundError`` (empty-filings template).
    """
    try:
        from edgar.httprequests import TooManyRequestsError

        if isinstance(exc, TooManyRequestsError):
            return RateLimitError(
                ticker, retry_after=getattr(exc, "retry_after", None)
            )
    except ImportError:
        pass

    try:
        import httpx

        if isinstance(exc, httpx.HTTPStatusError):
            status = getattr(getattr(exc, "response", None), "status_code", None)
            if status == 429:
                return RateLimitError(
                    ticker,
                    retry_after=_parse_retry_after_seconds_header(exc.response),
                )
            if status is not None and 500 <= status < 600:
                return TransientError(
                    f"SEC EDGAR returned {status} for {ticker}."
                )
    except ImportError:
        pass

    try:
        import requests

        if isinstance(exc, requests.HTTPError):
            status = getattr(getattr(exc, "response", None), "status_code", None)
            if status == 429:
                return RateLimitError(
                    ticker,
                    retry_after=_parse_retry_after_seconds_header(exc.response),
                )
            if status is not None and 500 <= status < 600:
                return TransientError(
                    f"SEC EDGAR returned {status} for {ticker}."
                )
    except ImportError:
        pass

    if isinstance(exc, SECError):
        return exc
    return TickerNotFoundError(
        f"Ticker {ticker!r} not found on SEC EDGAR."
    )


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
        raise ConfigurationError(
            "EDGAR_IDENTITY environment variable is not set."
        )

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


@lru_cache(maxsize=64)
def _fetch_filing_obj_cached(
    ticker_upper: str,
    filing_type: FilingType,
    fiscal_year: int | None,
) -> "TenK":
    identity = os.getenv("EDGAR_IDENTITY")
    if not identity:
        raise ConfigurationError(
            "EDGAR_IDENTITY environment variable is not set."
        )

    from edgar import Company, set_identity
    from edgar.company_reports import TenK

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

    try:
        obj = filing.obj()
    except Exception as exc:
        raise _classify_edgar_error(exc, ticker_upper) from exc

    if not isinstance(obj, TenK):
        raise SECError(f"Expected TenK, got {type(obj).__name__}")
    return obj


def fetch_filing_obj(
    ticker: str,
    filing_type: FilingType,
    fiscal_year: int | None = None,
) -> "TenK":
    """Fetch and parse a TenK filing via edgartools.

    Caches by ``(ticker_upper, filing_type, fiscal_year)``. ``fiscal_year=None``
    resolves to the latest filing; agent tools should prefer passing the
    resolved int so the cache key space stays unified.

    Normalizes ``ticker`` (strip + upper) before delegating to the cached
    inner function so callers passing ``"aapl"`` and ``"AAPL"`` share a
    cache entry.

    Raises:
        ConfigurationError: ``EDGAR_IDENTITY`` not set.
        TickerNotFoundError: Ticker not found or no 10-K filings.
        UnsupportedFilingTypeError: Ticker files 20-F instead (FPI).
        FilingNotFoundError: No filing matches the requested ``fiscal_year``.
        TransientError: SEC EDGAR returned 5xx.
        RateLimitError: SEC EDGAR returned 429. edgartools' own
            retry/backoff has already been exhausted; the caller must
            wait (typically ~10 minutes) before retrying. ``retry_after``
            is populated when SEC supplies the header and ``None``
            otherwise (which typically indicates the ~10-minute IP block).
    """
    return _fetch_filing_obj_cached(ticker.strip().upper(), filing_type, fiscal_year)
