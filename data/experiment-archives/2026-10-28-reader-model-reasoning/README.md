# Reader config: does a lower model / reasoning tier keep answer quality? (30 rows × 3 runs × 4 arms)

This directory archives DEV-231: the model × reasoning 2×2 re-run under the product's
**reader** configuration (reader prompt + six reader tools incl. `sec_filing_search`),
with answer quality scored by a blinded signal judge and a pre-registered decision rule.

## Start here

| Doc | Read this for |
|---|---|
| [`report.md`](report.md) | The reference: design, config alignment, results with CIs, judge method, discrimination check, decision, deviations, claim boundary |
| [`preregistration.md`](preregistration.md) | Decision rule and judge thresholds, committed before any answer was judged (+ Amendment 1) |
| [`spot_check/spot_check.md`](spot_check/spot_check.md) | The pending human step: 15 blinded answers with the judge's verdicts; fill `spot_check.csv` |

## Files

| File | What it is |
|---|---|
| `metrics.csv` | One row per (row, arm, repetition), 360 rows: health, tools, latency, tokens, cost, citations, SEC path |
| `tables.md` / `summary.json` | Process-metric tables and machine-readable summaries (row-bootstrap CIs) |
| `tool_selection/` | #86 tool-selection scorer over these runs against the hand labels |
| `judge/` | Judge prompt, blinded batches (`poolA/`, `poolB/`, `.json` + `.md`), subagent results, re-judge set |
| `judge/KEY_do_not_share/` | Opaque id → (row, arm, repetition, kind). Not shown to the judge |
| `judge/judge_summary.json`, `judge/judge_scores.csv` | Unblinded judge results: per-arm pass rates, contrasts, discrimination check, self-agreement |
| `grounding/` | Secondary quality (Amendment 2): faithfulness (`faith/`: prompt, batches with each run's evidence, results; perturbed-figure control) and completeness (`nuggets/` checklists, `coverage/` scoring, truncated control); keys in `grounding/KEY_do_not_share/`; `grounding_summary.json` |
| `decision.json` | The pre-registered rule applied mechanically |
| `config_dump/` | All four arms as resolved + the alignment check (only model settings differ: PASS) |
| `prewarm/`, `run_logs/` | Per-worker SEC pre-warm reports; code commit per launch |
| `raw.tar.gz` | Full per-run records (source of truth; Braintrust upload was off). `tar xzf raw.tar.gz` |

## Reproduce

Tag `experiment/2026-10-28-reader-model-reasoning`. Commands are in `report.md`'s Reproduce table.
