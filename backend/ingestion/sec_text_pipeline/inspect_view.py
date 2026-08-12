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


def _prelude_verdict(item: StructuredItem, compact: bool = False) -> str:
    if item.prelude:
        return f"valid ({len(item.prelude):,} chars)"
    if item.blocks[0].heading == "":
        chars = len(item.blocks[0].text)
        if compact:
            return f"reclassified ({chars:,} chars)"
        return f"{_RECLASSIFIED_LABEL} ({chars:,} chars in blocks[0])"
    return "absent"


def _item_chars(item: StructuredItem) -> int:
    return len(item.prelude) + sum(len(block.text) for block in item.blocks)


def _structured_count(filing: ParsedFiling) -> int:
    return sum(1 for item in filing.items if isinstance(item, StructuredItem))


def _header_lines(filing: ParsedFiling) -> list[str]:
    m = filing.metadata
    structured = _structured_count(filing)
    flat = len(filing.items) - structured
    return [
        f"{m.ticker} {m.filing_type} FY{m.fiscal_year} — {m.company_name}",
        f"filed {m.filing_date} · accession {m.accession_number} · CIK {m.cik}"
        f" · {m.primary_document} · parsed_at {m.parsed_at}",
        f"{len(filing.items)} items (structured {structured} / flat {flat})",
    ]


def to_inspect_markdown(filing: ParsedFiling) -> str:
    """Full markdown render: every Item's kind, detection verdicts, and
    complete content, laid out for side-by-side comparison with the SEC
    original."""
    title, source_line, counts = _header_lines(filing)
    lines = [f"# {title} — inspect view", "", source_line, "", counts, ""]
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
                item.text,
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
