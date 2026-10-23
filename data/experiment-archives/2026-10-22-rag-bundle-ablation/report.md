# RAG Capability-Bundle Ablation — chunk search vs whole-section 10-K reading (30 rows × 3 runs)

> **One-line takeaway:** With the model held fixed (GPT-5.6 Luna, effort medium), the RAG bundle used chunk search in 85 of 90 runs. Per question it put **34k fewer SEC tokens into context** (95% CI −61k to −15k), **finished 12.4 s faster** (−16.2 to −9.2) and **cost 69% less** ($0.47 vs $1.51 for 90 runs), with **no change in execution health** (+0.01, −0.04 to +0.08). The efficiency gain held in every source category, including Finnhub- and Tavily-answerable questions where the no-RAG arm read whole 10-K sections it didn't need. **Whether the answers are better is not yet known.** The 30-pair blind review is pending; the 2026-10-21 8-pair pilot preferred the no-RAG answers 5–3 (p = 0.73).

This is the reference report: design, config alignment, results with uncertainty,
deviations, and the claim boundary. For what else is in this directory, see
[`README.md`](README.md).

## Reproduce

| | |
|---|---|
| Git tag | `experiment/2026-10-22-rag-bundle-ablation` |
| Branch / Linear | `feat/rag-bundle-ablation` (stacked on `feat/model-reasoning-benchmark`) · DEV-220 |
| Code that ran | commit `b40354b`, later rebased as `11afb9f` (identical tree) |
| Run windows | Batch 1: 2026-10-22 01:02–01:24 UTC (128 runs, 64 A/B pairs). OpenAI credits ran out at 01:23:47 UTC; the remaining 26 pairs were re-run together at 04:15–04:26 UTC after the top-up, so every A/B pair still ran back-to-back. |
| Config dump | `python -m backend.evals.experiments.rag_ablation.run dump --out-dir <dir>` → [`config_dump/`](config_dump/) |
| Runs | `python -m backend.evals.experiments.rag_ablation.run run --out-dir <dir> --label 20261022-all30 --rows all --rep K` for K = 1, 2, 3 (needs Qdrant on `:6333` with the SEC collection, and `backend/.env` keys as in the model × reasoning benchmark) |
| Metrics | `python -m backend.evals.experiments.rag_ablation.analyze --raw-dir <dir>/raw --out-dir <archive>` |
| Review sheet | `python -m backend.evals.experiments.rag_ablation.review_sheet --raw-dir <dir>/raw/rep1 --out-dir <archive>/blind_review` |
| Braintrust | one experiment per (arm, repetition); see [`braintrust_links.json`](braintrust_links.json) |
| Total API cost | ≈ US$1.98 model spend (A $1.51, B $0.47); Tavily credits are shared with the model × reasoning benchmark |

**Live data cannot be replayed.** A re-run is a new sample; [`raw/`](raw/) keeps what
these runs saw.

## 1. Question

ADR-0010 assumes RAG over 10-Ks beats reading a long section in full. With the model
held fixed, does giving the agent `sec_filing_search` (dense retrieval over chunked
10-Ks, chunk-level citations) beat finding the right section with
`sec_filing_list_sections` and reading it whole with `sec_filing_get_section`?

## 2. Design

| | Arm A `luna_medium` | Arm B `reader_luna_medium` |
|---|---|---|
| Model | `openai:gpt-5.6-luna`, reasoning effort `medium` | same |
| Built model kwargs | Responses API, `reasoning={effort: medium, summary: auto}`, temperature dropped by langchain-openai | same |
| Tool budget | 10 calls per run | same |
| Tools | 5 baseline tools (whole-section reading only) | same 5 **+ `sec_filing_search`** |
| Prompt | canonical benchmark prompt (= `profiles/baseline`), 4,516 chars | `profiles/reader/system_prompt.md`, 8,970 chars, referenced not copied |

**This measures the bundle, not the tool alone.** The reader prompt's citation rules
are written for search chunks, so the tool and the prompt move together. The reader
prompt also differs in ways unrelated to retrieval: a stronger language policy,
grounding rules, `[N]` citations, and framing 10-K filings as the primary evidence
source. Rows whose best source is Finnhub or Tavily need no 10-K, so they show what
the prompt half of the bundle does on its own.

**Config alignment.** `run.py dump` resolves both arms the way the orchestrator builds
them, hashes every tool's description and argument schema plus the raw and rendered
prompt, and fails on any difference outside identity, tools and prompt: **PASS**
([`config_dump/ab_config_diff.json`](config_dump/ab_config_diff.json)). The five
shared tools have identical contracts.

