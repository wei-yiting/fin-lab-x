# BDD Scenarios

## Meta
- Design Reference: `artifacts/current/design.md`
- Generated: 2026-04-24
- Discovery Method: Three Amigos (Agent Teams — PO/Dev/QA synthesized from design.md)

---

## Feature: Dataset Selection & Slice Identity

### Context
Selector 將 full dataset 依 `full_dataset` / `row_ids` / `field_filter` / `manifest` 四種模式切成本次執行的 row set，並產生一份可重現的 `slice_identity`。這是整條 pipeline 的入口，所有下游 identity 都依賴它正確。

### Rule: 四種 slice mode 必須選出設計文件定義的 row set（Selector correctness — design §14.1）

#### S-slice-01: full_dataset 選出全部 30 題
> 驗證 `full_dataset` mode 會回傳 dataset 裡所有 row，順序與原 CSV 一致。

- **Given** 一份包含 30 題的 diagnostic dataset，`id` 為 1..30
- **When** 以 `slice_type=full_dataset` 呼叫 DatasetSelector
- **Then** 回傳的 row set 大小等於 30，`selected_row_ids` 依序為 1..30，`slice_identity.slice_type` 為 `full_dataset`

Category: Illustrative
Origin: PO

#### S-slice-02: row_ids 精確挑出指定題目
> 驗證 `row_ids` mode 只選出明列的 row，多餘或不存在的 id 視為錯誤。

- **Given** 同一份 30 題 dataset
- **When** 以 `slice_type=row_ids`，`slice_selector="3,7,12"` 呼叫 selector
- **Then** 回傳 3 筆 row，其 `row_id` 為 `{3,7,12}`；`slice_identity.selected_row_ids` 完全等於該集合

Category: Illustrative
Origin: Dev

#### S-slice-03: field_filter 依欄位值篩選
> 驗證 `field_filter` 能以 dataset column 做 exact-match 篩選。

- **Given** dataset 中 5 題 `capability_band=boundary`
- **When** 以 `slice_type=field_filter`，`slice_selector="capability_band=boundary"` 呼叫 selector
- **Then** 回傳 5 筆 row，全部 `capability_band` 為 `boundary`

Category: Illustrative
Origin: PO

#### S-slice-04: manifest 從外部檔案載入 row id 清單
> 驗證 `manifest` mode 讀取外部檔的 row-id 清單並選到對應 row。

- **Given** 一份 manifest 檔列有 `row_id` `2,5,9,18`
- **When** 以 `slice_type=manifest`，`slice_selector=<path-to-manifest>` 呼叫 selector
- **Then** 回傳 4 筆 row，`selected_row_ids` 為 `{2,5,9,18}`，與 manifest 檔一致

Category: Illustrative
Origin: Dev

### Rule: 同樣輸入必須產生相同的 slice_identity（reproducibility — design §14.1）

#### S-slice-05: 同樣 field_filter 兩次呼叫產生相同 slice_hash
> 驗證 selector 的 `slice_hash` 對相同輸入穩定。

- **Given** 一份 dataset 與 `slice_selector="capability_band=boundary"`
- **When** 連續兩次以相同參數呼叫 selector
- **Then** 兩次回傳的 `slice_identity.selected_row_ids` 與 `slice_hash` 完全相同

Category: Illustrative
Origin: QA

#### S-slice-06: manifest 檔內容改變會產生不同 slice_hash
> 驗證 manifest 內容被視為 slice identity 的一部分。

- **Given** 先以 manifest A（id `2,5,9`）跑一次，記錄 `slice_hash_a`
- **When** 將 manifest 改為 id `2,5,10` 後再以 `slice_type=manifest` 跑一次
- **Then** 新的 `slice_hash` 與 `slice_hash_a` 不同，`selected_row_ids` 反映新清單

Category: Illustrative
Origin: QA

### Rule: 不合法的 slice input 必須明確拒絕（boundary — design §14.1）

#### S-slice-07: row_ids 含 dataset 中不存在的 id 視為錯誤
> 驗證不存在 id 不會被靜默忽略。

- **Given** 30 題 dataset（id 1..30）
- **When** 以 `slice_type=row_ids`，`slice_selector="3,999"` 呼叫 selector
- **Then** selector 抛出明確錯誤，標示 `999` 不存在；不進入執行階段

Category: Illustrative
Origin: QA

#### S-slice-08: field_filter 結果為空集合視為錯誤
> 驗證空 slice 不會被誤當 full run 執行。

- **Given** dataset 中沒有任何 row 符合 `capability_band=nonexistent`
- **When** 以 `slice_type=field_filter`，`slice_selector="capability_band=nonexistent"` 呼叫 selector
- **Then** selector 抛出明確錯誤（或回傳空 row set 但標記為 `empty_slice` 並阻止 downstream 執行）

