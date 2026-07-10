# Implementation Plan: near-v1 diagnostic evaluation pipeline

> Design Reference: `[design.md](./design.md)`
> Planning Context: 依 `artifacts/current/design.md` 建立 `near_v1_diagnostic` evaluation pipeline。此 plan 聚焦一個可獨立驗證的 deliverable：用 Braintrust 記錄 execution / compare，用 Langfuse trace metadata 與 Annotation Queue 支援人工標註，提供 Langfuse export CSV 回 join 成 discussion-ready CSV，並提供 run-to-run compare guard 的 workflow。

**Goal:** 新增一條 `near_v1_diagnostic` pipeline，讓 `fin-lab_near-v1_diagnostic_dataset_codex.csv` 可依 slice 執行 near-v1、穩定寫入 Braintrust / Langfuse identity metadata，能將 Langfuse human annotation export join 回分析 CSV，並能在 run-to-run compare 前輸出 comparability guard。

**Architecture / Key Decisions:** Diagnostic pipeline 會留在 `backend/evals` 邊界內，不把 slice、annotation、export join、compare guard 邏輯放進 `backend/api` 或 agent core。`backend/evals/diagnostic/` 是 diagnostic-track shared package，提供未來 diagnostic datasets 可重用的 selector、identity、metadata projection、export join、compare guard、execution-health scorer；root-level `backend/evals/` 保留給 `eval_runner.py`、`eval_tasks.py`、`eval_spec_schema.py` 這類 high-level orchestration surface。Runner 只在 diagnostic scenario 啟用 slice / run identity path；既有 non-diagnostic scenarios 維持相容，不應被迫 import 或採用 diagnostic contract。Langfuse export join 以 deterministic `session_id = "{dataset_name}::{run_label}::{row_id}"` 作為 v1 formal contract 與 scores export join key，同時保留 `row_id` / `run_label` / `dataset_name` 在 trace metadata 中供 UI 檢視。Braintrust row-by-row compare 依 official docs 透過 comparison key match rows；diagnostic docs 必須要求 project comparison key 使用 stable diagnostic identity，並由 lightweight compare guard 在 compare 前標示 `same_row_set`、`overlap_only`、`dataset_version_drift`、`empty_intersection`。

**Tech Stack:** Python 3.11+, Pydantic v2, pytest, Braintrust Python SDK, Langfuse Python SDK v4, existing `backend.evals` runner/scenario framework.

---

## Dependencies Verification

| Dependency | Version | Source | What Was Verified | Notes |
| ---------- | ------- | ------ | ----------------- | ----- |
| Braintrust Python SDK | `braintrust>=0.11.0` in `pyproject.toml` | Context7 `/websites/braintrust_dev` official docs | `Eval`, `EvalCase(input, expected, metadata, id)`, `experiment_name`, experiment metadata, `braintrust.flush()`, and experiment comparison key behavior | Docs confirm `EvalCase` carries per-case metadata and optional `id`; docs also state experiment comparison matches rows by `input` by default and supports custom comparison keys such as `metadata` fields. Plan uses this for row/run/slice identity and requires a stable diagnostic comparison key. No untrusted setup instructions used. |
| Langfuse Python SDK | `langfuse>=4.5.0` in `pyproject.toml` | Context7 `/langfuse/langfuse-docs` official docs | `CallbackHandler`, `propagate_attributes(trace_name, session_id, metadata=...)`, LangChain callback wiring, score export fields including `trace_id`, `observation_id`, `session_id`, `name`, `data_type`, `string_value`, `comment`, `source` | Docs confirm score export contains `session_id`; plan relies on deterministic session ids instead of assuming scores export includes trace metadata. No prompt-injection-like instructions found in docs. |
| Pydantic v2 | `pydantic>=2.0` in `pyproject.toml` | Existing repo usage in `backend/evals/eval_spec_schema.py` | `BaseModel`, `ConfigDict(extra="forbid")`, `model_validator` patterns | Existing code is source of truth; no new external API behavior required. |

## Constraints

- Do not add `LLM-as-a-Judge` scorer for v1 diagnostic quality.
- Do not treat dataset `expected_near_v1_behavior`, `primary_failure_mechanism`, or `draft_pass_signals` as machine-enforced ground truth.
- Keep Braintrust global handler initialization inside `backend/evals/eval_runner.py`; do not move it into shared agent code.
- Keep Langfuse tracing request-scoped through `Orchestrator._build_langfuse_config()` and `CallbackHandler`.
- Support subset execution through `full_dataset`, `row_ids`, `field_filter`, and `manifest`.
- Preserve stable row identity as string `row_id`; do not let CSV numeric coercion turn `id` into `1.0`.
- Diagnostic platform mode must execute each selected row exactly once. Do not keep the existing "local pre-run then Braintrust upload run" behavior for this scenario, because duplicate Langfuse traces with the same deterministic `session_id` would corrupt annotation queue and export join semantics.
- Existing `language_policy` and `sec_retrieval` scenarios must keep current behavior and CLI compatibility.
- Diagnostic utilities should live under `backend/evals/diagnostic/`; do not expose track-specific helper modules at `backend/evals` root unless they are high-level orchestration surfaces.
- Braintrust project comparison key for diagnostic experiments must be configured to a stable diagnostic identity, not left to variable input fields if input includes run/session-specific values.
- v1 does not generate an answer-quality compare report. It does provide a lightweight compare guard that reads diagnostic run/slice metadata and emits `same_row_set`, `overlap_only`, `dataset_version_drift`, and `empty_intersection` before analysts interpret Braintrust comparisons.

---

## File Plan

