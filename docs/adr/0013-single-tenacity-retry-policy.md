# ADR-0013: Single tenacity retry policy (2026-08-06)

**Decision**: `backend/common/retry.py` defines `retry_transient`, the one
shared retry decorator: `retry_if_exception_type(TransientError)` (from the
ADR-0012 taxonomy) + `stop_after_attempt(2)` — single retry, conforming to
design-envelope §2 — + `wait_exponential_jitter()` + `before_sleep_log` +
`reraise=True`. Deleted with it: the dead-code
`fundamentals_pipeline/retry.py` (zero production callers) and
`embed_sec_filings.py`'s outer retry loop, which retried permanent errors,
stacked 3×3=9 attempts on top of the SEC pipeline's inner retry, and
mislabeled failures as `"skipped"`. Ships in the same slice as ADR-0011 and
ADR-0012 (shared root cause: one convention reimplemented in mutually unaware
places).

**§2 reconciliation (429 stays fail-fast)**: envelope §2 requires
429/`Retry-After` honored with bounded backoff "implemented once in the
shared client layer" — for EDGAR that layer is edgartools itself, whose
internal exponential backoff runs *before* any 429 reaches our code (pinned
by `test_fetch_filing_obj_429_raises_rate_limit_error_immediately` in
`backend/tests/common/test_sec_core.py`). Adding a second wait at our layer
would be exactly the "other backoff ladder" §2 forbids and the double-retry
stacking this slice removed elsewhere. Finnhub's `Retry-After` honoring is
DEV-69's chartered work on this same helper. So `RateLimitError` stays out of
the retry list.

**§0 reachability ratification**: `retry_transient` has no production caller
at this slice's merge — a deliberate, time-boxed exception to envelope §0,
sanctioned by the repo owner (2026-08-06). DEV-137 is recorded `blockedBy`
DEV-141 in Linear precisely so it lands next and becomes the first caller;
DEV-137 and DEV-69 both carry written notes that if they end up not using it
and nothing else does, it must be removed.

**Testing-seam note (SP-1.2)**: the DEV-141 Testing Decisions originally
routed retry coverage through existing seams (`process()`/`main()`); the
frozen-tree scope correction made `retry_transient` unreachable through those
seams this slice, so a direct unit-test seam
(`backend/tests/common/test_retry.py`) is authorized as a second new seam —
recorded as a dated correction on the DEV-141 issue.

**Rejected — `Retry-After`-aware pacing at our layer**: see the §2
reconciliation above — the shared client layer already owns it.

**Rejected — migrating the frozen tree's hand-rolled loop**
(`sec_filing_pipeline_html/pipeline.py`'s `_execute_with_retry`): the tree
dies at the DEV-139 sunset, so refactoring its retry internals now is work
thrown away.

**Re-evaluate if**: DEV-139 sunsets the frozen tree (its loop migrates onto
`retry_transient` or dies with the tree); DEV-69 needs source-specific 429
handling, at which point 429 policy becomes per-source rather than shared.
