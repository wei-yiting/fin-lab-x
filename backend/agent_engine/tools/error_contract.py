"""Tool error contract: what the model is told when a tool call raises.

Every tool exception is turned into one shape — what failed, why, whether it
is retryable, and the next step — so the agent can tell a permanent coverage
gap (stop calling this provider for this ticker) from a transient failure
(retry once). Known exceptions map to a specific ``kind``; anything else is
labelled ``unexpected`` and passes its own text through. The rendered text is
still run through ``sanitize_tool_error``.

Classification reads exception types and the structured fields the raise sites
attach (never the message wording), so raise-site messages can change freely.
The middleware has no view of the agent's toolset, so next steps name tool
families ("sec_filing_*", "finnhub_*") and "a news search", not specific
optional tools.
"""

from __future__ import annotations

import json
import re
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Literal

import requests
from finnhub.exceptions import FinnhubAPIException, FinnhubRequestException

from backend.agent_engine.streaming.tool_error_sanitizer import sanitize_tool_error
from backend.agent_engine.tools.finnhub_client import FinnhubNoDataError
from backend.common.errors import (
    ConfigurationError,
    RateLimitError,
    TickerNotFoundError,
    TransientError,
)
from backend.common.sec_core import (
    TENK_STANDARD_TITLES,
    FilingNotFoundError,
    NoTenKFilingsError,
    SectionNotFoundError,
    UnsupportedFilingTypeError,
)

Retryable = Literal["yes", "no", "unknown"]

_SEC_FAMILY = "sec_filing_*"
_FINNHUB_FAMILY = "finnhub_*"
_FINNHUB_TOOLS = "finnhub_stock_quote and finnhub_company_basic_financials"

# Ticker with an exchange suffix such as AIR.PA, 0700.HK, 7203.T. Excludes
# US share-class forms like BRK.B, whose suffix is a single letter.
_EXCHANGE_SUFFIX_RE = re.compile(r"^[A-Z0-9]+\.[A-Z]{2,}$")


@dataclass(frozen=True)
class ToolErrorReport:
    tool: str
    kind: str
    retryable: bool | None
    what_failed: str
    why: str
    next_step: str

    def render(self) -> str:
        flag: Retryable = (
            "unknown" if self.retryable is None else ("yes" if self.retryable else "no")
        )
        return (
            f"TOOL ERROR — kind: {self.kind} | retryable: {flag}\n"
            f"What failed: {self.what_failed}\n"
            f"Why: {self.why}\n"
            f"Next step: {self.next_step}"
        )


def format_tool_error(exc: BaseException, tool_call: Mapping[str, Any]) -> str:
    """Render ``exc`` raised by ``tool_call`` as the sanitized contract text."""
    return sanitize_tool_error(describe_tool_error(exc, tool_call).render())


@dataclass(frozen=True)
class _Call:
    tool: str
    args: Mapping[str, Any]

    @property
    def ticker(self) -> str:
        return str(self.args.get("ticker") or "").strip().upper()

    @property
    def family(self) -> str | None:
        if self.tool.startswith("sec_filing"):
            return "sec"
        if self.tool.startswith("finnhub"):
            return "finnhub"
        return None

    def report(
        self, kind: str, retryable: bool | None, why: str, next_step: str
    ) -> ToolErrorReport:
        # JSON, not k=v: the sanitizer redacts any "<...>key=<value>", which
        # would swallow section_key=7.
        args = json.dumps(
            {k: v for k, v in self.args.items() if v is not None},
            ensure_ascii=False,
            default=str,
        )
        return ToolErrorReport(
            self.tool, kind, retryable, f"{self.tool} {args}", why, next_step
        )