Category: Illustrative
Origin: QA

---

### Journey Scenarios

#### J-slice-01: 完整的 subset rerun 流程
> 驗證使用者從選 subset、執行、到 slice_identity 完整落地的端到端流程。

- **Given** reviewer 指定要重跑 `row_ids="3,7,12"` 這三題做 bug 修復回歸
- **When** runner 以該 slice 參數跑完 pipeline，並於 Braintrust 與 Langfuse 兩邊寫入執行紀錄
- **Then** Braintrust experiment metadata 與 Langfuse trace metadata 都帶有 `slice_label`、`slice_type=row_ids`、`selected_row_ids=[3,7,12]`，三題都有對應 trace，沒有其他 row 被執行

Category: Journey
Origin: Multiple

---

## Feature: Dual-Surface Execution & Identity Propagation

### Context
每一題執行時會同時寫入 Braintrust experiment record 與 Langfuse trace，兩邊共用 row/run/slice 三層 identity。這讓 Braintrust 可做 run-to-run compare，Langfuse 可作為 annotation surface，而兩端紀錄可以用穩定 key 對齊。

### Rule: Braintrust case metadata 必須包含完整 identity keys（Metadata integrity — design §8.1 §14.2）

#### S-exec-01: Braintrust case 帶有 row / run / slice metadata
> 驗證每個 Braintrust case 都能獨立被 identity key 定位。

- **Given** dataset row `id=5`、`run_label="baseline-2026-04-24"`、`slice_label="boundary-only"`
- **When** runner 完成該題執行並寫入 Braintrust
- **Then** 對應 Braintrust case 的 metadata 同時包含 `row_id=5`、`dataset_name`、`dataset_version`、`run_label="baseline-2026-04-24"`、`run_group`、`slice_label="boundary-only"`、`slice_type`、`agent_version`

Category: Illustrative
Origin: Dev

### Rule: Langfuse trace metadata 必須帶有同一組 identity keys（design §14.2）

#### S-exec-02: Langfuse trace 能用 row_id + run_label 對齊 Braintrust
> 驗證兩端共用 identity，匯出後可以 join。

- **Given** 同一次執行的 row `id=5`
- **When** runner 同時寫 Braintrust 與 Langfuse
- **Then** 該 Langfuse trace 的 metadata 至少包含 `row_id=5` 與 `run_label="baseline-2026-04-24"`；以 `(row_id=5, run_label="baseline-2026-04-24")` 能在 Braintrust 查到唯一對應 case

Category: Illustrative
Origin: Dev

### Rule: 三層 identity 不可互相推斷（design §6.4）

#### S-exec-03: 同一 run_label 跑兩個不同 slice 必須保留各自 slice_identity
> 驗證 run identity 不會吞掉 slice identity。

- **Given** `run_label="rerun-a"` 先跑 `slice=row_ids:3,7`，再以同 `run_label` 跑 `slice=row_ids:12`
- **When** 兩次執行都寫入 Braintrust 與 Langfuse
- **Then** 第一批 case/trace 的 `selected_row_ids=[3,7]`、第二批 `selected_row_ids=[12]`，`slice_hash` 不同；單靠 `run_label` 不能反推 slice

Category: Illustrative
Origin: QA

#### S-exec-04: 同一 row_id 在不同 run_label 下產生獨立 trace
> 驗證 row identity 不吞掉 run identity。

- **Given** 對 `row_id=5` 連跑兩次：`run_label="baseline"` 與 `run_label="after-fix"`
- **When** 兩次都寫入 Langfuse
- **Then** 兩條獨立 trace，各自帶對應 `run_label`；export 後可用 `(row_id, run_label)` 分辨兩次執行

Category: Illustrative
Origin: QA

### Rule: 執行錯誤不可污染 identity 或 downstream 對齊

#### S-exec-05: 單題執行失敗仍寫入帶 identity 的執行紀錄
> 驗證錯誤 row 不會在兩端之一缺席。

- **Given** `row_id=7` 在 agent 執行中抛出異常
- **When** runner 處理該異常
- **Then** Braintrust 仍有該 case（標記 `error` 狀態），Langfuse 仍有對應 trace（帶完整 identity metadata 與錯誤訊息）；`row_id=7` 不會只存在單邊

Category: Illustrative
Origin: QA

---

### Journey Scenarios

#### J-exec-01: 以相同 run_label 兩次執行並用 identity 對齊 compare
> 驗證 baseline → fix 的執行與對齊流程是完整的。

- **Given** reviewer 想比較修改前後 `row_ids="3,7,12"` 的行為
- **When** runner 以 `run_label="baseline"` 跑一次、再以 `run_label="after-fix"` 跑一次，兩次都寫入雙平台
- **Then** Braintrust 可用 `run_label` 列出兩組 experiment 做 compare；Langfuse 可依 `(row_id, run_label)` 篩出六條 trace，且 `(3,"baseline") / (3,"after-fix")` 兩條能成對出現

