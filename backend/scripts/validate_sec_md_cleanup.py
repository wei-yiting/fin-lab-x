"""Validate SEC 10-K markdown cleanup rules against cached filings.

Walks a ``LocalFilingStore`` cache directory, runs the cleanup rule
detectors (page separators, Part III stubs, heading variants,
false-positive risks) against every cached 10-K markdown, and writes a
report. Used to surface new boilerplate patterns or regressions before
modifying ``MarkdownCleaner``.

Re-run this whenever:
- Adding new tickers to the validation set
- Changing a cleanup rule in ``MarkdownCleaner``
- Investigating a suspected regression on a specific filing

Usage:
    uv run python backend/scripts/validate_sec_md_cleanup.py \\
        --cache-dir /path/to/data/sec_filings \\
        --output artifacts/current/validation_cleanup_patterns.md

See ``backend/scripts/README.md`` for what each statistic in the report
means and how to interpret it against the rules in
``backend/ingestion/sec_filing_pipeline/markdown_cleaner.py``.
"""

from __future__ import annotations

import argparse
import re
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

# Re-use production regexes and helpers directly so the validator cannot
# silently drift from ``MarkdownCleaner``. M-1.3 / M-1.4 regressions were
# caused by locally-forked versions of these.
from backend.ingestion.sec_filing_pipeline.markdown_cleaner import (
    _INCORP_BY_REF_RE as INCORP_BY_REF_RE,
    _ITEM_1_ANCHOR_RE as COVER_PAGE_FALLBACK_ANCHOR_RE,
    _PAGE_SEP_RE as PAGE_SEP_STRICT_RE,
    _PART_I_ANCHOR_RE as COVER_PAGE_PRIMARY_ANCHOR_RE,
    is_pure_part_iii_stub,
)

# ---------------------------------------------------------------------------
# Detection regexes that are local to the validator (heading variant
# classification + false-positive checks). The cleanup semantics (stub
# detection, anchor selection) are delegated to the production module.
# ---------------------------------------------------------------------------

# A `[Table of Contents](#anchor)` link – appears as standalone line near
# every page break in many filings.
TOC_LINK_RE = re.compile(r"\[Table of Contents\]\(#")

# Any bare `---` line (no surrounding pipes, not part of a markdown table).
BARE_DASH_RE = re.compile(r"^---[ \t]*$", re.MULTILINE)

# Markdown table separator: `|---|---|` or `| --- | --- |` (any pipe-and-dash).
TABLE_SEP_RE = re.compile(r"^\s*\|[\s\-:|]+\|\s*$", re.MULTILINE)

# Part heading variants: `# Part I`, `# PART I.`, `## Part I` etc.
PART_HEADING_RE = re.compile(
    r"^(#{1,3}) (?:PART|Part)\s+([IVX]+)\.?\s*([^\n]*)$",
    re.MULTILINE,
)

# Item heading variants: `## Item 1. Business`, `## ITEM 1.BUSINESS`,
# `## Item 1A.`, etc.
ITEM_HEADING_RE = re.compile(
    r"^(#{1,4}) (?:ITEM|Item)\s+(\d+[A-Z]?)\.?\s*([^\n]*)$",
    re.MULTILINE,
)

# Pull a full Item section (heading + body until next ## heading) for
# stub detection.
ITEM_SECTION_RE = re.compile(
    r"^(#{1,4}) (?:ITEM|Item)\s+(\d+[A-Z]?)\b([^\n]*)\n(.*?)(?=^#{1,4} |\Z)",
    re.MULTILINE | re.DOTALL,
)


# ---------------------------------------------------------------------------
# Stats container
# ---------------------------------------------------------------------------


@dataclass
class FilingStats:
    ticker: str
    fiscal_year: str
    converter: str
    path: Path

    toc_link_count: int = 0
    bare_dash_count: int = 0
    page_sep_strict_count: int = 0
    table_sep_count: int = 0

    # Part III stub classification — mirrors the production rule:
    # * stub: contains ref AND would be stripped by the cleaner.
    # * hybrid: contains ref BUT has enough non-ref remainder to survive.
    # * real: contains no ref at all (untouched by the cleaner).
    item_10_14_stub_count: int = 0
    item_10_14_hybrid_count: int = 0
    item_10_14_real_count: int = 0
    item_10_14_total: int = 0
    item_1c_present: bool = False
    item_1c_stub_like: bool = False
    item_9a_present: bool = False
    item_9b_present: bool = False
    item_9c_present: bool = False
    # Cover-page anchor: primary (# Part I), fallback (## Item 1), or none.
    cover_page_anchor_type: str = "none"  # "primary" | "fallback" | "none"
    cover_page_anchor_position: int = -1

    part_headings: list[str] = field(default_factory=list)
    item_headings: list[str] = field(default_factory=list)
    truncated_headings: list[str] = field(default_factory=list)
    empty_title_headings: list[str] = field(default_factory=list)

    part_variants: Counter[str] = field(default_factory=Counter)
    item_variants: Counter[str] = field(default_factory=Counter)

    fp_warnings: list[str] = field(default_factory=list)

    @property
    def cover_page_anchor_found(self) -> bool:
        return self.cover_page_anchor_type != "none"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def parse_frontmatter(content: str) -> tuple[dict[str, str], str]:
    if not content.startswith("---\n"):
        return {}, content
    end = content.find("\n---\n", 4)
    if end == -1:
        return {}, content
    fm_text = content[4:end]
    body = content[end + len("\n---\n") :]
    fm: dict[str, str] = {}
    for line in fm_text.splitlines():
        if ":" in line:
            k, _, v = line.partition(":")
            fm[k.strip()] = v.strip().strip("'\"")
    return fm, body


