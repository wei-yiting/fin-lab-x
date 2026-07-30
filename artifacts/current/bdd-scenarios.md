# BDD Scenarios — Golden Dataset Evaluation Pipeline

## Meta
- Design Reference: `artifacts/current/design.md`
- Generated: 2026-04-24
- Discovery Method: Three Amigos (Agent Teams — PO, Dev, QA all delivered full Round 1; QA delivery arrived after initial formulation and contributed two illustrative scenarios as late additions, noted inline with `Origin: QA`)

### User-resolved design decisions (input to these scenarios)

- **Cross-version assertion scope** (§8.8): `model.name` string equality only. Other model config fields (temperature, max_tokens, reasoning_effort) are NOT compared. Scenarios under Rule "Cross-version model assertion" test only `model.name`.
- **Dataset row hygiene**: fail-fast at dataset load. Any malformed JSON list column (`expected_tools`, `expected_sub_parts`) or any missing required cell (`pass_criterion_1/2/3`) blocks the whole run with exit non-zero. Per-row tolerance is explicitly rejected.
- **Experiment name collision** (§8.4 minute granularity): single-user tool assumption. No detection, no UUID suffix — Braintrust SDK default behavior is accepted. Not verified.

### Out-of-scope for these scenarios

- Concurrent runs / experiment name collision (user decision above)
- Temperature / max_tokens drift across versions (user decision above — only model.name is architecture-only gate)
- LLM judge quality / decision correctness (belongs in agent evaluation, not behavior test)
- Braintrust UI default column ordering (UI ergonomics, not system behavior)
- Retry policy tuning (judge retry semantics land on "emit score=None on exhausted retries" — single scenario covers this)

### Escalated assumptions to user (resolved)

- A1 (§8.8 scope) → resolved: model.name only
- A4 (CSV validation surface) → resolved: fail-fast at load
- A6 (single-user assumption) → resolved: single-user, accept collision risk

### Open design questions deferred to implementation

- A2: V1 system prompt citation format drift detection (current: docstring cross-reference, no automated check; scenarios verify scorer behavior at current format, not drift)
- A3: Braintrust Gateway silent model fallback (current: trust resolved `model` string in metadata; scenarios do not probe upstream routing)
- A7: "latest V1" baseline across reruns with different agent config (current: timestamp-latest wins; scenarios accept this and flag dataset_sha / git_sha for researcher review)
- A8: dataset_sha in experiment metadata (current: not in §9.2; design already lists git_sha; scenarios do not assert dataset hashing)
- A9: retry backoff/count tuning (current: emit score=None on exhaustion, continue run; scenarios cover the None-emission behavior, not the retry count)

---

## Feature: Dataset & Spec Authoring

### Context

The 30-row CSV (`dataset.csv`) and the YAML spec (`eval_spec.yaml`) together define what the eval measures. CSV has 13 columns (§4), with `expected_tools` and `expected_sub_parts` stored as JSON-string lists (Google Sheets round-trippable). `column_mapping` in the spec routes columns to Braintrust's `{input, expected, metadata}` shape.

### Rule: Dataset load rejects malformed or incomplete rows before any scorer runs

#### S-data-01: Malformed JSON list column blocks the run at load time
> Verifies that a single bad JSON cell aborts the whole run before any LLM call is paid

- **Given** `dataset.csv` has 30 rows and row 17's `expected_sub_parts` cell contains `["影響的量級", "機制",]` (trailing comma, invalid JSON)
- **When** the researcher runs `python -m backend.evals.eval_runner --scenario golden_dataset --version v1`
- **Then** the runner exits non-zero before dispatching any task, prints an error naming row 17 and the offending column, and no Braintrust experiment is created

Category: Illustrative
Origin: Dev

#### S-data-02: Missing required criterion cell blocks the run at load time
> Verifies that silent "comprehensiveness on empty criterion" cannot happen

- **Given** `dataset.csv` has 30 rows and row 8's `pass_criterion_3` cell is empty
- **When** the researcher runs `eval_runner --scenario golden_dataset --version v1`
- **Then** the runner exits non-zero at dataset load, prints an error naming row 8 and the missing column, and no experiment is created

Category: Illustrative
Origin: Dev

#### S-data-03: Valid dataset loads and JSON columns become typed values for scorers
> Verifies the happy-path transformation from CSV strings to parsed Python values

- **Given** `dataset.csv` has 30 rows, all required cells filled, all JSON-list cells valid
- **When** the runner loads the dataset
- **Then** each row's `expected.tools` is a Python list of strings (not the raw JSON string), `expected.sub_parts` is a Python list, and all scorer calls receive these parsed values

