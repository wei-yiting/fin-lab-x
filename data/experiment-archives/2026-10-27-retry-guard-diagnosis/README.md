# Retry-guard diagnosis — repeated failing tool calls vs the 10-call budget

> **One-line takeaway:** In 540 post-edgartools-fix runs the agent never repeated an
> identical failing tool call, so a retry guard would have changed 0 of 25 budget hits.
> No guard was built. Budget hits come from per-company fan-out on comparison questions.

## Start here

| Doc | Read this for |
|---|---|
| [`report.md`](report.md) | Definitions, per-arm counts, why no fix was warranted, claim boundary |

## Files

| File | What it is |
|---|---|
| `report.md` | The reference report |
| `per_run.csv` | One row per archived run (580 runs across the 2026-10-21 dev round and the two 2026-10-22 benchmarks): hard errors, budget-blocked calls, repeats after error with examples, distinct tickers, health |
| `diagnose_repeats.py` | The script that produced `per_run.csv` and the report's table from the source archives' raw records |

## Reproduce

Tag `experiment/2026-10-27-retry-guard-diagnosis`. The command is in `report.md`'s
Reproduce table.
