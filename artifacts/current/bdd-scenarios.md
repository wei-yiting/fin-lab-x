# BDD Scenarios

## Meta
- Design Reference: `artifacts/current/design.md`
- Generated: 2026-04-24
- Discovery Method: Three Amigos (Agent Teams — PO / Dev / QA, 3 challenge rounds)
- Scope: v1 workflow integrity per design §14 (selector correctness, metadata integrity, workflow viability); NOT LLM response quality or auto-scoring.

## NUI Assumptions Applied (auto-resolved from Round 3; user may course-correct)
| # | Topic | Assumption |
|---|---|---|
| 1 | `row_ids` validation mode | always fail-fast, no `--ignore-missing` opt-in |
| 2 | Duplicate row_ids in list | rejected pre-flight with `duplicate_row_ids` error |
| 3 | Silent row mutation within same `dataset_version` | not actively detected; pipeline trusts version label |
| 4 | Manifest grammar | integers only, one per line; `#` comments + blank lines ignored; ranges/hex/quoted rejected |
| 5 | `run_label` canonical form | `[a-z0-9_-]{1,64}`; non-canonical rejected at input |
| 6 | `agent_version` fingerprint on editable install | Operator-trusted; no `+dirty` detection; `git_commit` captures refinement |
| 7 | `run_label` collision handling | reject always; no `--force-new-suffix` |
| 8 | `--replace-incomplete` flag | out of scope v1; Operator uses a new label after crash |
| 9 | `observed_secondary_failure_mechanism` without primary | permitted (§9.2 lists both as optional) |
| 10 | Run metadata source-of-truth | identity keys on Braintrust record + Langfuse trace; no sidecar file |
| 11 | Multi-reviewer per trace | out of scope v1; single reviewer assumed |
| 12 | Annotation-completeness enforcement location | export layer; UI re-surfacing deferred pending Langfuse verification |

Personas:
- **Operator** — runs the pipeline via CLI (eval_runner).
- **Reviewer** — annotates traces in the Langfuse Annotation Queue UI.
- **Analyst** — exports Langfuse scores and joins them to the dataset for discussion.

---

## Feature: Dataset Selection & Slice Identity

### Context
Pipeline supports four slice modes (`full_dataset`, `row_ids`, `field_filter`, `manifest`) that resolve an input selector into a deterministic row set + `slice_identity`. Every slice invocation is validated pre-flight before any Braintrust record or Langfuse trace is emitted.

### Rule: full_dataset slice selects every row in the current dataset_version and is reproducible across repeat runs on the same version

#### S-slice-01: Full run on a stable dataset_version is reproducible
> Verifies the base reproducibility guarantee for a full run.

- **Given** dataset `fin-lab_near-v1_diagnostic` has 30 rows on version `v1.0`
- **When** Operator runs `slice_type=full_dataset`, records `slice_hash=H1`, and reruns with no dataset edits
- **Then** both runs execute all 30 `id` values and the second run produces the same `slice_hash=H1`

Category: Illustrative
Origin: PO

#### S-slice-02: Full run on a bumped dataset_version produces a distinct slice_hash
> Verifies that dataset version is part of slice identity.

- **Given** a full run on dataset_version `v1.0` (30 rows) produced `slice_hash=H1`
- **When** the dataset version is bumped to `v1.1` (now 32 rows) and Operator runs `slice_type=full_dataset` again
- **Then** the second run's `slice_hash` is different from `H1` and the run record carries `dataset_version=v1.1`

Category: Illustrative
Origin: Dev

### Rule: row_ids slice executes only the listed ids; pre-flight validation rejects any unknown, duplicate, or empty input

#### S-slice-03: row_ids selects only the listed rows
- **Given** dataset `v1.0` with rows 1..30
- **When** Operator runs `slice_type=row_ids`, `slice_selector="3,7,12"`
- **Then** exactly rows 3, 7, 12 are executed; the remaining 27 rows are not executed

Category: Illustrative
Origin: PO

#### S-slice-04: Unknown row_id fails pre-flight with zero emissions
> Verifies atomic pre-flight — no orphan traces from partial execution.

