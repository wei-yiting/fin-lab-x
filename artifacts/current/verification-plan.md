# Verification Plan

## Meta

- Scenarios Reference: `artifacts/current/bdd-scenarios.md`
- Generated: 2026-04-24
- Primary verification surfaces: CLI invocation of `eval_runner`; Braintrust SDK / export; Langfuse SDK / export; discussion-CSV file inspection.
- Browser automation is minimal — the pipeline is CLI-driven for Operator/Analyst and API-driven for Reviewer (Langfuse Annotation Queue). Reviewer actions are simulated via Langfuse SDK score writes.

Placeholder convention: `[POST-CODING: {what to look up}]` marks items that genuinely require the codebase/configs after implementation.

---

## Automated Verification — Deterministic

### Feature: Dataset Selection & Slice Identity

#### S-slice-01: Full run on a stable dataset_version is reproducible
- **Method**: script (CLI + Braintrust SDK query)
- **Steps**:
  1. `export RUN_LABEL_1=slice-01-a-$(date +%s)` — unique run_label for first run
  2. Run pipeline: `[POST-CODING: eval_runner command with --slice-type full_dataset --run-label $RUN_LABEL_1 --dataset-version v1.0]`
  3. Wait for completion; capture `slice_hash` from run metadata: `SLICE_HASH_1=$(braintrust experiment get --name $RUN_LABEL_1 --field slice_hash)` — `[POST-CODING: confirm Braintrust SDK path]`
  4. `export RUN_LABEL_2=slice-01-b-$(date +%s)`
  5. Run pipeline again with the same dataset_version: `[POST-CODING: eval_runner ... --run-label $RUN_LABEL_2 --dataset-version v1.0]`
  6. Capture `slice_hash` from second run: `SLICE_HASH_2=...`
  7. Assert: `SLICE_HASH_1 == SLICE_HASH_2`; both runs' `selected_row_ids` contain all 30 dataset row ids
- **Expected**: Both runs execute 30 rows; `slice_hash` matches; `slice_label="full_dataset"` on both.

#### S-slice-02: Full run on a bumped dataset_version produces a distinct slice_hash
- **Method**: script
- **Steps**:
  1. Run `full_dataset` on `dataset_version=v1.0` → capture `SLICE_HASH_V10`
  2. `[POST-CODING: bump the dataset to v1.1 — specify mechanism: new CSV file, registry bump, etc.]` — add 2 new rows (row 31, row 32)
  3. Run `full_dataset` on `dataset_version=v1.1` → capture `SLICE_HASH_V11`
  4. Assert: `SLICE_HASH_V10 != SLICE_HASH_V11`; run 2's `selected_row_ids` has length 32; run 2's `dataset_version` metadata is `v1.1`
- **Expected**: Two distinct `slice_hash` values; both runs record the correct `dataset_version`.

#### S-slice-03: row_ids selects only the listed rows
- **Method**: script
- **Steps**:
  1. Run pipeline with `--slice-type row_ids --slice-selector "3,7,12"`
  2. Query Braintrust: count records in this run_label's experiment
  3. Assert: exactly 3 records exist, with `row_id ∈ {3, 7, 12}`
  4. Query Langfuse: count traces for this run_label
  5. Assert: exactly 3 traces exist with the same row_ids
- **Expected**: 3 records + 3 traces; other 27 rows have no record or trace.

#### S-slice-04: Unknown row_id fails pre-flight with zero emissions
- **Method**: script
- **Steps**:
  1. Snapshot current Braintrust experiment count and Langfuse trace count for a reserved test project
  2. Run pipeline with `--slice-selector "3,7,999"` and a fresh `run_label=slice-04-$(date +%s)`; capture exit code and stderr
  3. Assert: exit code is non-zero; stderr contains `unknown_row_ids=[999]`
  4. Assert: Braintrust experiment count for the run_label is 0 (no experiment created)
  5. Assert: Langfuse trace count for the run_label is 0
- **Expected**: Fail-fast pre-flight; zero side effects on either platform.

#### S-slice-05: Duplicate row_id in the list is rejected
- **Method**: script
- **Steps**:
  1. Run pipeline with `--slice-selector "3,5,3,7"`
  2. Assert: exit code non-zero; stderr contains `duplicate_row_ids=[3]`
  3. Assert: zero Braintrust experiments and zero Langfuse traces created for this `run_label`
- **Expected**: Rejected pre-flight.

#### S-slice-06: Empty row_ids list is rejected
- **Method**: script
- **Steps**:
  1. Run pipeline with `--slice-type row_ids --slice-selector ""` and a fresh `run_label`
  2. Assert: exit code non-zero; stderr contains `empty_slice_forbidden`
  3. Assert: the run_label is not reserved in Braintrust — same run_label can be used in a subsequent (valid) run
- **Expected**: Rejected; `run_label` namespace uncontaminated.

