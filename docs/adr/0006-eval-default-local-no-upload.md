# ADR-0006: Eval runner defaults to local-only; Braintrust upload is opt-in (2026-07-28)

**Decision**: `braintrust.Eval()` becomes the eval runner's sole executor — the
prior "run a homegrown local loop, then run `Eval()` again for the platform"
dual path (every task function call happened twice) is gone. `Eval()` always
executes locally and computes scores; `no_send_logs=True` by default means no
network call, no experiment created, zero Braintrust quota spent, no API key
required. A new `--upload` flag flips `no_send_logs=False` to create a real
Braintrust experiment for that run; `--local-only` is removed with no
no-op alias. The result CSV, written directly from `Eval()`'s returned result
object, is the one permanent record in git (see `CONTEXT.md`'s **Eval run**
definition); an uploaded experiment is a 14-day-retention convenience layer
for diff/drill-down on top of it. If a local run ever needs retroactive
upload, `experiment.log()` is the mechanism — already verified workable — so
no bespoke backfill tool is built ahead of a real need.

**Rejected — auto-fallback dual path** (try upload, silently fall back to
local on failure): reintroduces the exact masked-failure problem this refactor
removes. An explicit `--upload` intent that silently downgrades to local-only
hides an infrastructure problem (bad key, network) behind a quiet success —
the accepted trade-off is a hard, non-zero-exit failure instead (grilling
Q5).

**Rejected — keep running both local eval and Braintrust `Eval()` per
invocation** (status quo before this issue): every task function call
happened twice per row, doubling LLM cost and latency on every
quality-iteration loop, for a redundant local execution whose only reason to
exist predated `Eval()` returning a per-row result object the CSV writer can
consume directly.

**Rejected — default to upload** (proposed and rejected once on 2026-07-20,
re-litigated and rejected again on 2026-07-26): would spend Braintrust
free-tier quota — shared with runtime tracing since ADR-0005 — on every
dev-loop iteration, require `BRAINTRUST_API_KEY` just to run an eval locally,
and pollute the Quality Track experiment list with throwaway dev-loop runs
never meant for comparison.

**Why**:

1. **The result CSV is already the durable artifact.** It is git-tracked with
   no retention window; an upload buys drill-down/diff convenience on top of
   it, not the permanent record itself. Defaulting to upload would spend
   quota for a benefit the primary artifact doesn't depend on.
2. **The local dev loop shouldn't need an API key.** Verified against
   braintrust 0.11.0 source and confirmed empirically: `no_send_logs=True`
   skips `init_experiment` entirely (`if not no_send_logs and parent is
   None: ...`), so `Eval()` never touches the network or requires
   credentials in the default path.
3. **Explicit intent stays honest.** `--upload` failing hard (non-zero exit,
   no silent downgrade) means a broken upload is always visible at the
   command line that asked for it, never discovered later as "huh, this
   experiment never showed up."

**Consequences / accepted trade-offs**:

- Comparing two local runs side-by-side in the Braintrust UI requires
  re-running with `--upload` (or a future `experiment.log()` backfill) —
  accepted, since routine quality-iteration already works from the CSV.
- `--upload` with a missing/invalid key surfaces as a preflight `RuntimeError`
  (missing key) or an exception from `Eval()`'s own `init_experiment` call
  (invalid key) — both propagate uncaught, by design.

**Re-evaluate if**: the quality-iteration workflow needs routine cross-run
comparison badly enough that the extra `--upload` keystroke becomes real
friction, or the Braintrust free tier changes such that opt-in upload no
longer meaningfully protects quota.
