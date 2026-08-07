# ADR-0011: Repo-anchored data path configuration (2026-08-06)

**Decision**: `backend/common/config.py` resolves every data path — the DuckDB
file, both SEC filing store directories, and the checkpoint DB — off its own
file location via `Path(__file__)`, never off the process's CWD. The six call
sites that used to hardcode `"data/..."` defaults now import from it. Each
resolver is env-overridable (`DUCKDB_PATH`, `CHECKPOINT_DB_PATH`,
`SEC_FILINGS_HTML_DIR`, `SEC_TEXT_DIR`) and defaults under `<repo>/data/`, so
a fresh clone works with zero setup. This lands in the same slice as the
unified error taxonomy (ADR-0012) and the shared retry policy (ADR-0013)
because all three share one root cause: the same convention reimplemented in
multiple places that don't know about each other.

**Context**: CWD-relative paths silently split a second `data/` root whenever
a process starts from a different directory — uvicorn vs CLI vs IDE vs cron.
The write-side and the JIT read-side then diverge: the filing cache written by
one entry point permanently misses for the other. The bug was reproduced
twice in one week — DEV-131 renamed the HTML pipeline's three hardcoded
defaults in place (still three independent hardcodes), and DEV-132 added a
fourth new one (`data/sec_text`) for the JSON filing store — confirming that
"build the new pipeline first, consolidate later" pays this bug forward
rather than avoiding it.

**Rejected — env-var fail-fast for unset paths** (raise `ConfigurationError`
when `SEC_FILINGS_HTML_DIR` etc. aren't set): pure friction for a
single-developer repo. Defaulting under `<repo>/data/` keeps the zero-setup
clone, and env override remains available for Docker/deploy.

**Rejected — document a required startup directory** ("always run from repo
root"): documenting the precondition is not removing it — a path that only
resolves correctly from one CWD *is* the bug, and every new entry point
(cron, IDE test runner) rediscovers it.

**Escape hatch**: each resolver is one function in one file. Changing a
default location or adding a new env override is a one-file edit, not a
repo-wide search-and-replace.

**Re-evaluate if**: deployment moves data outside the repo tree as the norm
(e.g. containerized volumes everywhere), at which point env-first with a
fail-fast default may fit better than repo-anchored defaults.
