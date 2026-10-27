# Model × Reasoning Benchmark — 2×2 on the zh diagnostic set (30 rows × 3 runs)

> **One-line takeaway:** Across 30 questions × 3 runs per cell, **raising reasoning strength made both model families slower** (Luna +11.5 s, Gemini +17.1 s per run; 95% CIs exclude 0) **with no detectable gain in execution health**. **Gemini 3.6 Flash was faster than GPT-5.6 Luna at both tiers** (−11.7 s and −6.0 s), and used fewer tool calls and a third of the input tokens. At the medium tier it still cost more per run (+$0.014), mostly because of list price; at the low tier the cost difference is not distinguishable from zero. None of the 360 runs failed because of the model: every health-0 run traces to data-coverage limits (20-F filers, a Finnhub 403, a 10-K without Item 7) or the 10-call tool budget.

This is the reference report: design, controlled variables, results with
uncertainty, deviations, and the claim boundary. For what else is in this
directory, see [`README.md`](README.md).

## Reproduce

| | |
|---|---|
| Git tag | `experiment/2026-10-22-model-reasoning-benchmark` |
| Branch / Linear | `feat/model-reasoning-benchmark` · DEV-206 |
| Code that ran | commit `3cfd78c`, later rebased onto main as `294fc84` (identical tree; the rebase only swapped the base from the edgartools fix branch to its squash-merge `c77277b`) |
| Run windows | Batch 1: 2026-10-22 00:59–01:38 UTC (257 runs). OpenAI API credits ran out at 01:23:47 UTC. Batch 2 resumed the 103 failed Luna runs at 04:14–04:35 UTC, after the credit top-up (see [§4](#4-deviations-during-execution)). |
| Config dump | `python -m backend.evals.experiments.model_reasoning_benchmark.run dump --out-dir <dir>` → [`config_dump/`](config_dump/) |
| Runs | `python -m backend.evals.experiments.model_reasoning_benchmark.run run --out-dir <dir> --label 20261022-all30 --rows all --rep K` for K = 1, 2, 3, one process each (needs Qdrant on `:6333` and `backend/.env` with OpenAI, Gemini, Tavily, Finnhub, Braintrust keys + `EDGAR_IDENTITY`) |
| Metrics | `python -m backend.evals.experiments.model_reasoning_benchmark.analyze --raw-dir <dir>/raw --out-dir <archive>` |
| Braintrust | one experiment per (arm, repetition); see [`braintrust_links.json`](braintrust_links.json) |
| Total API cost | ≈ US$7.17 model spend for 360 runs (luna_none $1.28, luna_medium $1.45, gemini_minimal $1.71, gemini_medium $2.73), plus ~895 Tavily credits shared with the concurrent RAG ablation and the smoke runs (list prices, see [Cost model](#cost-model)) |

**Live data cannot be replayed.** Tavily news, Finnhub quotes and "latest 10-K"
resolution depend on run time. A re-run is a new sample; [`raw/`](raw/) keeps what
these runs actually saw.

## 1. Question

How much do model family (OpenAI `gpt-5.6-luna` vs Google `gemini-3.6-flash`) and
reasoning strength (low vs medium) change an agent's execution health, tool use,
latency, tokens and cost, when the prompt, the tools and the tool budget are held
fixed?

This round also serves as the **pre-revision baseline** for the shared-prompt work
(DEV-206). It replaces the 2026-10-21 dev-split round, which ran before the
edgartools upgrade (DEV-219) and lost all SEC access for any 10-K not already in
the local cache.

## 2. Design

### Arms (the 2×2)

| Arm | Model | Reasoning control | Built model kwargs |
|---|---|---|---|
| `luna_none` | `openai:gpt-5.6-luna` | `reasoning.effort = none` | Responses API, `temperature=0.0` |
| `luna_medium` | `openai:gpt-5.6-luna` | `reasoning.effort = medium` | Responses API, temperature dropped by langchain-openai (provider default) |
| `gemini_minimal` | `google_genai:gemini-3.6-flash` | `thinking_level = minimal` (the model's floor; Gemini can't fully disable thinking) | `temperature=0.0`, `include_thoughts=True` |
| `gemini_medium` | `google_genai:gemini-3.6-flash` | `thinking_level = medium` | `temperature=0.0`, `include_thoughts=True` |

Held fixed for every arm: the single canonical prompt (identical rendered sha256), the
same five tools with identical contracts (`finnhub_stock_quote`,
`finnhub_company_basic_financials`, `tavily_financial_search`,
`sec_filing_list_sections`, `sec_filing_get_section`), and `max_tool_calls_per_run: 10`.
`run.py dump` resolves each arm the way the orchestrator builds it and fails unless the
arms differ only in identity and model settings: **PASS**
([`config_dump/config_alignment.json`](config_dump/config_alignment.json)).

### Dataset and rows

- `backend/evals/scenarios/baseline_behavior_diagnostic_zh/dataset.csv`, all **30**
  Chinese questions (version `2026-09-03`).
- **The dev/holdout/reserve split was deliberately not applied** (user decision for
  this round). `split.json` is still `proposed` and was not modified, but its holdout
  and reserve rows have now been run and inspected. If DEV-200 freezes that split
  later, those rows are no longer an unseen holdout for anyone who has read this
  report.
- Expected best source across the 30 rows: mixed 12, SEC 9, Finnhub 5, Tavily 4.

### Run protocol

- **3 repetitions** of every (row, arm) cell, so **360 runs**. One worker process per
  repetition; the three workers ran in parallel.
- **Row-major within each worker**: a row runs through all 4 arms before the next row.
  Arm order rotates by row and repetition (`(row + rep) mod 4`), so no arm always runs
  first or last.
- **Pre-warm**: each worker fetches every dataset ticker's latest 10-K once (24 10-K
  filers; TSMC/ASML file 20-Fs and Airbus is not an SEC registrant) before its first
  timed run, so EDGAR download cost doesn't land inside whichever arm happens to run
  first. All 24 succeeded on the upgraded edgartools.
- Checkpointer off, a unique session per run, 600 s timeout per run.
- Concurrency: the RAG-ablation experiment (DEV-220, 3 more workers) ran at the same
  time, so up to 6 agent runs were in flight. That inflates absolute latency
  ([§6](#6-claim-boundary)).

### Metrics (all from code; no LLM judge)

Execution health (existing scorer: 1.0 iff the stream finished normally and no tool
call errored), tool calls per tool, hard tool errors vs budget-blocked calls, TTFT
(first visible event) and E2E from `_astream_collect`, input/cached/output/reasoning
tokens per model call (LangChain callback, cross-checked against the stream's `Finish`
usage), estimated cost, Simplified-Chinese drift (`response_no_simplified_chars`), and
`[N]` citation integrity.

**Aggregation.** Each (row, arm) cell is first averaged over its 3 repetitions. Arms
are then compared across the 30 rows. 95% CIs come from a **row-level (cluster)
bootstrap**: rows are resampled with replacement, keeping each row's repetitions
together, with 2,000 resamples and a fixed seed. Contrasts are paired by row.

## 3. Results

### Arm summary (per-row means over repetitions; 95% CI = row-level bootstrap)

| Arm | Rows × reps | Task errors | Health mean [95% CI] | Median E2E s [95% CI] | Median TTFT s | Median tool calls | Median LLM calls | Median input tok | Median output tok | Median reasoning tok | Mean cost/run USD [95% CI] | Total cost USD | Hard tool errors/run | Runs at tool budget | Simplified-drift runs |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| luna_none | 30 × 3 | 0 | 0.91 [0.81, 0.99] | 27.3 [24.0, 31.4] | 2.2 | 6.0 | 3.0 | 38553 | 2022 | 0 | 0.0142 [0.0067, 0.0253] | 1.28 | 0.12 | 6 | 0 |
| luna_medium | 30 × 3 | 0 | 0.90 [0.79, 0.99] | 38.0 [35.1, 42.3] | 2.5 | 7.2 | 3.0 | 43749 | 2720 | 494 | 0.0161 [0.0091, 0.0260] | 1.45 | 0.14 | 9 | 1 |
| gemini_minimal | 30 × 3 | 0 | 0.97 [0.90, 1.00] | 15.1 [13.2, 16.8] | 1.4 | 3.7 | 2.8 | 12717 | 1421 | 0 | 0.0190 [0.0157, 0.0228] | 1.71 | 0.07 | 0 | 0 |
| gemini_medium | 30 × 3 | 0 | 0.99 [0.96, 1.00] | 31.5 [29.1, 33.8] | 2.0 | 4.5 | 3.0 | 15162 | 4345 | 2854 | 0.0303 [0.0275, 0.0336] | 2.73 | 0 | 2 | 1 |

### Run-to-run variability (same row, same arm, different repetition)

| Arm | Rows where health is identical across reps | Median within-row E2E CV | Median within-row SD of tool calls |
|---|---|---|---|
| luna_none | 93% | 0.14 | 0.58 |
| luna_medium | 93% | 0.13 | 0.58 |
| gemini_minimal | 100% | 0.14 | 0.58 |
| gemini_medium | 97% | 0.10 | 0.58 |

### Paired contrasts (mean per-row difference, treatment − control, 95% CI)

| Contrast | Treatment − control | Δ health | Δ E2E s | Δ cost/run USD | Δ tool calls |
|---|---|---|---|---|---|
| reasoning, Luna | luna_medium − luna_none | -0.01 [-0.07, +0.04] | +11.5 [+8.8, +14.2] | +0.0019 [-0.0002, +0.0037] | +0.5 [+0.0, +1.0] |
| reasoning, Gemini | gemini_medium − gemini_minimal | +0.02 [-0.03, +0.10] | +17.1 [+15.3, +19.4] | +0.0113 [+0.0077, +0.0152] | +0.9 [+0.5, +1.5] |
| family, low tier | gemini_minimal − luna_none | +0.06 [-0.03, +0.17] | -11.7 [-14.6, -8.9] | +0.0048 [-0.0071, +0.0132] | -2.2 [-2.8, -1.6] |
| family, medium tier | gemini_medium − luna_medium | +0.09 [-0.00, +0.20] | -6.0 [-9.2, -2.8] | +0.0142 [+0.0054, +0.0206] | -1.8 [-2.4, -1.1] |

### Health mean by expected best source

| Source | luna_none | luna_medium | gemini_minimal | gemini_medium |
|---|---|---|---|---|
| Finnhub | 1.00 | 0.93 | 1.00 | 1.00 |
| SEC | 1.00 | 1.00 | 1.00 | 1.00 |
| Tavily | 0.67 | 0.50 | 0.75 | 1.00 |
| mixed | 0.89 | 0.94 | 1.00 | 0.97 |

### What the numbers say

1. **Reasoning strength costs latency and buys nothing measurable here.** Within each family, the medium tier was slower (Luna +11.5 s [+8.8, +14.2]; Gemini +17.1 s [+15.3, +19.4]) and made slightly more tool calls. Health was unchanged (−0.01 [−0.07, +0.04]; +0.02 [−0.03, +0.10]). Luna's medium tier spent few reasoning tokens (median 494 per run), Gemini's spent ~2,850. Execution health is a process metric, though, so "no gain" means no gain in *completing without tool errors*. Answer quality was not measured.
2. **Gemini was faster at both tiers.** At the low tier it took −11.7 s [−14.6, −8.9] and 2.2 fewer tool calls; at the medium tier −6.0 s [−9.2, −2.8]. It also reached its first visible event sooner (median TTFT 1.4–2.0 s vs 2.2–2.5 s) and read far less context (median input 13–15k vs 39–44k tokens per run), largely because it made fewer `get_section` calls.
3. **Cost depends on more than list price.** At the medium tier Gemini cost more per run (+$0.0142 [+0.0054, +0.0206]). At the low tier the difference (+$0.0048 [−0.0071, +0.0132]) is indistinguishable from zero: Luna's habit of reading whole 10-K sections pushed 11 of its calls over the 272K-token long-context threshold (JPM rows 8 and 27), where OpenAI doubles the input price.
4. **Health differences are coverage problems, not model quality.** Gemini's health is nominally higher (+0.06 and +0.09; both CIs reach 0). All 21 health-0 runs trace to: TSMC/ASML filing 20-Fs (no 10-K tool support), Finnhub 403 for non-US tickers (Airbus), INTC's 10-K having no Item 7, or a run blocked only by the 10-call budget (3 runs). An arm that *attempts* an uncovered source scores 0, so health partly measures tool-use ambition.
5. **Run-to-run variance is real but modest.** For the same row and arm, E2E varied by a median CV of 0.10–0.14 across the 3 repetitions. Health was identical across repetitions on 93–100% of rows. n = 1 per cell (the 2026-10-21 round) would have mistaken some of this noise for config effects.
6. **Language.** Only 2 of 360 responses tripped the Simplified-Chinese drift scorer (one each for luna_medium and gemini_medium). The known drift failure is rare under the current prompt.


## 4. Deviations during execution

1. **OpenAI credits ran out mid-run.** At 01:23:47 UTC the OpenAI organization hit zero API credit, and 103 Luna runs failed with `RuntimeError: Stream error: You have no credits remaining`. Gemini was unaffected. The failed records were moved aside (not deleted), the user topped up the credit, and the three workers were resumed. Workers skip runs that already have a raw record, so only the failed runs re-ran (04:14–04:35 UTC). **Consequence:** for those cells, Luna saw live news and quotes about three hours later than Gemini did on the same row. This breaks the row-major time alignment for part of the family contrast. Rows needing only SEC filings are unaffected; Tavily/Finnhub-dependent rows may be.
2. **Concurrency.** Three workers for this experiment and three for the RAG ablation ran in parallel, so up to 6 agent runs were in flight. All arms ran under the same load profile within a batch, but absolute latencies are higher than on an idle machine. Pre-warm under this contention took 15–58 s per filing, but it happens outside the timed runs.
3. **Cost model corrected after the run.** The first pass summed tokens per run and missed OpenAI's long-context rate (>272K input tokens per request: 2× input, 1.5× output). Cost is now computed per model call; `metrics.csv` has a `long_context_priced_calls` column. Cached input on such requests is conservatively charged at 2× as well.
4. **Rebased after running.** Runs executed from `3cfd78c`. The branch was later rebased onto main's squash-merge of the edgartools fix (`c77277b`) with an identical tree, and is now `294fc84` plus the cost-model fix `16cebc6`.
5. **Tavily** exceeded the free plan's 1,000 credits; pay-as-you-go (enabled by the user) covered the last 32. No Tavily errors occurred.
6. **Smoke run** (row 13 × 4 arms, label `smoke`) preceded the batch. Its runs are separate Braintrust experiments and are excluded from these results.


## 5. Cost model

List prices read on 2026-10-21 from the providers' own pages:

| Model | Input | Cached input | Output | Source |
|---|---|---|---|---|
| `gpt-5.6-luna` | $0.20 / 1M | $0.02 / 1M | $1.20 / 1M (reasoning billed as output) | https://developers.openai.com/api/docs/models/gpt-5.6-luna |
| `gemini-3.6-flash` | $0.75 / 1M | $0.075 / 1M | $3.75 / 1M (incl. thinking) | https://ai.google.dev/gemini-api/docs/pricing (paid tier, standard, valid through 2026-12-31) |

`cost = (input − cached) × in + cached × cached_in + output × out`. For both providers,
LangChain's `output_tokens` already includes reasoning/thinking tokens. Tool API costs
(Tavily, Finnhub) and SEC embedding are excluded.

## 6. Claim boundary

- **Process metrics, not answer quality.** Health, tool use, latency, tokens and cost say how each config *executes*, not whether its answers are right. "Reasoning buys nothing" holds only for these metrics.
- **30 questions, 3 runs each.** The CIs are row-level bootstrap intervals over a small, hand-built diagnostic set (Traditional Chinese, US equities). They describe this set, not financial questions in general. There was no multiple-comparison correction across the 4 contrasts × 4 metrics.
- **Split not applied.** All 30 rows were used, including the proposed holdout and reserve rows, so this is exploration, not a held-out evaluation. Prompt work that reads these results has seen every row.
- **Live, non-replayable inputs**, with a ~3-hour gap between Luna's resumed runs and Gemini's runs on the same rows ([§4](#4-deviations-during-execution)).
- **Luna's reasoning contrast is confounded with temperature.** langchain-openai drops `temperature` for `effort=medium` (provider default) but keeps 0.0 for `effort=none`. Gemini's pair is clean on this axis, but `minimal` is Gemini's reasoning floor, not "off".
- **Latency measured under 6-way concurrency** on one machine and network, including tool and network time.
- **Cost is an estimate** from list prices and LangChain usage metadata. Context-cache storage fees and tool API costs are excluded.
