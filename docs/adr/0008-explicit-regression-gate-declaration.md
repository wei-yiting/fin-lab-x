# ADR-0008: Explicit regression gate declaration in eval specs (2026-07-28)

**Decision**: Every `eval_spec.yaml` must carry `regression.enabled: true|false` —
required, no default, no `status: draft` exemption. Per-scorer gate fields default to
the strictest values: `gate: true`, `metric_floor: 1.0`. An explicit `metric_floor` on
a `gate: false` scorer is a schema error. A gated scorer producing no scores across the
whole dataset fails the gate regardless of cause (all-errored and all-skipped alike);
partial skips don't trigger. Contract declared by DEV-117; verdict enforced by DEV-118.

**Rejected**:

- **Defaulting `enabled`** — `true` forces immature scenarios red, `false` silently
  excludes mature ones; no direction is safe, so "forgot to decide" must be a load error.
- **Draft exemption** — `status: draft` answers "are the metrics trustworthy?",
  `enabled` answers "does this gate merges?". Folding them means whoever removes
  `draft` is never forced to decide the gate.
- **`min_score` naming** — the gated value is a dataset-level metric (recall, MRR,
  pass rate), not a per-case score; `min_score` misreads as per-case must-pass.
- **Passing an all-skipped scorer** — a guard that skipped every case went inert
  silently; same disease as a crashed scorer (DEV-120's judge outage sat unnoticed for
  months behind exit 0). No `on_empty` knob — `gate: false` is the escape hatch.

**Why**: required where no default is safe; defaulted where the default is the
strictest value — omission can only tighten the gate, never open a hole.

**Re-evaluate if**: scenario count makes per-spec declaration real friction, or the
gate gains per-case semantics (reopens the floor naming).
