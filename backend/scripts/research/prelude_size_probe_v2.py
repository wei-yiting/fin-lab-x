"""Throw-away research script — re-measure Item prelude size distribution
using the markdown H3/H4 anchored block-heading detection (the design's
actual detection algorithm), not the old ALL-CAPS rule from
`prelude_block_relationship.py` (which only cleanly extracted a prelude in
2/24 = 8% of probes).

This is the evidence-gate re-run mandated by design.md §5.2 / DEV-127 R2:
validate ≥70% of non-stub Items yield a prelude < 3,000 chars under the new
detection, and produce per-item size data to inform per-item gating.

Same 6 tickers x 4 items = 24 probes as the original prelude research, for
apples-to-apples comparison against the 8% baseline.

Do not import from production code paths; this is a one-off probe.
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

if not os.getenv("EDGAR_IDENTITY"):
    print("EDGAR_IDENTITY missing", file=sys.stderr)
    sys.exit(2)

sys.path.insert(0, str(REPO_ROOT))
from edgar import Company, set_identity

from backend.common.sec_core import is_stub_section

set_identity(os.environ["EDGAR_IDENTITY"])

TICKERS = ["ADSK", "JPM", "JNJ", "WMT", "XOM", "CAT"]
ITEMS = ["1", "1A", "7", "7A"]

PRELUDE_CAP_CHARS = 2000  # design.md §5.2 guard (R2)
PROBE_TARGET_CHARS = 3000  # research memo's ≥70% threshold

H_RE = re.compile(r"^(#{1,6}) (.+)$")

# Same noise filter as the validated 30-probe H3/H4 research
# (h3_h4_combined_probe.py) — reused verbatim so this probe measures the same
# detection algorithm the design commits to, not a re-derived variant.
NOISE_LITERAL = {
    "TABLE OF CONTENTS",
    "FORM 10-K",
    "PART I",
    "PART II",
    "PART III",
    "PART IV",
    "FORWARD-LOOKING STATEMENTS",
    "FORWARD-LOOKING INFORMATION",
    "Forward-Looking Statements",
    "Cautionary Note About Forward-Looking Statements",
    "Cautionary Note on Forward-Looking Statements",
    "DOCUMENTS INCORPORATED BY REFERENCE",
    "SIGNATURES",
    "Signatures",
    "POWER OF ATTORNEY",
    "AVAILABLE INFORMATION",
    "Available Information",
    "UNITED STATES",
    "SECURITIES AND EXCHANGE COMMISSION",
    "•",
    "or",
    "OR",
    "Washington, D.C. 20549",
}
NOISE_PAT = [
    re.compile(r"^\d+$"),
    re.compile(r"^[•\-]+$"),
    re.compile(r"^Commission File", re.IGNORECASE),
    re.compile(r"^For the (fiscal year|transition period)", re.IGNORECASE),
    re.compile(r"^For the Fiscal Year Ended", re.IGNORECASE),
    re.compile(r"^\d{4}\s+(annual|form\s*10[-\s]?k|annual report)", re.IGNORECASE),
    re.compile(r"^Item\s+\d+[a-c]?\b", re.IGNORECASE),
    re.compile(r"^[A-Z\s]+(?:INC|CORP|COMPANY|LLC)\.?$"),
    re.compile(r"^Index to", re.IGNORECASE),
    re.compile(r"^Notes to consolidated financial statements", re.IGNORECASE),
    re.compile(r"^Consolidated Statements? of", re.IGNORECASE),
    re.compile(r"^Consolidated Balance Sheets?", re.IGNORECASE),
    re.compile(r"^Report of Independent", re.IGNORECASE),
    re.compile(r"^REPORT OF INDEPENDENT", re.IGNORECASE),
]


def is_noise(title: str) -> bool:
    s = title.strip()
    if not s:
        return True
    if s in NOISE_LITERAL:
        return True
    return any(p.match(s) for p in NOISE_PAT)


def canonicalize(s: str) -> str:
    """DEV-127 R9 — collapse whitespace + unify curly/straight quotes and
    dashes before anchor comparison, so markdown vs plain-text rendering
    differences don't cause silent anchor misses."""
    s = unicodedata.normalize("NFKC", s)
    s = s.replace("‘", "'").replace("’", "'")
    s = s.replace("“", '"').replace("”", '"')
    s = s.replace("–", "-").replace("—", "-")
    s = re.sub(r"\s+", " ", s)
    return s.strip()


def collect_headings(md_text: str) -> dict[int, list[str]]:
    out: dict[int, list[str]] = {1: [], 2: [], 3: [], 4: [], 5: [], 6: []}
    for ln in md_text.splitlines():
        m = H_RE.match(ln)
        if m:
            lv = len(m.group(1))
            out[lv].append(m.group(2).strip())
    return out


def safe_get_text(tenk, item: str) -> str | None:
    for c in [item.lower(), item.upper(), item]:
        try:
            sec = tenk[c]
            if sec is None:
                continue
            return sec.text() if hasattr(sec, "text") else str(sec)
        except (KeyError, TypeError):
            continue
    return None