Category: Illustrative
Origin: PO

### Rule: column_mapping routes CSV columns to the correct Braintrust fields (§4.2)

#### S-data-04: column_mapping delivers question/metadata/expected to the right fields
> Verifies the §4.2 contract: `question → input`, `target_version → metadata.target_version`, `pass_criterion_1 → expected.criterion_1`

- **Given** row 5 has `question = "寶成(9904)受地緣政治風險的具體影響為何？"`, `target_version = "v2"`, `category = "geopolitical_risk"`, `pass_criterion_1 = "提到具體 10-K 引用"`
- **When** the runner constructs the Braintrust test unit for row 5
- **Then** the unit has `input = "寶成(9904)受地緣政治風險的具體影響為何？"`, `metadata.target_version = "v2"`, `metadata.category = "geopolitical_risk"`, and `expected.criterion_1 = "提到具體 10-K 引用"`

Category: Illustrative
Origin: PO

---

### Journey Scenarios

#### J-data-01: Researcher authors CSV in Google Sheets and runs a smoke eval
> Proves CSV authoring → round-trip through sheets copy-paste → runner load → scorer execution all work end-to-end

- **Given** a researcher has authored 3 rows in Google Sheets, exported as CSV, and saved as `dataset.csv`
- **When** they run `eval_runner --scenario golden_dataset --version v1 --limit 3`
- **Then** all 3 rows parse successfully, scorers execute with typed `expected.*` values, and the local result CSV on disk shows 3 rows × score streams populated

Category: Journey
Origin: Multiple

---

## Feature: Eval Runner Execution

### Context

`eval_runner.py` is the CLI entry point. New flags (`--version`, `--judge-model`, `--limit`), env var substitution in YAML, judge whitelist, cross-version model assertion, Braintrust Gateway routing, cross-vendor warning, and post-flush upload verification are all additions to the existing runner.

### Rule: V1/V2/V3 orchestrator configs must declare identical `model.name` (§8.8)

#### S-run-01: Only v1 config exists — cross-version assertion passes trivially
> Verifies the boundary case where the set of discovered configs has size 1

- **Given** only `backend/agent_engine/agents/versions/v1_baseline/orchestrator_config.yaml` exists with `model.name: gpt-5-mini-<pinned-alias>`
- **When** the researcher runs `eval_runner --scenario golden_dataset --version v1 --limit 3`
- **Then** the cross-version assertion passes, the run proceeds, and the banner shows the resolved agent model

Category: Illustrative
Origin: PO

#### S-run-02: Two configs with different model.name block the run
> Verifies that architecture-only comparison is enforced before any LLM call

- **Given** `v1_baseline/orchestrator_config.yaml` has `model.name: gpt-5-mini-2025-08-07` and `v2_rag/orchestrator_config.yaml` has `model.name: gpt-5-mini-2025-11-12`
- **When** the researcher runs `eval_runner --scenario golden_dataset --version v2`
- **Then** the runner exits non-zero before dispatching, prints an error naming both config paths and both model strings, and no Braintrust experiment is created

Category: Illustrative
Origin: PO

### Rule: Judge model must be on the approved pinned-alias whitelist (§8.3)

#### S-run-03: Whitelisted pinned alias passes; unknown model blocks
> Verifies `APPROVED_JUDGES` gate against `--judge-model` CLI override

- **Given** `APPROVED_JUDGES = {"<gpt-5-mini pinned alias>", "<gemini-2.5-flash pinned alias>"}` and the researcher passes `--judge-model <gpt-5-mini pinned alias>`
- **When** the runner starts
- **Then** whitelist validation passes and the run proceeds

| judge_model passed                        | expectation        | notes                                                                 |
| ----------------------------------------- | ------------------ | --------------------------------------------------------------------- |
| `<gpt-5-mini pinned alias>`               | passes             | on whitelist                                                          |
| `gpt-5-mini`                              | blocks             | family alias, not a pinned dated alias — not in whitelist             |
| `claude-sonnet-4-6-2026-01-10`            | blocks             | off whitelist                                                         |

Category: Illustrative (table-driven)
Origin: PO

### Rule: `${VAR}` and `${VAR:-default}` are resolved before validation (§8.2)

#### S-run-04: Env var substitution resolves before whitelist validation
> Verifies the critical ordering: substitution happens inside `_load_yaml_mapping`, before `ScorerConfig.model_validate` sees the value

