from pathlib import Path
from unittest.mock import MagicMock

import httpx
import pytest

from backend.common.sec_core import (
    TENK_STANDARD_TITLES,
    ConfigurationError,
    FilingNotFoundError,
    FilingType,
    RateLimitError,
    SECError,
    SectionNotFoundError,
    TickerNotFoundError,
    TransientError,
    UnsupportedFilingTypeError,
    _resolve_latest_fiscal_year,
    fetch_filing_obj,
    is_stub_section,
    parse_item_number,
    trim_text_to_item_boundary,
)

_FIXTURES = Path(__file__).parent / "fixtures" / "stub_samples"


def test_filing_type_enum():
    assert FilingType.TEN_K == "10-K"
    assert FilingType("10-K") is FilingType.TEN_K


def test_all_sec_errors_inherit_from_sec_error():
    for exc_cls in (
        SectionNotFoundError,
        TickerNotFoundError,
        FilingNotFoundError,
        UnsupportedFilingTypeError,
        TransientError,
        RateLimitError,
        ConfigurationError,
    ):
        assert issubclass(exc_cls, SECError)


def test_tenk_standard_titles_shape():
    expected_keys = {
        "1", "1a", "1b", "1c",
        "2", "3", "4",
        "5", "6",
        "7", "7a",
        "8",
        "9", "9a", "9b", "9c",
        "10", "11", "12", "13", "14", "15", "16",
    }
    assert set(TENK_STANDARD_TITLES.keys()) == expected_keys
    assert len(TENK_STANDARD_TITLES) == len(expected_keys)
    for key, value in TENK_STANDARD_TITLES.items():
        assert isinstance(value, str)
        assert value, f"Title for key {key!r} must be non-empty"

    # Spot-check against the canonical SEC Form 10-K / Reg S-K item titles —
    # a typo in sec_core.py would fail these assertions.
    assert TENK_STANDARD_TITLES["1"] == "Business"
    assert TENK_STANDARD_TITLES["1a"] == "Risk Factors"
    assert TENK_STANDARD_TITLES["6"] == "[Reserved]"
    assert (
        TENK_STANDARD_TITLES["7"]
        == "Management's Discussion and Analysis of Financial Condition and Results of Operations"
    )
    assert (
        TENK_STANDARD_TITLES["9c"]
        == "Disclosure Regarding Foreign Jurisdictions that Prevent Inspections"
    )


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("1a", "1a"),
        ("1A", "1a"),
        ("Item 1a", "1a"),
        ("1a.", "1a"),
        (" 1a ", "1a"),
    ],
)
def test_parse_item_number_variants_success(raw, expected):
    assert parse_item_number(raw) == expected


@pytest.mark.parametrize(
    "raw",
    [
        "1 a",
        "part_i_item_1a",
        "１ａ",
        "99z",
    ],
)
def test_parse_item_number_variants_failure(raw):
    with pytest.raises(SectionNotFoundError):
        parse_item_number(raw)


def test_parse_item_number_error_message():
    with pytest.raises(SectionNotFoundError) as exc_info:
        parse_item_number("99z")
    assert "sec_filing_list_sections" in str(exc_info.value)


# ---------------------------------------------------------------------------
# trim_text_to_item_boundary
# ---------------------------------------------------------------------------


def test_trim_text_to_item_boundary_cuts_at_next_item():
    """The exact bleed shape observed for AAPL FY2025 Item 11."""
    text = (
        "Item 11.    Executive Compensation\n"
        "The information required by this Item will be included in the 2026 Proxy Statement.\n"
        "Item 12.    Security Ownership of Certain Beneficial Owners\n"
        "The information required by this Item will be included in the 2026 Proxy Statement.\n"
        "Item 13.    Certain Relationships\n"
    )
    trimmed = trim_text_to_item_boundary(text, "11")
    assert "Item 11." in trimmed
    assert "Item 12." not in trimmed
    assert "Item 13." not in trimmed


def test_trim_text_to_item_boundary_preserves_self_header():
    """The first 'Item N.' line — the section's own header — must survive."""
    text = "Item 7.    Management's Discussion and Analysis\nFirst paragraph.\n"
    assert trim_text_to_item_boundary(text, "7") == text


