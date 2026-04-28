"""SEC EDGAR integration smoke tests for sec_filing_* tools.

These tests hit the real SEC EDGAR API. Per SEC's stated policy, EDGAR
enforces a 10 req/s rate limit; pytest's default sequential execution
(no -n / xdist parallelism) keeps us well under that bound.

Tests are excluded from the default pytest run via `pyproject.toml`
`addopts = "-m 'not eval and not sec_integration'"` and only execute
when the `sec_integration` marker is explicitly selected.

POST-CODING / staleness notes:
- `expected_fy` constants are accurate as of 2026-04-20:
    - AAPL fiscal year ends late September; latest filed FY = 2025
    - MSFT fiscal year ends late June;     latest filed FY = 2025
    - NVDA fiscal year ends late January;  latest filed FY = 2025
- After AAPL/MSFT/NVDA file their next 10-K, these constants need to be
  bumped (do NOT loosen the assertion to >= — strict equality keeps the
  test honest about what EDGAR is currently serving).
"""

from __future__ import annotations

import json
import os
import re
from typing import Any

import pytest

from backend.common.sec_core import (
    _fetch_filing_obj_cached,
    _resolve_latest_fiscal_year_cached,
)


# ---------------------------------------------------------------------------
# Marker — applied to every test in this module
# ---------------------------------------------------------------------------

pytestmark = pytest.mark.sec_integration


# ---------------------------------------------------------------------------
# ISO date matcher
# ---------------------------------------------------------------------------

_ISO_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


# ---------------------------------------------------------------------------
# Autouse fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _require_edgar_identity():
    """Skip the test if EDGAR_IDENTITY is not configured.

    edgartools requires EDGAR_IDENTITY to identify the requester per SEC
    policy. Without it, calls would either fail or hit the SEC under an
    anonymous identity, which is non-conformant.
    """
    if not os.getenv("EDGAR_IDENTITY"):
        pytest.skip("EDGAR_IDENTITY not set")


@pytest.fixture(autouse=True)
def _clear_caches():
    """Clear the LRU caches before AND after each test so cache_info()
    assertions in cache-behavior tests reflect only the current test's
    activity (no carry-over from prior tests, no leakage to next test).
    """
    _fetch_filing_obj_cached.cache_clear()
    _resolve_latest_fiscal_year_cached.cache_clear()
    yield
    _fetch_filing_obj_cached.cache_clear()
    _resolve_latest_fiscal_year_cached.cache_clear()


# ---------------------------------------------------------------------------
# Tool invocation helper (mirrors backend/tests/tools/test_sec_filing_tools.py)
# ---------------------------------------------------------------------------


def _tool_call(tool_func, args: dict[str, Any]) -> dict[str, Any]:
    """Invoke a LangChain tool with a ToolCall envelope (required for
    InjectedToolCallId), then parse the JSON content and return the dict.
    """
    msg = tool_func.invoke(
        {
            "args": args,
            "name": tool_func.name,
            "type": "tool_call",
            "id": "integration-test-id",
        }
    )
    return json.loads(msg.content)


# ---------------------------------------------------------------------------
# Test 1: list_sections returns correct top-level metadata (S-sec-02)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "ticker,expected_fy",
    [
        ("AAPL", 2025),  # AAPL fiscal year ends in September
        ("MSFT", 2025),  # MSFT fiscal year ends in June
        ("NVDA", 2025),  # NVDA fiscal year ends in January
    ],
)
def test_list_sections_metadata(ticker: str, expected_fy: int) -> None:
    """S-sec-02: real EDGAR returns ticker / fiscal_year / period_of_report
    / filing_date / company_name / sections in the expected wire shape."""
    from backend.agent_engine.tools.sec_filing_tools import sec_filing_list_sections

    result = _tool_call(
        sec_filing_list_sections,
        {"ticker": ticker, "fiscal_year": expected_fy},
    )

    assert result["ticker"] == ticker
    assert result["fiscal_year"] == expected_fy, (
        f"{ticker} latest FY drift detected — got {result['fiscal_year']!r}, "
        f"expected {expected_fy}. If a newer 10-K has been filed, bump the "
        f"expected_fy constant rather than loosening this assertion."
    )

    period = result["period_of_report"]
    assert isinstance(period, str) and _ISO_DATE_RE.match(period), (
        f"period_of_report must be ISO 'YYYY-MM-DD'; got {period!r}"
    )

    filing_date = result["filing_date"]
    assert filing_date is not None, "filing_date must not be None"
    assert isinstance(filing_date, str) and _ISO_DATE_RE.match(filing_date), (
        f"filing_date must be ISO 'YYYY-MM-DD'; got {filing_date!r}"
    )

    assert isinstance(result["company_name"], str) and result["company_name"]
    assert isinstance(result["sections"], list) and len(result["sections"]) > 0

    for section in result["sections"]:
        assert "key" in section, f"section missing 'key': {section!r}"
        assert "char_count" in section, f"section missing 'char_count': {section!r}"


