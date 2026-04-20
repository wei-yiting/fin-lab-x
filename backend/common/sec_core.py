import re
from enum import StrEnum


class FilingType(StrEnum):
    TEN_K = "10-K"
    # TEN_Q = "10-Q"  # reserved for future PR


class SECError(Exception):
    """SEC domain base exception."""


class TickerNotFoundError(SECError): ...


class FilingNotFoundError(SECError): ...


class UnsupportedFilingTypeError(SECError): ...


class TransientError(SECError): ...


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