def classify_part_heading(line: str) -> str:
    body = line.lstrip("# ").strip()
    is_upper = body.startswith("PART")
    has_period = body.rstrip().endswith(".")
    if is_upper and has_period:
        return "UPPER+period"
    if is_upper:
        return "UPPER"
    if has_period:
        return "Mixed+period"
    return "Standard"


def classify_item_heading(line: str) -> str:
    m = ITEM_HEADING_RE.match(line)
    if not m:
        return "unmatched"
    title = m.group(3).strip()
    is_upper = "ITEM" in line[: line.index(m.group(2))]
    no_space_after_period = bool(re.search(r"\d+[A-Z]?\.[A-Za-z]", line))

    if not title:
        return "empty-title"
    if is_upper and no_space_after_period:
        return "UPPER+nospace"
    if is_upper and title.isupper():
        return "UPPER+UPPERtitle"
    if is_upper:
        return "UPPER+mixedtitle"
    if title.isupper():
        return "Item+UPPERtitle"
    return "Standard"


# ---------------------------------------------------------------------------
# Per-filing analysis
# ---------------------------------------------------------------------------


def analyze_filing(path: Path) -> FilingStats | None:
    content = path.read_text()
    fm, body = parse_frontmatter(content)
    ticker = fm.get("ticker") or path.parent.parent.name
    fiscal_year = fm.get("fiscal_year") or path.stem
    converter = fm.get("converter") or "unknown"

    stats = FilingStats(
        ticker=ticker,
        fiscal_year=fiscal_year,
        converter=converter,
        path=path,
    )

    stats.toc_link_count = len(TOC_LINK_RE.findall(body))
    stats.bare_dash_count = len(BARE_DASH_RE.findall(body))
    stats.page_sep_strict_count = len(PAGE_SEP_STRICT_RE.findall(body))
    stats.table_sep_count = len(TABLE_SEP_RE.findall(body))

    # Cover-page anchor presence — mirror the cleaner's primary /
    # fallback logic so BAC, JNJ (no `# Part I`, but have `## Item 1`)
    # aren't incorrectly reported as "missing anchor".
    cp_primary = COVER_PAGE_PRIMARY_ANCHOR_RE.search(body)
    if cp_primary:
        stats.cover_page_anchor_type = "primary"
        stats.cover_page_anchor_position = cp_primary.start()
    else:
        cp_fallback = COVER_PAGE_FALLBACK_ANCHOR_RE.search(body)
        if cp_fallback:
            stats.cover_page_anchor_type = "fallback"
            stats.cover_page_anchor_position = cp_fallback.start()

    # Item section walk — classify 10-14 sections using the exact same
    # ``is_pure_part_iii_stub`` rule the production cleaner applies, so
    # the report's stub/hybrid/real counts match what actually happens
    # at ingestion time.
    for match in ITEM_SECTION_RE.finditer(body):
        item_num = match.group(2).upper()
        section_body = match.group(4)
        has_ref = bool(INCORP_BY_REF_RE.search(section_body))
        section_len = len(section_body.strip())

        if item_num in {"10", "11", "12", "13", "14"}:
            stats.item_10_14_total += 1
            if not has_ref:
                stats.item_10_14_real_count += 1
            elif is_pure_part_iii_stub(section_body):
                stats.item_10_14_stub_count += 1
            else:
                stats.item_10_14_hybrid_count += 1
        elif item_num == "1C":
            stats.item_1c_present = True
            if has_ref or section_len < 200:
                stats.item_1c_stub_like = True
        elif item_num == "9A":
            stats.item_9a_present = True
        elif item_num == "9B":
            stats.item_9b_present = True
        elif item_num == "9C":
            stats.item_9c_present = True

    # Heading collection + variant classification
    for m in PART_HEADING_RE.finditer(body):
        line = m.group(0)
        stats.part_headings.append(line)
        stats.part_variants[classify_part_heading(line)] += 1

    for m in ITEM_HEADING_RE.finditer(body):
        line = m.group(0)
        stats.item_headings.append(line)
        variant = classify_item_heading(line)
        stats.item_variants[variant] += 1

        title = m.group(3).strip().rstrip(".").strip()
        if 0 < len(title) < 5:
            stats.truncated_headings.append(line)
        if not title:
            stats.empty_title_headings.append(line)

    # False positive risk: any Item 10-14 regex would match Item 1A/1B/1C
    item_10_14_regex = re.compile(r"^#{1,4} (?:ITEM|Item) 1[0-4]\b", re.MULTILINE)
    for h in stats.item_headings:
        m = item_10_14_regex.match(h)
        if m:
            after = h[m.end() : m.end() + 1]
            if after in {"A", "B", "C"}:
                stats.fp_warnings.append(
                    f"Item 10-14 regex would incorrectly match: {h!r}"
                )

    # False positive risk: any markdown table separator with digit/blank prev line
    for m in TABLE_SEP_RE.finditer(body):
        start = m.start()
        prev_nl = body.rfind("\n", 0, max(start - 1, 0))
        prev_line = body[(prev_nl + 1) if prev_nl >= 0 else 0 : max(start - 1, 0)]
        if re.fullmatch(r"[ \t]*\d*[ \t]*", prev_line):
            stats.fp_warnings.append(
                f"Table separator with digit/blank prev line: prev={prev_line!r} sep={m.group(0).strip()!r}"
            )

    return stats


