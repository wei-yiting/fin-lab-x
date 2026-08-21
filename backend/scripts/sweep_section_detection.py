#!/usr/bin/env python
"""Sweep tickers for edgartools' raw section-detection method (DEV-176).

``edgar.documents.document.Section.detection_method`` — a plain ``str``
edgartools sets to one of ``'toc'``, ``'heading'``, ``'pattern'``,
``'html_fallback'``, ``'unknown'``, or a comma-joined merge of several
(``'heading,pattern'``, when its own hybrid detector's dedup pass merges
duplicate sections found by more than one strategy) — is never read anywhere
in ``sec_text_pipeline`` today. ``toc``/``heading`` are the two reliable
strategies; ``pattern``/``html_fallback``/``unknown`` are degraded fallbacks
that produce semantically-named sections (e.g. ``mda``) with no reliable
item-key shape, which is why AMD's FY2025 10-K parses to zero substantive
items (see DEV-172, the parent spec).

This script is pure observation: it reads ``Section.detection_method``
directly off ``fetch_filing_bundle``'s ``TenK`` (the same fetch seam
``sec_text_pipeline.parser`` already uses) and separately cross-checks the
real ``parse_filing()`` outcome for the same ticker. It does not change any
pipeline code. ``parse_filing()`` still populates the shared
``data/sec_text/`` filing-store cache as a side effect, same as any other
caller (``ingest_tickers.py``, the ``sec_text_pipeline`` CLI).

Sweep corpus (``SWEEP_TICKERS``): DEV-162's finalized 16-ticker GICS
sector-x-cap grid, plus AMD (DEV-172's known repro). DEV-162's curation never
excluded a candidate via ``EmptyFilingError`` — its 2026-08-20 sync comment
records all 16 tickers parsing successfully on the first pass — so there is
no historical exclusion list to fold in here (DEV-176 acceptance criterion:
"if DEV-162 curation ever excluded a candidate via EmptyFilingError, include
and annotate it" — checked, none found).

Usage:
    uv run python -m backend.scripts.sweep_section_detection
    uv run python -m backend.scripts.sweep_section_detection AMD NVDA
"""

from __future__ import annotations

import argparse
import sys
from collections import Counter
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Literal

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

from backend.common.errors import FinLabError  # noqa: E402

# Latest-fiscal-year resolution deliberately reuses sec_core's private helper —
# same justification and precedent as ingest_tickers.py: the public parse path
# requires an explicit year, and duplicating the "latest 10-K period_of_report"
# lookup here would just drift. Read-only use from a one-shot sweep script.
from backend.common.sec_core import (  # noqa: E402
    FilingType,
    _resolve_latest_fiscal_year,
    fetch_filing_bundle,
)
from backend.ingestion.sec_text_pipeline.parser import (  # noqa: E402
    EmptyFilingError,
    parse_filing,
)

if TYPE_CHECKING:
    from edgar.documents.document import Section

# DEV-162's finalized 16-ticker GICS sector x cap grid — mirrors
# backend/evals/scenarios/sec_retrieval_ab/curation/ingest_tickers.py::TICKER_GRID
# (branch feat/sec-retrieval-eval-dataset) — plus AMD, the known degraded-ingest
# repro case (DEV-172).
SWEEP_TICKERS: tuple[str, ...] = (
    "NVDA",
    "DDOG",
    "LLY",
    "PODD",
    "JPM",
    "COIN",
    "AMZN",
    "DECK",
    "GOOGL",
    "CAT",
    "AXON",
    "COST",
    "XOM",
    "NEE",
    "PLD",
    "LIN",
    "AMD",
)

#: DEV-172's ratified trigger rule: these methods lose reliable item-key
#: structure. toc/heading are the two reliable strategies.
DEGRADED_METHODS: frozenset[str] = frozenset({"pattern", "html_fallback", "unknown"})
STANDARD_METHODS: frozenset[str] = frozenset({"toc", "heading"})

ParseOutcome = Literal["ok", "empty_filing", "error", "not_run"]
Classification = Literal["degraded", "standard", "undetermined"]


@dataclass(frozen=True)
class SectionObservation:
    """One edgartools ``Section``, reduced to the fields this sweep records."""

    name: str
    item: str | None
    part: str | None
    detection_method: str
    confidence: float


@dataclass
class TickerSweepResult:
    """One ticker's sweep outcome — raw section evidence plus a parse_filing
    cross-check, so a failure at either stage stays legible and distinct."""

    ticker: str
    fiscal_year: int | None = None
    accession_number: str | None = None
    sections: tuple[SectionObservation, ...] = ()
    #: Set when resolving the fiscal year or fetching the bundle fails —
    #: no section evidence exists for this ticker at all.
    fetch_error: str | None = None
    parse_outcome: ParseOutcome = "not_run"
    parse_item_count: int | None = None
    parse_error: str | None = None


