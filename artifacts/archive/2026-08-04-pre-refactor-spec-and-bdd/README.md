# Archive: pre-refactor spec & BDD suite (archived 2026-08-04, DEV-108)

Full planning/design/BDD artifact set for the **pre-refactor** multi-provider
streaming design — the 19-state ephemeral reasoning indicator, custom transient
SSE channel + sentence segmenter, and per-LLM-call Langfuse `metadata.reasoning`
writes.

**Superseded by** the 2026-07 refactor ruling chain:

- ADR-0006 — reasoning as collapsed transcript chips (replaces the ephemeral
  indicator model)
- ADR-0007 — trace-level reasoning transcript on a self-owned root span
  (replaces per-call Langfuse writes)
- Linear DEV-105 (refactor spec, incl. F5/F6′/F7 implementation decisions and
  the 2026-07-26 errata comments) and its tickets DEV-106 / DEV-107

The replacement `bdd-scenarios.md` / `verification-plan.md` in
`artifacts/current/` were re-drafted clean-room from those sources only
(DEV-108). Decision-chain provenance for the DEV-84 cascade-cost case study
lives in Linear (DEV-84 / DEV-105); this archive is the unmodified original
text — deliberately left without superseded annotations (DEV-108 ruling
2026-08-02: archiving *is* the preservation mechanism).

Note: `bdd-scenarios.md` / `verification-plan.md` here are the **2026-07-24
DEV-106-era revisions** (already chips/native-parts-aware but pre-F7); the
untouched pre-DEV-106 originals live in
`archive/2026-07-24-pre-dev106-ephemeral-indicator/`.

Tracked in git temporarily for work-state safety; untracked before the PR
(net diff must not contain artifacts).