#### S-slice-07: field_filter is reproducible on the same dataset_version
- **Method**: script
- **Steps**:
  1. Run pipeline with `--slice-type field_filter --slice-selector "capability_band=boundary"` on `v1.0` → capture `SELECTED_IDS_1` and `SLICE_HASH_1` from run metadata
  2. Rerun identical command on `v1.0` → capture `SELECTED_IDS_2` and `SLICE_HASH_2`
  3. Assert: `SELECTED_IDS_1 == SELECTED_IDS_2` (same set, same order after sort); `SLICE_HASH_1 == SLICE_HASH_2`
- **Expected**: Deterministic selector output across reruns.

#### S-slice-08: field_filter matching zero rows is rejected
- **Method**: script
- **Steps**:
  1. Run pipeline with `--slice-selector "capability_band=nonexistent"` (a value no row has)
  2. Assert: exit code non-zero; stderr contains `empty_slice_forbidden`
  3. Assert: zero Braintrust records; `run_label` not reserved
- **Expected**: Zero-match filter rejected pre-flight.

#### S-slice-09: manifest executes exactly the id-set regardless of text encoding
- **Method**: script
- **Steps**:
  1. Write `/tmp/manifest-lf.txt` with `2\n5\n9\n14\n22\n` (UTF-8, no BOM, LF)
  2. Write `/tmp/manifest-crlf-bom.txt` with `\xef\xbb\xbf2\r\n5\r\n9\r\n14\r\n22\r\n` (UTF-8 with BOM, CRLF)
  3. Run pipeline with `--slice-type manifest --manifest-path /tmp/manifest-lf.txt` → capture `SLICE_HASH_LF`
  4. Run pipeline with `--slice-type manifest --manifest-path /tmp/manifest-crlf-bom.txt` → capture `SLICE_HASH_CRLF`
  5. Assert: both runs executed rows 2, 5, 9, 14, 22; `SLICE_HASH_LF == SLICE_HASH_CRLF`
- **Expected**: Hash is over parsed integer set, not file bytes.

#### S-slice-10: manifest unsupported syntax is rejected with a line reference
- **Method**: script
- **Steps**:
  1. Write `/tmp/manifest-mixed.txt` with `1\n2\n# baseline failures\n\n  5\n3-7\n`
  2. Run pipeline with `--manifest-path /tmp/manifest-mixed.txt`
  3. Assert: exit code non-zero; stderr contains `unsupported_manifest_syntax` and the line number (expected line 6)
  4. Assert: no experiment created
- **Expected**: Integer-per-line + `#` comments + blank lines accepted; anything else rejected with line number.

#### S-slice-11: manifest referencing rows missing in the current dataset_version is rejected
- **Method**: script
- **Steps**:
  1. Ensure dataset is at `v1.1` where row 14 was removed (set up fixture)
  2. Run pipeline with manifest `[2,5,9,14,22]` on `v1.1`
  3. Assert: exit code non-zero; stderr contains `manifest_row_missing` with `14` listed
  4. Assert: zero executed rows; zero Braintrust records
- **Expected**: Fail-fast before first emission.

#### J-slice-01: Operator performs a full run then a subset rerun with stable slice identity
- **Method**: script
- **Steps**:
  1. Run `--slice-type full_dataset --run-label j-slice-01-full-$TS` → capture `SLICE_ID_FULL` (fields: `slice_type`, `slice_label`, `slice_hash`, `selected_row_ids`)
  2. Run `--slice-type row_ids --slice-selector "3,7,12" --run-label j-slice-01-sub1-$TS` → capture `SLICE_ID_SUB1`
  3. Run same row_ids with a new run_label `--run-label j-slice-01-sub2-$TS` → capture `SLICE_ID_SUB2`
  4. Assert: `SLICE_ID_FULL.slice_hash != SLICE_ID_SUB1.slice_hash`; `SLICE_ID_SUB1.slice_hash == SLICE_ID_SUB2.slice_hash`; the three `run_label`s are all recorded separately in Braintrust
- **Expected**: Three distinct slice identities; two subset runs share `slice_hash`; the full run differs.

---

### Feature: Braintrust Identity & Run Lifecycle

#### S-id-01: Full identity keyset is recorded on every case
- **Method**: script
- **Steps**:
  1. Run pipeline with `--slice-selector "7,12" --run-label near-v1-2026-04-24-a --run-group smoke --slice-label bugfix-7-12 --agent-version near-v1.0.3 --dataset-version v1.0`
  2. Query Braintrust for both records: `[POST-CODING: Braintrust SDK call to list experiment cases]`
  3. Assert: both records carry the 8 keys (`row_id`, `dataset_name=fin-lab_near-v1_diagnostic`, `dataset_version=v1.0`, `run_label=near-v1-2026-04-24-a`, `run_group=smoke`, `slice_label=bugfix-7-12`, `slice_type=row_ids`, `agent_version=near-v1.0.3`) populated with exactly those values
- **Expected**: All 8 keys present on both records.

