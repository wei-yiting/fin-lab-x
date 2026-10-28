"""Model family x reasoning strength (2x2) under the reader configuration.

Same question as ``model_reasoning_benchmark``, but every arm runs the
product's reader bundle — the reader profile's prompt and its six tools
(incl. ``sec_filing_search``) — instead of the canonical baseline prompt.
Control arm is ``reader_luna_medium`` (the RAG-ablation arm); the other
three live next to it in ``benchmark/ablations/`` and differ only in the
model block.

Subcommands:

- ``dump``: resolve every arm and fail unless the arms differ only in
  identity and model settings.
- ``run``: one repetition of rows x arms, row-major, arm order rotated by
  row and repetition. One process per repetition. Raw JSONs are the record;
  ``--braintrust`` additionally logs to Braintrust.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

from backend.evals.experiments.harness import (
    BACKEND_DIR,
    BENCHMARK_DIR,
    Arm,
    resolve_arm,
    run_experiment,
)

EXPERIMENT_NAME = "reader-model-reasoning"

READER_PROMPT = (
    BACKEND_DIR / "agent_engine" / "agents" / "profiles" / "reader" / "system_prompt.md"
)
CONTROL_ARM = "reader_luna_medium"
ARM_NAMES = [
    "reader_luna_none",
    "reader_luna_medium",
    "reader_gemini_minimal",
    "reader_gemini_medium",
]
ARMS = {
    name: Arm(name, BENCHMARK_DIR / "ablations" / name, READER_PROMPT)
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
    reference = resolved[CONTROL_ARM]
    unexpected = {
        name: sorted(
            k
            for k in reference.keys() | arm.keys()
            if reference.get(k) != arm.get(k) and k not in _ALLOWED_DIFF
        )
        for name, arm in resolved.items()
    }
    result = {
        "reference_arm": CONTROL_ARM,
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
    run.add_argument("--rows", choices=["dev", "all"], default="dev")
    run.add_argument("--row-ids", help="Comma-separated subset (smoke runs)")
    run.add_argument("--arms", help=f"Comma-separated subset of {ARM_NAMES}")
    run.add_argument("--braintrust", action="store_true")
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
            prewarm_tools=["sec_filing_list_sections", "sec_filing_search"],
            out_dir=args.out_dir,
            label=args.label,
            rep=args.rep,
            row_mode=args.rows,
            row_ids=args.row_ids.split(",") if args.row_ids else None,
            extra_metadata={"experiment": EXPERIMENT_NAME},
            log_to_braintrust=args.braintrust,
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
