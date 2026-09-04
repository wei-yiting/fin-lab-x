# Fix Round 3

> Fixer: Claude (general-purpose subagent) | Date: 2026-09-04

## Fixed

| Issue | How Fixed | Files Changed |
|-------|-----------|----------------|
| 1 [Minor M-3.1] | Reworded `test_other_dual_status_characters_score_one`'s docstring to describe what the test verifies directly, dropping "Round-2"/"round-1 fix"/"(Part A)" labels. | `test_language_policy_scorer.py` |
| 2 [Major M-3.2] | Added `_MAX_GENUINE_CHANGES = 3` module constant with rationale comment. `is_pure` now requires both `genuine_changes <= _MAX_GENUINE_CHANGES` and the existing ratio check. Updated docstring. | `scorer.py`, `test_language_policy_scorer.py` |
| 3 [Major M-3.3] | Added `assert len(_DUAL_STATUS_TRADITIONAL_CHARS) > 100, ...` immediately after computing the constant — names the source file, expected rough count, and what a low count implies. Not wrapped in try/except. | `scorer.py` |
| 4 [Blocking SP-3.1] | Added one paragraph to `benchmark/README.md`: the `boundary`×`may_pass_with_tuning` stratum's `dev`+1/`reserve`-1 adjustment and why (per-stratum rounding shortfall, this stratum absorbs it since it has the most rows). Seed value and remainder percentages deliberately not restored. `split.json` untouched. | `benchmark/README.md` |

## Not Fixed

None — all 4 items addressed.

## Tests Run

| Test Command | Result | Notes |
|--------------|--------|-------|
| `pytest backend/tests/evals/test_language_policy_scorer.py -v` | 21 passed | |
| `pytest backend/tests/` (full suite) | 1376 passed, 61 deselected | |
| `ruff format --check backend/` | 216 files already formatted | |
| `ruff check backend/` | All checks passed | |

**Orchestrator independently re-verified**: ran the full suite (`1376 passed, 61 deselected` — confirmed identical), `ruff format --check`/`ruff check` (both clean), grepped for leftover "Round-2"/"round-1"/"Part A" (zero matches), read `scorer.py` in full and confirmed the assertion and the hybrid `is_pure` logic (`genuine_changes <= 3 and ratio <= 0.15`) match the agreed design exactly, read `README.md` and confirmed the manual-adjustment paragraph is present without the seed-search narrative.

## Tests Added or Modified

| Test File | Added/Modified | What It Tests |
|-----------|-----------------|----------------|
| `test_language_policy_scorer.py` | Added `test_absolute_floor_fails_despite_low_ratio` | Response with 4 genuine changes (说/电/现/学) out of 57 total CJK chars, ratio ≈7.02% (well under 15%) — scores 0.0 because `genuine_changes (4) > _MAX_GENUINE_CHANGES (3)`. Fixer independently verified these numbers against the real module before writing the test, not hand-computed. |
| same | Docstring only | `test_other_dual_status_characters_score_one` reworded (issue 1) |
| same | Verified unmodified | `test_response_with_occasional_genuine_mistake_still_scores_one` (2 genuine changes) still scores 1.0 — confirms the floor didn't become zero-tolerance |
