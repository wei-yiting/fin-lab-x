# Verification Plan

## Meta

- Scenarios Reference: `.artifacts/current/bdd-scenarios.md`
- Generated: 2026-03-31

---

## Automated Verification

### Deterministic

#### S-disc-01: 完整目錄結構被正確發現

- **Method**: script
- **Steps**:
  1. 確認 `scenarios/language_policy/` 含 `dataset.csv` 和 `eval_spec.yaml`
  2. 執行 `python -m evals.runner language_policy --local-only`
  3. Assert: exit code = 0
  4. Assert: `results/` 目錄下有 `language_policy_*.csv` 檔案
- **Expected**: 指令成功完成，result CSV 存在

#### S-disc-02: 缺少檔案的目錄被跳過並警告

- **Method**: script
- **Steps**:
  1. 建立 `scenarios/broken/`，只放 `eval_spec.yaml`
  2. 確保 `scenarios/language_policy/` 合法存在
  3. 執行 `python -m evals.runner --all --local-only 2>&1`
  4. Assert: stderr/stdout 包含 "broken" 相關的 warning 文字和 "dataset.csv"
  5. Assert: `language_policy` 的 result CSV 存在
- **Expected**: broken 被跳過有警告，合法 scenario 正常產出

#### S-disc-03: 不存在的 scenario 名稱顯示可用清單

- **Method**: script
- **Steps**:
  1. 確保至少一個合法 scenario 存在
  2. 執行 `python -m evals.runner nonexistent --local-only 2>&1`
  3. Assert: exit code ≠ 0
  4. Assert: 輸出包含 "not found" 和至少一個可用的 scenario 名稱
- **Expected**: 錯誤訊息含 scenario 名稱和可用清單

#### S-disc-04: `--all` 在沒有任何 scenario 時提示

- **Method**: script
- **Steps**:
  1. 暫時清空 `scenarios/` 目錄（或指向一個空目錄）
  2. 執行 `python -m evals.runner --all --local-only 2>&1`
  3. Assert: 輸出包含 "no scenarios found"
  4. Assert: exit code ≠ 0
- **Expected**: 不會靜默成功

#### S-disc-05: 目錄不存在 vs 缺少檔案產生不同錯誤

- **Method**: script
- **Steps**:
  1. 確保 `scenarios/` 中沒有 `phantom/` 目錄，但有 `broken/`（只含 `eval_spec.yaml`）
  2. 執行 `python -m evals.runner phantom --local-only 2>&1`
  3. Assert: 輸出包含 "not found"
  4. 執行 `python -m evals.runner broken --local-only 2>&1`
  5. Assert: 輸出包含 "missing" 和 "dataset.csv"
  6. Assert: 兩個錯誤訊息的措辭明顯不同
- **Expected**: 兩種錯誤清楚可區分

#### S-disc-06: `__pycache__/` 不被視為 scenario

- **Method**: script
- **Steps**:
  1. 確保 `scenarios/__pycache__/` 存在（或手動建立）
  2. 確保至少一個合法 scenario 存在
  3. 執行 `python -m evals.runner --all --local-only 2>&1`
  4. Assert: 輸出不包含 "__pycache__" 相關錯誤或警告
  5. Assert: 合法 scenario 正常執行
- **Expected**: 系統目錄被靜默過濾

#### S-disc-07: 目錄名含空格 → 驗證錯誤

- **Method**: script
- **Steps**:
  1. 建立 `scenarios/response quality/`（含空格），放入 `dataset.csv` + `eval_spec.yaml`
  2. 執行 `python -m evals.runner --all --local-only 2>&1`
  3. Assert: 輸出包含 "response quality" 和 "invalid" 或 "character"
  4. Assert: 建議使用 `response_quality`
- **Expected**: 清楚的驗證錯誤和修正建議

#### S-disc-08: 兩個 scenario 的 config 宣告相同 `name` → 警告

- **Method**: script
- **Steps**:
  1. 建立 `scenarios/v1_quality/eval_spec.yaml` 含 `name: response_quality`
  2. 建立 `scenarios/v2_quality/eval_spec.yaml` 含 `name: response_quality`
  3. 兩個目錄都含有效的 `dataset.csv`
  4. 執行 `python -m evals.runner --all --local-only 2>&1`
  5. Assert: 輸出包含 "duplicate" 或 "response_quality" 重複相關的警告
- **Expected**: 警告使用者 experiment name 衝突

