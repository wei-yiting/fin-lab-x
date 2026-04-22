import pytest
from backend.ingestion.quant_data_pipeline.duck_db.connection import get_connection


@pytest.fixture
def tmp_duckdb(tmp_path):
    db_path = tmp_path / "test.db"
    conn = get_connection(str(db_path), ensure_schema=True)
    try:
        yield conn
    finally:
        conn.close()
