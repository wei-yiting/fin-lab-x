"""Throw-away — H3+H4 combined probe with noise filtering.

For each (ticker, item), compute:
- raw_h3, raw_h4
- anchored_h3, anchored_h4
- after noise filtering (page-number, ToC, cover-page boilerplate, FLS, bullets)
- final candidate count + verdict
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

H_RE = re.compile(r"^(#{1,6}) (.+)$")

NOISE_LITERAL = {
    "TABLE OF CONTENTS",
    "FORM 10-K",
    "PART I", "PART II", "PART III", "PART IV",
    "FORWARD-LOOKING STATEMENTS",
    "FORWARD-LOOKING INFORMATION",
    "Forward-Looking Statements",
    "Cautionary Note About Forward-Looking Statements",
    "Cautionary Note on Forward-Looking Statements",
    "DOCUMENTS INCORPORATED BY REFERENCE",
    "SIGNATURES", "Signatures",
    "POWER OF ATTORNEY",
    "AVAILABLE INFORMATION", "Available Information",
    "UNITED STATES",
    "SECURITIES AND EXCHANGE COMMISSION",
    "•",
    "or",
    "OR",
    "Washington, D.C. 20549",
}
NOISE_PAT = [
    re.compile(r"^\d+$"),  # pure numeric (page numbers)
    re.compile(r"^[•\-]+$"),  # bullets/dashes only
    re.compile(r"^Commission File", re.IGNORECASE),
    re.compile(r"^For the (fiscal year|transition period)", re.IGNORECASE),
    re.compile(r"^For the Fiscal Year Ended", re.IGNORECASE),
    re.compile(r"^\d{4}\s+(annual|form\s*10[-\s]?k|annual report)", re.IGNORECASE),
    re.compile(r"^Item\s+\d+[a-c]?\b", re.IGNORECASE),
    re.compile(r"^[A-Z\s]+(?:INC|CORP|COMPANY|LLC)\.?$"),  # company name in CAPS
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
    for p in NOISE_PAT:
        if p.match(s):
            return True
    return False


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


def probe(ticker: str, items: list[str]) -> dict:
    print(f"[fetch] {ticker}", file=sys.stderr, flush=True)
    filing = Company(ticker).get_filings(form="10-K").latest()
    tenk = filing.obj()
    md = filing.markdown()
    fy = str(getattr(filing, "period_of_report", ""))[:4]
    headings = collect_headings(md)

    raw_h3 = headings[3]
    raw_h4 = headings[4]

    h3_clean = [h for h in raw_h3 if not is_noise(h)]
    h4_clean = [h for h in raw_h4 if not is_noise(h)]
    h3_clean_unique = list(dict.fromkeys(h3_clean))
    h4_clean_unique = list(dict.fromkeys(h4_clean))

    per_item = {}
    item_anchored: dict[str, set[str]] = {}
    for item in items:
        text = safe_get_text(tenk, item)
        if not text:
            per_item[item] = {"chars": 0, "error": "section-not-found"}
            continue
        # is_stub heuristic
        compact = text.strip().lower()
        is_stub = len(text) < 1500 and any(
            p in compact
            for p in ["incorporated by reference", "reference is made to",
                      "appears on pages", "refer to the"]
        )
        standalone = {ln.strip() for ln in text.splitlines() if ln.strip()}

        h3_anchored = [h for h in h3_clean_unique if h in standalone]
        h4_anchored = [h for h in h4_clean_unique if h in standalone]

        # Combined dedupe: prefer H3 if same title in both
        combined = h3_anchored + [h for h in h4_anchored if h not in h3_anchored]
        item_anchored[item] = set(combined)

        # Verdict
        if is_stub:
            verdict = "stub"
        elif len(combined) >= 4:
            verdict = "good"
        elif len(combined) >= 2:
            verdict = "partial"
        elif len(combined) == 1:
            verdict = "thin"
        else:
            verdict = "fallback-needed"

        # Noise count (anchored items that pass our `is_noise` is 0; what we want
        # is "anchored items in the *raw* H3/H4 list that we filtered out")
        h3_anchored_noise = [h for h in raw_h3 if h in standalone and is_noise(h)]
        h4_anchored_noise = [h for h in raw_h4 if h in standalone and is_noise(h)]

        per_item[item] = {
            "chars": len(text),
            "is_stub": is_stub,
            "h3_anchored_clean": h3_anchored,
            "h4_anchored_clean": h4_anchored,
            "h3_anchored_clean_count": len(h3_anchored),
            "h4_anchored_clean_count": len(h4_anchored),
            "combined_clean_count": len(combined),
            "h3_anchored_noise_count": len(set(h3_anchored_noise)),
            "h4_anchored_noise_count": len(set(h4_anchored_noise)),
            "h4_anchored_noise_examples": list(set(h4_anchored_noise))[:5],
            "verdict": verdict,
        }

    # Cross-item collisions (true real anchored only)
    collisions: dict[str, list[str]] = {}
    all_titles: set[str] = set().union(*item_anchored.values())
    for t in all_titles:
        appearing = [it for it in items if t in item_anchored.get(it, set())]
        if len(appearing) >= 2:
            collisions[t] = appearing

    return {
        "ticker": ticker,
        "fiscal_year": fy,
        "md_total_chars": len(md),
        "h3_total_raw": len(raw_h3),
        "h3_total_clean_unique": len(h3_clean_unique),
        "h4_total_raw": len(raw_h4),
        "h4_total_clean_unique": len(h4_clean_unique),
        "per_item": per_item,
        "cross_item_collisions": collisions,
    }


def main() -> int:
    tickers = ["ADSK", "CAT", "JPM", "JNJ", "WMT", "XOM", "KO", "BA", "VZ", "DIS"]
    items = ["1", "1A", "7"]
    results = []
    for t in tickers:
        try:
            results.append(probe(t, items))
        except Exception as exc:
            results.append({"ticker": t, "error": f"{type(exc).__name__}: {exc}"})

    out_path = Path("/tmp/h3_h4_combined_results.json")
    out_path.write_text(json.dumps(results, indent=2, default=str, ensure_ascii=False))
    print(f"\n=> {out_path}", file=sys.stderr)
    print(json.dumps(results, indent=2, default=str, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