- **Given** dataset `v1.0` with rows 1..30
- **When** Operator runs `slice_selector="3,7,999"` where `999` does not exist
- **Then** the run aborts pre-flight with `unknown_row_ids=[999]`; zero Braintrust records and zero Langfuse traces exist for this run

Category: Illustrative
Origin: Multiple (PO seeded; Dev sharpened atomicity)

#### S-slice-05: Duplicate row_id in the list is rejected
- **Given** dataset `v1.0` with rows 1..30
- **When** Operator runs `slice_selector="3,5,3,7"`
- **Then** the run aborts pre-flight with `duplicate_row_ids=[3]`; zero Braintrust records and zero Langfuse traces exist

Category: Illustrative
Origin: QA

#### S-slice-06: Empty row_ids list is rejected
- **Given** dataset `v1.0` with rows 1..30
- **When** Operator runs `slice_type=row_ids`, `slice_selector=""`
- **Then** the run aborts pre-flight with `empty_slice_forbidden`; the `run_label` namespace is not reserved

Category: Illustrative
Origin: QA

### Rule: field_filter slice is reproducible on a stable dataset_version; zero-match filters are rejected

#### S-slice-07: field_filter is reproducible on the same dataset_version
- **Given** dataset `v1.0` has some rows with `capability_band=boundary`
- **When** Operator runs `slice_selector="capability_band=boundary"` twice on `v1.0` with no dataset edits between runs
- **Then** both runs produce the same `selected_row_ids` and the same `slice_hash`

Category: Illustrative
Origin: PO

#### S-slice-08: field_filter matching zero rows is rejected
- **Given** dataset `v1.0` has no rows with `capability_band=nonexistent`
- **When** Operator runs `slice_selector="capability_band=nonexistent"`
- **Then** the run aborts pre-flight with `empty_slice_forbidden`; no `run_label` is reserved

Category: Illustrative
Origin: QA

### Rule: manifest slice accepts integers-only grammar and fails when referenced rows are missing

#### S-slice-09: manifest executes exactly the id-set regardless of text encoding
> Verifies hash is computed over parsed integer set, not file bytes.

- **Given** a manifest file listing `[2, 5, 9, 14, 22]`
- **When** Operator saves the same manifest as UTF-8 without BOM (LF) then re-saves as UTF-8 with BOM (CRLF) and runs both
- **Then** both runs execute exactly those 5 rows and produce the same `slice_hash`

Category: Illustrative
Origin: QA

#### S-slice-10: manifest unsupported syntax is rejected with a line reference
- **Given** a manifest file containing `1\n2\n# baseline failures\n\n  5\n3-7\n`
- **When** Operator runs `slice_type=manifest` pointing at this file
- **Then** rows 1, 2, 5 are parsed (blank + `#` lines ignored, whitespace trimmed) and the `3-7` line is rejected with `unsupported_manifest_syntax` naming the line number

Category: Illustrative
Origin: Multiple (QA + Dev — formal grammar)

#### S-slice-11: manifest referencing rows missing in the current dataset_version is rejected
- **Given** manifest `[2, 5, 9, 14, 22]` succeeded on dataset_version `v1.0`
- **When** the dataset bumps to `v1.1` which has removed row 14, and Operator reruns the same manifest
- **Then** the run aborts pre-flight with `manifest_row_missing` naming row 14; zero rows are executed

Category: Illustrative
Origin: Dev

---

### Journey Scenarios

#### J-slice-01: Operator performs a full run then a subset rerun with stable slice identity
> Proves the slice layer produces deterministic, distinguishable slice_identity across run modes.

- **Given** a fresh dataset_version `v1.0` and no prior runs
- **When** Operator runs `full_dataset`, then runs `row_ids="3,7,12"` with a new `run_label`, then reruns the same `row_ids` list
- **Then** the three runs produce three distinguishable `slice_identity` records; the two `row_ids` runs share the same `slice_hash` (same ids, same version)

Category: Journey
Origin: Multiple

---

## Feature: Braintrust Identity & Run Lifecycle

### Context
Each Braintrust case record carries identity keys per design §8.1. The pipeline enforces mandatory-key completeness and run_label uniqueness at the Braintrust boundary so that downstream joins (D1/G1) remain 1:1.

