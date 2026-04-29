from datetime import date

import duckdb
import pytest

from backend.ingestion.quant_data_pipeline.calendar_to_fiscal_period import normalize_fiscal_period
from backend.ingestion.quant_data_pipeline.duck_db.row_models import (
    CompanyRow,
    YFinanceQuarterlyRow,
)
from backend.ingestion.quant_data_pipeline.duck_db.upsert import upsert_rows
from backend.ingestion.quant_data_pipeline.ingestion_run_tracker import (
    track_ingestion_run,
)


def test_foundation_roundtrip(tmp_duckdb):
    # 1. Insert company
    assert upsert_rows(
        tmp_duckdb,
        "companies",
        ["ticker"],
        [
            CompanyRow(
                ticker="MSFT",
                company_name="Microsoft Corporation",
                sector="Technology",
                industry="Software",
                fy_end_month=6,
                fy_end_day=30,
            )
        ],
    ) == 1
    row = tmp_duckdb.execute(
        "SELECT ticker, company_name, fy_end_month, updated_at FROM companies WHERE ticker='MSFT'"
    ).fetchone()
    assert row is not None
    assert row[:3] == ("MSFT", "Microsoft Corporation", 6)
    assert row[3] is not None  # updated_at set

    # 2. Compute fiscal period + insert quarterly
    fy, fq = normalize_fiscal_period(date(2024, 9, 30), fiscal_year_end_month=6)
    assert (fy, fq) == (2025, 1)

    with track_ingestion_run(tmp_duckdb, "yfinance", "MSFT") as report:
        n = upsert_rows(
            tmp_duckdb,
            "quarterly_financials",
            ["ticker", "fiscal_year", "fiscal_quarter"],
            [
                YFinanceQuarterlyRow(
                    ticker="MSFT",
                    fiscal_year=fy,
                    fiscal_quarter=fq,
                    period_end=date(2024, 9, 30),
                    total_revenue_usd=65_000_000_000,
                )
            ],
        )
        report.rows_written_total = n

    # 3. Verify audit row
    audit = tmp_duckdb.execute("""
        SELECT pipeline, ticker, status, rows_written_total
        FROM ingestion_runs
        WHERE pipeline='yfinance' AND ticker='MSFT'
    """).fetchone()
    assert audit == ("yfinance", "MSFT", "success", 1)


def test_segment_financials_supports_both_period_types(tmp_duckdb):
    tmp_duckdb.execute(
        """
        INSERT INTO segment_financials (
            ticker, fiscal_year, period_type, fiscal_quarter,
            period_end, segment_name, segment_revenue_usd
        ) VALUES
            ('MSFT', 2024, 'quarterly', 3, DATE '2024-09-30', 'Azure', 25000000000),
            ('MSFT', 2024, 'annual', NULL, DATE '2024-06-30', 'Azure', 100000000000)
        """
    )
    rows = tmp_duckdb.execute(
        "SELECT period_type, fiscal_quarter FROM segment_financials "
        "WHERE ticker='MSFT' ORDER BY period_type"
    ).fetchall()
    assert rows == [('annual', None), ('quarterly', 3)]


def test_geographic_revenue_supports_both_period_types(tmp_duckdb):
    tmp_duckdb.execute(
        """
        INSERT INTO geographic_revenue (
            ticker, fiscal_year, period_type, fiscal_quarter,
            period_end, region_name, revenue_usd
        ) VALUES
            ('MSFT', 2024, 'quarterly', 3, DATE '2024-09-30', 'Americas', 30000000000),
            ('MSFT', 2024, 'annual', NULL, DATE '2024-06-30', 'Americas', 120000000000)
        """
    )
    rows = tmp_duckdb.execute(
        "SELECT period_type, fiscal_quarter FROM geographic_revenue "
        "WHERE ticker='MSFT' ORDER BY period_type"
    ).fetchall()
    assert rows == [('annual', None), ('quarterly', 3)]


def test_segment_financials_rejects_quarterly_with_null_quarter(tmp_duckdb):
    with pytest.raises(duckdb.Error):
        tmp_duckdb.execute(
            """
            INSERT INTO segment_financials (
                ticker, fiscal_year, period_type, fiscal_quarter,
                period_end, segment_name, segment_revenue_usd
            ) VALUES ('MSFT', 2024, 'quarterly', NULL, DATE '2024-09-30', 'Azure', 1)
            """
        )


def test_segment_financials_rejects_annual_with_quarter(tmp_duckdb):
    with pytest.raises(duckdb.Error):
        tmp_duckdb.execute(
            """
            INSERT INTO segment_financials (
                ticker, fiscal_year, period_type, fiscal_quarter,
                period_end, segment_name, segment_revenue_usd
            ) VALUES ('MSFT', 2024, 'annual', 3, DATE '2024-06-30', 'Azure', 1)
            """
        )


def test_geographic_revenue_rejects_quarterly_with_null_quarter(tmp_duckdb):
    with pytest.raises(duckdb.Error):
        tmp_duckdb.execute(
            """
            INSERT INTO geographic_revenue (
                ticker, fiscal_year, period_type, fiscal_quarter,
                period_end, region_name, revenue_usd
            ) VALUES ('MSFT', 2024, 'quarterly', NULL, DATE '2024-09-30', 'Americas', 1)
            """
        )


def test_geographic_revenue_rejects_annual_with_quarter(tmp_duckdb):
    with pytest.raises(duckdb.Error):
        tmp_duckdb.execute(
            """
            INSERT INTO geographic_revenue (
                ticker, fiscal_year, period_type, fiscal_quarter,
                period_end, region_name, revenue_usd
            ) VALUES ('MSFT', 2024, 'annual', 3, DATE '2024-06-30', 'Americas', 1)
            """
        )
