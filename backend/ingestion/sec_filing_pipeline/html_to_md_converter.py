from __future__ import annotations

import logging
import re
from typing import Protocol

logger = logging.getLogger(__name__)

_LEADING_FRONTMATTER_RE = re.compile(r"\A---\n(?:.*\n)*?---\n*")


class HTMLToMarkdownConverter(Protocol):
    @property
    def name(self) -> str: ...
    def convert(self, html: str) -> str: ...


class HtmlToMarkdownAdapter:
    @property
    def name(self) -> str:
        return "html-to-markdown"

    def convert(self, html: str) -> str:
        from html_to_markdown import ConversionOptions
        from html_to_markdown import convert as htm_convert

        result = htm_convert(html, options=ConversionOptions(heading_style="atx"))
        content = result["content"] or ""
        return _LEADING_FRONTMATTER_RE.sub("", content)


class MarkdownifyAdapter:
    @property
    def name(self) -> str:
        return "markdownify"

    def convert(self, html: str) -> str:
        import markdownify

        return markdownify.markdownify(html, heading_style=markdownify.ATX)


def create_converter() -> HTMLToMarkdownConverter:
    try:
        import html_to_markdown as _  # noqa: F811, F401

        return HtmlToMarkdownAdapter()
    except ImportError:
        logger.warning("html-to-markdown not available, falling back to markdownify")
        return MarkdownifyAdapter()


def convert_with_fallback(
    html: str,
    primary: HTMLToMarkdownConverter,
    fallback: HTMLToMarkdownConverter,
) -> tuple[str, str]:
    try:
        md = primary.convert(html)
    except Exception:
        logger.warning(
            "Primary converter '%s' failed, falling back to '%s'",
            primary.name,
            fallback.name,
        )
        md = fallback.convert(html)
        return md, fallback.name

    if not md or len(md) < len(html) * 0.01:
        logger.warning(
            "Primary converter '%s' produced suspiciously small output "
            "(%d bytes from %d bytes input), falling back to '%s'",
            primary.name,
            len(md) if md else 0,
            len(html),
            fallback.name,
        )
        md = fallback.convert(html)
        return md, fallback.name

    return md, primary.name