#### S-id-02: Missing mandatory identity key aborts pre-flight
- **Method**: script
- **Steps**:
  1. Run pipeline omitting `--agent-version` (mandatory per NUI #6)
  2. Assert: exit code non-zero; stderr contains `missing_identity_key=[agent_version]`
  3. Assert: zero Braintrust records, zero Langfuse traces
- **Expected**: Fail-fast; zero emissions.

#### S-id-03: Different run_label produces two distinct records for the same row
- **Method**: script
- **Steps**:
  1. Run `--slice-selector "7" --run-label baseline-$TS1`
  2. Run `--slice-selector "7" --run-label after-fix-$TS1`
  3. Query Braintrust for `row_id=7` across both experiments
  4. Assert: exactly 2 records exist; they differ only in `run_label` field values
- **Expected**: Two independent records, no collision.

#### S-id-04: Duplicate run_label is rejected at the Braintrust experiment boundary
- **Method**: script
- **Steps**:
  1. Run `--slice-selector "7" --run-label baseline-$TS2` from machine A → complete successfully
  2. From a fresh shell (simulating a different machine with no local state), run the same command `--run-label baseline-$TS2`
  3. Assert: exit code non-zero; stderr contains `run_label_collision`
  4. Assert: Braintrust still has exactly 1 experiment with that name; no Langfuse trace was emitted by the second invocation (check by filtering traces by timestamp)
- **Expected**: Second run rejected at the Braintrust boundary.

#### S-id-05: Non-canonical run_label is rejected at input
- **Method**: script
- **Steps**:
  1. For each bad input in `("Baseline", "baseline ", "exp,1", "baseline" fullwidth — literal bytes `\xef\xbc\x82`)`, run the pipeline with `--run-label <input>`
  2. Assert: each rejects with `run_label_not_canonical`; stderr includes a suggested canonical form
  3. Assert: error is surfaced at CLI parse time — no Braintrust API call is made (verify via network trace or log marker)
- **Expected**: Input-time rejection, distinct from `run_label_collision`.

#### S-id-06: Braintrust prod with Langfuse staging is rejected pre-flight
- **Method**: script
- **Steps**:
  1. Set `BRAINTRUST_API_KEY` to prod project key
  2. Set `LANGFUSE_HOST` to a staging URL (e.g., `https://staging.langfuse.internal`)
  3. Run pipeline with a valid selector
  4. Assert: exit code non-zero; stderr contains `env_mismatch: braintrust=prod, langfuse=staging`
  5. Assert: zero rows executed; zero records or traces
- **Expected**: Pre-flight env assertion catches the misconfig.

#### S-id-07: Rerun of a run_label from a crashed prior run is rejected
- **Method**: script
- **Steps**:
  1. Start a 10-row run with `--run-label crashed-$TS3`; kill the process mid-row (e.g., `kill -9` after row 4 emitted) — `[POST-CODING: confirm how to simulate a hard crash given the run loop structure]`
  2. Verify Braintrust has a stub record with 4 rows
  3. Rerun with the same `--run-label crashed-$TS3`
  4. Assert: exit code non-zero; stderr contains `run_label_collision`
  5. Assert: Operator is directed to a new `run_label`; the 4-row stub remains untouched for audit
- **Expected**: Stub detection prevents silent re-use.

#### S-id-08: Completed response with a failed tool call is flagged as execution-health issue
- **Method**: unit/integration test with mocked diagnostic task output
- **Steps**:
  1. Construct a diagnostic task result with a non-empty final response and recorded tool outputs where one tool, e.g. `tavily_search`, contains an error marker
  2. Run `diagnostic_execution_health` against the result
  3. Assert: score is `0`; metadata contains `execution_complete=true`, `tool_call_all_successful=false`, and `tool_error_names=["tavily_search"]`
  4. Construct a second result with a final response and successful tool outputs
  5. Assert: score is `1`; metadata contains `execution_complete=true`, `tool_call_all_successful=true`, and `tool_error_names=[]`
  6. Assert: changing dataset reference hints (`expected_near_v1_behavior`, failure mechanism fields, pass signals) does not change the scorer output
- **Expected**: Execution/tool-call health is visible without using LLM-as-a-Judge or answer-quality checks.

#### J-id-01: Complete run emits aligned identity on both surfaces
- **Method**: script
- **Steps**:
  1. Run `--slice-selector "3,7,12" --run-label j-id-01-$TS --dataset-version v1.0 --agent-version near-v1.0.3`
  2. Query Braintrust: collect 3 records; extract 8 identity keys per record
  3. Query Langfuse: collect 3 traces for this run_label; extract identity keys from trace metadata
  4. Join the two lists on `(row_id, run_label, dataset_version)`
  5. Assert: exactly 3 matched pairs; Braintrust keys and Langfuse keys agree for each pair
- **Expected**: Cross-platform identity alignment verified end-to-end.

---

### Feature: Langfuse Reference Context Projection

#### S-ref-01: Full reference context lands on the trace
- **Method**: script (CLI + Langfuse SDK)
- **Steps**:
  1. Ensure dataset row `id=12` has the 7 reference source fields populated (fixture setup)
  2. Run pipeline with `--slice-selector "12"`
  3. Fetch the Langfuse trace for `(row_id=12, run_label=<this run>)` via SDK
  4. Assert: trace metadata contains all 7 keys `reference_capability_band`, `reference_expected_behavior`, `reference_primary_failure_mechanism`, `reference_secondary_failure_mechanism`, `reference_best_source`, `reference_likely_tuning_lever`, `reference_pass_signals` — each set to the dataset values
- **Expected**: 7-field projection verified.

#### S-ref-02: Sparse reference field is null-present, not omitted
- **Method**: script
- **Steps**:
  1. Pick / construct dataset row `id=5` with `secondary_failure_mechanism` empty
  2. Run pipeline with `--slice-selector "5"`
  3. Fetch trace metadata via Langfuse SDK
  4. Assert: `reference_secondary_failure_mechanism` key exists in metadata; its value is explicitly `null` (not missing); the other 6 `reference_*` keys are populated
- **Expected**: Key-present-with-null schema, stable for downstream join.

#### S-ref-03: reference_* is visible the moment the first LLM span appears
- **Method**: script
- **Steps**:
  1. Start a run for `row_id=12` in background: `<cli> --slice-selector "12" --run-label ref-03-$TS &`
  2. Poll Langfuse traces for this `run_label` every 200ms until the trace exists (should appear <5s)
  3. Fetch trace metadata immediately on first detection; capture snapshot
  4. Also poll for child spans; once the first LLM span exists, re-fetch trace metadata
  5. Assert: at the moment the first child span is observed, the trace root already has all 7 `reference_*` keys + identity keys
- **Expected**: No post-hoc injection — context is present at trace creation.

#### S-ref-04: Dataset row body edited post-run does not change the trace's reference_*
- **Method**: script
- **Steps**:
  1. Ensure dataset row `id=7` has `expected_near_v1_behavior="answer in 2 steps"`
  2. Run pipeline with `--slice-selector "7"`; fetch trace → record `reference_expected_behavior="answer in 2 steps"`
  3. Edit the dataset row to `"answer in 3 steps"` (same `dataset_version`, no bump) — `[POST-CODING: dataset edit mechanism]`
  4. Re-fetch the same Langfuse trace (do NOT rerun)
  5. Assert: `reference_expected_behavior="answer in 2 steps"` (unchanged)
- **Expected**: Trace is a snapshot; live dataset re-read is not used.

#### S-ref-05: Row appended mid-run is not executed and is not in slice_identity
- **Method**: script
- **Steps**:
  1. Start a `full_dataset` run in background with a 30-row dataset; inject an artificial per-row delay so total runtime is ~30 s `[POST-CODING: confirm or add a `--per-row-sleep-ms` option]`
  2. At `t0+5s` (mid-run), append a new row (`id=31`) to the dataset source
  3. Wait for run completion
  4. Assert: run executed exactly 30 rows; `selected_row_ids` is `[1..30]`; Braintrust records count is 30; Langfuse trace count is 30; no trace exists for `row_id=31`
- **Expected**: Slice freeze at start; mid-run dataset growth ignored.

#### S-ref-06: Row body edited mid-run does not leak into a later-in-run trace
- **Method**: script
- **Steps**:
  1. Start a `full_dataset` run with the 30-row dataset and delays, ordered so row 7 executes at `t0+10s`
  2. At `t0+5s`, edit row 7's `expected_near_v1_behavior` from `"answer in 2 steps"` to `"answer in 3 steps"` (same dataset_version)
  3. After the run completes, fetch the Langfuse trace for `row_id=7`
  4. Assert: `reference_expected_behavior="answer in 2 steps"` (snapshot value at run start)
- **Expected**: Freeze applies to row payloads, not just the id set.

#### S-ref-07: Oversize reference rubric is rejected pre-emit
- **Method**: script
- **Steps**:
  1. Prepare a dataset fixture where one row has `expected_near_v1_behavior` = 12 KB text
  2. Run pipeline targeting that row
  3. Assert: exit code non-zero; stderr contains `metadata_size_exceeded` naming the `row_id` and offending field
  4. Assert: no Braintrust record or Langfuse trace exists for that row (other rows in the slice may or may not have executed — `[POST-CODING: decide if oversize is whole-slice rejection or per-row skip]`)
- **Expected**: Pre-emit size validation refuses rather than silently truncating.

#### J-ref-01: Reviewer opens Annotation Queue and sees complete reference context
- **Method**: script + Langfuse SDK
- **Steps**:
  1. Run a two-row fixture: `--slice-selector "5,12"` with fixture where row 5 has empty `secondary_failure_mechanism` and row 12 has all fields populated
  2. Via Langfuse SDK, query the Annotation Queue (or list traces filtered by `run_label`)
  3. For each of the two traces, fetch metadata
  4. Assert: trace for row 5 has 7 reference keys (one `null`), 6 populated; trace for row 12 has 7 reference keys fully populated
  5. Optional manual step (Manual Behavior Test below): Reviewer opens the Langfuse UI to spot-check that the keys are visible and readable in the Annotation Queue side panel
- **Expected**: Reviewer has the full context the design promises.

---

### Feature: Human Annotation Schema v1

Reviewer actions are simulated via Langfuse SDK (`langfuse.score(...)`) rather than UI clicks. One Manual Behavior Test below covers the actual UI experience.

#### S-ann-01: Full core annotation persists
- **Method**: script
- **Steps**:
  1. Set up: run pipeline for `row_id=7` so a trace exists
  2. Via Langfuse SDK, write 4 scores on the trace: `observed_outcome=acceptable_answer`, `observed_alignment_to_prompt=medium`, `review_confidence=high`, `review_comment="cites 10-K, missed latest 8-K"` — `[POST-CODING: SDK call shape — one score per field vs JSON blob, per resolved Q-E1 = named scores]`
  3. Fetch scores for the trace
  4. Assert: all 4 scores present with matching values
- **Expected**: Named scores stored and retrievable.

#### S-ann-02: Partial core submission flagged at export
- **Method**: script
- **Steps**:
  1. Set up trace; write only 2 of 4 core scores (`observed_outcome=strong_answer`, `review_comment="clean"`)
  2. Run `[POST-CODING: discussion CSV export CLI]`
  3. Parse the output CSV; find the row for `(row_id, run_label)`
  4. Assert: row has `annotation_incomplete=true`; a `missing_fields` column lists `observed_alignment_to_prompt` and `review_confidence`
- **Expected**: Export-layer enforcement surfaces the gap.

#### S-ann-03: Primary mechanism without secondary is valid
- **Method**: script
- **Steps**:
  1. Set up trace; write 4 core scores + `observed_primary_failure_mechanism=stale_data`; do NOT write secondary
  2. Run export CLI
  3. Assert: CSV row has `observed_primary_failure_mechanism=stale_data`, `observed_secondary_failure_mechanism=null`, `annotation_incomplete=false`
- **Expected**: Partial diagnostics accepted without complaint.

#### S-ann-04: Secondary mechanism without primary is valid
- **Method**: script
- **Steps**:
  1. Set up trace; write 4 core + `observed_secondary_failure_mechanism=overreach` only
  2. Run export CLI
  3. Assert: CSV row has `observed_primary_failure_mechanism=null`, `observed_secondary_failure_mechanism=overreach`; `annotation_incomplete=false`; no `secondary_without_primary` error
- **Expected**: Permitted per §9.2.

#### S-ann-05: Revised annotation drives a new timestamped export
- **Method**: script
- **Steps**:
  1. Set up trace; write `observed_outcome=pass` at `t0`; run export → capture filename `F1`
  2. At `t1 > t0`, overwrite `observed_outcome=fail` — `[POST-CODING: Langfuse SDK call to overwrite a score]`
  3. Run export again
  4. Assert: a new file `discussion_<run_label>_<t1>.csv` exists and differs from `F1`; `F1` is unchanged on disk
  5. Parse new file; the row for that trace has `observed_outcome=fail` and `annotation_revised_at` ≈ `t1`
- **Expected**: Two export files; audit trail preserved.

#### S-ann-06: Retraction surfaces as an explicit status
- **Method**: script
- **Steps**:
  1. Set up trace; write 4 core scores
  2. Delete the `observed_outcome` score via Langfuse SDK — `[POST-CODING: SDK delete call]`
  3. Run export CLI
  4. Assert: CSV row has `_annotation_status=retracted`; `observed_outcome=null`; `annotation_revised_at` is set to the deletion time
- **Expected**: Retracted state distinct from `pending`.

#### J-ann-01: Reviewer completes trace-level annotation workflow
- **Method**: script + Langfuse SDK
- **Steps**:
  1. Set up one un-annotated trace
  2. Write via SDK: 4 core scores + `observed_primary_failure_mechanism=stale_data` + `needs_followup=true` + `followup_note="retest after retrieval window change"`
  3. Run export CLI
  4. Parse resulting CSV for this trace's row
  5. Assert: 6 populated observed_* fields; 3 omitted fields (`observed_secondary_failure_mechanism`, `observed_tuning_lever`) are `null`; `annotation_incomplete=false`
- **Expected**: Full mixed-schema annotation round-trip.

---

### Feature: Cross-Platform Join & Discussion Export

#### S-join-01: Canonical 3-key join produces exactly one matched pair
- **Method**: script
- **Steps**:
  1. Run pipeline for `row_id=7` with `run_label=join-01-$TS` on `dataset_version=v1.0`
  2. Run export CLI: `[POST-CODING: export command with --run-label join-01-$TS]`
  3. Parse output CSV; count rows matching `(row_id=7, run_label=join-01-$TS, dataset_version=v1.0)`
  4. Assert: exactly 1 row; all identity keys present; Braintrust-sourced and Langfuse-sourced columns both populated
- **Expected**: 1:1 join on the 3-key.

#### S-join-02: Same row_id in two dataset_versions produces two independent matches
- **Method**: script
- **Steps**:
  1. `[POST-CODING: verify cross-dataset_version run_label reuse is allowed, or adjust the scenario to use distinct run_labels per version while still proving row_id=7 gets two independent join rows across versions]`
  2. Run pipeline for `row_id=7` on `v1.0` with `run_label=baseline`; run export → CSV_V10
  3. Run pipeline for `row_id=7` on `v1.1` with `run_label=baseline-v11` (if run_label namespace is global); run export → CSV_V11
  4. Concatenate the two exports and assert two rows exist for `row_id=7`, differing in `dataset_version`; no row is dropped or merged
- **Expected**: Version is part of the join key — two independent rows.

#### S-join-03: Langfuse emission failed but Braintrust write succeeded — orphan surfaces
- **Method**: script
- **Steps**:
  1. Run pipeline with Langfuse intentionally unreachable (e.g., invalid `LANGFUSE_HOST` for partial of the run) — `[POST-CODING: determine how to simulate partial Langfuse failure; may require a feature flag or test-only mode]`
  2. Confirm Braintrust has the record for `(row_id=7, run_label=join-03-$TS)`; Langfuse has no trace
  3. Run export
  4. Assert: CSV contains a row for `row_id=7` with `_join_status=langfuse_emit_failed` (or the specific enum value chosen); all `observed_*` columns are `null`; the row is NOT silently dropped
- **Expected**: Orphan made visible via sentinel.

#### S-join-04: Unannotated trace surfaces as pending
- **Method**: script
- **Steps**:
  1. Run pipeline for `row_id=7`; do NOT write any annotation scores
  2. Run export
  3. Assert: CSV row has `_annotation_status=pending`; all `observed_*` core columns `null`; all 7 `reference_*` columns populated
- **Expected**: Unannotated state has its own sentinel.

#### S-join-05: Divergent reviewer observation preserved alongside dataset reference
- **Method**: script
- **Steps**:
  1. Ensure dataset row `id=12` has `primary_failure_mechanism=stale_data`
  2. Run pipeline; write `observed_primary_failure_mechanism=overreach` via SDK
  3. Run export
  4. Assert: CSV row for `row_id=12` has `reference_primary_failure_mechanism=stale_data` AND `observed_primary_failure_mechanism=overreach` in separate columns
- **Expected**: No overwrite between the two columns.

#### S-join-06: Blank observed does not trigger a fallback substitution
- **Method**: script
- **Steps**:
  1. Ensure dataset row `id=12` has `primary_failure_mechanism=stale_data`
  2. Run pipeline; write 4 core scores only (no `observed_primary_failure_mechanism`)
  3. Run export
  4. Assert: CSV row has `reference_primary_failure_mechanism=stale_data`; `observed_primary_failure_mechanism=` empty/null (no copy from reference)
- **Expected**: No silent reference→observed fallback.

#### S-join-07: 0-of-30 annotated produces a CSV worklist with coverage header
- **Method**: script
- **Steps**:
  1. Run pipeline for 30 rows with `--run-label worklist-$TS`; do NOT write any annotations
  2. Run export
  3. Assert: CSV file exists with 30 data rows; all 30 have `_annotation_status=pending` and empty `observed_*` columns
  4. Assert: CSV header comment contains `# annotation_coverage=0/30` and `# annotation_coverage_pct=0.0`
  5. Assert: CLI exit code is 0
- **Expected**: Export produces an annotation worklist, not an error.

#### S-join-08: Mid-annotation export does not expose half-saved required fields
- **Method**: script
- **Steps**:
  1. Run pipeline for a trace; start writing annotations: write 3 of 4 core scores; do NOT write the 4th (`review_confidence`)
  2. Run export while the 4th is "in progress" (simulated by writing the first 3 then immediately exporting before writing the 4th)
  3. Assert: CSV row has `_annotation_status=incomplete`; the 3 written scores are populated; `review_confidence=null`; an `annotation_snapshot_at` column records the export timestamp
- **Expected**: Point-in-time snapshot with explicit incomplete marker.

#### S-join-09: Second export after revision does not overwrite the first
- **Method**: script
- **Steps**:
  1. Run pipeline + annotate + export → capture filename `F1`; note `F1` mtime
  2. Revise one annotation via SDK
  3. Export again → capture filename `F2`
  4. Assert: `F1 != F2`; `F1` exists on disk with unchanged mtime; `F2` exists with the revised value; CLI for the second export prints a diff summary naming the revised rows
- **Expected**: Timestamped filenames; prior audit trail intact.

#### J-join-01: Analyst produces discussion CSV spanning reference + observed for the full run
- **Method**: script
- **Steps**:
  1. Run pipeline on 5 rows with fixture dataset
  2. Write full core + partial diagnostic scores for 4 of 5 traces (vary the pattern: some with primary, some with secondary only, some with followup)
  3. Leave 1 trace entirely unannotated
  4. Run export
  5. Assert: 5-row CSV; 4 rows have populated `observed_*` core + appropriate diagnostic columns + `reference_*` populated; 1 row has `_annotation_status=pending` with `reference_*` populated and `observed_*` null
  6. Assert: header contains `# annotation_coverage=4/5`
- **Expected**: Full workflow output — the Analyst's primary artifact.

#### J-join-02: reference_* evolves across runs of the same row
- **Method**: script
- **Steps**:
  1. Ensure dataset row `id=5` has `expected_best_source="10-K"`
  2. Run pipeline with `--run-label first-$TS`; export → CSV_1
  3. Update dataset row to `expected_best_source="10-Q"` (stay on same dataset_version for this test, or bump depending on §14.2 interpretation — `[POST-CODING: align with implementation's version-mutation policy from NUI #3]`)
  4. Run pipeline with `--run-label second-$TS`; export → CSV_2
  5. Assert: CSV_1's row for `row_id=5` shows `reference_best_source="10-K"`; CSV_2's row shows `reference_best_source="10-Q"`; CSV_1 is unchanged on disk
- **Expected**: Snapshot per run; cross-run evolution tracked.

---

### Feature: Run-to-Run Compare Rule Enforcement

Braintrust official docs state that experiment comparison matches rows by `input` by default and supports custom comparison keys in Project Settings. For diagnostic v1, Braintrust remains the row-by-row comparison UI, while `backend.evals.diagnostic.compare_guard` produces a small structured safety report from diagnostic run/slice metadata before Analysts interpret a comparison.

#### S-cmp-01: Identical subsets on the same dataset_version produce a clean summary
- **Method**: script
- **Steps**:
  1. Run `row_ids=[1,2,3,4,5]` on `v1.0` with `run_label=cmp-01-a`
  2. Run same selector with `run_label=cmp-01-b`
  3. Run compare guard: `uv run python -m backend.evals.diagnostic.compare_guard --run-a-manifest <cmp-01-a.csv> --run-b-manifest <cmp-01-b.csv> --output /tmp/cmp-01.json`
  4. Assert: output lists 5 rows, `same_row_set=true`, `overlap_only=false`, and no `dataset_version_drift`
- **Expected**: Clean same-row-set status.

#### S-cmp-02: Overlapping-but-not-identical subsets compare over the intersection
- **Method**: script
- **Steps**:
  1. Run `row_ids=[1,2,3,4,5]` on `v1.0` → `cmp-02-a`
  2. Run `row_ids=[3,4,5,6,7]` on `v1.0` → `cmp-02-b`
  3. Run compare guard for the two run manifests
  4. Assert: output lists 3 intersection rows (`{3,4,5}`); `overlap_only=false`
- **Expected**: Intersection used; no flag.

#### S-cmp-03: Full-vs-subset summary is flagged overlap_only
- **Method**: script
- **Steps**:
  1. Run `full_dataset` on `v1.0` → `cmp-03-a`
  2. Run `row_ids=[2,7,12,18,25]` on `v1.0` → `cmp-03-b`
  3. Run compare guard for the two run manifests
  4. Assert: output lists 5 intersection rows; output contains `overlap_only=true` and a warning that aggregate score should not be interpreted as full-dataset improvement
- **Expected**: Overlap-only flag set.

#### S-cmp-04: Full-vs-full across versions surfaces structured drift
- **Method**: script
- **Steps**:
  1. Run `full_dataset` on `v1.0` (30 rows) → `cmp-04-a`
  2. Run `full_dataset` on `v1.1` (32 rows, added rows 31 and 32) → `cmp-04-b`
  3. Run compare guard for the two run manifests
  4. Assert: output contains `overlap_only=true` AND `dataset_version_drift={added:[31,32], removed:[], intersection_size:30}`; no raw 30-vs-32 aggregate rendered
- **Expected**: Version drift structured detail.

#### S-cmp-05: Cross-version subset compare where row_ids don't correspond is rejected
- **Method**: script
- **Steps**:
  1. Run `row_ids=[1,2,3]` on `v1.0` → `cmp-05-a`
  2. Run `row_ids=[3]` on `v1.1` (where row 3 content differs) → `cmp-05-b`
  3. Run compare guard for the two run manifests
  4. Assert: exit code non-zero; output contains `dataset_version_mismatch: a=v1.0, b=v1.1`
- **Expected**: Mismatch refused, not silently intersected.

#### S-cmp-06: Non-overlapping subsets produce empty-intersection warning
- **Method**: script
- **Steps**:
  1. Run `row_ids=[1,2,3]` on `v1.0` → `cmp-06-a`
  2. Run `row_ids=[10,11,12]` on `v1.0` → `cmp-06-b`
  3. Run compare guard for the two run manifests
  4. Assert: output contains `intersection_size=0` and `warning=empty_intersection`; no parity statistics rendered
- **Expected**: Explicit empty warning.

#### J-cmp-01: Analyst validates a fix then notices a dataset refresh changed the comparison semantics
- **Method**: script
- **Steps**:
  1. Run `row_ids=[1..5]` on `v1.0` → `baseline-$TS`; run same on `v1.0` → `after-fix-$TS`; run `full_dataset` on `v1.1` (row 6 added) → `after-fix-full-$TS`
  2. Run compare guard for `baseline vs after-fix` → assert clean 5-row summary, no flag
  3. Run compare guard for `after-fix vs after-fix-full` → assert `overlap_only=true` and `dataset_version_drift={added:[6], removed:[], intersection_size:5}`
- **Expected**: Compare surface transitions cleanly between no-flag and flagged outcomes as dataset evolves.

---

## Automated Verification — Browser Automation

None required for v1. All scenarios are verifiable via CLI invocations and SDK-level API reads/writes. The Langfuse Annotation Queue UI is not a Coding-Agent-under-test component; Reviewer actions are simulated via Langfuse SDK score writes (see `S-ann-*` and `S-join-*`).

---

## Manual Verification

### Manual Behavior Test

> Tests the Coding Agent cannot automate — mostly about visual/UX behavior of external tools (Langfuse Annotation Queue UI).

#### MBT-ref-01: Reviewer opens a Langfuse trace and confirms reference_* context is visible in the Annotation Queue side panel
- **Reason**: Langfuse UI rendering of trace metadata is an external-tool concern; API-level assertion (covered by S-ref-01) confirms data is present, but not how it appears.
- **Steps**:
  1. User runs `--slice-selector "5,12" --run-label mbt-ref-01-$TS` against the real Langfuse project
  2. User opens Langfuse UI → Annotation Queue filtered to this `run_label`
  3. User opens the trace for `row_id=12`; inspects the trace metadata / side panel
- **Expected**: All 7 `reference_*` keys are visible, labels are readable, long rubric fields are not truncated below usability.

#### MBT-ann-01: Reviewer writes a full annotation via the UI and confirms field-submission UX
- **Reason**: The Langfuse Annotation Queue score submission form is an external surface; API simulation covers persistence, not field-submission UX.
- **Steps**:
  1. User opens a trace from an unannotated run
  2. User submits all 4 core fields + optional diagnostics via the UI
  3. User checks that the annotation persists (refresh, reopen)
  4. User tries to skip `review_confidence` deliberately
- **Expected**: Fields are present and submittable; submission is persisted; if Langfuse UI does NOT enforce core-field completeness, user confirms the export-layer enforcement (S-ann-02) is the right backstop.

#### MBT-env-01: Operator confirms Braintrust and Langfuse run records appear side-by-side and are mutually navigable
- **Reason**: Platform UI navigation (clicking a Braintrust experiment → finding the matching Langfuse trace) is a UX concern not covered by the SDK-level 1:1 join test (J-id-01).
- **Steps**:
  1. User runs J-id-01's pipeline invocation against the real prod project
  2. User opens Braintrust → experiment for this `run_label` → notes each `row_id`
  3. User opens Langfuse → traces for this `run_label` → confirms identity keys match
- **Expected**: User can quickly correlate between the two platforms using the shared identity keys.

---

### User Acceptance Test

> User (Product Owner) validates that the overall discussion-CSV workflow meets v1 integrity goals (§14.3).

#### UAT-workflow-01: Full diagnostic-discussion workflow feels viable end-to-end
- **Acceptance Question**: "Can a Reviewer + Analyst complete a diagnostic-discussion cycle for a 5-row subset without the pipeline getting in the way?"
- **Steps**:
  1. Operator runs `--slice-selector "2,7,12,18,25" --run-label uat-$TS` on the real dataset
  2. Reviewer (the user) opens Langfuse Annotation Queue and annotates all 5 traces with full core + partial diagnostics, taking normal-flow notes on ease of use
  3. Analyst (the user) runs discussion-CSV export
  4. User opens the CSV in their preferred tool (spreadsheet / pandas) and attempts to discuss the results — per-row `reference_*` vs `observed_*` patterns, any divergences, any followups
- **Expected**: CSV is usable without manual column rearrangement; Reviewer and Analyst each accomplished their role without pipeline friction; no missing data blocks discussion; the overall §14.3 goal is visibly met.

#### UAT-reproducibility-01: Subset rerun produces identical slice_identity and clean compare
- **Acceptance Question**: "Can the team trust that re-running a subset selector on a stable dataset gives bit-for-bit reproducible slice_identity, so run-to-run compares are trustworthy?"
- **Steps**:
  1. User runs `--slice-selector "3,7,12" --run-label rep-a-$TS`; notes `slice_hash` and `selected_row_ids`
  2. User reruns the same selector days later (still same `dataset_version`) with a new run_label
  3. User runs compare guard for the two run manifests, then optionally opens Braintrust row-by-row compare using the configured diagnostic comparison key
- **Expected**: Identical `slice_hash`; compare guard produces a clean summary with no `overlap_only` flag and no `dataset_version_drift`.

---

## Open Items Surfaced During Plan Construction

These do not block verification but affect how several steps resolve — coding phase must close them:

1. Exact CLI flag shape for `eval_runner` (e.g., `--slice-type`, `--slice-selector`, `--run-label`). Current plan uses placeholder flags.
2. Braintrust Project Settings comparison key exact SQL expression for diagnostic experiments — must use stable diagnostic identity metadata rather than variable run/session fields.
3. Braintrust SDK idiom for "reject on duplicate experiment name" (e.g., `update=False` vs an explicit pre-check) — affects S-id-04 and S-id-07 setup.
4. Langfuse SDK idiom for deleting a score (retraction) — affects S-ann-06.
5. Mechanism for simulating partial Langfuse failure (S-join-03) — test-only flag, network shim, or recorded-vs-live mode.
6. Dataset version-bump mechanism (S-slice-02, S-slice-11, J-join-02) — file-level replacement, registry pointer, or git tag.