---

#### S-csv-01: 單一欄位對應到 input string

- **Method**: script
- **Steps**:
  1. 準備 test scenario：`column_mapping: { prompt: input }`，CSV 含 `prompt` 欄位
  2. 使用 mock task function 回傳 input 值（echo back）
  3. 執行 `python -m evals.runner <scenario> --local-only`
  4. 讀取 result CSV，assert `output.response` 包含原始 prompt 文字
- **Expected**: input 為 string 正確傳遞

#### S-csv-02: 多欄位對應到 expected 和 metadata

- **Method**: script
- **Steps**:
  1. 準備 config：`column_mapping: { prompt: input, ideal_answer: expected.answer, difficulty: metadata.difficulty }`
  2. CSV row: `prompt="Revenue trend?", ideal_answer="Growing", difficulty="medium"`
  3. 使用 mock task function 回傳 `{"response": json.dumps(received_input)}`
  4. 執行 eval，讀取 result CSV
  5. Assert: `output.response` 包含原始 prompt 作為 string
- **Expected**: dotpath notation 正確組裝 expected/metadata

#### S-csv-03: mapping 引用不存在的 CSV 欄位 → 立即報錯

- **Method**: script
- **Steps**:
  1. `column_mapping` 引用 `question: input`，但 CSV headers 為 `prompt, ideal_answer`
  2. 執行 `python -m evals.runner <scenario> --local-only 2>&1`
  3. Assert: exit code ≠ 0
  4. Assert: 錯誤訊息包含 "question" 和 CSV headers 列表
  5. Assert: 無 result CSV 產出（task function 未執行）
- **Expected**: upfront validation，fail-fast

#### S-csv-04: 只有 header 沒有 data rows 的 CSV → 錯誤

- **Method**: script
- **Steps**:
  1. `dataset.csv` 只有 header row
  2. 執行 `python -m evals.runner <scenario> --local-only 2>&1`
  3. Assert: exit code ≠ 0
  4. Assert: 錯誤訊息包含 "no data rows"
- **Expected**: 不會靜默成功

#### S-csv-05: BOM 開頭的 CSV 正確解析

- **Method**: script
- **Steps**:
  1. 建立含 UTF-8 BOM 的 CSV：`echo -e '\xEF\xBB\xBFprompt,ideal_answer' > dataset.csv`
  2. 加入一筆 data row
  3. Config mapping 引用 `prompt: input`
  4. 執行 eval
  5. Assert: exit code = 0（mapping 成功找到 `prompt` 欄位）
- **Expected**: BOM 被正確處理

#### S-csv-06: CJK 內容端到端保持正確

- **Method**: script
- **Steps**:
  1. CSV 含 prompt `"請問台灣的首都在哪裡？"`
  2. Mock task function echo back input
  3. 執行 eval
  4. 讀取 result CSV，assert output 欄位包含完整 CJK 文字
- **Expected**: 無 mojibake

#### S-csv-07: 空白 cell 與有值 cell 的行為不同

- **Method**: script
- **Steps**:
  1. CSV 有 `expect_tool` 欄位 mapped to `expected.tool`
  2. Row 1: `expect_tool="tavily_search"`，Row 2: `expect_tool=`（空白）
  3. 使用 mock task function + mock scorer 回傳 `str(type(expected.get("tool")))` 作為 name
  4. 執行 eval
  5. Assert: Row 1 的 expected.tool 是 string，Row 2 的 expected.tool 是 None
- **Expected**: 空白 cell 為 None，非空字串

#### S-csv-08: 數值閾值轉為 float，非數值 ID 保持 string

- **Method**: script
- **Steps**:
  1. CSV 有 `expect_cjk_min="0.8"`, `version="3.10"`, `case_id="001"`
  2. Mock scorer 回傳 type information
  3. 執行 eval
  4. `[POST-CODING: 透過 debug log 或 mock scorer 驗證 expect_cjk_min 是 float 0.8，version 是 string "3.10"，case_id 是 string "001"]`
- **Expected**: 安全的 auto-conversion

#### S-csv-09: 未 mapped 的欄位不報錯且在 result CSV 中原封不動保留