def test_trim_text_to_item_boundary_no_boundary_passthrough():
    """A clean section without any 'Item N.' substring is returned unchanged."""
    text = "First paragraph of body text.\nSecond paragraph.\n"
    assert trim_text_to_item_boundary(text, "1") == text


@pytest.mark.parametrize(
    "current_item,heading_form",
    [
        ("11", "Item 11."),
        ("11", "ITEM 11."),
        ("11", "Item 11 ."),
        ("9c", "Item 9C."),
        ("1a", "Item 1A."),
    ],
)
def test_trim_text_to_item_boundary_case_and_subitem_letter(current_item, heading_form):
    """Match is case-insensitive and recognizes 1A/7A/9C-style sub-items."""
    text = f"{heading_form}    Title here\nBody.\nItem 99.    Something else.\n"
    trimmed = trim_text_to_item_boundary(text, current_item)
    assert heading_form in trimmed
    assert "Item 99." not in trimmed


def test_trim_text_to_item_boundary_does_not_match_inside_word():
    """A literal substring 'item 5.' inside a sentence body must NOT trigger
    a boundary cut — only line-leading or whitespace-leading matches do.
    """
    text = (
        "Item 7.    MD&A\n"
        "We also reference customer item 5.4 in the discussion below.\n"
        "Continuing the body of Item 7.\n"
    )
    # The 'item 5.4' inside the sentence has '5' as a digit prefix that the
    # boundary regex cares about — make sure word-boundary style anchoring
    # keeps that out of contention.
    trimmed = trim_text_to_item_boundary(text, "7")
    # If this assertion fails, the regex anchor is too loose.
    assert "Continuing the body of Item 7." in trimmed


@pytest.mark.parametrize(
    "fixture_name,expected_is_stub,expected_reason_substring",
    [
        ("aapl_item_11.txt", True, "incorporated"),
        ("aapl_item_1a.txt", False, None),
        ("item_1b_none.txt", False, None),
        ("item_6_reserved.txt", True, "reserved"),
        ("rare_part_stub.txt", True, "incorporated"),
    ],
)
def test_is_stub_section_boundary_samples(
    fixture_name, expected_is_stub, expected_reason_substring
):
    text = (_FIXTURES / fixture_name).read_text()
    is_stub, reason = is_stub_section(text)
    assert is_stub is expected_is_stub
    if expected_is_stub:
        assert expected_reason_substring in reason
        if fixture_name == "item_6_reserved.txt":
            # Classification specificity: a reserved section must not be
            # mislabeled as an incorporated-by-reference stub.
            assert "incorporated by reference" not in reason
    else:
        assert reason is None


@pytest.mark.parametrize("empty", ["", "   ", "\n\n\t"])
def test_is_stub_section_empty_input(empty):
    assert is_stub_section(empty) == (False, None)


@pytest.mark.parametrize(
    "text,expected_is_stub,expected_reason_substring",
    [
        # Below-threshold: incorp sentence + short trailer. After dropping
        # the incorp sentence and stripping whitespace/structural noise,
        # the remainder is ~16 chars (well under 100), so the classifier
        # must flag this as an incorp stub.
        (
            "Item 9. The information required by this Item is incorporated herein "
            "by reference from the Proxy Statement. See page 12.",
            True,
            "incorporated",
        ),
        # Above-threshold: incorp sentence + a substantive trailing
        # paragraph. After the same strip, the remainder is ~201 chars
        # (well above 100), so the item is NOT a stub despite containing
        # the incorp phrase earlier in the text.
        (
            "Item 9. The information required by this Item is incorporated herein "
            "by reference from the Proxy Statement. "
            "Beyond the pointer above, the Company also discusses material agreements, "
            "executive tenure, board composition, and a variety of long-running "
            "governance practices that materially shape how disclosure is organized "
            "for this item.",
            False,
            None,
        ),
    ],
)
def test_is_stub_section_threshold_boundary(
    text, expected_is_stub, expected_reason_substring
):
    is_stub, reason = is_stub_section(text)
    assert is_stub is expected_is_stub
    if expected_is_stub:
        assert expected_reason_substring in reason
    else:
        assert reason is None


