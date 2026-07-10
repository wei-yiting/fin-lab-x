# Architecture Decision Records

Append-only log of non-obvious decisions (envelope §4). One entry per decision, ≤100 words:
what was chosen, rejected alternatives, why. Where a decision deliberately reduces robustness
below production norms, cite the envelope section per §9. Entries are never edited after the
fact — a reversed decision gets a new entry that supersedes the old one by number.

Template:

```markdown
## ADR-NNN: <title> (YYYY-MM-DD)
**Decision**: <what was chosen>
**Rejected**: <alternatives and the one-line reason each lost>
**Why**: <the deciding constraint or evidence>
```

---

## ADR-001: Adopt the Design Envelope as calibration SSOT (2026-07-10)

**Decision**: every design, implementation, and review decision cites `docs/design-envelope.md`
by section number; robustness beyond the envelope (over-engineering) and shortcuts inside its
§4 zones (under-engineering) are symmetric Major review findings.

**Rejected**: per-review ad-hoc judgment — produced the July 2026 audit findings (~8–10k
removable lines across worktrees and main); rules embedded only in agent skill prompts —
invisible to non-Claude tools and to human reviewers.

**Why**: reviewers on both sides of a disagreement need one written standard they can cite;
depth belongs in the differentiating zones, not spread uniformly.

## ADR-002: The envelope stops at invariants + machinery ceilings; protocols live in slices (2026-07-10)

**Decision**: `design-envelope.md` states *what must hold* (invariants, quality bars) and *what
machinery tier is sanctioned* — never step-by-step protocols. Concrete mechanisms (e.g. the JIT
ingest sequence) are designed and proven in the implementing slice.

**Rejected**: keeping the guard→wipe→ingest→mark protocol in §2 — six adversarial-review rounds
each attacked protocol correctness, and each fix added more mechanism, dragging a calibration
document into implementation design.

**Why**: a protocol inside a policy document invites counterexample attacks and duplicates the
slice's design; invariants + ceilings close reverse-citation loopholes without owning the proof.
