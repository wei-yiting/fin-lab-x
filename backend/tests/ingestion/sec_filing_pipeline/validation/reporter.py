"""JSON + Markdown report writers for the validation harness.

Two report shapes:
  - HardGateReport: pass/fail summary for R-10/R-11/R-12/R-13 across a ticker set.
  - DiscoveryReport: per-ticker structural facts (H1/H2/H3/H4 counts, vendor,
    sanity status, sub-section samples) for human round review.
"""

from __future__ import annotations

import datetime as dt
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


def _now_iso() -> str:
    return dt.datetime.now().isoformat(timespec="seconds")


@dataclass
class TickerHardGateRow:
    ticker: str
    rule_results: dict[str, str]  # rule_id → 'satisfied' | 'failed' | 'skipped'
    failures: list[str] = field(default_factory=list)
    h1_missing: list[str] = field(default_factory=list)
    h2_missing: list[str] = field(default_factory=list)
    h2_order_preserved: bool = True

    @property
    def passed(self) -> bool:
        return not self.failures


@dataclass
class HardGateReport:
    round: int
    generated_at: str = field(default_factory=_now_iso)
    mode: str = "hard-gate"
    rules_checked: list[str] = field(default_factory=list)
    summary: dict[str, int] = field(default_factory=dict)
    per_ticker: dict[str, dict] = field(default_factory=dict)
    failures: list[str] = field(default_factory=list)

    def to_json(self) -> str:
        return json.dumps(asdict(self), indent=2, ensure_ascii=False)


@dataclass
class TickerDiscoveryRow:
    ticker: str
    vendor: str
    h1_count: int
    h2_count: int
    h3_count: int
    h4_count: int
    h5_count: int
    h1_first3: list[str]
    h2_first3: list[str]
    h3_samples: list[str]
    sanity_status: str  # 'ok' | 'NEEDS_REVIEW'
    sanity_reason: str
    perf_median_ms: float
    flags: list[str] = field(default_factory=list)
    error: str | None = None


@dataclass
class DiscoveryReport:
    round: int
    generated_at: str = field(default_factory=_now_iso)
    mode: str = "discovery"
    summary: dict[str, Any] = field(default_factory=dict)
    per_ticker: dict[str, dict] = field(default_factory=dict)

    def to_json(self) -> str:
        return json.dumps(asdict(self), indent=2, ensure_ascii=False)


def write_json(report: HardGateReport | DiscoveryReport, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(report.to_json(), encoding="utf-8")


def render_discovery_markdown(report: DiscoveryReport) -> str:
    """Human-readable round summary for J-prep-08 user review."""
    lines: list[str] = []
    lines.append(f"# Discovery Round {report.round}")
    lines.append("")
    lines.append(f"Generated: {report.generated_at}")
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    for key, value in report.summary.items():
        lines.append(f"- **{key}**: {value}")
    lines.append("")
    lines.append("## Per-Ticker")
    lines.append("")
    lines.append(
        "| Ticker | Vendor | H1 | H2 | H3 | H4 | H5 | Perf (ms) | Sanity | Flags |"
    )
    lines.append(
        "|--------|--------|----|----|----|----|----|-----------|--------|-------|"
    )
    for ticker, row in sorted(report.per_ticker.items()):
        if row.get("error"):
            lines.append(
                f"| {ticker} | — | — | — | — | — | — | — | ERROR | {row['error']} |"
            )
            continue
        flags = ",".join(row.get("flags", [])) or "—"
        lines.append(
            f"| {ticker} "
            f"| {row['vendor']} "
            f"| {row['h1_count']} "
            f"| {row['h2_count']} "
            f"| {row['h3_count']} "
            f"| {row['h4_count']} "
            f"| {row['h5_count']} "
            f"| {row['perf_median_ms']:.0f} "
            f"| {row['sanity_status']} "
            f"| {flags} |"
        )
    lines.append("")
    lines.append("## H1/H2 Samples (first 3 of each ticker)")
    lines.append("")
    for ticker, row in sorted(report.per_ticker.items()):
        if row.get("error"):
            continue
        lines.append(f"### {ticker}")
        lines.append("")
        lines.append("**H1**: " + (", ".join(row.get("h1_first3", [])) or "_none_"))
        lines.append("")
        lines.append("**H2**: " + (", ".join(row.get("h2_first3", [])) or "_none_"))
        lines.append("")
        if row.get("h3_samples"):
            lines.append(
                "**H3 sample**: " + ", ".join(row["h3_samples"][:5])
            )
            lines.append("")
    return "\n".join(lines) + "\n"


def render_hard_gate_markdown(report: HardGateReport) -> str:
    lines: list[str] = []
    lines.append(f"# Hard-Gate Round {report.round}")
    lines.append("")
    lines.append(f"Generated: {report.generated_at}")
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    for key, value in report.summary.items():
        lines.append(f"- **{key}**: {value}")
    lines.append("")
    if report.failures:
        lines.append("## Failures")
        lines.append("")
        for failure in report.failures:
            lines.append(f"- {failure}")
        lines.append("")
    lines.append("## Per-Ticker")
    lines.append("")
    lines.append("| Ticker | Result | Failures |")
    lines.append("|--------|--------|----------|")
    for ticker, row in sorted(report.per_ticker.items()):
        result = "PASS" if not row.get("failures") else "FAIL"
        failures = "; ".join(row.get("failures", [])) or "—"
        lines.append(f"| {ticker} | {result} | {failures} |")
    lines.append("")
    return "\n".join(lines) + "\n"
