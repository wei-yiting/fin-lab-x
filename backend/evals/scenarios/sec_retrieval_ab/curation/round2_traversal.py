"""Pipeline-independent SEC filing traversal helpers for round-2 curation."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from html.parser import HTMLParser

_BLOCK_TAGS = {
    "address",
    "article",
    "aside",
    "blockquote",
    "br",
    "caption",
    "div",
    "dl",
    "dt",
    "dd",
    "fieldset",
    "figcaption",
    "figure",
    "footer",
    "form",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "header",
    "hr",
    "li",
    "main",
    "nav",
    "ol",
    "p",
    "pre",
    "section",
    "table",
    "tbody",
    "tfoot",
    "thead",
    "tr",
    "ul",
}
_HIDDEN_TAGS = {"head", "script", "style", "noscript", "template", "ix:hidden"}
_VOID_TAGS = {
    "area",
    "base",
    "br",
    "col",
    "embed",
    "hr",
    "img",
    "input",
    "link",
    "meta",
    "param",
    "source",
    "track",
    "wbr",
}
_DOCUMENT_RE = re.compile(r"<DOCUMENT>(.*?)</DOCUMENT>", re.DOTALL | re.IGNORECASE)


@dataclass(frozen=True)
class TraversalWindow:
    window_id: str
    start: int
    end: int
    sha256: str
    text: str


class _VisibleTextParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self.hidden_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        if self.hidden_depth:
            if tag not in _VOID_TAGS:
                self.hidden_depth += 1
            return
        style = next((value for key, value in attrs if key.lower() == "style"), None)
        if tag in _HIDDEN_TAGS or (style and "display:none" in style.replace(" ", "")):
            self.hidden_depth = 1
            return
        if tag in _BLOCK_TAGS:
            self.parts.append("\n\n")

    def handle_endtag(self, tag: str) -> None:
        if self.hidden_depth:
            self.hidden_depth -= 1
            return
        tag = tag.lower()
        if tag == "td" or tag == "th":
            self.parts.append(" | ")
        elif tag in _BLOCK_TAGS:
            self.parts.append("\n\n")

    def handle_data(self, data: str) -> None:
        if not self.hidden_depth:
            self.parts.append(data)


def visible_text(html: str) -> str:
    """Return visible filing text without SEC pipeline structure or hierarchy."""
    parser = _VisibleTextParser()
    parser.feed(html)
    text = "".join(parser.parts).replace("\xa0", " ")
    text = re.sub(r"[ \t\r\f\v]+", " ", text)
    text = re.sub(r" *\| *(?=\n|$)", "", text)
    text = re.sub(r" *\n *", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def extract_primary_10k(submission: str) -> tuple[str, str]:
    """Extract the exact ``TYPE 10-K`` document from an EDGAR submission."""
    for document_match in _DOCUMENT_RE.finditer(submission):
        payload = document_match.group(1)
        type_match = re.search(r"^[ \t]*<TYPE>\s*([^\r\n]+)", payload, re.MULTILINE)
        if type_match is None or type_match.group(1).strip().upper() != "10-K":
            continue
        filename_match = re.search(
            r"^[ \t]*<FILENAME>\s*([^\r\n]+)", payload, re.MULTILINE
        )
        text_match = re.search(
            r"<TEXT>\s*(.*?)\s*</TEXT>", payload, re.DOTALL | re.IGNORECASE
        )
        if filename_match is None or text_match is None:
            raise ValueError("10-K document is missing FILENAME or TEXT")
        document = text_match.group(1).strip()
        xbrl_wrapper = re.fullmatch(
            r"<XBRL>\s*(.*?)\s*</XBRL>", document, re.DOTALL | re.IGNORECASE
        )
        if xbrl_wrapper is not None:
            document = xbrl_wrapper.group(1)
        return filename_match.group(1).strip(), document
    raise ValueError("complete submission does not contain an exact TYPE 10-K document")


def neutral_windows(text: str, *, window_size: int) -> list[TraversalWindow]:
    """Split canonical text into fixed, non-overlapping traversal windows."""
    if window_size <= 0:
        raise ValueError("window_size must be positive")
    windows = []
    for index, start in enumerate(range(0, len(text), window_size), start=1):
        end = min(start + window_size, len(text))
        content = text[start:end]
        windows.append(
            TraversalWindow(
                window_id=f"W{index:04d}",
                start=start,
                end=end,
                sha256=hashlib.sha256(content.encode()).hexdigest(),
                text=content,
            )
        )
    return windows