Category: Journey
Origin: Multiple

---

## Feature: Reference Metadata Projection on Langfuse Traces

### Context
Dataset 的既有診斷欄位會以 `reference_*` 前綴投影到 Langfuse trace metadata，作為 reviewer 在 Annotation Queue 的判斷 context。`reference_*` 不是 ground truth，也不能覆寫 reviewer 寫入的 `observed_*`。

### Rule: dataset 診斷欄位必須以 reference_* 前綴投影到 Langfuse trace（design §8.2）

#### S-ref-01: reference_* 欄位完整出現在 trace metadata
> 驗證七個 reference_* 欄位都被正確投影。

- **Given** dataset 中 `row_id=5` 的 `capability_band=core`、`expected_near_v1_behavior=should_pass`、`primary_failure_mechanism=tool_routing_error`、`secondary_failure_mechanism=evidence_synthesis_limit`、`expected_best_source=Tavily`、`likely_tuning_lever=...`、`draft_pass_signals=...`
- **When** runner 寫入該題的 Langfuse trace
- **Then** trace metadata 包含 `reference_capability_band="core"`、`reference_expected_behavior="should_pass"`、`reference_primary_failure_mechanism="tool_routing_error"`、`reference_secondary_failure_mechanism="evidence_synthesis_limit"`、`reference_best_source="Tavily"`、`reference_likely_tuning_lever`、`reference_pass_signals`，且值與 dataset 完全一致

Category: Illustrative
Origin: PO

#### S-ref-02: dataset 欄位空值投影為空 reference_* 欄位而非缺欄
> 驗證 optional 欄位一致行為，避免 reviewer 以為是 bug。

- **Given** `row_id=10` 的 `secondary_failure_mechanism` 欄位為空
- **When** runner 寫入該題的 Langfuse trace
- **Then** trace metadata 包含 `reference_secondary_failure_mechanism`（值為空字串或 null），key 不被省略

Category: Illustrative
Origin: Dev

### Rule: reference_* 不可覆寫 reviewer 的 observed_*（design §8.3 §9.3）

#### S-ref-03: reviewer 寫入 observed_* 後 trace 再次更新不會覆蓋
> 驗證 projection 不是寫入 scores/comments。

- **Given** `row_id=5` 的 Langfuse trace 已有 reviewer 寫入的 `observed_outcome="partial_answer"`
- **When** 同一 row 以同 run_label 再次被 pipeline 觸發（例如 replay）產生新的 metadata 投影
- **Then** `observed_outcome` 維持 `"partial_answer"`；`reference_*` 的投影寫入 trace metadata，不寫入 Langfuse scores 或 reviewer 的 observation

Category: Illustrative
Origin: QA

#### S-ref-04: reference_* 與 observed_* 命名不衝突
> 驗證 schema 上兩組欄位是並排而非覆蓋。

- **Given** 一條 trace 同時有 `reference_primary_failure_mechanism="tool_routing_error"` 與 reviewer 寫入 `observed_primary_failure_mechanism="source_coverage_gap"`
- **When** 讀取 trace metadata 與 scores
- **Then** 兩個欄位同時存在於不同位置（metadata vs scores/comments），值各自獨立保留

Category: Illustrative
Origin: PO

---

### Journey Scenarios

#### J-ref-01: reviewer 以 reference_* 作為 context 完成 trace annotation
> 驗證 reference_* 的生命週期能支撐一次完整的 human review。

- **Given** runner 為 `row_id=5` 寫入 Langfuse trace，metadata 帶有完整 `reference_*`
- **When** reviewer 在 Annotation Queue 打開該 trace，參考 `reference_*`，寫入 `observed_outcome`、`observed_alignment_to_prompt`、`review_confidence`、`review_comment`
- **Then** trace metadata 的 `reference_*` 保持不變，`observed_*` 以 scores/comments 形式存在，兩組欄位在 Langfuse UI 可並排看到

Category: Journey
Origin: Multiple

---

## Feature: Annotation Export & Dataset Join

### Context
Reviewer 完成 annotation 後，會從 Langfuse 匯出 scores/comments CSV，再以 `row_id + run_label` 和 dataset / run metadata 做 join，產生可供 analysis / discussion 使用的合併 CSV。Full vs subset compare 必須標記為 `overlap-only`。

### Rule: Langfuse export 能以 row_id + run_label join 回 dataset（design §14.3）

#### S-export-01: export 後以 row_id + run_label 做 inner join 得完整紀錄
> 驗證 join key 真的可用。