| Operation | Path | Purpose |
| --------- | ---- | ------- |
| Create | `backend/evals/diagnostic/__init__.py` | Package marker for shared diagnostic-track utilities. |
| Create | `backend/evals/diagnostic/models.py` | Typed contracts for diagnostic run identity, slice identity, selected rows, metadata payloads, and session id format. |
| Create | `backend/evals/diagnostic/dataset_selector.py` | Slice selector for `full_dataset`, `row_ids`, `field_filter`, and `manifest`, operating on raw CSV rows. |
| Create | `backend/evals/diagnostic/metadata_projector.py` | Build Braintrust metadata and Langfuse trace metadata from raw dataset row + run/slice identity. |
| Create | `backend/evals/diagnostic/annotation_export_joiner.py` | CLI/library for joining Langfuse scores export back to dataset rows by deterministic `session_id`. |
| Create | `backend/evals/diagnostic/compare_guard.py` | CLI/library for checking run-to-run comparability from diagnostic run and slice metadata. |
| Create | `backend/evals/diagnostic/run_manifest_writer.py` | Write platform-mode run manifests without rerunning the agent or pretending local outputs are available. |
| Create | `backend/evals/diagnostic/execution_scorer.py` | Non-quality health scorer that records execution completion and tool-call success. |
| Create | `backend/evals/scenarios/near_v1_diagnostic/dataset.csv` | Scenario-local copy of `artifacts/current/fin-lab_near-v1_diagnostic_dataset_codex.csv`. |
| Create | `backend/evals/scenarios/near_v1_diagnostic/eval_spec.yaml` | Scenario config with diagnostic identity settings and the execution-health scorer only. |
| Create | `backend/evals/scenarios/near_v1_diagnostic/README.md` | Operator guide: run examples, slice examples, Langfuse annotation schema, export join workflow. |
| Update | `backend/evals/eval_spec_schema.py` | Add optional `diagnostic` scenario config block while preserving `extra="forbid"`. |
| Update | `backend/evals/eval_tasks.py` | Add `run_near_v1_diagnostic()` and extend `_astream_collect()` to pass deterministic session id and trace metadata. |
| Update | `backend/evals/eval_runner.py` | Add diagnostic CLI flags, selected-row execution path, Braintrust metadata/experiment metadata, and selected raw-row CSV output alignment. |
| Update | `backend/evals/README.md` | Document the diagnostic human review track, commands, and platform caveats. |
| Update | `backend/evals/ARCHITECTURE.md` | Document the Braintrust / Langfuse split and diagnostic package boundary. |
| Update | `backend/agent_engine/agents/base.py` | Allow optional extra Langfuse metadata to be merged into trace metadata for `astream_run()`. |
| Update | `backend/tests/agents/test_orchestrator_langfuse.py` | Cover extra trace metadata propagation without changing existing defaults. |
| Create | `backend/tests/evals/test_diagnostic_dataset_selector.py` | Unit tests for all selector modes and validation errors. |
| Create | `backend/tests/evals/test_diagnostic_metadata_projector.py` | Unit tests for identity separation, metadata projection, and session id parsing. |
| Create | `backend/tests/evals/test_diagnostic_annotation_export_joiner.py` | Unit tests for Langfuse export pivot/join behavior. |
| Create | `backend/tests/evals/test_diagnostic_compare_guard.py` | Unit tests for same-row-set, overlap-only, version-drift, and empty-intersection compare guard behavior. |
| Create | `backend/tests/evals/test_diagnostic_run_manifest_writer.py` | Unit tests for platform-mode manifest shape and absence of local output columns. |
| Update | `backend/tests/evals/test_eval_spec_schema.py` | Tests for diagnostic config parsing and unknown-field rejection. |
| Update | `backend/tests/evals/test_eval_tasks.py` | Tests for diagnostic task prompt extraction, session id, and trace metadata forwarding. |
| Update | `backend/tests/evals/test_eval_runner.py` | Tests for diagnostic CLI flags, selected rows, local CSV output, and Braintrust `EvalCase` metadata. |
| Update | `backend/tests/evals/test_scorer_registry.py` | Optional explicit coverage that the diagnostic execution-health scorer resolves from config. |

**Structure sketch:**

```text
backend/evals/
  diagnostic/
    __init__.py
    models.py
    dataset_selector.py
    metadata_projector.py
    annotation_export_joiner.py
    compare_guard.py
    run_manifest_writer.py
    execution_scorer.py
  scenarios/
    near_v1_diagnostic/
      dataset.csv
      eval_spec.yaml
      README.md
```

### Task 1: Scenario Contract And Config Schema

**Files:**

- Create: `backend/evals/scenarios/near_v1_diagnostic/dataset.csv`
- Create: `backend/evals/scenarios/near_v1_diagnostic/eval_spec.yaml`
- Create: `backend/evals/scenarios/near_v1_diagnostic/README.md`
- Create: `backend/evals/diagnostic/__init__.py`
- Create: `backend/evals/diagnostic/execution_scorer.py`
- Update: `backend/evals/eval_spec_schema.py`
- Update: `backend/tests/evals/test_eval_spec_schema.py`
- Tests: `backend/tests/evals/test_scorer_registry.py` if scorer registry coverage needs one explicit diagnostic scorer resolution case

**What & Why:** Establish the scenario as a first-class eval scenario and add a small optional diagnostic config block to `ScenarioConfig`. This locks the dataset identity and avoids hardcoding `near_v1_diagnostic` behavior by scenario name inside runner logic.

**Approach Decision:**

| Option | Summary | Status | Why |
| ------ | ------- | ------ | --- |
| Optional `diagnostic:` config block in `eval_spec.yaml` | Generic runner can detect diagnostic behavior through config | Selected | Keeps behavior explicit, validates with Pydantic, avoids scenario-name conditionals. |
| Hardcode `scenario_name == "near_v1_diagnostic"` in runner | Quickest path | Rejected | Hidden coupling makes future diagnostic datasets harder and bypasses schema validation. |
| Empty `scorers: []` | No scores at all | Rejected | Braintrust docs describe `scores` as part of `Eval`; a deterministic code scorer can surface execution / tool-call health without judging answer quality. |

