"""Build the frozen tool-error-case dataset and its design/held-out split.

Rows are written here (not hand-edited in the CSV) so every error row's
``expected_failures`` is copied verbatim from the probe output: the exact
message the model saw before the error contract existed. A row is only kept
if every trigger it names actually fired in the probe.

The split is stratified by ``error_class`` with a fixed seed: each class's
six rows are shuffled and the first three go to ``design`` (the only rows
looked at while writing the new messages), the rest to ``heldout``.
Controls are their own tier.
"""

from __future__ import annotations

import argparse
import csv
import json
import random
import sys
from pathlib import Path
from typing import Any

from backend.evals.experiments.harness import SCENARIO_DIR as DIAGNOSTIC_ZH_DIR

SPLIT_SEED = 20261027
DESIGN_PER_CLASS = 3

QUOTE = "finnhub_stock_quote"
FIN = "finnhub_company_basic_financials"
LIST = "sec_filing_list_sections"
GET = "sec_filing_get_section"
NEWS = "tavily_financial_search"

FINNHUB_ANY = "finnhub_*"
SEC_ANY = "sec_filing_*"

BASE_COLUMNS = [
    "id", "question", "company_universe", "category", "expected_answer_type",
    "time_sensitivity", "question_style", "capability_band",
    "expected_baseline_behavior", "primary_failure_mechanism",
    "secondary_failure_mechanism", "expected_best_source", "likely_tuning_lever",
    "why_baseline_might_fail_or_pass", "draft_pass_signals",
]  # fmt: skip
EXTRA_COLUMNS = [
    "error_class", "language", "trigger_tickers", "expected_failures",
    "failing_sources", "acceptable_alternatives", "must_state_gap",
    "source_row_id",
]  # fmt: skip

CLASS_DEFAULTS: dict[str, dict[str, str]] = {
    "a_non_10k_filer": {
        "expected_baseline_behavior": "may_pass_with_tuning",
        "expected_best_source": "mixed",
        "failing_sources": "sec",
        "why": "公司不申報 10-K（20-F / 40-F），SEC 工具必定失敗；Finnhub 與新聞仍可用，"
        "答案應改用可用來源並說明官方 10-K 資料拿不到。",
    },
    "b_non_us_listing": {
        "expected_baseline_behavior": "should_fail_cleanly",
        "expected_best_source": "Tavily",
        "failing_sources": "finnhub|sec",
        "why": "非美國掛牌代號：Finnhub 免費方案回 403，SEC 查無此 ticker；"
        "只剩新聞（或美國 ADR 代號）可用，答案應說明行情/財務數據缺口。",
    },
    "c_missing_section_or_year": {
        "expected_baseline_behavior": "may_pass_with_tuning",
        "expected_best_source": "SEC",
        "failing_sources": "sec_section_or_year",
        "why": "公司有 10-K，但指定的章節或年度不存在；應改讀其他章節/年度或新聞，"
        "並說明原本要求的那份資料不存在。",
    },
    "d_invalid_or_delisted": {
        "expected_baseline_behavior": "should_fail_cleanly",
        "expected_best_source": "Tavily",
        "failing_sources": "finnhub|sec",
        "why": "代號無效或已下市：SEC 查無 ticker、Finnhub 報價為空（基本面可能回傳過時資料）；"
        "應改用新聞並說明即時資料不存在。",
    },
}

PASS_SIGNALS_ERROR = [
    "明確說出哪個資料來源拿不到資料、原因是什麼",
    "改用仍可用的來源回答能回答的部分",
    "不重複呼叫已確定對該 ticker 永久失敗的來源",
]


def _row(
    rid: int,
    cls: str,
    question: str,
    company: str,
    tickers: list[str],
    triggers: list[tuple[str, dict[str, Any]]],
    alternatives: list[str],
    *,
    language: str = "zh-TW",
    best_source: str | None = None,
    note: str = "",
) -> dict[str, Any]:
    return {
        "id": rid,
        "cls": cls,
        "question": question,
        "company": company,
        "tickers": tickers,
        "triggers": triggers,
        "alternatives": alternatives,
        "language": language,
        "best_source": best_source,
        "note": note,
    }