### Rule: Braintrust record carries all mandatory identity keys; missing mandatory key aborts the run

#### S-id-01: Full identity keyset is recorded on every case
- **Given** Operator runs `row_ids="7,12"` on dataset_version `v1.0` with `run_label=near-v1-2026-04-24-a`, `agent_version=near-v1.0.3`, `run_group=smoke`, `slice_label=bugfix-7-12`
- **When** execution completes
- **Then** both Braintrust records carry `row_id`, `dataset_name`, `dataset_version`, `run_label`, `run_group`, `slice_label`, `slice_type=row_ids`, `agent_version` populated with those exact values

Category: Illustrative
Origin: PO

#### S-id-02: Missing mandatory identity key aborts pre-flight
- **Given** pipeline invocation omits `agent_version` (a mandatory key per resolved NUI)
- **When** Operator launches the run
- **Then** the run aborts pre-flight with `missing_identity_key=[agent_version]`; zero records or traces exist

Category: Illustrative
Origin: PO

### Rule: run_label disambiguates runs of the same row; duplicate run_label is rejected at the Braintrust boundary

#### S-id-03: Different run_label produces two distinct records for the same row
- **Given** dataset_version `v1.0`
- **When** Operator runs `row_ids="7"` with `run_label=baseline`, then again with `run_label=after-fix`
- **Then** two distinct Braintrust records exist for `row_id=7`, differing only in `run_label`

Category: Illustrative
Origin: PO

#### S-id-04: Duplicate run_label is rejected at the Braintrust experiment boundary
> Verifies that uniqueness is enforced globally, not just locally.

- **Given** Operator A completed a run with `run_label=baseline` on dataset_version `v1.0` yesterday
- **When** Operator B (different machine, no shared local state) launches a new run with `run_label=baseline` on `v1.0` today
- **Then** Operator B's run is rejected at Braintrust init with `run_label_collision`; no new Braintrust record or Langfuse trace is emitted

Category: Illustrative
Origin: Dev

### Rule: run_label must match the canonical form — non-canonical input rejected at accept-time

#### S-id-05: Non-canonical run_label is rejected at input
> Separates "your input is malformed" from "that label is already taken".

- **Given** the canonical form is `[a-z0-9_-]{1,64}`
- **When** Operator submits any of `Baseline`, `baseline `, `exp,1`, or `baseline` (fullwidth)
- **Then** the pipeline rejects at CLI parse with `run_label_not_canonical`, suggests the canonical form, and never reaches Braintrust duplicate detection

Category: Illustrative
Origin: Multiple (QA surfaced; Dev sharpened error separation)

### Rule: Braintrust and Langfuse must point at the same environment — cross-environment runs rejected

#### S-id-06: Braintrust prod with Langfuse staging is rejected pre-flight
- **Given** `BRAINTRUST_API_KEY` resolves to the `prod` project while `LANGFUSE_HOST` points at `staging.langfuse.internal`
- **When** Operator launches any run
- **Then** pre-flight rejects with `env_mismatch: braintrust=prod, langfuse=staging`; zero rows are executed; `environment` is recorded as an identity key on all run records when this check passes

Category: Illustrative
Origin: Multiple (QA + Dev)

### Rule: A partial/crashed run does not allow silent reuse of its run_label

#### S-id-07: Rerun of a run_label from a crashed prior run is rejected
- **Given** a prior run with `run_label=baseline` crashed after emitting Braintrust records for rows 1–4 of 10
- **When** Operator reruns with the same `--run-label baseline`
- **Then** the run is rejected with `run_label_collision` (referring to the stub record); Operator is instructed to choose a new `run_label` for the retry

Category: Illustrative
Origin: QA

### Rule: Execution-health scorer reports completion and tool-call success without judging answer quality

#### S-id-08: Completed response with a failed tool call is flagged as execution-health issue
- **Given** a diagnostic row execution produces a final response, and one recorded tool call returns an error
- **When** the execution-health scorer runs for that Braintrust case
- **Then** the scorer metadata reports `execution_complete=true`, `tool_call_all_successful=false`, and `tool_error_names` containing the failed tool name; the scorer does not inspect reference fields or judge answer quality