**Critical Contract / Snippet:**

```python
class DiagnosticScenarioConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    dataset_name: str
    dataset_version: str
    row_id_column: str = "id"
    question_column: str = "question"
    agent_version: str = "v1_baseline"
```

`eval_spec.yaml` should use:

```yaml
name: near_v1_diagnostic
csv: dataset.csv
diagnostic:
  dataset_name: near_v1_diagnostic
  dataset_version: "2026-04-24"
  row_id_column: id
  question_column: question
  agent_version: v1_baseline
task:
  function: backend.evals.eval_tasks.run_near_v1_diagnostic
column_mapping:
  question: input.question
scorers:
  - name: diagnostic_execution_health
    function: backend.evals.diagnostic.execution_scorer.execution_health
```

**Implementation Notes:**

- Copy `artifacts/current/fin-lab_near-v1_diagnostic_dataset_codex.csv` into the scenario directory without rewriting row contents.
- `diagnostic_execution_health` must be a deterministic code scorer, not an LLM-as-a-Judge scorer. It belongs to the diagnostic bounded context because it measures diagnostic execution health, not generic answer quality.
- The scorer must not inspect reference fields or judge response quality. It only records:
  - `execution_complete`: task produced a final response and did not hit the runner error marker.
  - `tool_call_all_successful`: all recorded tool calls completed without an error marker.
  - `tool_error_names`: names of tools whose calls failed.
- The score should be `1` only when `execution_complete=true` and `tool_call_all_successful=true`; otherwise `0`. The three fields above should be included in scorer metadata so reviewers can distinguish answer-quality issues from execution/tool-call failures.
- `README.md` must document the Langfuse annotation schema v1 fields from the design: `observed_outcome`, `observed_alignment_to_prompt`, `review_confidence`, `review_comment`, optional `observed_*`, `needs_followup`, `followup_note`.

**Test Strategy:** Schema tests prove diagnostic config is parsed, defaults apply, and unknown diagnostic fields fail. Scorer tests prove execution-health scorer returns 1 when execution completes and all tool calls succeed, returns 0 when execution fails or any tool call reports an error, emits `tool_error_names`, and does not depend on dataset reference hints.

**Verification:**

| Scope | Command | Expected Result | Why |
| ----- | ------- | --------------- | --- |
| Targeted schema/scorer | `uv run pytest backend/tests/evals/test_eval_spec_schema.py backend/tests/evals/test_scorer_registry.py -q` | Tests pass; diagnostic config parses and scorer resolves | Proves config contract and scorer registration. |
| Scenario discovery | `uv run pytest backend/tests/evals/test_eval_runner.py -q -k discover_scenarios` | Discovery tests pass after adding a case for `near_v1_diagnostic` | Proves the scenario is discoverable without executing LLM-backed scenarios. |

**Execution Checklist:**

- [ ] 🔴 Write schema and scorer tests for this checkpoint
- [ ] 🔴 Add mandatory scorer registry coverage in `backend/tests/evals/test_scorer_registry.py` proving `backend.evals.diagnostic.execution_scorer.execution_health` resolves from config
- [ ] 🔴 Run tests and confirm they **fail** because `diagnostic` config and scorer do not exist yet
- [ ] 🟢 Add diagnostic config model, scenario files, README, and execution-health scorer
- [ ] 🔵 Review config naming and scenario file boundaries; remove any unused config keys
- [ ] 🔵 Run tests again and confirm they **still pass** after refactor
- [ ] Commit the checkpoint when it is stable: `git commit -m "feat(evals): add near-v1 diagnostic scenario contract"`

---

### Task 2: Diagnostic Slice Selection

**Files:**

- Create: `backend/evals/diagnostic/models.py`
- Create: `backend/evals/diagnostic/dataset_selector.py`
- Create: `backend/tests/evals/test_diagnostic_dataset_selector.py`

**What & Why:** Implement deterministic row selection before execution. Selector must operate on raw CSV rows so `id` remains `"1"` instead of becoming `1.0`.

**Critical Contract / Snippet:**

```python
@dataclass(frozen=True)
class DiagnosticSliceIdentity:
    slice_label: str
    slice_type: Literal["full_dataset", "row_ids", "field_filter", "manifest"]
    slice_selector: str
    selected_row_ids: tuple[str, ...]
    slice_hash: str
```

Selector rules:

- `full_dataset`: default when no slice arg is supplied.
- `row_ids`: comma-separated ids, preserve requested order, reject duplicates and missing ids.
- `field_filter`: exactly one `column=value` equality filter against raw CSV string values.
- `manifest`: newline-delimited row ids; ignore blank lines and `#` comments; reject missing ids.
- `slice_label`: if omitted, derive stable labels such as `full`, `rows-1-3-7`, `filter-capability_band-boundary`, or `manifest-<stem>`.

**Implementation Notes:**

- Add a small `parse_diagnostic_slice_args()` helper or equivalent pure function that receives already-parsed CLI strings.
- `slice_hash` should be deterministic over `slice_type`, `slice_selector`, and `selected_row_ids`, e.g. first 12 hex chars of SHA-256.
- Add a small `resolve_git_commit()` helper in `backend/evals/diagnostic/models.py` or `backend/evals/diagnostic/metadata_projector.py` that returns `git rev-parse --short HEAD` when available and `unknown` otherwise. This value is recommended by the design and should be included in run metadata, but it must not block local tests.
- Reject combinations like `--row-ids` plus `--field-filter`; exactly one selector mode may be active.