- **Method**: script
- **Steps**:
  1. 準備 CSV 含 `prompt, ideal_answer, notes, reviewer`，其中 `notes` 和 `reviewer` 不在 `column_mapping`
  2. Config mapping 只定義 `prompt: input, ideal_answer: expected.answer`
  3. 使用 mock task function echo back input
  4. 執行 `python -m evals.runner <scenario> --local-only`
  5. Assert: exit code = 0（mapping 階段無錯誤）
  6. 讀取 result CSV
  7. Assert: result CSV header 包含 `prompt, ideal_answer, notes, reviewer, output.*, score_*`
  8. Assert: `notes` 和 `reviewer` 欄位值與原始 CSV 完全相同
- **Expected**: unmapped 欄位 passthrough，不影響 pipeline

---

#### S-scr-01: Programmatic scorer 正確評分

- **Method**: script
- **Steps**:
  1. 準備 scenario：config 設定 `cjk_ratio` scorer，CSV 含 `expect_cjk_min: 0.20`
  2. Mock task function 回傳含 CJK 的文字（CJK ratio > 0.20）
  3. 執行 eval
  4. 讀取 result CSV，assert `score_cjk_ratio` 為 `1.0`
- **Expected**: scorer 正確計算並回傳 pass

#### S-scr-02: 無法解析的 scorer dotpath → 在任何 row 執行前報錯

- **Method**: script
- **Steps**:
  1. Config 設定 `function: scorers.nonexistent.my_scorer`
  2. 執行 `python -m evals.runner <scenario> --local-only 2>&1`
  3. Assert: exit code ≠ 0
  4. Assert: 錯誤訊息包含 "scorers.nonexistent"
  5. Assert: 無 result CSV 產出（task function 未執行）
- **Expected**: fail fast，不浪費計算

#### S-scr-03: Rubric template 正確插值 expected 欄位

- **Method**: script
- **Steps**:
  1. Config 設定 LLM-judge scorer（`autoevals.LLMClassifier`），rubric: `"Does the output mention {{expected.must_mention}}?"`
  2. CSV row `must_mention="revenue growth"`
  3. `[POST-CODING: mock LLMClassifier 的 LLM call 或透過 debug log 捕捉實際送出的 prompt_template rendered 結果]`
  4. Assert: 送出的 rubric 為 `"Does the output mention revenue growth?"`
- **Expected**: Mustache 插值正確

#### S-scr-04: Rubric 引用不存在的 expected 欄位 → 錯誤

- **Method**: script
- **Steps**:
  1. Rubric 含 `{{expected.nonexistent_field}}`（Mustache 語法）
  2. 執行 eval
  3. Assert: 錯誤訊息指出 `nonexistent_field` 無法解析，或 Mustache render 結果為空字串被偵測
- **Expected**: 插值變數驗證

#### S-scr-05: 空白的 expected 欄位在 rubric 中被清楚處理

- **Method**: script
- **Steps**:
  1. Rubric 含 `{{expected.must_mention}}`，但 CSV row 的 `must_mention` 為空白（None）
  2. 執行 eval
  3. Assert: 顯示警告或錯誤指出 `expected.must_mention` 為空（而非靜默插入空字串）
- **Expected**: 不產出無意義的 rubric

#### S-scr-06: 一個 scorer 失敗，其他 scorer 仍然執行

- **Method**: script
- **Steps**:
  1. 建立 3 個 scorers：#1 正常、#2 拋出 RuntimeError、#3 正常
  2. 執行 eval
  3. 讀取 result CSV，assert #1 和 #3 有分數值，#2 標記為 `ERROR`
  4. Assert: terminal 輸出指出 scorer #2 失敗
- **Expected**: failure isolation，partial results 保留

#### S-scr-07: Error 狀態與 score 0.0 可區分

- **Method**: script
- **Steps**:
  1. 建立 scenario：Row A 的 output 完全不符 expected（scorer 正常回傳 0.0），Row B 的 scorer 拋出 exception
  2. 執行 eval
  3. 讀取 result CSV
  4. Assert: Row A 有 `score_factuality: 0.0`（float），Row B 有 `score_factuality: ERROR`（string）
- **Expected**: 兩種情況明確可區分

#### S-scr-08: 重複的 scorer name → config 載入時報錯

- **Method**: script
- **Steps**:
  1. Config 定義兩個 scorers 都命名為 `"accuracy"`
  2. 執行 `python -m evals.runner <scenario> --local-only 2>&1`
  3. Assert: exit code ≠ 0
  4. Assert: 錯誤訊息包含 "duplicate" 和 "accuracy"
- **Expected**: config 驗證階段攔截

