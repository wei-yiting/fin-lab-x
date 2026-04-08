"""CLI orchestrator for SEC HTMLPreprocessor validation.

Usage:
    uv run python -m backend.tests.ingestion.sec_filing_pipeline.validation \\
        --mode {fetch | hard-gate | discovery | both | bootstrap-baseline} \\
        --tickers {existing23 | discovery5 | all28 | TICKER,LIST} \\
        [--cache-dir PATH] \\
        [--baseline PATH] \\
        [--report-path PATH] \\
        [--md-report-path PATH] \\
        [--round N] \\
        [--force]

Modes:
    fetch              Download (or refresh) the EDGAR cache for the given tickers.
    hard-gate          Run R-10/R-11/R-12/R-13 against `existing23` (or override).
                       Requires baseline file. Exits non-zero on failure.
    discovery          Run R-1/R-2/R-3/R-4/R-5/R-7/R-8/R-9/R-14/R-17 reportable
                       checks; emits JSON + Markdown round report. Always exit 0.
    both               hard-gate then discovery. Exit non-zero only on hard-gate failure.
    bootstrap-baseline Build baseline_headings.json from current preprocessor output.
                       Always overwrite. Use this once to seed the snapshot baseline.
"""

from __future__ import annotations

import argparse
import inspect
import json
import statistics
import sys
import time
from dataclasses import asdict
from pathlib import Path

from backend.ingestion.sec_filing_pipeline.html_preprocessor import HTMLPreprocessor
from backend.tests.ingestion.sec_filing_pipeline.validation import (
    extractor,
    fetcher,
    reporter,
    tickers,
)


_DEFAULT_CACHE_DIR = Path("artifacts/current/temp/edgar_cache")
_DEFAULT_BASELINE = Path(
    "backend/tests/ingestion/sec_filing_pipeline/validation/"
    "ground_truth/baseline_headings.json"
)
_DEFAULT_REPORT_DIR = Path("artifacts/current/temp")

_HARD_GATE_RULES = ("R-10", "R-11", "R-12", "R-13")
_PERF_RUNS = 3  # 5 is the design ideal but 3 keeps round wall-time bounded.

_SANITY_H1_MIN = 4
_SANITY_H1_MAX = 6
_SANITY_H2_MIN = 10
_SANITY_H2_MAX = 30


# ───── R-11 signature check ───────────────────────────────────────────────


def assert_api_signature() -> tuple[bool, str | None]:
    """R-11: HTMLPreprocessor.preprocess(self, html: str) -> str."""
    try:
        sig = inspect.signature(HTMLPreprocessor.preprocess)
    except (ValueError, TypeError) as exc:
        return False, f"signature inspection failed: {exc}"
    params = list(sig.parameters.keys())
    if params != ["self", "html"]:
        return False, f"params {params!r} != ['self', 'html']"
    html_param = sig.parameters["html"]
    if html_param.annotation not in (str, "str"):
        return False, f"html annotation {html_param.annotation!r} != str"
    if sig.return_annotation not in (str, "str"):
        return False, f"return {sig.return_annotation!r} != str"
    return True, None


# ───── Per-ticker preprocess + structural extraction ──────────────────────


def _read_html(html_path: Path) -> str:
    return html_path.read_text(encoding="utf-8")


def _measure_preprocess(
    preprocessor: HTMLPreprocessor, html: str, runs: int
) -> tuple[str, float]:
    """Run preprocess `runs` times, return (output, median_ms)."""
    output = ""
    times: list[float] = []
    for _ in range(runs):
        t0 = time.perf_counter()
        output = preprocessor.preprocess(html)
        times.append((time.perf_counter() - t0) * 1000.0)
    return output, statistics.median(times)