**Test Strategy:** Unit tests cover all four selector modes, stable ordering, duplicate ids, missing ids, invalid field filter syntax, no-match filters, and deterministic `slice_hash`.

**Verification:**

| Scope | Command | Expected Result | Why |
| ----- | ------- | --------------- | --- |
| Targeted selector | `uv run pytest backend/tests/evals/test_diagnostic_dataset_selector.py -q` | Tests pass | Proves slice correctness independent of LLM/API calls. |
| Type surface | `uv run pyright backend/evals/diagnostic/models.py backend/evals/diagnostic/dataset_selector.py` | No type errors | Protects typed contracts used by runner. |

**Execution Checklist:**

- [ ] 🔴 Write selector tests for `full_dataset`, `row_ids`, `field_filter`, `manifest`, and validation failures
- [ ] 🔴 Run tests and confirm they **fail** because selector module does not exist
- [ ] 🟢 Implement the minimal selector and model contracts
- [ ] 🔵 Refactor only if duplicate row lookup or label derivation is unclear
- [ ] 🔵 Run targeted selector tests again and confirm they **still pass**
- [ ] Commit the checkpoint when it is stable: `git commit -m "feat(evals): add diagnostic dataset slicing"`

---

### Task 3: Identity And Langfuse Metadata Projection

**Files:**

- Create: `backend/evals/diagnostic/metadata_projector.py`
- Update: `backend/agent_engine/agents/base.py`
- Update: `backend/tests/agents/test_orchestrator_langfuse.py`
- Create: `backend/tests/evals/test_diagnostic_metadata_projector.py`

**What & Why:** Build one source of truth for Braintrust metadata, Langfuse trace metadata, and deterministic session id. Extend `Orchestrator.astream_run()` with optional extra trace metadata so diagnostic execution can attach `reference_*` context without bypassing the existing Langfuse integration.

**Approach Decision:**

| Option | Summary | Status | Why |
| ------ | ------- | ------ | --- |
| Deterministic Langfuse `session_id` plus trace metadata | Encode `dataset_name`, `run_label`, `row_id` in session id; also attach explicit metadata | Selected | Context7 confirms Langfuse scores export includes `session_id`; this makes score-only export join possible. |
| Join Langfuse scores export through traces export | Export scores and traces separately, join by `trace_id`, then by metadata | Rejected for v1 | More moving parts for reviewers; can be added later if Langfuse export shape changes. |
| Store identity only in Braintrust metadata | Keep Langfuse clean | Rejected | Breaks annotation export join and reviewer context. |

**Critical Contract / Snippet:**

```python
def build_diagnostic_session_id(
    *, dataset_name: str, run_label: str, row_id: str
) -> str:
    # Reject "::" in components before formatting.
    return f"{dataset_name}::{run_label}::{row_id}"
```

Langfuse metadata keys:

```python
{
    "row_id": row_id,
    "dataset_name": dataset_name,
    "dataset_version": dataset_version,
    "run_label": run_label,
    "run_group": run_group,
    "agent_version": agent_version,
    "experiment_name": experiment_name,
    "slice_label": slice_label,
    "slice_type": slice_type,
    "slice_selector": slice_selector,
    "reference_capability_band": raw_row["capability_band"],
    "reference_expected_behavior": raw_row["expected_near_v1_behavior"],
    "reference_primary_failure_mechanism": raw_row["primary_failure_mechanism"],
    "reference_secondary_failure_mechanism": raw_row["secondary_failure_mechanism"],
    "reference_best_source": raw_row["expected_best_source"],
    "reference_likely_tuning_lever": raw_row["likely_tuning_lever"],
    "reference_pass_signals": raw_row["draft_pass_signals"],
}
```

Braintrust metadata keys should include only execution/compare identity plus lightweight row descriptors:

```python
{
    "row_id": row_id,
    "dataset_name": dataset_name,
    "dataset_version": dataset_version,
    "run_label": run_label,
    "run_group": run_group,
    "slice_label": slice_label,
    "slice_type": slice_type,
    "agent_version": agent_version,
    "category": raw_row["category"],
    "capability_band": raw_row["capability_band"],
}
```

**Implementation Notes:**

- Add `trace_metadata: Mapping[str, object] | None = None` to `Orchestrator.astream_run()`.
- Merge `trace_metadata` into the `metadata` dict inside `_build_langfuse_config()` after existing base metadata, rejecting collisions with reserved keys unless the value is identical.
- Use `propagate_attributes(metadata=trace_metadata)` only if this does not conflict with existing tests; otherwise LangChain config metadata remains the primary path and `session_id` remains in `propagate_attributes`.
- Keep all new imports at module top unless one of the project import-style exceptions applies.

**Test Strategy:** Metadata projector tests prove exact key projection, no `observed_*` keys are generated, session id is parseable, and delimiter validation works. Orchestrator test proves extra metadata is present in LangChain config metadata and existing trace-name/request-id behavior remains unchanged.

**Verification:**

| Scope | Command | Expected Result | Why |
| ----- | ------- | --------------- | --- |
| Targeted metadata | `uv run pytest backend/tests/evals/test_diagnostic_metadata_projector.py backend/tests/agents/test_orchestrator_langfuse.py -q` | Tests pass | Proves metadata contract and shared Langfuse integration safety. |
| Type surface | `uv run pyright backend/evals/diagnostic/metadata_projector.py backend/agent_engine/agents/base.py` | No type errors | Protects shared agent API signature. |

**Execution Checklist:**

