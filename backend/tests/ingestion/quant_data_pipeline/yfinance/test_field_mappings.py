import pytest

from backend.ingestion.quant_data_pipeline.yfinance.field_mappings import (
    BALANCE_LINE_TO_FIELD,
    CASHFLOW_LINE_TO_FIELD,
    DEFERRED_REVENUE_FALLBACK,
    INCOME_LINE_TO_FIELD,
    INFO_TO_MARKET_VALUATION_FIELD,
    YFINANCE_OWNED_COLUMNS,
)


def test_yfinance_owned_columns_is_frozenset():
    assert isinstance(YFINANCE_OWNED_COLUMNS, frozenset)


def test_yfinance_owned_columns_contains_yfinance_quarterly_fields():
    expected_present = {
        "total_revenue_usd",
        "goodwill_usd",
        "capital_expenditure_usd",
        "operating_cash_flow_usd",
        "diluted_eps",
        "deferred_revenue_usd",
    }
    assert expected_present.issubset(YFINANCE_OWNED_COLUMNS)


def test_yfinance_owned_columns_excludes_sec_only():
    sec_only_columns = {
        "product_revenue_usd",
        "service_revenue_usd",
        "current_rpo_usd",
        "noncurrent_rpo_usd",
        "total_lease_obligation_usd",
    }
    assert sec_only_columns.isdisjoint(YFINANCE_OWNED_COLUMNS)


def test_yfinance_owned_columns_excludes_pk_and_period():
    excluded = {"ticker", "fiscal_year", "fiscal_quarter", "period_start", "period_end"}
    assert excluded.isdisjoint(YFINANCE_OWNED_COLUMNS)


def test_yfinance_owned_columns_excludes_market_valuation_only_fields():
    assert "market_cap_usd" not in YFINANCE_OWNED_COLUMNS


def test_mapping_types_correct():
    assert isinstance(INFO_TO_MARKET_VALUATION_FIELD, dict)
    assert len(INFO_TO_MARKET_VALUATION_FIELD) >= 1
    for key, value in INFO_TO_MARKET_VALUATION_FIELD.items():
        assert isinstance(key, str)
        assert isinstance(value, tuple)
        assert len(value) == 2
        dest, converter = value
        assert isinstance(dest, str)
        assert converter is None or callable(converter)

    for mapping in (INCOME_LINE_TO_FIELD, BALANCE_LINE_TO_FIELD, CASHFLOW_LINE_TO_FIELD):
        assert isinstance(mapping, dict)
        assert len(mapping) >= 1
        for key, value in mapping.items():
            assert isinstance(key, str)
            assert isinstance(value, str)


def test_held_pct_converter_multiplies_by_100():
    _, converter = INFO_TO_MARKET_VALUATION_FIELD["heldPercentInstitutions"]
    assert converter is not None
    assert converter(0.7598) == pytest.approx(75.98)


def test_deferred_revenue_fallback_is_ordered_tuple():
    assert isinstance(DEFERRED_REVENUE_FALLBACK, tuple)
    assert DEFERRED_REVENUE_FALLBACK[0] == "Deferred Revenue"
    assert DEFERRED_REVENUE_FALLBACK[1] == "Current Deferred Revenue"
