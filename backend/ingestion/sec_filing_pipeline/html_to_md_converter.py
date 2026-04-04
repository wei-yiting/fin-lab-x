from __future__ import annotations

import logging
import re
from collections.abc import Mapping
from typing import Protocol

logger = logging.getLogger(__name__)

_LEADING_FRONTMATTER_RE = re.compile(r"\A---\n(?:.*\n)*?---\n*")

# If the primary converter output is less than this fraction of the input HTML
# length, we assume it failed to convert meaningful content (e.g. table-heavy
# filings where the converter silently drops content) and fall back.
_MIN_OUTPUT_RATIO = 0.01


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

        result = htm_convert(
            html,
            options=ConversionOptions(heading_style="atx", extract_metadata=True),
        )
        if isinstance(result, str):
            content = result
        elif isinstance(result, Mapping):
            content = result.get("content") or ""
        else:
            raise TypeError(
                f"html-to-markdown returned unexpected type: {type(result).__name__}"
            )
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

    if not md or len(md) < len(html) * _MIN_OUTPUT_RATIO:
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
