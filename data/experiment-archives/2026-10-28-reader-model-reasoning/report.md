# Reader config: does a lower model / reasoning tier keep answer quality?

> **One-line takeaway:** Under the reader configuration, **no cheaper or faster arm met the pre-registered bar, so the recommendation is to stay on `reader_luna_medium`**. `reader_luna_none` came closest: 28% cheaper per run, 5.9 s faster, routing recall no worse, and a signal-judge pass rate indistinguishable from the control (+0.004). But the lower CI bound (−0.033) missed the −0.03 non-inferiority margin by 0.003, so non-inferiority is *not established*. Both Gemini 3.6 Flash arms scored clearly lower on the judge (−0.13 to −0.15), skipped required sources more often, and cost 3.6–6.4× more per run. Faithfulness and completeness checks, added after the user's review ([§5](#5-secondary-quality-faithfulness-and-completeness)), show no significant loss for `reader_luna_none` either. But they lean the same way: vital key-point recall −0.03, and 5 of 30 answers with a contradicted claim vs 1 of 30, including an entity mix-up (Airbus ↔ AAR Corp).

This is the reference report: design, controlled variables, results with
uncertainty, judge method and validity checks, the decision, deviations and the
claim boundary. For the file list see [`README.md`](README.md). The decision rule
and thresholds were committed before any answer was judged:
[`preregistration.md`](preregistration.md).

## Reproduce