- [ ] 🔴 Write metadata projector and orchestrator metadata tests first
- [ ] 🔴 Run tests and confirm they **fail** because projector and `trace_metadata` support do not exist
- [ ] 🟢 Implement projector and minimal `Orchestrator.astream_run(trace_metadata=...)` support
- [ ] 🔵 Review metadata collision behavior and reserved key handling
- [ ] 🔵 Run targeted tests again and confirm they **still pass**
- [ ] Run broader affected Langfuse tests if shared orchestrator behavior changed: `uv run pytest backend/tests/agents/test_orchestrator_langfuse.py backend/tests/integration/test_langfuse_resilience.py -q`
- [ ] Commit the checkpoint when it is stable: `git commit -m "feat(evals): project diagnostic trace metadata"`

---

### Task 4: Runner Integration And Diagnostic Task Execution

**Files:**

- Create: `backend/evals/diagnostic/run_manifest_writer.py`
- Create: `backend/tests/evals/test_diagnostic_run_manifest_writer.py`
- Update: `backend/evals/eval_tasks.py`
- Update: `backend/evals/eval_runner.py`
- Update: `backend/tests/evals/test_eval_tasks.py`
- Update: `backend/tests/evals/test_eval_runner.py`

**What & Why:** Wire diagnostic selection and metadata projection into the existing runner while preserving old scenario behavior. Add CLI flags for run identity and slice selection, and pass diagnostic input to a new task function that calls `v1_baseline` with the row question only.

**Critical Contract / Snippet:**

```python
async def run_near_v1_diagnostic(input: Mapping[str, Any]) -> OrchestratorResult:
    question = str(input["question"])
    trace_metadata = input["trace_metadata"]
    session_id = str(input["session_id"])
    orchestrator = _get_orchestrator("v1_baseline")
    return await _astream_collect(
        orchestrator,
        question,
        session_id=session_id,
        trace_metadata=trace_metadata,
    )
```

CLI additions:

```text
--run-label TEXT
--run-group TEXT
--agent-version TEXT
--slice-label TEXT
--row-ids 1,3,7
--field-filter capability_band=boundary
--manifest path/to/row_ids.txt
```

Resolved run defaults:

- `run_label`: if omitted, generate `manual-YYYYmmdd-HHMMSS` in UTC and print it in the stderr banner.
- `run_group`: optional, default empty string or `manual`.
- `agent_version`: CLI overrides diagnostic config default.
- `experiment_name`: keep existing `{config.name}_{timestamp}` shape, but include `run_label`, `git_commit`, and slice identity in Braintrust experiment metadata and stderr banner.

**Implementation Notes:**

- Generic scenarios ignore diagnostic CLI flags unless `config.diagnostic` is present; if a user passes slice flags to a non-diagnostic scenario, fail fast with a clear error.
- Diagnostic row building should use `load_raw_csv_rows()` and selected raw rows. Do not rely on `load_dataset()` for `id`.
- For diagnostic `--local-only`, pass selected diagnostic `raw_data` into `_run_local_eval()` and selected `original_rows` into `write_result_csv()` so CSV rows align with selected row outputs.
- For diagnostic platform mode, do not call `_run_local_eval()` before `Eval()` and do not rely on Braintrust return-object row output shape. Build `EvalCase(input=case.input, expected={}, metadata=case.braintrust_metadata, id=case.case_id)`, call Braintrust `Eval()` once, flush, then write a local run manifest CSV with selected original rows plus identity columns (`row_id`, `session_id`, `experiment_name`, `run_label`, `slice_label`, `git_commit`, `braintrust_project`). The manifest is not a result CSV and must not include `output.*` columns.
- For generic non-diagnostic scenarios, preserve the current local pre-run + optional Braintrust upload behavior.
- Include Braintrust experiment metadata such as `dataset_name`, `dataset_version`, `run_label`, `run_group`, `slice_label`, `slice_type`, `selected_row_count`, `slice_hash`, `agent_version`, and `git_commit`.
- Keep runner sequential; do not introduce case concurrency under Braintrust global handler.

**Test Strategy:** Runner tests mock task/scorer imports and Braintrust imports to prove selected row count, input shape, metadata shape, CLI parsing, old local-only Braintrust import behavior, and diagnostic platform mode executes exactly once. Add manifest writer tests proving platform mode writes identity/run metadata but no `output.*` columns. Task tests mock `_get_orchestrator` and assert `astream_run()` receives question-only message, deterministic session id, and trace metadata.

**Verification:**

| Scope | Command | Expected Result | Why |
| ----- | ------- | --------------- | --- |
| Targeted runner/task | `uv run pytest backend/tests/evals/test_eval_tasks.py backend/tests/evals/test_eval_runner.py -q` | Tests pass | Proves diagnostic execution path and preserves runner behavior. |
| Full eval unit set | `uv run pytest backend/tests/evals -q` | Tests pass | Catches schema/runner/scorer interactions. |
| Local smoke with real agent | `uv run python -m backend.evals.eval_runner near_v1_diagnostic --local-only --row-ids 1 --run-label smoke-local --output-dir /tmp/near-v1-diagnostic-smoke` | Prints `Result: /tmp/near-v1-diagnostic-smoke/near_v1_diagnostic_*.csv`; CSV has one row with original dataset columns, `output.response`, `output.tool_outputs`, and `score_diagnostic_execution_health` | Proves end-to-end local execution when required LLM/tool env vars are configured. If env vars are missing, record that and rely on mocked unit tests until credentials are available. |
| Platform smoke with real agent | `uv run python -m backend.evals.eval_runner near_v1_diagnostic --row-ids 1 --run-label smoke-platform --output-dir /tmp/near-v1-diagnostic-platform-smoke` | Braintrust upload path executes once; local artifact is a run manifest CSV with one row and identity columns, not `output.*` columns | Proves platform path does not rerun the agent for local CSV output. |

**Execution Checklist:**

