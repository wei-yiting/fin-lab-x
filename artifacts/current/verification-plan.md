# Verification Plan — Golden Dataset Evaluation Pipeline

## Meta

- Scenarios Reference: `artifacts/current/bdd-scenarios.md`
- Generated: 2026-04-24

### Verification method distribution

Total scenarios from `bdd-scenarios.md`: 36 illustrative (`S-`) + 5 journey (`J-`) = 41.

| Method               | Count | Covers                                                                                       |
| -------------------- | ----- | -------------------------------------------------------------------------------------------- |
| Deterministic        | 39    | All 36 `S-` scenarios + 3 journey scenarios (J-data-01, J-run-01, J-score-01)                |
| Browser Automation   | 0     | No web UI for this feature. Braintrust UI (external) is a Manual/UAT surface.                |
| Manual Behavior Test | 2     | J-bt-01 (Braintrust UI compare view) + J-cal-01 partial (SME annotation fill)                |
| User Acceptance Test | 1     | J-cal-01 (full first-time calibration acceptance from researcher perspective)                |

Note: J-cal-01 appears in both Manual Behavior Test (the SME-fill sub-step) and UAT (the full workflow acceptance) because the SME human-work step sits inside the larger acceptance flow.

### Entry-point and tooling references

- Runner CLI: `python -m backend.evals.eval_runner --scenario golden_dataset --version {v1|v2|v3} [--judge-model ALIAS] [--limit N]`
- Scripts: `python -m backend.evals.scripts.propose_sub_parts`, `... gen_calibration_template`, `... calibration_report`
- Scorer direct-call fixture pattern: `from backend.evals.scorers.citation_validity import citation_validity; citation_validity(output=..., expected=..., input=...)`
- Braintrust SDK query: `from braintrust import init; list(init(project="golden_dataset", experiment=NAME).fetch())`
- Agent config scan root: `backend/agent_engine/agents/versions/`
- `[POST-CODING: {...}]` tags mark info that requires codebase inspection after implementation.

### Shared fixture conventions

- **Valid dataset fixture** (`tests/fixtures/golden_dataset/valid_3rows.csv`): 3 rows covering one each of `target_version=v2`, `v3`, `v2+v3`; all JSON columns valid; all criterion cells filled.
- **Malformed fixtures** (one per failure mode): same shape as valid, with exactly one cell mutated to trigger fail-fast.
- **Fake-tool-output fixture**: Python dict `{response: "...", tool_outputs: [{tool: "...", output: "..."}]}` passed directly to scorer functions, bypassing the runner.
- **Clock freeze**: `freezegun.freeze_time("2026-04-24T15:30:00Z")` wraps tests that assert on experiment names / timestamps.

---

## Automated Verification — Deterministic

### Feature: Dataset & Spec Authoring

#### S-data-01: Malformed JSON list column blocks the run at load time

- **Method**: script (CLI invocation + exit code + stderr grep)
- **Steps**:
  1. Copy `tests/fixtures/golden_dataset/valid_3rows.csv` to `/tmp/bad_json.csv`.
  2. Edit row 2's `expected_sub_parts` cell to contain `["量級", "機制",]` (trailing comma, invalid JSON).
  3. Run: `SCENARIO_CSV=/tmp/bad_json.csv python -m backend.evals.eval_runner --scenario golden_dataset --version v1 --limit 3 2> /tmp/out.err; echo "EXIT=$?"`. `[POST-CODING: confirm dataset-override mechanism — env var SCENARIO_CSV, CLI flag --dataset, or fixture path injection.]`
  4. Assert: exit code is non-zero.
  5. Assert: stderr contains "row 2" (or row-id equivalent) AND contains "expected_sub_parts" AND contains "JSON" or "parse".
  6. Assert: no new Braintrust experiment starting with `golden_dataset-v1-` was created in the last 2 minutes (query via SDK with timestamp filter).
- **Expected**: Runner rejects the dataset at load and no experiment is created — fail-fast contract holds.

#### S-data-02: Missing required criterion cell blocks the run at load time

- **Method**: script
- **Steps**:
  1. Copy valid fixture to `/tmp/blank_crit.csv`, clear row 2's `pass_criterion_3` cell.
  2. Run `eval_runner --scenario golden_dataset --version v1 --limit 3` against it, capture stderr and exit code.
  3. Assert: exit code non-zero; stderr names row 2 and `pass_criterion_3`.
  4. Assert: no new Braintrust experiment created.
- **Expected**: Same fail-fast contract, applied to missing required cells (user decision Q2=B).

#### S-data-03: Valid dataset loads and JSON columns become typed values for scorers

- **Method**: script + Braintrust SDK verification
- **Steps**:
  1. Run `eval_runner --scenario golden_dataset --version v1 --limit 3` against the valid fixture.
  2. Wait for the run to complete (stdout prints `[ok] Verified 3 rows uploaded to Braintrust`).
  3. Fetch the experiment: `experiment = init(project="golden_dataset", experiment="<captured-name>")`; `rows = list(experiment.fetch())`.
  4. For each of the 3 rows, assert: `row.expected["tools"]` is a Python list (not a string), `row.expected["sub_parts"]` is a Python list.