# ---------------------------------------------------------------------------
# Report rendering
# ---------------------------------------------------------------------------


def render_report(stats_list: list[FilingStats]) -> str:
    lines: list[str] = []
    lines.append("# Validation Report — Filing Markdown Cleanup Patterns")
    lines.append("")
    lines.append(f"- Total filings analyzed: **{len(stats_list)}**")
    tickers = sorted({s.ticker for s in stats_list})
    lines.append(f"- Unique tickers: **{len(tickers)}** ({', '.join(tickers)})")
    converters = Counter(s.converter for s in stats_list)
    conv_str = ", ".join(f"{k}={v}" for k, v in converters.most_common())
    lines.append(f"- Converters: {conv_str}")
    lines.append("")

    # ----- Summary table ------------------------------------------------
    lines.append("## Per-filing breakdown")
    lines.append("")
    lines.append(
        "Cover anchor values: ``primary`` = ``# Part I`` found; "
        "``fallback`` = ``## Item 1`` found (BAC/JNJ style); "
        "``**none**`` = neither found (cleaner will skip cover strip)."
    )
    lines.append("")
    lines.append(
        "Item 10-14 column format: ``stub/hybrid/real/total``. "
        "``stub`` = would be removed by the cleaner; "
        "``hybrid`` = contains ref sentence(s) but has enough non-ref "
        "remainder to survive (e.g. AMT exec biographies, CRM Code of "
        "Conduct); ``real`` = no ref sentence at all."
    )
    lines.append("")
    lines.append(
        "| Ticker | FY | Converter | Cover anchor | TOC links | Bare --- | Strict page sep | Table --- | Item 10-14 (stub/hybrid/real/total) | Item 1C | Item 9A | Truncated | FP risks |"
    )
    lines.append(
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |"
    )
    for s in sorted(stats_list, key=lambda x: (x.ticker, x.fiscal_year)):
        anchor_cell = (
            s.cover_page_anchor_type
            if s.cover_page_anchor_found
            else "**none**"
        )
        lines.append(
            f"| {s.ticker} | {s.fiscal_year} | {s.converter} "
            f"| {anchor_cell} "
            f"| {s.toc_link_count} | {s.bare_dash_count} | {s.page_sep_strict_count} | {s.table_sep_count} "
            f"| {s.item_10_14_stub_count}/{s.item_10_14_hybrid_count}/{s.item_10_14_real_count}/{s.item_10_14_total} "
            f"| {'real' if (s.item_1c_present and not s.item_1c_stub_like) else ('stub' if s.item_1c_present else '-')} "
            f"| {'Y' if s.item_9a_present else '-'} "
            f"| {len(s.truncated_headings)} "
            f"| {len(s.fp_warnings)} |"
        )
    lines.append("")

    # ----- Aggregated heading variants ----------------------------------
    lines.append("## Heading variants (aggregated)")
    lines.append("")
    part_total: Counter[str] = Counter()
    item_total: Counter[str] = Counter()
    for s in stats_list:
        part_total.update(s.part_variants)
        item_total.update(s.item_variants)

    lines.append("### Part heading variants")
    for variant, count in part_total.most_common():
        lines.append(f"- `{variant}` × **{count}**")
    lines.append("")

    lines.append("### Item heading variants")
    for variant, count in item_total.most_common():
        lines.append(f"- `{variant}` × **{count}**")
    lines.append("")

    # ----- Sample headings per variant ----------------------------------
    lines.append("### Item heading samples (first 3 per variant)")
    samples_by_variant: dict[str, list[tuple[str, str]]] = {}
    for s in stats_list:
        for h in s.item_headings:
            v = classify_item_heading(h)
            samples_by_variant.setdefault(v, []).append((s.ticker, h))
    for variant in sorted(samples_by_variant):
        lines.append(f"#### `{variant}`")
        for ticker, h in samples_by_variant[variant][:3]:
            lines.append(f"- {ticker}: `{h.strip()}`")
        lines.append("")

    # ----- Truncated headings --------------------------------------------
    lines.append("## Truncated headings (title < 5 chars)")
    lines.append("")
    truncated_any = False
    for s in stats_list:
        if s.truncated_headings:
            truncated_any = True
            for h in s.truncated_headings:
                lines.append(f"- {s.ticker} FY{s.fiscal_year}: `{h.strip()}`")
    if not truncated_any:
        lines.append("_None_")
    lines.append("")

    # ----- Empty-title headings (AMZN-style) -----------------------------
    lines.append("## Empty-title headings (AMZN next-line case)")
    lines.append("")
    empty_any = False
    for s in stats_list:
        if s.empty_title_headings:
            empty_any = True
            for h in s.empty_title_headings:
                lines.append(f"- {s.ticker} FY{s.fiscal_year}: `{h.strip()}`")
    if not empty_any:
        lines.append("_None_")
    lines.append("")

    # ----- Item 1C / 9A / 9B / 9C reality check --------------------------
    lines.append("## Item 1C / 9A / 9B / 9C presence")
    lines.append("")
    lines.append("| Ticker | FY | 1C | 1C stub-like? | 9A | 9B | 9C |")
    lines.append("| --- | --- | --- | --- | --- | --- | --- |")
    for s in sorted(stats_list, key=lambda x: (x.ticker, x.fiscal_year)):
        lines.append(
            f"| {s.ticker} | {s.fiscal_year} "
            f"| {'Y' if s.item_1c_present else '-'} "
            f"| {'Y' if s.item_1c_stub_like else '-'} "
            f"| {'Y' if s.item_9a_present else '-'} "
            f"| {'Y' if s.item_9b_present else '-'} "
            f"| {'Y' if s.item_9c_present else '-'} |"
        )
    lines.append("")

    # ----- False positive risks ------------------------------------------
    lines.append("## False positive risks")
    lines.append("")
    fp_any = False
    for s in stats_list:
        if s.fp_warnings:
            fp_any = True
            lines.append(f"### {s.ticker} FY{s.fiscal_year}")
            for w in s.fp_warnings[:10]:
                lines.append(f"- {w}")
            if len(s.fp_warnings) > 10:
                lines.append(f"- ... and {len(s.fp_warnings) - 10} more")
            lines.append("")
    if not fp_any:
        lines.append("_None detected_")
        lines.append("")

    # ----- Bare-dash sanity check -----------------------------------------
    lines.append("## Bare `---` vs strict page separator (gap analysis)")
    lines.append("")
    lines.append(
        "If `bare_dash` >> `strict_page_sep` for some filing, the spec regex "
        "may miss page separators that have blank lines instead of digit lines "
        "preceding `---`. Check the gap column."
    )
    lines.append("")
    lines.append("| Ticker | FY | Bare --- | Strict page sep | Gap |")
    lines.append("| --- | --- | --- | --- | --- |")
    for s in sorted(stats_list, key=lambda x: (x.ticker, x.fiscal_year)):
        gap = s.bare_dash_count - s.page_sep_strict_count
        marker = " ⚠️" if gap > 5 else ""
        lines.append(
            f"| {s.ticker} | {s.fiscal_year} | {s.bare_dash_count} | {s.page_sep_strict_count} | {gap}{marker} |"
        )
    lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--cache-dir",
        type=Path,
        required=True,
        help="Path to LocalFilingStore base directory (e.g. data/sec_filings)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        required=True,
        help="Path to write the markdown report",
    )
    args = parser.parse_args()

    md_files = sorted(args.cache_dir.rglob("*.md"))
    print(f"Found {len(md_files)} markdown files in {args.cache_dir}")

    stats_list: list[FilingStats] = []
    for path in md_files:
        try:
            s = analyze_filing(path)
            if s is not None:
                stats_list.append(s)
        except Exception as exc:
            print(f"WARN: failed to analyze {path}: {exc}")

    report = render_report(stats_list)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(report)
    print(f"Report written to {args.output} ({len(report)} chars)")


if __name__ == "__main__":
    main()