def split_methods(raw: str) -> frozenset[str]:
    """Split a possibly comma-joined ``detection_method`` into its tokens.

    edgartools' hybrid detector's dedup pass merges sections found by more
    than one strategy into ``','.join(sorted(methods))`` (e.g.
    ``'heading,pattern'``) — a real, reachable shape, not a hypothetical.
    """
    return frozenset(token.strip() for token in raw.split(",") if token.strip())


def ticker_methods(result: TickerSweepResult) -> frozenset[str]:
    """Every distinct detection-method token observed across the filing."""
    methods: set[str] = set()
    for section in result.sections:
        methods |= split_methods(section.detection_method)
    return frozenset(methods)


def classify_ticker(result: TickerSweepResult) -> Classification:
    """Degraded when any section used a degraded method (DEV-172: filing-
    level classification is inclusive — one degraded section means content
    loss somewhere even if the rest of the filing is clean). Undetermined
    when there is no detection-method evidence at all (fetch failed, or
    edgartools produced zero sections)."""
    if result.fetch_error is not None:
        return "undetermined"
    methods = ticker_methods(result)
    if not methods:
        return "undetermined"
    if methods & DEGRADED_METHODS:
        return "degraded"
    return "standard"


def degraded_tickers(results: Sequence[TickerSweepResult]) -> list[str]:
    return sorted(r.ticker for r in results if classify_ticker(r) == "degraded")


def standard_tickers(results: Sequence[TickerSweepResult]) -> list[str]:
    return sorted(r.ticker for r in results if classify_ticker(r) == "standard")


def undetermined_tickers(results: Sequence[TickerSweepResult]) -> list[str]:
    return sorted(r.ticker for r in results if classify_ticker(r) == "undetermined")


def method_distribution(results: Sequence[TickerSweepResult]) -> Counter[str]:
    """Ticker-level: how many tickers' observed method-set includes each
    method (a ticker mixing toc and pattern counts under both)."""
    dist: Counter[str] = Counter()
    for result in results:
        dist.update(ticker_methods(result))
    return dist


def section_method_distribution(results: Sequence[TickerSweepResult]) -> Counter[str]:
    """Section-level: raw count of every section (post comma-split) by
    method, across the whole swept corpus."""
    dist: Counter[str] = Counter()
    for result in results:
        for section in result.sections:
            dist.update(split_methods(section.detection_method))
    return dist


def _observe_section(section: "Section") -> SectionObservation:
    return SectionObservation(
        name=section.name,
        item=section.item,
        part=section.part,
        detection_method=section.detection_method,
        confidence=section.confidence,
    )


def sweep_ticker(ticker: str) -> TickerSweepResult:
    """Fetch + observe one ticker's latest 10-K.

    Two independent stages, each recorded separately: (1) the raw edgartools
    section detection-method evidence, read directly off ``fetch_filing_bundle``
    (never surfaced by ``sec_text_pipeline`` today); (2) a cross-check run
    through the real ``parse_filing()`` pipeline, to see whether the detected
    degradation currently manifests as ``EmptyFilingError`` or a reduced item
    count. A failure in stage 1 leaves no section evidence (``fetch_error``
    set); a failure in stage 2 still keeps stage 1's evidence.
    """
    ticker_norm = ticker.strip().upper()

    try:
        fiscal_year = _resolve_latest_fiscal_year(ticker_norm)
    except (FinLabError, ValueError) as exc:
        return TickerSweepResult(
            ticker=ticker_norm, fetch_error=f"{type(exc).__name__}: {exc}"
        )

    try:
        bundle = fetch_filing_bundle(ticker_norm, FilingType.TEN_K, fiscal_year)
    except (FinLabError, ValueError) as exc:
        return TickerSweepResult(
            ticker=ticker_norm,
            fiscal_year=fiscal_year,
            fetch_error=f"{type(exc).__name__}: {exc}",
        )

    sections = tuple(
        _observe_section(section) for section in bundle.tenk.sections.values()
    )
    result = TickerSweepResult(
        ticker=ticker_norm,
        fiscal_year=fiscal_year,
        accession_number=bundle.accession_number,
        sections=sections,
    )

    try:
        parsed = parse_filing(ticker_norm, fiscal_year)
        result.parse_outcome = "ok"
        result.parse_item_count = len(parsed.items)
    except EmptyFilingError as exc:
        result.parse_outcome = "empty_filing"
        result.parse_error = str(exc)
    except (FinLabError, ValueError) as exc:
        result.parse_outcome = "error"
        result.parse_error = f"{type(exc).__name__}: {exc}"

    return result


