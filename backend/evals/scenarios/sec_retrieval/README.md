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

`regression.enabled: true`; per-scorer floors live in `eval_spec.yaml`.
The floors are time-boxed to the frozen HTML pipeline and the placeholder
dataset, and expire on retriever cutover or dataset replacement — DEV-164
re-measures and re-derives them.
How the numbers were derived — and the recorded reference measurement
backing them (setup, per-case results, raw run CSV, expiry conditions) —
lives with the Regression Suite: `../../regression/metric-floor-policy.md`
and `../../regression/reference_measurements/sec_retrieval/`.

Key notes for dataset maintenance:
- NVDA uses FY2026 (fiscal year ending Jan 2026), not calendar year 2025.
- `expected_header_paths` must include Part-level prefix where present (e.g. `NVDA / 2026 / Part I / Item 1A`, not `NVDA / 2026 / Item 1A`). Tickers without Part structure (e.g. INTC) use `TICKER / YEAR` prefix only.
- Run `validate_sec_eval_dataset` after any dataset edits to check paths against live Qdrant.

## Pre-requisites

1. Ingest target tickers: `python -m backend.scripts.embed_sec_filings NVDA INTC AAPL AMD TSLA`
2. Validate dataset: `python -m backend.scripts.validation.validate_sec_eval_dataset`
3. Ungated measurement run (reports metrics, never evaluates `metric_floor`): `python -m backend.evals.eval_runner sec_retrieval`
4. Gated regression run: `EVAL_PROFILE=baseline pytest backend/evals/regression/ -m eval -k sec_retrieval` (see `../../regression/README.md`)