Category: Illustrative
Origin: User feedback

---

### Journey Scenarios

#### J-id-01: Complete run emits aligned identity on both surfaces
> Proves the identity contract (§6, §8) across Braintrust and Langfuse.

- **Given** Operator runs `row_ids="3,7,12"` on dataset_version `v1.0` with a fresh `run_label` and full identity keys
- **When** execution completes
- **Then** the three Braintrust records carry the 8-key identity set per §8.1 and the three Langfuse traces carry the matching identity keys per §8.2; joining Braintrust↔Langfuse on `(row_id, run_label, dataset_version)` produces exactly 3 matched pairs

Category: Journey
Origin: Multiple

---

## Feature: Langfuse Reference Context Projection

### Context
Each Langfuse trace carries both identity keys (§8.2) and all 7 `reference_*` fields projected from the dataset row. `reference_*` is a snapshot at trace-creation time — it is the Reviewer's context and must be stable and non-overwritten.

### Rule: Every Langfuse trace carries all 7 reference_* fields, null-present even when source is empty

#### S-ref-01: Full reference context lands on the trace
- **Given** dataset row `id=12` has `capability_band=boundary`, `expected_near_v1_behavior="partial"`, `primary_failure_mechanism="stale_data"`, `secondary_failure_mechanism="overreach"`, `expected_best_source="10-K"`, `likely_tuning_lever="retrieval_window"`, `draft_pass_signals="cites_filing_date"`
- **When** Operator executes that row
- **Then** the Langfuse trace metadata contains `row_id=12` + all 7 `reference_*` fields set to the dataset values above

Category: Illustrative
Origin: PO

#### S-ref-02: Sparse reference field is null-present, not omitted
- **Given** dataset row `id=5` has `secondary_failure_mechanism` empty
- **When** Operator executes that row
- **Then** the Langfuse trace metadata contains all 7 `reference_*` keys; `reference_secondary_failure_mechanism` is explicitly `null` (the key is present)

Category: Illustrative
Origin: Multiple (PO+Dev; Q-C1 resolved to null-present)

### Rule: reference_* is injected at trace creation and visible to a Reviewer opening the trace at any time during the run

#### S-ref-03: reference_* is visible the moment the first LLM span appears
> Verifies reference_* is not written post-hoc (which would miss early spans).

- **Given** Operator executes row `id=12`; the agent emits its first LLM child span ~50 ms after trace creation
- **When** Reviewer opens the Langfuse trace before the agent returns
- **Then** the trace root already carries all 7 `reference_*` fields and the identity keys

Category: Illustrative
Origin: Dev

### Rule: reference_* on an emitted trace is an immutable snapshot of the dataset row at run time

#### S-ref-04: Dataset row body edited post-run does not change the trace's reference_*
- **Given** a trace was emitted at `t0` with `reference_expected_behavior="answer in 2 steps"`
- **When** someone edits the dataset row's `expected_near_v1_behavior` to `"answer in 3 steps"` at `t1 > t0` without bumping `dataset_version`
- **Then** the trace at `t0` still reports `reference_expected_behavior="answer in 2 steps"` (snapshot retained, not re-read)

Category: Illustrative
Origin: Dev

### Rule: Slice is frozen at run start — mid-run dataset edits or appends do not leak into the current run's traces

#### S-ref-05: Row appended mid-run is not executed and is not in slice_identity
- **Given** Operator starts `slice_type=full_dataset` at `t0`, snapshotting 30 rows
- **When** row 31 is appended to the dataset at `t0+5s` while the run is still iterating row 10
- **Then** row 31 is not executed in this run; `selected_row_ids` remains `[1..30]`; `slice_hash` is computed over the frozen 30-row set

Category: Illustrative
Origin: QA

#### S-ref-06: Row body edited mid-run does not leak into a later-in-run trace
- **Given** a full run started at `t0`; row 7 body has `expected_near_v1_behavior="answer in 2 steps"` at snapshot time
- **When** row 7 is edited to `"answer in 3 steps"` at `t0+5s` and the agent invocation for row 7 happens at `t0+10s`
- **Then** the trace for row 7 carries `reference_expected_behavior="answer in 2 steps"` (snapshot value)