**Rows and protocol.** All 30 rows of the zh diagnostic dataset (split deliberately
not applied this round; `split.json` unchanged) × 3 repetitions = 180 runs. One worker
per repetition, row-major, the A/B pair always back-to-back with the first arm
alternating by `(row + rep) mod 2`. Each worker pre-warms both SEC paths for all 24
10-K filers named by the dataset; all succeeded. Up to 6 agent runs were in flight
(the model × reasoning benchmark ran at the same time).

**Metrics.** These are the same code-only metrics as the model × reasoning benchmark,
plus the SEC path each run took (search only / get_section only / both / neither) and
the SEC evidence tokens that entered context (cl100k count of `get_section` + `search`
results). Per-row means over repetitions come first, then paired B − A differences
with a row-level bootstrap 95% CI.

## 3. Results

### Arms

| Arm | Runs | Task errors | Health mean [95% CI] | SEC path (runs) | Hard tool errors/run | Runs at tool budget | Simplified-drift runs | Total cost USD |
|---|---|---|---|---|---|---|---|---|
| luna_medium | 90 | 0 | 0.92 [0.84, 0.99] | G×68 ∅×22 | 0.11 | 6 | 1 | 1.51 |
| reader_luna_medium | 90 | 0 | 0.93 [0.83, 1.00] | S+G×3 ∅×5 S×82 | 0.11 | 2 | 1 | 0.47 |

SEC path codes: S = search only, G = get_section only, S+G = both, ∅ = neither.

### Paired contrast B − A (per-row means over repetitions; 95% CI = row bootstrap)

| Subset | Rows | Δ execution_health | Δ sec_evidence_tokens | Δ input_tokens | Δ output_tokens | Δ tool_calls_total | Δ ttft_first_event_s | Δ e2e_s | Δ est_cost_usd |
|---|---|---|---|---|---|---|---|---|---|
| all rows | 30 | +0.01 [-0.04, +0.08] | -34,153 [-60,612, -15,413] | -34,072 [-59,524, -14,828] | -578 [-702, -457] | -2.1 [-2.7, -1.6] | -0.6 [-1.6, +0.0] | -12.4 [-16.2, -9.2] | -0.0116 [-0.0224, -0.0041] |
| source = Finnhub | 5 | +0.00 [+0.00, +0.00] | -32,244 [-55,992, -6,174] | -37,251 [-62,056, -6,830] | -573 [-746, -308] | -1.7 [-2.9, +0.0] | -2.8 [-7.8, +0.2] | -14.2 [-21.1, -7.7] | -0.0075 [-0.0125, -0.0019] |
| source = SEC | 9 | +0.00 [+0.00, +0.00] | -42,835 [-102,231, -7,084] | -44,367 [-99,623, -10,945] | -711 [-948, -459] | -2.8 [-4.0, -1.6] | -0.2 [-0.5, +0.2] | -16.3 [-22.7, -11.6] | -0.0160 [-0.0403, -0.0026] |
| source = Tavily | 4 | +0.08 [-0.25, +0.50] | -17,822 [-36,398, +754] | -16,631 [-39,701, +6,439] | -439 [-819, -186] | -1.6 [-2.8, -0.3] | -0.1 [-0.6, +0.5] | -8.8 [-13.8, -3.7] | -0.0042 [-0.0083, -0.0000] |
| source = mixed | 12 | +0.00 [-0.08, +0.08] | -33,880 [-80,016, -4,788] | -30,840 [-78,273, +2,127] | -527 [-720, -387] | -2.0 [-2.6, -1.3] | -0.1 [-0.5, +0.3] | -10.0 [-17.1, -4.0] | -0.0124 [-0.0309, -0.0018] |

### Per row (means over repetitions; cells are A / B)