---

#### S-run-01: Task function 以 input string 呼叫並取得 output

- **Method**: script
- **Steps**:
  1. 建立 mock task function：`def run(input): return {"response": f"received: {input}"}`
  2. 執行 eval
  3. 讀取 result CSV，assert `output.response` 以 "received:" 開頭且包含 input 值
- **Expected**: task function 接收 string input

#### S-run-02: config 缺少 `task.function` → 在執行前報錯

- **Method**: script
- **Steps**:
  1. Config 有 name、column_mapping 但缺少 task.function
  2. 執行 `python -m evals.runner <scenario> --local-only 2>&1`
  3. Assert: exit code ≠ 0
  4. Assert: 錯誤訊息包含 "task.function" 和 "required"
- **Expected**: schema validation

#### S-run-03: config YAML 語法錯誤 → 清楚報錯

- **Method**: script
- **Steps**:
  1. 在 eval_spec.yaml 中放入無效 YAML（tab/space 混用）
  2. 執行 runner
  3. Assert: 錯誤訊息包含 scenario 名稱和 "YAML" 或 "parse"
  4. Assert: 不是 raw Python traceback
- **Expected**: 人類可讀的錯誤訊息

#### S-run-04: 混合成功與失敗時，成功的仍然執行

- **Method**: script
- **Steps**:
  1. 建立 `scenarios/alpha/`（合法）、`scenarios/beta/`（scorer dotpath 錯誤）、`scenarios/gamma/`（合法）
  2. 執行 `python -m evals.runner --all --local-only 2>&1`
  3. Assert: `results/alpha_*.csv` 存在
  4. Assert: `results/gamma_*.csv` 存在
  5. Assert: 輸出包含 summary（如 "2 succeeded, 1 failed"）
- **Expected**: 合法 scenario 全部執行，失敗的不阻擋後續

#### S-run-05: `--local-only` 不需要 API key 也能執行

- **Method**: script
- **Steps**:
  1. `unset BRAINTRUST_API_KEY`
  2. 執行 `python -m evals.runner language_policy --local-only`
  3. Assert: exit code = 0
  4. Assert: result CSV 存在
- **Expected**: local mode 無 Braintrust 依賴

#### S-run-06: 指定不存在的 output 目錄 → 自動建立

- **Method**: script
- **Steps**:
  1. 確認 `./test_output_dir/` 不存在
  2. 執行 `python -m evals.runner language_policy --local-only --output-dir ./test_output_dir`
  3. Assert: `./test_output_dir/` 被建立且含 result CSV
  4. 清理：刪除 `./test_output_dir/`
- **Expected**: auto-create 目錄

#### S-run-07: Task function 缺少 return → 不產出假 score

- **Method**: script
- **Steps**:
  1. 建立 task function 沒有 return statement（Python 回傳 None）
  2. 執行 eval
  3. Assert: 錯誤訊息指出 task function 回傳 None
  4. Assert: 該 row 標記為 error，scorer 不被呼叫
- **Expected**: None output 被偵測和報告

#### S-run-08: 部分 row 失敗時，result CSV 標記失敗行

- **Method**: script
- **Steps**:
  1. 建立 mock task function：row 6 拋出 TimeoutError，其他正常
  2. CSV 含 8 rows
  3. 執行 eval
  4. 讀取 result CSV
  5. Assert: CSV 有 8 rows（非 7）
  6. Assert: row 6 的 output 和 score 欄位含 `ERROR`
  7. Assert: rows 1-5, 7-8 有正常值
  8. Assert: terminal 顯示 "7/8 cases succeeded"
- **Expected**: 完整 8 rows，失敗行有 error marker

#### S-run-09: Task function 超時 → 該 case 標記 error

- **Method**: script
- **Steps**:
  1. Config 設定 `task.timeout: 5`（5 秒，用於測試）
  2. Mock task function 含 `time.sleep(30)` 模擬 hung agent
  3. CSV 含 2 rows（row 1 正常，row 2 會 hang）
  4. 執行 eval
  5. Assert: row 1 正常完成
  6. Assert: row 2 在約 5 秒後標記為 `TIMEOUT`
  7. Assert: 總執行時間 < 15 秒（非 30+）
- **Expected**: timeout 生效，不會無限掛起

---

#### S-res-01: Result CSV 結構正確

