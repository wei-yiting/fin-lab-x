# baseline_behavior_diagnostic

`baseline_behavior_diagnostic` is the human-diagnostic eval scenario for baseline behavior diagnostic — an execution-behavior health check on an agent close to the baseline spec. It pins dataset identity and uses a deterministic scorer to record only execution / tool-call health, not answer quality.

## Scenario Contract

- `dataset.csv`: scenario-local dataset copy; content must match the source dataset row exactly
- `dataset_zh.csv`: Traditional Chinese language mirror of `dataset.csv` — same 30 rows, ids,
  and schema; only the free-text columns (`question`, `company_universe`,
  `expected_answer_type`, `draft_pass_signals`, `why_baseline_might_fail_or_pass`) are
  translated. Not wired into `eval_spec.yaml`; running the diagnostic against the Chinese
  set requires pointing a spec at it explicitly. Keep the two files row-aligned when editing.
- `eval_spec.yaml`: scenario config, including the `diagnostic` identity block
- scorer: `diagnostic_execution_health`

The `diagnostic` block currently fixes these fields:

- `dataset_name`
- `dataset_version`
- `agent_version`

Diagnostic datasets follow a fixed column-naming convention: a dataset MUST have an
`id` (row identity) and a `question` (prompt) column. Future diagnostic datasets always
follow this naming — column-name configurability (`row_id_column` / `question_column`)
was deliberately removed.

## Dataset Columns (annotation guide)

`dataset.csv` has 15 columns in three groups. Only `question` reaches the agent;
everything else is curation-time reference material that travels to the reviewer as
`reference_*` trace metadata (see the projection split below). When annotating,
read the reference columns as "what the curator predicted", never as ground truth —
the whole point of the diagnostic is to compare these predictions against what you
actually observe in the trace.

### Identity & input

| Column | Purpose |
|---|---|
| `id` | Row identity. The third segment of the session id (`{dataset}::{run_label}::{id}`) and the Braintrust comparison key — this is how your annotation joins back to the row. |
| `question` | The exact prompt sent to the agent. The only column the agent ever sees. |

### Descriptive facets (filtering / slicing during review)

| Column | Values | Purpose |
|---|---|---|
| `company_universe` | company name(s) | Which companies the question involves. Multi-entity rows stress tool budgeting. |
| `category` | 7 kinds, e.g. `recent_news_or_event_impact`, `regulatory_or_legal_risk` | The analytical job the question represents. Use to spot category-wide failure patterns. |
| `expected_answer_type` | free text | The shape a good answer would take (e.g. "Recent event summary + investment thesis judgment"). Calibrates what "responsive" looks like before you judge alignment. |
| `time_sensitivity` | `recent` / `stable` | Whether the answer depends on fresh data. `recent` rows failing on stale sources is a source problem, not a reasoning problem. |
| `question_style` | `natural` / `analysis` | `natural` = phrased like a real user; `analysis` = explicit analyst tasking. Distinguishes prompt-interpretation failures from capability failures. |

### Curator predictions (the expectation side — what you compare your observation against)

| Column | Values | Purpose |
|---|---|---|
| `capability_band` | `core` / `boundary` / `beyond_boundary` | Where the question sits relative to the baseline agent's designed capability. A `core` failure is alarming; a `beyond_boundary` pass is a bonus. |
| `expected_baseline_behavior` | `should_pass` / `may_pass_with_tuning` / `should_fail_cleanly` | The curator's predicted outcome. Note `should_fail_cleanly` rows: a *graceful* refusal there is the correct behavior — score your observation against this, not against "answered the question". |
| `primary_failure_mechanism` | `tool_routing_error`, `source_coverage_gap`, `overreach_vs_abstain`, `evidence_synthesis_limit`, `multi_entity_overload` | The most likely way this question breaks, predicted at curation time. Your `observed_primary_failure_mechanism` annotation either confirms or corrects it — the disagreement rate is the dataset's own quality signal. |
| `secondary_failure_mechanism` | same vocabulary, may be empty | Second most likely mechanism. |
| `expected_best_source` | `SEC` / `Finnhub` / `Tavily` / `mixed` | Which tool a well-routed agent would lean on. `mixed` (12 of 30 rows) names no single tool — which is why tool appropriateness stays a human judgement instead of a deterministic check. |
| `likely_tuning_lever` | `none`, `max_tool_calls`, `prompt`, `tavily_sources`, `tool_description` | If the row fails as predicted, the config knob most likely to fix it. Your `observed_tuning_lever` annotation refines this into an actual tuning backlog. |
| `why_baseline_might_fail_or_pass` | free text | The curator's reasoning behind the predictions above. Read this before judging a trace — it tells you what the row is *designed to probe*. |
| `draft_pass_signals` | JSON array of strings | Concrete things a passing answer should do (e.g. "Distinguish actions already taken from potential pressure"). Draft quality — treat as a checklist starting point, not a rubric. |

