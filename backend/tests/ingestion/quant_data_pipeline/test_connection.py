from pathlib import Path

import duckdb
import pytest

from backend.ingestion.quant_data_pipeline.duck_db import connection as connection_module
from backend.ingestion.quant_data_pipeline.duck_db.connection import get_connection
from backend.ingestion.quant_data_pipeline.quant_pipeline_errors import SchemaError

EXPECTED_TABLES = {
    "companies",
    "market_valuations",
    "quarterly_financials",
    "annual_financials",
    "segment_financials",
    "geographic_revenue",
    "customer_concentration",
    "ingestion_runs",
}


def test_normal_path(tmp_path):
    db_path = tmp_path / "x.db"
    conn = get_connection(str(db_path))
    try:
        result = conn.execute("SELECT 1").fetchone()
        assert result == (1,)
        assert db_path.exists()
    finally:
        conn.close()


def test_ensure_schema_true_creates_all_tables(tmp_path):
    db_path = tmp_path / "schema.db"
    conn = get_connection(str(db_path), ensure_schema=True)
    try:
        row = conn.execute(
            "SELECT count(*) FROM duckdb_tables() WHERE table_name='companies'"
        ).fetchone()
        assert row is not None and row[0] == 1

        actual_tables = {
            row[0]
            for row in conn.execute("SELECT table_name FROM duckdb_tables()").fetchall()
        }
        assert EXPECTED_TABLES.issubset(actual_tables)
    finally:
        conn.close()


def test_ensure_schema_false_skips_bootstrap(tmp_path):
    db_path = tmp_path / "empty.db"
    conn = get_connection(str(db_path), ensure_schema=False)
    try:
        tables = conn.execute("SELECT table_name FROM duckdb_tables()").fetchall()
        assert tables == []
    finally:
        conn.close()


def test_env_var_fallback(tmp_path, monkeypatch):
    target_path = str(tmp_path / "env_fallback.db")
    monkeypatch.setenv("DUCKDB_PATH", target_path)
    conn = get_connection()
    try:
        conn.execute("SELECT 1")
    finally:
        conn.close()
    assert Path(target_path).exists()


def test_schema_error_missing_file(tmp_path, monkeypatch):
    missing = tmp_path / "no_such_file.sql"
    monkeypatch.setattr(connection_module, "_SCHEMA_SQL_PATH", missing)
    with pytest.raises(SchemaError, match="missing"):
        get_connection(str(tmp_path / "err.db"), ensure_schema=True)


def test_schema_error_invalid_sql(tmp_path, monkeypatch):
    bad_sql = tmp_path / "bad.sql"
    bad_sql.write_text("NOT A VALID SQL STATEMENT;")
    monkeypatch.setattr(connection_module, "_SCHEMA_SQL_PATH", bad_sql)
    with pytest.raises(SchemaError, match="Failed to apply") as excinfo:
        get_connection(str(tmp_path / "err2.db"), ensure_schema=True)
    assert isinstance(excinfo.value.__cause__, duckdb.Error)