ERROR_ROWS = [
    # (a) non-10-K filers
    _row(1, "a_non_10k_filer",
         "台積電（TSM）最新一份年報裡，管理層怎麼描述地緣政治與客戶集中的風險？",
         "TSMC", ["TSM"], [(LIST, {"ticker": "TSM"})], [FINNHUB_ANY, NEWS]),
    _row(2, "a_non_10k_filer",
         "艾司摩爾（ASML）在官方年報的風險因子裡，怎麼評估對中國出口管制的影響？",
         "ASML Holding", ["ASML"], [(LIST, {"ticker": "ASML"})], [FINNHUB_ANY, NEWS]),
    _row(3, "a_non_10k_filer",
         "What does SAP's latest annual report say about the risks of its cloud "
         "transition, and how is the stock valued right now?",
         "SAP", ["SAP"], [(LIST, {"ticker": "SAP"})], [FINNHUB_ANY, NEWS],
         language="en"),
    _row(4, "a_non_10k_filer",
         "諾和諾德（NVO）年報怎麼談 GLP-1 減重藥的競爭壓力？現在的估值反映了多少？",
         "Novo Nordisk", ["NVO"], [(LIST, {"ticker": "NVO"})], [FINNHUB_ANY, NEWS]),
    _row(5, "a_non_10k_filer",
         "豐田汽車（TM）的官方年報對電動車轉型的投資計畫怎麼說？",
         "Toyota", ["TM"], [(LIST, {"ticker": "TM"})], [FINNHUB_ANY, NEWS]),
    _row(6, "a_non_10k_filer",
         "How does Royal Bank of Canada (RY) describe its credit loss provisioning "
         "in its latest annual filing?",
         "Royal Bank of Canada", ["RY"], [(LIST, {"ticker": "RY"})],
         [FINNHUB_ANY, NEWS], language="en",
         note="RY 申報 40-F；現行訊息是 'has no 10-K filings'，不會提到 40-F。"),
    # (b) non-US listings
    _row(7, "b_non_us_listing",
         "空中巴士在巴黎上市的股票（AIR.PA）現在的估值和獲利能力，跟航太同業比起來算高還是低？",
         "Airbus", ["AIR.PA"],
         [(QUOTE, {"ticker": "AIR.PA"}), (FIN, {"ticker": "AIR.PA"}),
          (LIST, {"ticker": "AIR.PA"})],
         [NEWS, FINNHUB_ANY]),
    _row(8, "b_non_us_listing",
         "雀巢（瑞士上市，NESN.SW）最近的股價表現和本益比如何？配息還穩嗎？",
         "Nestle", ["NESN.SW"],
         [(QUOTE, {"ticker": "NESN.SW"}), (FIN, {"ticker": "NESN.SW"}),
          (LIST, {"ticker": "NESN.SW"})],
         [NEWS, FINNHUB_ANY]),
    _row(9, "b_non_us_listing",
         "騰訊（0700.HK）現在的估值貴不貴？最近的財務指標有沒有轉弱？",
         "Tencent", ["0700.HK"],
         [(QUOTE, {"ticker": "0700.HK"}), (FIN, {"ticker": "0700.HK"}),
          (LIST, {"ticker": "0700.HK"})],
         [NEWS, FINNHUB_ANY]),
    _row(10, "b_non_us_listing",
         "What's Toyota's current share price on the Tokyo exchange (7203.T), and "
         "how does its P/E look?",
         "Toyota", ["7203.T"],
         [(QUOTE, {"ticker": "7203.T"}), (FIN, {"ticker": "7203.T"}),
          (LIST, {"ticker": "7203.T"})],
         [NEWS, FINNHUB_ANY], language="en"),
    _row(11, "b_non_us_listing",
         "台積電台股（2330.TW）現在的本益比跟毛利率是多少？",
         "TSMC", ["2330.TW"],
         [(QUOTE, {"ticker": "2330.TW"}), (FIN, {"ticker": "2330.TW"}),
          (LIST, {"ticker": "2330.TW"})],
         [NEWS, FINNHUB_ANY]),
    _row(12, "b_non_us_listing",
         "LVMH（MC.PA）最近股價跌了不少，從財務指標看算便宜了嗎？",
         "LVMH", ["MC.PA"],
         [(QUOTE, {"ticker": "MC.PA"}), (FIN, {"ticker": "MC.PA"}),
          (LIST, {"ticker": "MC.PA"})],
         [NEWS, FINNHUB_ANY]),
    # (c) missing section / filing year
    _row(13, "c_missing_section_or_year",
         "英特爾最新 10-K 的管理層討論與分析（Item 7）怎麼解釋營收和毛利的變化？",
         "Intel", ["INTC"], [(GET, {"ticker": "INTC", "section_key": "7"})],
         [SEC_ANY, NEWS]),
    _row(14, "c_missing_section_or_year",
         "蘋果 2022 財年 10-K 裡的 Item 1C 資安風險管理揭露寫了什麼？",
         "Apple", ["AAPL"],
         [(GET, {"ticker": "AAPL", "section_key": "1c", "fiscal_year": 2022})],
         [SEC_ANY, NEWS]),
    _row(15, "c_missing_section_or_year",
         "What did Nvidia disclose under Item 1C (Cybersecurity) in its fiscal "
         "2022 10-K?",
         "Nvidia", ["NVDA"],
         [(GET, {"ticker": "NVDA", "section_key": "1c", "fiscal_year": 2022})],
         [SEC_ANY, NEWS], language="en"),
    _row(16, "c_missing_section_or_year",
         "特斯拉 2008 年的 10-K 年報裡，怎麼描述它的商業模式和主要風險？",
         "Tesla", ["TSLA"], [(LIST, {"ticker": "TSLA", "fiscal_year": 2008})],
         [SEC_ANY, NEWS]),
    _row(17, "c_missing_section_or_year",
         "臉書（META）2010 財年的 10-K 裡揭露的營收和主要風險是什麼？",
         "Meta", ["META"], [(LIST, {"ticker": "META", "fiscal_year": 2010})],
         [SEC_ANY, NEWS]),
    _row(18, "c_missing_section_or_year",
         "蘋果 2027 財年的 10-K 對 AI 相關投資怎麼說？",
         "Apple", ["AAPL"], [(LIST, {"ticker": "AAPL", "fiscal_year": 2027})],
         [SEC_ANY, NEWS]),
    # (d) invalid / delisted tickers
    _row(19, "d_invalid_or_delisted",
         "Twitter（TWTR）被馬斯克收購之前，最後的財務體質跟估值大概是什麼樣子？",
         "Twitter", ["TWTR"],
         [(QUOTE, {"ticker": "TWTR"}), (LIST, {"ticker": "TWTR"})], [NEWS],
         note="Finnhub basic financials 對 TWTR 仍回傳過時數據（不報錯）。"),
    _row(20, "d_invalid_or_delisted",
         "矽谷銀行（SIVB）倒閉前，資產負債表上的利率風險有多嚴重？",
         "SVB Financial", ["SIVB"],
         [(QUOTE, {"ticker": "SIVB"}), (FIN, {"ticker": "SIVB"}),
          (LIST, {"ticker": "SIVB"})],
         [NEWS]),
    _row(21, "d_invalid_or_delisted",
         "How exposed was First Republic Bank (FRC) to uninsured deposits before "
         "it failed?",
         "First Republic Bank", ["FRC"],
         [(QUOTE, {"ticker": "FRC"}), (LIST, {"ticker": "FRC"})], [NEWS],
         language="en",
         note="Finnhub basic financials 對 FRC 仍回傳過時數據（不報錯）。"),
    _row(22, "d_invalid_or_delisted",
         "動視暴雪（ATVI）現在的股價和本益比是多少？",
         "Activision Blizzard", ["ATVI"],
         [(QUOTE, {"ticker": "ATVI"}), (LIST, {"ticker": "ATVI"})], [NEWS],
         note="已被微軟收購下市；Finnhub basic financials 仍回傳過時數據。"),
    _row(23, "d_invalid_or_delisted",
         "Block（代號 SQ）最近的本益比跟營收成長怎麼樣？",
         "Block", ["SQ"],
         [(QUOTE, {"ticker": "SQ"}), (LIST, {"ticker": "SQ"})],
         [NEWS, f"{FINNHUB_ANY}:XYZ", f"{SEC_ANY}:XYZ"],
         note="Block 2025 年改代號為 XYZ；用 XYZ 查到資料算可接受的替代來源。"),
    _row(24, "d_invalid_or_delisted",
         "朋友推薦一檔代號 XYZQ 的股票，幫我看一下它的基本面跟最近股價。",
         "unknown", ["XYZQ"],
         [(QUOTE, {"ticker": "XYZQ"}), (FIN, {"ticker": "XYZQ"}),
          (LIST, {"ticker": "XYZQ"})],
         [NEWS]),
]  # fmt: skip

