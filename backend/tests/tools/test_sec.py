"""Tests for SEC tools."""

import os
import sys
from unittest.mock import MagicMock, patch

import pytest
from pydantic import ValidationError

from backend.agent_engine.tools.sec import (
    MAX_SECTION_CHARS,
    _extract_section,
    sec_official_docs_retriever,
)


def test_sec_tool_exists():
    assert sec_official_docs_retriever is not None
    assert hasattr(sec_official_docs_retriever, "invoke")


def test_sec_tool_schema_validation():
    with pytest.raises(ValidationError):
        sec_official_docs_retriever.invoke({"doc_type": "10-K"})


def test_extract_section_returns_section_between_markers():
    text = "Item 1A Risk Factors details. Item 1B Next section."
    result = _extract_section(text, ["Item 1A"], ["Item 1B"])

    assert result == "Item 1A Risk Factors details."


def test_extract_section_truncates_long_section():
    long_body = "A" * (MAX_SECTION_CHARS + 20)
    text = f"Item 1A {long_body} Item 1B End"
    result = _extract_section(text, ["Item 1A"], ["Item 1B"])

    assert result is not None
    assert result.endswith("...")
    assert len(result) <= MAX_SECTION_CHARS + 3


def test_extract_section_returns_none_when_missing_markers():
    text = "No matching content here."
    result = _extract_section(text, ["Item 1A"], ["Item 1B"])

    assert result is None


def test_sec_official_docs_retriever_missing_identity():
    with patch.dict(os.environ, {}, clear=True):
        result = sec_official_docs_retriever.invoke(
            {"ticker": "AAPL", "doc_type": "10-K"}
        )

    assert result["error"] is True
    assert "EDGAR_IDENTITY" in result["message"]


@patch.dict(os.environ, {"EDGAR_IDENTITY": "test@test.com"}, clear=True)
@patch.dict("sys.modules", {"edgar": MagicMock()})
@patch("backend.agent_engine.tools.sec.Company", create=True)
@patch("backend.agent_engine.tools.sec.set_identity", create=True)
def test_sec_official_docs_retriever_no_filing_found(set_identity_mock, company_mock):
    edgar_module = sys.modules["edgar"]
    setattr(edgar_module, "Company", company_mock)
    setattr(edgar_module, "set_identity", set_identity_mock)
    filings_mock = MagicMock()
    filings_mock.latest.return_value = None
    company_mock.return_value.get_filings.return_value = filings_mock

    result = sec_official_docs_retriever.invoke({"ticker": "aapl", "doc_type": "10-K"})

    assert result["error"] is True
    assert "No 10-K filing found" in result["message"]
    company_mock.assert_called_once_with("AAPL")


@patch.dict(os.environ, {"EDGAR_IDENTITY": "test@test.com"}, clear=True)
@patch.dict("sys.modules", {"edgar": MagicMock()})
@patch("backend.agent_engine.tools.sec.Company", create=True)
@patch("backend.agent_engine.tools.sec.set_identity", create=True)
def test_sec_official_docs_retriever_returns_sections(set_identity_mock, company_mock):
    edgar_module = sys.modules["edgar"]
    setattr(edgar_module, "Company", company_mock)
    setattr(edgar_module, "set_identity", set_identity_mock)
    filing_text = (
        "Item 1A Risk Factors content. "
        "Item 1B Next section. "
        "Item 7 MD&A content. "
        "Item 8 Financial statements."
    )
    filing_mock = MagicMock()
    filing_mock.text.return_value = filing_text
    filing_mock.filing_date = "2024-01-01"
    filings_mock = MagicMock()
    filings_mock.latest.return_value = filing_mock
    company_mock.return_value.get_filings.return_value = filings_mock

    result = sec_official_docs_retriever.invoke({"ticker": "aapl", "doc_type": "10-K"})

    assert result["ticker"] == "AAPL"
    assert result["doc_type"] == "10-K"
    assert result["filing_date"] == "2024-01-01"
    assert "Item 1A" in result["risk_factors"]
    assert "Item 7" in result["mdna"]
    assert result["raw_excerpt"].endswith("...")
