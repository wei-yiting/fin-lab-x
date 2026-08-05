"""Throw-away — inspect the semantic content of the four over-cap 'prelude'
cases from prelude_size_probe_v2: what is actually inside the swallowed text?
Are there real (but undetected) sub-headings in there? What was the single
anchored heading and where does it sit in the item?

Cases: WMT 1A (57k), WMT 1 (16k), CAT 1 (11.5k), JPM 1A (6.4k).
Plus the two just-over-cap true-prelude candidates: CAT 1A, CAT 7.
"""

from __future__ import annotations

import json
import os
import re
import sys
import unicodedata
from pathlib import Path

from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parents[3]
load_dotenv(REPO_ROOT / "backend" / ".env")
sys.path.insert(0, str(REPO_ROOT))

from edgar import Company, set_identity

set_identity(os.environ["EDGAR_IDENTITY"])

CASES = [
    ("WMT", "1a"),
    ("WMT", "1"),
    ("CAT", "1"),
    ("JPM", "1a"),
    ("CAT", "1a"),
    ("CAT", "7"),
]

H_RE = re.compile(r"^(#{1,6}) (.+)$")


def canonicalize(s: str) -> str:
    s = unicodedata.normalize("NFKC", s)
    s = s.replace("‘", "'").replace("’", "'")
    s = s.replace("“", '"').replace("”", '"')
    s = s.replace("–", "-").replace("—", "-")
    s = re.sub(r"\s+", " ", s)
    return s.strip()


def headingish_lines(text: str) -> list[tuple[int, str]]:
    """Standalone short lines that look like sub-headings a human would see:
    5-90 chars, no sentence-ending punct, not mostly digits, surrounded by
    blank-ish structure."""
    lines = text.splitlines()
    out = []
    for i, ln in enumerate(lines):
        s = ln.strip()
        if not (5 <= len(s) <= 90):
            continue
        if s.endswith((".", "!", "?", ";", ",", ":")):
            continue
        if sum(c.isdigit() for c in s) >= 3:
            continue
        if any(c in s for c in "|$%"):
            continue
        prev_blank = i == 0 or not lines[i - 1].strip()
        next_nonempty = next((l for l in lines[i + 1 :] if l.strip()), "")
        if prev_blank and len(next_nonempty.strip()) > 60:
            out.append((i, s))
    return out


def main() -> int:
    tenk_cache: dict = {}
    md_cache: dict = {}
    report = {}
    for ticker, item in CASES:
        if ticker not in tenk_cache:
            print(f"[fetch] {ticker}", file=sys.stderr, flush=True)
            filing = Company(ticker).get_filings(form="10-K").latest()
            tenk_cache[ticker] = filing.obj()
            md_cache[ticker] = filing.markdown()
        tenk = tenk_cache[ticker]
        sec = tenk[item]
        text = sec.text() if hasattr(sec, "text") else str(sec)
        lines = text.splitlines()

        md_headings = {}
        for ln in md_cache[ticker].splitlines():
            m = H_RE.match(ln)
            if m:
                md_headings.setdefault(len(m.group(1)), []).append(m.group(2).strip())

        canon_line_set = {canonicalize(l) for l in lines if l.strip()}
        anchored = {
            lv: [h for h in hs if canonicalize(h) in canon_line_set]
            for lv, hs in md_headings.items()
        }

        hlines = headingish_lines(text)
        report[f"{ticker}-{item}"] = {
            "item_total_chars": len(text),
            "md_anchored_by_level": {
                str(lv): v for lv, v in anchored.items() if v and lv in (2, 3, 4, 5)
            },
            "headingish_line_count": len(hlines),
            "headingish_first_25": [f"L{i}: {s}" for i, s in hlines[:25]],
            "first_1200_chars": text[:1200],
        }

    out_path = Path("/tmp/prelude_failcase_semantics.json")
    out_path.write_text(json.dumps(report, indent=2, ensure_ascii=False))
    print(f"=> {out_path}", file=sys.stderr)
    for k, v in report.items():
        print(f"\n=== {k} (total {v['item_total_chars']} chars) ===")
        print(
            f"anchored md headings: { {lv: len(h) for lv, h in v['md_anchored_by_level'].items()} }"
        )
        print(f"headingish standalone lines: {v['headingish_line_count']}")
        for s in v["headingish_first_25"][:12]:
            print(f"  {s}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
