# Prompt × Tool 2×2 Ablation — separating the reader prompt from `sec_filing_search` (30 rows × 3 runs × 4 cells)

> **One-line takeaway:** The routing win and the efficiency win come from different factors. **Not skipping required 10-K evidence is a prompt effect.** SEC-skip runs fell from 10/69 (A) and 7/69 (C) to 2/69 (D) and 0/69 (B), a prompt main effect of −0.11 [−0.22, −0.02]. The tool main effect was −0.04 [−0.09, +0.00], with no interaction. **Fewer SEC tokens and lower cost are a tool effect** (−27.4k tokens, −$0.0066 per run, prompt ≈ 0). **The 7–8 s latency gain needs both.** Search alone did not change latency (C − A +0.1 s); search under the reader prompt cut 7.3 s (interaction −7.5 s [−10.4, −5.1]). The skip effect rests on only 5 discordant rows: the bootstrap CI excludes 0, but the exact sign test gives p = 0.06.

This is the reference report: design, config alignment, results with uncertainty,
deviations, and the claim boundary. For what else is in this directory, see
[`README.md`](README.md).

## Reproduce

| | |
|---|---|
| Git tag | `experiment/2026-10-27-prompt-tool-2x2` |
| Branch / Linear | `feat/prompt-tool-2x2-ablation` (stacked on `feat/rag-bundle-ablation`) · DEV-223 (child of DEV-220) |
| Code that ran | commit `af807ea`. The analysis fix `eb4e7ac` (full-gap rows out of routing metrics, sign test) changed no run code. |
| Run window | 2026-10-27 10:27–11:29 UTC. All 360 runs in one window, 3 workers (one per repetition) in parallel, nothing else running. |
| Config dump | `python -m backend.evals.experiments.prompt_tool_2x2.run dump --out-dir <dir>` → [`config_dump/`](config_dump/) |
| Runs | `python -m backend.evals.experiments.prompt_tool_2x2.run run --out-dir <dir> --label 20261027-all30 --rows all --rep K` for K = 1, 2, 3 (needs Qdrant on `:6333` with the SEC collection, and `backend/.env` keys as in the model × reasoning benchmark) |
| Metrics | `python -m backend.evals.experiments.prompt_tool_2x2.analyze --raw-dir <dir>/raw --labels <tool_routing_labels.csv> --out-dir <archive>` |
| Tool-selection tables | `python -m backend.evals.experiments.tool_selection.analyze --labels <tool_routing_labels.csv> --archives <archive> --out-dir <archive>/tool_selection` |
| Labels | the final tool-routing label file, identical to [`../2026-10-27-tool-selection/labels.csv`](../2026-10-27-tool-selection/labels.csv) (rules R1–R6 in that directory's `labelling_rules.md`) |
| Braintrust | one experiment per (cell, repetition), see [`braintrust_links.json`](braintrust_links.json); incomplete for the last ~55 runs (§4) |
| Total API cost | ≈ US$3.33 model spend (A $1.25, B $0.47, C $0.60, D $1.01), plus ≈ $0.08 for the smoke run |

**Live data cannot be replayed.** A re-run is a new sample; [`raw.tar.gz`](raw.tar.gz) keeps
what these runs saw.

## 1. Question

The [RAG bundle ablation](../2026-10-22-rag-bundle-ablation/report.md) changed two things
at once: it added `sec_filing_search` and swapped the canonical prompt for the reader
profile's prompt. The [tool-routing analysis](../2026-10-27-tool-selection/README.md)
then found that the bundle arm never skipped a 10-K the labels mark 必要 (0/69 runs),
while the control skipped 9/69, and none of those skips hit the tool budget. The agent
chose not to look. Which change caused this: the prompt, the tool, or the combination?
And which of them produces the bundle's token, latency and cost savings?

## 2. Design

A 2×2 factorial with the model held fixed:

| | canonical (baseline) prompt, 4,516 chars | reader profile prompt, 8,970 chars |
|---|---|---|
| **5 base tools** | **A** `luna_medium` (control) | **D** `reader_prompt_no_search` (prompt only) |
| **+ `sec_filing_search`** | **C** `luna_medium_plus_search` (tool only) | **B** `reader_luna_medium` (bundle) |

| | All four cells |
|---|---|
| Model | `openai:gpt-5.6-luna`, Responses API, `reasoning={effort: medium, summary: auto}` (langchain-openai drops temperature at this effort) |
| Tool budget | 10 calls per run |
| Base tools | `finnhub_stock_quote`, `finnhub_company_basic_financials`, `tavily_financial_search`, `sec_filing_list_sections`, `sec_filing_get_section` |
| Prompts | Referenced by path, never copied: `benchmark/prompt/system_prompt.md` (A, C) and `agent_engine/agents/profiles/reader/system_prompt.md` (B, D). The two configs under `benchmark/configs/` keep their single-canonical-prompt guarantee; C and D live under `benchmark/ablations/` beside B. |

**How the prompts differ on SEC.** The reader prompt opens by calling 10-K filings the
"primary evidence source". It has an SEC routing section: pinpoint questions go to
`sec_filing_search`, synoptic questions to `list_sections` + `get_section`, one call per
(ticker, fiscal year). It also has two SEC worked examples. The canonical prompt has a
one-line SEC note at the end ("call `sec_filing_list_sections` first … then
`sec_filing_get_section`") and no SEC example. The reader prompt also differs outside
SEC (language policy, grounding, `[N]` citation rules), so the prompt factor is this
whole prompt, not its SEC section alone.

**Arm D's prompt names a tool D lacks.** D keeps the reader prompt verbatim, so it still
tells the model to use `sec_filing_search`. Editing that out would make D a third
prompt rather than the "prompt only" cell. The analysis counts, per run, every call to a
tool outside the arm's toolset (LangGraph's `ToolNode` would return an error
`ToolMessage` for it).

**Config alignment.** `run.py dump` resolves all four cells the way the orchestrator
builds them. It hashes each tool's description and argument schema plus the raw and
rendered prompt, then checks two things: every cell differs from A only in identity,
tools and prompt, and each cell holds its designed tool set and prompt. Result:
**PASS** ([`config_dump/factorial_config_diff.json`](config_dump/factorial_config_diff.json)).
The shared tools' contracts are hash-identical in all cells; A and C share prompt hash
`83bf45ca…`, and B and D share `33ea9c8d…`. Config-loader tests pin the same layout.

**Rows and protocol.** All 30 rows of the zh diagnostic dataset × 3 repetitions × 4 cells
= 360 runs. The split is not applied, as in the previous two experiments, and
`split.json` is unchanged. Execution is row-major: a row's four cells run back-to-back
before the next row. Their order follows a 4×4 Williams square, indexed by
`(row + rep) mod 4`, so each cell takes each slot equally often and each ordered pair
of cells is adjacent once per square. Before timing starts, each worker pre-warms both
SEC paths for all 24 10-K filers named by the dataset; all 3 × 24 succeeded. A and B
were re-run here rather than reused from 2026-10-22, because news, quotes and the latest
10-K change between days.

**Metrics.** Code-only, no LLM judge:

- *Process* (as in the bundle ablation): execution health, SEC path, SEC evidence tokens
  entering context (cl100k), E2E latency, cost from per-call token usage at list prices,
  tool calls, budget hits.
- *Routing* (the tool-selection module's `score_run`, run against the final hand labels):
  routing recall (every 必要 source and one 擇一必要 source used), unnecessary-call rate
  (any 不必要 source used), and entity coverage. Rows with a full coverage gap are left
  out.
- *SEC skip*: on the 23 rows where SEC 10-K is 必要 and nothing is out of reach (69 runs
  per cell), the run called no SEC tool. A variant also requires a call that succeeded.
  "At budget" means the run had hit the tool budget.
- *Contrasts*: per-row means over repetitions first, then per-row contrasts with a
  row-level bootstrap 95% CI (2,000 resamples, fixed seed). With cell means A–D on a row:
  prompt main effect = ((D − A) + (B − C)) / 2, tool main effect = ((C − A) + (B − D)) / 2,
  interaction = (B − D) − (C − A). An exact sign test on the same per-row contrasts checks
  the bootstrap for the routing metrics. There, a few rows carry the whole contrast and a
  percentile CI can be optimistic.

## 3. Results

### Cells

| Cell | Arm | Runs | Task errors | Health [95% CI] | SEC path (runs) | Hard tool errors/run | Runs at budget | Unknown-tool calls | Total cost USD |
|---|---|---|---|---|---|---|---|---|---|
| A | luna_medium | 90 | 0 | 0.91 [0.82, 0.99] | G×67 ∅×23 | 0.12 | 9 | 0 | 1.25 |
| B | reader_luna_medium | 90 | 0 | 0.92 [0.83, 0.99] | S×82 S+G×3 ∅×5 | 0.12 | 5 | 0 | 0.47 |
| C | luna_medium_plus_search | 90 | 0 | 0.93 [0.84, 1.00] | S×58 S+G×6 G×4 ∅×22 | 0.13 | 6 | 0 | 0.60 |
| D | reader_prompt_no_search | 90 | 0 | 0.89 [0.78, 0.98] | G×81 ∅×9 | 0.20 | 4 | 0 | 1.01 |

SEC path codes: S = search only, G = get_section only, S+G = both, ∅ = no SEC tool.

### Routing per cell (label-scored)

| Cell | Routing recall [95% CI] | Unnecessary-call rate | Entity coverage | **SEC skips / SEC-必要 runs** | Skips at budget | Skipped rows (runs) |
|---|---|---|---|---|---|---|
| A | 0.89 [0.77, 0.99] | 0.34 [0.20, 0.51] | 0.83 [0.64, 1.00] | **10 / 69** | 0 | 3×3, 14×3, 26×3, 10×1 |
| B | 0.95 [0.89, 1.00] | 0.26 [0.11, 0.43] | 0.75 [0.58, 0.92] | **0 / 69** | 0 | – |
| C | 0.87 [0.77, 0.97] | 0.28 [0.14, 0.41] | 0.81 [0.61, 0.97] | **7 / 69** | 0 | 3×2, 14×2, 26×2, 7×1 |
| D | 0.97 [0.91, 1.00] | 0.23 [0.10, 0.38] | 0.86 [0.69, 1.00] | **2 / 69** | 0 | 14×1, 26×1 |

Recall and unnecessary-call rate cover 29 rows (row 4, a full coverage gap, is out).
Requiring a successful SEC call changes no skip count. Numbers match the tool-selection
module's own tables over these runs ([`tool_selection/tables.md`](tool_selection/tables.md)).

### Factorial readout (per-row contrasts, row bootstrap 95% CI)

| Effect | Δ routing recall (29 rows) | Δ SEC-skip rate (23 rows) | Δ SEC tokens (30) | Δ tool calls (30) | Δ E2E s (30) | Δ cost USD/run (30) |
|---|---|---|---|---|---|---|
| tool, baseline prompt (C − A) | −0.01 [−0.10, +0.07] | −0.04 [−0.10, +0.01] | −26,899 [−46,001, −13,438] | −0.0 [−0.4, +0.3] | +0.1 [−1.1, +1.5] | −0.0072 [−0.0140, −0.0027] |
| tool, reader prompt (B − D) | −0.01 [−0.09, +0.07] | −0.03 [−0.07, +0.00] | −27,900 [−39,933, −18,130] | −1.5 [−2.1, −0.9] | −7.3 [−9.8, −5.2] | −0.0060 [−0.0084, −0.0040] |
| prompt, no search (D − A) | +0.08 [+0.01, +0.17] | −0.12 [−0.23, −0.01] | −1,877 [−11,295, +5,683] | −0.4 [−0.8, +0.0] | −0.6 [−2.6, +1.9] | −0.0027 [−0.0075, +0.0006] |
| prompt, with search (B − C) | +0.08 [−0.01, +0.17] | −0.10 [−0.20, −0.03] | −2,878 [−5,103, −691] | −1.8 [−2.3, −1.3] | −8.0 [−9.6, −6.6] | −0.0015 [−0.0020, −0.0009] |
| bundle (B − A) | +0.07 [−0.06, +0.22] | −0.14 [−0.30, −0.01] | −29,777 [−49,692, −15,480] | −1.8 [−2.4, −1.3] | −7.9 [−9.2, −6.6] | −0.0087 [−0.0155, −0.0040] |
| **prompt main effect** | **+0.08 [+0.01, +0.17]** | **−0.11 [−0.22, −0.02]** | −2,378 [−7,541, +2,020] | −1.1 [−1.4, −0.7] | −4.3 [−5.7, −2.9] | −0.0021 [−0.0045, −0.0003] |
| **tool main effect** | −0.01 [−0.09, +0.06] | −0.04 [−0.09, +0.00] | **−27,400 [−42,680, −15,487]** | −0.8 [−1.1, −0.4] | −3.6 [−4.9, −2.3] | **−0.0066 [−0.0111, −0.0034]** |
| **interaction** | +0.00 [−0.07, +0.07] | +0.01 [−0.03, +0.07] | −1,001 [−8,075, +8,044] | **−1.4 [−2.1, −0.8]** | **−7.5 [−10.4, −5.1]** | +0.0012 [−0.0020, +0.0060] |

**Exact sign test on the routing contrasts** (rows where the contrast is < 0 / > 0, ties
dropped, two-sided p):

| Effect | routing recall | SEC-skip rate |
|---|---|---|
| prompt main effect | 1 / 7 (p = 0.070) | 5 / 0 (p = 0.062) |
| tool main effect | 4 / 4 (p = 1.000) | 4 / 1 (p = 0.375) |
| interaction | 3 / 4 (p = 1.000) | 1 / 2 (p = 1.000) |

The full tables, including unnecessary-call rate and the per-row SEC path of every cell,
are in [`tables.md`](tables.md).

### What the numbers say

1. **Not skipping the 10-K is a prompt effect.** Swapping in the reader prompt cut
   SEC-skip runs under either toolset: 10 → 2 without search, 7 → 0 with it. Adding search
   under a fixed prompt moved skips only slightly (10 → 7, 2 → 0). The prompt main effect
   is −0.11 [−0.22, −0.02], the tool main effect −0.04 [−0.09, +0.00], and the interaction
   is ≈ 0. Routing recall shows the same split: prompt +0.08 [+0.01, +0.17], tool −0.01.
2. **The evidence is consistent in direction but thin.** Every skip falls on 5 of the 23
   SEC-必要 rows: 3 (Boeing's recent problems), 14 (Costco membership-fee timing),
   26 (NVDA/LLY/COST expectations), 10 and 7. On all 5 the prompt main effect is negative
   and it is positive on none. With n = 5 discordant rows, though, the exact sign test can
   reach only p = 0.0625. The bootstrap CI excludes 0; the sign test does not reach 0.05.
   Read it as "a consistent direction on the few rows where skipping happens", not
   "established for this question type". The skipped runs all answered from Tavily news
   (plus Finnhub on row 26). These are "what's happening lately" questions where news
   looks sufficient, and the canonical prompt never says 10-Ks are the primary source.
3. **No skip hit the budget in any cell.** As in the tool-routing analysis, skipping is
   a choice, not starvation. Caveat: row 26's skips used 9 of the 10 calls, so the
   budget may still shape that row.
4. **SEC tokens and cost come from the tool.** Search cut SEC evidence by ~27k tokens
   per question under either prompt, and the prompt moved it by ≈ 2k. Cost follows
   tokens: tool main effect −$0.0066 per run, prompt −$0.0021.
5. **Latency needs both: an interaction.** Under the canonical prompt, search did not
   change E2E (+0.1 s) or tool-call count (−0.0). Under the reader prompt it cut 7.3 s and
   1.5 calls. Per-run call counts show the mechanism (an observed pattern, not separately
   tested). C still calls `sec_filing_list_sections` first in most runs (0.97 per run,
   following the canonical prompt's SEC note) and then searches, so it keeps the extra
   round trip. B, following the reader prompt's "pinpoint → search" rule, almost never
   lists sections (0.03 per run). The bundle's speed-up in the 2026-10-22 report is
   therefore not a property of RAG retrieval alone.
6. **The reader prompt's mention of a missing tool did not cause hallucinated calls.**
   D never called `sec_filing_search` (0 unknown-tool calls in 90 runs). With search
   unavailable, it read whole sections (G in 81 runs), and its SEC token load is close
   to A's (37.5k vs 39.4k).
7. **A and B replicate the 2026-10-22 run.** SEC skips 10/69 vs 9/69 (A) and 0/69 vs 0/69
   (B); recall 0.89 vs 0.86 (A) and 0.95 vs 0.93 (B); B's SEC path mix is identical
   (S×82, S+G×3, ∅×5).
8. **Execution health does not separate the cells** (0.89–0.93, overlapping CIs). D has
   the most hard tool errors per run (0.20 vs 0.12). This was not investigated further.

## 4. Deviations during execution

1. **Braintrust plan limit.** At about 11:19 UTC the Braintrust organization hit its
   monthly log-bytes limit. Log uploads for the last ~55 runs (from row 26 or 27 onward
   in each repetition) were rejected, so those runs are missing from or incomplete in their
   Braintrust experiments. The agent runs themselves were unaffected: every run's full
   record is in `raw.tar.gz`, and all metrics come from those records.
2. **Analysis fix after the run.** The first analysis pass kept row 4 (a full coverage
   gap) in routing recall and unnecessary-call rate. It was corrected to match the
   tool-selection module, and the sign test was added; run code was unchanged.
3. **Smoke run** (rows 13 and 19 × 4 cells, one repetition, $0.010 per run on average,
   all health 1.0) preceded the batch and is excluded.

## 5. Claim boundary

- **One model.** GPT-5.6 Luna at reasoning effort medium only. The tool-routing analysis
  found Gemini skips 10-Ks more often, and whether the prompt effect transfers is not
  measured here.
- **Process and routing metrics only.** There is no answer-quality grading. "Did not skip
  the 10-K" means a SEC tool was called, not that the evidence was used well or the answer
  improved.
- **Labels by one annotator, the author.** Routing recall, unnecessary-call rate and
  SEC-skip depend on the 必要 / 擇一必要 / 可接受 / 不必要 labels (rules R1–R6), set
  without a second rater or agreement measure.
- **Live data, not replayable.** News, quotes and the latest 10-Ks are fetched live; all
  four cells ran in one ~1-hour window so they saw the same data, but a re-run is a new
  sample.
- **The prompt factor is the whole reader prompt.** It changes SEC framing and routing
  rules, but also language, grounding and citation rules. The experiment shows that the
  reader prompt causes fewer skips, not which sentence does. "Primary evidence source"
  framing is a plausible candidate, not a tested one.
- **D's prompt references a tool D lacks.** It is kept verbatim by design. It produced no
  unknown-tool calls, but the instruction may still shape D's behaviour in ways a
  search-free rewrite would not.
- **Small, rare-event effect.** The SEC-skip contrast rests on 5 of 23 rows (sign test
  p = 0.06). The tables carry 8 effects × 8 metrics with no multiple-comparison
  correction. The headline claims are the pre-stated ones (prompt vs tool for recall,
  SEC skip, SEC tokens, E2E, cost); the rest is descriptive.
- **Split not applied.** All 30 rows ran (as in the two previous experiments); these rows
  are not a holdout.
