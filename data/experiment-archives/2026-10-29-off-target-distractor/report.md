# Off-target company — controlled replay eval (MVP)

Date 2026-10-29 · Linear DEV-232 (parent DEV-96) · Branch `feat/off-target-controlled-eval`
Design as run: [DESIGN_NOTE.md](DESIGN_NOTE.md)

> **MVP scope.** One afternoon's run: 10 fixture rows, 3 reps, one primary
> config plus two exploratory variants. Labels come from two LLM labelers plus
> documented rules, not a human annotator. Read the claim boundary before
> quoting numbers.

## Question

Traces showed answers about company X weaving in news about an unrelated
company Y that the news search returned alongside X's news. When that content
is in the evidence, does answer synthesis filter it out?

## Method

**Recorded tool outputs, replayed through a mocked tool.** Live news cannot be
controlled, so the eval freezes the evidence:

1. Source: the Tavily results that `reader_luna_medium` actually received in
   the reader 2×2 benchmark (archive `2026-10-28-reader-model-reasoning`), one
   run per question — the run with the most multi-company snippets.
2. Labels: every snippet sentence (1,067) labeled `target_or_neutral` /
   `relevant_other` / `unrelated_other` / `mixed` by Gemini and Codex
   independently (agreement 94.4 %, κ = 0.81). Disputed passages are kept;
   page chrome is neutral; passage continuations follow their passage.