- **Given** `eval_spec.yaml` has `model: ${JUDGE_MODEL:-<gemini-2.5-flash pinned alias>}` for the specificity scorer

| env state                                              | resolved model                                     | outcome       |
| ------------------------------------------------------ | -------------------------------------------------- | ------------- |
| `JUDGE_MODEL` unset                                    | `<gemini-2.5-flash pinned alias>` (default)        | whitelist ok  |
| `JUDGE_MODEL=<gpt-5-mini pinned alias>`                | `<gpt-5-mini pinned alias>`                        | whitelist ok  |
| `JUDGE_MODEL=claude-sonnet-4-6-2026-01-10`             | `claude-sonnet-4-6-2026-01-10`                     | whitelist blocks at validation |

- **When** the runner starts
- **Then** the resolved value (not the `${...}` literal) is what whitelist validation sees

Category: Illustrative (table-driven)
Origin: Multiple (PO seeded, Dev raised nested/colon edge cases — those remain unit tests per design)

### Rule: Cross-vendor agent+judge is a warning, not a block (§8.5)

#### S-run-05: Same-vendor agent and judge print warn banner and continue
> Verifies the warn-not-block contract from §1 and §8.5

- **Given** agent model resolves to `<gpt-5-mini pinned alias>` (vendor: openai) and judge model resolves to `<gpt-5-mini pinned alias>` (vendor: openai)
- **When** the runner starts
- **Then** the banner prints both vendors, followed by `[warn] judge and agent share vendor 'openai'. Cross-vendor recommended to avoid self-enhancement bias.`, and the run proceeds to completion

Category: Illustrative
Origin: PO

#### S-run-06: Cross-vendor agent and judge print no warn, run normally
> Verifies that different vendors produce a clean banner with no warning

- **Given** agent model `<gpt-5-mini pinned alias>` (openai) and judge model `<gemini-2.5-flash pinned alias>` (google)
- **When** the runner starts
- **Then** the banner shows both vendors on separate lines, no warn message is printed, and the run proceeds

Category: Illustrative
Origin: PO

### Rule: `--limit N` runs only the first N rows of the dataset

#### S-run-07: `--limit 3` executes 3 rows and uploads 3 to Braintrust
> Verifies dataset slicing end-to-end through upload

- **Given** `dataset.csv` has 30 valid rows
- **When** the researcher runs `eval_runner --scenario golden_dataset --version v1 --limit 3`
- **Then** exactly 3 rows are dispatched to the task function, the resulting Braintrust experiment contains 3 rows, and upload verification reports `[ok] Verified 3 rows uploaded to Braintrust`

Category: Illustrative
Origin: PO

### Rule: Upload verification runs post-flush and reports mismatch non-blockingly (§8.7)

#### S-run-08: Row-count mismatch post-flush logs error but exits 0
> Verifies that upload issues don't discard local results

- **Given** a run completed 30 rows locally but Braintrust fetch returns only 27 rows post-flush
- **When** upload verification runs
- **Then** the runner logs `[error] Upload verification: expected 30 rows, got 27`, the local result CSV on disk still contains 30 rows, and the runner exits 0

Category: Illustrative
Origin: PO

### Rule: Experiment name follows `{scenario}-{version}-{YYYYMMDD-HHMM}` format (§8.4)

#### S-run-09: V1 run on 2026-04-24 at 15:30 produces name `golden_dataset-v1-20260424-1530`
> Verifies name format with hyphen separator

- **Given** the current time is 2026-04-24 15:30 UTC
- **When** the researcher runs `eval_runner --scenario golden_dataset --version v1`
- **Then** the Braintrust experiment name is exactly `golden_dataset-v1-20260424-1530`

Category: Illustrative
Origin: PO

---

### Journey Scenarios

#### J-run-01: V1 smoke run end-to-end
> Proves the full pipeline: CLI → config scan → whitelist → substitution → banner → Gateway → 3 rows × 10+ Score streams → upload → verify

- **Given** a fresh repo with only `v1_baseline/orchestrator_config.yaml`, valid `dataset.csv` (30 rows), valid `eval_spec.yaml`, and `.env` with `BRAINTRUST_API_KEY`, `OPENAI_API_KEY`
- **When** the researcher runs `eval_runner --scenario golden_dataset --version v1 --limit 3`
- **Then** the banner shows cross-version pass / whitelist pass / agent+judge vendors / env substitution resolved; 3 rows execute through Braintrust Gateway; upload verification prints `[ok] Verified 3 rows uploaded to Braintrust`; and the researcher can open Braintrust UI to find `golden_dataset-v1-{date-time}` with 3 rows × scores across all 8 dimensions

