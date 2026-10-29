# Which of #82's answer-language fixes keeps English answers in English? A final-answer replay ablation

> **One-line takeaway:** With the evidence frozen (102 recorded runs, final model call
> regenerated twice per condition), English questions stayed in English **89.7%** of the
> time as recorded (R0), **78.2%** after #82's neutral directive wording (R2; worse,
> McNemar p = 0.008), and **100%** once `ResponseLanguageMiddleware` is added (R3,
> 156/156; p < 0.0001 vs R2). The middleware alone on the old wording gets 155/156 (M).
> Removing the reader prompt's language rule did not hurt (95.5%, p = 0.08 vs R0).
> Traditional Chinese controls were 48/48 in every condition.

## Question

PR #94 measured #82's fixes with live runs: before 71/78, wording only 65/78, wording +
middleware 78/78. Live arms re-run the whole agent, so each arm also gets different
tool calls and different evidence. This experiment asks how much each fix contributes when
**every condition sees byte-identical evidence**.

## Method: final-answer replay

The 102 arm-A runs of [`2026-10-28-language-middleware`](../2026-10-28-language-middleware/)
are the recordings: reader profile, `gpt-5.6-luna`, old SEC directive wording, no
middleware, 13 English questions × 6 runs + 4 Traditional Chinese questions × 6 runs. Each
recorded run was turned into a message list: the user question, then every recorded tool
call with its recorded result. The tool calls and evidence stay frozen. Only the last step
is regenerated: the model call that writes the answer. It runs under each condition with
the same model and settings as the recording (`openai:gpt-5.6-luna`, `reasoning: on`, API
default effort = medium, the reader tools bound, Responses API).

The bug lives in that final call: the model has tens of thousands of tokens of English
10-K text in context and writes the answer in the wrong language. Freezing everything
before the final call removes the biggest source of variance between live arms (which
filings and how much text got retrieved), so a paired comparison on the same recorded run
isolates the text that each fix changes.

### Conditions

#82 was meant to be added one fix at a time: system-prompt rule → directive wording →
middleware. **The first step does not apply to the reader profile:** #82 added the
language rule to the *baseline* profile's prompt, and the reader prompt already contained
the same rule before #82 (arm A ran with it). So the prompt rule is measured by
**removing** it (P0) instead of adding it.