- **Method**: script
- **Steps**:
  1. Scenario CSV 有 3 個 input 欄位（`prompt, ideal_answer, notes`），2 個 scorers（`factuality, completeness`）
  2. Mock task function 回傳 `{"response": "...", "model": "gpt-4"}`
  3. 執行 eval
  4. 讀取 result CSV header
  5. Assert: 欄位包含 `prompt, ideal_answer, notes, output.response, output.model, score_factuality, score_completeness`
- **Expected**: 所有原始欄位 + output.* + score_*

#### S-res-02: 兩次執行產出不同的 result 檔案

- **Method**: script
- **Steps**:
  1. 執行 eval 一次，記錄 result CSV 檔名
  2. 再次執行 eval
  3. Assert: `results/` 下有 2 個不同的 `language_policy_*.csv` 檔案
  4. Assert: 第一個檔案未被修改
- **Expected**: never-overwrite

#### S-res-03: 欄位名是原始 CSV header，非 dotpath

- **Method**: script
- **Steps**:
  1. Input CSV 有欄位 `prompt, ideal_answer`，mapping 為 `prompt: input, ideal_answer: expected.answer`
  2. 執行 eval
  3. 讀取 result CSV header
  4. Assert: 欄位名含 `prompt, ideal_answer`（非 `input, expected.answer`）
- **Expected**: 人類可讀的原始欄位名

#### S-res-04: Output 含逗號和換行時正確 escape

- **Method**: script
- **Steps**:
  1. Mock task function 回傳 `{"response": "First, we note\nthat revenue is $25.5B"}`
  2. 執行 eval
  3. 用 Python `csv.reader` 讀取 result CSV
  4. Assert: `output.response` 欄位值完整等於原始文字（含逗號和換行）
- **Expected**: proper CSV escaping

#### S-res-05: Input CSV 有欄位名 `output` → 衝突處理

- **Method**: script
- **Steps**:
  1. CSV 有欄位 `prompt, output, ideal_answer`（`output` 是使用者自定義欄位）
  2. 執行 eval
  3. 讀取 result CSV header
  4. Assert: 原始 `output` 欄位和生成的 `output.*` 欄位都存在且不衝突
- **Expected**: 無欄位名覆蓋或資料遺失

#### S-res-06: 從不同 working directory 執行，results 位置一致

- **Method**: script
- **Steps**:
  1. 從 repo root 執行 `python -m evals.runner language_policy --local-only`，記錄 result CSV 路徑
  2. 從 `backend/` 目錄執行相同指令，記錄 result CSV 路徑
  3. Assert: 兩個 result CSV 在相同的目錄下
- **Expected**: results 路徑不受 CWD 影響

---

#### S-bt-02: 缺少 API key 時 fail fast

- **Method**: script
- **Steps**:
  1. `unset BRAINTRUST_API_KEY`
  2. 執行 `python -m evals.runner language_policy 2>&1`（無 `--local-only`）
  3. Assert: exit code ≠ 0
  4. Assert: 錯誤訊息包含 "BRAINTRUST_API_KEY" 和 "--local-only"
  5. Assert: 沒有 result CSV 產出
- **Expected**: fail fast，不浪費計算

#### S-bt-03: `--local-only` 不觸發任何 Braintrust SDK 行為

- **Method**: script
- **Steps**:
  1. `unset BRAINTRUST_API_KEY`
  2. 執行 `python -m evals.runner language_policy --local-only`
  3. Assert: exit code = 0
  4. `[POST-CODING: 確認 braintrust module 未被 import（可透過 sys.modules 檢查或 monkey-patch import hook）]`
- **Expected**: 完全隔離

#### S-bt-04: Langfuse 不可用時 eval 仍然完成

- **Method**: script
- **Steps**:
  1. 設定無效的 `LANGFUSE_SECRET_KEY`（或 unset）
  2. 執行 `python -m evals.runner language_policy --local-only`
  3. Assert: exit code = 0
  4. Assert: result CSV 存在
  5. Assert: 輸出包含 Langfuse 相關的 warning（非 error）
- **Expected**: graceful degradation

#### S-bt-05: Braintrust upload 失敗不影響本地結果

- **Method**: script
- **Steps**:
  1. `[POST-CODING: 設定方式使 Braintrust upload 失敗（如設定無效的 API key 或 mock network failure）]`
  2. 執行 eval（非 local-only）
  3. Assert: result CSV 存在於 `results/`
  4. Assert: 輸出含 Braintrust 上傳失敗的錯誤訊息