| Row | Source | SEC path A | SEC path B | SEC tokens | E2E s | Cost USD | Health |
|---|---|---|---|---|---|---|---|
| 1 | Tavily | G×3 | S×3 | 32058 / 5251 | 34.4 / 23.0 | 0.0102 / 0.0040 | 1.00 / 1.00 |
| 2 | mixed | G×2 ∅×1 | S×3 | 25414 / 8847 | 38.4 / 32.4 | 0.0097 / 0.0055 | 1.00 / 1.00 |
| 3 | mixed | G×1 ∅×2 | S×3 | 5400 / 4852 | 28.9 / 23.0 | 0.0051 / 0.0039 | 1.00 / 1.00 |
| 4 | Tavily | ∅×3 | S×3 | 0 / 48 | 39.7 / 35.1 | 0.0052 / 0.0052 | 0.33 / 0.00 |
| 5 | Tavily | G×3 | S×3 | 53873 / 7884 | 39.6 / 23.4 | 0.0153 / 0.0047 | 0.33 / 1.00 |
| 6 | SEC | G×3 | S×3 | 56294 / 8930 | 44.5 / 26.4 | 0.0167 / 0.0055 | 1.00 / 1.00 |
| 7 | mixed | G×3 | S×3 | 27027 / 4783 | 44.2 / 31.3 | 0.0114 / 0.0057 | 1.00 / 1.00 |
| 8 | SEC | G×3 | S×3 | 272538 / 17871 | 60.7 / 22.8 | 0.1145 / 0.0068 | 1.00 / 1.00 |
| 9 | mixed | G×3 | S×3 | 46225 / 24675 | 40.9 / 30.6 | 0.0148 / 0.0097 | 0.67 / 1.00 |
| 10 | mixed | G×3 | S×3 | 63320 / 15023 | 33.3 / 21.5 | 0.0178 / 0.0064 | 1.00 / 1.00 |
| 11 | SEC | G×3 | S×3 | 5450 / 8662 | 20.7 / 16.1 | 0.0034 / 0.0038 | 1.00 / 1.00 |
| 12 | SEC | G×3 | S×3 | 15827 / 9801 | 37.9 / 18.4 | 0.0077 / 0.0047 | 1.00 / 1.00 |
| 13 | SEC | G×3 | S×3 | 37136 / 9921 | 31.8 / 16.7 | 0.0115 / 0.0044 | 1.00 / 1.00 |
| 14 | SEC | ∅×3 | S×3 | 0 / 6867 | 32.7 / 20.1 | 0.0040 / 0.0043 | 1.00 / 1.00 |
| 15 | SEC | G×3 | S×3 | 30936 / 10693 | 37.1 / 21.5 | 0.0107 / 0.0054 | 1.00 / 1.00 |
| 16 | SEC | G×3 | S×3 | 53376 / 10546 | 29.3 / 16.8 | 0.0141 / 0.0045 | 1.00 / 1.00 |
| 17 | mixed | G×3 | S×3 | 42388 / 15441 | 39.8 / 43.4 | 0.0135 / 0.0072 | 1.00 / 1.00 |
| 18 | SEC | G×3 | S×3 | 7043 / 9797 | 27.4 / 16.2 | 0.0049 / 0.0043 | 1.00 / 1.00 |
| 19 | Finnhub | G×3 | S×3 | 77986 / 5110 | 30.8 / 16.9 | 0.0186 / 0.0029 | 1.00 / 1.00 |
| 20 | Finnhub | G×3 | S×3 | 54896 / 6500 | 28.1 / 14.5 | 0.0141 / 0.0032 | 1.00 / 1.00 |
| 21 | mixed | G×3 | S×3 | 53888 / 18938 | 41.4 / 25.4 | 0.0162 / 0.0066 | 1.00 / 1.00 |
| 22 | Finnhub | G×3 | S×3 | 48855 / 11438 | 57.2 / 31.3 | 0.0147 / 0.0057 | 1.00 / 1.00 |
| 23 | Finnhub | G×2 ∅×1 | S×3 | 17667 / 5110 | 35.6 / 21.3 | 0.0074 / 0.0036 | 1.00 / 1.00 |
| 24 | Finnhub | ∅×3 | S×3 | 0 / 10027 | 30.0 / 26.5 | 0.0036 / 0.0054 | 1.00 / 1.00 |
| 25 | mixed | ∅×3 | ∅×3 | 0 / 0 | 20.4 / 18.4 | 0.0022 / 0.0020 | 1.00 / 1.00 |
| 26 | mixed | ∅×3 | S×3 | 0 / 13783 | 39.6 / 26.5 | 0.0048 / 0.0063 | 1.00 / 1.00 |
| 27 | mixed | G×3 | S×3 | 272538 / 8609 | 68.9 / 27.5 | 0.1137 / 0.0049 | 1.00 / 1.00 |
| 28 | Tavily | G×1 ∅×2 | ∅×2 S×1 | 280 / 1741 | 24.6 / 21.8 | 0.0027 / 0.0026 | 1.00 / 1.00 |
| 29 | mixed | G×2 ∅×1 | S×3 | 8437 / 8127 | 52.9 / 41.3 | 0.0076 / 0.0069 | 0.33 / 0.00 |
| 30 | mixed | G×3 | S+G×3 | 13448 / 28446 | 49.0 / 56.2 | 0.0069 / 0.0097 | 1.00 / 1.00 |

