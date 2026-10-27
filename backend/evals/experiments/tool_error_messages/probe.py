"""Probe candidate error triggers directly against the tools (no model calls).

Each probe invokes one tool once with the arguments a research question is
expected to elicit, and records whether it raised, the exception class, and
the exact message the model would see (``sanitize_tool_error(str(exc))``,
which is what ``_HandleToolErrors`` returned before the error contract).
Triggers that do not fire are dropped from the dataset.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

from backend.agent_engine.streaming.tool_error_sanitizer import sanitize_tool_error
from backend.agent_engine.tools import setup_tools
from backend.agent_engine.tools.registry import get_tool

load_dotenv(Path(__file__).resolve().parents[3] / ".env")

QUOTE = "finnhub_stock_quote"
FIN = "finnhub_company_basic_financials"
LIST = "sec_filing_list_sections"
GET = "sec_filing_get_section"

# (probe_id, tool, args). Ticker probes hit all three ticker-level tools.
TICKERS = [
    # (a) non-10-K filers (20-F / 40-F)
    "TSM", "ASML", "SAP", "NVO", "TM", "SHOP", "SONY", "BABA", "RY", "TD", "CNQ",
    # (b) non-US listings
    "AIR.PA", "NESN.SW", "0700.HK", "7203.T", "2330.TW", "MC.PA", "SAP.DE",
    # (d) invalid / delisted
    "TWTR", "FRC", "SIVB", "BBBY", "ATVI", "APPL", "GOOGLE", "FB", "SQ", "XYZQ",
    "PARA", "ANTM",
]  # fmt: skip

SECTION_PROBES: list[tuple[str, dict[str, Any]]] = [
    (GET, {"ticker": "INTC", "section_key": "7"}),
    (GET, {"ticker": "JPM", "section_key": "7"}),
    (GET, {"ticker": "BAC", "section_key": "7"}),
    (GET, {"ticker": "C", "section_key": "7"}),
    (GET, {"ticker": "GE", "section_key": "7"}),
    (GET, {"ticker": "WFC", "section_key": "7"}),
    (GET, {"ticker": "AAPL", "section_key": "1c", "fiscal_year": 2022}),
    (GET, {"ticker": "MSFT", "section_key": "1c", "fiscal_year": 2021}),
    (GET, {"ticker": "NVDA", "section_key": "1c", "fiscal_year": 2022}),
    (LIST, {"ticker": "TSLA", "fiscal_year": 2008}),
    (LIST, {"ticker": "META", "fiscal_year": 2010}),
    (LIST, {"ticker": "AAPL", "fiscal_year": 2027}),
    (GET, {"ticker": "NFLX", "section_key": "1a", "fiscal_year": 2001}),
]


def probe_list() -> list[tuple[str, dict[str, Any]]]:
    probes: list[tuple[str, dict[str, Any]]] = []
    for ticker in TICKERS:
        for tool in (QUOTE, FIN, LIST):
            probes.append((tool, {"ticker": ticker}))
    return probes + SECTION_PROBES


async def run_probe(tool_name: str, args: dict[str, Any]) -> dict[str, Any]:
    tool = get_tool(tool_name)
    call = {"name": tool_name, "args": args, "id": "probe", "type": "tool_call"}
    record: dict[str, Any] = {"tool": tool_name, "args": args}
    try:
        message = await tool.ainvoke(call)
        record["fired"] = False
        record["result_preview"] = str(getattr(message, "content", message))[:300]
    except Exception as exc:
        record["fired"] = True
        record["exc_type"] = f"{type(exc).__module__}.{type(exc).__name__}"
        record["raw"] = str(exc)
        record["model_saw"] = sanitize_tool_error(str(exc))
    return record


async def main_async(out: Path) -> None:
    setup_tools()
    records = []
    for tool_name, args in probe_list():
        record = await run_probe(tool_name, args)
        print(json.dumps(record, ensure_ascii=False)[:400], flush=True)
        records.append(record)
    out.write_text(json.dumps(records, indent=2, ensure_ascii=False))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    asyncio.run(main_async(args.out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