# Original diagnostic rows that hit zero tool errors in all 3 luna_medium
# reps of the 2026-10-22 benchmark, picked to span every source.
CONTROL_SOURCE_ROWS = {25: "3", 26: "11", 27: "16", 28: "20", 29: "25", 30: "28"}


def _probe_key(tool: str, args: dict[str, Any]) -> str:
    return json.dumps([tool, args], sort_keys=True)


def _error_csv_row(
    spec: dict[str, Any], probes: dict[str, dict[str, Any]]
) -> dict[str, Any]:
    failures = []
    for tool, args in spec["triggers"]:
        probe = probes.get(_probe_key(tool, args))
        if probe is None or not probe["fired"]:
            raise SystemExit(f"Row {spec['id']}: trigger {tool} {args} did not fire")
        failures.append(
            {
                "tool": tool,
                "args": args,
                "exc_type": probe["exc_type"].rsplit(".", 1)[-1],
                "message": probe["model_saw"],
            }
        )
    defaults = CLASS_DEFAULTS[spec["cls"]]
    why = defaults["why"] + (f" {spec['note']}" if spec["note"] else "")
    return {
        "id": spec["id"],
        "question": spec["question"],
        "company_universe": spec["company"],
        "category": "tool_error_recovery",
        "expected_answer_type": "可用來源回答+資料缺口揭露",
        "time_sensitivity": "recent",
        "question_style": "natural",
        "capability_band": "boundary",
        "expected_baseline_behavior": defaults["expected_baseline_behavior"],
        "primary_failure_mechanism": "source_coverage_gap",
        "secondary_failure_mechanism": "tool_routing_error",
        "expected_best_source": spec["best_source"] or defaults["expected_best_source"],
        "likely_tuning_lever": "tool_error_message",
        "why_baseline_might_fail_or_pass": why,
        "draft_pass_signals": json.dumps(PASS_SIGNALS_ERROR, ensure_ascii=False),
        "error_class": spec["cls"],
        "language": spec["language"],
        "trigger_tickers": "|".join(spec["tickers"]),
        "expected_failures": json.dumps(failures, ensure_ascii=False),
        "failing_sources": defaults["failing_sources"],
        "acceptable_alternatives": "|".join(spec["alternatives"]),
        "must_state_gap": "true",
        "source_row_id": "",
    }