Category: Journey
Origin: Multiple

---

## Feature: Scorer Behaviors

### Context

8 evaluation dimensions, expanded to 10+ Braintrust Score streams (§5). Three programmatic / hybrid scorers (`tool_call_accuracy`, `citation_validity`, `numerical_faithfulness`) and two per-element LLM-judge scorers (`completeness`, `faithfulness`) are custom Python. Three more (`comprehensiveness` × 3, `answer_relevancy`, `specificity`) are YAML `LLMClassifier` blocks. The scenarios below cover **structural behavior** of the scorers — not LLM judge quality.

### Rule: `tool_call_accuracy` supports three expected-mode semantics (§7.2)

#### S-score-01: tool_call_accuracy mode-driven outcome
> Verifies `all` / `any` / `strict_set` semantics via set operations on tool names

- **Given** `expected_tools = <expected>`, `expected_tools_mode = <mode>`, and the agent invoked the tools in `<actual>`
- **When** `tool_call_accuracy` runs
- **Then** the score is `<score>` with metadata recording `mode`, `expected`, `actual`, `missing`, `extras`

| expected                                           | mode        | actual                                                               | score | notes                                     |
| -------------------------------------------------- | ----------- | -------------------------------------------------------------------- | ----- | ----------------------------------------- |
| `[sec_official_docs_retriever, yfinance_stock_quote]` | `all`       | `[sec_official_docs_retriever, yfinance_stock_quote, tavily_search]` | 1.0   | expected ⊆ actual; extras allowed         |
| `[sec_official_docs_retriever, yfinance_stock_quote]` | `all`       | `[sec_official_docs_retriever]`                                      | 0.0   | `missing = [yfinance_stock_quote]`        |
| `[yfinance_stock_quote, sec_official_docs_retriever]` | `strict_set`| `[sec_official_docs_retriever, yfinance_stock_quote]`                | 1.0   | set equality, order irrelevant            |
| `[yfinance_stock_quote, sec_official_docs_retriever]` | `strict_set`| `[sec_official_docs_retriever, yfinance_stock_quote, tavily_search]` | 0.0   | `extras = [tavily_search]` breaks strict  |
| `[yfinance_stock_quote, sec_official_docs_retriever]` | `any`       | `[yfinance_stock_quote]`                                             | 1.0   | non-empty intersection                    |

Category: Illustrative (table-driven)
Origin: PO

#### S-score-02: tool_call_accuracy with empty expected_tools emits Score None
> Verifies "no expectations declared" produces N/A, not 0 (design §7.2)

- **Given** `expected_tools = []` for a row (author deliberately declares no tool expectation)
- **When** `tool_call_accuracy` runs
- **Then** the scorer emits `Score(name="tool_call_accuracy", score=None, metadata={"reason": "no expected tools"})` — the row is not counted as pass or fail

Category: Illustrative
Origin: PO

### Rule: `citation_validity` pre-filters dangling and fabricated citations before any LLM call (§7.3)

#### S-score-03: Dangling reference number → Score 0 without LLM call
> Verifies the programmatic guard: cited ref `[N]` not present in `**References**` section produces 0 immediately

- **Given** a response containing `"Revenue grew 10% in FY2024 [2]."` and a References block listing only `[1] https://sec.gov/...`
- **When** `citation_validity` runs
- **Then** the scorer emits `Score 0` for that citation with metadata `reason="ref num 2 not in References section"`, and the LLM verify step for this citation is skipped

Category: Illustrative
Origin: PO

#### S-score-04: Fabricated URL (not in any tool_output) → Score 0 without LLM call
> Verifies the second programmatic guard: cited URL absent from tool outputs produces 0 immediately

- **Given** a response citing `[1]` pointing to `https://fake.example.com/earnings`, and `tool_outputs` contains no occurrence of that URL
- **When** `citation_validity` runs
- **Then** the scorer emits `Score 0` with metadata `reason="citation URL not in tool_outputs"`, and no LLM call is made for this citation

Category: Illustrative
Origin: PO

#### S-score-05: Valid citation triggers LLM verify against source chunk
> Verifies the hybrid flow reaches the LLM judge step only after passing both programmatic guards

- **Given** a response with `"Revenue grew 10% [1]"` and References `[1] https://investor.nike.com/10-K`; tool outputs contain a chunk retrieved from `https://investor.nike.com/10-K` supporting the 10% claim
- **When** `citation_validity` runs
- **Then** the scorer invokes `LLMClassifier` with the surrounding claim and the source chunk, and emits `Score 1` or `Score 0` based on the judge's verdict

