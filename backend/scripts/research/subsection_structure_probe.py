"""Throw-away cross-sector research script — evaluate edgartools native
sub-section structure (Section objects) and `filing.markdown()` heading
quality across 6 tickers × Items 7 + 1A.

Outputs:
- Section attributes dump per (ticker, item) -> /tmp/subsec_dump_{ticker}_{item}.txt
- Markdown heading hierarchy stats per ticker -> /tmp/subsec_md_{ticker}.txt
- Aggregated summary JSON to stdout (for inclusion in research report).

Read-only. Does not import production pipeline modules. Uses only
shared `fetch_filing_obj` helper for proper rate-limit handling.
"""

from __future__ import annotations

import json
import os
import re
import sys
import traceback
from pathlib import Path

from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parents[3]
load_dotenv(REPO_ROOT / "backend" / ".env")

if not os.getenv("EDGAR_IDENTITY"):
    print("EDGAR_IDENTITY missing", file=sys.stderr)
    sys.exit(2)

sys.path.insert(0, str(REPO_ROOT))
from backend.common.sec_core import FilingType, fetch_filing_obj  # noqa: E402

from edgar import set_identity  # noqa: E402

set_identity(os.environ["EDGAR_IDENTITY"])


TICKERS = ["ADSK", "JPM", "JNJ", "WMT", "XOM", "CAT"]
ITEMS = ["7", "1A"]


HEADING_RE = re.compile(r"^(#{1,6})\s+(.*?)\s*$")
PART_HEADING_RE = re.compile(r"^#{1,2}\s+PART\s+", re.IGNORECASE)
ITEM_HEADING_RE = re.compile(r"^#{1,3}\s+ITEM\s+\d+", re.IGNORECASE)


def count_headings(md: str) -> dict:
    counts = {"h1": 0, "h2": 0, "h3": 0, "h4": 0, "h5": 0, "h6": 0}
    examples = {1: [], 2: [], 3: [], 4: []}
    for line in md.splitlines():
        m = HEADING_RE.match(line)
        if m:
            level = len(m.group(1))
            text = m.group(2)[:80]
            counts[f"h{level}"] = counts[f"h{level}"] + 1
            if level <= 4 and len(examples[level]) < 8:
                examples[level].append(text)
    return {"counts": counts, "examples": examples}


def find_item_md_range(md: str, item_num: str) -> tuple[int, int] | None:
    """Find the line range in markdown that corresponds to a specific Item.
    Returns (start_idx, end_idx) of the lines or None.
    """
    lines = md.splitlines()
    item_re = re.compile(
        r"^#{1,3}\s+ITEM\s+" + re.escape(item_num.upper()) + r"[.\s]",
        re.IGNORECASE,
    )
    next_item_re = re.compile(r"^#{1,3}\s+ITEM\s+\d+[A-C]?[.\s]", re.IGNORECASE)
    start = None
    for i, line in enumerate(lines):
        if item_re.match(line):
            start = i
            break
    if start is None:
        return None
    end = len(lines)
    for j in range(start + 1, len(lines)):
        if next_item_re.match(lines[j]) and not item_re.match(lines[j]):
            end = j
            break
    return (start, end)


def count_headings_in_range(md: str, start: int, end: int) -> dict:
    lines = md.splitlines()[start:end]
    counts = {"h1": 0, "h2": 0, "h3": 0, "h4": 0, "h5": 0, "h6": 0}
    examples = {1: [], 2: [], 3: [], 4: [], 5: []}
    for line in lines:
        m = HEADING_RE.match(line)
        if m:
            level = len(m.group(1))
            text = m.group(2)[:120]
            counts[f"h{level}"] = counts[f"h{level}"] + 1
            if level <= 5 and len(examples[level]) < 30:
                examples[level].append(text)
    return {"counts": counts, "examples": examples, "line_span": end - start}


def dump_section_attrs(sec, label: str) -> dict:
    """Capture all attributes/types of a Section object."""
    out = {"label": label}
    attrs_to_inspect = [
        "name", "title", "item", "part", "confidence", "detection_method",
        "validated", "start_offset", "end_offset", "node", "tables",
        "parse_section_name", "search",
    ]
    for a in attrs_to_inspect:
        try:
            v = getattr(sec, a, "<missing>")
            t = type(v).__name__
            if callable(v) and not isinstance(v, (int, str)):
                # don't call methods, just record type
                out[a] = {"type": t, "callable": True}
                continue
            if hasattr(v, "__len__") and not isinstance(v, str):
                try:
                    out[a] = {"type": t, "len": len(v), "repr": repr(v)[:200]}
                except Exception:
                    out[a] = {"type": t, "repr": repr(v)[:200]}
            else:
                out[a] = {"type": t, "value": repr(v)[:200]}
        except Exception as e:
            out[a] = {"error": f"{type(e).__name__}: {e}"}
    return out


