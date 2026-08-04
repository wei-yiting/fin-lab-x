# Trace Archives

Curated, irreproducible trace bundles pulled from the tracing platform within its
retention window (see ADR-0005 and the **Trace Archive** entry in `CONTEXT.md`).

Layout: one directory per bundle — `<YYYY-MM-DD>-<topic>/` containing the NDJSON
files from `bt sync pull` plus a one-line README describing what the bundle records
(typically a notable failure and, later, its successful counterpart).

This directory is git-tracked: bundles are hand-picked permanent evidence, not
reproducible runtime output (runtime outputs under `data/` — e.g. `sec_filings/`,
`*.db` — are individually gitignored). Never use it as a bulk backup of all traces.

Scope: runtime **traces only**. Experiments and evaluation results are separate
concepts with their own homes — and unlike logs, experiments are retained
long-term on the platform, so they need no retention-driven archival.
