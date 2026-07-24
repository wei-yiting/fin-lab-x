# ADR-0005: Runtime tracing unifies on Braintrust, replacing Langfuse (2026-07-24)

**Decision**: Migrate all runtime tracing in `backend/agent_engine` from Langfuse to
Braintrust, making Braintrust the single observability platform for both the eval track
(already there) and runtime traces. Decided via the DEV-111 grilling session; technical
feasibility proven by the DEV-100 POC (all streaming-observability gates PASS, evidence in
`scripts/poc_braintrust_tracing/NOTES.md` on `experiment/braintrust-tracing-poc` @ `06cbd6a`).

**Rejected**: staying on Langfuse. Its only argument was inertia — the two structural pain
points (`_runs` private-dict dependency, the HQ-17 `update_current_generation()` silent no-op)
had already been designed away by the F7 final shape, so "current state isn't painful" was
true but not a value argument.

**Why** (three real, verified reasons):

1. **Curated trace archival is the actual motive** — not platform-side long retention. The
   need: keep selected failure traces (and their successful counterparts) permanently, and
   re-upload them for side-by-side analysis. `bt sync pull/push` is an official, standard CLI
   round-trip; Langfuse can export but re-import requires a self-maintained script. No cron is
   needed — archival is event-driven, per trace worth keeping.
2. **Platform unification**: the eval track (Quality Track, Evaluation Runs) already lives on
   Braintrust. One platform means one annotation surface, one API key, one mental model — and
   this project's stated value is evaluation rigor and observability.
3. **F7 lands in its natural shape**: trace-level reasoning persistence is ~15 lines inside the
   streaming wrapper on Braintrust (root-span handle held by the request wrapper, public API
   only) vs a ~229-line callback with private-attribute workarounds on Langfuse.

**Consequences / accepted trade-offs**:

- **Retention drops 30 → 14 days** on the free tier. Accepted: archival is event-driven, and
  the issue-sync checklist gains a step — "any trace worth archiving from this session? Pull it
  now into `data/trace-archives/`" — so the window never depends on memory alone. The archive
  lives under `data/` (it is data, not prose); runtime outputs under `data/` are individually
  gitignored, curated assets like the archive are tracked by default.
- **Quota**: free tier is 1 GB/month processed data, shared with the eval track. Estimated
  heavy-dev usage is 100–200 MB/month (~5x headroom); overage stops ingestion (no billing).
  No pre-emptive payload engineering beyond the ingestion-sampling already in migration scope.
- **Annotation loop write-off**: the unmerged, never-run Langfuse annotation code (~561 lines
  on `feat/v1-eval-experiment-pipeline`) is sunk cost. Braintrust parity confirmed
  (`project_scores` API + human review + BTQL for the export join); the reviewer score schema
  itself is platform-neutral and carries over. Zero annotation data existed to migrate.
- **Version prerequisite**: braintrust 0.11 → ≥0.30, and the deprecated `braintrust-langchain`
  package is removed (`braintrust.integrations.langchain` replaces it).
- **DEV-107 sequencing**: DEV-107 still ships its Langfuse version (deliberately slimmed —
  smoke-level verify, no gold-plated tests) to keep the DEV-105 stacked-PR train's F7 slice
  complete; the migration slice runs immediately after the train merges. Bounded rework
  (hundreds of lines + one re-verify) is the accepted insurance premium for a clean train.
- **Guardrails Rule 1** ("Langfuse is the default backend") flips to Braintrust in the
  migration slice PR — docs and code change state in the same commit, never before.

**Re-evaluate if**: monthly processed data exceeds ~50% of quota and Pro pricing ($3/GB,
30-day retention) is unacceptable; Braintrust removes or materially degrades `bt sync` or the
free tier; or multi-reviewer annotation needs outgrow Braintrust human review.
