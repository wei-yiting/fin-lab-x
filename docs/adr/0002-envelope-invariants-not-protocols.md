# ADR-0002: The envelope stops at invariants + machinery ceilings; protocols live in slices (2026-07-10)

**Decision**: `design-envelope.md` states *what must hold* (invariants, quality bars) and *what
machinery tier is sanctioned* — never step-by-step protocols. Concrete mechanisms (e.g. the JIT
ingest sequence) are designed and proven in the implementing slice.

**Rejected**: keeping the guard→wipe→ingest→mark protocol in §2 — six adversarial-review rounds
each attacked protocol correctness, and each fix added more mechanism, dragging a calibration
document into implementation design.

**Why**: a protocol inside a policy document invites counterexample attacks and duplicates the
slice's design; invariants + ceilings close reverse-citation loopholes without owning the proof.
