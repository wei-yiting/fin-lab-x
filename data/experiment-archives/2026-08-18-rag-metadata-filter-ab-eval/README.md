# RAG Metadata-Filter A/B Eval — Entity Mismatch in SEC 10-K Retrieval

> **One-line takeaway:** On Chinese-language questions against a six-company SEC 10-K
> corpus, dense retrieval **without** a ticker filter returned the right company in only
> **62%** of top-10 chunks on average, with per-query precision ranging from **0.00 to
> 1.00**. With a `must=[ticker=X]` filter every query scored 1.00 — but that number is a
> property of the filter, not a finding. **The finding is the naive arm's low mean, high
> variance, and total collapse on the smallest ticker (AMD).**

This directory archives a completed one-shot experiment: does SEC 10-K dense retrieval
confuse companies when it isn't told which one to look at?

## Start here

| Doc | Read this for |
|---|---|
| [`report.md`](report.md) | The reference — setup, full tables, per-query numbers, caveats, reproduce instructions |
| [`insights.md`](insights.md) | The narrative — what the numbers mean and why, with a diagram |

## Files

| File | What it is |
|---|---|
| `README.md` | This index |
| `report.md` | The reference report |
| `insights.md` | The narrative walkthrough |
| `metrics.csv` | Per-query precision@5 / @10 for both arms, plus the naive arm's top-10 ticker mix — the numbers every table in `report.md` is built from |
| `retrieval_diff.md` | Qualitative top-5 side-by-side for five highlight queries (which chunks each arm actually returned). Generated 2026-05-13 — see the timestamp in the file itself for the exact moment; the filename carries no date since this directory's own name already does |
| `raw/rag_filter_naive_20260513_082006_625583.csv` | Raw Braintrust `Eval()` output for the naive arm: one row per query, full retrieved chunks (text, ticker, item, score) and both scores. Filename keeps its original 2026-05-13 timestamp — this is Braintrust's own generated name, kept for provenance |
| `raw/rag_filter_metadata_filter_20260513_081935_657577.csv` | Same for the metadata-filter arm |

The 2026-05-13 session ran each arm three times; all three runs were bit-identical, so
one raw file per arm is kept here. All six are on the tag under `backend/evals/results/`.

## Reproduce

Tag `experiment/2026-08-18-rag-metadata-filter-ab-eval` @ `dc1b3b8` pins the code that
produced this. `git checkout` it and see `report.md`'s Reproduce table for exact steps.
