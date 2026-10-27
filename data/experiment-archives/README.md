# Experiment Archives

Curated results of one-shot experiments — the permanent, human-readable record of what
was measured and what came out (see the **Experiment Archive** entry in `CONTEXT.md`).

Layout: one directory per experiment — `<YYYY-MM-DD>-<topic>/` — containing a short
`README.md` index (what's here, where to start), a `report.md` with the actual setup,
tables, and reproduce instructions, the per-query metrics that back those tables, and,
when they earn their place, the raw eval-run CSVs under `raw/`. `README.md` never carries
the report itself — its job is orientation, the same as any other directory's README; a
reader after one number goes straight to `report.md`. The directory's date is the day the
experiment was made reproducible, which is also the date in the matching git tag. Files
that carry their own provenance date (a raw run's original filename, a generated diff's
own timestamp) keep it even when it differs from the directory's date — that's the day
the *evidence* was produced, not the day it was archived.

An `insights.md` is optional per entry: the narrative walkthrough of what the numbers mean
and why, for a result substantial enough to warrant one.

Every archived experiment pairs with a git tag of the **same name** under `experiment/`,
which pins the code that produced it (scenarios, scorers, scripts, dataset). The tag holds
*how to run it*; this directory holds *what it produced*. Check the tag out to reproduce;
read here to see the results.

This directory is git-tracked and event-driven: an experiment is archived when its result
is worth keeping, not on every run. Dev-loop eval output stays in the gitignored
`backend/evals/results/`.

Scope: **experiments only** — one-shot A/B comparisons and ablations. Standing eval
scenarios and their regression gates live under `backend/evals/scenarios/`; curated
runtime traces live in `data/trace-archives/`.

| Experiment | Question | Tag |
|---|---|---|
| [`2026-08-18-rag-metadata-filter-ab-eval`](2026-08-18-rag-metadata-filter-ab-eval/) | How much cross-ticker bleed does SEC 10-K dense retrieval suffer without a ticker filter? | `experiment/2026-08-18-rag-metadata-filter-ab-eval` |
| [`2026-08-27-rag-metadata-filter-ab-eval-en-10ka-fix`](2026-08-27-rag-metadata-filter-ab-eval-en-10ka-fix/) | Does the finding above hold in English, once AMD's corpus bug (10-K/A instead of 10-K) is fixed? | `experiment/2026-08-27-rag-metadata-filter-ab-eval-en-10ka-fix` |
