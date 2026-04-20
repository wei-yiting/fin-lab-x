import pytest

from backend.common.sec_core import (
    _resolve_latest_fiscal_year,
    fetch_filing_obj,
)


@pytest.fixture(autouse=True)
def _clear_sec_core_caches():
    fetch_filing_obj.cache_clear()
    _resolve_latest_fiscal_year.cache_clear()
    yield
    fetch_filing_obj.cache_clear()
    _resolve_latest_fiscal_year.cache_clear()
