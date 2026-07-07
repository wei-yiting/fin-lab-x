"""Throw-away research script — analyze 10-K Item prelude vs block heading
relationships across diverse sectors. Output JSON to stdout for human review.
Do not import from production code paths; this is a one-off probe.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

# Repo root: .../improve-rag-ingestion
REPO_ROOT = Path(__file__).resolve().parents[3]
load_dotenv(REPO_ROOT / "backend" / ".env")

if not os.getenv("EDGAR_IDENTITY"):
    print("EDGAR_IDENTITY missing", file=sys.stderr)
    sys.exit(2)

# Production helpers — read-only use of stub detector.
sys.path.insert(0, str(REPO_ROOT))
from backend.common.sec_core import is_stub_section  # noqa: E402

from edgar import Company, set_identity  # noqa: E402

set_identity(os.environ["EDGAR_IDENTITY"])


TICKERS = ["ADSK", "JPM", "JNJ", "WMT", "XOM", "CAT"]
ITEMS = ["1", "1A", "7", "7A"]


def is_block_heading(line: str) -> bool:
    s = line.strip()
    return (
        s.isupper()
        and 5 <= len(s) <= 120
        and not s.isdigit()
        and not any(c in s for c in {"|", "$", "%"})
    )


def split_prelude(text: str) -> tuple[str | None, str | None, list[str]]:
    """Return (first_line, prelude, block_headings_found).

    - first_line: the very first non-empty line of the section (typically the
      Item heading like ``ITEM 7. ...``).
    - prelude: text between the first line and the first block heading; None
      means flat item (no block heading found).
    - block_headings_found: every detected block heading (for diagnostics).
    """
    lines = text.splitlines()
    # Find first non-empty line
    first_idx = None
    for i, line in enumerate(lines):
        if line.strip():
            first_idx = i
            break
    if first_idx is None:
        return None, None, []
    first_line = lines[first_idx].strip()

    # Walk subsequent lines for first block heading
    headings: list[str] = []
    first_heading_idx: int | None = None
    for i in range(first_idx + 1, len(lines)):
        if is_block_heading(lines[i]):
            headings.append(lines[i].strip())
            if first_heading_idx is None:
                first_heading_idx = i

    if first_heading_idx is None:
        return first_line, None, []

    prelude_lines = lines[first_idx + 1 : first_heading_idx]
    prelude = "\n".join(prelude_lines).strip()
    return first_line, prelude, headings


def analyze_one(ticker: str, item_key: str) -> dict:
    out: dict = {
        "ticker": ticker,
        "item": item_key,
        "ok": False,
    }
    try:
        tenk = Company(ticker).get_filings(form="10-K").latest().obj()
    except Exception as exc:
        out["error"] = f"fetch_failed: {type(exc).__name__}: {exc}"
        return out

    try:
        text = tenk[item_key.lower()]
    except Exception as exc:
        out["error"] = f"section_fetch_failed: {type(exc).__name__}: {exc}"
        return out

    if not text or not text.strip():
        out["error"] = "empty_section"
        return out

    is_stub, reason = is_stub_section(text)
    if is_stub:
        out["stub"] = reason
        return out

    first_line, prelude, headings = split_prelude(text)
    out["first_line"] = (first_line or "")[:200]
    out["block_headings_count"] = len(headings)
    out["block_headings_first_5"] = headings[:5]
    out["section_total_chars"] = len(text)
    if prelude is None:
        out["flat_item"] = True
        out["ok"] = True
        return out

    out["flat_item"] = False
    out["prelude_chars"] = len(prelude)
    out["prelude_excerpt_first_500"] = prelude[:500]
    if len(prelude) > 500:
        out["prelude_excerpt_last_300"] = prelude[-300:]
    out["ok"] = True
    return out


def main() -> int:
    results = []
    for ticker in TICKERS:
        for item in ITEMS:
            print(f"[fetch] {ticker} item {item}", file=sys.stderr)
            res = analyze_one(ticker, item)
            results.append(res)
    print(json.dumps(results, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