- **Expected**: local results 不受 Braintrust 失敗影響

#### S-bt-06: --all 不會造成 experiment 之間的 trace 汙染

- **Method**: script
- **Steps**:
  1. 準備 2 個合法 scenario：`alpha` 和 `beta`
  2. 執行 `python -m evals.runner --all --local-only`
  3. Assert: 兩個 scenario 都成功完成
  4. `[POST-CODING: 透過 Braintrust API 或 local mode output 驗證兩個 experiments 的 test cases 不重疊]`
- **Expected**: experiment 隔離

---

#### S-xf-01: 中途中斷保留已完成的 partial results

- **Method**: script
- **Steps**:
  1. 建立 scenario 含 10 rows，mock task function 在 row 6 加入 `time.sleep(60)`
  2. 在背景執行 eval
  3. 等待 5 秒（確保前 5 rows 完成），送 SIGINT
  4. 檢查是否有 result CSV 或 partial output
  5. Assert: 不存在損壞的半寫 CSV 檔案
- **Expected**: graceful shutdown

#### S-xf-02: 含特殊字元的值通過完整 pipeline 不變

- **Method**: script
- **Steps**:
  1. CSV 含 prompt 值 `"Tesla's revenue was $25.5B, up 15%\nKey highlights:\n- EPS: $1.85"`
  2. Mock task function echo back input
  3. 執行 eval
  4. 讀取 result CSV，找到對應 row
  5. Assert: 原始 `prompt` 欄位值完整保留（含逗號、換行、引號、dollar sign）
- **Expected**: end-to-end 資料完整性

---

## Automated Verification — Journey Scenarios

#### J-disc-01: 新手首次設定的錯誤恢復流程

- **Method**: script
- **Steps**:
  1. 確認 `scenarios/` 不存在或為空
  2. 執行 `python -m evals.runner --all --local-only 2>&1`
  3. Assert: 輸出含 "no scenarios found"
  4. 建立 `scenarios/test1/`，只放 `dataset.csv`
  5. 執行 `python -m evals.runner test1 --local-only 2>&1`
  6. Assert: 輸出含 "eval_spec.yaml" missing
  7. 加入 `eval_spec.yaml`，但 `task.function` 指向不存在的 function
  8. 執行 runner
  9. Assert: 輸出含 task function resolution error
  10. 修正 dotpath 指向合法 function
  11. 執行 runner
  12. Assert: exit code = 0，result CSV 存在
- **Expected**: 每一步都有清楚的錯誤提示，最終成功

#### J-csv-01: 從 CSV 編輯到 eval 執行的完整流程（含未 mapped 欄位保留）

- **Method**: script
- **Steps**:
  1. 準備包含 CJK 內容的 CSV（模擬 Google Sheets 匯出），含 `id, description`（未 mapped，供人工備註用）和 mapped 欄位，配對 config
  2. 執行 `python -m evals.runner language_policy --local-only`
  3. Assert: exit code = 0
  4. 讀取 result CSV
  5. Assert: 所有 CJK 內容正確保留
  6. Assert: 所有原始欄位（含未 mapped 的 `id`, `description`）都在 result CSV 中，值不變
  7. Assert: result CSV 含正確的 `output.*` 和 `score_*` 欄位
- **Expected**: CSV 作為 source of truth 的完整 pipeline，unmapped 欄位 passthrough

#### J-scr-01: 混合 programmatic 和 LLM-judge scorers（language_policy 實際場景）

- **Method**: script
- **Steps**:
  1. 使用 `language_policy` scenario：config 含 2 個 programmatic scorers（`tool_arg_no_cjk`, `response_language`）+ 1 個 LLM-judge scorer（`response_relevance`，rubric 檢查回覆是否只討論 `{{expected.ticker}}`）
  2. CSV 含 8 筆 test cases，包含 `ticker` 欄位
  3. 執行 `python -m evals.runner language_policy --local-only`
  4. 讀取 result CSV
  5. Assert: 8 rows，每 row 有 3 個 score 欄位（`score_tool_arg_no_cjk`, `score_response_language`, `score_response_relevance`）
  6. Assert: 3 種 score 都有值（非 ERROR）
  7. Assert: `response_relevance` score 為 0.0 或 1.0（來自 LLMClassifier 的 Y/N choice）
