# RAG Metadata-Filter A/B Eval — English-Dataset Re-run, AMD 10-K/A Fix

> **One-line takeaway:** With AMD's corpus fixed (it was accidentally a 10-K/A amendment,
> not the full 10-K) and the query language switched to English, dense retrieval **without**
> a ticker filter still returned the right company in only **69%** of top-10 chunks on
> average — and AMD is no longer the outlier. The worst case is now GOOGL's supply-chain
> question (p@10 = 0.10). Grouping by **question topic** instead of by ticker explains the
> data better: generic risk-factor questions (supply chain, customer concentration) average
> p@10 = 0.40 regardless of company; company-distinctive questions average 0.77.

This directory archives a completed one-shot experiment: a re-run of
[`2026-08-18-rag-metadata-filter-ab-eval`](../2026-08-18-rag-metadata-filter-ab-eval/) with
two independent changes — an English query set, and a corpus bug fix that turned out to
overturn that earlier run's headline finding.

## Reproduce

| | |
|---|---|
| Git tag | `experiment/2026-08-27-rag-metadata-filter-ab-eval-en-10ka-fix` |
| Checkout | `git checkout experiment/2026-08-27-rag-metadata-filter-ab-eval-en-10ka-fix` |
| Steps | `artifacts/experiment_results.md` §10.5 on the tag (from an empty Qdrant to scores) |
| Uploaded | 2026-08-23: naive p@5/p@10 = 0.800 / 0.689, metadata-filter = 1.000 / 1.000 |
| Braintrust | [`rag_filter_naive_20260823_085453`](https://www.braintrust.dev/app/Dong.wyt%20Personal/p/finlab-x/experiments/rag_filter_naive_20260823_085453) · [`rag_filter_metadata_filter_20260823_085508`](https://www.braintrust.dev/app/Dong.wyt%20Personal/p/finlab-x/experiments/rag_filter_metadata_filter_20260823_085508) |
| Linear | DEV-196 |

The experiment harness (scenarios, scorer, scripts, dataset) lives only on the tag; it was
deliberately not merged into `main` — see
[Why the harness stays on the tag](#why-the-harness-stays-on-the-tag).

## 1. What changed vs. the original run

| | Original (`2026-08-18`) | This run |
|---|---|---|
| Query language | Chinese (18 questions) | English (18 questions, same 6 tickers × 3 topics) |
| AMD's corpus | 10-K/A amendment — 83 chunks, Part III/IV only | Full 10-K — 427 chunks, Part I–IV |
| Why | Undiscovered at the time: `SECDownloader` had its own filing-locate path that main's `sec_core.py` fix (PR #64) didn't cover | Fixed by cherry-picking PR #64 + its follow-up PR #66 (`amendments=False` in `sec_downloader.py`) onto this experiment's branch |
| Qdrant collection | Shared `sec_filings_openai_large_dense_baseline` | Dedicated `sec_filings_rag_filter_en_baseline` — the shared collection had drifted (other concurrent work had grown it to 8 tickers / 3,518 pts by the time of this run) |
| Total chunks | 1,844 | 2,187 (the +343 delta is almost entirely AMD's fix; every other ticker is within ±1 of its original count) |
| `--upload` | No (both the original run and its 2026-08-18 reproduction were local-only) | Yes — both arms are real, citable Braintrust experiments |

Both changes are independent of each other. Either one alone would justify its own re-run;
doing them together means this report's numbers aren't cleanly separable into "the language
effect" vs. "the corpus-fix effect" — see [Caveats](#5-caveats).

## 2. Setup

| Parameter | Value |
|---|---|
| Embedding model | `text-embedding-3-large` (3072 dims) |
| Vector DB | Qdrant v1.17.1, cosine distance |
| Top-k | 10 |
| Corpus | 2,187 chunks (commit-marker points excluded) |
| Tickers (chunk count) | MSFT (372) · AAPL (254) · **AMD (427)** · INTC (403) · GOOGL (398) · NVDA (339) |
| Fiscal years | 2025, except NVDA 2026 |
| Dataset | 18 English-language questions, 6 tickers × 3 |
| Query language | English; each of AMD/Intel/NVIDIA/Google/Microsoft/Apple's own name appears in its own questions as ordinary English, same as any natural query would |
| Ingestion pipeline | frozen `sec_dense_pipeline_html`, with PR #64/#66's amendment-exclusion fix cherry-picked on top |

Both collections hold **identical embedding vectors** for the same reason as the original —
`sec_filings_naive` is populated by Qdrant `scroll + upsert` from the metadata-filter
collection. Build-time schema and query-time filter are the only differences:

| | Naive collection | Metadata-filter collection |
|---|---|---|
| Points | vectors + payload (copied verbatim) | vectors + payload |
| Payload index | none | `KeywordIndex` on `ticker` / `year` / `item` |
| Tenant hint | none | `is_tenant=True` on `ticker` |
| Query | `search(q, top_k=10)` | `search(q, must=[ticker=X], top_k=10)` — X is the dataset's oracle `target_ticker` |

**Metric:** `ticker_precision@k` — the fraction of the top-k chunks whose `ticker` payload
equals the query's target ticker.

## 3. Aggregate summary

| Metric | Naive (no filter) | Metadata-filter |
|---|---:|---:|
| **Mean p@5** | **0.800** | **1.000** |
| **Mean p@10** | **0.689** | **1.000** |
| Min p@10 | **0.10** | 1.00 |
| Max p@10 | 1.00 | 1.00 |
| Queries | 18 | 18 |

> The metadata-filter column's 1.000 is the same deterministic-filter tautology as every
> arm of this experiment family — not a finding on its own. The naive column moved up from
> the original run's 0.622 mean p@10 to 0.689, but that is not evidence English is
> meaningfully "easier": the corpus changed at the same time (AMD's contribution went from
> the smallest, most confusable corpus in the set to a mid-sized one), and n=18 is too small
> to attribute a 7-point mean shift to either cause individually.

## 4. Per-ticker breakdown (naive arm)

| Ticker | n | p@5 mean | p@10 mean | p@10 range |
|---|---:|---:|---:|---|
| INTC | 3 | 1.00 | **0.97** | 0.9 – 1.0 |
| MSFT | 3 | 0.80 | 0.73 | 0.6 – 1.0 |
| AAPL | 3 | 0.87 | 0.70 | 0.5 – 0.8 |
| NVDA | 3 | 0.80 | 0.70 | 0.5 – 0.8 |
| **AMD** | 3 | 0.80 | **0.67** | 0.5 – 0.8 |
| **GOOGL** | 3 | 0.53 | **0.37** | 0.1 – 0.6 |

**AMD is no longer the worst ticker.** With its corpus corrected to a full 10-K, its mean
p@10 (0.67) sits in the middle of the pack — close to AAPL and NVDA, not far below MSFT.
The original run's headline finding ("AMD is the smallest corpus and gets swallowed by
semantic neighbors") does not survive the fix; see
[§6](#6-what-actually-explains-the-variance-topic-not-ticker).

**GOOGL is now the worst ticker** (mean p@10 = 0.37, one query at 0.10) — see §6 for why.

## 5. Caveats

- **Two variables changed at once.** This run cannot isolate "does English score
  differently than Chinese" from "does a corrected AMD corpus score differently than a
  10-K/A." Both are real, deliberate changes (see §1); neither this report nor the
  original one supports a clean before/after comparison on either axis alone. A
  same-language, same-corpus-fix-only run (or a same-corpus, language-only run) would be
  needed to separate them — not done here.
- **AMD's corpus grew ~5×, not just "got corrected."** 83 → 427 chunks is a large change in
  candidate-chunk density, not a small one; some of AMD's improved p@10 may reflect having
  more of its own content to be retrieved from, independent of any language effect.
- **Small n.** 18 queries, 3 per ticker — per-ticker means are directional, not precise
  effect sizes; a single query's outlier (GOOGL's supply-chain question at 0.10) pulls its
  ticker's mean substantially.
- **Oracle ticker.** As in the original, the metadata-filter arm reads `target_ticker` from
  the dataset — router accuracy (extracting the right ticker from a natural-language
  question) is isolated out.
- **Corpus isolation.** This run used a dedicated Qdrant collection to avoid the shared
  production baseline, which had drifted from concurrent work (8 tickers, 3,518 points by
  the time of this run — see §1). The dedicated collection is not itself archived; only its
  results are.

## 6. What actually explains the variance: topic, not ticker

Re-grouping the same 18 queries by **question topic** instead of by ticker is a cleaner fit
to the data than the per-ticker table above:

| Question type | n | Mean p@10 | Range |
|---|---:|---:|---|
| Generic risk-factor language (supply chain / customer concentration) | 4 | **0.40** | 0.1 – 0.5 |
| Company-distinctive (brand, product, named competitor) | 14 | **0.77** | 0.4 – 1.0 |

Every "supply chain" or "customer concentration" question is at or near the bottom of its
own ticker's results, regardless of which ticker it's paired with:

| Ticker | Generic-topic question | p@10 |
|---|---|---:|
| GOOGL | What supply chain risks does Google's latest earnings report mention? | **0.1** |
| AAPL | What supply chain concentration issues affect Apple's hardware products? | 0.5 |
| AMD | What supply chain and manufacturing process dependency risks does AMD face? | 0.5 |
| NVDA | What customer concentration risks does NVIDIA face? | 0.5 |

10-K risk-factor sections are regulatory-disclosure boilerplate — companies describe supply
chain and customer-concentration risk in structurally and lexically similar language,
regardless of industry. An embedding model has little to anchor entity identity on when the
topic itself is generic. Company-distinctive questions (a named competitor, a specific
product line, a brand-linked business unit) give the embedding a much stronger entity signal
even without a filter — e.g. INTC's "process technology transition" (1.0) or MSFT's "cloud
business revenue growth" (1.0), both narratives essentially unique to one filer in this
corpus.

This reframing also explains why the "worst ticker" flipped between runs: AMD's 83-chunk
10-K/A skewed its questions' answers toward whatever the truncated document happened to
resemble regardless of topic, while GOOGL's supply-chain question — a generic-topic question
paired with a company that has no unusually distinctive risk-factor vocabulary — is a cleaner
example of the underlying mechanism than AMD ever was.

## 7. Why the harness stays on the tag

Same rationale as the original: `ticker_precision@k` under a deterministic filter is always
1.0, so as a standing eval on `main` it carries no information. The naive collection is an
artificial ablation with no production counterpart. The scenarios, scorer, and scripts
therefore live on the tag; this directory keeps what they produced.