def inspect_node(sec, label: str) -> dict:
    """Inspect the .node attribute structure if present."""
    info = {}
    node = getattr(sec, "node", None)
    if node is None:
        return {"node_present": False}
    info["node_present"] = True
    info["node_type"] = type(node).__name__
    info["node_module"] = type(node).__module__

    # Static / scalar attributes
    for a in ["tag_name", "type", "section_name", "depth", "semantic_type", "semantic_role"]:
        try:
            v = getattr(node, a, "<missing>")
            if v == "<missing>":
                continue
            info[f"node.{a}"] = repr(v)[:120]
        except Exception as e:
            info[f"node.{a}"] = f"ERR: {type(e).__name__}: {e}"

    # children / walk tree size
    try:
        kids = list(node.children) if hasattr(node, "children") and node.children is not None else []
        info["node.children_count"] = len(kids)
    except Exception as e:
        info["node.children_count"] = f"ERR: {type(e).__name__}: {e}"

    try:
        descendants = list(node.walk())
        info["node.walk_descendant_count"] = len(descendants)
    except Exception as e:
        info["node.walk_descendant_count"] = f"ERR: {type(e).__name__}: {e}"

    # Content surfaces
    try:
        nt = node.text() if callable(node.text) else node.text
        info["node.text_len"] = len(nt) if isinstance(nt, str) else "non-str"
    except Exception as e:
        info["node.text_len"] = f"ERR: {type(e).__name__}: {e}"

    try:
        nh = node.html() if callable(node.html) else node.html
        info["node.html_len"] = len(nh) if isinstance(nh, str) else "non-str"
        info["node.html_first_200"] = nh[:200] if isinstance(nh, str) else None
    except Exception as e:
        info["node.html_len"] = f"ERR: {type(e).__name__}: {e}"

    return info


def offset_check(sec, md_full_len: int, txt_len: int) -> dict:
    so = getattr(sec, "start_offset", None)
    eo = getattr(sec, "end_offset", None)
    out = {"start_offset": so, "end_offset": eo}
    if isinstance(so, int) and isinstance(eo, int):
        out["delta"] = eo - so
        out["delta_vs_text_len"] = (eo - so) - txt_len
        out["delta_vs_md_len"] = md_full_len - eo  # how far from end-of-md
    return out


