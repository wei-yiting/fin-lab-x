import re
from unittest.mock import MagicMock

import pytest
import requests
from finnhub.exceptions import FinnhubAPIException
from langchain_core.messages import ToolMessage

from backend.agent_engine.agents.base import _HandleToolErrors
from backend.agent_engine.tools.error_contract import (
    describe_tool_error,
    format_tool_error,
)
from backend.agent_engine.tools.finnhub_client import FinnhubNoDataError
from backend.common.errors import (
    ConfigurationError,
    RateLimitError,
    TickerNotFoundError,
    TransientError,
)
from backend.common.sec_core import (
    FilingNotFoundError,
    NoTenKFilingsError,
    SectionNotFoundError,
    UnsupportedFilingTypeError,
)


def _call(name: str, **args) -> dict:
    return {"name": name, "args": args, "id": "call-1", "type": "tool_call"}


def _finnhub_exc(status: int, error: str) -> FinnhubAPIException:
    response = MagicMock()
    response.status_code = status
    response.json.return_value = {"error": error}
    return FinnhubAPIException(response)


_HEADER_RE = re.compile(r"^TOOL ERROR — kind: (\w+) \| retryable: (yes|no|unknown)")


def _assert_contract_shape(message: str) -> tuple[str, str]:
    """Every rendered error states what failed, why, retryability and a next step."""
    match = _HEADER_RE.match(message)
    assert match, message
    assert "\nWhat failed: " in message
    assert "\nWhy: " in message
    assert "\nNext step: " in message
    return match.group(1), match.group(2)


def test_twenty_f_filer_is_permanent_for_all_sec_tools():
    exc = UnsupportedFilingTypeError(
        "Ticker SAP appears to be a foreign private issuer that files 20-F; "
        "only '10-K' is supported."
    )
    msg = format_tool_error(exc, _call("sec_filing_list_sections", ticker="SAP"))

    assert _assert_contract_shape(msg) == ("non_10k_filer", "no")
    assert 'sec_filing_list_sections {"ticker": "SAP"}' in msg
    assert "20-F" in msg
    assert "Do not call any sec_filing_* tool for SAP again" in msg
    assert "Finnhub" in msg
    assert "tell the user" in msg


def test_company_without_any_10k_is_non_10k_filer():
    exc = NoTenKFilingsError("Ticker 'RY' has no 10-K filings on SEC EDGAR.")
    msg = format_tool_error(exc, _call("sec_filing_list_sections", ticker="RY"))

    assert _assert_contract_shape(msg) == ("non_10k_filer", "no")
    assert "40-F" in msg
    assert "Do not call any sec_filing_* tool for RY again" in msg


def test_sec_ticker_not_found_with_exchange_suffix_names_non_us_listing():
    exc = TickerNotFoundError("Ticker 'MC.PA' not found on SEC EDGAR.")
    msg = format_tool_error(exc, _call("sec_filing_list_sections", ticker="MC.PA"))

    assert _assert_contract_shape(msg) == ("sec_ticker_not_found", "no")
    assert "non-US exchange listing" in msg
    assert "Do not call any sec_filing_* tool for MC.PA again" in msg


def test_sec_ticker_not_found_without_suffix_names_delisted_or_typo():
    exc = TickerNotFoundError("Ticker 'XYZQ' not found on SEC EDGAR.")
    msg = format_tool_error(exc, _call("sec_filing_get_section", ticker="xyzq"))

    kind, _ = _assert_contract_shape(msg)
    assert kind == "sec_ticker_not_found"
    assert "delisted" in msg
    assert "XYZQ" in msg
    assert "non-US exchange listing" not in msg


def test_finnhub_403_blocks_both_finnhub_tools_for_the_ticker():
    exc = _finnhub_exc(403, "You don't have access to this resource.")
    msg = format_tool_error(exc, _call("finnhub_stock_quote", ticker="0700.HK"))

    assert _assert_contract_shape(msg) == ("provider_no_access", "no")
    assert "finnhub_stock_quote" in msg
    assert "finnhub_company_basic_financials" in msg
    assert "Do not call any finnhub_* tool for 0700.HK again" in msg
    assert "403" in msg


@pytest.mark.parametrize("status", [429, 500, 503])
def test_finnhub_rate_limit_and_server_errors_are_retryable(status):
    exc = _finnhub_exc(status, "API limit reached" if status == 429 else "oops")
    msg = format_tool_error(exc, _call("finnhub_stock_quote", ticker="AAPL"))

    _, retryable = _assert_contract_shape(msg)
    assert retryable == "yes"
    assert "retry this call once" in msg


def test_finnhub_no_data_blocks_finnhub_for_the_ticker():
    exc = FinnhubNoDataError(
        "No quote data for ticker 'FRC'. The symbol may be invalid, "
        "delisted, or not covered by Finnhub free tier."
    )
    msg = format_tool_error(exc, _call("finnhub_stock_quote", ticker="FRC"))

    assert _assert_contract_shape(msg) == ("finnhub_no_data", "no")
    assert "Do not call any finnhub_* tool for FRC again" in msg
    assert "stale" in msg


def test_missing_section_lists_available_keys_inline():
    exc = SectionNotFoundError(
        "Section '7' not found in INTC 10-K FY2025. "
        "Call sec_filing_list_sections first to see available section keys.",
        fiscal_year=2025,
        available_keys=("1", "1a", "2", "8"),
    )
    msg = format_tool_error(
        exc, _call("sec_filing_get_section", ticker="INTC", section_key="7")
    )

    assert _assert_contract_shape(msg) == ("section_not_in_filing", "no")
    assert "FY2025" in msg
    assert "Available section keys in this filing: 1, 1a, 2, 8" in msg
    assert "no need to call sec_filing_list_sections" in msg
    assert "Do not request section '7' for INTC FY2025 again" in msg
    assert '"section_key": "7"' in msg
    assert "[REDACTED]" not in msg