- [ ] 🔴 Write runner/task tests for diagnostic CLI, selected rows, metadata, and old scenario compatibility
- [ ] 🔴 Include a regression test that diagnostic platform mode does not call `_run_local_eval()` before Braintrust `Eval()`
- [ ] 🔴 Run tests and confirm they **fail** because runner/task integration does not exist
- [ ] 🟢 Implement diagnostic row building, CLI parsing, and `run_near_v1_diagnostic()`
- [ ] 🔵 Refactor duplicated local/platform EvalCase assembly if needed
- [ ] 🔵 Run targeted tests again and confirm they **still pass**
- [ ] Run full eval unit set: `uv run pytest backend/tests/evals -q`
- [ ] Commit the checkpoint when it is stable: `git commit -m "feat(evals): run sliced diagnostic evals"`

---

### Flow Verification: Diagnostic Execution Flow

> Tasks 1-4 complete the dataset selection -> near-v1 execution -> Braintrust/Langfuse identity metadata flow. These checks must pass before implementing export join behavior.

| # | Method | Step | Expected Result |
| - | ------ | ---- | --------------- |
| 1 | Runtime / function invocation | `uv run pytest backend/tests/evals/test_diagnostic_dataset_selector.py backend/tests/evals/test_diagnostic_metadata_projector.py backend/tests/evals/test_eval_tasks.py backend/tests/evals/test_eval_runner.py -q` | All tests pass | Confirms selector, metadata, task, and runner contracts. |
| 2 | Runtime / CLI | `uv run python -m backend.evals.eval_runner near_v1_diagnostic --local-only --row-ids 1 --run-label smoke-local --output-dir /tmp/near-v1-diagnostic-smoke` | One-row CSV is created; `id` column is `1`; output columns contain agent response/tool outputs; execution-health score is present | Confirms local end-to-end path when env vars are available. |
| 3 | Trace inspection | Open the Langfuse trace whose session id is `near_v1_diagnostic::smoke-local::1` | Trace metadata contains `row_id=1`, `run_label=smoke-local`, `reference_*` fields; no `observed_*` fields are prefilled | Confirms reviewer context is available and not conflated with annotation output. |
| 4 | Braintrust UI | `uv run python -m backend.evals.eval_runner near_v1_diagnostic --row-ids 1 --run-label smoke-platform --output-dir /tmp/near-v1-diagnostic-platform-smoke` with `BRAINTRUST_API_KEY` configured | Braintrust experiment appears under project `finlab-x`; local artifact is a manifest CSV with no `output.*` columns; case and experiment metadata include `row_id=1`, `run_label=smoke-platform`, `slice_type=row_ids`, `slice_label`, `agent_version`, and `git_commit` | Confirms platform compare surface and single-execution constraint. |

- [ ] All flow verifications pass, or any skipped platform verification is documented with missing env/platform reason.

---

### Task 5: Langfuse Export Joiner

**Files:**

- Create: `backend/evals/diagnostic/annotation_export_joiner.py`
- Create: `backend/tests/evals/test_diagnostic_annotation_export_joiner.py`
- Update: `backend/evals/scenarios/near_v1_diagnostic/README.md`

**What & Why:** Convert Langfuse score export rows into a discussion-ready CSV aligned with the original diagnostic dataset. The joiner should be deterministic and local; it must not call Langfuse APIs in v1.

**Critical Contract / Snippet:**

```text
Input:
  dataset.csv
  langfuse scores export CSV
  run_label

Join:
  score.session_id == "{dataset_name}::{run_label}::{row_id}"
  score.source == "ANNOTATION"
  score.observation_id is empty/null for trace-level v1 annotations

Output:
  original dataset columns
  observed_outcome
  observed_alignment_to_prompt
  review_confidence
  review_comment
  observed_primary_failure_mechanism
  observed_secondary_failure_mechanism
  observed_tuning_lever
  needs_followup
  followup_note
  langfuse_trace_id
  langfuse_session_id
```

Accepted annotation field values:

| Field | Accepted values |
| ----- | --------------- |
| `observed_outcome` | `strong_answer`, `acceptable_answer`, `partial_answer`, `failed_cleanly`, `failed_with_overreach` |
| `observed_alignment_to_prompt` | `high`, `medium`, `low` |
| `review_confidence` | `high`, `medium`, `low` |
| `review_comment` | Any text value exported in `string_value` or `comment` |
| `observed_primary_failure_mechanism` | Prefer dataset mechanism labels such as `tool_routing_error`, `evidence_synthesis_limit`, `source_coverage_gap`, `overreach_vs_abstain`; preserve unknown non-empty labels instead of failing the join |
| `observed_secondary_failure_mechanism` | Same handling as `observed_primary_failure_mechanism`; optional |
| `observed_tuning_lever` | Prefer dataset lever labels such as `none`, `max_tool_calls`, `tool_description`, `tavily_sources`; preserve unknown non-empty labels instead of failing the join |
| `needs_followup` | Boolean score values `1`/`0`, `true`/`false`, or categorical/text equivalents normalized to `true`/`false` |
| `followup_note` | Any text value; optional |

CLI shape:

```bash
uv run python -m backend.evals.diagnostic.annotation_export_joiner \
  --dataset backend/evals/scenarios/near_v1_diagnostic/dataset.csv \
  --scores-export /path/to/langfuse_scores.csv \
  --dataset-name near_v1_diagnostic \
  --run-label smoke-local \
  --output /tmp/near-v1-diagnostic-discussion.csv
```

**Implementation Notes:**

