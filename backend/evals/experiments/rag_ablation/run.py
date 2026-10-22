"""RAG capability-bundle ablation on the zh diagnostic set.

Does RAG over 10-Ks (``sec_filing_search``) beat finding the right section
and reading it whole (``sec_filing_get_section``)? The model is held fixed
(``openai:gpt-5.6-luna``, reasoning effort ``medium``):

- Arm A ``luna_medium``: the 5 baseline tools + the canonical (baseline)
  prompt — whole-section reading only.
- Arm B ``reader_luna_medium``: the same + ``sec_filing_search``, with the
  reader profile's prompt (its citation rules are written for search
  chunks), so this measures the bundle, not the tool alone.

Subcommands:

- ``dump``: resolve both arms and fail unless they differ only in identity,
  tools, and prompt.
- ``run``: one repetition of rows x {A, B}, row-major, the pair always
  back-to-back with the first arm alternating. One process per repetition.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path
from typing import Any

from backend.evals.experiments.harness import (
    BACKEND_DIR,
    BENCHMARK_DIR,
    CANONICAL_PROMPT,
    Arm,
    resolve_arm,
    run_experiment,
)

EXPERIMENT_NAME = "rag-bundle-ablation"

READER_PROMPT = (
    BACKEND_DIR / "agent_engine" / "agents" / "profiles" / "reader" / "system_prompt.md"
)
ARM_A = "luna_medium"
ARM_B = "reader_luna_medium"
ARMS = {
    ARM_A: Arm(ARM_A, BENCHMARK_DIR / "configs" / ARM_A, CANONICAL_PROMPT),
    ARM_B: Arm(ARM_B, BENCHMARK_DIR / "ablations" / ARM_B, READER_PROMPT),
}

# Keys allowed to differ: identity strings and the bundle under test.
_ALLOWED_DIFF = {
    "arm",
    "config_dir",
    "prompt_path",
    "identity",
    "tools",
    "tool_contracts",
    "prompt",
}


def arm_order(row_position: int, rep: int) -> list[str]:
    return [ARM_A, ARM_B] if (row_position + rep) % 2 == 0 else [ARM_B, ARM_A]


def diff_arms(a: dict[str, Any], b: dict[str, Any]) -> dict[str, Any]:
    differing = sorted(k for k in a.keys() | b.keys() if a.get(k) != b.get(k))
    shared_tools = set(a["tools"]) & set(b["tools"])
    return {
        "differing_keys": differing,
        "unexpected_differences": [k for k in differing if k not in _ALLOWED_DIFF],
        "tools_only_in_b": [t for t in b["tools"] if t not in a["tools"]],
        "tools_only_in_a": [t for t in a["tools"] if t not in b["tools"]],
        "shared_tool_contracts_identical": all(
            a["tool_contracts"][t] == b["tool_contracts"][t] for t in shared_tools
        ),
    }


def cmd_dump(out_dir: Path) -> int:
    out_dir.mkdir(parents=True, exist_ok=True)
    resolved = {name: resolve_arm(arm) for name, arm in ARMS.items()}
    (out_dir / "resolved_configs.json").write_text(
        json.dumps(resolved, indent=2, ensure_ascii=False, default=str)
    )
    diff = diff_arms(resolved[ARM_A], resolved[ARM_B])
    (out_dir / "ab_config_diff.json").write_text(json.dumps(diff, indent=2))
    print(json.dumps(diff, indent=2))
    ok = not diff["unexpected_differences"] and diff["shared_tool_contracts_identical"]
    print("A/B config alignment:", "PASS" if ok else "FAIL")
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