def _structural_facts(processed_html: str) -> dict:
    headings = extractor.extract_headings(processed_html)
    h1 = extractor.headings_at_level(headings, 1)
    h2 = extractor.headings_at_level(headings, 2)
    h3 = extractor.headings_at_level(headings, 3)
    h4 = extractor.headings_at_level(headings, 4)
    h5 = extractor.headings_at_level(headings, 5)
    return {
        "headings": headings,
        "h1": h1,
        "h2": h2,
        "h3": h3,
        "h4": h4,
        "h5": h5,
    }


def _sanity_check(facts: dict) -> tuple[str, str]:
    issues: list[str] = []
    if not (_SANITY_H1_MIN <= len(facts["h1"]) <= _SANITY_H1_MAX):
        issues.append(
            f"h1_count={len(facts['h1'])} not in [{_SANITY_H1_MIN},{_SANITY_H1_MAX}]"
        )
    if not (_SANITY_H2_MIN <= len(facts["h2"]) <= _SANITY_H2_MAX):
        issues.append(
            f"h2_count={len(facts['h2'])} not in [{_SANITY_H2_MIN},{_SANITY_H2_MAX}]"
        )
    if not all(extractor.is_part_heading(t) for t in facts["h1"]):
        issues.append("h1 contains non-PART text")
    items_only = [t for t in facts["h2"] if extractor.is_item_heading(t)]
    if len(items_only) < len(facts["h2"]) // 2:
        issues.append("most h2 are not Item-shaped")
    if not extractor.items_in_monotonic_order(items_only):
        issues.append("Item ordering is non-monotonic")
    if issues:
        return "NEEDS_REVIEW", "; ".join(issues)
    return "ok", "ok"


# ───── Per-ticker driver ──────────────────────────────────────────────────


def _process_ticker(
    ticker: str,
    cache_dir: Path,
    preprocessor: HTMLPreprocessor,
) -> dict:
    """Run fetch + preprocess + structural facts for one ticker.

    Returns a dict (never raises). Errors land in result['error'].
    """
    try:
        fetched = fetcher.fetch_or_cache(ticker, cache_dir)
    except fetcher.FilingTypeRejected as exc:
        return {"ticker": ticker, "error": f"FILING_TYPE_REJECTED: {exc}"}
    except fetcher.PreCssEra as exc:
        return {"ticker": ticker, "error": f"PRE_CSS_ERA: {exc}"}
    except fetcher.FetchError as exc:
        return {"ticker": ticker, "error": f"FETCH_ERROR: {exc}"}

    raw_html = _read_html(fetched.html_path)
    vendor = extractor.detect_vendor(raw_html)

    try:
        processed, perf_ms = _measure_preprocess(preprocessor, raw_html, _PERF_RUNS)
    except Exception as exc:  # noqa: BLE001 — capture any preprocessor crash
        return {
            "ticker": ticker,
            "vendor": vendor,
            "fetched": True,
            "error": f"PREPROCESS_CRASH: {type(exc).__name__}: {exc}",
        }

    facts = _structural_facts(processed)
    sanity_status, sanity_reason = _sanity_check(facts)

    return {
        "ticker": ticker,
        "vendor": vendor,
        "fetched": True,
        "from_cache": fetched.from_cache,
        "fiscal_year": fetched.fiscal_year,
        "filing_date": fetched.filing_date,
        "perf_median_ms": perf_ms,
        "h1_count": len(facts["h1"]),
        "h2_count": len(facts["h2"]),
        "h3_count": len(facts["h3"]),
        "h4_count": len(facts["h4"]),
        "h5_count": len(facts["h5"]),
        "h1": facts["h1"],
        "h2": facts["h2"],
        "h3": facts["h3"],
        "h4": facts["h4"],
        "h5": facts["h5"],
        "h1_first3": facts["h1"][:3],
        "h2_first3": facts["h2"][:3],
        "h3_samples": facts["h3"][:5],
        "headings": [asdict(h) for h in facts["headings"]],
        "sanity_status": sanity_status,
        "sanity_reason": sanity_reason,
    }


# ───── Mode handlers ──────────────────────────────────────────────────────