- **Expected**: JSON strings are parsed before scorers receive them — no raw JSON strings reach `expected.*` in the uploaded experiment.

#### S-data-04: column_mapping delivers question/metadata/expected to the right fields

- **Method**: script + SDK field inspection
- **Steps**:
  1. Run the same `--limit 3` invocation as S-data-03.
  2. Fetch the experiment via SDK.
  3. For row 1 in the fixture (which has `question="..."`, `target_version="v2"`, `category="geopolitical_risk"`, `pass_criterion_1="..."`), assert: `row.input == <exact question string>`, `row.metadata["target_version"] == "v2"`, `row.metadata["category"] == "geopolitical_risk"`, `row.expected["criterion_1"] == <criterion text>`.
- **Expected**: `column_mapping` in `eval_spec.yaml` is applied correctly during load.

#### J-data-01: Researcher authors CSV in Google Sheets and runs a smoke eval

- **Method**: script + SDK + local file verification
- **Steps**:
  1. Use a CSV file that was actually exported from Google Sheets (part of the fixture suite) at `tests/fixtures/golden_dataset/from_sheets_3rows.csv` — includes potential gotchas like BOM, CRLF line endings, UTF-8 double-encoded strings.
  2. Run `eval_runner --scenario golden_dataset --version v1 --limit 3` against it.
  3. Assert: exit code 0; stdout shows `[ok] Verified 3 rows uploaded to Braintrust`.
  4. Fetch experiment via SDK; assert 3 rows present with populated scores across all 10+ Score streams (per §5).
  5. Assert: local result CSV on disk exists and has 3 rows. `[POST-CODING: path of local result CSV written by runner.]`
- **Expected**: Google Sheets exports round-trip cleanly through the runner with no encoding issues, producing scores on all rows.

---

### Feature: Eval Runner Execution

#### S-run-01: Only v1 config exists — cross-version assertion passes trivially

- **Method**: script
- **Steps**:
  1. In a staging workspace, ensure only `backend/agent_engine/agents/versions/v1_baseline/orchestrator_config.yaml` is present (no other `v*/orchestrator_config.yaml` directories with that file).
  2. Run `eval_runner --scenario golden_dataset --version v1 --limit 3 2>&1 | tee /tmp/run01.out`.
  3. Assert: exit code 0; stdout contains the banner line naming resolved agent model from v1 config.
  4. Assert: stdout does NOT contain "model mismatch".
- **Expected**: Single-config case passes assertion trivially; run proceeds.

#### S-run-02: Two configs with different model.name block the run

