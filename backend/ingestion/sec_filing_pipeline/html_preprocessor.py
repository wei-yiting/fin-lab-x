import re

from bs4 import BeautifulSoup, NavigableString, Tag

_PART_RE = re.compile(r"^\s*PART\s+(I{1,3}V?|IV)\b", re.IGNORECASE)
_ITEM_RE = re.compile(r"^\s*Item\s+\d+[A-Z]?\.", re.IGNORECASE)
_WHITESPACE_RE = re.compile(r"\s+")
_PRESERVE_WHITESPACE_PARENTS = frozenset({"pre", "code", "script", "style", "textarea"})

_DECORATIVE_PROPS = frozenset(
    {
        "font-family",
        "font-size",
        "font-style",
        "color",
        "background-color",
        "background",
        "padding",
        "padding-top",
        "padding-bottom",
        "padding-left",
        "padding-right",
        "margin",
        "margin-top",
        "margin-bottom",
        "margin-left",
        "margin-right",
        "border",
        "border-top",
        "border-bottom",
        "border-left",
        "border-right",
        "line-height",
        "letter-spacing",
        "text-decoration",
        "text-indent",
        "vertical-align",
        "width",
        "height",
        "min-width",
        "min-height",
        "max-width",
        "max-height",
    }
)

_BLOCK_TAGS = frozenset({"div", "p", "td", "th"})


def _has_bold_signal(tag: Tag) -> bool:
    if tag.find(["b", "strong"]):
        return True
    style = tag.get("style", "")
    if isinstance(style, list):
        style = ";".join(style)
    if re.search(r"font-weight\s*:\s*(700|bold)", style):
        return True
    for desc in tag.descendants:
        if isinstance(desc, Tag):
            desc_style = desc.get("style", "")
            if isinstance(desc_style, list):
                desc_style = ";".join(desc_style)
            if re.search(r"font-weight\s*:\s*(700|bold)", desc_style):
                return True
    return False


def _parse_style(style_str: str) -> list[tuple[str, str]]:
    props = []
    for part in style_str.split(";"):
        part = part.strip()
        if ":" not in part:
            continue
        name, _, value = part.partition(":")
        props.append((name.strip().lower(), value.strip()))
    return props


def _filter_decorative_styles(style_str: str) -> str | None:
    props = _parse_style(style_str)
    kept = [f"{name}:{value}" for name, value in props if name not in _DECORATIVE_PROPS]
    return "; ".join(kept) if kept else None


class HTMLPreprocessor:
    def preprocess(self, html: str) -> str:
        soup = BeautifulSoup(html, "html.parser")
        self._strip_xbrl_tags(soup)
        self._remove_hidden_elements(soup)
        self._strip_decorative_styles(soup)
        self._unwrap_font_tags(soup)
        self._normalize_text_whitespace(soup)
        self._promote_headings(soup)
        return str(soup)

    def _strip_xbrl_tags(self, soup: BeautifulSoup) -> None:
        for tag in soup.find_all(re.compile(r"^ix:")):
            tag.unwrap()

    def _remove_hidden_elements(self, soup: BeautifulSoup) -> None:
        for tag in soup.find_all(
            style=re.compile(r"display\s*:\s*none", re.IGNORECASE)
        ):
            tag.decompose()

    def _strip_decorative_styles(self, soup: BeautifulSoup) -> None:
        for tag in soup.find_all(style=True):
            style_str = tag["style"]
            if isinstance(style_str, list):
                style_str = ";".join(style_str)
            filtered = _filter_decorative_styles(style_str)
            if filtered:
                tag["style"] = filtered
            else:
                del tag["style"]

    def _unwrap_font_tags(self, soup: BeautifulSoup) -> None:
        for font_tag in soup.find_all("font"):
            font_tag.unwrap()

    def _normalize_text_whitespace(self, soup: BeautifulSoup) -> None:
        # Older SEC filings (pre-~2010, varies by filer) embed hard line breaks
        # inside text content nodes — e.g. "Item\n1A. Risk Factors." or
        # "United\nStates Securities and Exchange Commission".  Browsers render
        # these as a single space (HTML whitespace collapsing), but Markdown
        # converters preserve them verbatim, fragmenting paragraphs into
        # one-fragment-per-line output that destroys RAG chunking quality.
        #
        # We mirror browser behavior here: collapse runs of \s (newlines, tabs,
        # multiple spaces) to a single space inside every text node, except for
        # those whose parent preserves whitespace (<pre>, <code>, etc.).
        for text_node in list(soup.find_all(string=True)):
            parent = text_node.parent
            if parent is not None and parent.name in _PRESERVE_WHITESPACE_PARENTS:
                continue
            normalized = _WHITESPACE_RE.sub(" ", text_node)
            if normalized != text_node:
                text_node.replace_with(NavigableString(normalized))

    def _promote_headings(self, soup: BeautifulSoup) -> None:
        # SEC filings overwhelmingly use <div>/<p>/<span> with bold styling
        # rather than semantic <h1>-<h6> tags for section structure.  In the
        # rare cases where <h*> tags do appear (e.g. AAPL 2010 uses <h5> for
        # repeated "Table of Contents" anchor links on every page), they
        # decorate navigation links rather than mark real section headings, so
        # we leave them untouched and they pass through to Markdown as-is.
        #
        # This heuristic detects "PART …" and "Item …" patterns in bold block
        # elements and rewrites them as <h1>/<h2> so downstream Markdown
        # converters produce proper heading structure.
        #
        # Reverse traversal ensures inner (more specific) matches are promoted
        # first; the descendant guard then prevents an outer container from being
        # promoted redundantly when one of its children already was.
        promoted = set()
        for tag in reversed(soup.find_all(_BLOCK_TAGS)):
            if id(tag) in promoted:
                continue
            if any(id(d) in promoted for d in tag.descendants if isinstance(d, Tag)):
                continue

            # MSFT 2025 (and similar XBRL exporters) split heading text across
            # adjacent <span> elements — e.g. <span>PART</span><span> I</span>.
            # ``get_text(strip=True)`` would strip each text node before joining,
            # producing "PARTI" and breaking the regex match.  We must preserve
            # internal whitespace, then strip and collapse only at the edges.
            text = " ".join(tag.get_text().split())
            if not text:
                continue

            heading_level = None
            if _PART_RE.match(text):
                heading_level = "h1"
            elif _ITEM_RE.match(text):
                heading_level = "h2"

            if not heading_level or not _has_bold_signal(tag):
                continue

            if any(
                child.name in _BLOCK_TAGS and child.get_text(strip=True)
                for child in tag.children
                if isinstance(child, Tag)
            ):
                continue

            promoted.add(id(tag))
            tag.name = heading_level
            tag.string = text
            if tag.attrs:
                tag.attrs.clear()