- **Expected**: programmatic 和 LLM-judge scorer 共存，LLM-judge 使用真實 LLM 呼叫

#### J-run-01: 單一 scenario 端到端執行

- **Method**: script
- **Steps**:
  1. 準備完整的 scenario（config + CSV + task function + scorer）
  2. 執行 `python -m evals.runner language_policy --local-only`
  3. Assert: result CSV 存在且結構正確
  4. Assert: 每一 row 都有 output 和 score 值
  5. Assert: 所有原始欄位保留
- **Expected**: 完整 data flow

#### J-res-01: Config 變更前後的 result CSV 共存

- **Method**: script
- **Steps**:
  1. 以 2 個 scorers 執行 eval，記錄 result CSV A 的檔名
  2. 修改 config 新增第 3 個 scorer
  3. 再次執行 eval
  4. Assert: result CSV A 仍存在且未被修改
  5. Assert: result CSV B 存在且有 3 個 score 欄位
- **Expected**: 歷史結果不受 config 變更影響

#### J-bt-02: 多 scenario batch evaluation

- **Method**: script
- **Steps**:
  1. 準備 2 個合法 scenario 各有不同的 CSV 和 scorers
  2. 執行 `python -m evals.runner --all --local-only`
  3. Assert: 兩個 scenario 各自的 result CSV 存在
  4. Assert: 輸出顯示 summary "2 scenarios succeeded"
- **Expected**: batch 模式完整運作

---

## Manual Verification

### Manual Behavior Test

#### S-bt-01: 預設模式同時產出 local CSV 和 Braintrust experiment

- **Reason**: 需要 Braintrust 帳號和有效的 API key 才能驗證 experiment 建立
- **Steps**:
  1. 設定 `BRAINTRUST_API_KEY` 環境變數
  2. 執行 `python -m evals.runner language_policy`
  3. 確認 terminal 輸出 Braintrust experiment URL
  4. 確認 `results/` 有 result CSV
  5. 開啟 URL，確認 experiment 出現在 Braintrust UI
- **Expected**: dual output（local CSV + Braintrust experiment）

#### S-bt-07: LLM-judge 的 LLM 呼叫不出現在 task trace 中

- **Reason**: 需要 Braintrust UI 檢視 trace 結構，無法透過 CLI 驗證 trace 內容
- **Steps**:
  1. 準備含 LLM-judge scorer 的 scenario
  2. 執行 eval（非 local-only）
  3. 在 Braintrust UI 開啟 experiment
  4. Drill-down 到一個 test case 的 trace
  5. 確認 trace 只包含 agent 的 LLM calls 和 tool calls
  6. 確認 scorer 的 LLM call 不在 trace 中
- **Expected**: 乾淨的 trace，只有 agent 行為

#### S-bt-08: Experiment metadata 附加到 Braintrust experiment

- **Reason**: 需要 Braintrust UI 確認 metadata 正確顯示和可搜尋
- **Steps**:
  1. Config 加入 `experiment: { model: "gpt-4o", prompt_version: "v3-cot" }`
  2. 執行 eval
  3. 在 Braintrust UI 確認 experiment 附帶 metadata
  4. 嘗試用 metadata 搜尋或篩選
- **Expected**: metadata 可見且可用於篩選

### User Acceptance Test

#### J-bt-01: Prompt 迭代工作流程（含 programmatic + LLM-judge 混合 scores）

- **Acceptance Question**: Braintrust 的 experiment diff 是否能有效支援 prompt 迭代決策？包含 LLM-judge score 的變化是否清楚可見？
- **Steps**:
  1. 以目前的 prompt 執行 `python -m evals.runner language_policy`（3 個 scorers：`tool_arg_no_cjk`, `response_language`, `response_relevance`）
  2. 修改 agent 的 system prompt
  3. 再次執行 eval
  4. 在 Braintrust UI 開啟兩個 experiments 的 Compare view
  5. 觀察：能否看到每個 test case 的 3 個 scorer 分數變化（含 LLM-judge `response_relevance`）？
  6. 點進一個退步的 test case，觀察 trace 是否清楚呈現 input → tool calls → output
  7. 確認 `response_relevance` scorer 的 LLM call 不在 task trace 中（trace 隔離）
  8. 判斷：這個 diff 資訊是否足以決定 prompt 修改是好是壞？
- **Expected**: 清楚的 per-case regression/improvement（含 LLM-judge score），trace drill-down 提供足夠的 debugging context
