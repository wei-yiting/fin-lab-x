# ADR-0012: Unified error taxonomy under FinLabError (2026-08-06)

**Decision**: `backend/common/errors.py` defines `FinLabError` as the
top-level base plus the four cross-subsystem error classes —
`TransientError`, `TickerNotFoundError`, `ConfigurationError`,
`RateLimitError` — exactly once, each inheriting `FinLabError` directly.
Subsystem bases `SECError(FinLabError)` and
`FundamentalsPipelineError(FinLabError)` keep only errors specific to their
own subsystem. Four broad `except SECError` / `isinstance(..., SECError)`
handlers widen to `FinLabError` so a class migrating between subsystems can't
silently stop matching. The `RateLimitError` constructor is genericized
(`source: str` instead of a baked-in "SEC EDGAR {ticker}" message) so
DEV-69's Finnhub 429 handling can reuse it. Ships in the same slice as
ADR-0011 (repo-anchored paths) and ADR-0013 (shared retry policy) — one root
cause, one convention reimplemented in places that don't know about each
other. The shared retry decorator (ADR-0013) keys off this taxonomy's
`TransientError`.

**Context**: the same three class names previously had two independent,
unrelated definitions in two subsystems — an `except TransientError` written
against one definition silently never matched instances raised by the other.
The 7/6 audit's C3 incident was exactly this shape: a handler that looked
correct in review and did nothing at runtime.

**Frozen-tree note**: the `_html` baseline tree (frozen as the A/B baseline
per AGENTS.md "Ingestion Rewrite Coexistence") receives only the minimal
handler-widening lines — its two `except SECError` sites widen to
`FinLabError` so its re-raised errors keep matching. Everything else there is
untouched; its retry internals migrate or die with the DEV-139 sunset.

**Rejected — alias re-export** (keep both definitions, point one at the
other via `X = other_module.X`): preserves two names for one concept — the
exact ambiguity that caused the 7/6 incident. A grep for "is this defined
once" would still return two hits.

**Rejected — multiple-inheritance bridge**
(`class TransientError(SECError, FundamentalsPipelineError)`): couples two
subsystem bases that have no business knowing about each other, and MRO
ambiguity grows with every new subsystem that wants in.

**Escape hatch**: the taxonomy is one module. Adding a cross-subsystem class
or demoting one back to a subsystem is a one-file edit plus the handlers a
grep for the class name finds.

**Re-evaluate if**: a third subsystem needs error semantics the four shared
classes can't express, at which point the shared/local split line gets
redrawn deliberately rather than by accretion.