Category: Illustrative
Origin: PO

#### S-score-06: Response with no citations at all emits Score None
> Verifies the "no citations" null path from §7.3

- **Given** a response with no inline `[N]`, no `**References**` section, and no natural-language attribution (no "according to X" / "根據 X")
- **When** `citation_validity` runs
- **Then** the scorer emits `Score(name="citation_validity", score=None, metadata={"reason": "no citations in response"})`

Category: Illustrative
Origin: PO

### Rule: `numerical_faithfulness` filters incidental and year numbers, then verifies each remaining claim (§7.1)

#### S-score-07: 4-digit year is skipped, claim numbers are verified per-claim
> Verifies the extractor filter and per-number Score emission

- **Given** a question "2024 年 Q1 Nike 北美營收成長多少？", a response "Nike 2024 Q1 北美營收成長 5.7%, 達 $5.6B.", and tool outputs supporting both 5.7% and $5.6B
- **When** `numerical_faithfulness` runs
- **Then** exactly 2 Scores are emitted: `numerical_faithfulness_0` for 5.7% and `numerical_faithfulness_1` for $5.6B, both = 1; the `2024` is skipped (4-digit year + question overlap)

Category: Illustrative
Origin: PO

#### S-score-08: Fabricated number detected by judge → Score 0 with context metadata
> Verifies per-number failure attribution

- **Given** a response "營收成長 12%" while tool outputs only support 5.7%
- **When** `numerical_faithfulness` runs
- **Then** `numerical_faithfulness_0` = 0 with metadata containing the extracted number `12%`, the surrounding ±80-char context, and the judge's reason

Category: Illustrative
Origin: PO

#### S-score-09: Response with no numeric claims emits Score None
> Verifies the null path

- **Given** a response "預期衝擊有限，但未有具體數據" (no numbers)
- **When** `numerical_faithfulness` runs
- **Then** one Score is emitted: `Score(name="numerical_faithfulness", score=None, metadata={"reason": "no numeric claims"})`

Category: Illustrative
Origin: PO

### Rule: `completeness` emits per-sub-part Scores + one `_overall` AND aggregate (§5.1)

#### S-score-10: All sub-parts covered → per-sub Scores 1 and overall = 1
> Verifies AND aggregation happy path

- **Given** a row with `expected_sub_parts = ["量級", "機制", "應對策略"]` and a response covering all three
- **When** `completeness` runs
- **Then** four Scores emit: `completeness_sub_1 = 1`, `completeness_sub_2 = 1`, `completeness_sub_3 = 1`, `completeness_overall = 1`

Category: Illustrative
Origin: PO

#### S-score-11: One sub-part missing → that sub = 0 and overall = 0
> Verifies AND aggregation with partial coverage

- **Given** the same row as S-score-10 and a response covering "量級" and "機制" but not "應對策略"
- **When** `completeness` runs
- **Then** `completeness_sub_1 = 1`, `completeness_sub_2 = 1`, `completeness_sub_3 = 0`, `completeness_overall = 0`

Category: Illustrative
Origin: PO

#### S-score-14: Completeness with empty `expected_sub_parts=[]` emits Score None (not vacuous 1.0)
> Verifies that vacuous AND over an empty sub-part set does not silently inflate the overall score

- **Given** a row whose `expected_sub_parts` parses to `[]` (author deliberately indicated "no sub-part breakdown required") — contrast with a row where the column is entirely missing, which fails at dataset load per user decision Q2=B
- **When** `completeness` runs
- **Then** a single Score is emitted: `completeness` with `score=None` and `metadata.reason="no expected sub_parts"`; no `completeness_sub_*` Scores and no `completeness_overall = 1.0` from vacuous AND

Category: Illustrative
Origin: QA

### Rule: `comprehensiveness` emits 3 independent Scores with no aggregate (§5.1)

#### S-score-12: Partial criteria coverage produces independent per-criterion Scores
> Verifies §5.1's "no `_overall`" decision

- **Given** a row with `pass_criterion_1/2/3` all filled and a response covering criteria 1 and 2 but not 3
- **When** the 3 comprehensiveness `LLMClassifier` blocks run (one per criterion)
- **Then** `comprehensiveness_c1 = 1`, `comprehensiveness_c2 = 1`, `comprehensiveness_c3 = 0`, and no `comprehensiveness_overall` Score is emitted

Category: Illustrative
Origin: PO

