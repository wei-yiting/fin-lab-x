"""Shared pytest fixtures for the fundamentals pipeline foundation tests.

Subsystem test packages (yfinance, SEC XBRL) can reuse ``tmp_duckdb`` across
package boundaries either by adding to their own ``conftest.py``::

    pytest_plugins = ["backend.tests.ingestion.fundamentals_pipeline.conftest"]

or by importing the fixture directly::

    from backend.tests.ingestion.fundamentals_pipeline.conftest import tmp_duckdb
"""

import pytest

from backend.ingestion.fundamentals_pipeline.duck_db.connection import get_connection


@pytest.fixture
def tmp_duckdb(tmp_path):
    db_path = tmp_path / "test.db"
    conn = get_connection(str(db_path), ensure_schema=True)
    try:
        yield conn
    finally:
        conn.close()
