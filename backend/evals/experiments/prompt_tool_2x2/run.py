"""Prompt x tool 2x2 factorial ablation on the zh diagnostic set.

The RAG bundle ablation changed the prompt and ``sec_filing_search``
together, so its effects cannot be split between them. This crosses the two
factors, model held fixed (``openai:gpt-5.6-luna``, reasoning effort
``medium``, tool budget 10):

=================  ==============================  ===============================
                   canonical (baseline) prompt     reader profile prompt
=================  ==============================  ===============================
5 base tools       A ``luna_medium``               D ``reader_prompt_no_search``
+ search           C ``luna_medium_plus_search``   B ``reader_luna_medium``
=================  ==============================  ===============================

D keeps the reader prompt verbatim, so it names a tool D does not have; the
analysis records every call to a tool outside the arm's toolset.

Subcommands:

- ``dump``: resolve all four arms and fail unless each differs from A only
  in identity, tools, and prompt, and the cells hold exactly the designed
  tool/prompt combinations.
- ``run``: one repetition of rows x {A, B, C, D}, row-major, the four arms of
  a row always back-to-back in a Williams-balanced order. One process per
  repetition.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path
from typing import Any

from backend.evals.experiments.harness import (
    BENCHMARK_DIR,
    CANONICAL_PROMPT,
    Arm,
    resolve_arm,
    run_experiment,
)
from backend.evals.experiments.rag_ablation.run import READER_PROMPT, diff_arms

EXPERIMENT_NAME = "prompt-tool-2x2"

ARM_A = "luna_medium"
ARM_B = "reader_luna_medium"
ARM_C = "luna_medium_plus_search"
ARM_D = "reader_prompt_no_search"
ARMS = {
    ARM_A: Arm(ARM_A, BENCHMARK_DIR / "configs" / ARM_A, CANONICAL_PROMPT),
    ARM_B: Arm(ARM_B, BENCHMARK_DIR / "ablations" / ARM_B, READER_PROMPT),
    ARM_C: Arm(ARM_C, BENCHMARK_DIR / "ablations" / ARM_C, CANONICAL_PROMPT),
    ARM_D: Arm(ARM_D, BENCHMARK_DIR / "ablations" / ARM_D, READER_PROMPT),
}
SEARCH_TOOL = "sec_filing_search"
# arm -> (has sec_filing_search, uses the reader prompt)
CELLS = {
    ARM_A: (False, False),
    ARM_B: (True, True),
    ARM_C: (True, False),
    ARM_D: (False, True),
}

# Williams design for 4 treatments: every arm takes every slot once, and
# every ordered pair of arms is adjacent exactly once, so carry-over from
# the preceding run is balanced across arms.
_ORDERS = [
    [ARM_A, ARM_B, ARM_D, ARM_C],
    [ARM_B, ARM_C, ARM_A, ARM_D],
    [ARM_C, ARM_D, ARM_B, ARM_A],
    [ARM_D, ARM_A, ARM_C, ARM_B],
]


def arm_order(row_position: int, rep: int) -> list[str]:
    return list(_ORDERS[(row_position + rep) % len(_ORDERS)])


def check_factorial(resolved: dict[str, dict[str, Any]]) -> dict[str, Any]:
    """Each arm vs A, plus the cell layout: who has search, who has which prompt."""
    control = resolved[ARM_A]
    pairwise = {
        name: diff_arms(control, arm) for name, arm in resolved.items() if name != ARM_A
    }
    base_tools = control["tools"]
    prompt_sha = {
        False: resolved[ARM_A]["prompt"]["raw_sha256"],
        True: resolved[ARM_B]["prompt"]["raw_sha256"],
    }
    layout_errors = []
    for name, (has_search, reader_prompt) in CELLS.items():
        arm = resolved[name]
        expected_tools = [*base_tools, SEARCH_TOOL] if has_search else base_tools
        if arm["tools"] != expected_tools:
            layout_errors.append(f"{name}: tools {arm['tools']} != {expected_tools}")
        if arm["prompt"]["raw_sha256"] != prompt_sha[reader_prompt]:
            layout_errors.append(f"{name}: prompt is not the designed cell's prompt")
    if prompt_sha[False] == prompt_sha[True]:
        layout_errors.append("the two prompt levels are identical")
    return {
        "vs_control": pairwise,
        "layout_errors": layout_errors,
        "ok": not layout_errors
        and all(
            not d["unexpected_differences"] and d["shared_tool_contracts_identical"]
            for d in pairwise.values()
        ),
    }


def cmd_dump(out_dir: Path) -> int:
    out_dir.mkdir(parents=True, exist_ok=True)
    resolved = {name: resolve_arm(arm) for name, arm in ARMS.items()}
    (out_dir / "resolved_configs.json").write_text(
        json.dumps(resolved, indent=2, ensure_ascii=False, default=str)
    )
    check = check_factorial(resolved)
    (out_dir / "factorial_config_diff.json").write_text(json.dumps(check, indent=2))
    print(json.dumps(check, indent=2))
    print("2x2 config alignment:", "PASS" if check["ok"] else "FAIL")
    return 0 if check["ok"] else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="cmd", required=True)
    dump = sub.add_parser("dump")
    dump.add_argument("--out-dir", type=Path, required=True)
    run = sub.add_parser("run")
    run.add_argument("--out-dir", type=Path, required=True)
    run.add_argument("--label", required=True)
    run.add_argument("--rep", type=int, required=True)
    run.add_argument("--rows", choices=["dev", "all"], default="dev")
    run.add_argument("--row-ids", help="Comma-separated subset (smoke runs)")
    args = parser.parse_args(argv)

    if args.cmd == "dump":
        return cmd_dump(args.out_dir)

    asyncio.run(
        run_experiment(
            experiment_name=EXPERIMENT_NAME,
            arms=ARMS,
            arm_order=arm_order,
            prewarm_tools=["sec_filing_list_sections", "sec_filing_search"],
            out_dir=args.out_dir,
            label=args.label,
            rep=args.rep,
            row_mode=args.rows,
            row_ids=args.row_ids.split(",") if args.row_ids else None,
            extra_metadata={"experiment": EXPERIMENT_NAME},
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