- Treat Langfuse score export as long-form rows and pivot by score `name`.
- Parse every score `session_id` with the diagnostic session-id parser and verify the parsed `dataset_name` and `run_label` match CLI inputs before accepting the row. Do not join by raw string construction alone.
- For `TEXT`, read `string_value`; for `CATEGORICAL`, read `string_value`; for `BOOLEAN`, normalize `value` `1`/`0` into `true`/`false`.
- Ignore score rows whose `source` is not `ANNOTATION` unless `--include-non-annotation` is explicitly added later; do not implement that flag in v1.
- If multiple annotation rows exist for the same `(session_id, name)`, select the latest by `updated_at` when available, otherwise `created_at`, otherwise file order.
- Preserve dataset row order in output.
- Add a `join_status` column with `annotated`, `missing_annotation`, or `partial_annotation`.
- Do not fail the whole join when some rows have no annotation; missing annotations are expected during partial review.

**Test Strategy:** Unit tests use tiny synthetic dataset and Langfuse scores exports to prove pivoting, trace-level filtering, latest score wins, missing annotations, BOOLEAN normalization, and rejection of malformed session ids.

**Verification:**

| Scope | Command | Expected Result | Why |
| ----- | ------- | --------------- | --- |
| Targeted joiner | `uv run pytest backend/tests/evals/test_diagnostic_annotation_export_joiner.py -q` | Tests pass | Proves export join behavior without platform calls. |
| CLI synthetic smoke | `uv run python -m backend.evals.diagnostic.annotation_export_joiner --dataset backend/evals/scenarios/near_v1_diagnostic/dataset.csv --scores-export /tmp/langfuse-scores-synthetic.csv --dataset-name near_v1_diagnostic --run-label smoke-local --output /tmp/near-v1-diagnostic-discussion.csv` | Output CSV exists; rows preserve dataset columns and include observed annotation columns; missing rows have `join_status=missing_annotation` | Proves operator-facing command works. |

**Execution Checklist:**

- [ ] 🔴 Write joiner tests using synthetic Langfuse score export rows
- [ ] 🔴 Run tests and confirm they **fail** because joiner does not exist
- [ ] 🟢 Implement joiner library functions and CLI
- [ ] 🔵 Refactor pivot/latest-row logic for readability if needed
- [ ] 🔵 Run targeted joiner tests again and confirm they **still pass**
- [ ] Commit the checkpoint when it is stable: `git commit -m "feat(evals): join diagnostic annotations export"`

---

### Flow Verification: Annotation Export Join Flow

> Task 5 completes the human annotation export -> discussion CSV flow.

| # | Method | Step | Expected Result |
| - | ------ | ---- | --------------- |
| 1 | Assertion script / CLI | Create a tiny synthetic Langfuse scores export with `session_id=near_v1_diagnostic::smoke-local::1`, `name=observed_outcome`, `source=ANNOTATION`, `data_type=CATEGORICAL`, `string_value=acceptable_answer`; run the joiner command | Output row for dataset `id=1` has `observed_outcome=acceptable_answer` and `join_status` not `missing_annotation` | Confirms score export pivot and join contract. |
| 2 | Manual Langfuse export | Export actual Langfuse scores after annotating one trace in Annotation Queue; run the joiner against the exported CSV | Output CSV contains original dataset columns plus `observed_*`; annotated rows carry reviewer values; unannotated rows are marked `missing_annotation` | Confirms real platform export shape. |

- [ ] All flow verifications pass, or platform export verification is documented as pending if no annotations exist yet.

---

### Task 6: Diagnostic Compare Guard

**Files:**

- Create: `backend/evals/diagnostic/compare_guard.py`
- Create: `backend/tests/evals/test_diagnostic_compare_guard.py`
- Update: `backend/evals/scenarios/near_v1_diagnostic/README.md`

**What & Why:** Provide a lightweight local guard that checks whether two diagnostic runs are comparable before an Analyst interprets Braintrust row-by-row compare output. Braintrust handles row matching through its comparison key; this guard handles diagnostic-specific comparability semantics such as full-vs-subset, cross-version drift, and empty intersections.

**Critical Contract / Snippet:**

```text
Input:
  run A diagnostic metadata
  run B diagnostic metadata

Output:
  status: same_row_set | intersection | overlap_only | dataset_version_drift | empty_intersection | dataset_version_mismatch
  row_count_a
  row_count_b
  intersection_size
  added_row_ids
  removed_row_ids
  warnings
```

CLI shape:

```bash
uv run python -m backend.evals.diagnostic.compare_guard \
  --run-a-manifest /path/to/run-a-manifest.csv \
  --run-b-manifest /path/to/run-b-manifest.csv \
  --output /tmp/diagnostic-compare-guard.json
```

**Implementation Notes:**

- Read diagnostic run metadata from platform-mode manifest CSVs or exported metadata files. Do not call Braintrust APIs in v1.
- Treat identical `dataset_version` + identical `selected_row_ids` as `same_row_set`.
- Treat same-version overlapping subsets as comparable over intersection and not `overlap_only`, matching the BDD scenarios.
- Treat full-vs-subset and cross-version full-vs-full as `overlap_only`; include `dataset_version_drift` when versions differ.
- Reject empty intersections with `empty_intersection`; do not produce parity statistics.
- Reject cross-version subset comparisons when row ids may not represent the same row content; use `dataset_version_mismatch` unless the implementation can prove row content identity.
- Document that Braintrust Project Settings should use a stable diagnostic comparison key such as row identity metadata; the guard does not replace Braintrust's row-by-row UI.

**Test Strategy:** Unit tests use tiny synthetic manifest/metadata inputs to prove identical subsets, overlapping subsets, full-vs-subset, full-vs-full version drift, cross-version subset mismatch, and empty-intersection behavior.

**Verification:**

| Scope | Command | Expected Result | Why |
| ----- | ------- | --------------- | --- |
| Targeted compare guard | `uv run pytest backend/tests/evals/test_diagnostic_compare_guard.py -q` | Tests pass | Proves run-to-run safety semantics without platform calls. |
| CLI synthetic smoke | `uv run python -m backend.evals.diagnostic.compare_guard --run-a-manifest /tmp/run-a.csv --run-b-manifest /tmp/run-b.csv --output /tmp/diagnostic-compare-guard.json` | Output JSON exists and contains the expected status / intersection metadata | Proves operator-facing command works. |

