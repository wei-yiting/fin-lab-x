# SEC Retrieval Eval Scenario

Evaluates the RAG path's retrieval quality for SEC 10-K filings.

## Scorers

- `header_path_recall_at_5` / `header_path_recall_at_10`: Fraction of expected header paths matched in top-K results
- `mrr`: Mean Reciprocal Rank of first hit
- `map`: Mean Average Precision across expected entries

## Dataset

10 manually written rows covering three query types:
- `single_ticker_fact`: Basic factual retrieval for one company
- `single_ticker_deep`: Deeper analysis within one company's filing
- `cross_company_comparison`: Multi-ticker queries testing structural ceiling

**Status: draft** — This dataset was hand-written as a fallback. The original design (`design_v2-rag-pipeline.md` Section 6.3) planned an Ensemble & Rerank synthetic generation pipeline (`generate_sec_eval_dataset.py`) where two LLMs generate candidate questions and a judge LLM filters the best ones. That script was never implemented; the current 10 rows are manually curated placeholders.

**Next step:** Evaluate whether to build the synthetic generation script, or manually generate questions via LLM with careful human curation. Either way, the dataset should be expanded and answer snippets validated against actual filing content before trusting metrics.

## Regression gate

`enabled: true`, `metric_floor` per scorer — see `eval_spec.yaml`. Floors are
derived from a **reference measurement**, not aspirational targets: the one
recorded run below, minus a fixed margin, rounded down to the nearest 0.05.
The margin is deliberately wide — floors catch collapse, not slow erosion
(erosion belongs to the Quality Track) — and this dataset was only measured
once (it's a draft placeholder; multiple runs wouldn't distinguish signal
from dataset noise).

**Reference measurement** — `2026-08-19`, git `73faf5f`, collection
`sec_filings_openai_large_dense_baseline` (3154 points, frozen HTML
pipeline). Taken after re-ingesting all five dataset tickers with the
10-K/A amendment fix (PR #64/#66) — the earlier ingests of AMD and TSLA
had picked up amendments instead of the original 10-K filings:

| Scorer | Measured | Margin | `metric_floor` |
| --- | --- | --- | --- |
| `header_path_recall_at_5` | 0.95 | −0.20 | 0.75 |
| `header_path_recall_at_10` | 0.95 | −0.20 | 0.75 |
| `mrr` | 0.80 | −0.20 | 0.60 |
| `map` | 0.75 | −0.20 | 0.55 |

**⚠️ This floor is time-boxed to the frozen HTML pipeline.** It measures
`eval_tasks.run_sec_retrieval`, which calls `sec_dense_pipeline_html.retriever`
— the pipeline currently in production, but scheduled for sunset (see
`AGENTS.md` "Ingestion Rewrite Coexistence"). Once the retriever cuts over to
the new `sec_dense_pipeline` (tracked in DEV-160) and this dataset is
replaced by a curated one (DEV-162), **DEV-164** re-measures against the new
retriever + dataset and re-derives these floors from scratch — the values
above do not carry over.

Key notes for dataset maintenance:
- NVDA uses FY2026 (fiscal year ending Jan 2026), not calendar year 2025.
- `expected_header_paths` must include Part-level prefix where present (e.g. `NVDA / 2026 / Part I / Item 1A`, not `NVDA / 2026 / Item 1A`). Tickers without Part structure (e.g. INTC) use `TICKER / YEAR` prefix only.
- Run `validate_sec_eval_dataset` after any dataset edits to check paths against live Qdrant.

## Pre-requisites

1. Ingest target tickers: `python -m backend.scripts.embed_sec_filings NVDA INTC AAPL AMD TSLA`
2. Validate dataset: `python -m backend.scripts.validation.validate_sec_eval_dataset`
3. Run: `python -m backend.evals.eval_runner sec_retrieval`
