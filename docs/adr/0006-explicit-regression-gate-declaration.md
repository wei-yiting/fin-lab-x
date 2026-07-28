# ADR-0006: Explicit regression gate declaration in eval specs (2026-07-28)

**Decision**: Every scenario's `eval_spec.yaml` must carry a `regression` block with an
explicit `enabled: true|false` — unconditionally required, with no exemption for
`status: draft` scenarios. Per-scorer gate fields are optional with fail-safe defaults:
`gate` defaults to `true` (counted in the gate) and `metric_floor` defaults to `1.0`
(for binary scorers, per-case must-pass). Declaring an explicit `metric_floor` on a
scorer with `gate: false` is a schema error. A gated scorer that produces no scores at
all over the dataset fails the gate, with no distinction by cause — every case erroring
and every case deliberately skipping are both red. Decided via the DEV-117 grilling
session; the gate itself is consumed by the Regression Suite runner (DEV-118), which
implements the verdict rules stated here.

**Rejected**:

- **Defaulting `regression.enabled`** (either direction). Default `true` forces immature
  scenarios red; default `false` silently excludes mature ones. Both directions are wrong
  for some scenario, so there is no safe default — the field must be stated. "Forgot to
  decide" becomes a load error instead of a silent state.
- **Exempting `status: draft` scenarios from the block**. `draft` answers "are this
  dataset's metrics trustworthy?" (a warning banner for humans); `regression.enabled`
  answers "does this scenario gate merges?" (a contract for the runner). Folding one into
  the other re-creates the silent state at the end of the lifecycle: whoever removes
  `draft` would never be forced to answer the gate question. The two axes stay orthogonal,
  with no cross-validation between them.
- **`min_score` as the floor field name**. A scorer's output is a metric — recall, MRR,
  pass rate — not a "score", and the gated value is the dataset-level aggregate, not a
  per-case minimum. `min_score` reads as per-case must-pass, which only coincidentally
  matches for binary scorers at floor 1.0; on a continuous metric with floor 0.7 the
  misreading hides real per-case failures. Named `metric_floor` (see CONTEXT.md).
- **Splitting the empty-metric verdict by cause** — failing an all-errored scorer while
  passing an all-skipped one. Skips look benign because they are a designed path (a scorer
  returns no score when the case makes no claim on it), but a gated scorer that skipped
  every case means the dataset stopped asserting anything through it: the guard went inert
  without a word. That is the same silent-hole failure as a crashed scorer, so the verdict
  is the same. The failure message names the cause; the verdict does not depend on it.
- **A per-scorer knob for empty-metric behavior** (`on_empty: fail|pass`). A scorer that
  may legitimately produce nothing already has an escape hatch — `gate: false`. A second
  mechanism for the same intent is a knob nobody needs (design-envelope §7).

**Why**:

1. **Required where no default is safe, defaulted where the default is the strictest
   value.** Scenario-level membership has no fail-safe default (see Rejected), so it is
   required. Scorer-level fields default to the most protective interpretation — counted,
   floor 1.0 — so an omission can only make the gate stricter, never open a hole. Same
   philosophy (no silent holes), two mechanisms.
2. **Dead config is the same disease as silent defaults.** A `metric_floor` on an ungated
   scorer reads as protection but does nothing; rejecting the combination costs one
   validator and keeps every line of a spec meaningful.
3. **An empty metric cannot support the gate's conclusion.** The gate answers "did
   existing behavior get worse"; a scorer that measured nothing gives no grounds to say
   no. Passing it makes a broken or inert guard permanently invisible — which is exactly
   how DEV-120's LLM-judge outage (every case throwing `AuthenticationError`, the run
   still exiting 0) survived three and a half months unnoticed.
4. **The lifecycle has a designated owner for each flip.** sec_retrieval ships
   `enabled: false` with a rationale comment; the flip to `true` (with measured floors)
   belongs to DEV-103. The required block is what makes that handoff visible in the asset
   instead of in someone's memory.

**Consequences / accepted trade-offs**:

- The `regression` block is required, so adding it is not purely additive for spec files:
  both pre-existing scenario specs gain the block in the same slice that introduces the
  schema requirement (language_policy `enabled: true`, sec_retrieval `enabled: false`).
  Engine code (`eval_runner`, scorer registry, dataset loading) is untouched.
- Every future scenario must state its gate membership before it loads, including
  throwaway or experimental ones — the cost of writing two lines is accepted as the price
  of making "not in the gate" always an explicit statement.
- `metric_floor` values are trusted declarations; nothing verifies them against measured
  baselines. The convention (measure, then set the floor with margin — DEV-103's
  procedure) is process, not schema.
- The empty-metric rule is stated here but enforced downstream: DEV-117 carries only the
  schema, DEV-118's gate evaluator implements the verdict. Until DEV-118 ships, a
  scorer-wide outage still exits 0 — the rule is a contract, not yet a mechanism.
- A gated scorer whose dataset legitimately makes no claim on some cases stays green as
  long as at least one case scores; the rule triggers only on a fully empty metric. Partial
  skew (7 of 8 cases skipping) is invisible to the gate — accepted, since a dataset that
  thin is a curation problem, not a regression signal.

**Re-evaluate if**: the number of scenarios grows to where per-spec declaration is real
friction and a central gate manifest becomes simpler; or the Regression Suite gains
per-case (not aggregate) gating semantics, which would reopen the floor-naming question.
