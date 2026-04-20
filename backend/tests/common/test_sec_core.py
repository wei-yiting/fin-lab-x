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
)


def test_filing_type_enum():
    assert FilingType.TEN_K == "10-K"
    assert FilingType("10-K") is FilingType.TEN_K


def test_section_not_found_error_is_sec_error():
    assert issubclass(SectionNotFoundError, SECError)
    for exc_cls in (
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
