# ADR-0016: Partial-absence semantics in the regression gate (2026-08-12)

**Decision**: A gated scorer's verdict aggregate is computed over the cases that produced a
score: deliberate skips (`Score(score=None)`) and per-case scorer errors leave the
denominator, and both appear as counts in the verdict detail. Two absences are red regardless
of aggregates: any task crash (a case whose task function errored, leaving every scorer
absent) fails the gate, and a scenario declaring `regression.enabled: true` with no gated
scorer fails as a configuration contradiction. Fully-empty metrics stay red per ADR-0008.

**Rejected**:

- **Excluding crashed cases from the denominator** — the agent failing on the production
  streaming path is itself the regression; 7/8 perfect scores would report green over a
  crash (DEV-120's silent exit 0, one level up).
- **Failing on any scorer error** — an occasional judge API error would flake the gate red;
  a red light that cries wolf stops gating merges. A scorer error is instrument failure,
  not subject failure — until the instrument produces nothing at all (ADR-0008).
- **Passing the zero-gated-scorer scenario** — `enabled: true` with no gated scorer wears
  the gate badge with no guard behind it; inert by construction, the same disease ADR-0008
  rejects at the scorer level.

**Why**: subject failure (task crash) is signal; instrument failure (scorer error) is noise —
but when noise removes all evidence, "no regression" can no longer be supported. All three
rules are corollaries of that one sentence.

**Re-evaluate if**: transient infrastructure crashes (not agent bugs) start flaking the
task-crash rule, or the gate gains per-case semantics.
