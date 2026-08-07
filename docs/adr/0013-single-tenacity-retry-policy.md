# ADR-0013: Single tenacity retry policy (2026-08-06)

**Decision**: All retry behavior goes through `retry_transient`
(`backend/common/retry.py`): it retries `TransientError` only (from the
ADR-0012 taxonomy), 2 total attempts (single retry, envelope §2),
exponential backoff + jitter, and re-raises the original exception. New
fetchers and pipelines apply this decorator — never a hand-rolled retry
loop. Permanent errors and `RateLimitError` never enter the retry list.
429 handling is per-source per envelope §2: for EDGAR the pre-emptive
throttle lives in the edgartools client (8 req/s, under SEC's 10 req/s
cap), and a 429 (≈10-minute IP block; retrying extends it) fails fast
with `retry_after` surfaced; for Finnhub, one bounded `Retry-After`
backoff is DEV-69's chartered extension of this same helper.

**Context**: three unrelated hand-rolled retry implementations had
diverged — one retried permanent failures and stacked on an inner retry.
One declarative policy replaces them.

**Governance exception**: `retry_transient` has no production caller at
this slice's merge — a time-boxed envelope §0 exception sanctioned by the
repo owner. DEV-137 (blockedBy this slice) is the designated first
consumer; DEV-137/DEV-69 carry removal conditions if it ends up unused.
Its direct unit-test seam is authorized by a dated correction on DEV-141.

**Rejected — `Retry-After` pacing at this layer for EDGAR**: vendor
semantics make it harmful (a SEC 429 is a block, and waiting-then-retrying
extends it); a second wait would also stack on the client layer — the
exact pattern this decision removes.

**Rejected — migrating the frozen `_html` tree's own retry loop**: that
tree dies at the DEV-139 sunset; it keeps its local 3-attempt behavior
until then — do not migrate it.

**Re-evaluate if**: DEV-139 sunsets the frozen tree; DEV-69 finds source
semantics the per-source rule doesn't cover.
