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

Langfuse Human Annotation / Annotation Queue 需要先建立 Score Config。Free plan 若只能使用一個 Annotation Queue，可用本地 setup script 建立單一 combined queue：

```bash
uv run python -m backend.evals.diagnostic.langfuse_annotation_setup
```

這個 queue 會同時包含第一輪 triage 欄位與完整 diagnostic 欄位。第一輪先填：

- `triage_outcome`: `good` / `bad`

這一輪用來降低後續 annotation noise：先把明顯 good 的 traces filter 掉，只有 `bad` 或需要追蹤的 traces 再補完整診斷欄位。

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

## Annotation Export Join

Langfuse scores export 需要先匯出成 CSV，再用本地 joiner 回接原始 dataset：

```bash
uv run python -m backend.evals.diagnostic.annotation_export_joiner \
  --dataset backend/evals/scenarios/near_v1_diagnostic/dataset.csv \
  --scores-export /path/to/langfuse_scores.csv \
  --dataset-name near_v1_diagnostic \
  --run-label smoke-local \
  --output /tmp/near-v1-diagnostic-discussion.csv
```

join key 不是直接拼字串比對而已；joiner 會先 parse `session_id`，確認：

- `dataset_name`
- `run_label`
- `row_id`

只有符合 diagnostic session contract、`source=ANNOTATION`、而且是 trace-level annotation 的 score row 會被接受。

輸出會保留原始 dataset 欄位，並另外附上：

- `observed_outcome`
- `observed_alignment_to_prompt`
- `review_confidence`
- `review_comment`
- `observed_primary_failure_mechanism`
- `observed_secondary_failure_mechanism`
- `observed_tuning_lever`
- `needs_followup`
- `followup_note`
- `langfuse_trace_id`
- `langfuse_session_id`
- `join_status`

`join_status` 語意：

- `annotated`: 核心 reviewer 欄位都已存在
- `partial_annotation`: 有部分 reviewer annotation，但還不完整
- `missing_annotation`: 這列還沒有 trace-level annotation

Langfuse Score Config name 最長 35 字元，因此 UI 裡的
`obs_secondary_failure_mechanism` 會在 export join 時映射回
`observed_secondary_failure_mechanism`。

## Compare Guard

在 Analyst 解讀 Braintrust compare 前，先用本地 compare guard 檢查兩個 diagnostic run 是否真的可比：

```bash
uv run python -m backend.evals.diagnostic.compare_guard \
  --run-a-manifest /path/to/run-a-manifest.csv \
  --run-b-manifest /path/to/run-b-manifest.csv \
  --output /tmp/diagnostic-compare-guard.json
```

compare guard 不會取代 Braintrust 的 row-by-row compare；它只負責先標示 comparability semantics，例如：

- `same_row_set`
- `intersection`
- `overlap_only`
- `dataset_version_mismatch`
- `empty_intersection`

compare guard 讀的檔案至少要有這些欄位：

- `row_id`
- `dataset_version`
- `selected_row_ids`
- `slice_label`
- `slice_type`

判讀原則：

- 同版、同 row set 才能直接讀 aggregate compare
- 同版 subset-vs-subset 若有交集，會標成 `intersection`
- 同版 full-vs-subset 會標成 `overlap_only`
- 跨 version 的 full-vs-full 仍可看交集 row，但會在 warning 內標示 `dataset_version_drift`
- 跨 dataset version 的 subset compare 預設視為 `dataset_version_mismatch`
- 若沒有交集 row，直接視為 `empty_intersection`

另外，Braintrust Project Settings 應設定穩定的 comparison key，例如 `row_id`。compare guard 只負責先做可比性判斷，不會取代 Braintrust UI 的 row matching。
