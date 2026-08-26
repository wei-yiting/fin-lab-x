#!/usr/bin/env python
"""Sweep tickers for edgartools' raw section-detection method.

``edgar.documents.document.Section.detection_method`` — a plain ``str``
edgartools sets to one of ``'toc'``, ``'heading'``, ``'pattern'``,
``'html_fallback'``, ``'unknown'``, or a comma-joined merge of several
(``'heading,pattern'``, when its own hybrid detector's dedup pass merges
duplicate sections found by more than one strategy) — is never read anywhere
in ``sec_text_pipeline`` today. ``toc``/``heading`` are the two reliable
strategies; ``pattern``/``html_fallback``/``unknown`` are degraded fallbacks
that produce semantically-named sections (e.g. ``mda``) with no reliable
item-key shape, which is why AMD's FY2025 10-K parses to zero substantive
items (see the parent degraded-ingest spec).

This script is pure observation: it reads ``Section.detection_method``
directly off ``fetch_filing_bundle``'s ``TenK`` (the same fetch seam
``sec_text_pipeline.parser`` already uses) and separately cross-checks the
real ``parse_filing()`` outcome for the same ticker. It does not change any
pipeline code, nor does it touch the shared ``data/sec_text/`` filing-store
cache that other callers (``ingest_tickers.py``, the ``sec_text_pipeline``
CLI) read and write — the cross-check passes ``parse_filing()`` a local
no-op store built for exactly this purpose.

Sweep corpus (``SWEEP_TICKERS``): the finalized 16-ticker GICS
sector-x-cap grid, plus AMD (the known degraded-ingest repro case). That
grid's curation never excluded a candidate via ``EmptyFilingError`` — its
2026-08-20 sync comment records all 16 tickers parsing successfully on the
first pass — so there is no historical exclusion list to fold into the
corpus below.

Usage:
    uv run python -m backend.scripts.sweep_section_detection
    uv run python -m backend.scripts.sweep_section_detection AMD NVDA

Prints the report to stdout; posting it to the parent spec issue as a
comment is a manual hand-off after the run, not something this script does.
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

# Latest-fiscal-year resolution deliberately reuses sec_core's private helper:
# the public parse path requires an explicit year, and duplicating the
# "latest 10-K period_of_report" lookup here would just drift. Read-only use
# from a one-shot sweep script.
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

    from backend.ingestion.sec_text_pipeline.filing_models import ParsedFiling

# A 16-ticker GICS sector x market-cap grid (at least one large-cap per
# sector, roughly half the sectors adding a mid/small-cap) — plus AMD, the
# known degraded-ingest repro case.
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

#: The ratified trigger rule: these are the only two methods known to
#: keep reliable item-key structure. classify_ticker() fails closed — a
#: method string outside this set (a degraded one, or one this sweep has
#: never seen, e.g. after an edgartools upgrade) counts as degraded rather
#: than being silently trusted.
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
    sections: tuple[SectionObservation, ...] = ()
    #: Set when resolving the fiscal year or fetching the bundle fails — a
    #: ticker-lookup / network problem, not evidence about this filing.
    fetch_error: str | None = None
    #: Set when the bundle fetch succeeds but edgartools produces zero
    #: sections — a problem with THIS filing's own structure/parseability
    #: (its document likely failed to parse), distinct from fetch_error.
    filing_error: str | None = None
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
    """Standard only when every observed method is toc/heading (filing-level
    classification is inclusive — one non-standard section
    means content loss somewhere even if the rest of the filing is clean).
    Fails closed: a method string outside STANDARD_METHODS counts as
    degraded whether or not this sweep recognizes it, so an unfamiliar
    future value can never be silently trusted. Undetermined when there is
    no detection-method evidence at all — either a fetch_error (ticker
    lookup / network problem) or a filing_error (this specific filing's
    document produced zero sections); the two are recorded separately on
    the result even though both classify the same way here for now."""
    if result.fetch_error is not None:
        return "undetermined"
    methods = ticker_methods(result)
    if not methods:
        return "undetermined"
    if methods <= STANDARD_METHODS:
        return "standard"
    return "degraded"


def degraded_tickers(results: Sequence[TickerSweepResult]) -> list[str]:
    return sorted(r.ticker for r in results if classify_ticker(r) == "degraded")


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


class _NonPersistingStore:
    """Satisfies FilingStore without touching disk — sweep_ticker() only
    needs parse_filing()'s return value, never a persisted copy."""

    def get(
        self, ticker: str, filing_type: FilingType, fiscal_year: int
    ) -> "ParsedFiling | None":
        return None

    def save(self, filing: "ParsedFiling") -> None:
        pass


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
    filing_error = None
    if not sections:
        filing_error = (
            f"fetched {ticker_norm} FY{fiscal_year} successfully but edgartools "
            f"produced 0 sections — a problem with this filing's own document "
            f"(it likely failed to parse inside edgartools), not a ticker "
            f"lookup problem."
        )
    result = TickerSweepResult(
        ticker=ticker_norm,
        fiscal_year=fiscal_year,
        sections=sections,
        filing_error=filing_error,
    )

    try:
        parsed = parse_filing(
            ticker_norm, fiscal_year, force=True, store=_NonPersistingStore()
        )
        result.parse_outcome = "ok"
        result.parse_item_count = len(parsed.items)
    except EmptyFilingError as exc:
        result.parse_outcome = "empty_filing"
        result.parse_error = str(exc)
    except (FinLabError, ValueError) as exc:
        result.parse_outcome = "error"
        result.parse_error = f"{type(exc).__name__}: {exc}"

    return result


def _render_parse_outcome(result: TickerSweepResult) -> str:
    """The ``parse_filing()`` cross-check result alone — independent of
    ``fetch_error``/``filing_error`` — so a filing-error ticker can still
    show it instead of having its cross-check outcome hidden."""
    if result.parse_outcome == "ok":
        return f"ok ({result.parse_item_count} items)"
    if result.parse_outcome == "empty_filing":
        return f"EmptyFilingError: {result.parse_error}"
    if result.parse_outcome == "error":
        return f"error: {result.parse_error}"
    return "not run"


def _parse_outcome_cell(result: TickerSweepResult) -> str:
    if result.fetch_error is not None:
        return f"fetch failed: {result.fetch_error}"
    if result.filing_error is not None:
        return (
            f"filing error: {result.filing_error} "
            f"| parse_filing(): {_render_parse_outcome(result)}"
        )
    return _render_parse_outcome(result)


def render_report(results: Sequence[TickerSweepResult]) -> str:
    """Markdown report: per-ticker table, raw section name shapes, detection
    method distribution, and the degraded ticker list — the deliverable for
    the parent degraded-ingest spec's tracking comment."""
    ordered = sorted(results, key=lambda r: r.ticker)
    lines: list[str] = ["# Section-detection sweep", ""]

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
                lines.append(f"- {r.ticker}: {r.fetch_error or r.filing_error}")

    if {r.ticker for r in results} == set(SWEEP_TICKERS):
        lines.append("")
        lines.append(
            "Sweep-corpus curation exclusions: none — the grid's 2026-08-20 "
            "sync comment records all 16 tickers parsing successfully on the "
            "first pass, so no candidate was ever swapped out for "
            "`EmptyFilingError`."
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
        "sweep corpus)",
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