def _parse_outcome_cell(result: TickerSweepResult) -> str:
    if result.fetch_error is not None:
        return f"fetch failed: {result.fetch_error}"
    if result.parse_outcome == "ok":
        return f"ok ({result.parse_item_count} items)"
    if result.parse_outcome == "empty_filing":
        return f"EmptyFilingError: {result.parse_error}"
    if result.parse_outcome == "error":
        return f"error: {result.parse_error}"
    return "not run"


def render_report(results: Sequence[TickerSweepResult]) -> str:
    """Markdown report: per-ticker table, raw section name shapes, detection
    method distribution, and the degraded ticker list — the DEV-176 deliverable
    for the DEV-172 comment."""
    ordered = sorted(results, key=lambda r: r.ticker)
    lines: list[str] = ["# Section-detection sweep (DEV-176)", ""]

    lines.append("## Per-ticker")
    lines.append("")
    lines.append(
        "| Ticker | FY | Sections | Detection method(s) | Class | parse_filing() |"
    )
    lines.append("| --- | --- | --- | --- | --- | --- |")
    for r in ordered:
        methods = ", ".join(sorted(ticker_methods(r))) or "—"
        lines.append(
            f"| {r.ticker} | {r.fiscal_year if r.fiscal_year is not None else '—'} "
            f"| {len(r.sections)} | {methods} | {classify_ticker(r)} "
            f"| {_parse_outcome_cell(r)} |"
        )

    lines.append("")
    lines.append("## Section name shapes (raw evidence)")
    for r in ordered:
        if not r.sections:
            continue
        lines.append("")
        lines.append(f"**{r.ticker}** ({len(r.sections)} sections):")
        for s in r.sections:
            lines.append(
                f"- `{s.name}` (item={s.item!r}, part={s.part!r}, "
                f"method={s.detection_method!r}, confidence={s.confidence:.2f})"
            )

    lines.append("")
    lines.append("## Detection method distribution")
    lines.append("")
    lines.append(
        "Ticker-level (a mixed-method ticker counts under each method it uses):"
    )
    lines.append("")
    lines.append("| Method | Tickers |")
    lines.append("| --- | --- |")
    for method, count in sorted(method_distribution(results).items()):
        lines.append(f"| {method} | {count} |")
    lines.append("")
    lines.append("Section-level (raw count across the whole corpus):")
    lines.append("")
    lines.append("| Method | Sections |")
    lines.append("| --- | --- |")
    for method, count in sorted(section_method_distribution(results).items()):
        lines.append(f"| {method} | {count} |")

    degraded = degraded_tickers(results)
    undetermined = undetermined_tickers(results)
    determined = len(results) - len(undetermined)
    rate = (len(degraded) / determined * 100) if determined else 0.0

    lines.append("")
    lines.append("## Degraded ticker list")
    lines.append("")
    lines.append(
        f"{len(degraded)} / {determined} determined tickers ({rate:.0f}%) degraded: "
        f"{', '.join(degraded) if degraded else '(none)'}"
    )

    if undetermined:
        lines.append("")
        lines.append("## Undetermined (no detection-method evidence)")
        lines.append("")
        for r in ordered:
            if r.ticker in undetermined:
                lines.append(f"- {r.ticker}: {r.fetch_error}")

    lines.append("")
    lines.append(
        "DEV-162 curation exclusions: none — its 2026-08-20 sync comment records "
        "all 16 grid tickers parsing successfully on the first pass, so no "
        "candidate was ever swapped out for `EmptyFilingError`."
    )

    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    arg_parser = argparse.ArgumentParser(
        description=(
            "Sweep tickers for edgartools' raw section-detection method and "
            "report a distribution table + degraded-ticker list. Pure "
            "observation — never modifies sec_text_pipeline."
        )
    )
    arg_parser.add_argument(
        "tickers",
        nargs="*",
        help=f"Ticker symbols to sweep (default: the {len(SWEEP_TICKERS)}-ticker "
        "DEV-176 sweep corpus)",
    )
    args = arg_parser.parse_args(argv)
    tickers = tuple(t.strip().upper() for t in args.tickers) or SWEEP_TICKERS

    results: list[TickerSweepResult] = []
    for ticker in tickers:
        result = sweep_ticker(ticker)
        status = classify_ticker(result)
        print(f"[{status.upper()}] {ticker}: {_parse_outcome_cell(result)}", flush=True)
        results.append(result)

    print()
    print(render_report(results))

    return 1 if undetermined_tickers(results) else 0


if __name__ == "__main__":
    sys.exit(main())