def _control_csv_rows() -> list[dict[str, Any]]:
    with (DIAGNOSTIC_ZH_DIR / "dataset.csv").open(encoding="utf-8") as fh:
        source = {row["id"]: row for row in csv.DictReader(fh)}
    rows = []
    for new_id, source_id in CONTROL_SOURCE_ROWS.items():
        row: dict[str, Any] = dict(source[source_id])
        row.update(
            {
                "id": new_id,
                "error_class": "control",
                "language": "zh-TW",
                "trigger_tickers": "",
                "expected_failures": "[]",
                "failing_sources": "",
                "acceptable_alternatives": "",
                "must_state_gap": "false",
                "source_row_id": source_id,
            }
        )
        rows.append(row)
    return rows


def build_split(rows: list[dict[str, Any]]) -> dict[str, Any]:
    rng = random.Random(SPLIT_SEED)
    design: list[str] = []
    heldout: list[str] = []
    for cls in CLASS_DEFAULTS:
        ids = sorted((str(r["id"]) for r in rows if r["error_class"] == cls), key=int)
        rng.shuffle(ids)
        design += sorted(ids[:DESIGN_PER_CLASS], key=int)
        heldout += sorted(ids[DESIGN_PER_CLASS:], key=int)
    control = [str(r["id"]) for r in rows if r["error_class"] == "control"]
    return {
        "status": "frozen",
        "seed": SPLIT_SEED,
        "stratified_by": "error_class",
        "design": sorted(design, key=int),
        "heldout": sorted(heldout, key=int),
        "control": control,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--probe", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args(argv)

    probes = {
        _probe_key(p["tool"], p["args"]): p for p in json.loads(args.probe.read_text())
    }
    rows = [_error_csv_row(spec, probes) for spec in ERROR_ROWS]
    rows += _control_csv_rows()

    args.out_dir.mkdir(parents=True, exist_ok=True)
    with (args.out_dir / "dataset.csv").open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=BASE_COLUMNS + EXTRA_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
    (args.out_dir / "split.json").write_text(
        json.dumps(build_split(rows), indent=2) + "\n"
    )
    print(f"wrote {len(rows)} rows to {args.out_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