def describe_tool_error(
    exc: BaseException, tool_call: Mapping[str, Any]
) -> ToolErrorReport:
    call = _Call(
        str(tool_call.get("name") or "unknown_tool"), tool_call.get("args") or {}
    )
    ticker = call.ticker
    report = call.report

    if isinstance(exc, (UnsupportedFilingTypeError, NoTenKFilingsError)):
        form = (
            "20-F"
            if isinstance(exc, UnsupportedFilingTypeError)
            else "another annual form such as 40-F (Canadian issuers)"
        )
        return report(
            "non_10k_filer",
            False,
            f"{ticker} does not file 10-K reports; it files {form}. The SEC tools "
            "here read 10-K filings only, so this will not change on retry.",
            f"Do not call any {_SEC_FAMILY} tool for {ticker} again. Use Finnhub "
            "tools for its price and fundamentals and a news search for "
            "qualitative context, and tell the user its annual-report text is "
            "not available here.",
        )

    if isinstance(exc, FilingNotFoundError):
        return _fiscal_year_report(exc, call)

    if isinstance(exc, SectionNotFoundError):
        return _section_report(exc, call)

    if isinstance(exc, TickerNotFoundError) and call.family == "sec":
        if _EXCHANGE_SUFFIX_RE.match(ticker):
            cause = (
                f"{ticker} looks like a non-US exchange listing; non-US listings "
                "are not SEC registrants"
            )
        else:
            cause = (
                f"{ticker} is not a current SEC ticker; the company may be "
                "delisted, acquired, renamed, or the symbol mistyped"
            )
        return report(
            "sec_ticker_not_found",
            False,
            f"{cause}. This will not change on retry.",
            f"Do not call any {_SEC_FAMILY} tool for {ticker} again. If you are "
            "confident the company files 10-Ks under a different US ticker, you "
            "may try that ticker once; otherwise use a news search and tell the "
            "user SEC filings are not available for it.",
        )

    if isinstance(exc, FinnhubNoDataError):
        return report(
            "finnhub_no_data",
            False,
            f"Finnhub has no live data for {ticker}; the symbol is likely "
            "delisted, renamed, or invalid. This will not change on retry.",
            f"Do not call any {_FINNHUB_FAMILY} tool for {ticker} again — any "
            "fundamentals it still returns for a dead symbol would be stale. If "
            "you are confident the company now trades under a new ticker, use "
            "that; otherwise use a news search and tell the user live market "
            "data is not available.",
        )

    if isinstance(exc, FinnhubAPIException):
        status = getattr(exc, "status_code", None)
        if status in (401, 403):
            return report(
                "provider_no_access",
                False,
                f"Finnhub denied access to {ticker} (HTTP {status}): the data plan "
                "used here does not cover this symbol — typically non-US exchange "
                f"listings. {_FINNHUB_TOOLS} share that coverage, so neither will "
                "work and retrying will not help.",
                f"Do not call any {_FINNHUB_FAMILY} tool for {ticker} again. If "
                "you are confident the company has a US-listed ticker or ADR, you "
                "may try that once; otherwise use a news search and tell the user "
                f"live price and fundamentals for {ticker} are not available.",
            )
        if status == 429 or (status is not None and status >= 500):
            return _transient(call, f"Finnhub returned HTTP {status}.")

    if isinstance(exc, (TransientError, RateLimitError, FinnhubRequestException)):
        return _transient(call, sanitize_tool_error(str(exc)))
    if isinstance(exc, (requests.Timeout, requests.ConnectionError)):
        return _transient(call, f"Network error: {type(exc).__name__}.")

    if isinstance(exc, ConfigurationError):
        family_glob = {"sec": _SEC_FAMILY, "finnhub": _FINNHUB_FAMILY}.get(
            call.family or ""
        )
        scope = f"any {family_glob} tool" if family_glob else call.tool
        return report(
            "source_unavailable",
            False,
            "This data source is not configured in this deployment.",
            f"Do not call {scope} again. Answer from other sources and tell the "
            "user this data source is unavailable.",
        )

    return report(
        "unexpected",
        None,
        sanitize_tool_error(str(exc)) or type(exc).__name__,
        "Retry this exact call at most once. If it fails again, continue with "
        "other sources and tell the user this data could not be retrieved.",
    )


def _transient(call: _Call, why: str) -> ToolErrorReport:
    return call.report(
        "transient",
        True,
        f"{why} This looks temporary.",
        "You may retry this call once. If it fails again, continue without it "
        "and tell the user this data was temporarily unavailable.",
    )


def _fiscal_year_report(exc: FilingNotFoundError, call: _Call) -> ToolErrorReport:
    ticker = call.ticker
    year = call.args.get("fiscal_year")
    earliest, latest = exc.earliest_fiscal_year, exc.latest_fiscal_year
    if latest is not None and isinstance(year, int) and year > latest:
        why = (
            f"{ticker}'s FY{year} 10-K has not been filed yet; the latest "
            f"available is FY{latest}."
        )
    elif earliest is not None and isinstance(year, int) and year < earliest:
        why = (
            f"{ticker}'s 10-K history starts at FY{earliest}; a FY{year} 10-K "
            "will never exist."
        )
    else:
        why = f"{ticker} has no 10-K for FY{year}."
    if earliest is not None and latest is not None:
        why += f" Available fiscal years: FY{earliest}–FY{latest}."
    pointer = (
        f"Use fiscal_year={latest} (latest) or another year in that range"
        if latest is not None
        else "Omit fiscal_year to get the latest 10-K"
    )
    return call.report(
        "fiscal_year_unavailable",
        False,
        why,
        f"Do not request FY{year} for {ticker} again. {pointer} if it still "
        f"answers the question, and tell the user the FY{year} 10-K does not "
        "exist.",
    )


def _section_report(exc: SectionNotFoundError, call: _Call) -> ToolErrorReport:
    key = str(call.args.get("section_key") or "")
    year = (
        exc.fiscal_year if exc.fiscal_year is not None else call.args.get("fiscal_year")
    )
    filing = f"{call.ticker} FY{year}" if year is not None else call.ticker

    if exc.first_fiscal_year is not None:
        return call.report(
            "section_not_in_filing",
            False,
            f"Item {key.upper()} was first required in FY{exc.first_fiscal_year} 10-Ks; "
            f"{filing}'s 10-K has no such item.",
            f"Do not request section '{key}' for {filing} again. Use "
            f"fiscal_year={exc.first_fiscal_year} or later for this item, or "
            f"section '1a' (Risk Factors) of FY{year}, and tell the user the "
            f"FY{year} 10-K has no Item {key.upper()}.",
        )

    if exc.available_keys is not None:
        keys = ", ".join(exc.available_keys)
        return call.report(
            "section_not_in_filing",
            False,
            f"Section '{key}' could not be found in {filing}'s 10-K. Available "
            f"section keys in this filing: {keys}.",
            f"Do not request section '{key}' for {filing} again. Call "
            "sec_filing_get_section with the closest available key above (no "
            "need to call sec_filing_list_sections), or use a news search, and "
            "tell the user the requested section could not be read.",
        )

    return call.report(
        "invalid_section_key",
        False,
        f"'{key}' is not a 10-K item number. Valid keys: "
        f"{', '.join(TENK_STANDARD_TITLES)}.",
        "Call sec_filing_get_section again with one of the valid keys.",
    )