# ---------------------------------------------------------------------------
# fetch_filing_obj / _resolve_latest_fiscal_year
# ---------------------------------------------------------------------------


class _TenKStub:
    """Stand-in class for edgar.company_reports.TenK used as the isinstance
    target after monkeypatching `edgar.company_reports.TenK`."""


def _make_filing(period_of_report: str, tenk_stub_cls: type) -> MagicMock:
    filing = MagicMock()
    filing.period_of_report = period_of_report
    obj_instance = tenk_stub_cls()
    filing.obj = MagicMock(return_value=obj_instance)
    return filing


def _make_filings_collection(filings_list: list) -> MagicMock:
    coll = MagicMock()
    coll.__iter__ = lambda self: iter(filings_list)
    coll.__len__ = lambda self: len(filings_list)
    coll.latest = MagicMock(return_value=filings_list[-1] if filings_list else None)
    return coll


@pytest.fixture
def mock_edgar(monkeypatch):
    """Assemble a mock edgar.Company / Filings / Filing / TenK chain.

    Returns a dict exposing `company_spy`, `company_instance`, `filings`,
    `filings_by_form` (mapping form -> filings collection), `tenk_cls`, and
    a helper `set_filings(form, filings_list)`.
    """
    monkeypatch.setenv("EDGAR_IDENTITY", "Test Reporter test@example.com")

    tenk_cls = _TenKStub

    filings_by_form: dict[str, MagicMock] = {}

    def get_filings(form: str):
        return filings_by_form.get(form, _make_filings_collection([]))

    company_instance = MagicMock()
    company_instance.get_filings = MagicMock(side_effect=get_filings)

    company_spy = MagicMock(return_value=company_instance)
    monkeypatch.setattr("edgar.Company", company_spy)
    monkeypatch.setattr("edgar.set_identity", MagicMock())
    monkeypatch.setattr("edgar.company_reports.TenK", tenk_cls)

    def set_filings(form: str, filings_list: list):
        filings_by_form[form] = _make_filings_collection(filings_list)

    return {
        "company_spy": company_spy,
        "company_instance": company_instance,
        "set_filings": set_filings,
        "tenk_cls": tenk_cls,
    }


def test_fetch_filing_obj_configuration_error_without_identity(monkeypatch):
    monkeypatch.delenv("EDGAR_IDENTITY", raising=False)
    with pytest.raises(ConfigurationError):
        fetch_filing_obj("AAPL", FilingType.TEN_K, 2025)


def test_fetch_filing_obj_caches_by_key(mock_edgar):
    tenk_cls = mock_edgar["tenk_cls"]
    aapl_filing = _make_filing("2025-09-27", tenk_cls)
    msft_filing = _make_filing("2025-06-30", tenk_cls)
    mock_edgar["set_filings"]("10-K", [aapl_filing])

    # First AAPL call → Company called once.
    fetch_filing_obj("AAPL", FilingType.TEN_K, 2025)
    assert mock_edgar["company_spy"].call_count == 1

    # Second AAPL call (same key) → cache hit, no new Company call.
    fetch_filing_obj("AAPL", FilingType.TEN_K, 2025)
    assert mock_edgar["company_spy"].call_count == 1

    # Different ticker → new Company call.
    mock_edgar["set_filings"]("10-K", [msft_filing])
    fetch_filing_obj("MSFT", FilingType.TEN_K, 2025)
    assert mock_edgar["company_spy"].call_count == 2


def test_fetch_filing_obj_fiscal_year_filter(mock_edgar):
    tenk_cls = mock_edgar["tenk_cls"]
    f2024 = _make_filing("2024-09-30", tenk_cls)
    f2025 = _make_filing("2025-09-27", tenk_cls)
    mock_edgar["set_filings"]("10-K", [f2024, f2025])

    obj_2024 = fetch_filing_obj("AAPL", FilingType.TEN_K, 2024)
    # The 2024 filing's .obj() result should be what we got back.
    assert obj_2024 is f2024.obj.return_value

    with pytest.raises(FilingNotFoundError):
        fetch_filing_obj("AAPL", FilingType.TEN_K, 2099)


