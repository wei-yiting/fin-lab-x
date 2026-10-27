"""Tool-selection metrics over recorded agent runs, scored against hand labels.

Every diagnostic row is hand-labelled per data source (必要 / 擇一必要 /
可接受 / 不必要, rules R1–R4 of the annotation pass). Each recorded run's
tool calls are mapped to sources and compared with its row's labels — no
agent is re-run and no LLM judge is used.

Aggregation follows the benchmark analyses: per-row means over repetitions
first, then a row-level (cluster) bootstrap 95% CI across rows.

Per-run definitions:

- *source used*: called at least once, errored calls included. The
  ``recall_success_only`` variant counts a source only if at least one call
  to it returned without error; ``errored_only_sources`` lists sources that
  were called but never succeeded.
- *routing recall*: every 必要 source used and, when the row has 擇一必要
  sources, at least one of them used.
- *unnecessary*: at least one 不必要 source used; ``unnecessary_calls`` counts
  the calls to 不必要 sources.
- *ticker accuracy*: among calls that pass a ``ticker`` arg, the share whose
  ticker is in the row's expected tickers. Case and separators are
  normalised and share classes of one issuer are the same ticker
  (``TICKER_ALIASES``); a different listing of the same issuer (an ADR, a
  foreign exchange code) is not — fix the row's expected tickers instead.

Coverage-gap rows (the data the question needs is out of reach of every
tool) are excluded from recall and unnecessary-call rate and reported apart:

- *insufficient evidence stated*: the answer matches
  ``INSUFFICIENT_EVIDENCE_RE``, a keyword heuristic for zh-TW answers that
  counts both "evidence is insufficient" claims and data-limitation
  disclosures ("資料限制說明"), but not topical uses such as 出口限制. The
  phrases were drawn from the row-4 answers, so the matched phrase of every
  coverage-gap run is listed in tables.md (and every run in metrics.csv)
  for a hand audit.
- *repeated failed calls*: calls whose tool and args equal an earlier call
  in the same run that errored. ``retries_after_source_failure`` is looser:
  calls to a source with a ticker after an earlier call to that source with
  that ticker errored.

Usage::

    python -m backend.evals.experiments.tool_selection.analyze \\
        --labels tool_routing_annotation.xlsx \\
        --archives data/experiment-archives/2026-10-22-model-reasoning-benchmark \\
                   data/experiment-archives/2026-10-22-rag-bundle-ablation \\
        --out-dir <scratch dir>
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import statistics
import tarfile
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import openpyxl

from backend.evals.experiments.model_reasoning_benchmark.analyze import (
    _bootstrap,
    _num,
    per_row_means,
)

SHEET = "標註"
SOURCE_COLUMNS = {
    "Finnhub 報價": "quote",
    "Finnhub 財務指標": "financials",
    "Tavily 新聞": "news",
    "SEC 10-K": "sec10k",
}
SOURCES = list(SOURCE_COLUMNS.values())
SOURCE_CODES = {"quote": "Q", "financials": "F", "news": "N", "sec10k": "S"}
TOOL_SOURCE = {
    "finnhub_stock_quote": "quote",
    "finnhub_company_basic_financials": "financials",
    "tavily_financial_search": "news",
    "sec_filing_list_sections": "sec10k",
    "sec_filing_get_section": "sec10k",
    "sec_filing_search": "sec10k",
}

REQUIRED = "必要"
EITHER = "擇一必要"
ACCEPTABLE = "可接受"
UNNECESSARY = "不必要"
LABEL_CODES = {REQUIRED: "R", EITHER: "E", ACCEPTABLE: "A", UNNECESSARY: "U"}
GAP_TRUE = {"是", "y", "yes", "true", "1"}

PER_ROW_KEYS = (
    "recall",
    "unnecessary",
    "tool_calls_total",
    "ticker_accuracy",
    "insufficient_evidence_stated",
    "repeated_failed_calls",
)

TICKER_ALIASES = {"GOOG": "GOOGL", "BRK.A": "BRK.B"}

INSUFFICIENT_EVIDENCE_RE = re.compile(
    r"(證據|資料|數據|資訊)[^。\n]{0,4}(不足|有限|不夠)"
    r"|無法(取得|確認|驗證|查證|擷取|量化)"
    r"|未能(取得|確認|找到|查到)"
    r"|沒有(取得|找到|查到|拿到)"
    r"|(查|找)不到"
    r"|工具[^。\n]{0,6}(不支援|只支援|無法)"
    r"|(資料|數據|資訊)[^。\n]{0,6}限制"
)


class LabelError(ValueError):
    pass


@dataclass
class RowLabel:
    row_id: str
    tickers: frozenset[str]
    labels: dict[str, str]
    coverage_gap: bool


@dataclass
class LabelSheet:
    rows: dict[str, RowLabel]
    total_rows: int
    incomplete: list[str]
    gap_column_found: bool


def normalize_ticker(ticker: str) -> str:
    t = re.sub(r"[-/ ]", ".", ticker.strip().upper())
    return TICKER_ALIASES.get(t, t)


def parse_tickers(raw: str) -> frozenset[str]:
    without_notes = re.sub(r"\(.*?\)|（.*?）", "", raw)
    return frozenset(
        normalize_ticker(t) for t in re.split(r"[,，、;；\s]+", without_notes) if t
    )


def _text(value: Any) -> str:
    return "" if value is None else str(value).strip()


def load_labels(path: Path) -> LabelSheet:
    ws = openpyxl.load_workbook(path, read_only=True, data_only=True)[SHEET]
    lines = list(ws.iter_rows(values_only=True))
    header = [_text(h) for h in lines[0]]
    col = {name: i for i, name in enumerate(header)}
    tickers_col = next(i for i, h in enumerate(header) if h.startswith("預期 tickers"))
    gap_col = next(
        (i for i, h in enumerate(header) if "coverage gap" in h.lower()), None
    )

    rows: dict[str, RowLabel] = {}
    incomplete: list[str] = []
    total = 0
    for line in lines[1:]:
        row_id = _text(line[col["id"]])
        if not row_id:
            continue
        total += 1
        labels = {src: _text(line[col[name]]) for name, src in SOURCE_COLUMNS.items()}
        filled = [v for v in labels.values() if v]
        if not filled:
            continue
        if len(filled) < len(labels):
            incomplete.append(row_id)
            continue
        unknown = [v for v in filled if v not in LABEL_CODES]
        if unknown:
            raise LabelError(f"row {row_id}: unknown label(s) {unknown}")
        if sum(v == EITHER for v in filled) == 1:
            raise LabelError(
                f"row {row_id}: a single {EITHER} source has no alternative"
            )
        gap = gap_col is not None and _text(line[gap_col]).lower() in GAP_TRUE
        rows[row_id] = RowLabel(
            row_id=row_id,
            tickers=parse_tickers(_text(line[tickers_col])),
            labels=labels,
            coverage_gap=gap,
        )
    return LabelSheet(rows, total, incomplete, gap_col is not None)


def _experiment(archive_dir: Path) -> str:
    return re.sub(r"^\d{4}-\d{2}-\d{2}-", "", archive_dir.name)


def load_records(archive_dirs: list[Path]) -> list[dict[str, Any]]:
    """Reads run JSONs straight from each archive's raw.tar.gz.

    An arm name recorded in more than one archive is a separate run of the
    same config, so it is qualified with its experiment rather than pooled.
    """
    loaded: list[tuple[int, str, dict[str, Any]]] = []
    for index, archive_dir in enumerate(archive_dirs):
        with tarfile.open(archive_dir / "raw.tar.gz", "r:gz") as tar:
            for member in tar.getmembers():
                name = Path(member.name).name
                # macOS tar adds an AppleDouble "._<name>" xattr member per file.
                if (
                    not member.isfile()
                    or not name.endswith(".json")
                    or name.startswith("._")
                ):
                    continue
                data = tar.extractfile(member)
                assert data is not None
                loaded.append((index, _experiment(archive_dir), json.load(data)))
    loaded.sort(
        key=lambda x: (x[0], x[2]["arm"], int(x[2]["row_id"]), x[2]["repetition"])
    )
    experiments_per_arm: dict[str, set[str]] = defaultdict(set)
    for _, experiment, rec in loaded:
        experiments_per_arm[rec["arm"]].add(experiment)
    records = []
    for _, experiment, rec in loaded:
        arm = rec["arm"]
        config = arm if len(experiments_per_arm[arm]) == 1 else f"{arm} @ {experiment}"
        records.append({**rec, "config": config})
    return records


def _canonical(args: dict[str, Any]) -> str:
    return json.dumps(args, sort_keys=True, ensure_ascii=False)


def score_run(record: dict[str, Any], label: RowLabel | None) -> dict[str, Any]:
    output = record.get("output") or {}
    calls = output.get("tool_outputs") or []
    response = output.get("response") or ""

    called: Counter[str] = Counter()
    succeeded: set[str] = set()
    failed_calls: set[tuple[str, str]] = set()
    failed_source_tickers: set[tuple[str, str]] = set()
    repeated_failed = 0
    retries_after_failure = 0
    tickers: list[str] = []
    for c in calls:
        source = TOOL_SOURCE.get(c["tool"], c["tool"])
        args = c.get("args") or {}
        ticker = normalize_ticker(args["ticker"]) if args.get("ticker") else None
        key = (c["tool"], _canonical(args))
        if key in failed_calls:
            repeated_failed += 1
        if ticker and (source, ticker) in failed_source_tickers:
            retries_after_failure += 1

        called[source] += 1
        if ticker:
            tickers.append(ticker)
        if c.get("error"):
            failed_calls.add(key)
            if ticker:
                failed_source_tickers.add((source, ticker))
        else:
            succeeded.add(source)

    match = INSUFFICIENT_EVIDENCE_RE.search(response)
    run: dict[str, Any] = {
        "row_id": record["row_id"],
        "config": record.get("config", record["arm"]),
        "arm": record["arm"],
        "rep": record["repetition"],
        "labelled": label is not None,
        "coverage_gap": label.coverage_gap if label else "",
        "tool_calls_total": len(calls),
        **{f"used_{src}": called[src] > 0 for src in SOURCES},
        "errored_only_sources": " ".join(
            src for src in SOURCES if called[src] and src not in succeeded
        ),
        "recall": "",
        "recall_success_only": "",
        "unnecessary": "",
        "unnecessary_calls": "",
        "ticker_calls": len(tickers),
        "ticker_correct": "",
        "ticker_accuracy": "",
        "off_list_tickers": "",
        "insufficient_evidence_stated": match is not None,
        "insufficient_evidence_match": match.group(0) if match else "",
        "repeated_failed_calls": repeated_failed,
        "retries_after_source_failure": retries_after_failure,
    }
    if label is None:
        return run

    def recall(used: set[str]) -> bool:
        required = {s for s, v in label.labels.items() if v == REQUIRED}
        either = {s for s, v in label.labels.items() if v == EITHER}
        return required <= used and (not either or bool(either & used))

    unnecessary = [s for s, v in label.labels.items() if v == UNNECESSARY]
    correct = [t for t in tickers if t in label.tickers]
    run.update(
        recall=recall(set(called)),
        recall_success_only=recall(succeeded),
        unnecessary=any(called[s] for s in unnecessary),
        unnecessary_calls=sum(called[s] for s in unnecessary),
        ticker_correct=len(correct),
        ticker_accuracy=len(correct) / len(tickers) if tickers else "",
        off_list_tickers=" ".join(
            sorted({t for t in tickers if t not in label.tickers})
        ),
    )
    return run


def _mean(runs: list[dict[str, Any]], key: str) -> float | None:
    vals = [v for r in runs if (v := _num(r[key])) is not None]
    return statistics.mean(vals) if vals else None


def _ci(runs: list[dict[str, Any]], key: str) -> tuple[float, float, float] | None:
    means = per_row_means(runs, key)
    if not means:
        return None
    return _bootstrap({rid: v for (rid, _), v in means.items()}, statistics.mean)


def summarize(runs: list[dict[str, Any]], sheet: LabelSheet) -> dict[str, Any]:
    configs: dict[str, Any] = {}
    for config in dict.fromkeys(r["config"] for r in runs):
        cfg_runs = [r for r in runs if r["config"] == config]
        routing = [r for r in cfg_runs if r["labelled"] and not r["coverage_gap"]]
        gap = [r for r in cfg_runs if r["labelled"] and r["coverage_gap"]]
        labelled = routing + gap
        configs[config] = {
            "runs": len(cfg_runs),
            "median_tool_calls": statistics.median(
                r["tool_calls_total"] for r in cfg_runs
            ),
            "routing_rows": len({r["row_id"] for r in routing}),
            "routing_runs": len(routing),
            "recall": _ci(routing, "recall"),
            "recall_success_only": _ci(routing, "recall_success_only"),
            "unnecessary_rate": _ci(routing, "unnecessary"),
            "unnecessary_calls_per_run": _ci(routing, "unnecessary_calls"),
            "errored_only_source_uses": sum(
                len(r["errored_only_sources"].split()) for r in routing
            ),
            "ticker_rows": len({r["row_id"] for r in labelled if r["ticker_calls"]}),
            "ticker_accuracy": _ci(labelled, "ticker_accuracy"),
            "gap_rows": len({r["row_id"] for r in gap}),
            "gap_runs": len(gap),
            "insufficient_evidence_stated": _ci(gap, "insufficient_evidence_stated"),
            "repeated_failed_calls_per_run": _ci(gap, "repeated_failed_calls"),
            "runs_with_repeated_failed_call": sum(
                1 for r in gap if r["repeated_failed_calls"]
            ),
            "retries_after_source_failure_per_run": _ci(
                gap, "retries_after_source_failure"
            ),
        }

    cells: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for r in runs:
        if r["labelled"]:
            cells[(r["row_id"], r["config"])].append(r)
    per_row: dict[str, dict[str, dict[str, float | None]]] = defaultdict(dict)
    for (rid, config), cell in cells.items():
        per_row[rid][config] = {key: _mean(cell, key) for key in PER_ROW_KEYS}

    off_list: dict[str, Counter[str]] = defaultdict(Counter)
    for r in runs:
        for t in str(r["off_list_tickers"]).split():
            off_list[r["row_id"]][t] += 1

    return {
        "labelled_rows": len(sheet.rows),
        "total_rows": sheet.total_rows,
        "routing_rows": sum(not r.coverage_gap for r in sheet.rows.values()),
        "gap_rows": sum(r.coverage_gap for r in sheet.rows.values()),
        "incomplete_rows": sheet.incomplete,
        "gap_column_found": sheet.gap_column_found,
        "configs": configs,
        "per_row": per_row,
        "off_list_tickers": {rid: dict(c) for rid, c in off_list.items()},
        "gap_runs": [
            {
                k: r[k]
                for k in ("row_id", "config", "rep", "insufficient_evidence_match")
            }
            for r in runs
            if r["labelled"] and r["coverage_gap"]
        ],
    }


def _fmt_ci(value: tuple[float, float, float] | None, digits: int = 2) -> str:
    if value is None:
        return "–"
    point, lo, hi = value
    return f"{point:.{digits}f} [{lo:.{digits}f}, {hi:.{digits}f}]"


def _fmt(value: float | None, digits: int = 2) -> str:
    return "–" if value is None else f"{value:.{digits}f}"


def _label_codes(label: RowLabel) -> str:
    return " ".join(
        f"{SOURCE_CODES[s]}:{LABEL_CODES[label.labels[s]]}" for s in SOURCES
    )


def render_tables(summary: dict[str, Any], sheet: LabelSheet) -> str:
    configs = summary["configs"]
    lines: list[str] = []
    if summary["labelled_rows"] < summary["total_rows"]:
        lines += [
            f"> **PRELIMINARY — {summary['labelled_rows']} of "
            f"{summary['total_rows']} rows labelled. Smoke check only; do not "
            "interpret.**",
            "",
        ]
    if not summary["gap_column_found"]:
        lines += [
            "> No `Coverage gap` column in the label sheet: every labelled row is "
            "scored for routing.",
            "",
        ]
    lines += [
        f"Rows: {summary['routing_rows']} scored for routing, "
        f"{summary['gap_rows']} coverage-gap, "
        f"{len(summary['incomplete_rows'])} partially labelled (skipped).",
        "",
        "Cells are means over rows of per-row means over repetitions; "
        "[95% CI] = row-level bootstrap.",
        "",
        "## Routing (coverage-gap rows excluded)",
        "",
        "| Config | Rows | Runs | Recall | Recall (successful calls only) "
        "| Unnecessary-call rate | Unnecessary calls/run | Errored-only source uses "
        "| Median tool calls (all runs) |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for name, c in configs.items():
        lines.append(
            f"| {name} | {c['routing_rows']} | {c['routing_runs']} "
            f"| {_fmt_ci(c['recall'])} | {_fmt_ci(c['recall_success_only'])} "
            f"| {_fmt_ci(c['unnecessary_rate'])} "
            f"| {_fmt_ci(c['unnecessary_calls_per_run'])} "
            f"| {c['errored_only_source_uses']} | {c['median_tool_calls']:g} |"
        )
    lines += [
        "",
        "## Ticker-argument accuracy (all labelled rows)",
        "",
        "| Config | Rows | Accuracy |",
        "|---|---|---|",
    ]
    for name, c in configs.items():
        lines.append(
            f"| {name} | {c['ticker_rows']} | {_fmt_ci(c['ticker_accuracy'])} |"
        )
    lines += [
        "",
        "## Coverage-gap rows",
        "",
        "| Config | Rows | Runs | Insufficient evidence stated "
        "| Repeated failed calls/run | Runs with a repeated failed call "
        "| Retries after source failure/run |",
        "|---|---|---|---|---|---|---|",
    ]
    for name, c in configs.items():
        lines.append(
            f"| {name} | {c['gap_rows']} | {c['gap_runs']} "
            f"| {_fmt_ci(c['insufficient_evidence_stated'])} "
            f"| {_fmt_ci(c['repeated_failed_calls_per_run'])} "
            f"| {c['runs_with_repeated_failed_call']} "
            f"| {_fmt_ci(c['retries_after_source_failure_per_run'])} |"
        )

    names = list(configs)
    lines += [
        "",
        "## Per row × config",
        "",
        "Labels: Q = Finnhub quote, F = Finnhub financials, N = Tavily news, "
        "S = SEC 10-K; R = 必要, E = 擇一必要, A = 可接受, U = 不必要.",
        "Routing cells: recall / unnecessary-call rate / mean tool calls. "
        "Gap cells: insufficient evidence stated / repeated failed calls / "
        "mean tool calls.",
        "",
        "| Row | Labels | Gap | " + " | ".join(names) + " |",
        "|---|---|---|" + "---|" * len(names),
    ]
    for rid in sorted(summary["per_row"], key=int):
        label = sheet.rows[rid]
        cells = []
        for name in names:
            m = summary["per_row"][rid].get(name)
            if m is None:
                cells.append("–")
            elif label.coverage_gap:
                cells.append(
                    f"{_fmt(m['insufficient_evidence_stated'])} / "
                    f"{_fmt(m['repeated_failed_calls'], 1)} / "
                    f"{_fmt(m['tool_calls_total'], 1)}"
                )
            else:
                cells.append(
                    f"{_fmt(m['recall'])} / {_fmt(m['unnecessary'])} / "
                    f"{_fmt(m['tool_calls_total'], 1)}"
                )
        gap = "yes" if label.coverage_gap else ""
        lines.append(
            f"| {rid} | {_label_codes(label)} | {gap} | " + " | ".join(cells) + " |"
        )

    lines += [
        "",
        "## Ticker args outside the expected list (calls, all configs)",
        "",
        "| Row | Expected | Off-list (calls) |",
        "|---|---|---|",
    ]
    for rid in sorted(summary["off_list_tickers"], key=int):
        expected = ", ".join(sorted(sheet.rows[rid].tickers))
        found = ", ".join(
            f"{t} ×{n}" for t, n in sorted(summary["off_list_tickers"][rid].items())
        )
        lines.append(f"| {rid} | {expected} | {found} |")
    if not summary["off_list_tickers"]:
        lines.append("| – | – | none |")

    lines += [
        "",
        "## Coverage-gap audit: matched insufficiency phrase per run",
        "",
        "| Row | Config | Rep | Matched phrase |",
        "|---|---|---|---|",
    ]
    for r in summary["gap_runs"]:
        phrase = r["insufficient_evidence_match"] or "(none)"
        lines.append(f"| {r['row_id']} | {r['config']} | {r['rep']} | {phrase} |")
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--labels", type=Path, required=True)
    parser.add_argument("--archives", type=Path, nargs="+", required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args(argv)

    sheet = load_labels(args.labels)
    records = load_records(args.archives)
    runs = [score_run(r, sheet.rows.get(r["row_id"])) for r in records]
    order = {name: i for i, name in enumerate(dict.fromkeys(r["config"] for r in runs))}
    runs.sort(key=lambda r: (int(r["row_id"]), order[r["config"]], r["rep"]))

    args.out_dir.mkdir(parents=True, exist_ok=True)
    with open(args.out_dir / "metrics.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(runs[0].keys()))
        writer.writeheader()
        writer.writerows(runs)
    summary = summarize(runs, sheet)
    (args.out_dir / "tables.md").write_text(render_tables(summary, sheet))

    print(
        f"{summary['labelled_rows']} of {summary['total_rows']} rows labelled: "
        f"{summary['routing_rows']} scored for routing, "
        f"{summary['gap_rows']} coverage-gap, "
        f"{len(summary['incomplete_rows'])} partially labelled (skipped "
        f"{', '.join(summary['incomplete_rows']) or '–'})"
    )
    if not sheet.gap_column_found:
        print("warning: no 'Coverage gap' column; no row is treated as a coverage gap")
    print(f"{len(runs)} runs -> {args.out_dir / 'metrics.csv'}, tables.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