**Execution Checklist:**

- [ ] 🔴 Write compare guard tests for same-row-set, overlap-only, version-drift, cross-version mismatch, and empty-intersection behavior
- [ ] 🔴 Run tests and confirm they **fail** because compare guard does not exist
- [ ] 🟢 Implement compare guard library functions and CLI
- [ ] 🔵 Refactor status derivation only if the branching becomes unclear
- [ ] 🔵 Run targeted compare guard tests again and confirm they **still pass**
- [ ] Commit the checkpoint when it is stable: `git commit -m "feat(evals): add diagnostic compare guard"`

### Flow Verification: Compare Guard Flow

> Task 6 completes the run-to-run comparability guard before analysts interpret Braintrust comparisons.

| # | Method | Step | Expected Result |
| - | ------ | ---- | --------------- |
| 1 | CLI synthetic smoke | Create two tiny manifest CSVs with the same `dataset_version` and identical row ids; run compare guard | Output has `same_row_set=true`, `overlap_only=false`, and no `dataset_version_drift` |
| 2 | CLI synthetic smoke | Create full-vs-subset manifests on the same `dataset_version`; run compare guard | Output has `overlap_only=true`, `intersection_size` equal to subset size, and a warning not to treat aggregate as full-dataset improvement |
| 3 | CLI synthetic smoke | Create cross-version full manifests where v1.1 adds rows; run compare guard | Output has `overlap_only=true` and structured `dataset_version_drift` with added / removed row ids |

- [ ] All compare guard flow verifications pass.

---

### Task 7: Documentation, Repo Checks, And Delivery Verification

**Files:**

- Update: `backend/evals/README.md`
- Update: `backend/evals/ARCHITECTURE.md`
- Update: `backend/evals/scenarios/near_v1_diagnostic/README.md`

**What & Why:** Document the diagnostic track without mixing it with golden dataset / LLM judge scoring. Ensure all expected commands and platform caveats are discoverable by the next engineer.

**Implementation Notes:**

- Add a short "Diagnostic Human Review" track to `backend/evals/README.md`, distinct from Regression Guardrail and Quality Improvement scoring.
- Document example commands for full run, row id subset, field filter, manifest, Braintrust platform mode, Langfuse export join, and compare guard.
- Document Braintrust Project Settings comparison key expectation for diagnostic experiments.
- Update architecture docs to describe the dual-surface split: Braintrust for execution/compare, Langfuse for trace review/annotation.
- Avoid raw Mermaid blocks unless the repo docs already require them; if adding diagrams to docs, raw Mermaid is acceptable inside repository markdown but do not paste it into chat.

**Test Strategy:** Documentation itself has no unit tests, but final repo checks must cover all modified code and targeted smoke flows.

**Verification:**

| Scope | Command | Expected Result | Why |
| ----- | ------- | --------------- | --- |
| Eval unit tests | `uv run pytest backend/tests/evals -q` | All eval unit tests pass | Covers new selector/runner/joiner/compare guard and existing eval behavior. |
| Orchestrator Langfuse tests | `uv run pytest backend/tests/agents/test_orchestrator_langfuse.py -q` | Tests pass | Confirms shared metadata change is safe. |
| Type check | `uv run pyright backend/evals backend/agent_engine/agents/base.py backend/tests/evals backend/tests/agents/test_orchestrator_langfuse.py` | No type errors | Catches public contract mismatches. |
| Lint | `uv run ruff check backend/evals backend/tests/evals backend/agent_engine/agents/base.py backend/tests/agents/test_orchestrator_langfuse.py` | No lint errors | Keeps style consistent. |
| Optional format check | `uv run ruff format --check backend/evals backend/tests/evals backend/agent_engine/agents/base.py backend/tests/agents/test_orchestrator_langfuse.py` | No formatting changes needed | Confirms formatting. |

**Execution Checklist:**

- [ ] Update docs after code behavior is stable
- [ ] Run all verification commands in this task
- [ ] If any platform smoke is skipped, document exact missing env/platform dependency, such as `BRAINTRUST_API_KEY`, `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`, `LANGFUSE_HOST`, `OPENAI_API_KEY`, or scenario-specific tool keys like `TAVILY_API_KEY`
- [ ] Commit the checkpoint when it is stable: `git commit -m "docs(evals): document diagnostic annotation workflow"`

---

## Pre-delivery Checklist

### Code Level (TDD)

- [ ] Targeted verification for each task passes
- [ ] `uv run pytest backend/tests/evals -q` passes
- [ ] `uv run pytest backend/tests/agents/test_orchestrator_langfuse.py -q` passes
- [ ] `uv run pyright backend/evals backend/agent_engine/agents/base.py backend/tests/evals backend/tests/agents/test_orchestrator_langfuse.py` passes
- [ ] `uv run ruff check backend/evals backend/tests/evals backend/agent_engine/agents/base.py backend/tests/agents/test_orchestrator_langfuse.py` passes
- [ ] `uv run ruff format --check backend/evals backend/tests/evals backend/agent_engine/agents/base.py backend/tests/agents/test_orchestrator_langfuse.py` passes

### Flow Level (Behavioral)

- [ ] All flow verification steps executed and passed, or skipped platform steps have explicit missing-dependency notes
- [ ] Flow: Diagnostic Execution Flow — PASS / FAIL
- [ ] Flow: Annotation Export Join Flow — PASS / FAIL
- [ ] Flow: Compare Guard Flow — PASS / FAIL

### Summary

- [ ] Both levels pass -> ready for delivery
- [ ] Any failure is documented with cause and next action
