# RAG Metadata-Filter A/B Eval — Entity Mismatch in SEC 10-K Retrieval

> **One-line takeaway:** On Chinese-language questions against a six-company SEC 10-K
> corpus, dense retrieval **without** a ticker filter returned the right company in only
> **62%** of top-10 chunks on average, with per-query precision ranging from **0.00 to
> 1.00**. With a `must=[ticker=X]` filter every query scored 1.00 — but that number is a
> property of the filter, not a finding. **The finding is the naive arm's low mean, high
> variance, and total collapse on the smallest ticker (AMD).**

This is the reference report — setup, tables, and reproduce instructions. For the narrative
walkthrough of what these numbers mean and why, with a diagram of the retrieval mechanism, see
[`insights.md`](insights.md). For what else is in this directory, see [`README.md`](README.md).

## Reproduce

| | |
|---|---|
| Git tag | `experiment/2026-08-18-rag-metadata-filter-ab-eval` @ `dc1b3b8` |
| Checkout | `git checkout experiment/2026-08-18-rag-metadata-filter-ab-eval` |
| Steps | `artifacts/experiment_results.md` §8 on the tag (from an empty Qdrant to scores) |
| Original run | 2026-05-13, three runs per arm, all bit-identical |
| Reproduction | 2026-08-18 from the tag: naive p@5/p@10 = 0.656 / 0.617, metadata-filter = 1.000 / 1.000 (differences at the third decimal are embedding-API noise) |
| Cited by | 《RAG 不只是 Vector Search — Metadata Filtering 的三層契約》 |
| Linear | DEV-113 |

