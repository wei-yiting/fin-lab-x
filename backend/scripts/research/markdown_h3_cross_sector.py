"""Throw-away — cross-sector H3 cross-check probe.

Goal: assess "markdown H3 primary + text fallback" detection rule for
Path 2 SEC RAG ingestion.

Per (ticker, item) we measure:
- Total markdown H3 count (filing-wide)
- For the Item plain text (tenk[item].text()), which H3 titles are
  matched as a standalone line
- Noise inventory (ToC, page header/footer)
- Cross-Item collisions between the items examined
"""

from __future__ import annotations

import json
import os
import re
import sys
import time
from pathlib import Path

from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parents[3]
load_dotenv(REPO_ROOT / "backend" / ".env")
sys.path.insert(0, str(REPO_ROOT))

from edgar import Company, set_identity  # noqa: E402

set_identity(os.environ["EDGAR_IDENTITY"])

HEADING_RE = re.compile(r"^(#{1,6})\s+(.*?)\s*$")

PAGE_HEADER_RE = re.compile(r"^\d{4}\s+(annual|form\s*10[-\s]?k|annual report)", re.IGNORECASE)
PAGE_NUM_TRAIL_RE = re.compile(r"\s+\d{1,3}\s*$")
ITEM_HEADING_RE = re.compile(r"^\s*item\s+\d+[a-c]?\b", re.IGNORECASE)
PART_HEADING_RE = re.compile(r"^\s*part\s+(?:i{1,3}v?|iv|v)\b\.?\s*$", re.IGNORECASE)


def collect_markdown_h3(md_text: str) -> list[dict]:
    """Return [{ line, raw, normalized }] for every level-3 heading in md_text."""
    out = []
    for i, line in enumerate(md_text.splitlines()):
        m = HEADING_RE.match(line)
        if not m:
            continue
        level = len(m.group(1))
        if level != 3:
            continue
        raw = m.group(2).strip()
        out.append({"line": i + 1, "raw": raw, "normalized": raw})
    return out


def classify_h3_noise(h3_title: str) -> str:
    """Classify an H3 title as one of:
    `real-candidate` / `noise-page-header` / `noise-page-footer` /
    `noise-numeric` / `noise-empty` / `noise-toc-link` /
    `noise-item` / `noise-part`.
    """
    s = h3_title.strip()
    if not s:
        return "noise-empty"
    if s.isdigit():
        return "noise-numeric"
    if PART_HEADING_RE.match(s):
        return "noise-part"
    # Page header pattern: "2025 Annual Report 46" etc.
    if PAGE_HEADER_RE.match(s):
        return "noise-page-header"
    if PAGE_NUM_TRAIL_RE.search(s) and len(s.split()) >= 2:
        # Annotation: trailing number on a heading-like line is page footer
        # but only flag if the prefix looks like a real heading (not "Item ...")
        return "noise-page-footer"
    if "[" in s and "](" in s:
        return "noise-toc-link"
    # Ignore ITEM-only headings (this is the Item heading itself, not a sub-heading)
    if ITEM_HEADING_RE.match(s) and len(s) < 80:
        return "noise-item"
    return "real-candidate"


def find_anchored_in_section(section_text: str, h3_titles: list[str]) -> dict:
    """For every h3 title, check whether it appears as a standalone line
    in `section_text`. Return:
      {"<title>": [<line index>, ...]}
    """
    lines = section_text.splitlines()
    # Build index: stripped non-empty line -> [line indices]
    index: dict[str, list[int]] = {}
    for i, ln in enumerate(lines):
        s = ln.strip()
        if not s:
            continue
        index.setdefault(s, []).append(i)

    results: dict[str, list[int]] = {}
    for t in h3_titles:
        s = t.strip()
        if not s:
            continue
        # Exact standalone match
        if s in index:
            results[t] = index[s]
    return results


def safe_get_section_text(tenk, item: str) -> str | None:
    """Return tenk[item].text() handling KeyError and case variants."""
    candidates = [item.lower(), item.upper(), item.lower().replace("a", "A")]
    for c in candidates:
        try:
            sec = tenk[c]
            if sec is not None:
                t = sec.text() if hasattr(sec, "text") else str(sec)
                if t:
                    return t
        except (KeyError, TypeError):
            continue
    return None


def is_stub_likely(text: str) -> bool:
    """Cheap stub detector — incorporated by reference / pseudo-stub
    patterns that should be flagged 'pseudo-stub'."""
    if not text or len(text) < 1500:
        compact = text.lower() if text else ""
        if any(
            phrase in compact
            for phrase in [
                "incorporated by reference",
                "incorporated herein by reference",
                "reference is made to",
                "refer to the",
                "appears on pages",
            ]
        ):
            return True
    return False


