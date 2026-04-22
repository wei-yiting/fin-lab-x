import json

import pytest

from backend.ingestion.quant_data_pipeline.quant_ingestion_runs import ingestion_run
from backend.ingestion.quant_data_pipeline.quant_pipeline_errors import TickerNotFoundError


def test_success_path(tmp_duckdb):
    with ingestion_run(tmp_duckdb, "yfinance", "NVDA") as report:
        report.rows_written_total = 5
        report.metadata["periods_covered"] = {"quarterly": ["2025Q3"]}

    row = tmp_duckdb.execute(
        "SELECT pipeline, ticker, status, rows_written_total, error_class, started_at, finished_at, metadata FROM ingestion_runs"
    ).fetchone()
    assert row is not None
    pipeline, ticker, status, n_rows, err_class, started_at, finished_at, meta = row
    assert (pipeline, ticker, status, n_rows) == ("yfinance", "NVDA", "success", 5)
    assert err_class is None
    assert started_at <= finished_at
    parsed_meta = json.loads(meta)
    assert parsed_meta["periods_covered"] == {"quarterly": ["2025Q3"]}


def test_error_path(tmp_duckdb):
    with pytest.raises(TickerNotFoundError, match="NVDA not found"):
        with ingestion_run(tmp_duckdb, "yfinance", "NVDA") as _:
            raise TickerNotFoundError("NVDA not found")

    row = tmp_duckdb.execute(
        "SELECT status, error_class, error_message, rows_written_total FROM ingestion_runs"
    ).fetchone()
    assert row is not None
    assert row == ("error", "TickerNotFoundError", "NVDA not found", 0)


def test_partial_metadata_preserved_on_error(tmp_duckdb):
    with pytest.raises(RuntimeError, match="boom"):
        with ingestion_run(tmp_duckdb, "yfinance", "NVDA") as report:
            report.rows_written_total = 3
            report.metadata["api_latency_ms"] = {"info": 120}
            raise RuntimeError("boom")

    row = tmp_duckdb.execute(
        "SELECT rows_written_total, metadata FROM ingestion_runs"
    ).fetchone()
    assert row is not None
    assert row[0] == 3
    parsed_meta = json.loads(row[1])
    assert parsed_meta["api_latency_ms"] == {"info": 120}


def test_sec_only_kwargs(tmp_duckdb):
    with ingestion_run(
        tmp_duckdb,
        "sec_xbrl",
        "NVDA",
        target_filing_type="10-K",
        target_fiscal_year=2024,
        target_accession_number="0001045810-24-000316",
    ):
        pass

    row = tmp_duckdb.execute(
        "SELECT target_filing_type, target_fiscal_year, target_accession_number FROM ingestion_runs"
    ).fetchone()
    assert row == ("10-K", 2024, "0001045810-24-000316")


def test_distinct_run_ids(tmp_duckdb):
    with ingestion_run(tmp_duckdb, "yfinance", "AAPL"):
        pass
    with ingestion_run(tmp_duckdb, "yfinance", "MSFT"):
        pass

    count = tmp_duckdb.execute(
        "SELECT COUNT(DISTINCT run_id) FROM ingestion_runs"
    ).fetchone()[0]
    assert count == 2
