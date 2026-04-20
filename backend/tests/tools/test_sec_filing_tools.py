"""Tests for sec_filing_list_sections tool."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest

from backend.common.sec_core import (
    TickerNotFoundError,
    _fetch_filing_obj_cached,
    _resolve_latest_fiscal_year_cached,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

NON_STUB_TEXT = "This is a real section with substantive content that is not a stub. " * 50
STUB_TEXT = (
    "The information required by this Item is incorporated herein by reference "
    "from the Company's 2026 Proxy Statement."
)


def _tool_call(tool_func, args: dict) -> dict:
    """Invoke a tool with a ToolCall envelope (required for InjectedToolCallId)."""
    msg = tool_func.invoke(
        {
            "args": args,
            "name": tool_func.name,
            "type": "tool_call",
            "id": "test-call-id",
        }
    )
    return json.loads(msg.content)


def _make_section(item: str | None, text: str, name: str = "") -> MagicMock:
    s = MagicMock()
    s.item = item
    s.text.return_value = text
    s.name = name or f"item_{item}"
    return s


def _make_tenk(sections: dict[str, MagicMock], period: str = "2025-09-27") -> MagicMock:
    tenk = MagicMock()
    tenk.document.sections = sections
    tenk.period_of_report = period
    tenk.filing_date = "2025-11-01"
    tenk.company.name = "Apple Inc."
    return tenk


# ---------------------------------------------------------------------------
# Autouse cache-clearing (mirrors backend/tests/common/conftest.py)
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def _clear_caches():
    _fetch_filing_obj_cached.cache_clear()
    _resolve_latest_fiscal_year_cached.cache_clear()
    yield
    _fetch_filing_obj_cached.cache_clear()
    _resolve_latest_fiscal_year_cached.cache_clear()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_list_sections_canonical_order():
    """Sections in output must follow TENK_STANDARD_TITLES key order regardless
    of the dict iteration order from tenk.document.sections."""
    from backend.agent_engine.tools.sec_filing_tools import sec_filing_list_sections
    from backend.common.sec_core import TENK_STANDARD_TITLES

    # Provide sections in deliberately scrambled order: 7, 1a, 1
    scrambled = {
        "item 7": _make_section("7", NON_STUB_TEXT, "item_7"),
        "item 1a": _make_section("1a", NON_STUB_TEXT, "item_1a"),
        "item 1": _make_section("1", NON_STUB_TEXT, "item_1"),
    }
    tenk = _make_tenk(scrambled)

    with (
        patch("backend.agent_engine.tools.sec_filing_tools.fetch_filing_obj", return_value=tenk),
        patch("backend.agent_engine.tools.sec_filing_tools._resolve_latest_fiscal_year", return_value=2025),
        patch("backend.agent_engine.tools.sec_filing_tools.get_stream_writer", side_effect=RuntimeError("no writer")),
    ):
        result = _tool_call(sec_filing_list_sections, {"ticker": "AAPL", "fiscal_year": 2025})

    keys_in_output = [s["key"] for s in result["sections"]]
    canonical_keys = [k for k in TENK_STANDARD_TITLES if k in {"1", "1a", "7"}]
    assert keys_in_output == canonical_keys


def test_list_sections_output_schema():
    """Output must contain resolved fiscal_year, ISO period_of_report, non-empty company_name."""
    from backend.agent_engine.tools.sec_filing_tools import sec_filing_list_sections

    tenk = _make_tenk(
        {"item 1": _make_section("1", NON_STUB_TEXT)},
        period="2025-09-27",
    )

    with (
        patch("backend.agent_engine.tools.sec_filing_tools.fetch_filing_obj", return_value=tenk),
        patch("backend.agent_engine.tools.sec_filing_tools._resolve_latest_fiscal_year", return_value=2025),
        patch("backend.agent_engine.tools.sec_filing_tools.get_stream_writer", side_effect=RuntimeError("no writer")),
    ):
        result = _tool_call(sec_filing_list_sections, {"ticker": "AAPL", "fiscal_year": 2025})

    assert result["fiscal_year"] == 2025
    assert result["period_of_report"] == "2025-09-27"
    assert result["company_name"] and result["company_name"] != ""
    assert result["ticker"] == "AAPL"
    assert result["doc_type"] == "10-K"


def test_list_sections_stub_flag_optional_on_wire():
    """Non-stub entries must have exactly {key, char_count}; stub entries must
    have exactly {key, char_count, is_stub, stub_reason}."""
    from backend.agent_engine.tools.sec_filing_tools import sec_filing_list_sections

    sections = {
        "item 1a": _make_section("1a", NON_STUB_TEXT),
        "item 2": _make_section("2", NON_STUB_TEXT),
        "item 11": _make_section("11", STUB_TEXT),
    }
    tenk = _make_tenk(sections)

    with (
        patch("backend.agent_engine.tools.sec_filing_tools.fetch_filing_obj", return_value=tenk),
        patch("backend.agent_engine.tools.sec_filing_tools._resolve_latest_fiscal_year", return_value=2025),
        patch("backend.agent_engine.tools.sec_filing_tools.get_stream_writer", side_effect=RuntimeError("no writer")),
    ):
        result = _tool_call(sec_filing_list_sections, {"ticker": "AAPL", "fiscal_year": 2025})

    by_key = {s["key"]: s for s in result["sections"]}

    # Non-stub: only key + char_count
    for k in ("1a", "2"):
        assert set(by_key[k].keys()) == {"key", "char_count"}, (
            f"Non-stub section {k!r} has unexpected keys: {by_key[k].keys()}"
        )

    # Stub: key + char_count + is_stub + stub_reason
    assert set(by_key["11"].keys()) == {"key", "char_count", "is_stub", "stub_reason"}, (
        f"Stub section '11' has unexpected keys: {by_key['11'].keys()}"
    )
    assert by_key["11"]["is_stub"] is True
    assert by_key["11"]["stub_reason"]


def test_list_sections_stream_event_resolved_fy():
    """Stream event message must contain ticker and FY<int> (not FYNone)."""
    from backend.agent_engine.tools.sec_filing_tools import sec_filing_list_sections

    tenk = _make_tenk(
        {"item 1": _make_section("1", NON_STUB_TEXT)},
        period="2025-09-27",
    )
    captured_events: list[dict] = []
    mock_writer = MagicMock(side_effect=lambda evt: captured_events.append(evt))

    with (
        patch("backend.agent_engine.tools.sec_filing_tools.fetch_filing_obj", return_value=tenk),
        patch("backend.agent_engine.tools.sec_filing_tools._resolve_latest_fiscal_year", return_value=2025),
        patch("backend.agent_engine.tools.sec_filing_tools.get_stream_writer", return_value=mock_writer),
    ):
        _tool_call(sec_filing_list_sections, {"ticker": "aapl", "fiscal_year": None})

    assert len(captured_events) == 1
    evt = captured_events[0]
    assert evt["status"] == "listing_sections"
    assert "AAPL" in evt["message"]
    assert "FY2025" in evt["message"]
    assert "FYNone" not in evt["message"]
    assert evt["toolName"] == "sec_filing_list_sections"
    assert evt["toolCallId"]  # non-empty


def test_list_sections_uses_metadata_only_fy_resolve():
    """When fiscal_year=None, fetch_filing_obj must be called with a resolved int,
    never with None."""
    from backend.agent_engine.tools.sec_filing_tools import sec_filing_list_sections

    tenk = _make_tenk(
        {"item 1": _make_section("1", NON_STUB_TEXT)},
    )

    with (
        patch("backend.agent_engine.tools.sec_filing_tools.fetch_filing_obj", return_value=tenk) as mock_fetch,
        patch("backend.agent_engine.tools.sec_filing_tools._resolve_latest_fiscal_year", return_value=2025),
        patch("backend.agent_engine.tools.sec_filing_tools.get_stream_writer", side_effect=RuntimeError("no writer")),
    ):
        _tool_call(sec_filing_list_sections, {"ticker": "AAPL", "fiscal_year": None})

    call_kwargs = mock_fetch.call_args
    # fetch_filing_obj(ticker_upper, FilingType(doc_type), resolved_fy)
    passed_fy = call_kwargs.args[2] if len(call_kwargs.args) >= 3 else call_kwargs.kwargs.get("fiscal_year")
    assert passed_fy is not None
    assert isinstance(passed_fy, int)


def test_list_sections_raises_ticker_not_found():
    """TickerNotFoundError from _resolve_latest_fiscal_year must propagate;
    stream event must NOT have been emitted (error before fetch)."""
    from backend.agent_engine.tools.sec_filing_tools import sec_filing_list_sections

    captured_events: list[dict] = []
    mock_writer = MagicMock(side_effect=lambda evt: captured_events.append(evt))

    with (
        patch(
            "backend.agent_engine.tools.sec_filing_tools._resolve_latest_fiscal_year",
            side_effect=TickerNotFoundError("ZZZZ not found"),
        ),
        patch("backend.agent_engine.tools.sec_filing_tools.get_stream_writer", return_value=mock_writer),
    ):
        with pytest.raises(TickerNotFoundError):
            # Use .func to bypass LangChain tool wrapper which catches exceptions
            inner = getattr(sec_filing_list_sections, "func", sec_filing_list_sections)
            inner(ticker="ZZZZ", tool_call_id="test-call-id", fiscal_year=None)

    # No stream event should have been emitted since error occurred before emit point
    assert len(captured_events) == 0


def test_list_sections_observe_span_name():
    """The @observe decorator must be applied: inner func has __wrapped__."""
    from backend.agent_engine.tools.sec_filing_tools import sec_filing_list_sections

    inner = getattr(sec_filing_list_sections, "func", sec_filing_list_sections)
    assert hasattr(inner, "__wrapped__"), (
        "sec_filing_list_sections inner func is missing @observe() decorator (__wrapped__)"
    )
