"""PROTOTYPE (DEV-121) — trace coverage check for the TTFT benchmark runs.

Verifies the "full trace coverage" half of the claim: every request issued by
ttft_benchmark_prototype.py must have a Langfuse trace whose span tree contains
at least one LLM generation and (for tool-using runs) at least one tool span.

Usage:
    uv run python backend/scripts/ttft_trace_coverage_check.py
"""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

from langfuse import Langfuse  # noqa: E402

TOOL_NAMES = (
    "finnhub_stock_quote",
    "finnhub_company_basic_financials",
    "tavily_financial_search",
    "sec_filing_list_sections",
    "sec_filing_get_section",
)

RESULTS_DIR = Path(__file__).parent / "ttft_results"


def benchmark_window() -> tuple[datetime, datetime]:
    starts = []
    for f in ("smoke.json", "full-run-1.json"):
        data = json.loads((RESULTS_DIR / f).read_text())
        starts.append(datetime.fromisoformat(data["started_at"]))
    return min(starts) - timedelta(minutes=2), max(starts) + timedelta(minutes=50)


def main() -> None:
    lf = Langfuse(
        public_key=os.environ["LANGFUSE_PUBLIC_KEY"],
        secret_key=os.environ["LANGFUSE_SECRET_KEY"],
        host=os.environ["LANGFUSE_BASE_URL"].strip('"'),
    )
    t_from, t_to = benchmark_window()
    print(f"window: {t_from.isoformat()} → {t_to.isoformat()}")

    traces = []
    page = 1
    while True:
        batch = lf.api.trace.list(
            from_timestamp=t_from, to_timestamp=t_to, limit=100, page=page
        )
        traces.extend(batch.data)
        if page >= batch.meta.total_pages:
            break
        page += 1

    print(f"traces found: {len(traces)}")
    complete, incomplete = 0, []
    for t in traces:
        full = lf.api.trace.get(t.id)
        obs = full.observations or []
        n_gen = sum(1 for o in obs if o.type == "GENERATION")
        tool_names = sorted(
            {o.name for o in obs if o.name and o.name.startswith(TOOL_NAMES)}
        )
        errors = [o.name for o in obs if o.level == "ERROR"]
        ok = n_gen >= 1 and len(obs) >= 2
        complete += ok
        if not ok or errors:
            incomplete.append((t.id, n_gen, len(obs), errors))
        print(
            f"  {t.timestamp.isoformat()}  obs={len(obs):3d} gen={n_gen:2d} "
            f"tools={len(tool_names):2d} {'OK' if ok else 'INCOMPLETE'}"
            f"{' errors=' + str(errors) if errors else ''}"
        )

    print(f"\ncomplete span trees: {complete}/{len(traces)}")
    if incomplete:
        print("incomplete/errored:")
        for row in incomplete:
            print(f"  {row}")


if __name__ == "__main__":
    main()
