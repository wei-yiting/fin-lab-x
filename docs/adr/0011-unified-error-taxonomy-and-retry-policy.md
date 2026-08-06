# ADR-0011: Unified error taxonomy, repo-anchored config, and a single retry policy (2026-08-06)

**Decision**: Three converging fixes, shipped as one slice because they share
one root cause — "the same convention reimplemented in multiple places that
don't know about each other." (1) `backend/common/config.py` resolves every
data path (DuckDB file, SEC filing stores, checkpoint DB) off its own file
location via `Path(__file__)`, never off CWD; the six call sites that used to
hardcode `"data/..."` defaults now import from it. (2) `backend/common/errors.py`
defines `FinLabError` as the top-level base plus the four cross-subsystem
error classes — `TransientError`, `TickerNotFoundError`, `ConfigurationError`,
`RateLimitError` — exactly once; `SECError` and `FundamentalsPipelineError`
subclass `FinLabError` directly and keep only errors specific to their own
subsystem. Four `except SECError` / `isinstance(..., SECError)` sites widen to
`FinLabError` so a class migrating between subsystems can't silently stop
matching a handler. (3) `backend/common/retry.py` adds `retry_transient`, a
single tenacity-based decorator (`retry_if_exception_type(TransientError)`,
`stop_after_attempt(3)`, `wait_exponential_jitter()`, `before_sleep_log`,
`reraise=True`), replacing two of the three hand-rolled retry loops audited
in DEV-74/141: the dead-code `fundamentals_pipeline/retry.py` (zero
production callers) is deleted outright, and `embed_sec_filings.py`'s
buggy outer loop — which retried permanent failures, stacked another 3
attempts on top of the SEC pipeline's own internal retry (9 worst case), and
reported every failure as `"skipped"` — is deleted rather than migrated,
since the pipeline it wraps already retries `TransientError` correctly one
layer down. `retry_transient` ships with no production caller yet; its first
consumers are DEV-137 (JIT fetch) and DEV-69 (Finnhub fetcher), both landing
on a clean base instead of inventing a fourth implementation.

**Ratified exception — envelope §0 reachability**: `retry_transient` has no
production caller at this slice's merge time, which design-envelope §0's
reachability rule ("unreachable generality is deleted, not documented")
would normally flag. This is a deliberate, time-boxed exception, not
speculative generality: DEV-137 is already recorded as `blockedBy` DEV-141
in Linear specifically so it lands immediately after this slice and consumes
`retry_transient` as its first real caller — "might be useful someday" (the
disqualifying case per envelope §8) does not apply to a consumer already
queued and sequenced. If DEV-137 and DEV-69 both stall, `retry_transient`
and its test become deletable dead weight and should be swept.

**Explicit exclusion**: `sec_filing_pipeline_html/pipeline.py`'s own
`_execute_with_retry` (the third hand-rolled loop) is **not** migrated. It
lives in the `_html` tree frozen as the A/B baseline (AGENTS.md §
"Ingestion Rewrite Coexistence"); DEV-139 deletes that whole tree, so
refactoring its retry internals now is work thrown away at sunset. Only the
minimal D4 change lands there: its two `except SECError` sites widen to
`FinLabError`, because `TransientError`/`TickerNotFoundError`/
`RateLimitError` moving off `SECError` onto `FinLabError` directly would
otherwise make that pipeline's own re-raised errors silently stop matching.

**Context**: the path bug was reproduced twice in one week — DEV-131 renamed
the HTML pipeline's three hardcoded `data/sec_filings_html` defaults in
place (still three independent hardcodes) and DEV-132 added a fourth
independent hardcode (`data/sec_text`) for the new JSON filing store,
confirming "build the new pipeline before consolidating" pays this bug
forward rather than avoiding it. The error-taxonomy bug already caused a
real incident (7/6 audit C3): two modules each defined their own
`TransientError`, so an `except TransientError` in one module silently never
matched an instance raised by the other.

**Rejected — alias re-export** (keep both class definitions, point one at
the other via `X = other_module.X`): preserves two names for one concept,
which is exactly the ambiguity that caused the 7/6 incident; a grep for "is
this defined once" would still return two hits.

**Rejected — multiple-inheritance bridge** (`class TransientError(SECError,
FundamentalsPipelineError)`): couples two subsystem bases that have no
business knowing about each other, and MRO ambiguity grows with every third
subsystem that wants in.

**Rejected — `Retry-After`-aware pacing on 429** (parse the header, sleep,
retry once): matches SEC's actual behavior (a ~10-minute IP block, and EDGAR
usually omits the header entirely) worse than failing fast — a process that
sleeps 10 minutes holding a worker is worse than one that exits and lets the
operator decide when to resume. `RateLimitError` stays out of the retry list
on principle: retrying a rate limit is the one failure mode that makes the
problem worse, not better.

**Rejected — env-var fail-fast for unset data paths** (raise
`ConfigurationError` if `SEC_FILINGS_HTML_DIR` etc. aren't set): pure
friction for a single-developer repo; defaulting under `<repo>/data/` means
a fresh clone works with zero setup, and env override is still available
for Docker/deploy.

**Escape hatch**: every path resolver and the retry decorator are single
functions/objects in `backend/common/`; changing the default policy is a
one-file edit, not a repo-wide search-and-replace.

**Re-evaluate if**: DEV-139 sunsets the frozen `_html` tree — its retry loop
either gets migrated onto `retry_transient` then or deleted with the rest of
the tree, whichever DEV-139 decides; DEV-69's Finnhub fetcher needs
`Retry-After` pacing for a source that behaves differently from SEC EDGAR,
at which point 429 handling becomes source-specific rather than a shared
policy.
