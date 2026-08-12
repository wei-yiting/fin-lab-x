# BDD Verification — Round 2

## Phase 1 — Targeted re-verification (S-fallback-03, S-fallback-04)

Both scenarios independently re-constructed (different synthetic text than the Round 1 script,
to keep the evidence independent) and re-run against the post-fix code (commit `0a83ace`).

- **S-fallback-03**: PASS (3/3 rows). Row 2 ("Item 1A Compliance Program") now matches the
  Round-1-revised expectation (reject) — code behavior unchanged from Round 1, only the scenario's
  expected value changed, per the documented user ruling.
- **S-fallback-04**: PASS (2/2 rows). Row 2 ("12  34  56  78") now correctly rejected by the new
  `_FALLBACK_DIGITS_ONLY_RE` rule.
- Supplementary: both new pinned regression tests from the fix commit
  (`test_item_prefixed_title_rejection_pinned_current_behavior`,
  `test_digits_and_whitespace_line_rejected`) pass; full `test_block_detection.py` (45 tests) green.

## Phase 2 — Full regression (all 12 scenarios)

All 12 scenarios executed fresh against current code.

| Scenario | Round 1 | Round 2 |
|---|---|---|
| S-fallback-01 | PASS | PASS |
| S-fallback-02 | PASS | PASS |
| S-fallback-03 | FAIL | **PASS** |
| S-fallback-04 | FAIL | **PASS** |
| S-fallback-05 | PASS | PASS |
| S-fallback-06 | PASS | PASS |
| S-fallback-07 | PASS | PASS |
| S-fallback-08 | PASS | PASS |
| S-fallback-09 | PASS | PASS |
| S-fallback-10 | PASS | PASS |
| J-fallback-01 | PASS | PASS |
| J-fallback-02 | PASS | PASS |

No regressions: all 10 previously-passing scenarios remain green. Full raw run:
`pytest artifacts/current/temp/test_verification_round2_full.py -v` → 34 passed (0 failed, 0
errors) across the 12 scenarios' sub-cases. Corroborating run of the entire existing pinned suite
for this module: `pytest backend/tests/ingestion/sec_text_pipeline/ -q` → 131 passed.

## Summary

| Metric | Value |
|--------|-------|
| Total | 12 |
| Passed | 12 |
| Failed | 0 |
| Errors | 0 |

Automated verification loop complete — all scenarios pass. No code, test, or scenario files were
modified during Round 2 verification itself (read-only); the code fix and scenario revision that
made these pass both landed **before** this round, per
`artifacts/current/temp/bdd-verification-round-1-resolutions.md`.

## Manual Verification Phase — status

- **Manual Behavior Test**: none (confirmed empty in `verification-plan.md` — this feature has no
  UI, no physical-device or high-concurrency requirement). Nothing to present via the interactive
  checklist.
- **User Acceptance Test**: out of loop scope per skill principle #6 (checked at PR review time,
  not in this loop). 2 items pending: UAT-01 and UAT-02, both blocked on the `inspect` CLI, which
  does not exist yet (tracked separately as DEV-134).