Category: Illustrative
Origin: Dev

### Rule: Trace metadata payload must stay within Langfuse size limits — oversize rejected pre-emit

#### S-ref-07: Oversize reference rubric is rejected pre-emit
- **Given** dataset row whose `expected_near_v1_behavior` content is 12 KB (exceeds Langfuse metadata cap)
- **When** Operator tries to execute that row
- **Then** the pipeline refuses to emit the trace with `metadata_size_exceeded` naming `row_id` and the offending field; no partial trace is created

Category: Illustrative
Origin: QA

---

### Journey Scenarios

#### J-ref-01: Reviewer opens Annotation Queue and sees complete reference context
> Proves the trace projection + Annotation Queue context delivery path.

- **Given** Operator just completed a run on `row_ids="5,12"`
- **When** Reviewer opens the Langfuse Annotation Queue filtered by this run's `run_label`
- **Then** both traces appear with their 7 `reference_*` fields fully populated and identity keys visible for cross-referencing

Category: Journey
Origin: Multiple

---

## Feature: Human Annotation Schema v1

### Context
Reviewer records `observed_*` fields against a trace via the Langfuse Annotation Queue UI. Schema v1 is a mixed core + optional-diagnostic shape (§9). Core completeness is enforced at export (not by the UI, pending Langfuse verification). Revisions, retractions, and partial diagnostic submissions are all realistic paths.

### Rule: Reviewer can record all 4 core observed_* fields at trace level

#### S-ann-01: Full core annotation persists
- **Given** a Langfuse trace for `(row_id=7, run_label=baseline)`
- **When** Reviewer submits `observed_outcome=acceptable_answer`, `observed_alignment_to_prompt=medium`, `review_confidence=high`, `review_comment="cites 10-K, missed latest 8-K"`
- **Then** all 4 fields are stored on the trace and retrievable via Langfuse export

Category: Illustrative
Origin: PO

### Rule: Missing required core field is flagged in export (annotation_incomplete)

#### S-ann-02: Partial core submission flagged at export
- **Given** Reviewer submits only `observed_outcome=strong_answer` and `review_comment="clean"`, omitting `observed_alignment_to_prompt` and `review_confidence`
- **When** Analyst runs export for this trace's `run_label`
- **Then** the trace's row in the discussion CSV carries `annotation_incomplete=true` and lists the missing fields

Category: Illustrative
Origin: Multiple (Dev + QA)

### Rule: Optional diagnostic fields may be omitted in any combination, including secondary-without-primary

#### S-ann-03: Primary mechanism without secondary is valid
- **Given** Reviewer has provided all 4 core fields
- **When** Reviewer adds `observed_primary_failure_mechanism=stale_data` and leaves `observed_secondary_failure_mechanism` blank
- **Then** the annotation persists; export shows `observed_primary_failure_mechanism=stale_data` and `observed_secondary_failure_mechanism=null`; no validator complaint

Category: Illustrative
Origin: Dev

#### S-ann-04: Secondary mechanism without primary is valid (both optional per §9.2)
- **Given** Reviewer has provided all 4 core fields
- **When** Reviewer adds only `observed_secondary_failure_mechanism=overreach`
- **Then** the annotation persists; export shows only the secondary populated; no `secondary_without_primary` validation error

Category: Illustrative
Origin: QA (NUI-resolved as permitted)

### Rule: Reviewer revision after export is surfaced in subsequent exports (never silently loses audit trail)

#### S-ann-05: Revised annotation drives a new timestamped export
- **Given** Reviewer set `observed_outcome=pass` at `t0`; Analyst exported to `discussion_baseline_2026-04-20T10-00Z.csv`
- **When** Reviewer revises to `observed_outcome=fail` at `t1` and Analyst re-exports
- **Then** the new file is named `discussion_baseline_{t1}.csv`; the prior file is untouched; the new CSV row carries `annotation_revised_at=t1`

Category: Illustrative
Origin: QA

### Rule: Retracted annotation (set then cleared) is distinguishable from never-set