The experiment harness (scenarios, scorer, scripts, dataset) lives only on the tag; it was
deliberately not merged into `main` — see [Why the harness stays on the tag](#why-the-harness-stays-on-the-tag).

## 1. Setup

| Parameter | Value |
|---|---|
| Embedding model | `text-embedding-3-large` (3072 dims) |
| Vector DB | Qdrant v1.17.1, cosine distance |
| Top-k | 10 |
| Corpus | 1,844 chunks (commit-marker points excluded) |
| Tickers (chunk count) | GOOGL (397) · INTC (402) · MSFT (371) · NVDA (338) · AAPL (253) · AMD (83) |
| Fiscal years | 2025, except NVDA 2026 |
| Dataset | 18 Chinese-language questions, 6 tickers × 3 |
| Query language | Chinese; no question contains a ticker code |
| Ingestion pipeline | frozen `sec_dense_pipeline_html` |

Both collections hold **identical embedding vectors** — the naive collection is populated
by Qdrant `scroll + upsert` from the metadata-filter collection. The only differences are
build-time schema and query-time filter:

| | Naive collection | Metadata-filter collection |
|---|---|---|
| Points | vectors + payload (copied verbatim) | vectors + payload |
| Payload index | none | `KeywordIndex` on `ticker` / `year` / `item` |
| Tenant hint | none | `is_tenant=True` on `ticker` |
| Query | `search(q, top_k=10)` | `search(q, must=[ticker=X], top_k=10)` — X is the dataset's oracle `target_ticker` |

**Metric:** `ticker_precision@k` — the fraction of the top-k chunks whose `ticker` payload
equals the query's target ticker. It measures entity scope, not answer relevance.

## 2. Aggregate summary

| Metric | Naive (no filter) | Metadata-filter |
|---|---:|---:|
| **Mean p@5** | **0.644** | **1.000** |
| **Mean p@10** | **0.622** | **1.000** |
| Std dev p@5 | 0.326 | 0.000 |
| Std dev p@10 | 0.312 | 0.000 |
| Min p@10 | **0.00** | 1.00 |
| Max p@10 | 1.00 | 1.00 |
| Queries | 18 | 18 |

> The metadata-filter column's 1.000 is a mathematical consequence of `must=[ticker=X]`
> forcing every returned point to belong to X. It is not a finding. The numbers worth
> quoting are the naive column: mean 0.622, minimum 0.00, standard deviation 0.312, and
> the per-query breakdown below.

## 3. Per-ticker breakdown (naive arm)

| Ticker | n | p@5 mean | p@5 range | p@10 mean | p@10 range |
|---|---:|---:|---|---:|---|
| AAPL | 3 | 0.93 | 0.8 – 1.0 | 0.73 | 0.4 – 0.9 |
| AMD | 3 | **0.27** | **0.0 – 0.4** | **0.13** | **0.0 – 0.2** |
| GOOGL | 3 | 0.40 | 0.2 – 0.6 | 0.47 | 0.4 – 0.6 |
| INTC | 3 | 0.67 | 0.2 – 1.0 | 0.80 | 0.6 – 1.0 |
| MSFT | 3 | 0.93 | 0.8 – 1.0 | 0.87 | 0.7 – 1.0 |
| NVDA | 3 | 0.67 | 0.4 – 0.8 | 0.73 | 0.4 – 0.9 |

- **AMD is the biggest casualty** — only 83 chunks (4.5% of the corpus), and it shares
  vocabulary with INTC and NVDA (all fabless / AI-accelerator narratives). Without a filter
  its three questions average p@10 = 0.13.
- **MSFT does best** — 「微軟」 is highly specific to MSFT's own filing text, so even the
  naive arm lands.
- **GOOGL** has the most chunks (397) yet still gets contaminated: "Google / cloud"
  concepts appear heavily in AAPL and MSFT filings too.

## 4. Per-query table

`TICKER:N` marks how many of the naive top-10 belong to each ticker; anything other than
the target is cross-ticker contamination. (Same data as `metrics.csv`.)

| Ticker | Query | Naive p@5 | Naive p@10 | MF p@5 | MF p@10 | Naive top-10 ticker mix |
|---|---|---:|---:|---:|---:|---|
| AAPL | 蘋果在中國市場面臨什麼風險? | 1.0 | 0.9 | 1.0 | 1.0 | **AAPL:9** GOOGL:1 |
| AAPL | 蘋果服務業務最新的成長趨勢是什麼? | 1.0 | 0.9 | 1.0 | 1.0 | **AAPL:9** NVDA:1 |
| AAPL | 蘋果硬體產品的供應鏈集中度問題? | 0.8 | **0.4** | 1.0 | 1.0 | **AAPL:4** NVDA:3 INTC:2 GOOGL:1 |
| AMD | AMD 在資料中心市場跟 Intel 競爭的進度? | 0.4 | **0.2** | 1.0 | 1.0 | INTC:7 **AMD:2** NVDA:1 |
| AMD | AMD 的 AI 加速器產品有什麼策略? | 0.4 | **0.2** | 1.0 | 1.0 | NVDA:4 INTC:4 **AMD:2** |
| AMD | AMD 面臨的供應鏈與製程依賴風險? | **0.0** | **0.0** | 1.0 | 1.0 | INTC:7 NVDA:3 |
| GOOGL | Google 在 AI 監管方面揭露了哪些挑戰? | 0.6 | 0.6 | 1.0 | 1.0 | **GOOGL:6** NVDA:2 MSFT:2 |
| GOOGL | Google 最新財報提到哪些供應鏈風險? | 0.2 | **0.4** | 1.0 | 1.0 | **GOOGL:4** AAPL:4 INTC:1 NVDA:1 |
| GOOGL | Google 雲端業務面臨什麼競爭壓力? | 0.4 | **0.4** | 1.0 | 1.0 | MSFT:5 **GOOGL:4** AAPL:1 |
| INTC | 英特爾代工業務的策略與風險? | 0.2 | 0.6 | 1.0 | 1.0 | **INTC:6** AAPL:2 NVDA:2 |
| INTC | 英特爾在 AI 晶片市場的競爭定位? | 0.8 | 0.8 | 1.0 | 1.0 | **INTC:8** NVDA:2 |
| INTC | 英特爾製程技術轉型遇到哪些挑戰? | 1.0 | 1.0 | 1.0 | 1.0 | **INTC:10** |
| MSFT | 微軟在生成式 AI 方面有什麼競爭優勢? | 0.8 | 0.7 | 1.0 | 1.0 | **MSFT:7** NVDA:2 GOOGL:1 |
| MSFT | 微軟跟 OpenAI 的合作對營運帶來什麼風險? | 1.0 | 0.9 | 1.0 | 1.0 | **MSFT:9** NVDA:1 |
| MSFT | 微軟雲端事業的營收成長動能來自哪裡? | 1.0 | 1.0 | 1.0 | 1.0 | **MSFT:10** |
| NVDA | 輝達受美國出口管制影響的程度? | 0.8 | 0.9 | 1.0 | 1.0 | **NVDA:9** INTC:1 |
| NVDA | 輝達在資料中心 GPU 的競爭優勢來源? | 0.8 | 0.9 | 1.0 | 1.0 | **NVDA:9** INTC:1 |
| NVDA | 輝達面臨哪些客戶集中度風險? | 0.4 | **0.4** | 1.0 | 1.0 | **NVDA:4** INTC:3 AAPL:2 GOOGL:1 |

## 5. Per-query variance highlights

### Tier 1 — catastrophic (naive p@10 ≤ 0.2)

| # | Query | Naive p@10 | What went wrong |
|:---:|---|:---:|---|
| 1 | AMD 面臨的供應鏈與製程依賴風險? | **0.0** | Top-10 = 7 × INTC + 3 × NVDA + **0 × AMD**. Not one chunk from the target company. A downstream LLM would "answer" an AMD question with Intel's and NVIDIA's supply-chain language. |
| 2 | AMD 在資料中心市場跟 Intel 競爭的進度? | **0.2** | Top-10 = 7 × INTC + 1 × NVDA + 2 × AMD. "Competing with Intel" pulls INTC's data-center sections even though the question is about AMD's own strategy. |
| 3 | AMD 的 AI 加速器產品有什麼策略? | **0.2** | Top-10 = 4 × NVDA + 4 × INTC + 2 × AMD. "AI accelerator" + "strategy" is evenly distributed across all three filings; similarity cannot separate them. |

AMD's three questions average **p@10 = 0.13**. At 4.5% of the corpus, its chunks are
drowned by semantic neighbours under pure vector search.

### Tier 2 — half-poisoned (0.2 < naive p@10 ≤ 0.5)

| Query | Naive p@10 | Main contaminant |
|---|:---:|---|
| Google 最新財報提到哪些供應鏈風險? | 0.4 | AAPL:4 — Apple's Asian contract-manufacturing narrative is the canonical supply-chain passage |
| Google 雲端業務面臨什麼競爭壓力? | 0.4 | MSFT:5 — Azure sections outrank Google Cloud |
| 輝達面臨哪些客戶集中度風險? | 0.4 | INTC:3 + AAPL:2 + GOOGL:1 — customer concentration is generic 10-K language |
| 蘋果硬體產品的供應鏈集中度問題? | 0.4 | NVDA:3 + INTC:2 — hardware supply chain reads alike across all three |

### Tier 3 — clean without a filter (naive p@10 = 1.0)

| Query | Naive p@10 | Why the entity signal is strong enough |
|---|:---:|---|
| 微軟雲端事業的營收成長動能來自哪裡? | 1.0 | 「微軟」+「雲端」+「營收成長」 all concentrate in MSFT's own text |
| 英特爾製程技術轉型遇到哪些挑戰? | 1.0 | Process-technology transition is INTC's unique narrative; the others are fabless and never discuss their own fabs |

Pre-filtering is not uniformly necessary: for queries whose entity scope is already
disambiguated in embedding space, the filter adds little. For AMD-type queries it is the
difference between 0% and 100%.

## 6. Cross-ticker contamination patterns

| Target | Most common contaminants (all 3 queries × top-10) |
|---|---|
| AMD | INTC (direct rival) > NVDA (fabless GPU / AI peer) |
| GOOGL | AAPL (supply chain) + MSFT (cloud competition) |
| NVDA | INTC (same chip industry) |
| AAPL | NVDA, INTC (hardware analogues) |
| INTC | NVDA, AAPL (generic tech-filing language) |
| MSFT | NVDA, GOOGL (AI and cloud competition) |

Contamination sources track industry rivalry: semantic similarity is strongest between
direct competitors — exactly the pairs a reader least wants confused.

## 7. How to read the numbers

| Number | Finding? | How to use it |
|---|---|---|
| Metadata-filter p@10 = 1.000 | No — tautology of `must=[ticker=X]` | The "fix works" control; do not present it on its own |
| Naive mean p@10 = 0.622 | Yes | Roughly four of every ten retrieved chunks are noise from the wrong entity |
| Naive std = 0.312 | Yes | Not just low on average — reliability is unpredictable per query (0% to 100%) |
| AMD collapse (0.13 mean) | Yes | Small-corpus tickers get buried by semantic neighbours even when their data is present |
| MSFT / INTC queries already at 1.0 | Yes | Pre-filtering has diminishing returns where the entity signal is strong |

## 8. Caveats

- **Small corpus.** 1,844 chunks across 6 companies. HNSW traversal does not degrade at
  this scale, so any latency or within-ticker-recall benefit of the tenant index is **not
  measurable here**; those claims rest on the mechanism, not on this data.
- **Oracle ticker.** The metadata-filter arm reads `target_ticker` from the dataset —
  router accuracy (extracting the ticker from a Chinese question) is isolated out. In
  production, a wrong router decision is a separate failure mode this experiment does not
  cover.
- **n = 3 per ticker.** Per-ticker means are directional, not precise effect sizes.
- **Cross-lingual queries.** Chinese questions against English chunks. The embedding model
  aligns reasonably well across languages, but this is also a condition under which entity
  mismatch is easier to trigger.

## Why the harness stays on the tag

`ticker_precision@k` under a deterministic filter is always 1.0, so as a standing eval on
`main` it would carry no information; the "is the filter actually applied" guard belongs in
a unit test on the retriever, not in an eval scenario. The naive collection is an
artificial ablation with no production counterpart. Both arms, the scorer, and the scripts
therefore live on the tag; this directory keeps what they produced.

The genuinely non-tautological question — does the router pick the right ticker from a
Chinese question — is an agent-level eval and a separate piece of work.
