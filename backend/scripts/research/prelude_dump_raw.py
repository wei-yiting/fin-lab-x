"""Companion probe — dump raw section text for suspicious cases identified in
the first pass. Outputs to /tmp/ for human inspection.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parents[3]
load_dotenv(REPO_ROOT / "backend" / ".env")
sys.path.insert(0, str(REPO_ROOT))

from edgar import Company, set_identity  # noqa: E402

set_identity(os.environ["EDGAR_IDENTITY"])


# (ticker, item, max_chars_to_dump, dump_label)
TARGETS = [
    ("JPM", "7", 2000, "JPM_item_7_short"),
    ("JPM", "7A", 2000, "JPM_item_7A_short"),
    ("XOM", "7", 1000, "XOM_item_7_short"),
    ("XOM", "7A", 1000, "XOM_item_7A_short"),
    # Items where "Table of Contents" was the first line
    ("ADSK", "7", 1500, "ADSK_item_7_first_chunk"),
    ("CAT", "7", 1500, "CAT_item_7_first_chunk"),
    # JPM item 1 had only 1 misclassified block heading — see what's there
    ("JPM", "1", 4000, "JPM_item_1_first_chunk"),
    # CAT item 1 also massive prelude — see if sub-headings are NOT all caps
    ("CAT", "1", 4000, "CAT_item_1_first_chunk"),
    # WMT item 7 — sub-heading style (Overview etc.)
    ("WMT", "7", 4000, "WMT_item_7_first_chunk"),
    # JNJ item 7 — block headings appear to be product names with embedded numbers
    ("JNJ", "7", 4000, "JNJ_item_7_first_chunk"),
    # ADSK item 1A — flat item, see if it has bold-but-not-caps subheadings
    ("ADSK", "1A", 2500, "ADSK_item_1A_first_chunk"),
    # WMT 1A — flat
    ("WMT", "1A", 2500, "WMT_item_1A_first_chunk"),
]


def main() -> int:
    for ticker, item, n, label in TARGETS:
        try:
            tenk = Company(ticker).get_filings(form="10-K").latest().obj()
            text = tenk[item.lower()]
        except Exception as exc:
            print(f"{label}: FAILED {exc}", file=sys.stderr)
            continue
        path = f"/tmp/prelude_dump_{label}.txt"
        with open(path, "w", encoding="utf-8") as f:
            f.write(f"=== {ticker} item {item} (total chars={len(text)}) ===\n\n")
            f.write(text[:n])
        print(f"wrote {path} ({min(n, len(text))} chars of {len(text)})", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
