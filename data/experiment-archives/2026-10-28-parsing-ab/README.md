# HTML vs Text Parsing A/B — SEC 10-K Retrieval

> **One-line takeaway:** With embedding, chunking, top-k, filters and query
> vectors held fixed, the edgartools-based text pipeline reaches recall@10 0.95
> vs 0.60 for the frozen HTML parser (Δ +0.35 [+0.20, +0.50], n = 40). Most of
> the gap is Item attribution, not evidence retrieval: ignoring labels, the gap
> is +0.075 [+0.000, +0.175].

This directory archives a completed one-shot experiment: does replacing the
hand-written SEC HTML parser with the text pipeline change what dense retrieval
finds?

## Start here

| Doc | Read this for |
|---|---|
| [`report.md`](report.md) | The reference: design, controlled variables, results with CIs, gap decomposition, failure examples, claim boundary, per-row table, reproduce steps |
| [`recall_at_5_definitions.md`](recall_at_5_definitions.md) | Slide-ready recall@5 table: did the evidence reach the LLM vs did it also carry the right Item label |

## Files

| File | What it is |
|---|---|
| `README.md` | This index |
| `report.md` | The reference report |
| `recall_at_5_definitions.md` | Recall@5 / @10 / MRR for both arms under *snippet only* vs *snippet + correct Item* (strict as reference), plus the @5 HTML miss diagnosis |
| `tables.md` | Generated tables from `analyze` (aggregate, sensitivity, breakdowns incl. per-ticker, miss diagnosis, every discordant row) |
| `per_row.csv` | Per row: strict, format-insensitive and label-agnostic ranks for both arms, MRR, outcome class |
| `summary.json` | Aggregate point estimates and CIs per metric and arm |
| `run_meta.json` | Run provenance: git commit, dataset sha256, collections and point counts, embedding config, top-k |
| `ingest_manifest.json` | Per filing and arm: chunk count, Item-label distribution, accession, edgartools version |
| `raw/retrievals.jsonl.gz` | Both arms' top-10 chunks (path, item, score, text) for every row |
| `raw/query_embeddings.json.gz` | The shared query vectors; drop in to reproduce retrieval exactly |
| `raw/ingest_manifest_superseded_text-edgartools-5.17.1.json` | The first text-arm ingest on the edgartools 5.17.1 store, kept for the chunk-count comparison in `report.md` §4 |

## Reproduce

Tag `experiment/2026-10-28-parsing-ab` pins the harness, dataset and scorer.
`git checkout` it and follow `report.md`'s Reproduce section.
