# SEC Retrieval Eval Scenario

Evaluates the v2 RAG pipeline's retrieval quality for SEC 10-K filings.

## Scorers

- `header_path_recall_at_5` / `header_path_recall_at_10`: Fraction of expected header paths matched in top-K results
- `mrr`: Mean Reciprocal Rank of first hit
- `map`: Mean Average Precision across expected entries

## Dataset

10 placeholder rows covering three query types:
- `single_ticker_fact`: Basic factual retrieval for one company
- `single_ticker_deep`: Deeper analysis within one company's filing
- `cross_company_comparison`: Multi-ticker queries testing structural ceiling

Dataset requires human curation — placeholder paths and snippets may not match actual filing content.

Key notes for dataset maintenance:
- NVDA uses FY2026 (fiscal year ending Jan 2026), not calendar year 2025.
- `expected_header_paths` must include Part-level prefix where present (e.g. `NVDA / 2026 / Part I / Item 1A`, not `NVDA / 2026 / Item 1A`). Tickers without Part structure (e.g. INTC) use `TICKER / YEAR` prefix only.
- Run `validate_sec_eval_dataset` after any dataset edits to check paths against live Qdrant.

## Pre-requisites

1. Ingest target tickers: `python -m backend.scripts.embed_sec_filings NVDA INTC AAPL AMD TSLA`
2. Validate dataset: `python -m backend.scripts.validate_sec_eval_dataset`
3. Run: `python -m backend.evals.eval_runner sec_retrieval`