# ---------------------------------------------------------------------------
# Test 2: AAPL Item 10 is a stub (S-sec-03)
# ---------------------------------------------------------------------------


def test_list_sections_stub_marker_aapl() -> None:
    """S-sec-03: AAPL Items 10 and 11 are both incorporated by reference
    from the proxy statement and must surface as is_stub=True.

    Both items historically posed different problems: Item 11 used to bleed
    Items 12/13/14 content into its body via edgartools' section detection,
    pushing it past the stub threshold. ``trim_text_to_item_boundary`` now
    cuts the body at the next item heading, so Item 11 is recognized as a
    stub as well as Item 10.
    """
    from backend.agent_engine.tools.sec_filing_tools import sec_filing_list_sections

    result = _tool_call(
        sec_filing_list_sections,
        {"ticker": "AAPL", "fiscal_year": 2025},
    )

    for key in ("10", "11"):
        section = next((s for s in result["sections"] if s["key"] == key), None)
        assert section is not None, (
            f"AAPL FY2025 must list a section with key {key!r}"
        )
        assert section.get("is_stub") is True, (
            f"Item {key} must be flagged is_stub=True; got {section!r}"
        )
        reason = (section.get("stub_reason") or "").lower()
        assert "proxy" in reason or "incorporated" in reason, (
            f"Item {key} stub_reason should reference 'proxy' or 'incorporated'; "
            f"got {section.get('stub_reason')!r}"
        )


def test_get_section_does_not_bleed_into_next_item_aapl() -> None:
    """``get_section("11")`` must return Item 11 body only — not the bleed
    that edgartools' section detection produces (Items 12/13/14 content
    appended to Item 11 in AAPL FY2025).
    """
    from backend.agent_engine.tools.sec_filing_tools import sec_filing_get_section

    result = _tool_call(
        sec_filing_get_section,
        {"ticker": "AAPL", "fiscal_year": 2025, "section_key": "11"},
    )

    content = result["content"]
    assert "Item 11" in content, "Item 11 body must include its own heading"
    # The bleed signature: Items 12/13/14 headings appearing inside what
    # should be Item 11 alone.
    for next_heading in ("Item 12.", "Item 13.", "Item 14."):
        assert next_heading not in content, (
            f"get_section('11') content must not contain {next_heading!r} — "
            f"trim_text_to_item_boundary should cut the bleed"
        )


# ---------------------------------------------------------------------------
# Test 3: char_count from list_sections matches len(content) from get_section (S-sec-06)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "ticker,fy,section_key",
    [
        ("AAPL", 2025, "1a"),
        ("AAPL", 2025, "4"),
        ("MSFT", 2025, "7"),
    ],
)
def test_content_length_matches_char_count(
    ticker: str, fy: int, section_key: str
) -> None:
    """S-sec-06: char_count reported by list_sections must equal
    len(content) returned by get_section for the same key."""
    from backend.agent_engine.tools.sec_filing_tools import (
        sec_filing_get_section,
        sec_filing_list_sections,
    )

    list_result = _tool_call(
        sec_filing_list_sections,
        {"ticker": ticker, "fiscal_year": fy},
    )
    section_entry = next(
        (s for s in list_result["sections"] if s["key"] == section_key), None
    )
    assert section_entry is not None, (
        f"{ticker} FY{fy} list_sections did not return key {section_key!r}; "
        f"available keys: {[s['key'] for s in list_result['sections']]}"
    )
    expected_char_count = section_entry["char_count"]

    get_result = _tool_call(
        sec_filing_get_section,
        {"ticker": ticker, "section_key": section_key, "fiscal_year": fy},
    )

    assert len(get_result["content"]) == expected_char_count, (
        f"len(content)={len(get_result['content'])} but list_sections reported "
        f"char_count={expected_char_count} for {ticker} FY{fy} item {section_key!r}"
    )


