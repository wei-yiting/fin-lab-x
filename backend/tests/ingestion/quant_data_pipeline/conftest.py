"""Shared pytest fixtures for the quant data pipeline foundation tests.

Subsystem test packages (yfinance, SEC XBRL) can reuse ``tmp_duckdb`` across
package boundaries either by adding to their own ``conftest.py``::

    pytest_plugins = ["backend.tests.ingestion.quant_data_pipeline.conftest"]

or by importing the fixture directly::

    from backend.tests.ingestion.quant_data_pipeline.conftest import tmp_duckdb
"""

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
