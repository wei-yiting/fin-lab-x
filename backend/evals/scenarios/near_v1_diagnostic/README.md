# near_v1_diagnostic

`near_v1_diagnostic` 是給 near-v1 人工診斷流程用的 eval scenario。它固定 dataset identity，並用 deterministic scorer 只記錄 execution / tool-call health，不評斷答案品質。

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

## Langfuse Annotation Schema v1

人工標註匯出預期至少包含以下欄位：

- `observed_outcome`
- `observed_alignment_to_prompt`
- `review_confidence`
- `review_comment`

可選欄位：

- 其他 `observed_*` 欄位
- `needs_followup`
- `followup_note`

這些欄位是 reviewer observation contract，不應由 execution scorer 預填，也不應混進 dataset reference hints。

## Execution Health Scorer

`diagnostic_execution_health` 只看 execution 是否完成、以及所有 tool call 是否成功：

- `execution_complete`: task 有產生 final response，且不是 runner error marker
- `tool_call_all_successful`: 所有 recorded tool call 都沒有 error marker
- `tool_error_names`: 失敗 tool 的名稱列表

只有當 `execution_complete=true` 且 `tool_call_all_successful=true` 時，score 才會是 `1`；否則為 `0`。

## Notes

- 這個 scenario 不使用 LLM judge
- 這個 scenario 的 scorer 不讀 reference answer hints，也不評斷回答內容好壞