#### S-ann-06: Retraction surfaces as an explicit status, not as "pending"
- **Given** Reviewer set `observed_outcome=fail` then deleted the score via Langfuse UI
- **When** Analyst runs export
- **Then** that trace's row carries `_annotation_status=retracted` with `observed_outcome=null`; it is NOT reported as `pending`

Category: Illustrative
Origin: QA

---

### Journey Scenarios

#### J-ann-01: Reviewer completes trace-level annotation workflow
> Proves core + optional diagnostic paths for a single trace.

- **Given** Reviewer opens an un-annotated trace in the Annotation Queue
- **When** Reviewer fills all 4 core fields + `observed_primary_failure_mechanism` + `needs_followup=true` + `followup_note`, and submits
- **Then** all submitted fields are stored on the trace; the trace's `annotation_incomplete` flag is false; an export for this run surfaces all 6 filled fields and the 3 unsubmitted optional fields as `null`

Category: Journey
Origin: Multiple

---

## Feature: Cross-Platform Join & Discussion Export

### Context
Analyst exports Langfuse scores for a `run_label` and joins them to the dataset + Braintrust records. The join key is `(row_id, run_label, dataset_version)` (§6.4, §14.2). Discussion CSV places `reference_*` and `observed_*` side-by-side (§9.3, §14.3). Partial states (unannotated, orphan, retracted) surface via explicit sentinel columns.

### Rule: Braintrust record and Langfuse trace join 1:1 by (row_id, run_label, dataset_version)

#### S-join-01: Canonical 3-key join produces exactly one matched pair
- **Given** a completed run with `run_label=baseline` on `dataset_version=v1.0` that executed `row_id=7`
- **When** Analyst joins the Braintrust export and Langfuse export by `(row_id, run_label, dataset_version)`
- **Then** exactly one matched row is produced

Category: Illustrative
Origin: PO

#### S-join-02: Same row_id in two dataset_versions produces two independent matches
> Proves dataset_version is part of the join key (Q-D1 resolution).

- **Given** a run on `dataset_version=v1.0` for `row_id=7` with `run_label=baseline`, and a separate run on `v1.1` for `row_id=7` with `run_label=baseline` (uniqueness check passed because v1.0 run previously exported and its run_label was cleared, or the namespace is version-scoped — implementation detail)
- **When** Analyst joins across both runs
- **Then** two distinct matched rows are returned, one per `dataset_version`; no row is dropped or merged

Category: Illustrative
Origin: Dev

### Rule: Orphan state (Braintrust-only or Langfuse-only) is surfaced with a structured _join_status, never silently dropped

#### S-join-03: Langfuse emission failed but Braintrust write succeeded — orphan surfaces
- **Given** for `(row_id=7, run_label=baseline)` the Braintrust record was written but the Langfuse trace POST failed
- **When** Analyst runs the join/export
- **Then** the row appears in the output with `_join_status=langfuse_emit_failed` and all `observed_*` columns `null`; the row is NOT silently dropped

Category: Illustrative
Origin: Multiple (Dev + QA)

### Rule: Unannotated trace has a distinct status, not conflated with retracted or incomplete

#### S-join-04: Unannotated trace surfaces as pending with empty observed_*
- **Given** a Langfuse trace exists for `(row_id=7, run_label=baseline)` with no human annotation yet
- **When** Analyst runs the export
- **Then** the row carries `_annotation_status=pending`, all 4 `observed_*` core columns are `null`, and all 7 `reference_*` columns are populated

Category: Illustrative
Origin: QA

### Rule: reference_* and observed_* coexist side-by-side in the joined CSV — neither overwrites the other

#### S-join-05: Divergent reviewer observation preserved alongside dataset reference
- **Given** dataset row `id=12` has `primary_failure_mechanism=stale_data` (projected as `reference_primary_failure_mechanism=stale_data`); Reviewer recorded `observed_primary_failure_mechanism=overreach`
- **When** Analyst runs the export
- **Then** the row has `reference_primary_failure_mechanism=stale_data` and `observed_primary_failure_mechanism=overreach` in separate columns — neither overwrites the other

Category: Illustrative
Origin: PO

