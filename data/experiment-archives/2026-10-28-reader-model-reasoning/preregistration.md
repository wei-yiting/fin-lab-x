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

## Amendment 1 — 2026-10-27 23:30 (before any real answer was judged)

The Anthropic API account had no credit, so the judge is **not** a pinned API
call. Per the user's decision, the judge is a set of **fresh Claude Code
subagents** (general-purpose agent type, inheriting this session's model,
`claude-opus-5-5`) with no conversation context. Each subagent receives only
`judge_prompt.md` and one batch file (30 shuffled items: opaque id, question,
signals, answer) and writes one result file. One fresh subagent per batch,
identical instructions for every batch. The 40-item re-judge set is two extra
batches of 20, judged by two more fresh subagents.

Consequences: no fixed temperature or seed, so an exact re-run is not
guaranteed; the judge sees ~30 answers at once rather than one per request,
so within-batch comparison effects can't be ruled out (the prompt forbids
grading on a curve; the self-agreement re-judge uses different batch
compositions, which partly measures this). Thresholds and the decision rule
above are unchanged.

Also: the Gemini account was out of credit when the Luna workers started
(23:09). The Gemini workers started at 23:21 after the user topped up, so the
Gemini arms lag the Luna arms by ~12 min to ~30 min on the same row. That is
reported as a deviation.

## Amendment 2 — 2026-10-28 ~09:50 (secondary measures, added before they were run)

After the primary analysis, the user pointed out that the signals measure
whether a point is *mentioned*, not whether the answer is complete or faithful.
Two secondary measures are added. They are reported next to the primary
result and **do not change the pre-registered decision rule above**.

**Faithfulness (claim-level groundedness).** Scope: repetition 1 of
`reader_luna_none` and `reader_luna_medium` (the only arm that cuts both cost
and latency, vs the control), 60 answers. A fresh subagent receives the
question, the answer, and the tool outputs *that run* received, lists every
checkable factual claim (figures, dates, named events, attributions to
filings or news; at most 25) and labels each supported / unsupported /
contradicted by that evidence. Metric: support rate = supported / claims.
- Validity control: 30 *perturbed* answers (a rep-1 Luna answer with one
  figure altered). The judge passes if it flags the altered figure as
  unsupported or contradicted in ≥ 80% of them.
- Interpretation: `reader_luna_none` is non-inferior on faithfulness if the
  paired Δ support rate has a 95% CI lower bound > −0.05.

**Completeness (nugget recall), exploratory.** Per row, a fresh subagent
reads the question and the four rep-1 answers (one per arm, anonymised and
shuffled) and writes 4–8 key points a complete answer needs, each marked
vital / okay. The lists are **not human-reviewed**, so completeness is
exploratory and not a gate. Each rep-1 answer (120) is then scored per key
point (covered 1 / partial 0.5 / missing 0) by fresh subagents. Metric: vital
key-point recall.
- Validity control: 30 truncated answers (opening ~15% of a rep-1 Luna
  answer); paired Δ vs their base answers must be ≤ −0.25 with CI upper
  bound < 0.
