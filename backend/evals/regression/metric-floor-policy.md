# Metric Floor Policy

How a `metric_floor` gets its number. Applies to every scenario with
`regression.enabled: true`; the gate mechanics themselves are governed by
ADR-0008 (declaration contract) and ADR-0015 (absence semantics).

## Derivation

Floors derive from a recorded **reference measurement** (see `CONTEXT.md`),
never from aspirational targets:

```
metric_floor = measured value − 0.20, rounded down to the nearest 0.05
```

- The margin is deliberately wide: floors catch **collapse**, not slow
  erosion — erosion is the Quality Track's job. A tight floor turns normal
  measurement jitter into false reds, which teaches people to distrust the
  gate. Observed jitter on a 10-row dataset: re-embedding the same filing
  moves rank metrics (MRR/MAP) by ±0.25–0.5 per case from near-tie chunk
  reordering alone.
- If the formula yields ≤ 0.20 for a metric, stop and flag it instead of
  applying it mechanically — that metric has no signal on this dataset.

## Measurement count

- **Draft / placeholder dataset**: one run. Multiple runs cannot separate
  signal from dataset noise at that quality level.
- **Curated dataset**: three runs, take the minimum per metric.

## Gate membership

All scorers are gated by default (no `gate:` keys written — the schema
default is already `true`). Rank metrics stay gated alongside recall: they
catch ranking collapse (right chunks retrieved but sunk below the top
positions), which recall@K cannot see. Exclude a scorer only with evidence
that it is noise-dominated on the current dataset, and record why.

## Recording obligations

Every reference measurement is recorded under
`reference_measurements/<scenario>/` as a dated pair:

- `<YYYY-MM-DD>_<git-sha>.md` — what was measured: dataset version and
  provenance, retriever/pipeline and collection (with point count), model,
  per-scorer measured value → floor derivation, per-case results, and the
  expiry conditions (what event invalidates these floors and which issue
  re-derives them).
- `<YYYY-MM-DD>_<git-sha>.csv` — the raw per-case run, curated from the
  gitignored `backend/evals/results/` (the "run worth keeping" pattern from
  the `CONTEXT.md` Eval run entry).

## Re-derivation

A floor is invalidated — never adjusted in place — by any change to what it
measured: retriever/pipeline cutover, dataset replacement, or embedding
model change. Re-measure and add a **new** record pair; old records stay as
history.