#### S-join-06: Blank observed does not trigger a fallback substitution
- **Given** Reviewer completed core fields but left `observed_primary_failure_mechanism` blank
- **When** Analyst runs the export
- **Then** `reference_primary_failure_mechanism` retains its dataset value; `observed_primary_failure_mechanism` is empty — no reference-to-observed fallback copy

Category: Illustrative
Origin: PO

### Rule: Zero-annotation export produces a worklist CSV (not an error)

#### S-join-07: 0-of-30 annotated produces a CSV worklist with coverage header
- **Given** a completed run with `run_label=baseline` over 30 rows; zero annotations have been recorded
- **When** Analyst runs the export
- **Then** the CSV has 30 rows, all `reference_*` populated, all `observed_*` null, and the header contains `# annotation_coverage=0/30` and `annotation_coverage_pct=0.0`; CLI exit is zero

Category: Illustrative
Origin: Dev

### Rule: Concurrent annotation and export yields a point-in-time snapshot; in-flight annotations are flagged as incomplete

#### S-join-08: Mid-annotation export does not expose half-saved required fields
- **Given** Reviewer has saved 3 of 4 core fields on a trace at export time
- **When** Analyst triggers the export
- **Then** the row appears with `_annotation_status=incomplete` and the 3 saved fields populated; no silent "confidence=null + outcome=fail" combination appears without a status marker

Category: Illustrative
Origin: QA

### Rule: Re-export writes a new timestamped file — the prior export is retained for audit

#### S-join-09: Second export after revision does not overwrite the first
- **Given** a prior export file `discussion_baseline_{t0}.csv` exists
- **When** Analyst re-exports at `t1`
- **Then** a new file `discussion_baseline_{t1}.csv` is produced; `discussion_baseline_{t0}.csv` is unchanged on disk; CLI prints a diff summary naming revised rows

Category: Illustrative
Origin: Multiple (QA + Dev)

---

### Journey Scenarios

#### J-join-01: Analyst produces discussion CSV spanning reference + observed for the full run
> Proves the §14.3 workflow: export → join → reference_* and observed_* side-by-side.

- **Given** Operator has executed a 5-row run; Reviewer has annotated 4 of 5 traces with full core fields and partial diagnostics
- **When** Analyst runs export for this `run_label`
- **Then** the output CSV has 5 rows; 4 rows carry populated `observed_*` core + partial diagnostic columns alongside all 7 `reference_*` columns; 1 row carries `_annotation_status=pending` with `reference_*` only; header notes `annotation_coverage=4/5`

Category: Journey
Origin: Multiple

#### J-join-02: reference_* evolves across runs of the same row
> Proves "never overwritten" is within-trace, not across-runs.

- **Given** dataset row `id=5` had `expected_best_source="10-K"` when run 1 executed at `t0`; the dataset is then updated to `expected_best_source="10-Q"`; run 2 executes at `t1`
- **When** Analyst exports run 1 and run 2 separately
- **Then** run 1's CSV row for `row_id=5` carries `reference_best_source="10-K"` (snapshot at `t0`); run 2's CSV row for `row_id=5` carries `reference_best_source="10-Q"` (snapshot at `t1`); run 1's export is not modified

Category: Journey
Origin: Multiple

---

## Feature: Run-to-Run Compare Rule Enforcement

### Context
Two completed runs can be compared (§7.1). Braintrust handles row-by-row comparison through its configured comparison key, while the diagnostic compare guard checks run/slice metadata before Analysts interpret the comparison. Same-row-set comparisons are treated as canonical; any row-set difference (full-vs-subset, cross-version, empty intersection) must be surfaced with explicit flags (`overlap_only`, `dataset_version_drift`, `empty_intersection`). Analyst never sees a silent aggregate over non-comparable row sets.

### Rule: Subset-vs-subset compare uses the intersection row set and is NOT marked overlap_only

#### S-cmp-01: Identical subsets on the same dataset_version produce a clean summary
- **Given** run A used `row_ids=[1,2,3,4,5]` on `v1.0`; run B used `row_ids=[1,2,3,4,5]` on `v1.0`
- **When** Analyst compares A vs B
- **Then** the compare guard summary is computed over 5 rows; the summary is NOT marked `overlap_only`

Category: Illustrative
Origin: PO