def test_section_added_later_points_to_first_year_that_has_it():
    exc = SectionNotFoundError(
        "Section '1c' (Cybersecurity) was added by SEC in 2023 and is not "
        "present in FY2022.",
        fiscal_year=2022,
        first_fiscal_year=2023,
    )
    msg = format_tool_error(
        exc,
        _call(
            "sec_filing_get_section", ticker="AAPL", section_key="1c", fiscal_year=2022
        ),
    )

    assert _assert_contract_shape(msg) == ("section_not_in_filing", "no")
    assert "FY2023" in msg
    assert "1a" in msg


def test_invalid_section_key_lists_valid_keys():
    exc = SectionNotFoundError("Section key 'MD&A' is not a valid 10-K item number.")
    msg = format_tool_error(
        exc, _call("sec_filing_get_section", ticker="AAPL", section_key="MD&A")
    )

    kind, _ = _assert_contract_shape(msg)
    assert kind == "invalid_section_key"
    assert "Valid keys: 1, 1a, 1b, 1c, 2," in msg


def test_fiscal_year_not_filed_yet_points_to_latest():
    exc = FilingNotFoundError(
        "No 10-K filed yet for AAPL fiscal year 2027 — the most recent available "
        "is FY2025.",
        earliest_fiscal_year=1994,
        latest_fiscal_year=2025,
    )
    msg = format_tool_error(
        exc, _call("sec_filing_list_sections", ticker="AAPL", fiscal_year=2027)
    )

    assert _assert_contract_shape(msg) == ("fiscal_year_unavailable", "no")
    assert "not been filed yet" in msg
    assert "fiscal_year=2025" in msg
    assert "Do not request FY2027 for AAPL again" in msg


def test_fiscal_year_before_history_points_to_earliest():
    exc = FilingNotFoundError(
        "TSLA has no 10-K filing history before FY2010; fiscal year 2008 could "
        "never have one.",
        earliest_fiscal_year=2010,
        latest_fiscal_year=2025,
    )
    msg = format_tool_error(
        exc, _call("sec_filing_list_sections", ticker="TSLA", fiscal_year=2008)
    )

    assert _assert_contract_shape(msg) == ("fiscal_year_unavailable", "no")
    assert "will never exist" in msg
    assert "FY2010" in msg


@pytest.mark.parametrize(
    "exc",
    [
        TransientError("SEC EDGAR returned 503 for AAPL."),
        RateLimitError("SEC EDGAR (AAPL)", retry_after=5),
        requests.Timeout("read timed out"),
        requests.ConnectionError("connection reset"),
    ],
)
def test_transient_failures_are_retryable_once(exc):
    msg = format_tool_error(exc, _call("sec_filing_list_sections", ticker="AAPL"))

    kind, retryable = _assert_contract_shape(msg)
    assert kind == "transient"
    assert retryable == "yes"
    assert "retry this call once" in msg


def test_configuration_error_is_permanent_for_the_provider():
    exc = ConfigurationError("EDGAR_IDENTITY environment variable is not set.")
    msg = format_tool_error(exc, _call("sec_filing_list_sections", ticker="AAPL"))

    assert _assert_contract_shape(msg) == ("source_unavailable", "no")
    assert "Do not call any sec_filing_* tool again" in msg


def test_unknown_exception_stays_generic_but_labelled():
    exc = RuntimeError("something odd happened")
    msg = format_tool_error(exc, _call("tavily_financial_search", query="x"))

    assert _assert_contract_shape(msg) == ("unexpected", "unknown")
    assert "something odd happened" in msg
    assert "at most once" in msg


def test_redaction_still_applies_to_rendered_message():
    exc = RuntimeError(
        "failed with api_key=sk-abcdef1234567890 at /srv/app/secret/config.py"
    )
    msg = format_tool_error(exc, _call("tavily_financial_search", query="x"))

    assert "sk-abcdef1234567890" not in msg
    assert "/srv/app/secret" not in msg
    assert "[REDACTED]" in msg


def test_describe_exposes_structured_fields():
    exc = UnsupportedFilingTypeError("files 20-F")
    report = describe_tool_error(exc, _call("sec_filing_get_section", ticker="TSM"))

    assert report.kind == "non_10k_filer"
    assert report.retryable is False
    assert report.tool == "sec_filing_get_section"


def test_middleware_returns_contract_message_as_error_tool_message():
    request = MagicMock()
    request.tool_call = _call("sec_filing_list_sections", ticker="ASML")

    def handler(_request):
        raise UnsupportedFilingTypeError("files 20-F")

    result = _HandleToolErrors().wrap_tool_call(request, handler)

    assert isinstance(result, ToolMessage)
    assert result.status == "error"
    assert result.tool_call_id == "call-1"
    assert result.content.startswith("TOOL ERROR — kind: non_10k_filer")


@pytest.mark.asyncio
async def test_async_middleware_returns_contract_message():
    request = MagicMock()
    request.tool_call = _call("finnhub_stock_quote", ticker="AIR.PA")

    async def handler(_request):
        raise _finnhub_exc(403, "You don't have access to this resource.")

    result = await _HandleToolErrors().awrap_tool_call(request, handler)

    assert result.status == "error"
    assert result.content.startswith("TOOL ERROR — kind: provider_no_access")