def probe_ticker(ticker: str, items: list[str]) -> dict:
    """Run the H3 + Item plain text cross-check for one ticker."""
    print(f"[fetch] {ticker}", file=sys.stderr, flush=True)
    company = Company(ticker)
    filings = company.get_filings(form="10-K")
    if not filings or len(filings) == 0:
        return {"ticker": ticker, "error": "no 10-K filings"}
    filing = filings.latest()
    fiscal_year = str(getattr(filing, "period_of_report", ""))[:4]
    tenk = filing.obj()

    md = filing.markdown()
    h3_all = collect_markdown_h3(md)
    h3_titles = [h["raw"] for h in h3_all]

    # Classify each H3
    noise_buckets: dict[str, list[dict]] = {}
    for h in h3_all:
        cat = classify_h3_noise(h["raw"])
        h["category"] = cat
        noise_buckets.setdefault(cat, []).append(h)

    # Per-item probe
    per_item: dict[str, dict] = {}
    item_text_index: dict[str, set[str]] = {}  # item -> set of standalone-line strings
    for item in items:
        text = safe_get_section_text(tenk, item)
        item_data = {
            "section_chars": 0 if text is None else len(text),
            "section_first_120": text[:120] if text else "",
            "stub_pseudo": False,
        }
        if text is None:
            item_data["error"] = "section not found"
            per_item[item] = item_data
            continue

        if is_stub_likely(text):
            item_data["stub_pseudo"] = True

        # Compute standalone lines once
        standalone = {ln.strip() for ln in text.splitlines() if ln.strip()}
        item_text_index[item] = standalone

        # Anchored search of the FULL filing's H3 list against this Item's text
        anchored = find_anchored_in_section(text, h3_titles)

        # Bucket anchored matches by category
        anchored_real = []
        anchored_noise = []
        for title, line_idxs in anchored.items():
            cat = classify_h3_noise(title)
            entry = {"title": title, "category": cat, "matches": len(line_idxs)}
            if cat == "real-candidate":
                anchored_real.append(entry)
            else:
                anchored_noise.append(entry)

        item_data.update({
            "anchored_total": len(anchored),
            "anchored_real_candidates": anchored_real,
            "anchored_real_count": len(anchored_real),
            "anchored_noise_count": len(anchored_noise),
            "anchored_noise_examples": anchored_noise[:5],
        })
        per_item[item] = item_data

    # Cross-Item collisions: H3s anchored in >1 item
    collision_map: dict[str, list[str]] = {}
    item_anchored_real_titles: dict[str, set[str]] = {}
    for item in items:
        d = per_item.get(item, {})
        item_anchored_real_titles[item] = {
            e["title"] for e in d.get("anchored_real_candidates", [])
        }
    all_real_titles: set[str] = set().union(*item_anchored_real_titles.values())
    for title in all_real_titles:
        appearing_in = [
            i for i in items if title in item_anchored_real_titles.get(i, set())
        ]
        if len(appearing_in) >= 2:
            collision_map[title] = appearing_in

    # ToC pollution probe: scan first 5% of markdown for H3 inside ToC region
    md_lines = md.splitlines()
    toc_window = md_lines[: max(40, len(md_lines) // 20)]  # first 5% or 40 lines
    toc_h3_titles: list[str] = []
    for i, line in enumerate(toc_window):
        m = HEADING_RE.match(line)
        if m and len(m.group(1)) == 3:
            toc_h3_titles.append(m.group(2).strip())

    return {
        "ticker": ticker,
        "fiscal_year": fiscal_year,
        "md_total_chars": len(md),
        "md_h3_total": len(h3_all),
        "h3_inventory_first_25": h3_all[:25],
        "h3_noise_buckets_summary": {
            k: len(v) for k, v in noise_buckets.items()
        },
        "h3_noise_buckets_examples": {
            k: [v["raw"] for v in vs[:5]] for k, vs in noise_buckets.items()
        },
        "toc_window_h3_titles": toc_h3_titles[:15],
        "toc_window_h3_count": len(toc_h3_titles),
        "per_item": per_item,
        "cross_item_collisions": collision_map,
    }


def main() -> int:
    tickers = ["ADSK", "CAT", "JPM", "JNJ", "WMT", "XOM", "KO", "BA", "VZ", "DIS"]
    items = ["1", "1A", "7"]
    results = []
    for t in tickers:
        try:
            r = probe_ticker(t, items)
            results.append(r)
        except Exception as exc:
            err_type = type(exc).__name__
            print(f"[error] {t}: {err_type}: {exc}", file=sys.stderr, flush=True)
            results.append({"ticker": t, "error": f"{err_type}: {exc}"})
            # Mild backoff on errors
            time.sleep(2)
    out_path = Path("/tmp/h3_cross_sector_results.json")
    out_path.write_text(json.dumps(results, indent=2, default=str, ensure_ascii=False))
    print(f"\nResults written to {out_path}", file=sys.stderr)
    print(json.dumps(results, indent=2, default=str, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
