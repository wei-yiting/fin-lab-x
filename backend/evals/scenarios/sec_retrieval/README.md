# SEC Retrieval Eval Scenario

Evaluates the v2 RAG pipeline's retrieval quality for SEC 10-K filings.

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

Key notes for dataset maintenance:
- NVDA uses FY2026 (fiscal year ending Jan 2026), not calendar year 2025.
- `expected_header_paths` must include Part-level prefix where present (e.g. `NVDA / 2026 / Part I / Item 1A`, not `NVDA / 2026 / Item 1A`). Tickers without Part structure (e.g. INTC) use `TICKER / YEAR` prefix only.
- Run `validate_sec_eval_dataset` after any dataset edits to check paths against live Qdrant.

## Pre-requisites

1. Ingest target tickers: `python -m backend.scripts.embed_sec_filings NVDA INTC AAPL AMD TSLA`
2. Validate dataset: `python -m backend.scripts.validation.validate_sec_eval_dataset`
3. Run: `python -m backend.evals.eval_runner sec_retrieval`