def test_fetch_filing_obj_skips_amendments(mock_edgar):
    tenk_cls = mock_edgar["tenk_cls"]
    filing = _make_filing("2025-09-27", tenk_cls)
    mock_edgar["set_filings"]("10-K", [filing])

    fetch_filing_obj("AAPL", FilingType.TEN_K, 2025)

    called_forms = [
        call.kwargs.get("form") or (call.args[0] if call.args else None)
        for call in mock_edgar["company_instance"].get_filings.call_args_list
    ]
    assert "10-K" in called_forms
    assert "10-K/A" not in called_forms


def test_fetch_filing_obj_ticker_not_found(monkeypatch):
    monkeypatch.setenv("EDGAR_IDENTITY", "Test Reporter test@example.com")

    def _boom(ticker):
        raise Exception("company not found")

    monkeypatch.setattr("edgar.Company", _boom)
    monkeypatch.setattr("edgar.set_identity", MagicMock())
    monkeypatch.setattr("edgar.company_reports.TenK", _TenKStub)

    with pytest.raises(TickerNotFoundError) as exc_info:
        fetch_filing_obj("ZZZZ", FilingType.TEN_K, 2025)
    assert "ZZZZ" in str(exc_info.value)


def test_fetch_filing_obj_fpi_ticker_tsm(mock_edgar):
    tenk_cls = mock_edgar["tenk_cls"]
    # 10-K is empty (default). Populate 20-F.
    mock_edgar["set_filings"]("20-F", [_make_filing("2024-12-31", tenk_cls)])

    with pytest.raises(UnsupportedFilingTypeError) as exc_info:
        fetch_filing_obj("TSM", FilingType.TEN_K, 2024)
    msg = str(exc_info.value)
    assert "20-F" in msg
    assert "foreign private issuer" in msg


def test_fetch_filing_obj_transient_error(monkeypatch):
    monkeypatch.setenv("EDGAR_IDENTITY", "Test Reporter test@example.com")

    company_instance = MagicMock()
    http_error = httpx.HTTPStatusError(
        message="503",
        request=httpx.Request("GET", "https://sec.gov"),
        response=httpx.Response(503),
    )
    company_instance.get_filings = MagicMock(side_effect=http_error)

    monkeypatch.setattr("edgar.Company", MagicMock(return_value=company_instance))
    monkeypatch.setattr("edgar.set_identity", MagicMock())
    monkeypatch.setattr("edgar.company_reports.TenK", _TenKStub)

    with pytest.raises(TransientError):
        fetch_filing_obj("AAPL", FilingType.TEN_K, 2025)


def _make_429_httpx_error(retry_after: str | None = None) -> httpx.HTTPStatusError:
    headers = {"Retry-After": retry_after} if retry_after is not None else {}
    response = httpx.Response(429, headers=headers)
    return httpx.HTTPStatusError(
        message="429",
        request=httpx.Request("GET", "https://sec.gov"),
        response=response,
    )


def test_fetch_filing_obj_429_raises_rate_limit_error_immediately(monkeypatch):
    """429 → RateLimitError with retry_after populated, no retry attempt.

    edgartools already runs its own exponential-backoff retries before any
    429 reaches this layer. We intentionally do NOT wrap an additional
    retry here — the caller must wait (typically ~10 minutes) before
    retrying on its own. This test pins that contract: exactly one
    ``get_filings`` call, no sleep, ``retry_after`` surfaced from the
    SEC-provided header.
    """
    monkeypatch.setenv("EDGAR_IDENTITY", "Test Reporter test@example.com")

    company_instance = MagicMock()
    company_instance.get_filings = MagicMock(
        side_effect=_make_429_httpx_error(retry_after="5")
    )
    monkeypatch.setattr("edgar.Company", MagicMock(return_value=company_instance))
    monkeypatch.setattr("edgar.set_identity", MagicMock())
    monkeypatch.setattr("edgar.company_reports.TenK", _TenKStub)

    import time as _time

    sleeps: list[float] = []
    monkeypatch.setattr(_time, "sleep", lambda s: sleeps.append(s))

    with pytest.raises(RateLimitError) as exc_info:
        fetch_filing_obj("AAPL", FilingType.TEN_K, 2025)

    assert exc_info.value.retry_after == 5
    assert sleeps == []
    assert company_instance.get_filings.call_count == 1


