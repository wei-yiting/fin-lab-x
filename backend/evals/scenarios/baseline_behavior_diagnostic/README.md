# baseline_behavior_diagnostic

`baseline_behavior_diagnostic` 是 baseline behavior diagnostic（對接近 baseline 規格的 agent 做執行行為健康檢查）的人工診斷 eval scenario。它固定 dataset identity，並用 deterministic scorer 只記錄 execution / tool-call health，不評斷答案品質。

## Scenario Contract

- `dataset.csv`: scenario-local dataset copy；內容必須與來源 dataset row 完全一致
- `eval_spec.yaml`: scenario config，包含 `diagnostic` identity block
- scorer: `diagnostic_execution_health`

`diagnostic` block 目前固定以下欄位：

- `dataset_name`
- `dataset_version`
- `row_id_column`
- `question_column`
- `agent_version`

## Human Review Schema（platform-neutral contract）

人工半場的 annotation loop 依 ADR-0005 統一於 Braintrust 重建（DEV-115）；本目錄不再包含
annotation 佈建與 export join 工具。以下 reviewer score schema 是 platform-neutral 的契約，
DEV-115 重建 score configs 時沿用：

第一輪 triage：

- `triage_outcome`: `good` / `bad`——先把明顯 good 的 traces filter 掉，只有 `bad` 或需要
  追蹤的 traces 再補完整診斷欄位，降低 annotation noise。

第二輪完整診斷（人工標註至少包含）：

- `observed_outcome`
- `observed_alignment_to_prompt`
- `review_confidence`
- `review_comment`

可選欄位：

- 其他 `observed_*` 欄位（`observed_primary_failure_mechanism`、`obs_secondary_failure_mechanism`、`observed_tuning_lever`）
- `needs_followup`
- `followup_note`

這些欄位是 reviewer observation contract，不應由 execution scorer 預填，也不應混進 dataset
reference hints。

## Execution Health Scorer

`diagnostic_execution_health` 只看 execution 是否完成、以及所有 tool call 是否成功：

- `execution_complete`: task 有產生 final response，且不是 runner error marker
- `tool_call_all_successful`: 所有 recorded tool call 都沒有 error marker
- `tool_error_names`: 失敗 tool 的名稱列表

只有當 `execution_complete=true` 且 `tool_call_all_successful=true` 時，score 才會是 `1`；否則為 `0`。

## Notes

- 這個 scenario 不使用 LLM judge
- 這個 scenario 的 scorer 不讀 reference answer hints，也不評斷回答內容好壞

## Annotation Join Contract

人工標註要能 join 回 dataset 原始列，靠的是 deterministic session id：

```
{dataset_name}::{run_label}::{row_id}
```

join 端（DEV-115 的 BTQL joiner）必須 parse 這個字串並驗證三段皆吻合，而不是拼字串比對。
沒有 annotation 的列，reviewer 欄位留空。

Braintrust Project Settings 應設定穩定的 comparison key（例如 `row_id`），compare UI 才會對齊同一筆 dataset row。
