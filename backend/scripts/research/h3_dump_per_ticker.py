"""Throw-away — for each ticker dump the full H3 inventory + per-Item
anchored matches to /tmp/h3_dump_<ticker>.txt for manual cross-check.

Reads /tmp/h3_cross_sector_results.json produced by markdown_h3_cross_sector.py
and re-runs markdown collection to dump the *raw* H3 list (the JSON only
keeps first 25 examples).
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
ITEM_HEADING_RE = re.compile(r"^\s*item\s+\d+[a-c]?\b", re.IGNORECASE)


def main() -> int:
    tickers = ["ADSK", "CAT", "JPM", "JNJ", "WMT", "XOM", "KO", "BA", "VZ", "DIS"]
    items = ["1", "1A", "7"]
    summary = {}
    for ticker in tickers:
        print(f"[fetch] {ticker}", file=sys.stderr, flush=True)
        try:
            filing = Company(ticker).get_filings(form="10-K").latest()
            tenk = filing.obj()
            md = filing.markdown()
        except Exception as exc:
            print(f"[error] {ticker}: {type(exc).__name__}: {exc}", file=sys.stderr)
            time.sleep(2)
            continue

        h3_list = []
        for i, line in enumerate(md.splitlines()):
            m = HEADING_RE.match(line)
            if m and len(m.group(1)) == 3:
                h3_list.append((i + 1, m.group(2).strip()))

        item_texts = {}
        for it in items:
            try:
                sec = tenk[it.lower()]
                item_texts[it] = sec.text() if sec is not None else ""
            except Exception:
                item_texts[it] = ""

        # For each H3, find matching items
        rows = []
        for line, title in h3_list:
            standalone_in = []
            for it in items:
                t = item_texts.get(it, "")
                if not t:
                    continue
                # standalone-line match
                for ln in t.splitlines():
                    if ln.strip() == title:
                        standalone_in.append(it)
                        break
            rows.append((line, title, standalone_in))

        out_path = Path(f"/tmp/h3_dump_{ticker}.txt")
        with out_path.open("w") as f:
            f.write(f"=== {ticker} 10-K (period={getattr(filing, 'period_of_report', '?')}) ===\n")
            f.write(f"md_chars={len(md)}  total_h3={len(h3_list)}\n\n")
            for line, title, items_match in rows:
                marker = ",".join(items_match) if items_match else "-"
                f.write(f"L{line:>6}  [{marker:>10}]  {title[:160]}\n")
            f.write("\n=== ITEM SECTION HEADS ===\n")
            for it in items:
                t = item_texts.get(it, "")
                f.write(f"\n-- Item {it} ({len(t)} chars) --\n")
                f.write(t[:500])
                f.write("\n")

        # Top toc-window: first 10% of md
        md_lines = md.splitlines()
        toc_window_size = max(60, len(md_lines) // 10)
        toc_h3 = [
            (i + 1, m.group(2).strip())
            for i, line in enumerate(md_lines[:toc_window_size])
            if (m := HEADING_RE.match(line)) and len(m.group(1)) == 3
        ]
        toc_path = Path(f"/tmp/h3_toc_window_{ticker}.txt")
        with toc_path.open("w") as f:
            f.write(f"=== {ticker} ToC window (first {toc_window_size} md lines) ===\n")
            for line, title in toc_h3:
                f.write(f"L{line:>5}  {title[:160]}\n")

        summary[ticker] = {
            "total_h3": len(h3_list),
            "toc_window_h3": len(toc_h3),
            "per_item_anchored_real": {
                it: sum(1 for _, _, items_match in rows if it in items_match)
                for it in items
            },
        }
        print(f"[done]  {ticker}: total_h3={len(h3_list)}, toc_h3={len(toc_h3)}", file=sys.stderr)

    summary_path = Path("/tmp/h3_dump_summary.json")
    summary_path.write_text(json.dumps(summary, indent=2))
    print(f"\nSummary: {summary_path}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
