import re
from dataclasses import dataclass

from bs4 import BeautifulSoup, Tag
from bs4.element import NavigableString

_MIN_HEADING_TEXT_LEN = 3
_MAX_HEADING_TEXT_LEN = 200
_SENTENCE_END_CHARS = frozenset(".!?")

_FONT_SIZE_PT_RE = re.compile(r"font-size\s*:\s*([0-9]+(?:\.[0-9]+)?)pt", re.IGNORECASE)
_FONT_WEIGHT_RE = re.compile(r"font-weight\s*:\s*(700|bold)", re.IGNORECASE)

_ITEM_HEADING_RE = re.compile(r"^\s*Item\s+(\d+[A-Z]?)\.", re.IGNORECASE)
_ITEM_REGION_BLOCKS = ("div", "p", "td", "th")


@dataclass(frozen=True)
class ItemRegion:
    item_num: str
    start_tag: Tag
    end_tag: Tag | None


def detect_item_regions(soup: BeautifulSoup) -> list[ItemRegion]:
    """Return ordered list of body-level Item regions.

    Algorithm:
      1. Find all block elements (div/p/td/th) whose stripped text matches
         ^Item\\s+\\d+[A-Z]?\\..
      2. Group by normalized item_num.
      3. For each item_num pick the LAST occurrence (TOC is always before body).
      4. Sort picked tags by document position.
      5. Pair each tag with its successor as end_tag; last tag has end_tag=None.
    """
    all_blocks = soup.find_all(_ITEM_REGION_BLOCKS)

    # Map item_num -> (doc_index, tag); last write wins (last occurrence heuristic)
    last_occurrence: dict[str, tuple[int, Tag]] = {}
    for idx, tag in enumerate(all_blocks):
        match = _ITEM_HEADING_RE.match(tag.get_text(strip=True))
        if match:
            item_num = match.group(1).upper()
            last_occurrence[item_num] = (idx, tag)

    if not last_occurrence:
        return []

    # Sort by document position (idx) to preserve raw document order
    sorted_items = sorted(
        last_occurrence.items(), key=lambda kv: kv[1][0]
    )
    ordered = [(item_num, tag) for item_num, (_, tag) in sorted_items]

    regions: list[ItemRegion] = []
    for i, (item_num, start_tag) in enumerate(ordered):
        end_tag = ordered[i + 1][1] if i + 1 < len(ordered) else None
        regions.append(
            ItemRegion(item_num=item_num, start_tag=start_tag, end_tag=end_tag)
        )

    return regions


def has_table_ancestor(tag: Tag) -> bool:
    """Return True if any ancestor of tag is <table>."""
    for parent in tag.parents:
        if isinstance(parent, Tag) and parent.name == "table":
            return True
    return False


def extract_dominant_font_size(tag: Tag) -> float | None:
    """Extract the font-size (in pt) that dominates by character count.

    Walks every text node inside tag and finds the nearest ancestor span with a
    parseable `font-size:Npt`, crediting the text length to that size. This
    ensures each text node is counted exactly once even under nested spans.
    Returns None if no text node maps to a parseable font-size. Small-size
    footnote markers (e.g. "1" in 6pt) lose to the dominant heading size
    because they carry fewer characters.
    """
    size_char_counts: dict[float, int] = {}

    for text_node in tag.find_all(string=True):
        text = str(text_node).strip()
        if not text:
            continue
        size = _find_text_font_size(text_node, tag)
        if size is None:
            continue
        size_char_counts[size] = size_char_counts.get(size, 0) + len(text)

    if not size_char_counts:
        return None

    return max(size_char_counts, key=lambda s: size_char_counts[s])


def is_bold_only_block(tag: Tag) -> bool:
    """Return True iff tag is a bold-only sub-section heading candidate.

    Rules:
      - tag.name must be 'div' or 'p' (never 'td'/'th')
      - has_table_ancestor(tag) must be False
      - no nested <div>/<p>/<table> inside tag
      - text length in [_MIN_HEADING_TEXT_LEN, _MAX_HEADING_TEXT_LEN]
      - text is not purely numeric (page number guard)
      - if text length > 30, text must not end with . ! ?
      - every text-bearing descendant must have font-weight 700 or bold
        (via own style or any ancestor up to tag, including <b>/<strong>)
    """
    if tag.name not in ("div", "p"):
        return False

    if has_table_ancestor(tag):
        return False

    if tag.find(["div", "p", "table"]):
        return False

    text = tag.get_text(strip=True)
    text_len = len(text)

    if text_len < _MIN_HEADING_TEXT_LEN or text_len > _MAX_HEADING_TEXT_LEN:
        return False

    if text.isnumeric():
        return False

    if text_len > 30 and text[-1] in _SENTENCE_END_CHARS:
        return False

    has_any_text = False
    for text_node in tag.find_all(string=True):
        if not str(text_node).strip():
            continue
        has_any_text = True
        if not _has_bold_ancestor(text_node, tag):
            return False

    return has_any_text


def _get_style(tag: Tag) -> str:
    """Return tag's inline style as a single string, never None."""
    raw = tag.get("style")
    if raw is None:
        return ""
    if isinstance(raw, list):
        return ";".join(raw)
    return raw


def _has_bold_ancestor(node: NavigableString, root: Tag) -> bool:
    """Return True if node has a bold signal on any ancestor up to and including root."""
    current = node.parent
    while current is not None:
        if isinstance(current, Tag):
            if current.name in ("b", "strong"):
                return True
            if _FONT_WEIGHT_RE.search(_get_style(current)):
                return True
        if current is root:
            return False
        current = current.parent
    return False


def _find_text_font_size(text_node: NavigableString, root: Tag) -> float | None:
    """Return the font-size (pt) from the nearest ancestor span up to root, or None."""
    current = text_node.parent
    while current is not None:
        if isinstance(current, Tag) and current.name == "span":
            match = _FONT_SIZE_PT_RE.search(_get_style(current))
            if match:
                return float(match.group(1))
        if current is root:
            return None
        current = current.parent
    return None
