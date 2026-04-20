from pathlib import Path

import pytest

from backend.common.sec_core import (
    TENK_STANDARD_TITLES,
    ConfigurationError,
    FilingNotFoundError,
    FilingType,
    SECError,
    SectionNotFoundError,
    TickerNotFoundError,
    TransientError,
    UnsupportedFilingTypeError,
    is_stub_section,
    parse_item_number,
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
