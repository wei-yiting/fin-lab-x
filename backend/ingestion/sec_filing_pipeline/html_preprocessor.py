import re

from bs4 import BeautifulSoup, Tag

_PART_RE = re.compile(r"^\s*PART\s+(I{1,3}V?|IV)\b", re.IGNORECASE)
_ITEM_RE = re.compile(r"^\s*Item\s+\d+[A-Z]?\.", re.IGNORECASE)

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

_BLOCK_TAGS = frozenset({"div", "p", "td", "th", "span"})


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
        self._promote_headings(soup)
        return str(soup)

    def _strip_xbrl_tags(self, soup: BeautifulSoup) -> None:
        for tag in soup.find_all(re.compile(r"^ix:")):
            tag.unwrap()

    def _remove_hidden_elements(self, soup: BeautifulSoup) -> None:
        for tag in soup.find_all(style=re.compile(r"display\s*:\s*none", re.IGNORECASE)):
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

    def _promote_headings(self, soup: BeautifulSoup) -> None:
        promoted = set()
        for tag in reversed(soup.find_all(_BLOCK_TAGS)):
            if id(tag) in promoted:
                continue
            if any(id(d) in promoted for d in tag.descendants if isinstance(d, Tag)):
                continue

            text = tag.get_text(strip=True)
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
