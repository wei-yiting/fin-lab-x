import pytest

from backend.common.sec_core import (
    _fetch_filing_obj_cached,
    _resolve_latest_fiscal_year_cached,
)


@pytest.fixture(autouse=True)
def _clear_sec_core_caches():
    _fetch_filing_obj_cached.cache_clear()
    _resolve_latest_fiscal_year_cached.cache_clear()
    yield
    _fetch_filing_obj_cached.cache_clear()
    _resolve_latest_fiscal_year_cached.cache_clear()
