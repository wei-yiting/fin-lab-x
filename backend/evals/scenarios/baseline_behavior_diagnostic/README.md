# baseline_behavior_diagnostic

`baseline_behavior_diagnostic` is the human-diagnostic eval scenario for baseline behavior diagnostic — an execution-behavior health check on an agent close to the baseline spec. It pins dataset identity and uses a deterministic scorer to record only execution / tool-call health, not answer quality.

## Scenario Contract

- `dataset.csv`: scenario-local dataset copy; content must match the source dataset row exactly
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

- other `observed_*` fields (`observed_primary_failure_mechanism`, `obs_secondary_failure_mechanism`, `observed_tuning_lever`)
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
source expectations, which still contain `mixed` and the retired `yfinance`.

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
