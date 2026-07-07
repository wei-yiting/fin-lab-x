"""Throw-away — for each ticker × Item, inventory the sub-headings actually
present in `filing.markdown()` and compare against `section.text()`'s
ALL-CAPS detection. Persist comparison tables to /tmp/.

Item-range detection is permissive — handles:
- Standard `## ITEM 7.` (ADSK, JNJ, CAT, JPM)
- Split-title `## Item 7.` + `## Management's Discussion...` (CAT)
- Title Case variant (JNJ `## Item 7. Management's discussion...`)
- Heading-glued-with-body (JPM `## Item 1A. Risk Factors.The...`)
- WMT/XOM where Item heading is missing entirely from markdown
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parents[3]
load_dotenv(REPO_ROOT / "backend" / ".env")
sys.path.insert(0, str(REPO_ROOT))

from edgar import Company, set_identity  # noqa: E402

set_identity(os.environ["EDGAR_IDENTITY"])


HEADING_RE = re.compile(r"^(#{1,6})\s+(.*?)\s*$")


def find_item_range(md_lines: list[str], item_num: str) -> tuple[int, int] | None:
    """Find lines [start, end) containing the Item's body in markdown.

    Strategy: locate the first heading whose text starts with
    'Item N' (case-insensitive, period-or-space separator).
    Walk to the next heading whose text starts with 'Item M' where M != N.
    """
    item_re = re.compile(
        r"^\s*item\s+" + re.escape(item_num.lower()) + r"(?:[.\s]|$)",
        re.IGNORECASE,
    )
    next_item_re = re.compile(r"^\s*item\s+\d+[a-c]?(?:[.\s]|$)", re.IGNORECASE)
    start = None
    for i, line in enumerate(md_lines):
        m = HEADING_RE.match(line)
        if m and item_re.match(m.group(2)):
            start = i
            break
    if start is None:
        return None
    end = len(md_lines)
    for j in range(start + 1, len(md_lines)):
        m = HEADING_RE.match(md_lines[j])
        if not m:
            continue
        text = m.group(2)
        if next_item_re.match(text) and not item_re.match(text):
            end = j
            break
    return (start, end)


def is_alldigit_or_short(text: str) -> bool:
    s = text.strip()
    return s.isdigit() or len(s) <= 1 or s in {"or", "OR"}


def is_table_row(text: str) -> bool:
    return bool(re.search(r"\d{2,},\d{3}", text)) or "|" in text or text.count("$") > 1


def split_caps_titlecase(text: str) -> str:
    s = text.strip()
    if not s:
        return "empty"
    if s.isupper() and len(s) >= 5:
        return "ALL_CAPS"
    # Title Case: each word capitalized
    words = re.findall(r"[A-Za-z]+", s)
    if words and all((w[0].isupper() for w in words if len(w) >= 4)):
        return "TitleCase"
    return "other"


def cleanup_heading(text: str) -> str:
    return text.strip()


def inventory(ticker: str, items: list[str]) -> dict:
    filing = Company(ticker).get_filings(form="10-K").latest()
    tenk = filing.obj()
    md = filing.markdown()
    md_lines = md.splitlines()

    out = {"ticker": ticker, "md_total_chars": len(md), "items": {}}

    for item in items:
        rng = find_item_range(md_lines, item)
        sec_text = tenk[item.lower()]
        sec_lines = sec_text.splitlines()

        # Walk section.text() and pick out ALL CAPS short lines (the "v1" detector)
        v1_caps = []
        for ln in sec_lines:
            s = ln.strip()
            if (
                s.isupper()
                and 5 <= len(s) <= 120
                and not s.isdigit()
                and not any(c in s for c in {"|", "$", "%"})
            ):
                v1_caps.append(s)

        item_data: dict = {
            "section_text_chars": len(sec_text),
            "md_range": rng,
            "v1_caps_in_section_text": v1_caps,
            "v1_caps_count": len(v1_caps),
        }

        if rng is None:
            item_data["md_headings_in_range"] = None
            out["items"][item] = item_data
            continue

        # Collect headings within range
        headings = []
        for i in range(rng[0], rng[1]):
            m = HEADING_RE.match(md_lines[i])
            if m:
                headings.append({
                    "line": i + 1,
                    "level": len(m.group(1)),
                    "text": cleanup_heading(m.group(2))[:200],
                })

        # Filter "noise" headings — short, digit-only, table rows, repeated chars,
        # leftover SEC/registrant page-cover artifacts
        clean = []
        for h in headings:
            t = h["text"]
            if is_alldigit_or_short(t):
                continue
            if is_table_row(t):
                continue
            if re.fullmatch(r"#+|_+", t):
                continue
            clean.append({**h, "case": split_caps_titlecase(t)})

        # by level
        levels: dict = {}
        for h in clean:
            lv = h["level"]
            levels[lv] = levels.get(lv, 0) + 1
        case_dist: dict = {}
        for h in clean:
            case_dist[h["case"]] = case_dist.get(h["case"], 0) + 1

        item_data["md_headings_in_range"] = {
            "raw_count": len(headings),
            "clean_count": len(clean),
            "by_level": levels,
            "by_case": case_dist,
            "examples_first_30": clean[:30],
        }
        out["items"][item] = item_data

    return out


def main() -> int:
    tickers = ["ADSK", "JPM", "JNJ", "WMT", "XOM", "CAT"]
    items = ["7", "1A"]
    results = []
    for t in tickers:
        try:
            print(f"[fetch] {t}", file=sys.stderr)
            results.append(inventory(t, items))
        except Exception as exc:
            results.append({"ticker": t, "error": f"{type(exc).__name__}: {exc}"})
    print(json.dumps(results, indent=2, default=str, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
