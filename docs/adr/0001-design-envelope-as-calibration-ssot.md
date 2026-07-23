# ADR-0001: Adopt the Design Envelope as calibration SSOT (2026-07-10)

**Decision**: every design, implementation, and review decision cites `docs/design-envelope.md`
by section number; robustness beyond the envelope (over-engineering) and shortcuts inside its
§4 zones (under-engineering) are symmetric Major review findings.

**Rejected**: per-review ad-hoc judgment — produced the July 2026 audit findings (~8–10k
removable lines across worktrees and main); rules embedded only in agent skill prompts —
invisible to non-Claude tools and to human reviewers.

**Why**: reviewers on both sides of a disagreement need one written standard they can cite;
depth belongs in the differentiating zones, not spread uniformly.