#### S-cmp-02: Overlapping-but-not-identical subsets compare over the intersection
- **Given** run A used `[1,2,3,4,5]` on `v1.0`; run B used `[3,4,5,6,7]` on `v1.0`
- **When** Analyst compares A vs B
- **Then** the compare guard summary is computed over `{3,4,5}`; the summary is NOT marked `overlap_only`

Category: Illustrative
Origin: PO

### Rule: Full-vs-subset compare MUST mark the summary overlap_only

#### S-cmp-03: Full-vs-subset summary is flagged overlap_only
- **Given** run A used `slice_type=full_dataset` (30 rows) on `v1.0`; run B used `row_ids=[2,7,12,18,25]` on `v1.0`
- **When** Analyst compares A vs B
- **Then** the compare guard reports the 5-row intersection; it is marked `overlap_only`; no 30-row aggregate is presented as comparable

Category: Illustrative
Origin: PO

### Rule: Cross-dataset_version compare must surface dataset_version_drift (with added/removed rows)

#### S-cmp-04: Full-vs-full across versions surfaces structured drift
- **Given** run A used `full_dataset` on `v1.0` (30 rows); run B used `full_dataset` on `v1.1` (32 rows — rows 31 and 32 added, nothing removed)
- **When** Analyst compares A vs B
- **Then** the compare guard is marked `overlap_only` and carries `dataset_version_drift={added:[31,32], removed:[], intersection_size:30}`; raw 30-vs-32 aggregate is not rendered

Category: Illustrative
Origin: Multiple (Dev + QA)

#### S-cmp-05: Cross-version subset compare where row_ids don't correspond is rejected
- **Given** run A used `row_ids=[1,2,3]` on `v1.0`; run B used `row_ids=[3]` on `v1.1` where row 3 on v1.0 and on v1.1 have different content
- **When** Analyst attempts compare
- **Then** the compare is rejected with `dataset_version_mismatch: A=v1.0, B=v1.1`

Category: Illustrative
Origin: Multiple (Dev + QA)

### Rule: Empty intersection compares surface an explicit warning, not a parity summary

#### S-cmp-06: Non-overlapping subsets produce empty-intersection warning
- **Given** run A used `row_ids=[1,2,3]` on `v1.0`; run B used `row_ids=[10,11,12]` on `v1.0`
- **When** Analyst compares A vs B
- **Then** the compare guard output carries `intersection_size=0` and `warning=empty_intersection`; no parity statistics are rendered

Category: Illustrative
Origin: QA

---

### Journey Scenarios

#### J-cmp-01: Analyst validates a fix then notices a dataset refresh changed the comparison semantics
> Proves the compare layer flags silent comparability regressions.

- **Given** run `baseline` and run `after-fix` both on `row_ids=[1..5]` on `v1.0`; later the dataset is bumped to `v1.1` (row 6 added); Operator runs `full_dataset` on `v1.1` as `after-fix-full`
- **When** Analyst first compares `baseline` vs `after-fix` (both subsets on `v1.0`), then compares `after-fix` vs `after-fix-full` (subset on v1.0 vs full on v1.1)
- **Then** the first compare guard result produces a clean 5-row summary; the second compare guard result is marked `overlap_only` with `dataset_version_drift={added:[6], removed:[], intersection_size:5}`

Category: Journey
Origin: Multiple

---

## Out-of-Scope for v1 (explicitly noted — do not implement in this pass)

| Topic | Why out of scope |
|---|---|
| `--replace-incomplete` / `--force-new-suffix` / `--ignore-missing` opt-in flags | v1 favors strict fail-fast; simpler surface area |
| Editable-install `agent_version` fingerprint (`+dirty`) | Operator-trusted for v1 |
| Langfuse Annotation Queue UI re-surfacing of incomplete traces | deferred pending Langfuse feature verification |
| Multi-reviewer-per-trace coverage reporting | single-reviewer assumed in v1 |
| LLM-as-judge scorer, observation-level annotations, automatic analysis pull-back | out of scope per design §2.2 / §15 |
| Per-field reference_* sparsity-semantics table | deferred per §13.1 (v1 is not gold-scorer dataset) |
