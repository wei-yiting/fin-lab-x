# ADR-0009: One-page soft target replaces the 100-word ADR cap (2026-08-05)

**Decision**: Envelope §4's "≤100 words" clause for ADRs is replaced by: every
ADR opens with a 1–2 sentence decision statement and targets one page (~500
words); overflow triggers a structural test — two fused decisions are split,
design detail is linked out — before any compression of rationale; with
reviewer judgment, a wicked problem (argued trade-offs across ≥2 real options)
may exceed the target.

**Context**: the old cap was internally contradictory — it demanded Nygard-era
length while requiring MADR-era content (rejected alternatives + why), and
Nygard's template is short precisely because it has no alternatives section.
An industry survey (`artifacts/current/research_adr_length_regulation.md`,
branch history; 16 primary sources, per-claim URLs) found **zero** primary
sources using a hard word cap: the canon regulates scope (one decision per
record, link out design detail) and skimmability (decision statement up
front), never substance. This repo's log had already outgrown the cap
systematically (ADR-0005 onward: 541–751 words), and the overflow content was
exactly the argued alternatives the cap's own content requirement demands.
Existing ADRs are not rewritten (entries are never edited after the fact);
all are legal under the new rule. This ADR supersedes nothing — the cap lived
in the envelope text, not in any ADR.

**Rejected — Y-statement TL;DR** (survey candidate C): best skim experience of
the surveyed formats, but the six-clause sentence takes practice to write well
and duplicates content between TL;DR and body; a free-form 1–2 sentence
decision statement buys the same skimmability at lower ceremony.

**Rejected — MADR two-tier template** (survey candidate D): most faithful to
the strongest template lineage and would legitimize both the short and long
existing ADRs, but imposes a tier-choice judgment call per record plus MADR
headings on a free-form log that already works. Reconsider only if ADR
quality degrades under the soft target.

**Why**: the cap regulated the wrong variable. A length rule protects
skimmability of the decision log and scope discipline per record — both
survive under the soft target — while the substance the cap destroyed (the
"why not" behind each rejected alternative) is the content every surveyed
source treats as the part still useful years later. **Reopen when** ADRs
routinely blow past a page without triggering the split/link-out test, or
when the PR reviewer gate stops holding the line.
