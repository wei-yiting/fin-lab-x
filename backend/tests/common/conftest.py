import pytest

from backend.common.sec_core import (
    _fetch_filing_bundle_cached,
    _fetch_filing_markdown_cached,
    _fetch_filing_obj_cached,
    _locate_filing_cached,
    _resolve_latest_fiscal_year_cached,
)

_SEC_CORE_CACHES = (
    _fetch_filing_bundle_cached,
    _fetch_filing_markdown_cached,
    _fetch_filing_obj_cached,
    _locate_filing_cached,
    _resolve_latest_fiscal_year_cached,
)


@pytest.fixture(autouse=True)
def _clear_sec_core_caches():
    for cache in _SEC_CORE_CACHES:
        cache.cache_clear()
    yield
    for cache in _SEC_CORE_CACHES:
        cache.cache_clear()
