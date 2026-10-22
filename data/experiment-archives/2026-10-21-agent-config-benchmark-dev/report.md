# Agent-Config Benchmark (dev split) — RAG bundle ablation + model × reasoning 2×2

> **One-line takeaway (directional, n=1 × 8 dev rows):** With the model held fixed
> (`gpt-5.6-luna`, effort `medium`), the RAG bundle (`sec_filing_search` + reader prompt)
> **always** chose chunk search over whole-section reading (8/8 rows) and, on the three
> rows where both arms read the same filing successfully, put **2.3–13× fewer SEC tokens**
> into context and finished **~35–50% faster**. It also pulled SEC evidence into questions
> that didn't need it (both Finnhub-only "sanity" rows), so the bundle changes tool-use
> *policy*, not just retrieval. **Cheaper did not mean better**: in a blind pairwise
> review (one rater), the no-RAG arm was preferred on **5 of 8** rows, including the
> row with the biggest token saving (row 6, 13×). That is 5–3 with no ties, sign test
> p = 0.73, so it can't say the RAG answers were *worse*, only that its efficiency gain
> came with no visible quality gain. In the 2×2, every execution-health failure traced back to
> broken tools or data coverage (edgartools on META/V/MA 10-Ks, no data for Airbus), not to
> the model; the clear differences were in latency (Gemini minimal fastest) and cost (Luna
> 2.3–5.6× cheaper).

This is the reference report — setup, tables, decisions, and reproduce instructions. For
what else is in this directory, see [`README.md`](README.md).

## Reproduce