### Rule: LLM-judge scorer emits `score=None` when the judge call fails after retries (A9 convention)

#### S-score-13: Exhausted judge retries → Score None with reason, other rows unaffected
> Verifies that transient judge failures don't abort the whole experiment

- **Given** a run of 3 rows where row 2's `faithfulness` judge call fails with 429 on all retry attempts
- **When** `faithfulness` finishes for all 3 rows
- **Then** row 2 emits `Score(name="faithfulness_0", score=None, metadata={"reason": "judge retries exhausted"})`, rows 1 and 3 produce normal `Score 1`/`0`, and the Braintrust experiment uploads all 3 rows

Category: Illustrative
Origin: Dev (CC-4)

---

### Journey Scenarios

#### J-score-01: Full scorer sweep for one row produces all 10+ Score streams
> Proves the end-to-end dispatch: one row's `response + tool_outputs` flows through all scorers and produces the expected Score stream shape

- **Given** a row whose response has 2 citations, 3 numeric claims, covers 3 sub-parts, and the agent invoked the expected 2 tools
- **When** the runner executes all 8 scorers for this row
- **Then** the row's Score streams in Braintrust include `comprehensiveness_c1/c2/c3`, `completeness_sub_1/2/3 + overall`, `faithfulness_0/1/2`, `numerical_faithfulness_0/1/2`, `answer_relevancy`, `citation_validity_0/1`, `tool_call_accuracy`, `specificity` — matching §5 expected stream shape

Category: Journey
Origin: Multiple

---

## Feature: Braintrust Experiment Organization

### Context

Every run produces one Braintrust experiment with a deterministic name (§8.4, §9.1), structured metadata (§9.2), tags, and a base_experiment pointer for compare view (§9.3). V1 runs have no base; V2/V3 runs look up the latest V1 experiment by prefix match.

### Rule: Every experiment carries structured metadata and tags suitable for filtering (§9.2)

#### S-bt-01: V1 run attaches metadata and tags matching §9.2 schema
> Verifies metadata completeness and tag shape

- **Given** a V1 run at 2026-04-24 15:30 UTC with `git_sha = abc123def456`, agent model `<gpt-5-mini pinned alias>`, judge model `<gemini-2.5-flash pinned alias>`, no limit
- **When** the runner creates the Braintrust experiment
- **Then** the experiment has metadata `{version: "v1", agent_model: "<gpt-5-mini alias>", judge_model: "<gemini-2.5-flash alias>", git_sha: "abc123def456", run_id: "2026-04-24T15:30:00Z", limit: null}` and tags `["v1", "agent:openai", "judge:google", "golden_dataset"]`

Category: Illustrative
Origin: PO

### Rule: V2/V3 base_experiment is the latest V1 experiment; V1 base_experiment is None (§9.3)

#### S-bt-02: V2 run picks latest V1 experiment as base_experiment
> Verifies prefix-match + latest selection

- **Given** Braintrust has `golden_dataset-v1-20260421-1530` and `golden_dataset-v1-20260423-0900`, and no other experiments
- **When** the researcher runs `eval_runner --version v2`
- **Then** the V2 run's `Eval(..., base_experiment=...)` is called with the 2026-04-23 V1 experiment name, enabling Braintrust's compare view

Category: Illustrative
Origin: PO

#### S-bt-03: V2 run with no V1 baseline warns and continues with base_experiment=None
> Verifies the fallback from §9.3

- **Given** Braintrust has no experiments starting with `golden_dataset-v1-`
- **When** the researcher runs `eval_runner --version v2`
- **Then** the runner prints a warning "no V1 baseline found; base_experiment unset — compare view must be configured manually", sets `base_experiment=None`, and proceeds to run

Category: Illustrative
Origin: PO

#### S-bt-04: V1 run sets base_experiment=None unconditionally
> Verifies V1 is always its own baseline

- **Given** any state of prior experiments (including existing `golden_dataset-v1-*`)
- **When** the researcher runs `eval_runner --version v1`
- **Then** `Eval()` is called with `base_experiment=None` — V1 runs never reference another experiment

Category: Illustrative
Origin: PO

---

### Journey Scenarios

#### J-bt-01: V2 vs V1 compare view in Braintrust UI
> Proves the baseline linkage is usable from the researcher's UI perspective

- **Given** a V1 baseline experiment `golden_dataset-v1-20260421-1530` with 30 rows × scores already uploaded
- **When** the researcher runs `eval_runner --version v2` (30 rows), then opens Braintrust UI → `golden_dataset` project → clicks the new V2 experiment → uses the Compare dropdown
- **Then** the UI displays per-row diffs between V2 and the V1 baseline for all 10+ Score streams, letting the researcher identify which rows improved and which regressed

