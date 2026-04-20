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