| Condition | Reader prompt language rule | SEC directive text in tool results | Middleware instruction |
|---|---|---|---|
| **P0** | removed | old | — |
| **R0** (as recorded) | present | old | — |
| **R2** | present | #82 neutral wording | — |
| **R3** (= #82) | present | #82 neutral wording | appended |
| **M** (middleware only) | present | old | appended |

- *Prompt rule* (removed in P0): the reader prompt bullet "Your final answer MUST be in
  the language of the USER'S MESSAGE … Re-read the user's message before writing the
  answer and match its language exactly." The tool-argument rule above it stays.
- *Directive*: in R2/R3 the old `language_directive_pre/post` strings ("The following SEC
  filing content is in English… regardless of the language of this content" / "End of SEC
  filing content. Reminder…") are replaced inside the recorded tool results with #82's
  wording ("Write your final answer in the same language as the user's question." /
  "Reminder: write your final answer in the same language as the user's question."). That
  is 220 pre + 220 post replacements across the 102 recordings.
- *Middleware*: the system message is built by calling
  `response_language._with_language_instruction` itself (production code), which appends
  "RESPONSE LANGUAGE: The user's latest message is written in English. Write your entire
  final answer in English, whatever language the tool outputs are in." (or Traditional
  Chinese).

Exact texts are in [`replay_config.json`](replay_config.json).

- **Samples:** 102 recordings × 5 conditions × 2 replays = 1020 final calls, 0 errors
  (130 rate-limited calls were retried).
- **Scorer:** PR #94's deterministic scorer, unchanged
  (`language_middleware/scorer.py`: script counts + function-word counts; zh answers must
  contain no Simplified-only characters). I also searched all 722 English passes for
  embedded CJK or Cyrillic phrases (the kind of failure #94's hand review caught): none
  found.
- **Stats:** Wilson 95% CIs; exact two-sided McNemar on pairs that share the same recording
  and replay index.

## Replay fidelity (R0 vs the recorded answers)

R0 replays the recorded final call with the recorded prompt and evidence. It differs from
the recording in two ways. The recording keeps each tool call and result but not the
original turn grouping (parallel calls in one turn) or the model's intermediate
reasoning, so each call is rebuilt as its own turn. And the final call is sampled again.

| | Recorded (arm A, scorer) | R0 replay |
|---|---|---|
| EN pass rate | 72/78 = 92.3% (#94 reports 71/78 after hand review) | 140/156 = 89.7% |
| Per-run pass/fail agreement | — | 184 / 204 (90%) |
| Recorded failures that fail again on replay | — | 4 / 12 replays |
| Recorded passes that fail on replay | — | 12 / 192 replays |

The replay reproduces the **rate** (92% → 90%) but not **which runs** fail. A recorded
drift is mostly re-sampled away, and a recorded English answer sometimes drifts on replay.
So the drift is a stochastic event at the final call whose probability depends on the
question and evidence (J&J litigation d06 and the Alphabet/Microsoft antitrust starter s3
fail most often). It is not a fixed property of a given trajectory, which is why each
recording is replayed twice and the analysis is paired.

## Results

### English questions (13 questions × 6 recordings × 2 replays = 156 per condition)

| Condition | EN in English | Rate | Wilson 95% CI | Qs with ≥1 failure | Wrong languages |
|---|---|---|---|---|---|
| P0 — no prompt rule | 149 / 156 | 95.5% | 91.0–97.8% | 5 / 13 | es 4, zh-Hans 2, ja 1 |
| **R0 — as recorded** | 140 / 156 | 89.7% | 84.0–93.6% | 6 / 13 | es 14, ru 1, zh-Hans 1 |
| R2 — + neutral wording | 122 / 156 | 78.2% | 71.1–84.0% | 10 / 13 | es 20, ja 10, ru 2, zh-Hans 2 |
| **R3 — + middleware (= #82)** | **156 / 156** | **100%** | 97.6–100% | **0 / 13** | — |
| M — middleware only, old wording | 155 / 156 | 99.4% | 96.5–99.9% | 1 / 13 | es 1 (d06) |

Traditional Chinese controls (4 questions × 6 recordings × 2 replays): **48/48 in every
condition**.

### Paired comparisons (exact McNemar, 156 pairs)

| Comparison | Pass only in first | Pass only in second | p |
|---|---|---|---|
| P0 → R0 (prompt rule present) | 15 | 6 | 0.078 |
| R0 → R2 (+ neutral wording) | 30 | 12 | **0.008** (worse) |
| R2 → R3 (+ middleware) | 0 | 34 | **1.2 × 10⁻¹⁰** |
| R0 → M (middleware only) | 0 | 15 | **6.1 × 10⁻⁵** |
| R0 → R3 (all of #82) | 0 | 16 | **3.1 × 10⁻⁵** |
| M → R3 (wording, given middleware) | 0 | 1 | 1.0 |

### Reading

1. **The middleware is the fix.** Adding it never turned a pass into a failure (0
   discordant pairs against it in every comparison) and removed every failure on top of
   either directive wording: 156/156 with the new wording, 155/156 with the old one.
2. **The neutral rewording on its own made things worse on the same evidence**:
   89.7% → 78.2% (p = 0.008), and the wrong-language mix shifted toward Japanese (1 → 10).
   PR #94's live runs showed the same direction (83% vs 91%) but could not separate it from
   noise (Fisher p = 0.23). The paired replay can.
3. **The reader prompt's language rule did not help** at the final call: removing it gave
   95.5% vs 89.7% (p = 0.08, not significant). The rule tells the model that tool outputs
   are English, which may prime the same misreading as the old directive, but this run
   does not establish that.
4. **The one middleware failure** (M, d06, Spanish) shows the appended instruction is a
   strong, not absolute, guarantee. With the new wording (R3) it was 156/156.

## Claim boundary

- **Model change not covered.** #82 also moved the *baseline* profile from `gpt-5-nano` to
  `gpt-5.6-luna`. This replay is reader + Luna only. The original "2/4 English per run"
  symptom was baseline + nano + a Chinese prompt example and is not measured here.
- **Final call only.** The trajectory is frozen, so any effect of the fixes on tool
  selection, query language or number of calls is out of scope. These are effects on the
  answer-writing call given identical evidence.
- **Reconstructed trajectories.** Turn grouping and intermediate reasoning are not in the
  recordings. Fidelity above shows R0 reproduces the recorded failure rate but not
  run-level outcomes.
- **Clustering.** The 156 pairs come from 13 questions; failures cluster on a few (d06,
  s3, d17, s1). McNemar treats pairs as independent, so p-values are optimistic about
  generalising to new questions. The direction is consistent across questions, though:
  R3 has 0 failures on all 13.
- **Prompt rule measured by removal**, on a prompt that otherwise already had #82-era
  content. That is not the same as adding the rule to baseline, which is what #82 did.
- **Chinese controls** are short, single-language questions about US stocks. Mixed-language
  questions are not tested. They show no regression, not an improvement (no zh failures
  were ever recorded).
- English-vs-other detection is the deterministic scorer. Failures are whole-answer
  language switches, and passes were checked for embedded CJK or Cyrillic phrases, but not
  every answer was read by hand.

## Cost

1020 final calls, US$3.04 total (≈ US$0.60 per condition; US$0.20/M input, US$0.02/M
cached, US$1.20/M output), plus a US$0.03 smoke test. Wall-clock ≈ 10 minutes at 6–24
concurrency (rate limits hit at 44 concurrent calls; failed calls were rerun).

## Reproduce

```bash
python -m backend.evals.experiments.language_replay.replay --rep 1 \
    --out data/experiment-archives/2026-10-29-language-replay/raw
python -m backend.evals.experiments.language_replay.replay --rep 2 \
    --out data/experiment-archives/2026-10-29-language-replay/raw
python -m backend.evals.experiments.language_replay.analyze \
    data/experiment-archives/2026-10-29-language-replay
```

`analyze.py` reads `raw/*.json` if present, else the packed `raw.jsonl.gz`.
Replays are sampled (temperature is ignored by reasoning models), so reruns give similar
rates, not identical answers.