Category: Journey
Origin: PO

---

## Feature: Human Calibration Workflow

### Context

Five-stage workflow (§10.1): bootstrap sub_parts → V1 first run → generate annotation template → SME fills binary judgments → κ report. κ ≥ 0.7 accepts; < 0.7 triggers rubric rewrite and re-loop. 10 calibration rows produce ~100 binary SME judgments in ~1.5-2 hours.

### Rule: `gen_calibration_template.py` produces a 10-row CSV with dynamic sub-part columns

#### S-cal-01: Template has variable-length completeness columns sized to max sub_parts across selected rows
> Verifies the variable-column schema from §10.3

- **Given** a V1 experiment `golden_dataset-v1-20260424-1530` where the 10 calibration rows have sub_parts lengths `[2, 3, 2, 4, 3, 2, 3, 2, 3, 2]` (max = 4)
- **When** the researcher runs `gen_calibration_template.py --experiment golden_dataset-v1-20260424-1530`
- **Then** the output CSV has fixed SME columns (`sme_comp_c1/c2/c3`, `sme_faithfulness`, etc.) plus exactly 4 completeness columns `sme_completeness_sub_1..sme_completeness_sub_4`; rows with fewer sub_parts leave excess columns blank

Category: Illustrative
Origin: PO

### Rule: `calibration_report.py` computes per-dim κ and marks each as accept or rewrite (§10.4)

#### S-cal-02: All dims κ ≥ 0.7 → report marks all accept
> Verifies the accept path

- **Given** a completed annotation CSV and matching V1 experiment where SME and judge agree enough on every dim to produce κ ≥ 0.7
- **When** the researcher runs `calibration_report.py --annotation <file> --experiment <exp>`
- **Then** the report markdown shows every dim with `[ok] accept` and no `[warn] rewrite rubric` entries

Category: Illustrative
Origin: PO

#### S-cal-05: Calibration report pins to a specific V1 experiment, not "latest"
> Verifies temporal-coupling integrity: SME annotations are meaningful only against the exact V1 run they were generated from

- **Given** Braintrust has two V1 experiments — `golden_dataset-v1-20260421-1530` (the one the annotation template was generated from) and a newer `golden_dataset-v1-20260424-0900` (a rerun after the SME started annotating)
- **When** the researcher runs `calibration_report.py --annotation annotation_20260421-1545.csv --experiment golden_dataset-v1-20260421-1530`
- **Then** the report fetches and computes κ against `golden_dataset-v1-20260421-1530` (the experiment whose rows the SME annotated), ignoring the newer V1 experiment; the report's header records both the annotation CSV path and the exact experiment name used

Category: Illustrative
Origin: QA

#### S-cal-03: One dim κ < 0.7 triggers rewrite mark, others accept
> Verifies per-dim independence — one bad dim doesn't mark the whole run rewrite

- **Given** a completed annotation where `comprehensiveness_c1` κ = 0.82, `completeness_sub_1` κ = 0.74, `faithfulness` κ = 0.65 (others ≥ 0.7)
- **When** the report runs
- **Then** the report marks `comprehensiveness_c1 [ok] accept`, `completeness_sub_1 [ok] accept`, `faithfulness [warn] rewrite rubric`, and lists the divergent rows for `faithfulness` with judge/SME verdicts

Category: Illustrative
Origin: PO

#### S-cal-04: Zero-variance dim where SME and judge both unanimous is treated as accept (A-edge case)
> Verifies the degenerate-κ handling: raw agreement falls back to "accept" when Cohen κ is mathematically undefined

- **Given** an annotation where SME marked all 10 cells for `specificity` as `1` and the judge scored all 10 as `1`
- **When** the report runs
- **Then** the `specificity` row shows κ = undefined + raw agreement = 100%, marked `[ok] accept` (not `[warn] rewrite`)

Category: Illustrative
Origin: Dev (Challenge 5.3)

---

### Journey Scenarios

#### J-cal-01: First-time calibration end-to-end through accept
> Proves the full 5-stage workflow for a real SME session

- **Given** a fresh repo with `dataset.csv` authored (questions only, `expected_sub_parts` column empty)
- **When** the researcher runs `propose_sub_parts.py` → SME reviews and commits updated `dataset.csv` → runs `eval_runner --version v1` → runs `gen_calibration_template.py` → SME fills the annotation CSV (~1.5 hr, ~100 cells) → runs `calibration_report.py`
- **Then** the report shows κ per dim; if all ≥ 0.7 the researcher proceeds to V2/V3 runs; if any dim < 0.7, the researcher rewrites that rubric and re-runs from stage 2

