"""Shared fixtures for yfinance subsystem tests.

The parent ``conftest.py`` at ``backend/tests/ingestion/quant_data_pipeline/``
is auto-discovered by pytest, so its ``tmp_duckdb`` fixture is already
available here — no ``pytest_plugins`` re-registration needed (and adding it
collides with pytest's plugin registry).
"""

import pytest

from backend.ingestion.quant_data_pipeline.yfinance import yfinance_client


@pytest.fixture(autouse=True)
def _reset_pacing():
    """Reset module-level pacing counters around every test."""
    yfinance_client.reset_pacing_stats()
    yield
    yfinance_client.reset_pacing_stats()