### How these reach you during review

The runner projects each row into two bundles. The reviewer-facing one rides the
trace as `reference_*`-prefixed metadata (`reference_expected_behavior`,
`reference_best_source`, `reference_pass_signals`, ...), so every prediction above
is visible right next to the trace you are annotating. The scorer's bundle
deliberately excludes all of it. The prefix is the guard rail: `reference_*` = what
was predicted, `observed_*` (your annotation) = what actually happened. Error
analysis lives in the gap between the two.

## Human Review Schema (platform-neutral contract)

The human-review half of the annotation loop is being rebuilt on Braintrust per
ADR-0005 (DEV-115); this directory no longer includes annotation-provisioning or
export-join tooling. The reviewer score schema below is a platform-neutral contract
that DEV-115 will reuse when rebuilding the score configs:

First-pass triage:

- `triage_outcome`: `good` / `bad` — filter out obviously-good traces first; only
  `bad` or traces needing follow-up get the full diagnostic fields, reducing
  annotation noise.

Second-pass full diagnosis (human annotation includes at least):

- `observed_outcome`
- `observed_alignment_to_prompt`
- `review_confidence`
- `review_comment`

Optional fields:

- other `observed_*` fields (`observed_primary_failure_mechanism`, `observed_secondary_failure_mechanism`, `observed_tuning_lever`)
- `needs_followup`
- `followup_note`

These fields are the reviewer observation contract — they must not be pre-filled by
the execution scorer, and must not be mixed into dataset reference hints.

## Execution Health Scorer

`diagnostic_execution_health` only looks at whether execution completed and whether all tool calls succeeded:

- `execution_complete`: the stream emitted a non-error `Finish` event (`finished_normally` flag)
- `tool_call_all_successful`: every recorded tool call's `error` field is empty
- `tool_call_count`: how many tool calls were recorded
- `tool_error_names`: names of the tools that failed

The score is `1` only when both `execution_complete=true` and `tool_call_all_successful=true`; otherwise `0`.

### What this scorer deliberately does NOT measure

**Tool appropriateness.** The scorer never asks whether the agent reached for a tool
suited to the question — it does not read the dataset's `expected_best_source` or any
other reference hint. An agent that answers question 6 (J&J litigation risk, expected
to go to SEC filings) from a single web search still scores `1` as long as the search
succeeded and the run finished.

`tool_call_all_successful` is also vacuously true at zero tool calls, so an agent
answering purely from model memory scores `1` too. `tool_call_count` exists to make
that case visible when filtering an experiment — it is recorded, never scored.

Judging tool appropriateness is the human reviewer's job, which is why
`reference_best_source` is projected into the trace metadata (the expectation side)
and deliberately withheld from the scorer's Braintrust bundle (the observation side).
Promoting it to a deterministic check would first require reconciling the dataset's
source expectations — 12 of 30 rows declare `mixed`, which names no single
acceptable tool.

## Notes

- This scenario does not use an LLM judge
- This scenario's scorer does not read reference answer hints, and does not judge answer content

## Annotation Join Contract

Human annotations join back to the original dataset row via a deterministic session id:

```
{dataset_name}::{run_label}::{row_id}
```

The join side (DEV-115's BTQL joiner) must parse this string and verify all three
segments match, not just compare it as a raw string. Rows with no annotation leave
the reviewer fields blank.

Braintrust Project Settings should set a stable comparison key (e.g. `row_id`) so the
compare UI aligns the same dataset row.
