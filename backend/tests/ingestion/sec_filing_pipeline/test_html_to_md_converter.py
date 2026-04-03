from __future__ import annotations

from unittest.mock import patch

import pytest

from backend.ingestion.sec_filing_pipeline.html_to_md_converter import (
    HtmlToMarkdownAdapter,
    MarkdownifyAdapter,
    convert_with_fallback,
    create_converter,
)

SAMPLE_HTML = (
    "<h2>Item 1. Business</h2>"
    "<p>The company designs semiconductors.</p>"
    "<h3>Overview</h3>"
    "<p>Founded in 1993.</p>"
)


class TestAtxHeadings:
    """S-conv-01 / S-conv-04: Both adapters produce ATX headings."""

    def test_html_to_markdown_adapter_produces_atx(self):
        adapter = HtmlToMarkdownAdapter()
        md = adapter.convert(SAMPLE_HTML)
        assert "## Item 1. Business" in md
        assert "### Overview" in md
        assert "===" not in md
        assert "---" not in md

    def test_markdownify_adapter_produces_atx(self):
        adapter = MarkdownifyAdapter()
        md = adapter.convert(SAMPLE_HTML)
        assert "## Item 1. Business" in md
        assert "### Overview" in md
        assert "===" not in md
        assert "---" not in md

    def test_both_adapters_agree_on_heading_style(self):
        htm = HtmlToMarkdownAdapter()
        mkd = MarkdownifyAdapter()
        md_htm = htm.convert(SAMPLE_HTML)
        md_mkd = mkd.convert(SAMPLE_HTML)
        for prefix in ("## ", "### "):
            assert prefix in md_htm
            assert prefix in md_mkd


class TestAdapterNames:
    def test_html_to_markdown_adapter_name(self):
        assert HtmlToMarkdownAdapter().name == "html-to-markdown"

    def test_markdownify_adapter_name(self):
        assert MarkdownifyAdapter().name == "markdownify"


class TestCreateConverter:
    def test_returns_html_to_markdown_when_available(self):
        converter = create_converter()
        assert converter.name == "html-to-markdown"

    def test_falls_back_to_markdownify_on_import_error(self):
        with patch.dict("sys.modules", {"html_to_markdown": None}):
            converter = create_converter()
            assert converter.name == "markdownify"


class TestConvertWithFallback:
    """S-conv-03: Four fallback conditions."""

    def _make_stub(self, name: str, side_effect=None, return_value=None):
        class Stub:
            @property
            def name(self_inner):
                return name

            def convert(self_inner, html: str) -> str:
                if side_effect:
                    raise side_effect
                return return_value if return_value is not None else ""

        return Stub()

    def test_primary_success(self):
        primary = HtmlToMarkdownAdapter()
        fallback = MarkdownifyAdapter()
        md, converter_name = convert_with_fallback(SAMPLE_HTML, primary, fallback)
        assert converter_name == "html-to-markdown"
        assert "## Item 1. Business" in md

    def test_invocation_error_triggers_fallback(self):
        primary = self._make_stub("html-to-markdown", side_effect=RuntimeError("boom"))
        fallback = MarkdownifyAdapter()
        md, converter_name = convert_with_fallback(SAMPLE_HTML, primary, fallback)
        assert converter_name == "markdownify"
        assert "## Item 1. Business" in md

    def test_empty_output_triggers_fallback(self):
        primary = self._make_stub("html-to-markdown", return_value="")
        fallback = MarkdownifyAdapter()
        md, converter_name = convert_with_fallback(SAMPLE_HTML, primary, fallback)
        assert converter_name == "markdownify"
        assert len(md) > 0

    def test_tiny_output_triggers_fallback(self):
        long_html = "<p>" + "x" * 10000 + "</p>"
        primary = self._make_stub("html-to-markdown", return_value="x")
        fallback = MarkdownifyAdapter()
        md, converter_name = convert_with_fallback(long_html, primary, fallback)
        assert converter_name == "markdownify"

    @pytest.mark.parametrize(
        "ratio",
        [0.005, 0.009],
        ids=["0.5%-of-input", "0.9%-of-input"],
    )
    def test_below_one_percent_triggers_fallback(self, ratio):
        html_body = "a" * 10000
        long_html = f"<p>{html_body}</p>"
        tiny_output = "x" * int(len(long_html) * ratio)
        primary = self._make_stub("html-to-markdown", return_value=tiny_output)
        fallback = self._make_stub("markdownify", return_value="fallback result")
        md, converter_name = convert_with_fallback(long_html, primary, fallback)
        assert converter_name == "markdownify"

    def test_above_one_percent_uses_primary(self):
        html_body = "a" * 10000
        long_html = f"<p>{html_body}</p>"
        adequate_output = "x" * int(len(long_html) * 0.02)
        primary = self._make_stub("html-to-markdown", return_value=adequate_output)
        fallback = MarkdownifyAdapter()
        md, converter_name = convert_with_fallback(long_html, primary, fallback)
        assert converter_name == "html-to-markdown"