# ---------------------------------------------------------------------------
# Test 4: J-sec-01 happy path — list + get 1A on AAPL
# ---------------------------------------------------------------------------


def test_journey_happy_path_aapl() -> None:
    """J-sec-01: list (resolve latest FY) + get Item 1A; period_of_report
    must agree across calls and the second call must hit the filing cache."""
    from backend.agent_engine.tools.sec_filing_tools import (
        sec_filing_get_section,
        sec_filing_list_sections,
    )

    list_out = _tool_call(sec_filing_list_sections, {"ticker": "AAPL"})

    item_1a = next((s for s in list_out["sections"] if s["key"] == "1a"), None)
    assert item_1a is not None, "AAPL list_sections must return key '1a'"
    list_1a_char_count = item_1a["char_count"]

    get_out = _tool_call(
        sec_filing_get_section,
        {
            "ticker": "AAPL",
            "section_key": "1a",
            "fiscal_year": list_out["fiscal_year"],
        },
    )

    assert list_out["period_of_report"] == get_out["period_of_report"], (
        "list_sections and get_section must return the same period_of_report "
        "for the same resolved filing"
    )
    assert list_1a_char_count == len(get_out["content"]), (
        f"char_count mismatch: list={list_1a_char_count}, "
        f"get_len={len(get_out['content'])}"
    )

    cache_info = _fetch_filing_obj_cached.cache_info()
    assert cache_info.hits >= 1, (
        f"_fetch_filing_obj_cached must have at least 1 hit on the second "
        f"call (get_section reusing the cached TenK); cache_info={cache_info}"
    )


# ---------------------------------------------------------------------------
# Test 5: J-sec-03 multi-section caching — list + 3 gets on MSFT
# ---------------------------------------------------------------------------


def test_journey_multi_section_cache_msft() -> None:
    """J-sec-03: list + 3 get_sections on MSFT; verify all four responses
    share the same period_of_report and the LRU caches behave per the
    metadata-only FY-resolve strategy from Task 6.

    Expected cache trace:
      - list_sections(MSFT, None)      → resolve_fy MISS, fetch MISS
      - get_section(MSFT, '1a', fy)    → fetch HIT  (resolve_fy not called: explicit fy)
      - get_section(MSFT, '7',  fy)    → fetch HIT
      - get_section(MSFT, '7a', fy)    → fetch HIT
    """
    from backend.agent_engine.tools.sec_filing_tools import (
        sec_filing_get_section,
        sec_filing_list_sections,
    )

    list_out = _tool_call(sec_filing_list_sections, {"ticker": "MSFT"})
    resolved_fy = list_out["fiscal_year"]
    base_period = list_out["period_of_report"]

    get_periods: list[str] = []
    for section_key in ("1a", "7", "7a"):
        get_out = _tool_call(
            sec_filing_get_section,
            {
                "ticker": "MSFT",
                "section_key": section_key,
                "fiscal_year": resolved_fy,
            },
        )
        get_periods.append(get_out["period_of_report"])

    for idx, period in enumerate(get_periods, start=1):
        assert period == base_period, (
            f"period_of_report drift on get #{idx}: {period!r} vs base "
            f"{base_period!r} — all four responses must reference the same filing"
        )

    fetch_info = _fetch_filing_obj_cached.cache_info()
    assert fetch_info.misses == 1, (
        f"_fetch_filing_obj_cached.misses expected 1 (only the list call "
        f"populates the cache); got {fetch_info}"
    )
    assert fetch_info.hits >= 3, (
        f"_fetch_filing_obj_cached.hits expected >= 3 (3 get calls reuse the "
        f"cached TenK); got {fetch_info}"
    )

    resolve_info = _resolve_latest_fiscal_year_cached.cache_info()
    assert resolve_info.misses == 1, (
        f"_resolve_latest_fiscal_year_cached.misses expected 1 (only the "
        f"first list call resolves latest FY); got {resolve_info}"
    )
    assert resolve_info.hits == 0, (
        f"_resolve_latest_fiscal_year_cached.hits expected 0 (subsequent "
        f"calls pass explicit fiscal_year and skip resolve); got {resolve_info}"
    )