- **Method**: script
- **Steps**:
  1. Add a temporary `backend/agent_engine/agents/versions/v2_rag/orchestrator_config.yaml` with `model.name: <different pinned alias>` (different from v1's model.name).
  2. Run `eval_runner --scenario golden_dataset --version v2 --limit 3 2> /tmp/run02.err; echo "EXIT=$?"`.
  3. Assert: exit code non-zero; stderr contains `v1_baseline` AND `v2_rag` AND both model name strings.
  4. Assert: no new Braintrust experiment was created in the last 2 minutes.
  5. Cleanup: remove the temporary v2 config.
- **Expected**: Cross-version guard blocks before dispatch.

#### S-run-03: Judge model whitelist (table-driven)

- **Method**: script (parametrized)
- **Steps**: Run once per row in the table, capturing exit code and stderr. For each row, assert the resulting state.
  1. `eval_runner --scenario golden_dataset --version v1 --judge-model <model> --limit 1 2> /tmp/run03-<label>.err; echo $?`.
  2. Repeat with each value of `<model>`.

| label          | --judge-model value                  | expected exit | stderr must contain           |
| -------------- | ------------------------------------ | ------------- | ----------------------------- |
| pinned-valid   | `<gpt-5-mini pinned alias>`          | 0             | (banner only, no error)       |
| family-alias   | `gpt-5-mini`                         | non-zero      | "not in whitelist" + "gpt-5-mini" |
| off-whitelist  | `claude-sonnet-4-6-2026-01-10`       | non-zero      | "not in whitelist"            |

- **Expected**: Whitelist enforces pinned alias discipline; family and off-whitelist values block.

#### S-run-04: Env var substitution resolves before whitelist validation

- **Method**: script (parametrized, with env var control)
- **Steps**:
  1. Set `eval_spec.yaml` specificity scorer to `model: ${JUDGE_MODEL:-<gemini-2.5-flash pinned alias>}` (fixture copy, not the real spec).
  2. Run once per table row, setting/unsetting `JUDGE_MODEL` in the environment.

| env state                                              | expected exit | verification                                                                                       |
| ------------------------------------------------------ | ------------- | -------------------------------------------------------------------------------------------------- |
| `JUDGE_MODEL` unset                                    | 0             | Fetch experiment; `metadata.judge_model == "<gemini-2.5-flash pinned alias>"`                      |
| `JUDGE_MODEL=<gpt-5-mini pinned alias>`                | 0             | `metadata.judge_model == "<gpt-5-mini pinned alias>"`                                              |
| `JUDGE_MODEL=claude-sonnet-4-6-2026-01-10`             | non-zero      | stderr contains "not in whitelist" — proving substitution ran before validation                    |

- **Expected**: Substitution happens in `_load_yaml_mapping` before Pydantic sees the value, so whitelist checks the resolved string.

#### S-run-05: Same-vendor agent and judge print warn banner and continue

- **Method**: script + stdout grep
- **Steps**:
  1. Configure v1 config `model.name: <gpt-5-mini pinned alias>` (openai) and eval_spec specificity `model: <gpt-5-mini pinned alias>` (openai) — both same vendor.
  2. Run `eval_runner --scenario golden_dataset --version v1 --limit 1 2>&1 | tee /tmp/run05.out`.
  3. Assert: stdout contains `[warn]` AND `judge and agent share vendor 'openai'`.
  4. Assert: exit code 0; the run completed (experiment exists in Braintrust with 1 row).
- **Expected**: Warn banner appears but does not block.

#### S-run-06: Cross-vendor agent and judge — no warn banner

- **Method**: script + stdout grep
- **Steps**:
  1. Configure v1 `model.name: <gpt-5-mini pinned alias>` (openai) and eval_spec specificity `model: <gemini-2.5-flash pinned alias>` (google).
  2. Run `eval_runner --scenario golden_dataset --version v1 --limit 1 2>&1 | tee /tmp/run06.out`.
  3. Assert: stdout shows both vendors in banner; stdout does NOT contain `[warn] judge and agent share vendor`.
- **Expected**: Silent banner — no unnecessary warning.

#### S-run-07: `--limit 3` runs 3 rows and uploads 3 to Braintrust

- **Method**: script + SDK + stdout grep
- **Steps**:
  1. Run `eval_runner --scenario golden_dataset --version v1 --limit 3 2>&1 | tee /tmp/run07.out`.
  2. Assert stdout contains `[ok] Verified 3 rows uploaded to Braintrust`.
  3. Parse the experiment name from stdout (pattern `golden_dataset-v1-<timestamp>`).
  4. Fetch via SDK: `rows = list(init(project="golden_dataset", experiment=NAME).fetch()); assert len(rows) == 3`.
  5. Assert: every row has a non-empty `scores` dict.
- **Expected**: Exactly 3 rows executed and uploaded; upload verification confirms.

#### S-run-08: Row-count mismatch logs error but exits 0

- **Method**: script + mocked SDK
- **Steps**:
  1. Wrap the Braintrust fetch to return fewer rows than uploaded (monkey-patch or integration-test helper): `[POST-CODING: patch path for init().fetch() or its equivalent in eval_runner.py's upload verification step.]`
  2. Run `eval_runner --scenario golden_dataset --version v1 --limit 3 2>&1 | tee /tmp/run08.out; echo "EXIT=$?"`.
  3. Assert: stdout/stderr contains `[error] Upload verification: expected 3 rows, got <N>` where N < 3.
  4. Assert: exit code 0.
  5. Assert: local result CSV on disk has 3 rows. `[POST-CODING: local result CSV path.]`
- **Expected**: Mismatch is surfaced but never blocks — local results preserved.

#### S-run-09: V1 run on frozen clock produces exact experiment name

- **Method**: script + clock freeze
- **Steps**:
  1. With `freezegun.freeze_time("2026-04-24T15:30:00Z")` (or an equivalent test helper), run `eval_runner --scenario golden_dataset --version v1 --limit 1`.
  2. Parse the experiment name from stdout.
  3. Assert: name == `golden_dataset-v1-20260424-1530` (exact string match).
- **Expected**: Name format exactly matches §8.4 / §9.1; hyphen separator, UTC timestamp.

#### J-run-01: V1 smoke run end-to-end

- **Method**: script (full integration, ties together S-run-01, 03, 04-pass, 05 or 06, 07, 09, and S-data-03/04)
- **Steps**:
  1. Fresh workspace: only v1 config present; `.env` with `BRAINTRUST_API_KEY`, `OPENAI_API_KEY`; valid 30-row `dataset.csv`.
  2. Run `eval_runner --scenario golden_dataset --version v1 --limit 3 2>&1 | tee /tmp/j-run-01.out`.
  3. Assert banner shows: cross-version pass, whitelist pass, agent vendor, judge vendor, env substitution resolved.
  4. Assert stdout includes `[ok] Verified 3 rows uploaded to Braintrust`.
  5. Fetch experiment via SDK; assert 3 rows, metadata matches §9.2 schema, tags match §8.4.
  6. For row 1, assert Score streams present: `comprehensiveness_c1/c2/c3`, `completeness_sub_*` + `completeness_overall`, `faithfulness_*`, `numerical_faithfulness_*` (may be None), `answer_relevancy`, `citation_validity_*` (may be None), `tool_call_accuracy` (may be None), `specificity`.
- **Expected**: Full smoke run completes cleanly; Braintrust experiment is ready for inspection.

---

### Feature: Scorer Behaviors

#### S-score-01: tool_call_accuracy mode-driven outcome (table-driven)

- **Method**: direct scorer call (unit-boundary integration)
- **Steps**: For each row in the table below, construct the `output` and `expected` fixtures in Python and invoke the scorer.

```python
from backend.evals.scorers.tool_call_accuracy import tool_call_accuracy

cases = [
  # (expected_tools, mode, actual_tools, expected_score, expected_meta_key_value)
  (["sec_official_docs_retriever", "yfinance_stock_quote"],
   "all",
   ["sec_official_docs_retriever", "yfinance_stock_quote", "tavily_search"],
   1.0, {"missing": []}),
  (["sec_official_docs_retriever", "yfinance_stock_quote"],
   "all",
   ["sec_official_docs_retriever"],
   0.0, {"missing": ["yfinance_stock_quote"]}),
  (["yfinance_stock_quote", "sec_official_docs_retriever"],
   "strict_set",
   ["sec_official_docs_retriever", "yfinance_stock_quote"],
   1.0, None),
  (["yfinance_stock_quote", "sec_official_docs_retriever"],
   "strict_set",
   ["sec_official_docs_retriever", "yfinance_stock_quote", "tavily_search"],
   0.0, {"extras": ["tavily_search"]}),
  (["yfinance_stock_quote", "sec_official_docs_retriever"],
   "any",
   ["yfinance_stock_quote"],
   1.0, None),
]

for exp_tools, mode, actual, exp_score, exp_meta in cases:
    output = {"response": "...", "tool_outputs": [{"tool": t, "output": ""} for t in actual]}
    expected = {"tools": exp_tools, "tools_mode": mode}
    score = tool_call_accuracy(output=output, expected=expected, input="")
    assert score.score == exp_score
    if exp_meta:
        for k, v in exp_meta.items(): assert score.metadata[k] == v
```

- **Expected**: `all`, `strict_set`, `any` modes behave per §7.2. Set semantics; extras ignored only in `all`/`any`, penalized in `strict_set`.

#### S-score-02: tool_call_accuracy with empty expected_tools emits Score None

- **Method**: direct scorer call
- **Steps**:
  1. Call `tool_call_accuracy(output={"response":"x","tool_outputs":[]}, expected={"tools": [], "tools_mode": "all"}, input="")`.
  2. Assert: `score.score is None`; `score.metadata["reason"] == "no expected tools"`.
- **Expected**: Null path triggers on empty list — row not counted.

#### S-score-03: Dangling reference → Score 0 without LLM call

- **Method**: direct scorer call + LLM call counter
- **Steps**:
  1. Mock `autoevals.LLMClassifier.__call__` to count invocations.
  2. Construct `output = {"response": "Revenue grew 10% in FY2024 [2].\n\n**References**\n[1] https://sec.gov/x/10-K", "tool_outputs": [{"tool": "sec", "output": "https://sec.gov/x/10-K content"}]}` and `expected = {}` (citation_validity reads only output).
  3. Call `citation_validity(output=output, expected=expected, input="")`.
  4. Assert: returned Scores contain one Score with value `0` and metadata `reason` mentioning "not in References".
  5. Assert: LLM call counter is 0 for this citation.
- **Expected**: Programmatic guard triggers before any LLM cost.

#### S-score-04: Fabricated URL → Score 0 without LLM call

- **Method**: direct scorer call + LLM call counter
- **Steps**:
  1. Mock LLMClassifier to count invocations.
  2. `output = {"response": "Revenue [1]\n\n**References**\n[1] https://fake.example.com/earnings", "tool_outputs": [{"tool": "sec", "output": "unrelated content"}]}`.
  3. Call citation_validity.
  4. Assert: Score 0; metadata reason mentions "not in tool_outputs"; LLM call counter 0.
- **Expected**: URL-absence guard skips LLM cost.

#### S-score-05: Valid citation triggers LLM verify against source chunk

- **Method**: direct scorer call with stubbed LLM
- **Steps**:
  1. Stub `LLMClassifier` to return `{"name": "citation_support", "score": 1, "metadata": {"rationale": "stub"}}`.
  2. `output = {"response": "Revenue grew 10% [1]\n\n**References**\n[1] https://investor.nike.com/10-K", "tool_outputs": [{"tool": "sec", "output": "https://investor.nike.com/10-K - Revenue grew 10%"}]}`.
  3. Call citation_validity.
  4. Assert: exactly one LLM call invoked; Score 1 emitted with metadata including `ref_num="1"`, `url="https://investor.nike.com/10-K"`, `claim` containing "Revenue grew 10%".
- **Expected**: Both guards pass → LLM verify step runs → score based on judge verdict.

#### S-score-06: No citations → Score None

- **Method**: direct scorer call
- **Steps**:
  1. `output = {"response": "Revenue grew. No citations here.", "tool_outputs": [{"tool": "sec", "output": "..."}]}`.
  2. Call citation_validity.
  3. Assert: one Score; `score is None`; `metadata.reason == "no citations in response"`.
- **Expected**: Null path triggers when no attribution of any kind detected.

#### S-score-07: 4-digit year skipped; claim numbers verified per-claim

- **Method**: direct scorer call with stubbed LLM
- **Steps**:
  1. Stub LLMClassifier to return `score=1` for both numeric-faithfulness verify calls.
  2. `output = {"response": "Nike 2024 Q1 北美營收成長 5.7%, 達 $5.6B.", "tool_outputs": [...]}`; `input = "2024 年 Q1 Nike 北美營收成長多少？"`.
  3. Call numerical_faithfulness.
  4. Assert: exactly 2 Scores named `numerical_faithfulness_0` and `numerical_faithfulness_1`; both have `score=1`.
  5. Assert: no Score with metadata.number == "2024".
- **Expected**: Year filter applied; per-claim Scores emitted.

#### S-score-08: Fabricated number → Score 0 with context metadata

- **Method**: direct scorer call with stubbed LLM
- **Steps**:
  1. Stub LLMClassifier to return `score=0, metadata.rationale="value does not match source"`.
  2. `output = {"response": "營收成長 12%", "tool_outputs": [{"tool": "yfinance", "output": "revenue growth 5.7%"}]}`; `input = "營收成長多少？"`.
  3. Call numerical_faithfulness.
  4. Assert: one Score `numerical_faithfulness_0` = 0; metadata.number contains `12%`, metadata.context is non-empty, metadata.reason reflects judge rationale.
- **Expected**: Failure attribution metadata is rich enough for κ divergent-row analysis.

#### S-score-09: No numeric claims → Score None

- **Method**: direct scorer call
- **Steps**:
  1. `output = {"response": "預期衝擊有限，但未有具體數據。", "tool_outputs": []}`; `input = "..."`.
  2. Call numerical_faithfulness.
  3. Assert: exactly one Score; `score is None`; `metadata.reason == "no numeric claims"`.
- **Expected**: No-numbers path emits single null Score.

#### S-score-10: Completeness — all sub-parts covered

- **Method**: direct scorer call with stubbed LLM
- **Steps**:
  1. Stub LLMClassifier to return `score=1` for all 3 per-sub-part calls.
  2. `output = {"response": "量級 20%, 機制是供應鏈中斷, 應對是加強備料", ...}`; `expected = {"sub_parts": ["量級", "機制", "應對策略"]}`.
  3. Call completeness.
  4. Assert: 4 Scores emitted — `completeness_sub_1/2/3 = 1`, `completeness_overall = 1`.
- **Expected**: Per-sub-part + AND aggregate.

#### S-score-11: Completeness — one sub-part missing

- **Method**: direct scorer call with stubbed LLM
- **Steps**:
  1. Stub LLMClassifier to return `score=1` for sub_1 and sub_2, `score=0` for sub_3.
  2. Same inputs as S-score-10 but with response missing "應對" coverage.
  3. Call completeness.
  4. Assert: `completeness_sub_1 = 1`, `completeness_sub_2 = 1`, `completeness_sub_3 = 0`, `completeness_overall = 0`.
- **Expected**: AND aggregate drops to 0 when any sub is 0.

#### S-score-14: Completeness with empty `expected_sub_parts=[]` emits Score None

- **Method**: direct scorer call + LLM call counter
- **Steps**:
  1. Mock LLMClassifier to count invocations.
  2. `output = {"response": "任何內容", "tool_outputs": []}`; `expected = {"sub_parts": []}`.
  3. Call `completeness(output=output, expected=expected, input="...")`.
  4. Assert: returned value is a single Score (not a list of Scores).
  5. Assert: `score.name == "completeness"`, `score.score is None`, `score.metadata["reason"] == "no expected sub_parts"`.
  6. Assert: no `completeness_sub_*` or `completeness_overall=1.0` emitted.
  7. Assert: LLM call counter == 0 (no judge cost spent on empty sub_parts).
- **Expected**: Empty sub_parts list is treated explicitly as null, not as vacuous-True AND.

#### S-score-12: Comprehensiveness — 3 independent Scores

- **Method**: direct scorer call (YAML-loaded LLMClassifier blocks) with stubbed LLM
- **Steps**:
  1. Stub LLMClassifier to return `score=1` for c1, c2; `score=0` for c3.
  2. Load the 3 comprehensiveness scorers from `eval_spec.yaml` (fixture) with their rubric blocks.
  3. Invoke each block with `input`, `expected.criterion_N`, `output.response`.
  4. Collect all returned Scores.
  5. Assert: `comprehensiveness_c1 = 1`, `c2 = 1`, `c3 = 0`; no `comprehensiveness_overall` score exists.
- **Expected**: Three independent streams, no aggregate.

#### S-score-13: Judge retries exhausted → Score None, other rows unaffected

- **Method**: integration test with mocked HTTP (aiohttp/httpx mock to Gateway)
- **Steps**:
  1. Configure retry mock: the judge endpoint for row 2's `faithfulness_0` claim returns 429 on every call; other rows and other claims return normal responses.
  2. Run `eval_runner --scenario golden_dataset --version v1 --limit 3` against the 3-row valid fixture. `[POST-CODING: retry count/backoff specifics surfaced during impl — plug into mock accordingly.]`
  3. Fetch experiment via SDK.
  4. Assert: row 2's `faithfulness_0` has `score is None` and metadata contains `reason` mentioning "retries" or "exhausted".
  5. Assert: rows 1 and 3 have `faithfulness_0` with numeric scores (not None).
  6. Assert: experiment has 3 rows total (upload not aborted).
- **Expected**: Transient judge failures degrade gracefully to None without aborting the experiment.

#### J-score-01: Full scorer sweep for one row produces all 10+ Score streams

- **Method**: script + SDK
- **Steps**:
  1. Craft a single-row dataset at `tests/fixtures/golden_dataset/full_sweep_1row.csv` where:
     - Response has exactly 2 inline citations `[1]` and `[2]` with valid References and URLs present in tool_outputs
     - Response has exactly 3 numeric claims (plus 1 year to be skipped)
     - `expected_sub_parts` has 3 entries
     - `expected_tools = [A, B]` with mode `all`; agent called both
  2. Run `eval_runner --scenario golden_dataset --version v1 --limit 1` against this fixture.
  3. Fetch the experiment via SDK.
  4. Assert row 0's `scores` dict contains keys: `comprehensiveness_c1`, `c2`, `c3`, `completeness_sub_1`, `sub_2`, `sub_3`, `completeness_overall`, `faithfulness_0`, `_1`, `_2`, `numerical_faithfulness_0`, `_1`, `_2`, `answer_relevancy`, `citation_validity_0`, `_1`, `tool_call_accuracy`, `specificity`.
- **Expected**: Full dispatch works and all 10+ Score streams materialize in Braintrust.

---

### Feature: Braintrust Experiment Organization

#### S-bt-01: V1 run attaches metadata and tags matching §9.2 schema

- **Method**: script + SDK
- **Steps**:
  1. Stage: clean v1 config with known model alias; set `git_sha` via `git rev-parse HEAD` capture; freeze clock to 2026-04-24T15:30:00Z.
  2. Run `eval_runner --scenario golden_dataset --version v1 --limit 1`.
  3. Fetch experiment `golden_dataset-v1-20260424-1530` via SDK.
  4. Assert `experiment.metadata` keys: `version="v1"`, `agent_model=<known alias>`, `judge_model=<resolved alias>`, `git_sha=<captured sha>`, `run_id="2026-04-24T15:30:00Z"`, `limit=1`.
  5. Assert `experiment.tags` set equals `{"v1", "agent:openai", "judge:google", "golden_dataset"}` (or whatever vendors result from the aliases used).
- **Expected**: Metadata and tags match §9.2 exactly.

#### S-bt-02: V2 run picks latest V1 experiment as base_experiment

- **Method**: script + SDK pre-seeding
- **Steps**:
  1. Pre-seed Braintrust by running `eval_runner --version v1 --limit 1` twice with clock frozen at 2026-04-21T15:30:00Z then 2026-04-23T09:00:00Z (or use SDK to upload pre-built experiments with those names).
  2. Add a temporary v2 config with `model.name` identical to v1 (passes cross-version assert).
  3. Run `eval_runner --scenario golden_dataset --version v2 --limit 1`.
  4. Fetch the new V2 experiment via SDK.
  5. Assert: `experiment.metadata.base_experiment == "golden_dataset-v1-20260423-0900"` (the later of the two).
  6. Cleanup v2 config.
- **Expected**: `find_latest_experiment("golden_dataset-v1-")` returns the lexicographically-latest prefix-matching name.

#### S-bt-03: V2 run with no V1 baseline warns and continues

- **Method**: script
- **Steps**:
  1. Use a fresh Braintrust project name (`golden_dataset_test_<random>`) to guarantee no V1 experiments exist. `[POST-CODING: confirm per-test project override mechanism.]`
  2. Add a temporary v2 config with matching model.name.
  3. Run `eval_runner --scenario golden_dataset --version v2 --limit 1 2>&1 | tee /tmp/bt03.out`.
  4. Assert: stdout contains warning "no V1 baseline found" (or equivalent phrase).
  5. Fetch experiment; assert `base_experiment is None` (or absent from metadata).
  6. Assert exit code 0 — run completed.
  7. Cleanup.
- **Expected**: Graceful continue with explicit warning; experiment uploaded without a baseline link.

#### S-bt-04: V1 run sets base_experiment=None unconditionally

- **Method**: script + SDK
- **Steps**:
  1. Pre-seed project with prior V1 experiment (per S-bt-02 step 1 — one of them is enough).
  2. Run `eval_runner --scenario golden_dataset --version v1 --limit 1`.
  3. Fetch the new V1 experiment.
  4. Assert: `base_experiment` is None / absent from metadata.
- **Expected**: V1 is always its own baseline — no accidental chaining.

#### J-bt-01: V2 vs V1 compare view in Braintrust UI — *see Manual Behavior Test section*

---

### Feature: Human Calibration Workflow

#### S-cal-01: Template has variable-length completeness columns sized to max sub_parts

- **Method**: script + CSV header parsing
- **Steps**:
  1. Pre-seed a V1 experiment where the 10 calibration rows' sub_parts lengths are known: use a dataset fixture engineered so sub_parts = `[2, 3, 2, 4, 3, 2, 3, 2, 3, 2]` (max 4). `[POST-CODING: calibration row selection logic — if seeded, use seed; if first-10, use rows 1-10.]`
  2. Run `python -m backend.evals.scripts.gen_calibration_template --experiment <V1 experiment name>` → produces `annotation_<timestamp>.csv`.
  3. Read the CSV header row.
  4. Assert header contains exactly 4 completeness columns: `sme_completeness_sub_1`, `sme_completeness_sub_2`, `sme_completeness_sub_3`, `sme_completeness_sub_4`.
  5. Assert header contains the fixed SME columns: `sme_comp_c1`, `sme_comp_c2`, `sme_comp_c3`, `sme_faithfulness`, `sme_numerical_faithfulness`, `sme_answer_relevancy`, `sme_citation_validity`, `sme_specificity` (per §10.3).
  6. For a row in the generated CSV where the row's actual sub_parts count is 2, assert `sme_completeness_sub_3` and `sme_completeness_sub_4` are blank.
- **Expected**: Variable-column sizing per §10.3; blank cells for excess.

#### S-cal-02: All dims κ ≥ 0.7 → report marks all accept

- **Method**: script + markdown parsing
- **Steps**:
  1. Pre-seed a V1 experiment with 10 scored rows where all dims will produce κ ≥ 0.7.
  2. Pre-fill an annotation CSV matching that experiment such that SME and judge largely agree on every dim (e.g., both rate 9/10 rows the same).
  3. Run `python -m backend.evals.scripts.calibration_report --annotation <file> --experiment <exp>` → produces `calibration_report_<ts>.md`.
  4. Parse the markdown table.
  5. Assert: every dim row in the table has `[ok] accept` in the Verdict column.
  6. Assert: no dim row has `[warn] rewrite`.
- **Expected**: Full accept path produces clean report.

#### S-cal-03: One dim κ < 0.7 triggers rewrite mark, others accept

- **Method**: script + markdown parsing
- **Steps**:
  1. Pre-seed experiment + annotation such that `faithfulness` κ = 0.65, other dims κ ≥ 0.7.
  2. Run `calibration_report.py`.
  3. Parse the markdown.
  4. Assert: `faithfulness` row has `[warn] rewrite rubric`.
  5. Assert: `comprehensiveness_c1`, `completeness_sub_1`, others have `[ok] accept`.
  6. Assert: a "分歧 rows" section exists for `faithfulness` listing divergent rows with judge and SME verdicts.
- **Expected**: Per-dim independence with rich divergence reporting.

#### S-cal-05: Calibration report pins to a specific V1 experiment, not "latest"

- **Method**: script + SDK pre-seeding + markdown parsing
- **Steps**:
  1. Pre-seed Braintrust: upload two V1 experiments, `golden_dataset-v1-20260421-1530` (with engineered scores matching the fixture annotation) and `golden_dataset-v1-20260424-0900` (with different scores that would diverge from the fixture annotation).
  2. Prepare an annotation CSV `annotation_20260421-1545.csv` whose rows match the 2026-04-21 V1 experiment.
  3. Run `python -m backend.evals.scripts.calibration_report --annotation annotation_20260421-1545.csv --experiment golden_dataset-v1-20260421-1530` → produces `calibration_report_<ts>.md`.
  4. Parse the report header/metadata section.
  5. Assert: the report's header records `annotation: annotation_20260421-1545.csv` AND `experiment: golden_dataset-v1-20260421-1530`.
  6. Assert: the κ values in the report match the 2026-04-21 experiment's scores, not the 2026-04-24 experiment's. (Verify by re-running with `--experiment golden_dataset-v1-20260424-0900` against the same annotation and confirming κ values differ.)
- **Expected**: `--experiment` is a required pin; the CLI never silently defaults to "latest V1", which would make κ apples-to-oranges when a V1 rerun happens during annotation.

#### S-cal-04: Zero-variance unanimous agreement is treated as accept

- **Method**: script + markdown parsing
- **Steps**:
  1. Pre-seed annotation where SME marked all 10 cells for `specificity` as `1` and the judge scored all 10 as `1`.
  2. Run `calibration_report.py`.
  3. Parse the markdown.
  4. Assert: the `specificity` row shows κ as "undefined" (or equivalent handling, e.g., "N/A") AND raw agreement 100% AND Verdict `[ok] accept`.
- **Expected**: Degenerate-κ case falls back to raw-agreement-based accept, not reject.

#### J-cal-01: First-time calibration end-to-end through accept — see *User Acceptance Test* and *Manual Behavior Test* sections below

---

## Manual Verification — Manual Behavior Test

> Scenarios the Coding Agent cannot automate because they depend on human judgment (SME annotation) or an external UI (Braintrust compare view).

#### J-bt-01: V2 vs V1 compare view in Braintrust UI

- **Reason**: Braintrust UI rendering of compare-experiment view is an external service the pipeline does not control. Cannot be automated without browser automation for a URL outside our codebase.
- **Steps**:
  1. After running the S-bt-02 script setup, open `https://www.braintrust.dev/app` → navigate to project `golden_dataset`.
  2. Click the newest V2 experiment (e.g., `golden_dataset-v2-<timestamp>`).
  3. Find the Compare dropdown; verify it pre-selects or allows selection of the V1 baseline from S-bt-02.
  4. Verify per-row diff view appears with columns for V2 scores and V1 scores side-by-side.
  5. Verify at least one Score stream (e.g., `tool_call_accuracy`) shows a diff value.
- **Expected**: Researcher can load the compare view and see actionable per-row, per-score diffs without manual reconfiguration.

#### J-cal-01 (partial): SME fills the annotation CSV

- **Reason**: SME binary judgments are the ground truth input to κ; no automated substitute is meaningful for this step. ~100 cells × 1.5-2 hr human work.
- **Steps**:
  1. After S-cal-01 produces `annotation_<ts>.csv`, hand the file to the SME.
  2. SME opens in Google Sheets or Excel, fills each `sme_*` cell with `0`, `1`, or leaves blank for N/A.
  3. SME saves file, hands back.
- **Expected**: Completed annotation CSV matches template schema, ready for `calibration_report.py`.

---

## Manual Verification — User Acceptance Test

#### J-cal-01: First-time calibration end-to-end

- **Acceptance Question**: Can a researcher go from a fresh repo to an accepted calibration (all dims κ ≥ 0.7) and trust the V1 baseline for V2/V3 comparisons?
- **Steps**:
  1. Starting from a fresh workspace with only the curated 30-question dataset (no `expected_sub_parts` yet), run `python -m backend.evals.scripts.propose_sub_parts` → observe proposed sub_parts → review 30 rows in ≤ 30 minutes, editing where needed → commit updated `dataset.csv`.
  2. Run `eval_runner --scenario golden_dataset --version v1` (full 30 rows) → expect ~$0.50 and ~5-10 minute duration → confirm `[ok] Verified 30 rows uploaded`.
  3. Run `gen_calibration_template.py --experiment <name>` → get `annotation_<ts>.csv` with 10 rows.
  4. SME fills ~100 binary cells in 1.5-2 hours (per §10 estimate) → save.
  5. Run `calibration_report.py` → read the markdown report.
  6. If any dim κ < 0.7, rewrite that rubric (inline in `eval_spec.yaml` or `scorers/*.py`), re-run stages 2-5.
  7. When all dims `[ok] accept`, researcher proceeds to V2/V3 runs confident in the baseline.
- **Expected**:
  - Total elapsed time matches §14 estimate: ~0.5 hr sub_parts + 0.5 hr V1 run + 1.5-2 hr SME annotation + report + (0-2 rewrite loops).
  - Final V1 baseline has all 8 dims accepted; compare view for V2/V3 becomes interpretable.
  - Researcher's confidence check: "If I see V2's `faithfulness` average = 0.85 and V1's = 0.50, I believe that signals an architecture-level improvement, not rubric drift."

---

## Appendix: Shared verification prerequisites

- **Working Braintrust API key** with project creation rights (test project used: `golden_dataset_test_<suffix>` or similar isolated project to avoid polluting production).
- **Pinned judge aliases resolved**: the verification scripts hard-code the actual pinned dated aliases once §13 Open Dependencies land. Before that, scripts use the placeholder strings `<gpt-5-mini pinned alias>` and `<gemini-2.5-flash pinned alias>` and will fail whitelist validation — this is a signal that §13 is not yet complete.
- **Test data isolation**: every Braintrust-hitting test uses a suffixed project name (e.g., `golden_dataset_pytest_abc123`) to avoid polluting the real `golden_dataset` project. `[POST-CODING: confirm per-test project override mechanism.]`
- **Test cost budget**: the full verification suite runs ~40-60 LLM-judge calls (scoped-down dataset + stubs). Estimated cost < $0.10 per full run. Matches §5.2 scaling.
