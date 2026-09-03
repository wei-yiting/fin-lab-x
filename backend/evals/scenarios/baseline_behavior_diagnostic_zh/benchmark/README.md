# Benchmark protocol (DEV-200/205/206)

Infrastructure and frozen artifacts for the fast-vs-reasoning model-configuration
benchmark defined in DEV-200. Lives under this scenario (not `profiles/`) because
`baseline_behavior_diagnostic_zh` is the frozen decision's benchmark body — see
`ProfileConfigLoader.load_from_dir()`'s docstring for why benchmark configs don't
live under `profiles/`.

## Layout

- `configs/{c1_luna_none,c2_luna_medium,c3_gemini_minimal,c4_gemini_medium}/orchestrator_config.yaml` —
  the 2×2 candidate matrix (family × reasoning strength). Each is a normal
  `WorkflowProfileConfig` YAML, loaded via `ProfileConfigLoader.load_from_dir()`.
  None of them ship a `system_prompt.md` — the loader injects the single
  canonical prompt below, so 4 configs can never drift into 4 slightly
  different prompts.
- `prompt/system_prompt.md` — the single canonical shared prompt. Seeded as an
  unmodified copy of the `baseline` profile's prompt; DEV-206 evolves it from
  here (product behavior, tool-contract changes, and the known failures below),
  cross-checked against all 4 configs before any revision is kept.
- `split.json` — the dev/holdout/reserve row-id split proposal (status:
  `proposed`, pending the 🧑 human split-review gate on DEV-200). Read via
  `backend.evals.diagnostic.row_selection.load_split_sidecar` /
  `apply_split`, which default to dev rows only — holdout/reserve need an
  explicit opt-in on the caller's side, and only after the split is frozen.

## Status

DEV-205 delivers the infrastructure above and the split *proposal*. DEV-206
evolves the prompt, runs the cross-config dev-set validation cycle, and
performs the actual freeze (commit + `experiment/2026-09-baseline-model-config-benchmark`
tag). Until that freeze, nothing here is authoritative — the split is a
candidate for human review, and the seeded prompt is baseline's, unmodified.

## Known failure sources DEV-206's prompt evolution targets

Recorded here (not as an exhaustive list — dev-set work is itself a discovery
surface, see DEV-200):

- Simplified/Traditional Chinese drift in zh responses — never previously
  addressed. Caught automatically by `language_policy`'s new
  `response_no_simplified_chars` scorer.
- Weak Tavily query construction — searches sometimes land on a ticker's
  general news page instead of the specific event asked about.
- Off-target company answers in multi-company questions — see
  `on_target_company`'s functional criterion (other-company content is only
  legitimate when it directly supports the answer about the asked-about
  company).
