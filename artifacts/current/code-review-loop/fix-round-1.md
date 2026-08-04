# Fix Round 1

> Fixer: claude-fable-5 (subagent) | Date: 2026-08-04
> Orchestrator pre-fixes this round: ADR renumbered 0006→0008 (collision with DEV-102's ADR on main) and condensed 901→249 words (M-1.4, user-adjudicated "concise even if >100 words"); commit `1012868`.

## Adjudications (user)

- **M-1.1** (gate fields have no consumer): **Declined** — conflicts with the explicit DEV-117/118 slice split; the consumer is DEV-118, blocked by this ticket. Reviewer lacked ticket context by design (quality axis is spec-blind).
- **M-1.3** (uncalibrated judge gated): keep `enabled: true`, add explicit YAML comment that no TPR/TNR calibration exists; labels owned by DEV-96.
- **M-1.4** (ADR length): condensed by orchestrator (see above); repo case law note — ADRs 0003–0007 also exceed the envelope §4 100-word limit (233–636 words); enforcement of the stock is out of this slice's scope.

### Fixed

| Issue ID | How Fixed | Files Changed |
|----------|-----------|---------------|
| SP-1.1 | `_resolve_rubric_files` now rejects absolute `rubric_file` values with a `ValueError` prefixed `Invalid scenario config in {config_path}:` before the path join | `backend/evals/eval_spec_schema.py`, `backend/tests/evals/test_eval_spec_schema.py` |
| M-1.2 | Deleted the both-set rejection branch in `validate_mode` (exclusivity is now an input-boundary rule only, enforced by `_reject_inline_rubrics`); deleted `test_scorer_config_rejects_rubric_and_rubric_file_together` plus its now-unused imports; added a why-comment at the `model_copy` call noting validation bypass is intentional; added a round-trip test | `backend/evals/eval_spec_schema.py`, `backend/tests/evals/test_language_policy_scorer.py`, `backend/tests/evals/test_eval_spec_schema.py` |
| M-1.3 | Added 2-line YAML comment on the `regression` block: judge NOT validated against human-labeled ground truth (no TPR/TNR measured); calibration labels owned by DEV-96; `enabled: true` kept per user decision | `backend/evals/scenarios/on_target_company/eval_spec.yaml` |
| m-1.1 | Schema example updated: required `regression.enabled` (no-default note), inline `rubric:` → `rubric_file:` (relative-path + inline-rejected notes), documented `gate` (default true) and `metric_floor` (default 1.0); added `on_target_company/` to the structure map | `backend/evals/README.md` |

### Not Fixed (with reason)

| Issue ID | Reason |
|----------|--------|
| M-1.1 | Declined by orchestrator/user — see Adjudications |

### Reverted (fix broke tests)

None.

### Tests Run

| Test Command | Result | Notes |
|--------------|--------|-------|
| `uv run pytest backend/tests/evals/ -q` | ✅ 162 passed | — |
| `uv run pytest backend/tests/ -q` | ✅ 882 passed, 49 deselected | — |
| `uv run ruff check backend/` | ✅ All checks passed | — |
| `uv run ruff format backend/` | ✅ 158 files unchanged | — |

### Tests Added or Modified

| Test File | Added/Modified | What It Tests |
|-----------|----------------|---------------|
| `backend/tests/evals/test_eval_spec_schema.py` | Added `test_llm_judge_absolute_rubric_file_fails` | Absolute `rubric_file` raises ValueError ("must be a path relative") |
| `backend/tests/evals/test_eval_spec_schema.py` | Added `test_loaded_config_round_trips_through_validation` | Loaded config (rubric + rubric_file both set) survives `ScenarioConfig.model_validate(config.model_dump())` |
| `backend/tests/evals/test_language_policy_scorer.py` | Deleted `test_scorer_config_rejects_rubric_and_rubric_file_together` | Premise invalidated by M-1.2 decision (both-set is a legitimate loaded state) |