def block_headings_for_item(
    item_text: str, h3_clean_unique: list[str], h4_clean_unique: list[str]
) -> tuple[list[str], str]:
    """Return (ordered anchored headings in item_text, source) using the
    design's priority: H3 anchored > H4 anchored > text fallback (fallback
    left unimplemented here — out of scope for prelude sizing, flagged as
    'fallback-needed' since design.md §4.5's fallback doesn't produce a
    markdown-anchored prelude boundary the same way)."""
    lines = item_text.splitlines()
    canon_lines = [(ln, canonicalize(ln)) for ln in lines]

    def anchor(headings: list[str]) -> list[tuple[int, str]]:
        canon_targets = {canonicalize(h) for h in headings}
        found = []
        for idx, (raw, canon) in enumerate(canon_lines):
            if canon and canon in canon_targets:
                found.append((idx, raw.strip()))
        return found

    h3_found = anchor(h3_clean_unique)
    if h3_found:
        return [h for _, h in h3_found], "markdown_h3"
    h4_found = anchor(h4_clean_unique)
    if h4_found:
        return [h for _, h in h4_found], "markdown_h4"
    return [], "fallback-needed"


def compute_prelude(item_text: str, first_heading_line: str) -> str:
    """Text from the start of the Item body to (not including) the line
    matching first_heading_line, using canonicalized comparison (R9)."""
    lines = item_text.splitlines()
    target = canonicalize(first_heading_line)
    for idx, ln in enumerate(lines):
        if canonicalize(ln) == target:
            return "\n".join(lines[:idx]).strip()
    return ""


def analyze_one(
    ticker: str, item_key: str, h3_clean_unique: list[str], h4_clean_unique: list[str]
) -> dict:
    out: dict = {"ticker": ticker, "item": item_key, "ok": False}
    tenk = ANALYZE_CACHE.get(ticker)
    if tenk is None:
        out["error"] = "tenk_not_loaded"
        return out

    text = safe_get_text(tenk, item_key.lower())
    if not text or not text.strip():
        out["error"] = "empty_section"
        return out

    is_stub, reason = is_stub_section(text)
    if is_stub:
        out["stub"] = reason
        out["ok"] = True
        return out

    out["item_total_chars"] = len(text)
    headings, source = block_headings_for_item(text, h3_clean_unique, h4_clean_unique)
    out["detection_source"] = source
    out["block_headings_count"] = len(headings)

    if not headings:
        out["flat_item_or_fallback_needed"] = True
        out["ok"] = True
        return out

    prelude = compute_prelude(text, headings[0])
    out["prelude_chars"] = len(prelude)
    out["prelude_under_3000"] = len(prelude) < PROBE_TARGET_CHARS
    out["prelude_over_cap_2000"] = len(prelude) > PRELUDE_CAP_CHARS
    out["prelude_excerpt_first_300"] = prelude[:300]
    out["ok"] = True
    return out


ANALYZE_CACHE: dict = {}


def main() -> int:
    results = []
    for ticker in TICKERS:
        print(f"[fetch] {ticker}", file=sys.stderr, flush=True)
        try:
            filing = Company(ticker).get_filings(form="10-K").latest()
            tenk = filing.obj()
            md = filing.markdown()
        except Exception as exc:
            for item in ITEMS:
                results.append(
                    {
                        "ticker": ticker,
                        "item": item,
                        "ok": False,
                        "error": f"fetch_failed: {type(exc).__name__}: {exc}",
                    }
                )
            continue

        ANALYZE_CACHE[ticker] = tenk
        headings = collect_headings(md)
        h3_clean_unique = list(dict.fromkeys(h for h in headings[3] if not is_noise(h)))
        h4_clean_unique = list(dict.fromkeys(h for h in headings[4] if not is_noise(h)))

        for item in ITEMS:
            print(f"[analyze] {ticker} item {item}", file=sys.stderr, flush=True)
            results.append(analyze_one(ticker, item, h3_clean_unique, h4_clean_unique))

    # Summary stats
    non_stub = [r for r in results if r.get("ok") and "stub" not in r]
    with_prelude = [r for r in non_stub if "prelude_chars" in r]
    under_3000 = [r for r in with_prelude if r["prelude_under_3000"]]
    over_cap = [r for r in with_prelude if r["prelude_over_cap_2000"]]

    by_item: dict[str, dict] = {}
    for item in ITEMS:
        item_rows = [r for r in with_prelude if r["item"] == item]
        item_under = [r for r in item_rows if r["prelude_under_3000"]]
        by_item[item] = {
            "n_with_prelude": len(item_rows),
            "n_under_3000": len(item_under),
            "pct_under_3000": (
                round(100 * len(item_under) / len(item_rows), 1) if item_rows else None
            ),
        }

    summary = {
        "total_probes": len(results),
        "non_stub_items": len(non_stub),
        "items_with_detected_prelude": len(with_prelude),
        "items_flat_or_fallback_needed": len(
            [r for r in non_stub if r.get("flat_item_or_fallback_needed")]
        ),
        "prelude_under_3000_count": len(under_3000),
        "prelude_under_3000_pct_of_with_prelude": (
            round(100 * len(under_3000) / len(with_prelude), 1)
            if with_prelude
            else None
        ),
        "prelude_over_cap_2000_count": len(over_cap),
        "gate_target": "≥70% non-stub Items with a detected prelude should be < 3,000 chars",
        "by_item": by_item,
    }

    output = {"summary": summary, "results": results}
    out_path = Path("/tmp/prelude_size_probe_v2_results.json")
    out_path.write_text(json.dumps(output, indent=2, ensure_ascii=False))
    print(f"\n=> {out_path}", file=sys.stderr)
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
