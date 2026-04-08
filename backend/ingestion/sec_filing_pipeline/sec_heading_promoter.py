import re
from collections import Counter
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

_REPEATED_TEXT_MIN_OCCURRENCES = 4
_REPEATED_TEXT_MAX_LEN = 50
_SELF_REFERENCE_RE = re.compile(r"^\s*Item\s+\d+[A-Z]?\b", re.IGNORECASE)


def _build_noise_tokens(soup: BeautifulSoup) -> frozenset[str]:
    """Collect short block texts that appear at least _REPEATED_TEXT_MIN_OCCURRENCES
    times — typically page header/footer noise like 'Part I' or 'Bank of America'."""
    counter: Counter[str] = Counter()
    for tag in soup.find_all(["div", "p", "td", "th"]):
        text = tag.get_text(strip=True)
        if _MIN_HEADING_TEXT_LEN <= len(text) <= _REPEATED_TEXT_MAX_LEN:
            counter[text] += 1
    return frozenset(t for t, count in counter.items() if count >= _REPEATED_TEXT_MIN_OCCURRENCES)


def _is_self_reference(text: str) -> bool:
    """Return True if text looks like an Item N reference rather than a sub-section."""
    return _SELF_REFERENCE_RE.match(text) is not None


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


def _map_sizes_to_levels(unique_sizes: list[float]) -> dict[float, str]:
    """Map sorted-descending unique font-sizes to h3/h4/h5, capping at h5."""
    mapping: dict[float, str] = {}
    for idx, size in enumerate(unique_sizes):
        if idx == 0:
            mapping[size] = "h3"
        elif idx == 1:
            mapping[size] = "h4"
        else:
            mapping[size] = "h5"
    return mapping


def promote_subsections(
    soup: BeautifulSoup,
    regions: list[ItemRegion],
) -> None:
    """Rewrite bold-only blocks inside each item region as <h3>/<h4>/<h5>.

    For each ItemRegion:
      1. Walk forward from region.start_tag to region.end_tag.
      2. Collect every tag passing is_bold_only_block().
      3. For each collected tag, extract its dominant font-size.
      4. Rank unique font-sizes descending → map to h3/h4/h5 (cap at h5).
      5. Rewrite each collected tag to its mapped heading level in-place,
         clearing attrs and setting .string to the collapsed text.

    Blocks outside any region are untouched.
    """
    if not regions:
        return

    noise_tokens = _build_noise_tokens(soup)

    # Include h1/h2 because the Part/Item promotion pass running before this
    # function may have already rewritten the regions' start_tag from div/p to
    # h1/h2 — same Python object, different tag name.
    all_blocks = soup.find_all(["div", "p", "h1", "h2"])

    # Region transitions are signalled by start_tag identity. Each non-None
    # end_tag is the next region's start_tag, so a single start_tag lookup
    # handles both "enter region N" and "leave region N-1".
    start_tag_ids: dict[int, int] = {id(r.start_tag): idx for idx, r in enumerate(regions)}

    current_region_idx: int | None = None
    region_blocks: list[list[Tag]] = [[] for _ in regions]

    for block in all_blocks:
        bid = id(block)
        if bid in start_tag_ids:
            current_region_idx = start_tag_ids[bid]
            continue
        if current_region_idx is not None:
            region_blocks[current_region_idx].append(block)

    # Per-region: filter candidates → collect font-sizes → rank → rewrite
    for blocks in region_blocks:
        candidates: list[Tag] = []
        for b in blocks:
            if not is_bold_only_block(b):
                continue
            text = b.get_text(strip=True)
            if text in noise_tokens or _is_self_reference(text):
                continue
            candidates.append(b)
        if not candidates:
            continue

        block_sizes: list[tuple[Tag, float]] = []
        for candidate in candidates:
            size = extract_dominant_font_size(candidate)
            if size is not None:
                block_sizes.append((candidate, size))

        if not block_sizes:
            continue

        unique_sizes = sorted({s for _, s in block_sizes}, reverse=True)
        size_to_level = _map_sizes_to_levels(unique_sizes)

        for block, size in block_sizes:
            level = size_to_level[size]
            text = block.get_text(strip=True)
            block.name = level
            block.string = text
            block.attrs.clear()
