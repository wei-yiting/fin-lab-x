import time
from datetime import date, datetime

import pytest
from pydantic import BaseModel

from backend.ingestion.quant_data_pipeline.duck_db.row_models import (
    CompanyRow,
    MarketValuationRow,
    YFinanceQuarterlyRow,
)
from backend.ingestion.quant_data_pipeline.duck_db.upsert import upsert_rows


def test_empty_list_short_circuit(tmp_duckdb):
    """Empty list returns 0 and touches nothing in the DB."""
    result = upsert_rows(tmp_duckdb, "companies", ["ticker"], [])
    assert result == 0
    count = tmp_duckdb.execute("SELECT count(*) FROM companies").fetchone()
    assert count is not None and count[0] == 0


def test_insert_normal_path(tmp_duckdb):
    """Single CompanyRow inserts correctly and updated_at is populated."""
    row = CompanyRow(
        ticker="MSFT",
        company_name="Microsoft Corp",
        sector="Technology",
        industry="Software",
        fy_end_month=6,
        fy_end_day=30,
    )
    result = upsert_rows(tmp_duckdb, "companies", ["ticker"], [row])
    assert result == 1

    fetched = tmp_duckdb.execute(
        "SELECT ticker, company_name, sector, industry, fy_end_month, fy_end_day, updated_at "
        "FROM companies WHERE ticker='MSFT'"
    ).fetchone()
    assert fetched is not None
    assert fetched[0] == "MSFT"
    assert fetched[1] == "Microsoft Corp"
    assert fetched[2] == "Technology"
    assert fetched[3] == "Software"
    assert fetched[4] == 6
    assert fetched[5] == 30
    assert fetched[6] is not None  # updated_at set by DB


def test_idempotent_update(tmp_duckdb):
    """Re-upserting same PK with different sector updates the row and advances updated_at."""
    row_v1 = CompanyRow(
        ticker="MSFT",
        company_name="Microsoft Corp",
        sector="Technology",
        industry="Software",
        fy_end_month=6,
        fy_end_day=30,
    )
    upsert_rows(tmp_duckdb, "companies", ["ticker"], [row_v1])
    first_at = tmp_duckdb.execute(
        "SELECT updated_at FROM companies WHERE ticker='MSFT'"
    ).fetchone()
    assert first_at is not None

    time.sleep(0.05)  # ensure CURRENT_TIMESTAMP advances

    row_v2 = CompanyRow(
        ticker="MSFT",
        company_name="Microsoft Corp",
        sector="NewSector",
        industry="Software",
        fy_end_month=6,
        fy_end_day=30,
    )
    upsert_rows(tmp_duckdb, "companies", ["ticker"], [row_v2])
    second_at = tmp_duckdb.execute(
        "SELECT updated_at, sector FROM companies WHERE ticker='MSFT'"
    ).fetchone()
    assert second_at is not None
    assert second_at[1] == "NewSector"
    assert second_at[0] >= first_at[0]


def test_column_level_merge(tmp_duckdb):
    """yfinance DTO must not clobber SEC-only columns written by a prior raw INSERT."""
    # Pre-seed SEC-only columns via raw SQL
    tmp_duckdb.execute(
        "INSERT INTO quarterly_financials "
        "(ticker, fiscal_year, fiscal_quarter, period_end, product_revenue_usd, current_rpo_usd) "
        "VALUES ('NVDA', 2025, 3, '2025-09-30', 10000000, 20000000)"
    )

    # yfinance upsert: only yfinance-scoped fields — no product_revenue_usd, no current_rpo_usd
    yf_row = YFinanceQuarterlyRow(
        ticker="NVDA",
        fiscal_year=2025,
        fiscal_quarter=3,
        period_end=date(2025, 9, 30),
        total_revenue_usd=50_000_000_000,
    )
    upsert_rows(
        tmp_duckdb,
        "quarterly_financials",
        ["ticker", "fiscal_year", "fiscal_quarter"],
        [yf_row],
    )

    row = tmp_duckdb.execute(
        "SELECT product_revenue_usd, current_rpo_usd, total_revenue_usd "
        "FROM quarterly_financials WHERE ticker='NVDA' AND fiscal_year=2025 AND fiscal_quarter=3"
    ).fetchone()
    assert row is not None
    assert row[0] == 10_000_000, "product_revenue_usd must be untouched by yfinance upsert"
    assert row[1] == 20_000_000, "current_rpo_usd must be untouched by yfinance upsert"
    assert row[2] == 50_000_000_000, "total_revenue_usd must be written by yfinance upsert"


