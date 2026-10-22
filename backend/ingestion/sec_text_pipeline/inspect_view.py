"""Human-facing render views over a :class:`ParsedFiling`.

The filing store is machine-facing JSON; these functions derive the
human-readable surfaces used for prelude spot-checks and detection
failure analysis. Render logic lives here, outside the frozen
``filing_models.py`` schema module.

The prelude verdict is inferred at render time — the schema stores no
judgment, only ``prelude: str`` where ``""`` means "no prelude". A
reclassified leading block (detection-time prelude over the validity
threshold) is recognizable by ``blocks[0].heading == ""``: anchored
headings are never empty, so an empty heading in first position is the
reclassification marker.
"""

from backend.ingestion.sec_text_pipeline.filing_models import (
    FlatItem,
    ParsedFiling,
    ParsedItem,
    StructuredItem,
)

_RECLASSIFIED_LABEL = "reclassified leading block"

# FlatItem bodies render as a head+tail preview (full char count stays exact):
# a flat item's raw text can bleed past its own boundary into the next item
# (see parser._trim_section_text — observed on AAPL FY2025's Item 11 carrying
# Items 12-15), and that failure only shows up at the tail. A head-only
# preview would hide it; `--section` remains the full-text path.
_FLAT_PREVIEW_EACH_END = 300

# A degraded filing's text is the whole document, so its preview budget is
# larger: the head must reach past the body opening into real content, and
# the tail must show whether the signature-block cut landed correctly.
_DEGRADED_PREVIEW_EACH_END = 1500


def _prelude_verdict(item: StructuredItem, compact: bool = False) -> str:
    if item.prelude:
        return f"valid ({len(item.prelude):,} chars)"
    if item.blocks[0].heading == "":
        chars = len(item.blocks[0].text)
        if compact:
            return f"reclassified ({chars:,} chars)"
        return f"{_RECLASSIFIED_LABEL} ({chars:,} chars in blocks[0])"
    return "absent"


def _flat_preview(text: str, each_end: int = _FLAT_PREVIEW_EACH_END) -> str:
    if len(text) <= 2 * each_end:
        return text
    head = text[:each_end]
    tail = text[-each_end:]
    skipped = len(text) - 2 * each_end
    return f"{head}\n\n… [{skipped:,} chars omitted] …\n\n{tail}"


def _item_chars(item: StructuredItem) -> int:
    return len(item.prelude) + sum(len(block.text) for block in item.blocks)


def _structured_count(filing: ParsedFiling) -> int:
    return sum(1 for item in filing.items if isinstance(item, StructuredItem))


def _header_lines(filing: ParsedFiling) -> list[str]:
    m = filing.metadata
    if filing.is_degraded:
        counts = (
            f"DEGRADED ingest — section detection: "
            f"{m.section_detection_method or 'unrecorded'} — unstructured "
            f"full text ({len(filing.degraded_text or ''):,} chars)"
        )
    else:
        structured = _structured_count(filing)
        flat = len(filing.items) - structured
        counts = f"{len(filing.items)} items (structured {structured} / flat {flat})"
    return [
        f"{m.ticker} {m.filing_type} FY{m.fiscal_year} — {m.company_name}",
        f"filed {m.filing_date} · accession {m.accession_number} · CIK {m.cik}"
        f" · {m.primary_document} · parsed_at {m.parsed_at}",
        counts,
    ]


def to_inspect_markdown(filing: ParsedFiling) -> str:
    """Full markdown render: every Item's kind, detection verdicts, and
    complete block content, laid out for side-by-side comparison with the
    SEC original. FlatItem bodies appear as a head+tail preview (each end
    capped, middle elided) next to their full char count; ``--section``
    prints them in full."""
    title, source_line, counts = _header_lines(filing)
    lines = [f"# {title} — inspect view", "", source_line, "", counts, ""]
    if filing.is_degraded:
        lines.extend(
            [
                "## Degraded full text",
                "",
                _flat_preview(filing.degraded_text or "", _DEGRADED_PREVIEW_EACH_END),
                "",
            ]
        )
        return "\n".join(lines)
    for item in filing.items:
        lines.extend(_render_item_markdown(item))
    return "\n".join(lines)


def _render_item_markdown(item: ParsedItem) -> list[str]:
    lines = [f"## Item {item.item} — {item.title}", ""]
    if isinstance(item, FlatItem):
        lines.extend(
            [
                "- kind: flat",
                f"- text: {len(item.text):,} chars",
                "",
                _flat_preview(item.text),
                "",
            ]
        )
        return lines
    lines.extend(
        [
            "- kind: structured",
            f"- detection_source: {item.detection_source}",
            f"- prelude: {_prelude_verdict(item)}",
            f"- blocks: {len(item.blocks)}",
            "",
        ]
    )
    if item.prelude:
        lines.extend(["### [prelude]", "", item.prelude, ""])
    total = len(item.blocks)
    for idx, block in enumerate(item.blocks, start=1):
        heading = block.heading or f"({_RECLASSIFIED_LABEL})"
        lines.extend([f"### Block {idx}/{total} — {heading}", "", block.text, ""])
    return lines


def to_summary_text(filing: ParsedFiling) -> str:
    """One-screen summary table — per-Item verdicts only, no body content."""
    header_title, source_line, counts = _header_lines(filing)
    if filing.is_degraded:
        # The header's counts line already carries the whole verdict; a
        # degraded filing has no items to tabulate.
        return "\n".join([header_title, source_line, counts])
    row_fmt = "{:<5} {:<11} {:<13} {:<28} {:>6} {:>9}"
    rows = [
        header_title,
        source_line,
        counts,
        "",
        row_fmt.format("item", "kind", "source", "prelude", "blocks", "chars"),
    ]
    for item in filing.items:
        if isinstance(item, FlatItem):
            rows.append(
                row_fmt.format(item.item, "flat", "—", "—", "—", f"{len(item.text):,}")
            )
        else:
            rows.append(
                row_fmt.format(
                    item.item,
                    "structured",
                    item.detection_source,
                    _prelude_verdict(item, compact=True),
                    len(item.blocks),
                    f"{_item_chars(item):,}",
                )
            )
    return "\n".join(rows)


def to_section_text(filing: ParsedFiling, section_key: str) -> str:
    """Plain-text render of a single Item (case-insensitive item key).

    Raises ``ValueError`` when the key matches no Item in the filing,
    listing the keys that exist.
    """
    key = section_key.strip().lower()
    if filing.is_degraded:
        raise ValueError(
            f"{filing.metadata.ticker} FY{filing.metadata.fiscal_year} was "
            f"ingested degraded (section detection: "
            f"{filing.metadata.section_detection_method or 'unrecorded'}) and "
            f"has no per-Item sections; use the inspect view for its full text."
        )
    for item in filing.items:
        if item.item == key:
            return _section_text(item)
    available = ", ".join(item.item for item in filing.items)
    raise ValueError(
        f"No item {section_key!r} in {filing.metadata.ticker} "
        f"FY{filing.metadata.fiscal_year} — available: {available}"
    )


def _section_text(item: ParsedItem) -> str:
    if isinstance(item, FlatItem):
        return item.text
    parts = [item.prelude] if item.prelude else []
    for block in item.blocks:
        parts.append(
            f"{block.heading}\n\n{block.text}" if block.heading else block.text
        )
    return "\n\n".join(parts)
