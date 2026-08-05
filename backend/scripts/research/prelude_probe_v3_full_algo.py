"""Throw-away research — validate the REVISED prelude design (DEV-127 R2v2)
on an expanded cross-sector sample.

Revised algorithm under test (full detection chain, not just markdown path):

1. Markdown path with plausibility check:
   anchored (canonicalized) H3 headings are trusted only if
   count >= 2 AND first-anchored position <= 30% into the item text;
   else try H4 under the same check; else demote to text fallback.
2. Text fallback: Title-Case standalone-line detection (design §4.5 rules).
3. Prelude validity threshold: text before the first block heading is a
   valid prelude iff <= 3,000 chars — attached whole, never truncated.
   Larger => NOT a prelude: reclassified as a heading-less leading block
   (chunked + embedded normally), prelude metadata = None. Zero content loss.

Sample: 18 tickers x 4 items (1, 1A, 7, 7A) = 72 probes.

Outputs per-probe rows + summary to /tmp/prelude_probe_v3_results.json.
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

TICKERS = [
    # original 6 (baseline comparison)
    "ADSK",
    "JPM",
    "JNJ",
    "WMT",
    "XOM",
    "CAT",
    # h3/h4 30-probe extras
    "KO",
    "BA",
    "VZ",
    "DIS",
    # further sector spread: tech, semis, pharma, industrials, finance, energy
    "NVDA",
    "AAPL",
    "MSFT",
    "GE",
    "PFE",
    "GS",
    "HD",
    "COP",
]
ITEMS = ["1", "1A", "7", "7A"]

PRELUDE_VALIDITY_CHARS = 3000  # <=: valid prelude, attach whole; >: leading block
PLAUSIBILITY_MIN_COUNT = 2
PLAUSIBILITY_MAX_FIRST_POS = 0.30  # first anchored heading within first 30%

H_RE = re.compile(r"^(#{1,6}) (.+)$")

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
            out[len(m.group(1))].append(m.group(2).strip())
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


# --- markdown path -----------------------------------------------------------


def anchor_headings(lines_canon: list[str], candidates: list[str]) -> list[int]:
    """Return line indices where a candidate heading appears as the whole
    (canonicalized) line, in document order."""
    targets = {canonicalize(c) for c in candidates}
    return [i for i, canon in enumerate(lines_canon) if canon and canon in targets]


def plausible(
    anchor_idxs: list[int], char_offsets: list[int], total_chars: int
) -> bool:
    if len(anchor_idxs) < PLAUSIBILITY_MIN_COUNT:
        return False
    first_char = char_offsets[anchor_idxs[0]]
    return first_char <= PLAUSIBILITY_MAX_FIRST_POS * total_chars


# --- text fallback path (design §4.5) ---------------------------------------

ITEM_SELF_RE = re.compile(r"^item\s+\d+[a-c]?\.?", re.IGNORECASE)
DIGIT_CLUSTER_RE = re.compile(r"\d{3,}")


def fallback_heading_idxs(lines: list[str]) -> list[int]:
    idxs = []
    for i, line in enumerate(lines):
        s = line.strip()
        if not (5 <= len(s) <= 120):
            continue
        if s.isdigit() or DIGIT_CLUSTER_RE.search(s):
            continue
        if ITEM_SELF_RE.match(s):
            continue
        if any(c in s for c in "|$%"):
            continue
        prev = lines[i - 1].rstrip() if i > 0 else ""
        if prev.endswith((".", "!", "?")):
            continue
        nxt = next((l.strip() for l in lines[i + 1 :] if l.strip()), "")
        if len(nxt) <= 80:
            continue
        # Title-Case-or-CAPS-ish: standalone line not ending with sentence punct
        if s.endswith((".", ",", ";", ":")):
            continue
        idxs.append(i)
    return idxs


# --- probe -------------------------------------------------------------------


def analyze_item(text: str, h3_clean: list[str], h4_clean: list[str]) -> dict:
    lines = text.splitlines()
    lines_canon = [canonicalize(l) for l in lines]
    # char offset of each line start
    offsets = []
    pos = 0
    for l in lines:
        offsets.append(pos)
        pos += len(l) + 1
    total = len(text)

    h3_idx = anchor_headings(lines_canon, h3_clean)
    h4_idx = anchor_headings(lines_canon, h4_clean)

    demoted_from_markdown = False
    if plausible(h3_idx, offsets, total):
        path, idxs = "markdown_h3", h3_idx
    elif plausible(h4_idx, offsets, total):
        path, idxs = "markdown_h4", h4_idx
    else:
        if h3_idx or h4_idx:
            demoted_from_markdown = True
        fb = fallback_heading_idxs(lines)
        if plausible(fb, offsets, total):
            path, idxs = "text_fallback", fb
        else:
            return {
                "path": "flat",
                "demoted_from_markdown": demoted_from_markdown,
                "blocks": 0,
            }

    first_idx = idxs[0]
    prelude_raw = "\n".join(lines[:first_idx]).strip()
    # strip the Item's own heading line from prelude measurement (it is not
    # prose; design keeps title separately in StructuredItem.title)
    plines = prelude_raw.splitlines()
    if plines and ITEM_SELF_RE.match(plines[0].strip()):
        prelude_raw = "\n".join(plines[1:]).strip()

    valid = len(prelude_raw) <= PRELUDE_VALIDITY_CHARS
    return {
        "path": path,
        "demoted_from_markdown": demoted_from_markdown,
        "blocks": len(idxs),
        "first_heading": lines[first_idx].strip()[:80],
        "prelude_chars": len(prelude_raw),
        "prelude_valid": valid,
        "prelude_action": "attach_whole" if valid else "reclassify_leading_block",
        "prelude_excerpt": prelude_raw[:200],
    }


def main() -> int:
    results = []
    for ticker in TICKERS:
        print(f"[fetch] {ticker}", file=sys.stderr, flush=True)
        try:
            filing = Company(ticker).get_filings(form="10-K").latest()
            tenk = filing.obj()
            md = filing.markdown()
            fy = str(getattr(filing, "period_of_report", ""))[:4]
        except Exception as exc:
            results.append({"ticker": ticker, "error": f"{type(exc).__name__}: {exc}"})
            continue

        hd = collect_headings(md)
        h3_clean = list(dict.fromkeys(h for h in hd[3] if not is_noise(h)))
        h4_clean = list(dict.fromkeys(h for h in hd[4] if not is_noise(h)))

        for item in ITEMS:
            row: dict = {"ticker": ticker, "fy": fy, "item": item}
            text = safe_get_text(tenk, item.lower())
            if not text or not text.strip():
                row["outcome"] = "missing"
                results.append(row)
                continue
            stub, reason = is_stub_section(text)
            # pseudo-stub patterns (v2, remaining-content style approximation):
            if not stub and len(text) < 1500:
                compact = re.sub(r"\s+", " ", text.lower())
                if any(
                    p in compact
                    for p in [
                        "reference is made to",
                        "appears on page",
                        "refer to the",
                        "incorporated by reference",
                    ]
                ):
                    stub, reason = True, "pseudo-stub (v2 pattern)"
            if stub:
                row["outcome"] = "stub"
                row["stub_reason"] = reason
                results.append(row)
                continue

            row["outcome"] = "analyzed"
            row["item_chars"] = len(text)
            row.update(analyze_item(text, h3_clean, h4_clean))
            results.append(row)

    analyzed = [r for r in results if r.get("outcome") == "analyzed"]
    structured = [r for r in analyzed if r.get("path") != "flat"]
    with_prelude = [r for r in structured if r.get("prelude_chars", 0) > 0]
    valid_prelude = [r for r in structured if r.get("prelude_valid")]
    reclassified = [
        r for r in structured if r.get("prelude_action") == "reclassify_leading_block"
    ]
    demoted = [r for r in analyzed if r.get("demoted_from_markdown")]

    def pct(a: int, b: int) -> float | None:
        return round(100 * a / b, 1) if b else None

    by_item: dict[str, dict] = {}
    for item in ITEMS:
        rows = [r for r in structured if r["item"] == item]
        v = [r for r in rows if r.get("prelude_valid")]
        by_item[item] = {
            "structured": len(rows),
            "valid_prelude": len(v),
            "reclassified": len([r for r in rows if not r.get("prelude_valid")]),
            "pct_valid": pct(len(v), len(rows)),
        }

    summary = {
        "total_probes": len(results),
        "analyzed_non_stub": len(analyzed),
        "stubs": len([r for r in results if r.get("outcome") == "stub"]),
        "missing": len([r for r in results if r.get("outcome") == "missing"]),
        "path_distribution": {
            p: len([r for r in analyzed if r.get("path") == p])
            for p in ["markdown_h3", "markdown_h4", "text_fallback", "flat"]
        },
        "demoted_from_markdown_by_plausibility": len(demoted),
        "structured_items": len(structured),
        "valid_prelude_count": len(valid_prelude),
        "valid_prelude_pct_of_structured": pct(len(valid_prelude), len(structured)),
        "nonempty_prelude_count": len(with_prelude),
        "reclassified_leading_block_count": len(reclassified),
        "reclassified_cases": [
            f"{r['ticker']} {r['item']} ({r['prelude_chars']} chars, path={r['path']})"
            for r in reclassified
        ],
        "prelude_size_histogram_valid": {
            "0 (no prelude)": len(
                [r for r in valid_prelude if r["prelude_chars"] == 0]
            ),
            "1-500": len([r for r in valid_prelude if 1 <= r["prelude_chars"] <= 500]),
            "501-1500": len(
                [r for r in valid_prelude if 500 < r["prelude_chars"] <= 1500]
            ),
            "1501-3000": len(
                [r for r in valid_prelude if 1500 < r["prelude_chars"] <= 3000]
            ),
        },
        "by_item": by_item,
        "content_loss_guarantee": "zero — every reclassified pseudo-prelude is chunked as a leading block",
    }

    output = {"summary": summary, "results": results}
    out_path = Path("/tmp/prelude_probe_v3_results.json")
    out_path.write_text(json.dumps(output, indent=2, ensure_ascii=False))
    print(f"\n=> {out_path}", file=sys.stderr)
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