- **Given** 一次 `slice=row_ids:3,7,12` 的 run，reviewer 在三條 trace 各寫入 `observed_*`
- **When** 從 Langfuse export scores CSV，並以 `(row_id, run_label)` 與 dataset 及 run metadata 做 join
- **Then** 產生 3 列 joined rows，每列同時含 dataset 欄位、`reference_*`、`observed_*`、`review_comment`、`run_label`、`slice_label`

Category: Illustrative
Origin: PO

#### S-export-02: 缺少某題 annotation 時 join 行為明確
> 驗證未 annotated row 不會靜默消失，也不會假裝已標註。

- **Given** 三題 run 中只有兩題被 annotated
- **When** 執行 join
- **Then** 三列都存在於 joined CSV；未標註的那列 `observed_*` 欄位為空且明確標記為 `unannotated`，不被解讀為「已標且為空」

Category: Illustrative
Origin: QA

#### S-export-03: run_label 重複使用時 join 不混淆兩次 run
> 驗證 join key 的唯一性假設。

- **Given** 同 `run_label="rerun-a"` 被使用在兩個不同時段，Langfuse 內因此有兩批 trace
- **When** export 並 join
- **Then** 系統要嘛（a）以 `(row_id, run_label, started_at)` 區分並各自 join、要嘛（b）偵測到 `run_label` 衝突並報錯；不得把兩次 run 的 observation 混入同一列

Category: Illustrative
Origin: QA

#### S-export-04: dataset_version 改變後舊 export 的 join 被標示
> 驗證 dataset 演進不會污染歷史 annotation。

- **Given** `dataset_version="v1.0"` 下做過 annotation，隨後 dataset 更新為 `v1.1`（某些 `reference_*` 改變）
- **When** 用 `v1.1` dataset 與 `v1.0` export 做 join
- **Then** joined CSV 內每列都帶 `dataset_version="v1.0"`，並在顯著欄位標示 `dataset_version_mismatch`；不會用 `v1.1` 的 `reference_*` 默默蓋掉舊資料

Category: Illustrative
Origin: QA

### Rule: full vs subset compare 必須標記 overlap-only（design §7.1 §7.2）

#### S-export-05: full vs subset compare 產出 overlap-only summary
> 驗證不會把不同 row distribution 的 aggregate 當同質比較。

- **Given** experiment A 為 full 30 題，experiment B 為 `slice=row_ids:3,7,12`
- **When** 請求 A vs B 的 compare summary
- **Then** summary header 標記 `overlap-only`，聚合基底為 `{3,7,12}` 三題；A 的另外 27 題不納入聚合數字

Category: Illustrative
Origin: Dev

#### S-export-06: subset vs subset 當 row set 相同時不標 overlap-only
> 驗證 overlap-only 不被濫用。

- **Given** experiment A 與 B 都是 `row_ids:3,7,12`
- **When** 做 A vs B compare summary
- **Then** summary 不帶 `overlap-only` 標記，聚合基底為完整 `{3,7,12}`

Category: Illustrative
Origin: Dev

#### S-export-07: subset vs subset 但 row set 只部分重疊時仍以交集為基底
> 驗證 overlap rule 對 subset 兩兩比較也成立。

- **Given** A 為 `row_ids:3,7,12`，B 為 `row_ids:7,12,18`
- **When** 做 A vs B compare summary
- **Then** summary 標記 `overlap-only`，聚合基底為交集 `{7,12}`；A 的 `3` 與 B 的 `18` 不納入聚合

Category: Illustrative
Origin: QA

---

### Journey Scenarios

#### J-export-01: 從 Langfuse annotation 到 discussion CSV 的完整 E2E
> 驗證整條 annotation → analysis 流程可以跑通。

- **Given** reviewer 對 `row_ids:3,7,12` 的三條 trace 在 Annotation Queue 寫入完整 `observed_*`
- **When** 以 Langfuse export CSV，執行 AnnotationExportJoiner 與 dataset + run metadata 做 join
- **Then** 產出一份 joined CSV：三列同時含 dataset question、`reference_*`、`observed_*`、`review_comment`、`run_label`、`slice_label`；reviewer 可直接把這份 CSV 拿去與 agent 做後續 discussion

Category: Journey
Origin: Multiple

#### J-export-02: 跨 run 的 compare 在 overlap-only 規則下產出可用 summary
> 驗證 full vs subset compare 能在正確聚合語意下產出 summary。

- **Given** Braintrust 上已有一個 full run `exp-full` 與一個 subset run `exp-subset` (`row_ids:3,7,12`)
- **When** 請求兩者 compare summary
- **Then** summary 標頭顯示 `overlap-only`、overlap row set 為 `{3,7,12}`、指標聚合只基於這三題；UI / CSV 能清楚看到這個基底而非 30 題的 aggregate

Category: Journey
Origin: Multiple
