"""Before/after tool error messages on the tool-error-case set (luna_medium).

Both arms run the same config (``benchmark/configs/luna_medium``), prompt and
tools. They differ only in the text ``_HandleToolErrors`` returns for a tool
exception:

- ``before``: ``sanitize_tool_error(str(exc))`` — byte-for-byte the
  pre-contract behavior (raise-site message text was not changed, only
  structured fields were added), patched in for the duration of the run.
- ``after``: the tool error contract (``format_tool_error``).

Rows run row-major; each row's before/after pair runs back to back, with the
order alternating by row and repetition. Launch one process per repetition.

Subcommands:

- ``dump``: resolve both arms and fail unless they are identical except for
  the arm name (the message difference is code, not config).
- ``run``: one repetition of rows x arms.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from pathlib import Path
from typing import Any
from unittest.mock import patch

from backend.agent_engine.streaming.tool_error_sanitizer import sanitize_tool_error
from backend.evals.experiments.harness import (
    BACKEND_DIR,
    BENCHMARK_DIR,
    CANONICAL_PROMPT,
    Arm,
    resolve_arm,
    run_experiment,
)

EXPERIMENT_NAME = "tool-error-messages"
SCENARIO_DIR = BACKEND_DIR / "evals" / "scenarios" / "tool_error_cases_zh"
CONFIG_DIR = BENCHMARK_DIR / "configs" / "luna_medium"

# 10-K filers the rows name (error rows c and the controls), warmed at their
# latest fiscal year. Year-specific filings (FY2022, FY2010, ...) stay cold;
# the alternating arm order spreads that cost over both arms.
PREWARM_TICKERS = [
    "INTC", "AAPL", "NVDA", "TSLA", "META", "XYZ",
    "BA", "WMT", "V", "KO", "DIS", "NFLX", "NKE",
]  # fmt: skip


def legacy_tool_error(exc: BaseException, tool_call: Mapping[str, Any]) -> str:
    """The pre-contract middleware text: redaction only."""
    return sanitize_tool_error(str(exc))


@contextmanager
def legacy_messages() -> Iterator[None]:
    with patch("backend.agent_engine.agents.base.format_tool_error", legacy_tool_error):
        yield


ARM_NAMES = ["before", "after"]
ARMS = {
    "before": Arm("before", CONFIG_DIR, CANONICAL_PROMPT, legacy_messages),
    "after": Arm("after", CONFIG_DIR, CANONICAL_PROMPT),
}


def arm_order(row_position: int, rep: int) -> list[str]:
    """Alternate which arm runs first by row and repetition."""
    return ARM_NAMES if (row_position + rep) % 2 == 0 else ARM_NAMES[::-1]


def cmd_dump(out_dir: Path) -> int:
    out_dir.mkdir(parents=True, exist_ok=True)
    resolved = {name: resolve_arm(arm) for name, arm in ARMS.items()}
    (out_dir / "resolved_configs.json").write_text(
        json.dumps(resolved, indent=2, ensure_ascii=False, default=str)
    )
    before, after = resolved["before"], resolved["after"]
    differing = sorted(
        k for k in before.keys() | after.keys() if before.get(k) != after.get(k)
    )
    ok = differing == ["arm"]
    print("Differing keys:", differing)
    print("Config alignment (only the arm name differs):", "PASS" if ok else "FAIL")
    return 0 if ok else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="cmd", required=True)
    dump = sub.add_parser("dump")
    dump.add_argument("--out-dir", type=Path, required=True)
    run = sub.add_parser("run")
    run.add_argument("--out-dir", type=Path, required=True)
    run.add_argument("--label", required=True)
    run.add_argument("--rep", type=int, required=True)
    run.add_argument("--row-ids", help="Comma-separated subset (smoke runs)")
    args = parser.parse_args(argv)

    if args.cmd == "dump":
        return cmd_dump(args.out_dir)

    asyncio.run(
        run_experiment(
            experiment_name=EXPERIMENT_NAME,
            arms=ARMS,
            arm_order=arm_order,
            prewarm_tools=["sec_filing_list_sections"],
            out_dir=args.out_dir,
            label=args.label,
            rep=args.rep,
            row_mode="all",
            row_ids=args.row_ids.split(",") if args.row_ids else None,
            extra_metadata={"experiment": EXPERIMENT_NAME},
            scenario_dir=SCENARIO_DIR,
            prewarm_tickers=PREWARM_TICKERS,
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
