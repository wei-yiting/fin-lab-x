# sec_retrieval Metric Floors — Decision Record

How the current `metric_floor` values in
`backend/evals/scenarios/sec_retrieval/eval_spec.yaml` were decided. This
documents the floor decision for this scenario only — it is not a repo-wide
policy. Other enabled scenarios (e.g. `language_policy`) simply take
ADR-0008's strict default `metric_floor: 1.0`, a contract default with no
measurement involved. Gate mechanics are governed by ADR-0008 (declaration
contract) and ADR-0016 (absence semantics).

## Why measured floors instead of the strict default

`sec_retrieval`'s metrics (recall/MRR/MAP) measure degrees of quality, not
correctness — a `1.0` default would be meaningless. The floors were instead
derived from a recorded **reference measurement** (see `CONTEXT.md`), never
from aspirational targets.

## Derivation

```
metric_floor = measured value − 0.20, rounded down to the nearest 0.05
```

- The margin was chosen deliberately wide: floors catch **collapse**, not
  slow erosion — erosion is the Quality Track's job. A tight floor turns
  normal measurement jitter into false reds, which teaches people to
  distrust the gate. Observed jitter on the 10-row dataset: re-embedding
  the same filing moves rank metrics (MRR/MAP) by ±0.25–0.5 per case from
  near-tie chunk reordering alone.
- Had the formula yielded ≤ 0.20 for a metric, the plan was to stop and
  flag it instead of applying it mechanically — that metric would have no
  signal on this dataset. (It did not fire for any of the four metrics.)

## Measurement count

This measurement was one run: on the placeholder dataset, multiple runs
cannot separate signal from dataset noise. For the next re-derivation
(DEV-164, curated dataset), the recorded recommendation is three runs,
taking the minimum per metric.

## Gate membership

All four scorers are gated (no `gate:` keys written — the schema default is
already `true`). Rank metrics stay gated alongside recall: they catch
ranking collapse (right chunks retrieved but sunk below the top positions),
which recall@K cannot see.

## Expiry and re-derivation

These floors are invalidated — never adjusted in place — by any change to
what they measured: retriever/pipeline cutover, dataset replacement, or
embedding model change. Re-derivation means a new measurement and a new
record pair under `reference_measurements/sec_retrieval/`; a multi-run
re-measurement's record documents all runs and the per-metric minimum used
for derivation. Old records stay as history.