def test_updated_at_assertion_guard(tmp_duckdb):
    """DTO that declares updated_at must trigger ValueError before touching DB."""

    class BadRow(BaseModel):
        ticker: str
        updated_at: datetime

    bad_row = BadRow(ticker="BAD", updated_at=datetime.now())
    with pytest.raises(ValueError, match="updated_at"):
        upsert_rows(tmp_duckdb, "companies", ["ticker"], [bad_row])


def test_pydantic_validation_error_on_missing_required_field():
    """CompanyRow requires ticker and company_name — missing them raises ValidationError."""
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        CompanyRow(
            company_name="No Ticker Corp",
            fy_end_month=12,
            fy_end_day=31,
        )  # type: ignore[call-arg]


def test_existing_default_behavior_unchanged(tmp_duckdb):
    """Default-path (no coalesce_columns kwarg) still upserts and overwrites as before."""
    row_v1 = CompanyRow(
        ticker="MSFT",
        company_name="Microsoft Corp",
        sector="Technology",
        industry="Software",
        fy_end_month=6,
        fy_end_day=30,
    )
    upsert_rows(tmp_duckdb, "companies", ["ticker"], [row_v1])
    row_v2 = CompanyRow(
        ticker="MSFT",
        company_name="Microsoft Corp",
        sector="NewSector",
        industry="Software",
        fy_end_month=6,
        fy_end_day=30,
    )
    result = upsert_rows(tmp_duckdb, "companies", ["ticker"], [row_v2])
    assert result == 1

    fetched = tmp_duckdb.execute(
        "SELECT sector FROM companies WHERE ticker='MSFT'"
    ).fetchone()
    assert fetched is not None
    assert fetched[0] == "NewSector"


def test_coalesce_columns_preserves_existing_value_on_null(tmp_duckdb):
    """COALESCE(EXCLUDED.col, table.col): None incoming preserves stored value."""
    initial = MarketValuationRow(
        ticker="MSFT",
        as_of_date=date(2026, 5, 4),
        market_cap_usd=3_400_000_000_000,
        dividend_yield_pct=0.46,
    )
    upsert_rows(
        tmp_duckdb,
        "market_valuations",
        ["ticker", "as_of_date"],
        [initial],
        coalesce_columns=["market_cap_usd", "dividend_yield_pct"],
    )

    refresh = MarketValuationRow(
        ticker="MSFT",
        as_of_date=date(2026, 5, 4),
        market_cap_usd=None,
        dividend_yield_pct=0.47,
    )
    upsert_rows(
        tmp_duckdb,
        "market_valuations",
        ["ticker", "as_of_date"],
        [refresh],
        coalesce_columns=["market_cap_usd", "dividend_yield_pct"],
    )

    fetched = tmp_duckdb.execute(
        "SELECT market_cap_usd, dividend_yield_pct "
        "FROM market_valuations WHERE ticker='MSFT' AND as_of_date='2026-05-04'"
    ).fetchone()
    assert fetched is not None
    assert fetched[0] == 3_400_000_000_000, "market_cap_usd must be preserved on NULL"
    assert fetched[1] == 0.47, "non-None incoming dividend_yield_pct must overwrite"


def test_coalesce_columns_overwrites_with_non_null(tmp_duckdb):
    """When both rows have non-None values, the new value wins under COALESCE."""
    initial = MarketValuationRow(
        ticker="AAPL",
        as_of_date=date(2026, 5, 4),
        market_cap_usd=3_000_000_000_000,
    )
    upsert_rows(
        tmp_duckdb,
        "market_valuations",
        ["ticker", "as_of_date"],
        [initial],
        coalesce_columns=["market_cap_usd"],
    )

    updated = MarketValuationRow(
        ticker="AAPL",
        as_of_date=date(2026, 5, 4),
        market_cap_usd=3_100_000_000_000,
    )
    upsert_rows(
        tmp_duckdb,
        "market_valuations",
        ["ticker", "as_of_date"],
        [updated],
        coalesce_columns=["market_cap_usd"],
    )

    fetched = tmp_duckdb.execute(
        "SELECT market_cap_usd FROM market_valuations "
        "WHERE ticker='AAPL' AND as_of_date='2026-05-04'"
    ).fetchone()
    assert fetched is not None
    assert fetched[0] == 3_100_000_000_000


