# Trace Archives

Curated, irreproducible trace bundles pulled from the tracing platform within its
retention window (see ADR-0005 and the **Trace Archive** entry in `CONTEXT.md`).

Layout: one directory per bundle — `<YYYY-MM-DD>-<topic>/` containing the NDJSON
files from `bt sync pull` plus a one-line README describing what the bundle records
(typically a notable failure and, later, its successful counterpart).

Unlike everything else under `data/`, this directory is git-tracked: bundles are
hand-picked permanent evidence, not reproducible runtime output. Never use it as a
bulk backup of all traces.
