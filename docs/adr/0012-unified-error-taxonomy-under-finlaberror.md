# ADR-0012: Unified error taxonomy under FinLabError (2026-08-06)

**Decision**: `FinLabError` (`backend/common/errors.py`) is the root of
the shared taxonomy. `TransientError`, `TickerNotFoundError`,
`ConfigurationError`, and `RateLimitError` are defined exactly once
there and subclass it directly. Subsystem bases (`SECError`,
`FundamentalsPipelineError`) subclass `FinLabError` and hold only
subsystem-specific errors. Rules going forward:

- Never redefine a shared error class inside a subsystem.
- Rate-limit failures are `RateLimitError` — never a `TransientError`
  subclass, because they must not enter the retry path (ADR-0013).
- Handler layers that want "any expected failure in the shared
  taxonomy" catch `FinLabError`. (Error families outside it — e.g. the
  JIT retriever's local classes — are not covered; see Re-evaluate.)
- A new subsystem adds its own base under `FinLabError` with only its
  own errors.

**Context**: the same class names existed as two unrelated hierarchies
in two subsystems, so an `except` written against one silently never
matched the other's instances.

**Rejected — alias re-export** (keep both definitions, point one at the
other): preserves two names for one concept — the exact ambiguity that
caused the incident.

**Rejected — multiple-inheritance bridge** (shared classes inheriting
every subsystem base): couples subsystem bases that have no business
knowing about each other, and MRO ambiguity grows with each new
subsystem.

**Re-evaluate if**: the JIT retriever's local error families (currently
plain `Exception` subclasses, out of scope here) are folded in.