Category: Journey
Origin: Multiple

---

## Appendix: Challenges demoted to unit test or out of scope

The following Round 1 Dev and QA challenges were surfaced but do not appear as behavior scenarios, either because they belong at the unit test level, because of user-resolved scope decisions, or because they represent implementation discipline rather than user-observable behavior.

### From QA Round 1 (23 challenges total; 2 folded in as S-score-14 + S-cal-05; remaining 21 classified below)

- **Folded in**: Empty `expected_sub_parts=[]` vacuous-AND (→ S-score-14); calibration temporal coupling (→ S-cal-05).
- **Out of scope per user decision Q2=B**: UTF-8 BOM / CRLF, Excel autocast, single-quote JSON, Chinese numerals in numerical_faithfulness, newlines/quotes in pass_criterion — any malformed or encoding-suspect row now blocks at dataset load before a scorer ever sees it.
- **Out of scope per user decision Q3=A**: concurrent eval_runner invocations, clock skew affecting `find_latest_experiment` — single-user tool assumption accepted.
- **Demoted to unit test**: env var cycle detection, `--limit 0` / negative, YAML anchors bypassing cross-version assert, URL match substring-vs-equality in citation, prompt injection in tool_outputs (no defense in scope — same as CC-1 pattern).
- **Deferred to implementation discipline**: BRAINTRUST_API_KEY rotation mid-run (operational), Braintrust `fetch()` eventual consistency (retry on empty fetch), OPENAI_BASE_URL setdefault precedence (startup sanity check recommended), git_sha on detached HEAD (metadata honesty), BRAINTRUST_KEY env-var typo discoverability (startup validator recommended), Ctrl+C mid-Score-emission (atomicity in scorer wrapper), Braintrust quota 429 at init (fail-fast before agent runs), rubric fingerprint across κ iterations (metadata field recommended), annotation CSV schema drift when dataset edits between template and report, emoji / ZWSP / Chinese citation regex brittleness, 50K-char response runaway cost, agent refusal as a distinct signal, row id reuse after dataset edit.
- **Escalates design-level concerns**: mustache-in-criterion injection (autoevals configuration decision, not behavior), heterogeneous judge vendor tag cardinality (metadata shape decision, design silent). Both recorded for implementation review, not verified as behavior.

### From Dev Round 1

- **Demoted to unit test**: 2.5 (env var substitution: nested, recursive, `$VAR` no braces, URL defaults with colon) — grammar coverage belongs in `test_env_substitution.py`, already listed in §12 Testing Strategy.
- **Demoted to unit test**: 2.7 (vendor detection from model name string) — implementation helper, tested via fixture not E2E.
- **Demoted to unit test**: 2.9 (`--limit 100` against 30 rows) — simple CLI input guard.
- **Out of scope per user decision Q2=B**: 1.2 multi-state equivalence class (empty list vs missing vs whitespace) collapses to "any invalid shape = block".
- **Out of scope per user decision Q1=A**: 2.2 temperature/max_tokens drift — model.name-only gate is accepted; sampling param drift is not enforced.
- **Out of scope per user decision Q3=A**: 2.10 / 2.11 / CC-2 (same-minute collision / timezone / Ctrl+C idempotency) — single-user tool assumption accepted.
- **Demoted to docstring discipline**: A2 (V1 prompt / citation pattern coupling) — §11.3 already prescribes docstring cross-reference; no automated test required.
- **Out of scope for this pipeline**: 3.10 (Braintrust UI headline metric display) — UI ergonomics, not system behavior.
- **Demoted to unit test**: CC-3 (Braintrust column rendering for sparse indexed Scores) — §12 already lists "multi-Score scorer return of Braintrust column rendering" as an integration smoke test, not a behavior scenario.
- **Deferred to implementation discipline**: 4.1 (git dirty state annotation in metadata) — recommended for implementation but not gated by a behavior scenario.
- **Deferred to implementation discipline**: 4.2 (dataset_sha in metadata to detect dataset drift across V1/V2) — design does not require; flagged for post-V1 review.
- **Deferred to implementation discipline**: 5.1 (deterministic calibration row sampling) — recommendation is to seed by experiment name; no behavior scenario gates this.
- **Deferred to implementation discipline**: 5.4 (re-annotation after rubric rewrite) — workflow convention, not an automated behavior.