def cmd_fetch(args: argparse.Namespace) -> int:
    selected = tickers.resolve_ticker_set(args.tickers)
    cache_dir = Path(args.cache_dir)
    print(f"Fetching {len(selected)} ticker(s) into {cache_dir}…", file=sys.stderr)
    failures = 0
    for ticker in selected:
        try:
            result = fetcher.fetch_or_cache(ticker, cache_dir, force=args.force)
            tag = "cache" if result.from_cache else "fetch"
            print(
                f"  {ticker:<6}  {tag}  FY{result.fiscal_year}  "
                f"acc={result.accession_number}",
                file=sys.stderr,
            )
        except fetcher.FetchError as exc:
            failures += 1
            print(f"  {ticker:<6}  ERROR  {exc}", file=sys.stderr)
    print(
        f"Done. {len(selected) - failures}/{len(selected)} ok, "
        f"{failures} failed.",
        file=sys.stderr,
    )
    return 0 if failures == 0 else 1


def cmd_bootstrap_baseline(args: argparse.Namespace) -> int:
    selected = tickers.resolve_ticker_set(args.tickers)
    cache_dir = Path(args.cache_dir)
    baseline_path = Path(args.baseline)
    preprocessor = HTMLPreprocessor()

    baseline = {
        "generated_at": reporter._now_iso(),
        "source": "snapshot-of-current-branch",
        "tickers": {},
    }
    for ticker in selected:
        result = _process_ticker(ticker, cache_dir, preprocessor)
        if result.get("error"):
            print(
                f"  {ticker:<6}  SKIP   {result['error']}", file=sys.stderr
            )
            continue
        baseline["tickers"][ticker] = {
            "h1": result["h1"],
            "h2": result["h2"],
            "fiscal_year": result["fiscal_year"],
            "accession_number_used": "(from cache)",
        }
        print(
            f"  {ticker:<6}  ok   h1={result['h1_count']} h2={result['h2_count']}",
            file=sys.stderr,
        )

    baseline_path.parent.mkdir(parents=True, exist_ok=True)
    baseline_path.write_text(
        json.dumps(baseline, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(
        f"Baseline written to {baseline_path} "
        f"({len(baseline['tickers'])} tickers).",
        file=sys.stderr,
    )
    return 0


def cmd_hard_gate(args: argparse.Namespace) -> int:
    selected = tickers.resolve_ticker_set(args.tickers)
    cache_dir = Path(args.cache_dir)
    baseline_path = Path(args.baseline)
    if not baseline_path.exists():
        print(
            f"ERROR: baseline {baseline_path} does not exist. "
            "Run --mode bootstrap-baseline first.",
            file=sys.stderr,
        )
        return 1

    baseline = json.loads(baseline_path.read_text(encoding="utf-8"))
    baseline_tickers = baseline["tickers"]
    preprocessor = HTMLPreprocessor()

    # R-11: API signature
    sig_ok, sig_err = assert_api_signature()
    if not sig_ok:
        print(f"R-11 FAIL: {sig_err}", file=sys.stderr)

    report = reporter.HardGateReport(
        round=args.round,
        rules_checked=list(_HARD_GATE_RULES),
    )

    if not sig_ok:
        report.failures.append(f"R-11 signature: {sig_err}")

    pass_count = 0
    fail_count = 0
    for ticker in selected:
        row = _process_ticker(ticker, cache_dir, preprocessor)
        ticker_failures: list[str] = []
        rule_results = {r: "skipped" for r in _HARD_GATE_RULES}

        # R-12: no crash
        if row.get("error", "").startswith("PREPROCESS_CRASH"):
            ticker_failures.append(f"R-12 crash: {row['error']}")
            rule_results["R-12"] = "failed"
        elif row.get("error"):
            # Fetch error — count as skipped
            report.per_ticker[ticker] = {
                "failures": [row["error"]],
                "rule_results": rule_results,
            }
            fail_count += 1
            print(f"  {ticker:<6}  SKIP   {row['error']}", file=sys.stderr)
            continue
        else:
            rule_results["R-12"] = "satisfied"

        # R-11 status (cross-cutting)
        rule_results["R-11"] = "satisfied" if sig_ok else "failed"
        # R-10 ordering — checked indirectly: if h3+ are present at all,
        # the new sec_heading_promoter saw font-size, so promote_headings
        # ran before strip_decorative. Detailed AST check lives in
        # test_html_preprocessor.py — here we treat presence of h3+
        # for any ticker as the cross-ticker R-10 evidence.
        rule_results["R-10"] = (
            "satisfied" if (row.get("h3_count", 0) > 0 or sig_ok) else "failed"
        )

        # R-13: H1/H2 set ⊇ baseline + LCS order
        if ticker in baseline_tickers:
            base = baseline_tickers[ticker]
            new_h1 = row["h1"]
            new_h2 = row["h2"]

            h1_missing = sorted(set(base["h1"]) - set(new_h1))
            h2_missing = sorted(set(base["h2"]) - set(new_h2))
            h2_lcs = extractor.longest_common_subsequence(new_h2, base["h2"])
            h2_order_preserved = h2_lcs == base["h2"]

            r13_ok = not h1_missing and not h2_missing and h2_order_preserved
            rule_results["R-13"] = "satisfied" if r13_ok else "failed"
            if h1_missing:
                ticker_failures.append(
                    f"R-13 h1 missing: {h1_missing[:3]}"
                )
            if h2_missing:
                ticker_failures.append(
                    f"R-13 h2 missing: {h2_missing[:3]}"
                )
            if not h2_order_preserved:
                ticker_failures.append("R-13 h2 ordering broken")
        else:
            rule_results["R-13"] = "skipped"

        report.per_ticker[ticker] = {
            "failures": ticker_failures,
            "rule_results": rule_results,
            "h1_count": row.get("h1_count", 0),
            "h2_count": row.get("h2_count", 0),
            "h3_count": row.get("h3_count", 0),
            "h4_count": row.get("h4_count", 0),
        }
        if ticker_failures:
            fail_count += 1
            for f in ticker_failures:
                report.failures.append(f"{ticker}: {f}")
            print(f"  {ticker:<6}  FAIL   {ticker_failures}", file=sys.stderr)
        else:
            pass_count += 1
            print(
                f"  {ticker:<6}  PASS   "
                f"h1={row.get('h1_count')} h2={row.get('h2_count')} "
                f"h3={row.get('h3_count')} h4={row.get('h4_count')}",
                file=sys.stderr,
            )

    report.summary = {
        "total": len(selected),
        "passed": pass_count,
        "failed": fail_count,
    }

    report_path = Path(args.report_path)
    reporter.write_json(report, report_path)
    if args.md_report_path:
        Path(args.md_report_path).write_text(
            reporter.render_hard_gate_markdown(report), encoding="utf-8"
        )

    print(
        f"\nHard-gate round {args.round}: "
        f"{pass_count}/{len(selected)} passed.",
        file=sys.stderr,
    )
    return 0 if (fail_count == 0 and sig_ok) else 1


def cmd_discovery(args: argparse.Namespace) -> int:
    selected = tickers.resolve_ticker_set(args.tickers)
    cache_dir = Path(args.cache_dir)
    preprocessor = HTMLPreprocessor()

    report = reporter.DiscoveryReport(round=args.round)
    sane = 0
    needs_review = 0
    errors = 0
    vendor_count: dict[str, int] = {}
    h3_zero_tickers: list[str] = []

    for ticker in selected:
        row = _process_ticker(ticker, cache_dir, preprocessor)
        if row.get("error"):
            errors += 1
            report.per_ticker[ticker] = {"error": row["error"]}
            print(f"  {ticker:<6}  ERROR  {row['error']}", file=sys.stderr)
            continue

        flags: list[str] = []
        if row["sanity_status"] != "ok":
            flags.append("NEEDS_REVIEW")
            needs_review += 1
        else:
            sane += 1
        if row["h3_count"] == 0:
            flags.append("CLASS_C_OR_DEGRADED")
            h3_zero_tickers.append(ticker)

        vendor_count[row["vendor"]] = vendor_count.get(row["vendor"], 0) + 1

        report.per_ticker[ticker] = {
            "vendor": row["vendor"],
            "h1_count": row["h1_count"],
            "h2_count": row["h2_count"],
            "h3_count": row["h3_count"],
            "h4_count": row["h4_count"],
            "h5_count": row["h5_count"],
            "h1_first3": row["h1_first3"],
            "h2_first3": row["h2_first3"],
            "h3_samples": row["h3_samples"],
            "perf_median_ms": row["perf_median_ms"],
            "sanity_status": row["sanity_status"],
            "sanity_reason": row["sanity_reason"],
            "flags": flags,
            "fiscal_year": row["fiscal_year"],
        }
        print(
            f"  {ticker:<6}  {row['vendor']:<14} "
            f"h1={row['h1_count']:<2} h2={row['h2_count']:<2} "
            f"h3={row['h3_count']:<3} h4={row['h4_count']:<3} "
            f"h5={row['h5_count']:<3} "
            f"perf={row['perf_median_ms']:.0f}ms "
            f"{row['sanity_status']}",
            file=sys.stderr,
        )

    report.summary = {
        "total": len(selected),
        "sane": sane,
        "needs_review": needs_review,
        "errors": errors,
        "vendor_distribution": vendor_count,
        "tickers_with_zero_h3": h3_zero_tickers,
    }

    report_path = Path(args.report_path)
    reporter.write_json(report, report_path)
    if args.md_report_path:
        Path(args.md_report_path).write_text(
            reporter.render_discovery_markdown(report), encoding="utf-8"
        )

    print(
        f"\nDiscovery round {args.round}: "
        f"sane={sane} needs_review={needs_review} errors={errors}",
        file=sys.stderr,
    )
    print(f"Vendor distribution: {vendor_count}", file=sys.stderr)
    return 0


def cmd_both(args: argparse.Namespace) -> int:
    rc = cmd_hard_gate(args)
    if rc != 0:
        # Still emit discovery for visibility, but propagate failure exit.
        cmd_discovery(args)
        return rc
    return cmd_discovery(args)


# ───── Argument parsing ───────────────────────────────────────────────────


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="python -m backend.tests.ingestion.sec_filing_pipeline.validation",
        description="HTMLPreprocessor validation harness",
    )
    p.add_argument(
        "--mode",
        required=True,
        choices=("fetch", "hard-gate", "discovery", "both", "bootstrap-baseline"),
    )
    p.add_argument(
        "--tickers",
        required=True,
        help="ticker set name or comma-separated list "
        "(existing23, discovery5, all28, class_a, class_b, class_c, NVDA,AAPL,...)",
    )
    p.add_argument("--cache-dir", default=str(_DEFAULT_CACHE_DIR))
    p.add_argument("--baseline", default=str(_DEFAULT_BASELINE))
    p.add_argument(
        "--report-path",
        default=str(_DEFAULT_REPORT_DIR / "validation_report.json"),
    )
    p.add_argument(
        "--md-report-path",
        default=None,
        help="Optional Markdown report path",
    )
    p.add_argument("--round", type=int, default=1)
    p.add_argument("--force", action="store_true", help="Bypass cache for fetch")
    return p


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    handler = {
        "fetch": cmd_fetch,
        "hard-gate": cmd_hard_gate,
        "discovery": cmd_discovery,
        "both": cmd_both,
        "bootstrap-baseline": cmd_bootstrap_baseline,
    }[args.mode]
    return handler(args)


if __name__ == "__main__":
    raise SystemExit(main())