### What the numbers say

1. **Which path B took: search, almost always.** B used `sec_filing_search` alone in 82 of 90 runs. It combined it with `get_section` 3 times (row 30, all three repetitions) and used no SEC tool 5 times (row 25 every time, row 28 twice). A read whole sections in 68 runs and skipped SEC in 22.
2. **Context and latency: large, consistent reductions.** Per question, B − A was −34.2k SEC tokens and −34.1k input tokens, with 2.1 fewer tool calls and 12.4 s less E2E (all CIs exclude 0). Median per run: SEC evidence 9.6k vs 27.0k tokens, input 18.9k vs 43.3k, E2E 22.6 s vs 37.0 s. The extreme case is JPM (rows 8 and 27), where A read ~272k SEC tokens per run, crossed OpenAI's long-context price tier 6 times and took 61–69 s. B answered from 9–18k tokens in 23–28 s.
3. **Cost: −$0.0116 per run [−0.0224, −0.0041].** That is 69% less overall, and the reduction holds in each source category (the Tavily category's upper bound reaches 0).
4. **The bundle changes policy, not just retrieval.** On Finnhub- and Tavily-answerable rows, which need no 10-K, A still read whole sections in most runs, and B replaced that with search. The "sanity" expectation that A ≈ B on these rows does not hold: both arms consult filings there, just at different cost. On rows 14, 24 and 26 the reverse happened: A skipped SEC and B added searches, costing more on those rows.
5. **Execution health: no difference** (0.92 vs 0.93). All 13 health-0 runs are coverage failures: TSMC/ASML 20-Fs, the Finnhub 403 and SEC "not found" for Airbus, INTC's 10-K lacking Item 7, or a budget block.
6. **Citations.** Whenever an answer used `[N]` markers, B's markers and definitions matched in 86 of 87 answers, A's in 49 of 54. This is the prompt half of the bundle at work (the reader prompt's citation rules).
7. **What this does not settle: answer quality.** Fewer tokens can mean precise evidence or missing context. Read [§6](#6-blind-pairwise-review) before concluding "RAG is better".


## 4. Deviations during execution

1. **OpenAI credit outage.** At 01:23:47 UTC the OpenAI organization ran out of API credit. Both arms run on OpenAI, so the 26 unfinished A/B pairs failed together. Their records were moved aside, and after the user's top-up the pairs re-ran together (04:15–04:26 UTC). The back-to-back pairing was preserved; only those 26 pairs saw later live data than the rest.
2. **Concurrency.** This experiment's 3 workers ran alongside the model × reasoning benchmark's 3, so up to 6 runs were in flight. A and B shared the same load within each pair.
3. **Cost model corrected after the run.** It is now priced per model call, applying OpenAI's >272K-input long-context rate (6 of A's calls, 0 of B's). This widened the measured cost gap.
4. **Rebased after running.** Runs executed from `b40354b`. The tree is unchanged by the rebase onto main, the model × reasoning archive commit and the cost fix.
5. **Smoke run** (row 13 × A/B) preceded the batch and is excluded.

## 5. Claim boundary

- **Bundle, not tool.** B changes the toolset *and* the prompt. The reader prompt adds stricter language/grounding/citation rules and frames 10-Ks as the primary source. Finnhub/Tavily rows show the prompt moving tool-use policy by itself, so no effect here can be credited to `sec_filing_search` alone. A tool-only ablation (same prompt, ± search) is the next experiment.
- **Process metrics, quality pending.** Lower tokens, latency and cost are measured. Answer quality is not, until the blind review is done. One rater, one repetition, and blinding is weakened by citation style.
- **30 questions × 3 runs**, row-bootstrap CIs, no multiple-comparison correction across the 8 metrics × 5 subsets; the per-source subsets are small (4–12 rows).
- **Split not applied** (user decision): holdout and reserve rows were run and are no longer unseen.
- **Live inputs**; 26 of 90 pairs ran about three hours after the others.
- **Same model, same temperature handling**: langchain-openai drops temperature for effort=medium in both arms (provider default sampling).

## 6. Blind pairwise review

[`blind_review/blind_review.html`](blind_review/blind_review.html) (Markdown twin `blind_review.md`) holds repetition 1's 30 A/B pairs, randomly labelled X/Y with a system RNG (B is X in 16 of 30). `sec://` chunk ids are masked, and answers are rendered at build time so the sheet works without JavaScript. The key is in `blind_review/blind_review_KEY.json`; open it only after judging.

**Status: pending.** Results will be decoded against the key and added here.