3. Conditions (minimal pair): **C1** = recorded results unchanged;
   **C0** = the same results with the 62 consensus-unrelated sentences cut
   (0–25 % of a row's news text). Everything else is identical.
4. Replay tool: a `tavily_financial_search` stand-in with the live tool's
   name, description and args schema (sha256 of both identical to the live
   tool's), returning the k-th recorded call's results on the k-th call.
   SEC (Qdrant RAG) and Finnhub stay live.
5. Runs: 10 rows (those where C0 ≠ C1) × {C0, C1} × 3 reps, condition order
   alternating; raw JSON per run (`raw/`).
6. Scoring
   - **Deterministic:** does the answer name a company that appears *only* in
     the cut sentences (EN + zh aliases)?
   - **LLM judge:** fresh, context-free Claude Code subagents, blinded to arm
     and condition, applying the functional rubric (other-company content
     passes only if it supports the answer to the aspect asked), statement by
     statement.
   - **Judge validation:** 7 known-bad controls — a C0 answer with one injected
     sentence translated from that row's cut span.

## Results

### Primary: `reader_luna_medium`, original questions

| | C0 (cut) | C1 (original) |
|---|---|---|
| Deterministic mention of cut-only companies | 1 / 30 | 2 / 30 |
| LLM judge: answer has off-target content | **0 / 30** | **0 / 30** |
| Runs that called Tavily | 28 / 30 | 30 / 30 |
| C1 runs served a call that contains cut content (exposed) | — | 29 / 30 |

Paired exact McNemar over (row, rep): deterministic 1 vs 0 discordant,
p = 1.0; judge 0 vs 0. 95 % upper bound on the C1 off-target rate (0 / 30,
Clopper–Pearson): **11.6 %**, ignoring clustering by row.

All 3 deterministic hits are row 4 (TSMC vs ASML exposure), and the judge
passed every one of them: the answers name AMD and Google as TSMC customers
and cite a source titled "Nvidia Blackwell, Google TPUs…" — context, not
off-target content. The string check over-counts; the judge layer is what
separates "names another company" from "off-target".

### Judge validity

Known-bad controls flagged **7 / 7** (each flagged statement names the
injected company: Bank of America, Apple, Coca-Cola bottlers, Anthropic /
Bessemer, BP, UBS, Anglo American / De Beers). Zero of 120 real answers were
flagged, including the 4 deterministic hits read by hand as legitimate.
No known-good controls beyond that, so TNR is not separately measured.

### Exploratory: `reader_luna_none` (no reasoning)

| | C0 | C1 |
|---|---|---|
| Deterministic | 1 / 30 | 0 / 30 |
| LLM judge | 0 / 30 | 0 / 30 |
| C1 exposed | — | 19 / 30 |

Luna none calls Tavily less (1.6 vs 2.6 calls per C1 run), so with per-call
replay it reaches the call holding the cut content less often. Among exposed
runs the judge still flags nothing.

### Exploratory: open news-recap question, `reader_luna_medium`

Same fixtures, question replaced by `"{target companies} 最近有什麼新聞？"` —
the open recap shape of the trace failure and of the `on_target_company`
seed cases, which invites listing whatever the search returned.

| | C0 | C1 |
|---|---|---|
| Deterministic | 0 / 30 | 0 / 30 |
| LLM judge | 0 / 30 | 0 / 30 |
| C1 exposed | — | 28 / 30 |

No controls were added to this round (the same judge prompt was validated
above). Example (row 10, rep 1, C1 — evidence includes EU raids on Coca-Cola
bottlers and Microsoft/OpenAI items): the answer opens with "以下只列出能確認與
公司直接相關的內容" and covers Apple's DMA issues, Google's search remedies, and
states it found no reliable Meta-specific news — the unrelated items are
dropped explicitly.

### Examples

- Row 1 (Tesla, short-term shock vs long-term thesis), C1: the evidence
  includes a roundup paragraph on Bank of America's earnings miss and Baird's
  "overdone" call. No answer in 6 C1 runs (2 arms) mentions Bank of America.
- Row 4 (TSMC vs ASML exposure), C1: 24 cut sentences (Nvidia charges,
  DeepSeek sell-off, Rapidus, SoftBank). Answers name AMD / Google only as
  TSMC customers — the judge passes them as supporting context.
- Row 10 (Apple / Google / Meta regulatory risk): see the recap example above.

## Interpretation

Under controlled evidence the current reader configuration does **not**
reproduce the trace-observed failure: the unrelated passages reach the model
(29 / 30 exposed) and do not reach the answer (0 / 30), with or without
reasoning, and also on open news-recap questions (0 / 30). Pooled over the
three C1 cells, 0 / 90 (95 % upper bound ≈ 4 % before clustering). The eval itself is sensitive —
the judge catches every injected off-target sentence — so this is a negative
result about the agent, not a blind instrument.

## Claim boundary

- n = 10 rows × 3 reps per cell; rows are the clusters, so the effective
  sample is closer to 10 than 30. A 0 / 30 bounds the rate below ~12 %; it does
  not show the rate is 0.
- Fixtures were selected for the most multi-company content (stress test), and
  the cut content is mostly roundup paragraphs; it is not a prevalence estimate.
- Labels: two LLM labelers + rules; the 7 disputed passages were kept, not
  human-adjudicated. Human spot check of judge verdicts: not done.
- Only Tavily is replayed; SEC and Finnhub are live. Titles are not redacted
  (row 26 keeps two titles naming a removed company).
- The replay ignores the agent's query, so a "latest news" query can get
  2024–2025 snippets; one recap answer flags the results as dated.
- One config family (reader prompt, GPT-5.6 Luna); trace failures may come
  from other prompts or question types.

## Next steps

1. Human spot check of ~20 judge verdicts; known-good controls for TNR.
2. Broaden the question set toward the trace failure (open news recaps,
   single-company "what's new"), and harder distractors (same-sector peers).
3. Plug the replay tool into the scenario harness as a regression check once
   a reproducing condition exists.

## Reproduce

| | |
|---|---|
| Fixtures | `python -m backend.evals.experiments.off_target_distractor.fixtures` (reads `artifacts/current/off_target_labeling/`) |
| Runs | `python -m backend.evals.experiments.off_target_distractor.run --arm <arm> [--prompt-variant recap] --out-dir <dir> --rows 1,3,4,5,7,10,24,26,27,29 --reps 3 --no-prewarm` (Qdrant on :6333, `backend/.env`) |
| Deterministic | `python -m backend.evals.experiments.off_target_distractor.score --raw-dir <dir>/raw/<arm>` |
| Judge | `python -m backend.evals.experiments.off_target_distractor.judge build …` → one fresh subagent per batch with `PROMPT.md` → `judge score …` |
