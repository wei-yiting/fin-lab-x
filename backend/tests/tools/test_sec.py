"""Tests for SEC tools."""

from backend.agent_engine.tools.sec import sec_official_docs_retriever


def test_sec_tool_exists():
    """Test SEC tool can be imported."""
    assert sec_official_docs_retriever is not None
    assert hasattr(sec_official_docs_retriever, "invoke")
