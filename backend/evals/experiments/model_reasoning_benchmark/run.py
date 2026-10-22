"""Model family x reasoning strength benchmark (2x2) on the zh diagnostic set.

Arms are the four benchmark configs (``luna_none``, ``luna_medium``,
``gemini_minimal``, ``gemini_medium``), all running the single canonical
prompt and the same five tools — only the model block differs.

Subcommands:

- ``dump``: resolve every arm (built model kwargs, tools, tool-contract
  hashes, raw/rendered prompt hashes) and fail unless the arms differ only
  in identity and model settings.
- ``run``: one repetition of rows x arms, row-major. Launch one process per
  repetition (``--rep 1``, ``--rep 2``, ...) to run repetitions in parallel.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

from backend.evals.experiments.harness import (
    BENCHMARK_DIR,
    CANONICAL_PROMPT,
    Arm,
    resolve_arm,
    run_experiment,
)

EXPERIMENT_NAME = "model-reasoning-benchmark"

ARM_NAMES = ["luna_none", "luna_medium", "gemini_minimal", "gemini_medium"]
ARMS = {
    name: Arm(name, BENCHMARK_DIR / "configs" / name, CANONICAL_PROMPT)
    for name in ARM_NAMES
}

# Keys allowed to differ between arms: identity strings and the model
# settings under test.
_ALLOWED_DIFF = {"arm", "config_dir", "identity", "config_model", "built_model"}


def arm_order(row_position: int, rep: int) -> list[str]:
    """Rotate arm order by row and repetition so no arm always runs first."""
    shift = (row_position + rep) % len(ARM_NAMES)
    return ARM_NAMES[shift:] + ARM_NAMES[:shift]


def cmd_dump(out_dir: Path) -> int:
    out_dir.mkdir(parents=True, exist_ok=True)
    resolved = {name: resolve_arm(arm) for name, arm in ARMS.items()}
    (out_dir / "resolved_configs.json").write_text(
        json.dumps(resolved, indent=2, ensure_ascii=False, default=str)
    )
    reference = resolved[ARM_NAMES[0]]
    unexpected = {
        name: sorted(
            k
            for k in reference.keys() | arm.keys()
            if reference.get(k) != arm.get(k) and k not in _ALLOWED_DIFF
        )
        for name, arm in resolved.items()
    }
    result = {
        "reference_arm": ARM_NAMES[0],
        "unexpected_differences": unexpected,
        "models": {
            name: {"config": arm["config_model"], "built": arm["built_model"]}
            for name, arm in resolved.items()
        },
    }
    (out_dir / "config_alignment.json").write_text(json.dumps(result, indent=2))
    ok = not any(unexpected.values())
    print(json.dumps(unexpected, indent=2))
    print("Config alignment (only model settings differ):", "PASS" if ok else "FAIL")
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
    run.add_argument(
        "--rows",
        choices=["dev", "all"],
        default="dev",
        help="'dev' = split-guarded dev rows; 'all' = every dataset row, "
        "an explicit opt-out of the (still proposed) split",
    )
    run.add_argument("--row-ids", help="Comma-separated subset (smoke runs)")
    run.add_argument("--arms", help=f"Comma-separated subset of {ARM_NAMES}")
    args = parser.parse_args(argv)

    if args.cmd == "dump":
        return cmd_dump(args.out_dir)

    arms = ARMS
    if args.arms:
        unknown = [a for a in args.arms.split(",") if a not in ARMS]
        if unknown:
            parser.error(f"Unknown arms: {unknown}")
        arms = {a: ARMS[a] for a in args.arms.split(",")}

    def order(row_position: int, rep: int) -> list[str]:
        return [a for a in arm_order(row_position, rep) if a in arms]

    asyncio.run(
        run_experiment(
            experiment_name=EXPERIMENT_NAME,
            arms=arms,
            arm_order=order,
            prewarm_tools=["sec_filing_list_sections"],
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