| | |
|---|---|
| Git tag | `experiment/2026-10-28-reader-model-reasoning` |
| Branch / Linear | `feat/reader-model-reasoning-benchmark` · DEV-231 (parent DEV-199) |
| Code that ran | `7bf21f8` (all Luna runs, Gemini batch 1); `e62e48b` / `7bc46ae` for the Gemini resumes. The run path (`harness.py`, `run.py`, configs) is identical across the three; only docs and `judge.py` changed. |
| Config dump | `python -m backend.evals.experiments.reader_model_reasoning.run dump --out-dir <dir>` → [`config_dump/`](config_dump/) |
| Runs | `python -m backend.evals.experiments.reader_model_reasoning.run run --out-dir <dir> --label <label> --rows all --rep K [--arms …]` for K = 1, 2, 3 (needs Qdrant on `:6333`, `backend/.env` with OpenAI, Gemini, Tavily, Finnhub keys + `EDGAR_IDENTITY`). Braintrust logging is off by default (`--braintrust` turns it on). |
| Process metrics | `python -m backend.evals.experiments.reader_model_reasoning.analyze --raw-dir <dir>/raw --out-dir <archive>` |
| Tool selection | `python -m backend.evals.experiments.tool_selection.analyze --labels tool_routing_labels.csv --archives <archive> --out-dir <archive>/tool_selection` |
| Judge | `… reader_model_reasoning.judge build-pool / collect / score / spot-check` (see module docstring); grading itself was done by fresh Claude Code subagents ([§4.1](#41-method)) |
| Faithfulness / completeness | `… reader_model_reasoning.grounding build-faith / build-nuggets / build-coverage / score` (grading by fresh subagents, as for the judge) |
| Decision | `python -m backend.evals.experiments.reader_model_reasoning.decide --toolsel-metrics … --process-summary … --judge-summary … --out-dir <archive>` |
| Model spend | ≈ US$5.58 for 360 runs (luna_none $0.35, luna_medium $0.48, gemini_minimal $1.72, gemini_medium $3.03), plus ~321 Tavily calls on pay-as-you-go. Judge: Claude Code subagents (no API bill). |

**Live data cannot be replayed.** Tavily news, Finnhub quotes and "latest 10-K"
resolution depend on run time. A re-run is a new sample; `raw.tar.gz` keeps what
these runs saw.

## 1. Question

The reader configuration is the product's direction (#85: −69% cost, −12.4 s vs
whole-section reading; #88: the reader prompt is what stops the agent skipping
required 10-Ks). Under it, does a cheaper or faster model setting keep **answer
quality** relative to `reader_luna_medium`, while cutting cost and latency?

## 2. Design

### Arms

| Arm | Model | Reasoning control |
|---|---|---|
| `reader_luna_none` | `openai:gpt-5.6-luna` | `reasoning.effort = none` |
| `reader_luna_medium` (**control**) | `openai:gpt-5.6-luna` | `reasoning.effort = medium` |
| `reader_gemini_minimal` | `google_genai:gemini-3.6-flash` | `thinking_level = minimal` (the floor) |
| `reader_gemini_medium` | `google_genai:gemini-3.6-flash` | `thinking_level = medium` |

Held fixed: the reader prompt (`agent_engine/agents/profiles/reader/system_prompt.md`,
referenced by path, identical rendered sha256 across arms), the six reader tools
with identical contracts (`finnhub_stock_quote`, `finnhub_company_basic_financials`,
`tavily_financial_search`, `sec_filing_list_sections`, `sec_filing_get_section`,
`sec_filing_search`), and `max_tool_calls_per_run: 10`. `run.py dump` fails unless
the arms differ only in identity and model settings: **PASS**
([`config_dump/config_alignment.json`](config_dump/config_alignment.json)). A loader
test pins the same.

### Rows and protocol

- All **30** zh diagnostic rows (dataset `2026-09-03`); the dev/holdout split is
  still `proposed` and was deliberately not applied (same as #84/#85).
- **3 repetitions** × 4 arms = **360 runs**, 0 task errors. One worker per
  repetition, row-major, arm order rotated by `(row + rep) mod 4`.
- Pre-warm of both SEC paths (list sections + search) for the 24 10-K filers in
  every worker before timed runs; all succeeded ([`prewarm/`](prewarm/)).
- Checkpointer off, unique session per run, 600 s timeout.
- Raw JSON per run is the record (Braintrust's monthly log quota was exhausted).

### Metrics and aggregation

Process metrics as in #84 (health, tools, hard tool errors, TTFT/E2E, tokens incl.
reasoning, per-call cost with the >272K long-context tier, Simplified-Chinese
drift, `[N]` citation integrity), SEC path as in #85, and #86's tool-selection
metrics against the hand labels. Each (row, arm) cell is averaged over its
repetitions first; 95% CIs are row-level (cluster) bootstraps, 2,000 resamples,
fixed seed; contrasts are paired by row.

## 3. Results — process and tool selection

### Arm summary

| Arm | Health [95% CI] | Median E2E s [95% CI] | Median TTFT s | Median tool calls | Median input tok | Median reasoning tok | Mean cost/run USD [95% CI] | Hard tool errors/run |
|---|---|---|---|---|---|---|---|---|
| reader_luna_none | 0.97 [0.90, 1.00] | 18.5 [17.1, 21.4] | 2.6 | 4.0 | 13,564 | 0 | 0.0038 [0.0034, 0.0043] | 0.07 |
| **reader_luna_medium** | 0.92 [0.82, 1.00] | 24.5 [21.5, 27.5] | 2.2 | 4.8 | 22,489 | 487 | 0.0053 [0.0047, 0.0060] | 0.14 |
| reader_gemini_minimal | 0.97 [0.90, 1.00] | 15.0 [13.9, 15.9] | 1.7 | 3.0 | 17,447 | 0 | 0.0192 [0.0178, 0.0205] | 0.07 |
| reader_gemini_medium | 0.97 [0.90, 1.00] | 34.6 [31.6, 37.0] | 2.1 | 4.0 | 20,441 | 3,605 | 0.0337 [0.0315, 0.0361] | 0.09 |

### Paired contrasts vs the control (treatment − `reader_luna_medium`)

| Arm | Δ health | Δ E2E s | Δ cost/run USD | Δ tool calls |
|---|---|---|---|---|
| reader_luna_none | +0.04 [+0.00, +0.12] | **−5.9 [−8.1, −3.7]** | **−0.0015 [−0.0020, −0.0010]** | −0.9 [−1.4, −0.3] |
| reader_gemini_minimal | +0.04 [+0.00, +0.12] | **−10.3 [−12.8, −8.0]** | +0.0138 [+0.0127, +0.0150] | −1.5 [−2.0, −1.1] |
| reader_gemini_medium | +0.04 [+0.00, +0.12] | +8.6 [+6.3, +10.7] | +0.0283 [+0.0266, +0.0303] | −0.8 [−1.2, −0.3] |

### Tool selection vs hand labels (#86 scorer; 29 routing rows)

| Arm | Routing recall [95% CI] | Δ recall vs control (paired) | Unnecessary-call rate | Ticker accuracy | Entity coverage (all pairs) |
|---|---|---|---|---|---|
| reader_luna_none | 0.99 [0.97, 1.00] | +0.04 [−0.01, +0.11] | 0.39 | 0.98 | 0.72 |
| **reader_luna_medium** | 0.94 [0.87, 1.00] | — | 0.31 | 0.98 | 0.78 |
| reader_gemini_minimal | 0.79 [0.66, 0.92] | **−0.14 [−0.28, −0.03]** | 0.34 | 0.99 | 0.56 |
| reader_gemini_medium | 0.89 [0.78, 0.97] | −0.06 [−0.16, +0.02] | 0.45 | 0.98 | 0.67 |

Full tables: [`tables.md`](tables.md), [`tool_selection/tables.md`](tool_selection/tables.md).

### What the numbers say

1. **Only `reader_luna_none` cuts both cost and latency.** It is 28% cheaper and
   5.9 s faster than the control, with fewer tool calls and no health loss.
2. **Gemini is faster at the low tier but not cheaper.** At list price ($0.75/M
   input vs $0.20/M), `reader_gemini_minimal` costs 3.6× the control per run, and
   `reader_gemini_medium` is both slower (+8.6 s) and 6.4× more expensive.
   Gemini's medium thinking tier spent a median 3,605 reasoning tokens per run.
3. **Gemini skips required sources more often**, the same pattern #86 found under
   the baseline prompt: routing recall 0.79 (minimal) and 0.89 (medium) vs 0.94,
   and lower multi-company entity coverage. The reader prompt narrows the gap for
   Luna (0.94–0.99) but not for Gemini.
4. **Health is at ceiling** (0.92–0.97, all CIs reach 1.00). All health-0 runs are
   Tavily-dependent rows; health does not separate the arms.
5. **Citations are intact.** Every run with `[N]` markers had matching
   definitions in Luna none (90/90), Luna medium (87/87), Gemini medium (89/90);
   Gemini minimal 86/89. Nearly every run used `sec_filing_search` only.

## 4. Results — answer quality (blinded signal judge)

### 4.1 Method

- **What is graded.** Each answer against its row's `draft_pass_signals` (3 per
  row), pass/fail per signal with a one-line reason. Primary metric: signal pass
  rate (share of the row's signals passed), per-row mean over repetitions.
- **Who grades.** Fresh **Claude Code subagents** (general-purpose agent type,
  inheriting this session's model, `claude-opus-5-5`), with no conversation
  context. The Anthropic API account had no credit, and the user chose this
  route ([Amendment 1](preregistration.md#amendment-1--2026-10-27-2330-before-any-real-answer-was-judged)).
  Claude produced none of the answers. Each subagent got only
  [`judge/poolA/judge_prompt.md`](judge/poolA/judge_prompt.md) (sha256
  `b38f46293a91…`) and one batch file, and wrote one result file. One fresh
  subagent per batch, identical instructions.
- **Blinding.** Real answers and controls were pooled, shuffled with a fixed seed,
  given opaque ids *after* the shuffle, and split into batches of 30. The judge saw
  id, question, signals and answer only; the key lives in
  [`judge/KEY_do_not_share/`](judge/KEY_do_not_share/). `sec://` chunk ids were
  masked in every answer.
- **Two pools.** Under the deadline, the Luna answers (pool A, 270 items incl.
  controls, 9 batches) were judged while the Gemini arms were still running; the
  Gemini answers (pool B, 310 items, 11 batches) after. Pool B mixed back in **40
  pool-A answers as anchors** to measure drift between pools.
- **Self-agreement.** 40 pool-A items were re-judged by two more fresh subagents
  in different batch compositions.

### 4.2 Discrimination check (judge validity, pre-registered)

Known-worse controls were built from one base answer per row per pool (60 per
kind across both pools): `truncated` (opening ~15%), `evidence_stripped` (every
sentence with a digit removed, plus citations, URLs and source tags), `off_topic`
(another row's answer).

| Control | n | Control pass rate | Δ vs its base / row [95% CI] | Threshold | Result |
|---|---|---|---|---|---|
| truncated | 60 | 0.36 | −0.50 [−0.59, −0.41] | Δ ≤ −0.25, CI < 0 | **PASS** |
| evidence_stripped | 60 | 0.46 | −0.40 [−0.51, −0.29] | Δ ≤ −0.25, CI < 0 | **PASS** |
| off_topic | 60 | 0.00 | −0.88 [−0.92, −0.83] | rate ≤ 0.15 | **PASS** |

**The judge passes the pre-registered check.** It is not uniform, though. Controls
built from **Luna** answers (pool A) dropped much less: truncated 0.59 and
evidence-stripped 0.74, a Δ of −0.21 that would fail on its own. Gemini-based
controls dropped to 0.36 and 0.46. Two reasons, from the judge's own reasons:

- Luna answers put the conclusion and key evidence in the opening paragraph, so
  the first 15% still meets "give a clear conclusion" and often "base it on
  disclosures".
- Stripping digits leaves *named* qualitative evidence ("EUV 禁令、荷蘭許可擴大"),
  and only ~27% of the signals are about evidence at all.

So the judge reliably catches gross degradation, but **the signals are coarse.**
Of 90 (row, signal) pairs, 63 were passed by every real answer across all four
arms, and 81 by every Luna answer.

| Reliability | Value |
|---|---|
| Self-agreement (40 re-judged, pool A) | 0.95 per signal, 0.85 per answer |
| Cross-pool anchors (40 pool-A answers re-judged in pool B) | 0.98 per signal, 0.95 per answer |
| Human agreement | **pending**: 15-answer blinded sheet in [`spot_check/`](spot_check/) |

### 4.3 Quality by arm

| Arm | Answers | Signal pass rate [95% CI] | All-signals-pass [95% CI] | Δ pass rate vs control [95% CI] |
|---|---|---|---|---|
| reader_luna_none | 90 | 0.948 [0.907, 0.981] | 0.84 [0.72, 0.94] | **+0.004 [−0.033, +0.041]** |
| **reader_luna_medium** | 90 | 0.944 [0.904, 0.981] | 0.83 [0.71, 0.94] | — |
| reader_gemini_minimal | 90 | 0.793 [0.707, 0.870] | 0.51 [0.33, 0.68] | **−0.152 [−0.237, −0.074]** |
| reader_gemini_medium | 90 | 0.815 [0.733, 0.889] | 0.58 [0.41, 0.73] | **−0.130 [−0.211, −0.063]** |

## 5. Secondary quality: faithfulness and completeness

*Added after the primary analysis, at the user's request, and pre-registered as
[Amendment 2](preregistration.md) before being run. These do not change the
decision rule.*

Both judged by fresh Claude Code subagents over blinded, shuffled batches with
opaque ids, using the same setup as §4.1. Prompts, batches, keys and results are
in [`grounding/`](grounding/). Scope is **repetition 1 only** (30 rows per arm).

### 5.1 Faithfulness: are the answer's claims supported by the evidence *that run* retrieved?

Each Luna answer was shown with every tool output its own run received. The
judge listed up to 25 checkable factual claims (figures, dates, named events,
attributions to filings or news) and labelled each supported, unsupported or
contradicted. Gemini was left out: it already fails on cost and routing.

| | reader_luna_none | **reader_luna_medium** |
|---|---|---|
| Claims checked (30 answers) | 427 | 446 |
| Support rate [95% CI] | 0.977 [0.956, 0.992] | 0.983 [0.971, 0.994] |
| Contradicted claims | 9 | 1 |
| Answers with ≥ 1 contradicted claim | **5 / 30** | 1 / 30 |
| Paired Δ support rate (none − medium) | −0.006 [−0.030, +0.015] | — |

- **Judge validity: PASS.** 28 answers had one figure altered by ~+40%. The
  judge flagged 26 of 28 (93% ≥ 80%). The 2 misses were construction errors,
  not claims: "10-K" turned into "14-K" (a `\b` boundary bug before a CJK
  character) and a ranking-table index. All valid altered figures were caught.
- **Average support: non-inferior** at the pre-set −0.05 margin.
- **The tail differs.** `reader_luna_none`'s contradictions are synthesis and
  attribution errors, not invented numbers:
  - **row 29:** used ticker `AIR` (AAR Corp, an aviation MRO company) as
    *Airbus*, with 4 claims citing AAR's 10-K and Finnhub data as Airbus's;
  - **row 20:** "cash flow covers the dividend" while its evidence shows OCF
    $7.4B < dividends $8.8B;
  - **row 28:** a North America segment margin quoted as Nike Brand overall;
  - **row 17:** advertising ranked 3rd when AWS is larger;
  - **row 7:** a forced sale called "still possible" after the evidence
    reported it was rejected.

  `reader_luna_medium`'s one contradiction was a −3% vs −2% slip. With n = 30
  this 5 vs 1 is descriptive, not significant. It is also the kind of error the
  signal judge cannot see: row 29 passes "cite the official disclosure" while
  citing the wrong company's.

### 5.2 Completeness: key-point (nugget) recall, exploratory

For each row a fresh subagent wrote 7–8 key points (≥ 4 vital) from the
question and the four arms' rep-1 answers, anonymised and shuffled. Each rep-1
answer (120) was then scored per point: covered 1, partial 0.5, missing 0.

| Arm | Vital recall [95% CI] | All-point recall | Δ vital vs control [95% CI] |
|---|---|---|---|
| reader_luna_none | 0.919 [0.880, 0.955] | 0.864 | −0.032 [−0.077, +0.008] |
| **reader_luna_medium** | 0.951 [0.923, 0.976] | 0.868 | — |
| reader_gemini_minimal | 0.868 [0.818, 0.913] | 0.756 | **−0.083 [−0.146, −0.023]** |
| reader_gemini_medium | 0.871 [0.812, 0.923] | 0.792 | **−0.080 [−0.155, −0.012]** |

- **Judge validity: PASS.** 30 truncated answers scored 0.51 vital recall, −0.42
  [−0.47, −0.37] vs their bases. Unlike the signals, the checklist sees that an
  opening paragraph is not a complete answer.
- **Limits.** The checklists were **not reviewed by a human**. They are drawn
  from the four arms' own answers, so they reward the facts any arm found.
  Repetition 1 only.

### 5.3 What the three quality lenses say together

| Lens | luna_none vs luna_medium | Gemini vs luna_medium |
|---|---|---|
| Signal pass rate (primary, 3 reps) | +0.004 (no difference) | −0.13 to −0.15 (worse) |
| Faithfulness support (rep 1) | −0.006 (no difference); contradictions 5 vs 1 answers | not measured |
| Vital completeness (rep 1, exploratory) | −0.032, CI [−0.077, +0.008] | −0.08 (worse) |

For Gemini all lenses agree: lower quality. For `reader_luna_none`, no lens shows
a significant loss. But the two depth-sensitive lenses both point the same way
(fewer key points, more contradicted claims), which is what one would expect if
dropping reasoning makes synthesis shallower. This doesn't meet a significance
bar; it does mean the "no detectable difference" in §4.3 should not be read as
"no difference".

## 6. Decision (pre-registered rule, applied mechanically: [`decision.json`](decision.json))

| Arm | Quality non-inferior (Δ lower bound > −0.03) | Judge discrimination | Routing not worse (Δ lower bound > −0.10) | Acceptable |
|---|---|---|---|---|
| reader_luna_none | ❌ −0.033 | ✅ | ✅ −0.011 | ❌ |
| reader_gemini_minimal | ❌ −0.237 | ✅ | ❌ −0.278 | ❌ |
| reader_gemini_medium | ❌ −0.211 | ✅ | ❌ −0.156 | ❌ |

**Recommendation: stay on `reader_luna_medium`.** No arm met every condition.

How to read the `reader_luna_none` result: the evidence says **"no detectable
difference"**, not "non-inferior". The point estimate is +0.004. The miss is
0.003 on a margin the 30-row design can barely resolve: the CI half-width is
~0.037, so even a true Δ of 0 would fail a −0.03 margin about as often as it
passes. Switching to `reader_luna_none` would save ~$0.0015 and ~6 s per
question. The cost of being wrong is answer quality the signals cannot see.
[§5](#5-secondary-quality-faithfulness-and-completeness) finds no significant
loss there either, but the depth-sensitive measures lean against
`reader_luna_none`: vital recall −0.03, and contradicted claims in 5/30 vs 1/30
answers. **If the product wants `reader_luna_none`'s savings, the next step is
a powered test, not a switch:** a frozen holdout, more rows, a human-reviewed
checklist, and the faithfulness check on all repetitions.

## 7. Deviations during execution

1. **Credits.** The Gemini account returned 402 (prepayment depleted) and the
   Anthropic account had no credit when the batch started. The Luna workers
   started at 2026-10-27 23:09 (Asia/Taipei); the Gemini workers started at 23:21
   after the user's top-up. The judge moved from a pinned API call to Claude Code
   subagents (Amendment 1, before any judging).
2. **Machine sleep and DNS.** The Mac went to sleep at ~23:42 with the Gemini
   workers mid-row and stayed asleep (maintenance wakes only) until morning. A
   resume at 01:44 also hung (sleep + a DNS outage). The final resume ran
   09:16–09:27 on 2026-10-28. **Consequence:** for rows ≥ ~21–23 in each
   repetition, Gemini answers saw live news and quotes ~10 hours later than Luna.
   SEC-only rows are unaffected. Workers skip runs with an existing raw record, and
   in-flight runs at a hang left no record, so no run is duplicated or partial.
3. **Two judge pools** instead of one ([§4.1](#41-method)), to meet the
   deadline. The cross-pool anchors agree 0.98 per signal, so pool drift is small;
   it can't be ruled out entirely.
4. **Braintrust off.** The monthly log quota was exhausted; `raw.tar.gz` is the
   only record.

## 8. Claim boundary

- **Population.** 30 Chinese diagnostic questions, 24 US 10-K filers + 3 non-10-K
  companies, one dataset version. Not the holdout split (still `proposed`).
- **The quality claim is signal-level.** `draft_pass_signals` check whether key
  moves are present (distinguish X from Y, cite disclosures, give a conclusion).
  They don't measure depth, completeness or factual correctness; the ceiling
  (63/90 pairs passed by every answer) bounds what can be detected. "Gemini
  scores lower" is a robust signal-level finding; "Luna none is as good as
  Luna medium" is not established.
- **Judge.** One model family (Claude), via Claude Code subagents: no fixed
  temperature or seed, so an exact re-run isn't guaranteed. Each subagent saw 30
  answers at once, so within-batch comparison effects can't be fully excluded;
  self-agreement 0.95 and cross-pool 0.98 bound the noise. Human agreement is
  pending the spot check.
- **No fact-checking against the world.** The signal judge doesn't verify facts.
  Faithfulness ([§5.1](#51-faithfulness-are-the-answers-claims-supported-by-the-evidence-that-run-retrieved))
  checks claims only against each run's own tool outputs, Luna arms, rep 1.
  "Supported" means "in the evidence", not "true".
- **Completeness is exploratory.** The checklists come from the arms' own
  answers and were not human-reviewed.
- **Time.** The Gemini/Luna time gap (deviation 2) affects Tavily/Finnhub-dependent
  rows in the family comparison.
- **Prices** are list prices read 2026-10-21 (same table as #84). Gemini's
  relative cost would change under a different price sheet; latency and quality
  would not.