def write_dump(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


def _level_hist(items: list) -> dict:
    out: dict = {}
    for h in items:
        lv = h.get("level")
        out[lv] = out.get(lv, 0) + 1
    return out


def analyse_ticker(ticker: str) -> dict:
    print(f"[fetch] {ticker}", file=sys.stderr)
    out: dict = {"ticker": ticker}
    try:
        from edgar import Company  # noqa: PLC0415

        filing = Company(ticker).get_filings(form="10-K").latest()
        tenk = filing.obj()
    except Exception as exc:
        out["fetch_error"] = f"{type(exc).__name__}: {exc}"
        return out

    # Filing-level markdown — note: tenk has no .filing attr; we use the
    # original Filing handle.
    try:
        md = filing.markdown()
        out["md_total_chars"] = len(md)
        out["md_overall"] = count_headings(md)
    except Exception as exc:
        out["md_error"] = f"{type(exc).__name__}: {exc}\n{traceback.format_exc()[:500]}"
        md = ""

    # Document.headings — separate parse tree exposed by edgartools
    try:
        doc_headings = tenk.doc.headings
        levels = {}
        for h in doc_headings:
            lv = getattr(h, "level", None)
            levels[lv] = levels.get(lv, 0) + 1
        out["doc_headings_total"] = len(doc_headings)
        out["doc_headings_by_level"] = levels
    except Exception as exc:
        out["doc_headings_error"] = f"{type(exc).__name__}: {exc}"

    # Persist top-of-md sample for later debugging
    if md:
        write_dump(
            Path(f"/tmp/subsec_md_{ticker}_first_200_lines.txt"),
            "\n".join(md.splitlines()[:200]),
        )
        # Also write only the markdown heading lines (compressed view)
        heading_lines = [
            f"L{i+1}: {line}"
            for i, line in enumerate(md.splitlines())
            if HEADING_RE.match(line)
        ]
        write_dump(
            Path(f"/tmp/subsec_md_{ticker}_headings.txt"),
            "\n".join(heading_lines),
        )

    out["per_item"] = {}
    for item in ITEMS:
        try:
            sec_text = tenk[item.lower()]
        except Exception as exc:
            out["per_item"][item] = {"error": f"{type(exc).__name__}: {exc}"}
            continue

        # Section object attribute dump (via .sections.get(key) — needs key
        # discovery first since key format differs by company).
        sections_map = tenk.sections
        keys = list(sections_map)
        target_key = None
        for k in keys:
            if k.lower().endswith(f"item_{item.lower()}"):
                target_key = k
                break
        if target_key is None:
            for k in keys:
                if k.lower() == f"item {item.lower()}":
                    target_key = k
                    break
        if target_key is None:
            out["per_item"][item] = {"sections_get_failed": True, "available_keys": keys[:8]}
            continue
        try:
            sec = sections_map.get(target_key)
        except Exception as exc:
            out["per_item"][item] = {"sections_get_error": f"{type(exc).__name__}: {exc}"}
            continue

        attrs_dump = dump_section_attrs(sec, f"{ticker}_{item}")
        node_info = inspect_node(sec, f"{ticker}_{item}")
        offsets = offset_check(sec, len(md), len(sec_text))

        # Document headings that fall within this Section's text range — match
        # by substring presence in sec_text rather than by offset (offsets are
        # section-relative, not filing-relative).
        try:
            doc_headings = tenk.doc.headings
            in_section = []
            for h in doc_headings:
                t = getattr(h, "text", None)
                if callable(t):
                    t = t()
                if t and isinstance(t, str) and t.strip() and t.strip() in sec_text:
                    in_section.append({
                        "level": getattr(h, "level", None),
                        "text": t.strip()[:120],
                    })
            attrs_dump["doc_headings_in_section"] = {
                "count": len(in_section),
                "by_level": _level_hist(in_section),
                "examples_first_25": in_section[:25],
            }
        except Exception as exc:
            attrs_dump["doc_headings_in_section_error"] = f"{type(exc).__name__}: {exc}"

        # Markdown heading stats restricted to this Item's range
        md_range = find_item_md_range(md, item) if md else None
        if md_range is not None:
            range_stats = count_headings_in_range(md, *md_range)
        else:
            range_stats = None

        out["per_item"][item] = {
            "section_text_chars": len(sec_text),
            "section_key": target_key,
            "attrs": attrs_dump,
            "node": node_info,
            "offsets": offsets,
            "md_range_found": md_range is not None,
            "md_range": md_range,
            "md_range_stats": range_stats,
        }

        # Persist Section attrs + first 80 lines of section.text() to /tmp/
        section_dump_lines = [f"=== {ticker} item {item} (key={target_key}) ==="]
        section_dump_lines.append(f"section_text_chars: {len(sec_text)}")
        section_dump_lines.append("")
        section_dump_lines.append("--- attrs ---")
        section_dump_lines.append(json.dumps(attrs_dump, indent=2, default=str)[:4000])
        section_dump_lines.append("")
        section_dump_lines.append("--- node info ---")
        section_dump_lines.append(json.dumps(node_info, indent=2, default=str)[:4000])
        section_dump_lines.append("")
        section_dump_lines.append("--- offsets ---")
        section_dump_lines.append(json.dumps(offsets, indent=2, default=str))
        section_dump_lines.append("")
        section_dump_lines.append("--- first 100 lines of sec.text() ---")
        section_dump_lines.extend(sec_text.splitlines()[:100])
        if md_range:
            section_dump_lines.append("")
            section_dump_lines.append("--- markdown lines in this item ---")
            md_lines = md.splitlines()[md_range[0]:md_range[1]]
            heading_only = [f"L{md_range[0]+i+1}: {ln}" for i, ln in enumerate(md_lines) if HEADING_RE.match(ln)]
            section_dump_lines.extend(heading_only[:60])
        write_dump(
            Path(f"/tmp/subsec_dump_{ticker}_item_{item}.txt"),
            "\n".join(section_dump_lines),
        )

    return out


def main() -> int:
    results = []
    for t in TICKERS:
        results.append(analyse_ticker(t))
    print(json.dumps(results, indent=2, default=str, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
