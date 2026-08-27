# RAG Metadata-Filter A/B Eval — English-Dataset Re-run, AMD 10-K/A Fix

> **One-line takeaway:** Re-running [`2026-08-18-rag-metadata-filter-ab-eval`](../2026-08-18-rag-metadata-filter-ab-eval/)
> in English, after fixing a bug that had AMD's corpus pointing at a 10-K/A amendment
> instead of the full 10-K, overturns that run's headline finding: AMD is no longer the
> worst-performing ticker (mean p@10 0.67, was 0.13). The better explanation for the data
> is topic, not ticker — generic risk-factor questions (supply chain, customer
> concentration) score ~0.40 mean p@10 regardless of company; company-distinctive questions
> score ~0.77.

This directory archives a completed one-shot experiment: does the entity-mismatch finding
from the original Chinese-language run hold up once a corpus bug is fixed and the query
language matches what production actually sends to the retriever?

## Start here

| Doc | Read this for |
|---|---|
| [`report.md`](report.md) | The reference — what changed vs. the original run, setup, full tables, per-query numbers, caveats, reproduce instructions |
| [`insights.md`](insights.md) | The narrative — what the numbers mean and why, with a diagram |

## Files

| File | What it is |
|---|---|
| `README.md` | This index |
| `report.md` | The reference report |
| `insights.md` | The narrative walkthrough |
| `metrics.csv` | Per-query precision@5 / @10 for both arms, plus the naive arm's top-10 ticker mix — the numbers every table in `report.md` is built from |
| `retrieval_diff.md` | Qualitative top-5 side-by-side for five highlight queries (which chunks each arm actually returned). Generated 2026-08-27 — see the timestamp in the file itself; the filename carries no date since this directory's own name already does |
| `raw/rag_filter_naive_20260823_085453_599229.csv` | Raw Braintrust `Eval()` output for the naive arm: one row per query, full retrieved chunks (text, ticker, item, score) and both scores. Filename is Braintrust's own generated name, kept for provenance |
| `raw/rag_filter_metadata_filter_20260823_085508_111068.csv` | Same for the metadata-filter arm |

Both arms were uploaded to Braintrust (`--upload`) — unlike the original run, which stayed
local. See `report.md`'s Reproduce table for the experiment links.

## Reproduce

Tag `experiment/2026-08-27-rag-metadata-filter-ab-eval-en-10ka-fix` pins the code that
produced this. `git checkout` it and see `report.md`'s Reproduce table for exact steps.

## Relationship to the original archive

This does not replace [`2026-08-18-rag-metadata-filter-ab-eval`](../2026-08-18-rag-metadata-filter-ab-eval/),
which stays as the permanent record of the original Chinese-language run — including its
now-superseded AMD finding, kept for provenance rather than corrected in place. Read both if
you're tracing why the "worst ticker" changed between them.