| | |
|---|---|
| Git tag | `experiment/2026-10-21-agent-config-benchmark-dev` (runs executed from commit `60cdb5d`; the tag adds only the analysis/report code and this archive) |
| Branch / Linear | `feat/dev-206-config-selectable-diagnostic-task` · DEV-206 (parent DEV-199) |
| Run window | 2026-10-21 15:57:00 → 16:19:08 UTC (23:57 → 00:19 Asia/Taipei), one process, sequential |
| Config dump | `python -m backend.evals.experiments.agent_config_benchmark.run dump --out-dir <dir>` → [`config_dump/`](config_dump/) |
| Runs | `python -m backend.evals.experiments.agent_config_benchmark.run run --out-dir <dir> --label 20261021-dev` (needs Qdrant on `:6333`, `backend/.env` with OpenAI, Gemini, Tavily, Finnhub, Braintrust keys + `EDGAR_IDENTITY`) |
| Metrics | `python -m backend.evals.experiments.agent_config_benchmark.analyze --raw-dir <dir>/raw --out-dir <archive>` |
| Review sheet | `python -m backend.evals.experiments.agent_config_benchmark.review_sheet --raw-dir <archive>/raw --out-dir <archive>/blind_review` |
| Braintrust | one experiment per arm, links in [`braintrust_links.json`](braintrust_links.json) and [§9](#9-braintrust-experiments) |
| Total API cost | ≈ US$0.61 for the 40 runs (list prices, [§6](#6-cost-model)) |

**Live data cannot be replayed.** Tavily news, Finnhub quotes, and the "latest 10-K"
resolution all depend on run time. Re-running produces new evidence, not a reproduction —
the tag reproduces the *procedure*; [`raw/`](raw/) preserves what this run actually saw.

## 1. Questions

| # | Question | Variable | Fixed |
|---|---|---|---|
| E1 | Is RAG over 10-Ks (`sec_filing_search`) better than finding the right section and reading it whole (`sec_filing_get_section`)? Tests ADR-0010's "RAG over long-context reading" assumption. | RAG capability bundle = tool set + prompt | model, reasoning effort, temperature setting, tool budget, tool contracts |
| E2 | How much do model family and reasoning strength move execution health, tool errors, latency, tokens, and cost? | model family × reasoning tier | prompt (single canonical), tools, tool budget |

## 2. Design

### Arms

| Arm | Config dir | Model | Reasoning | Tools | Prompt | In |
|---|---|---|---|---|---|---|
| `luna_medium` (**E1 Arm A**) | `benchmark/configs/luna_medium` | `openai:gpt-5.6-luna` | effort `medium` | 5 baseline tools | canonical (= `profiles/baseline/system_prompt.md`) | E1 + E2 |
| `reader_luna_medium` (**E1 Arm B**) | `benchmark/ablations/reader_luna_medium` | `openai:gpt-5.6-luna` | effort `medium` | 5 baseline + `sec_filing_search` | `profiles/reader/system_prompt.md` (referenced, not copied) | E1 |
| `luna_none` | `benchmark/configs/luna_none` | `openai:gpt-5.6-luna` | effort `none` | 5 baseline | canonical | E2 |
| `gemini_minimal` | `benchmark/configs/gemini_minimal` | `google_genai:gemini-3.6-flash` | `thinking_level=minimal` | 5 baseline | canonical | E2 |
| `gemini_medium` | `benchmark/configs/gemini_medium` | `google_genai:gemini-3.6-flash` | `thinking_level=medium` | 5 baseline | canonical | E2 |

All arms: `max_tool_calls_per_run: 10`. The 5 baseline tools are `finnhub_stock_quote`,
`finnhub_company_basic_financials`, `tavily_financial_search`, `sec_filing_list_sections`,
`sec_filing_get_section`. 40 runs total = 8 (E1 Arm B) + 4 × 8 (E2); `luna_medium` is
shared by both experiments and was run once.

**E1 measures a bundle, not a tool.** Arm B changes the tool set *and* the prompt together,
deliberately: the reader prompt's citation rules are written for `sec_filing_search`
chunk ids, so giving Arm A's prompt the search tool (or Arm B's prompt no search tool)
would test a configuration nobody would ship. The cost of this choice is that the reader
prompt also differs in ways unrelated to retrieval (stronger language policy, grounding
rules, `[N]` citation format, "SEC filings are the primary evidence source" framing).
Any A/B difference may come from either half of the bundle.

### Config alignment check (run before any experiment run)

`run.py dump` resolves each arm the way the orchestrator does (`load_from_dir` + the chat
model actually built by `_init_model`), hashes every tool's description and args schema,
and hashes the raw and rendered prompt. It then diffs Arm A against Arm B and fails on any
difference outside identity, tools, and prompt. Result: **PASS** ([`config_dump/e1_config_diff.json`](config_dump/e1_config_diff.json)).

| Field | Arm A `luna_medium` | Arm B `reader_luna_medium` | Same? |
|---|---|---|---|
| Model | `openai:gpt-5.6-luna` | `openai:gpt-5.6-luna` | ✓ |
| Config `reasoning` / `reasoning_effort` | `on` / `medium` | `on` / `medium` | ✓ |
| Built model kwargs | `reasoning={effort: medium, summary: auto}`, Responses API | same | ✓ |
| Config temperature / built temperature | 0.0 / `None` (see note) | 0.0 / `None` | ✓ |
| `max_tool_calls_per_run` | 10 | 10 | ✓ |
| Tools | 5 baseline | 5 baseline + `sec_filing_search` | ✗ (intended) |
| Contracts of the 5 shared tools (description + args hashes) | — | — | ✓ identical |
| Prompt raw sha256 (chars) | `83bf45ca…` (4,516) | `33ea9c8d…` (8,970) | ✗ (intended) |

Note on temperature: the YAMLs say `temperature: 0.0`, but langchain-openai drops
`temperature` for a reasoning-enabled GPT-5.x model, so both E1 arms (and `luna_medium` in
E2) actually sample at the provider default. `luna_none` keeps 0.0; both Gemini arms keep
0.0. This is identical across the E1 pair, but **it is a confound inside E2's Luna pair**
(see [§8](#8-claim-boundary)).

The four E2 configs share one rendered prompt (sha256 `f11cead6…`): the canonical-prompt
guarantee held.

### Dataset and split

- `backend/evals/scenarios/baseline_behavior_diagnostic_zh/dataset.csv` (30 Chinese questions), version `2026-09-03`.
- **Dev split only**: rows `3, 6, 9, 13, 17, 20, 24, 29` from `benchmark/split.json` (status `proposed`), selected through `apply_split`'s dev-only default. Holdout and reserve rows were never read; `split.json` was not modified.
- Expected best source on these rows: SEC 2 (6, 13), mixed 4 (3, 9, 17, 29), Finnhub 2 (20, 24). Rows 20 and 24 are the **sanity rows**: they need no 10-K, so A ≈ B was expected.

| Row | Gist (zh original in the dataset) | Expected source |
|---|---|---|
| 3 | Boeing's current problems: regulation, deliveries, or demand? | mixed |
| 6 | J&J's biggest litigation risk: visible costs vs. what may still grow | SEC |
| 9 | Under stricter EU/US platform regulation, Apple vs. Meta — whose business takes the bigger direct hit? | mixed |
| 13 | Do Visa's and Mastercard's official disclosures support "regulation will squeeze card-network profitability"? | SEC |
| 17 | Is Amazon's ads business a high-quality profit engine now? | mixed |
| 20 | Is Coca-Cola still a stable dividend payer? | Finnhub |
| 24 | Tesla vs. NVIDIA: which looks more priced-for-perfection? | Finnhub |
| 29 | Boeing vs. Airbus: who weathers the current supply-chain/regulatory turbulence better? | mixed |

### Run protocol

- **Row-major**: each row runs through all 5 arms before the next row starts, so live news and quotes are as close in time as possible across arms (one row's 5 runs span ~2–4 minutes).
- **Within-row order**: the E1 pair always runs back-to-back (smallest live-data gap between A and B) and alternates which arm goes first (A first on even-indexed rows, B first on odd); the other three E2 arms rotate. The order is recorded per run (`slot_in_row` in `metrics.csv`, `row_order` in `raw/`).
- **n = 1** per (row, arm). Each run gets a per-arm session id; checkpointer off, so no cross-run memory.
- **Pre-warm** (in the same process, before the first timed run): for each of the 10 SEC-filing tickers the dev rows mention, call `sec_filing_list_sections` and `sec_filing_search` once. Otherwise the first arm to touch a ticker pays the EDGAR download and JIT embedding cost inside its latency (observed in the smoke test: ~15 s per cold search), and which arm that is would depend on run order. Pre-warm results: [`prewarm.json`](prewarm.json).
- **Timeout** 600 s per run (not hit).
- **Smoke tests**: row 6 × all 5 arms, run before the batch under labels `smoke`/`smoke2` (separate Braintrust experiments). Not part of the results.

### Metrics (all from code — no LLM judge)

| Metric | Source |
|---|---|
| Execution health | existing `execution_health` scorer: 1.0 iff the stream finished normally **and** no tool call errored |
| Tool calls, per-tool counts, SEC path (search only / get_section only / both / neither — attempted calls) | `OrchestratorResult.tool_outputs` |
| Hard tool errors vs. budget-blocked calls | tool outputs with an error, split by the budget middleware's marker text |
| SEC evidence tokens | cl100k token count of `sec_filing_get_section` + `sec_filing_search` tool results (what entered context) |
| TTFT (first visible event: reasoning, tool call, or text), E2E | timestamps recorded in `_astream_collect` (new `timing` field) |
| Input / cached / output / reasoning tokens, LLM calls | per-model-call `usage_metadata` via a LangChain callback; cross-checked against the stream's `Finish` usage (equal on all 40 runs) |
| Estimated cost | tokens × list price ([§6](#6-cost-model)) |
| Simplified-Chinese drift | `language_policy`'s `response_no_simplified_chars` scorer, applied as-is |
| Citation integrity | deterministic: set of inline `[N]` markers == set of bottom `[N]:` definitions (blank when an answer uses neither) |

## 3. E1 results — RAG bundle (B) vs. whole-section reading (A)

Cells are `A / B`. Generated by `analyze.py` ([`tables.md`](tables.md)); per-run detail in [`metrics.csv`](metrics.csv).

| Row | Expected source | SEC path | Tool calls | search calls | get_section calls | Hard tool errors | SEC evidence tokens | Input tokens | Output tokens | TTFT s | E2E s | Cost USD | Health | No-simplified | [N] bijective |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 3 | mixed | neither / search_only | 6 / 5 | 0 / 1 | 0 / 0 | 0 / 0 | 0 / 4962 | 16939 / 25420 | 2006 / 1475 | 3.0 / 1.9 | 38.4 / 26.1 | 0.0040 / 0.0040 | 1.0 / 1.0 | 1.0 / 1.0 | ✓ / ✓ |
| 6 | SEC | get_section_only / search_only | 6 / 2 | 0 / 1 | 4 / 0 | 0 / 0 | 70998 / 5341 | 79330 / 12228 | 3313 / 2602 | 4.7 / 2.1 | 48.0 / 30.2 | 0.0186 / 0.0045 | 1.0 / 1.0 | 1.0 / 1.0 | ✓ / ✓ |
| 9 | mixed | get_section_only / search_only | 10 / 7 | 0 / 3 | 2 / 0 | 2 / 2 | 16331 / 5358 | 58831 / 28246 | 3819 / 2906 | 3.9 / 2.4 | 64.6 / 41.9 | 0.0102 / 0.0061 | 0.0 / 0.0 | 1.0 / 1.0 | ✓ / ✓ |
| 13 | SEC | neither / search_only | 11 / 12 | 0 / 2 | 0 / 0 | 5 / 4 | 0 / 28 | 21545 / 43245 | 2308 / 2830 | 2.8 / 1.8 | 49.3 / 47.6 | 0.0046 / 0.0063 | 0.0 / 0.0 | 1.0 / 1.0 | ✓ / ✓ |
| 17 | mixed | get_section_only / search_only | 7 / 4 | 0 / 4 | 3 / 0 | 0 / 0 | 41103 / 17582 | 52916 / 41350 | 4527 / 3143 | 4.0 / 3.4 | 64.7 / 33.0 | 0.0145 / 0.0079 | 1.0 / 1.0 | 1.0 / 1.0 | – / ✓ |
| 20 | Finnhub | get_section_only / search_only | 5 / 3 | 0 / 1 | 2 / 0 | 0 / 0 | 52695 / 4651 | 61093 / 11164 | 1830 / 1220 | 2.6 / 1.7 | 27.9 / 13.7 | 0.0132 / 0.0026 | 1.0 / 1.0 | 1.0 / 1.0 | ✓ / ✓ |
| 24 | Finnhub | neither / search_only | 6 / 8 | 0 / 2 | 0 / 0 | 0 / 0 | 0 / 9772 | 7473 / 27256 | 2333 / 2310 | 3.7 / 4.7 | 36.1 / 35.0 | 0.0037 / 0.0059 | 1.0 / 1.0 | 1.0 / 1.0 | – / ✓ |
| 29 | mixed | neither / search_only | 8 / 9 | 0 / 2 | 0 / 0 | 0 / 2 | 0 / 4426 | 13740 / 39261 | 3238 / 3393 | 3.1 / 2.3 | 52.1 / 51.6 | 0.0051 / 0.0070 | 1.0 / 0.0 | 1.0 / 1.0 | ✓ / ✓ |

| Aggregate (8 pairs) | A (no RAG) | B (RAG bundle) |
|---|---|---|
| Median SEC evidence tokens | 8,166 | 5,152 |
| Median input tokens | 37,231 | 27,751 |
| Median output tokens | 2,786 | 2,716 |
| Median tool calls | 6.5 | 6.0 |
| Median TTFT s | 3.4 | 2.2 |
| Median E2E s | 48.7 | 34.0 |
| Hard tool errors (sum) | 7 | 8 |
| Total cost USD (8 runs) | 0.0739 | 0.0443 |
| Runs with health 1.0 | 6 | 5 |
| SEC path | get_section 4, neither 4 | **search_only 8** |

### What the pairs show

**1. Which path Arm B chose: chunk search, every time.** B called `sec_filing_search` on
all 8 rows and never called `sec_filing_get_section` (on row 13 it fell back to
`list_sections` after search failed, as its prompt instructs, then ran out of budget). So
in practice E1 compares *chunk retrieval* against *whole-section reading or no SEC at all*.
That is itself a finding: given both tools, this model plus the reader prompt treated
search as the default, even on questions that arguably fit the prompt's "synoptic →
`get_section`" route (e.g. row 6, characterizing J&J's overall litigation risk).

**2. When both arms read the same filing successfully, B used far less context and was faster.**
These are the clean comparisons: rows 6, 17, and 20 (and row 9 partially: AAPL succeeded,
META failed in both arms).

| Row | SEC tokens A → B | Ratio | Input tokens A → B | E2E s A → B | Cost A → B |
|---|---|---|---|---|---|
| 6 | 70,998 → 5,341 | 13.3× | 79,330 → 12,228 | 48.0 → 30.2 | $0.0186 → $0.0045 |
| 17 | 41,103 → 17,582 | 2.3× | 52,916 → 41,350 | 64.7 → 33.0 | $0.0145 → $0.0079 |
| 20 | 52,695 → 4,651 | 11.3× | 61,093 → 11,164 | 27.9 → 13.7 | $0.0132 → $0.0026 |
| 9 (partial) | 16,331 → 5,358 | 3.0× | 58,831 → 28,246 | 64.6 → 41.9 | $0.0102 → $0.0061 |

A whole 10-K section is 16k–71k tokens per run here. None of these runs got near the
272K-token long-context price tier, but per call that cost is linear and it adds latency.

**3. B also used SEC where A (and the question) did not need it, at a cost.** On rows 3,
24, and 29, A answered without SEC; B added 1–2 searches and +8k to +26k input tokens, so
B cost the same or more there. The reader prompt frames 10-K filings as the "primary
evidence source", and B behaved accordingly.

**4. The sanity rows did not come out A ≈ B, and that is informative.** The expectation
was that rows 20 and 24 (Finnhub-only) would look alike. They didn't:

- Row 20 (Coca-Cola dividends): A read **two whole sections** (52.7k tokens) for a dividend question; B ran one search (4.7k). B was ~2× faster and ~5× cheaper.
- Row 24 (TSLA vs NVDA valuation): A used no SEC; B ran 2 searches, +19.8k input tokens.

In both rows the difference comes from **policy** (whether and how to consult a filing),
not from retrieval quality. That fits the bundle confound named in §2: on questions that
don't need a 10-K, the prompt half of the bundle is driving behavior. Do not read the
SEC-row differences as pure retrieval effects.

**5. Execution health doesn't separate the arms.** A got 6/8, B 5/8. Every failure is a
tool or data-coverage defect ([§5](#5-defects-found)): rows 9 and 13 (META/V/MA 10-Ks
unreadable on **both** SEC paths) hit both arms, and on row 29 B *attempted*
`sec_filing_search` and Finnhub on Airbus (`AIR.PA` — not an SEC filer, and Finnhub's
plan returns 403), while A happened not to call a failing endpoint. The health score
penalizes trying a tool that is down, so it can't reveal whether an answer is good.

**6. Language and citations.** No Simplified-Chinese drift in either arm (0/16).
Whenever an answer used `[N]` markers, every marker had a definition and vice versa
(A: 6/6, B: 8/8).

**7. Blind preference: A 5, B 3 (see [§10](#10-blind-pairwise-review)).** Fewer tokens can
mean "precise evidence" or "missed context" — a whole Item 1A has the full litigation
picture, and eight chunks may not. The blind review leans toward the second reading, but
only weakly. On the clean SEC pairs, A was preferred on rows 6 and 20 and B on row 17. So
the largest context cut (row 6, 71k → 5k SEC tokens) is also a row where the
whole-section answer won. Where B added SEC that A skipped (rows 3, 24), A was preferred
both times. B won on row 29 despite execution health 0, which shows directly that health
is not a quality proxy. With 8 pairs and one rater, this is a hypothesis for the next
round, not a result: *chunk retrieval saves context and time but may drop synthesis
context that synoptic questions need.*

## 4. E2 results — model family × reasoning tier

| Arm | Runs | Health mean | Task errors | Hard tool errors | Runs at 10-call budget | Median tool calls | Median LLM calls | Median TTFT s | Median E2E s | Median input tok | Median output tok | Median reasoning tok | Total cost USD (8 runs) | Simplified-drift runs |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| luna_none | 8 | 0.62 | 0 | 7 | 1 | 6.0 | 2.5 | 4.7 | 28.8 | 14,564 | 1,818 | 0 | 0.0482 | 0 |
| luna_medium | 8 | 0.75 | 0 | 7 | 2 | 6.5 | 3.0 | 3.4 | 48.7 | 37,230 | 2,786 | 568 | 0.0739 | 0 |
| gemini_minimal | 8 | 0.75 | 0 | 5 | 0 | 4.0 | 3.0 | 1.6 | 16.6 | 17,882 | 1,436 | 0 | 0.1692 | 0 |
| gemini_medium | 8 | 0.88 | 0 | 4 | 1 | 6.5 | 4.0 | 2.0 | 33.9 | 18,494 | 4,397 | 2,568 | 0.2706 | 0 |

(Total over the 8 runs: luna_none 191k input / 15k output tokens; luna_medium 312k / 23k;
gemini_minimal 333k / 11k; gemini_medium 226k / 35k. Max single-run cost: $0.060,
gemini_medium row 17.)

- **Health**: every health-0 run is a row-9/13/29 tool or data-coverage failure (§5). Which arm scored lower mostly reflects *whether it called a broken tool* (e.g. gemini_medium skipped SEC on row 9 and kept 1.0; luna_none tried Finnhub on `AIR.PA` on row 29 and dropped to 0). **No model-attributable failure** appeared: 0 task errors, 0 unfinished streams.
- **Latency**: Gemini was faster at both tiers: gemini_minimal had the lowest median E2E (16.6 s) and TTFT (1.6 s). Raising reasoning roughly doubled E2E within each family (Luna 28.8 → 48.7 s, Gemini 16.6 → 33.9 s).
- **Reasoning tokens**: Luna at `medium` spent few reasoning tokens (median 568, total 4.7k); Gemini at `medium` spent ~4.5× more (median 2,568, total 21.5k). Both "low" tiers reported 0 reasoning tokens. Gemini's `minimal` is the model's floor, not a true "off".
- **Cost**: Luna was 2.3–5.6× cheaper per batch ($0.048 / $0.074 vs. $0.169 / $0.271) at similar or lower token counts, because list prices differ (input $0.20 vs $0.75, output $1.20 vs $3.75 per 1M). Gemini's high cached-input share (gemini_minimal: 181k of 333k input tokens cached) softens this only a little.
- **Tool use**: gemini_minimal made the fewest tool calls (median 4); `luna_medium` was the only E2 arm to hit the 10-call budget twice (rows 9 and 13, both retrying failing SEC calls).
- **Language**: 0 Simplified-Chinese drift in all 32 E2 runs. The known drift failure did not reproduce in this batch; with n=1 that is weak evidence it is gone.
- **Pre-revision baseline (DEV-206 AC #1)**: this table is the current canonical prompt's dev × 4 configs round, with execution health on record.

## 5. Defects found

The run surfaced real system defects. They are reported as found, not fixed: fixing them
mid-experiment would have changed the system under test.

| # | Defect | Effect on this run | Evidence |
|---|---|---|---|
| D1 | `sec_filing_list_sections` / `sec_filing_get_section` raise `AttributeError: 'NoneType' object has no attribute 'sections'` for **META, V, MA** FY2025 10-Ks. Root cause: edgartools' `TenK.document` returns `None` for these filings (the primary `.htm` exists in the filing index; the parser only warns), and both tools iterate `tenk.document.sections`. | Rows 9 and 13: every arm that tried the whole-section path got errors and lost health; 23 of the 31 hard tool errors in the batch | `prewarm.json`, `raw/row09__*`, `raw/row13__*` |
| D2 | `sec_filing_search` fails for the same three tickers with `CorpusUnavailableError: Search failed: 'NoneType' object has no attribute 'download'`. JIT ingestion depends on the same edgartools fetch. | Rows 9 and 13: the RAG path is equally blind for META/V/MA, so **row 13 (an SEC-source row) has no usable SEC evidence in any arm**; 4 hard tool errors | same |
| D3 | Agents retry a failing SEC call: `luna_medium` called `list_sections` on V three times in one run. | Burns the 10-call budget (row 13 hit it in A and B) | `raw/row13__luna_medium.json` |
| D4 | Data coverage: Airbus (`AIR.PA`) isn't an SEC filer, and Finnhub returns 403 on the current plan. | Row 29 health drops for whichever arm tries it (B and luna_none); the remaining 4 hard tool errors | `raw/row29__*` |

Three of the ten SEC-filing tickers in the dev set are unreadable on both SEC paths,
which caps what E1 can say about SEC-heavy questions on this split.

## 6. Cost model

List prices read on 2026-10-21 from the providers' own pages:

| Model | Input | Cached input | Output | Source |
|---|---|---|---|---|
| `gpt-5.6-luna` | $0.20 / 1M | $0.02 / 1M | $1.20 / 1M (reasoning tokens billed as output) | https://developers.openai.com/api/docs/models/gpt-5.6-luna |
| `gemini-3.6-flash` | $0.75 / 1M | $0.075 / 1M | $3.75 / 1M (incl. thinking tokens) | https://ai.google.dev/gemini-api/docs/pricing (paid tier, standard; rates valid through 2026-12-31, doubling on 2027-01-01) |

`cost = (input − cached) × in + cached × cached_in + output × out`. For both providers,
LangChain's `output_tokens` already includes reasoning/thinking tokens (checked on the
gemini_medium smoke run: 5,500 output, of which 4,178 reasoning). Context-cache storage
fees and the 272K long-context tier are not modeled. The tier is billed per request, and
the largest single run's *total* input across all its model calls was 139.5k tokens
(gemini_minimal, row 6), so no individual request came close.
Embedding cost for pre-warm/JIT ingestion is excluded (shared, one-off).

## 7. Decisions made during execution

The user was unavailable during the run, so these calls were made autonomously and are
recorded here for review:

1. **Arm B as a separate ablation config (brief option b), not the `reader` profile.** The reader profile leaves `reasoning_effort` unset; it resolves to `medium` only via `_init_model`'s provider default. An explicit `medium` makes the A/B dump identical except for the bundle. Putting the config in `benchmark/ablations/` instead of `benchmark/configs/` keeps the 2×2's single-canonical-prompt guarantee untouched, and the reader prompt is referenced by path, never copied. A config-loader test pins "differs from `luna_medium` only in tools".
2. **One Braintrust experiment per arm, driven manually** (`braintrust.init` + `start_span`), instead of the scenario runner's one-`Eval()`-per-config. The runner can't interleave configs row by row; row-major execution was the brief's requirement for live-data fairness.
3. **Within-row order**: E1 pair back-to-back with alternating first arm; E2 arms rotated (§2).
4. **Pre-warm SEC caches** before timed runs (§2). Without it, cold JIT ingestion lands inside whichever arm runs first.
5. **Qdrant**: started `qdrant/qdrant:v1.17.1` on the main checkout's existing `fin-lab-x_qdrant_data` volume, collection `sec_filings_openai_large_dense_baseline`. JIT ingestion added the dev tickers' latest 10-Ks to that volume (additive, same as product use).
6. **Defects D1–D4 left unfixed** (§5).
7. **Blind review sheet masks `sec://` chunk ids** as "SEC 10-K excerpt". Otherwise every pair is unblinded by citation format. `[N]` marker density can still hint at the arm, as the sheet notes.
8. **Smoke runs** used row 6 (a dev row) and are excluded from results; they ran ~5 minutes before the batch and touched the same live sources.

## 8. Claim boundary

What this experiment can and cannot support:

- **Directional only.** n = 1 per (row, arm), 8 dev rows, heterogeneous questions. No significance testing, no confidence intervals. One run per cell can't separate a config effect from run-to-run sampling noise, which is not small for agent trajectories (tool choice, call count). For E1 the paired, back-to-back design reduces but does not remove this.
- **Live, non-replayable inputs.** News, quotes, and "latest 10-K" depend on the run window (2026-10-21 15:57–16:19 UTC). A re-run is a new sample, not a replication.
- **E1 measures the bundle** (tools + prompt), not `sec_filing_search` alone. The sanity rows show the prompt half changes tool-use policy on its own.
- **Quality evidence is one human rater on 8 pairs.** Execution health, tokens, latency, and cost are process metrics. The only quality signal is the blind review (A 5 – B 3, p = 0.73): one rater, who also built the system, with no rubric beyond "more useful to the investor", and with blinding weakened by `[N]` citation density. It can't support "RAG is worse" or "RAG is better".
- **Execution health is confounded by tool defects** (§5) on rows 9, 13, and 29; 3 of 10 SEC tickers are unreadable on both paths. Health differences between arms here are not model or prompt quality signals.
- **E2's Luna pair differs in effective temperature** (`luna_none` 0.0 vs. `luna_medium` provider default, because langchain-openai drops temperature for reasoning-enabled GPT-5.x). The "reasoning effort" effect within Luna is entangled with a sampling change. Gemini's pair is clean on this axis (both 0.0), but `minimal` is Gemini's reasoning floor, not "off".
- **Latency** is end-to-end wall clock, including tool and network time (Tavily, Finnhub, EDGAR, local Qdrant), measured from one machine on one night. Medians over 8 rows only.
- **Dev split is a tuning surface.** These rows are meant for iteration; nothing here is a holdout result.

## 9. Braintrust experiments

Project `finlab-x`, one experiment per arm (row metadata includes `row_id`, `arm`,
`slot_in_row`, `row_order`; scores `diagnostic_execution_health` and
`response_no_simplified_chars`; the LangChain trace nests under each row):

| Arm | Experiment |
|---|---|
| luna_medium (E1 A + E2) | [agent-config-benchmark-dev_20261021-dev_luna_medium](https://www.braintrust.dev/app/Dong.wyt%20Personal/p/finlab-x/experiments/agent-config-benchmark-dev_20261021-dev_luna_medium) |
| reader_luna_medium (E1 B) | [agent-config-benchmark-dev_20261021-dev_reader_luna_medium](https://www.braintrust.dev/app/Dong.wyt%20Personal/p/finlab-x/experiments/agent-config-benchmark-dev_20261021-dev_reader_luna_medium) |
| luna_none | [agent-config-benchmark-dev_20261021-dev_luna_none](https://www.braintrust.dev/app/Dong.wyt%20Personal/p/finlab-x/experiments/agent-config-benchmark-dev_20261021-dev_luna_none) |
| gemini_minimal | [agent-config-benchmark-dev_20261021-dev_gemini_minimal](https://www.braintrust.dev/app/Dong.wyt%20Personal/p/finlab-x/experiments/agent-config-benchmark-dev_20261021-dev_gemini_minimal) |
| gemini_medium | [agent-config-benchmark-dev_20261021-dev_gemini_medium](https://www.braintrust.dev/app/Dong.wyt%20Personal/p/finlab-x/experiments/agent-config-benchmark-dev_20261021-dev_gemini_medium) |

Braintrust's free tier keeps traces for 14 days. [`raw/`](raw/) is the permanent record
(full responses, tool calls with args and results, per-model-call usage, tool timings).

## 10. Blind pairwise review

[`blind_review/e1_blind_review.html`](blind_review/e1_blind_review.html) (or the `.md`
twin): 8 E1 pairs, randomly labelled X/Y (system RNG), verdict = X better / Y better /
tie / both bad, plus notes. The key is
[`blind_review/e1_blind_review_KEY.json`](blind_review/e1_blind_review_KEY.json). The rater
judged from the sheet alone on 2026-10-22 and exported
[`e1_blind_review_verdicts.csv`](blind_review/e1_blind_review_verdicts.csv); it was then
decoded against the key into
[`e1_blind_review_results.csv`](blind_review/e1_blind_review_results.csv).

| Row | Expected source | SEC path A / B | SEC tokens A / B | Preferred |
|---|---|---|---|---|
| 3 | mixed | neither / search | 0 / 4,962 | **A** |
| 6 | SEC | get_section / search | 70,998 / 5,341 | **A** |
| 9 | mixed | get_section / search (META failed both) | 16,331 / 5,358 | **B** |
| 13 | SEC | neither / search (all SEC failed) | 0 / 28 | **A** |
| 17 | mixed | get_section / search | 41,103 / 17,582 | **B** |
| 20 | Finnhub (sanity) | get_section / search | 52,695 / 4,651 | **A** |
| 24 | Finnhub (sanity) | neither / search | 0 / 9,772 | **A** |
| 29 | mixed | neither / search | 0 / 4,426 | **B** |

**A (no RAG) 5 – B (RAG bundle) 3**, no ties, no "both bad". Two-sided sign test
p = 0.73. Limits: one rater (also the system's author), no written rubric, no notes, and
the blinding was partial. SEC chunk ids were masked, but B's `[N]` citation density can
still identify it. The sheet was regenerated once before judging (to fix rendering),
which re-drew the X/Y labels. No verdicts had been recorded at that point, and the key on
file matches the sheet that was judged.