def test_fetch_filing_obj_429_http_date_retry_after_falls_back_to_none(monkeypatch):
    """Retry-After in HTTP-date form → retry_after is None (documented).

    ``_parse_retry_after_seconds_header`` is deliberately narrow: SEC
    EDGAR emits integer seconds in practice, so the HTTP-date form is
    intentionally unsupported to keep the hot path simple. This test
    pins that contract — a date-form header must surface as
    ``RateLimitError.retry_after is None`` rather than an exception.
    """
    monkeypatch.setenv("EDGAR_IDENTITY", "Test Reporter test@example.com")

    company_instance = MagicMock()
    company_instance.get_filings = MagicMock(
        side_effect=_make_429_httpx_error(retry_after="Wed, 21 Oct 2015 07:28:00 GMT")
    )
    monkeypatch.setattr("edgar.Company", MagicMock(return_value=company_instance))
    monkeypatch.setattr("edgar.set_identity", MagicMock())
    monkeypatch.setattr("edgar.company_reports.TenK", _TenKStub)

    with pytest.raises(RateLimitError) as exc_info:
        fetch_filing_obj("AAPL", FilingType.TEN_K, 2025)

    assert exc_info.value.retry_after is None
    assert company_instance.get_filings.call_count == 1


def test_resolve_latest_fiscal_year_reads_metadata_only(mock_edgar):
    tenk_cls = mock_edgar["tenk_cls"]
    filing = _make_filing("2025-09-27", tenk_cls)
    mock_edgar["set_filings"]("10-K", [filing])

    fy = _resolve_latest_fiscal_year("AAPL")
    assert fy == 2025
    filing.obj.assert_not_called()


def test_resolve_latest_fiscal_year_cached(mock_edgar):
    tenk_cls = mock_edgar["tenk_cls"]
    filing = _make_filing("2025-09-27", tenk_cls)
    mock_edgar["set_filings"]("10-K", [filing])

    _resolve_latest_fiscal_year("AAPL")
    _resolve_latest_fiscal_year("AAPL")
    assert mock_edgar["company_spy"].call_count == 1


def test_resolve_latest_fiscal_year_ticker_not_found(mock_edgar):
    # Both forms empty → TickerNotFoundError.
    with pytest.raises(TickerNotFoundError):
        _resolve_latest_fiscal_year("ZZZZ")


def test_resolve_latest_fiscal_year_fpi(mock_edgar):
    tenk_cls = mock_edgar["tenk_cls"]
    mock_edgar["set_filings"]("20-F", [_make_filing("2024-12-31", tenk_cls)])
    with pytest.raises(UnsupportedFilingTypeError):
        _resolve_latest_fiscal_year("TSM")


def test_fetch_filing_obj_cache_key_normalizes_ticker(mock_edgar):
    """Lowercase and uppercase ticker inputs must share one cache entry."""
    tenk_cls = mock_edgar["tenk_cls"]
    filing = _make_filing("2025-09-27", tenk_cls)
    mock_edgar["set_filings"]("10-K", [filing])

    fetch_filing_obj("aapl", FilingType.TEN_K, 2025)
    fetch_filing_obj("AAPL", FilingType.TEN_K, 2025)

    # Same canonical key → only one underlying call to edgar.Company.
    assert mock_edgar["company_spy"].call_count == 1


def test_fetch_filing_obj_ticker_not_found_both_forms_empty(mock_edgar):
    """Empty 10-K list + empty 20-F list on fetch_filing_obj → TickerNotFoundError."""
    # Both forms default to empty in mock_edgar (filings_by_form uninitialized).
    with pytest.raises(TickerNotFoundError) as exc_info:
        fetch_filing_obj("ZZZZ", FilingType.TEN_K, 2025)
    assert "ZZZZ" in str(exc_info.value)
