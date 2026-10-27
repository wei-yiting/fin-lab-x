# Pre-registration — reader-config model × reasoning 2×2 (DEV-231)

Committed before any answer was judged and before any arm-level result was
looked at. The commit timestamp of this file is the evidence. Anything decided
later is reported as a deviation.

## Question

Under the reader configuration (reader prompt + six reader tools incl.
`sec_filing_search`), does a cheaper or faster model setting keep answer quality
relative to `reader_luna_medium`?

Arms: `reader_luna_none`, `reader_luna_medium` (control), `reader_gemini_minimal`,
`reader_gemini_medium`. Only the model block differs (`run.py dump` gate).

## Quality measure

- Primary quality metric: **signal pass rate** — per answer, the share of that
  row's `draft_pass_signals` the judge marks pass; averaged over a cell's
  repetitions, then over rows.
- Secondary: all-signals-pass rate.
- Judge: scripted, one request per answer, fixed prompt (sha256 recorded in
  `judge_config.json`), fixed model and settings recorded there. The judge sees
  an opaque id, the question, the signals and the answer, nothing else.
- All real answers and the controls below are judged in one shuffled pool.

## Discrimination check (gate for any quality claim)

One base answer per row (seeded random draw over all arms × reps) yields two
controls; a third uses another row's answer:

| Control | Built as | Pass condition |
|---|---|---|
| `truncated` | opening ~15% of the base answer, cut at a sentence end | paired Δ (control − its base answer) ≤ −0.25 **and** 95% CI upper bound < 0 |
| `evidence_stripped` | base answer minus every sentence containing a digit, citation markers, reference lines, URLs, bracketed source tags | paired Δ ≤ −0.25 **and** 95% CI upper bound < 0 |
| `off_topic` | a real answer to a different row, judged against this row's signals | control signal pass rate ≤ 0.15 |

The judge **passes** the discrimination check only if all three hold. If it
fails, the report says the judge cannot support a quality claim, and no arm is
recommended on quality grounds.

Also reported, not gating: judge self-agreement on a 40-item re-judge
(signal-level; < 0.85 is flagged as judge noise), the number of (row, signal)
pairs that every real answer passes (ceiling indicator), and human agreement on
the 15-answer spot check once the user completes it.

## Decision rule

A cheaper/faster arm is **acceptable** only if all hold:

1. Signal pass rate non-inferior to `reader_luna_medium`: lower bound of the
   95% row-bootstrap CI of the paired per-row Δ (arm − control) **> −0.03**.
2. The judge passed the discrimination check.
3. Routing recall (#86 scorer, hand labels) not materially worse: lower bound
   of the 95% CI of the paired per-row Δ **> −0.10**.

Recommendation: among acceptable arms, the one with the lowest mean cost per
run; if two acceptable arms' cost CIs overlap, the one with the lower median
E2E latency. If none is acceptable, recommend staying on `reader_luna_medium`
and say which condition failed.

## Statistics

Per-row means over the 3 repetitions first; 95% CIs from a row-level (cluster)
bootstrap, 2,000 resamples, seed 20261022 (same as #84). Contrasts are paired
by row. 30 rows → the CI reflects question-level variation; it does not cover
time-of-day variation in live data.