def test_coalesce_columns_rejects_pk(tmp_duckdb):
    """coalesce_columns containing a PK column raises ValueError before any DB work."""
    row = MarketValuationRow(
        ticker="MSFT",
        as_of_date=date(2026, 5, 4),
        market_cap_usd=3_400_000_000_000,
    )
    with pytest.raises(ValueError) as excinfo:
        upsert_rows(
            tmp_duckdb,
            "market_valuations",
            ["ticker", "as_of_date"],
            [row],
            coalesce_columns=["ticker"],
        )
    msg = str(excinfo.value)
    assert "coalesce_columns" in msg
    assert "PK" in msg


def test_coalesce_columns_empty_iterable_treated_as_none(tmp_duckdb):
    """Empty iterable disables COALESCE — None values overwrite stored ones."""
    initial = MarketValuationRow(
        ticker="GOOG",
        as_of_date=date(2026, 5, 4),
        market_cap_usd=2_000_000_000_000,
        dividend_yield_pct=0.10,
    )
    upsert_rows(
        tmp_duckdb,
        "market_valuations",
        ["ticker", "as_of_date"],
        [initial],
        coalesce_columns=[],
    )

    refresh = MarketValuationRow(
        ticker="GOOG",
        as_of_date=date(2026, 5, 4),
        market_cap_usd=None,
        dividend_yield_pct=None,
    )
    upsert_rows(
        tmp_duckdb,
        "market_valuations",
        ["ticker", "as_of_date"],
        [refresh],
        coalesce_columns=[],
    )

    fetched = tmp_duckdb.execute(
        "SELECT market_cap_usd, dividend_yield_pct "
        "FROM market_valuations WHERE ticker='GOOG' AND as_of_date='2026-05-04'"
    ).fetchone()
    assert fetched is not None
    assert fetched[0] is None, "empty coalesce_columns must not protect None overwrite"
    assert fetched[1] is None


def test_coalesce_columns_unknown_column_raises(tmp_duckdb):
    """Typo in coalesce_columns is caught at runtime against the DTO field set."""
    row = MarketValuationRow(
        ticker="MSFT",
        as_of_date=date(2026, 5, 4),
        market_cap_usd=3_400_000_000_000,
    )
    with pytest.raises(ValueError, match="not_a_real_column"):
        upsert_rows(
            tmp_duckdb,
            "market_valuations",
            ["ticker", "as_of_date"],
            [row],
            coalesce_columns=["not_a_real_column"],
        )


def test_coalesce_columns_set_or_tuple_works(tmp_duckdb):
    """Iterable[str] accepts non-list containers (set, tuple)."""
    initial = MarketValuationRow(
        ticker="NVDA",
        as_of_date=date(2026, 5, 4),
        market_cap_usd=2_800_000_000_000,
    )
    upsert_rows(
        tmp_duckdb,
        "market_valuations",
        ["ticker", "as_of_date"],
        [initial],
        coalesce_columns=("market_cap_usd",),
    )

    refresh = MarketValuationRow(
        ticker="NVDA",
        as_of_date=date(2026, 5, 4),
        market_cap_usd=None,
    )
    upsert_rows(
        tmp_duckdb,
        "market_valuations",
        ["ticker", "as_of_date"],
        [refresh],
        coalesce_columns={"market_cap_usd"},
    )

    fetched = tmp_duckdb.execute(
        "SELECT market_cap_usd FROM market_valuations "
        "WHERE ticker='NVDA' AND as_of_date='2026-05-04'"
    ).fetchone()
    assert fetched is not None
    assert fetched[0] == 2_800_000_000_000
