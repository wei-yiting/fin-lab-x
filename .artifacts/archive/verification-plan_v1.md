# Verification Plan

## Meta

- Scenarios Reference: `.artifacts/current/bdd-scenarios.md`
- Generated: 2026-03-27

---

## Automated Verification

### Deterministic

#### S-disc-01: 完整目錄結構被正確發現

- **Method**: script
- **Steps**:
  1. 確認 `scenarios/language_policy/` 含 `dataset.csv` 和 `config.yaml`
  2. 執行 `python -m evals.runner language_policy --local-only`
  3. 檢查 exit code = 0
  4. 檢查 `results/` 目錄下有 `language_policy_*.csv` 檔案
- **Expected**: 指令成功完成，result CSV 存在

#### S-disc-02: 缺少檔案的目錄被跳過並警告

- **Method**: script
- **Steps**:
  1. 建立 `scenarios/broken/`，只放 `config.yaml`
  2. 確保至少一個合法 scenario 存在
  3. 執行 `python -m evals.runner --all --local-only 2>&1`
  4. Assert: stderr/stdout 包含 "broken" 相關的 warning 文字
  5. Assert: 合法 scenario 的 result CSV 存在
- **Expected**: broken 被跳過有警告，合法 scenario 正常產出

#### S-disc-03: 不存在的 scenario 名稱顯示可用清單

- **Method**: script
- **Steps**:
  1. 執行 `python -m evals.runner nonexistent --local-only 2>&1`
  2. Assert: exit code ≠ 0
  3. Assert: 輸出包含 "not found" 和至少一個可用的 scenario 名稱
- **Expected**: 錯誤訊息含 scenario 名稱和可用清單

#### S-disc-04: `--all` 在沒有任何 scenario 時提示

- **Method**: script
- **Steps**:
  1. 暫時清空 `scenarios/` 目錄（或指向一個空目錄）
  2. 執行 `python -m evals.runner --all --local-only 2>&1`
  3. Assert: 輸出包含 "no scenarios found"
- **Expected**: 不會靜默成功

#### S-disc-05: 混合合法與不合法時，合法的仍然執行

- **Method**: script
- **Steps**:
  1. 建立 `scenarios/alpha/`（合法）、`scenarios/beta/`（合法）、`scenarios/broken/`（缺 CSV）
  2. 執行 `python -m evals.runner --all --local-only 2>&1`
  3. Assert: `results/alpha_*.csv` 存在
  4. Assert: `results/beta_*.csv` 存在
  5. Assert: 輸出包含 summary（如 "2 succeeded, 1 skipped"）
- **Expected**: 合法 scenario 全部執行，broken 被跳過

#### S-csv-01: 單一欄位對應到 input string

- **Method**: script
- **Steps**:
  1. 準備 test scenario：`column_mapping: { prompt: input }`，CSV 含 `prompt` 欄位
  2. 使用 mock task function 回傳 input 值（echo back）
  3. 執行 eval
  4. `[POST-CODING: 檢查 Braintrust log 或 runner 內部 debug output 確認 transformed data 結構]`
- **Expected**: input 為 string 而非 object

#### S-csv-02: 多欄位對應到巢狀結構

- **Method**: script
- **Steps**:
  1. 準備 test scenario：`column_mapping: { prompt: input.question, category: input.category, ideal_answer: expected.answer }`
  2. CSV row: `prompt="Revenue trend?", category="financials", ideal_answer="Growing"`
  3. 使用 mock task function 回傳 `json.dumps(input)` 以檢視 input 結構
  4. 執行 eval，檢查 result CSV 的 output 欄位
  5. Assert: output 包含 `{"question": "Revenue trend?", "category": "financials"}`
- **Expected**: dotpath notation 正確產出巢狀 object

#### S-csv-03: 未映射的額外欄位被忽略

- **Method**: script
- **Steps**:
  1. CSV 含 `prompt, ideal_answer, notes`，mapping 只定義 `prompt` 和 `ideal_answer`
  2. 執行 eval
  3. Assert: 正常完成，沒有 error
  4. `[POST-CODING: 確認 transformed data 不含 notes 欄位]`
- **Expected**: 額外欄位不影響執行

#### S-csv-04: mapping 引用不存在的 CSV 欄位 → 錯誤

- **Method**: script
- **Steps**:
  1. `column_mapping` 引用 `question: input`，但 CSV 只有 `prompt` 欄位
  2. 執行 `python -m evals.runner <scenario> --local-only 2>&1`
  3. Assert: exit code ≠ 0
  4. Assert: 錯誤訊息包含 "question" 和 "not found"
- **Expected**: upfront validation，不會執行任何 task

#### S-csv-05: CJK 內容端到端保持正確

- **Method**: script
- **Steps**:
  1. CSV 含 prompt `"請問台灣的首都在哪裡？"`
  2. Mock task function echo back input
  3. 執行 eval
  4. 讀取 result CSV，assert output 欄位包含 `"請問台灣的首都在哪裡？"`（完整 CJK 文字）
- **Expected**: 無 mojibake

#### S-csv-06: CSV 內含逗號、換行、引號的欄位值正確解析

- **Method**: script
- **Steps**:
  1. CSV 含 cell 值 `"He said, ""hello""\nand left"`
  2. 執行 eval
  3. 讀取 result CSV，parse 後 assert 原始值完整保留
- **Expected**: RFC 4180 compliant parsing 和 writing

#### S-csv-07: 只有 header 沒有 data rows 的 CSV → 錯誤

- **Method**: script
- **Steps**:
  1. `dataset.csv` 只有 header row
  2. 執行 `python -m evals.runner <scenario> --local-only 2>&1`
  3. Assert: exit code ≠ 0
  4. Assert: 錯誤訊息包含 "no data rows"
- **Expected**: 不會靜默成功

#### S-scr-01: Programmatic scorer 正確評分

- **Method**: script
- **Steps**:
  1. 準備 scenario：config 設定 `cjk_ratio` scorer，CSV 含 `expect_cjk_min: 0.20`
  2. Mock task function 回傳含有 CJK 的文字（CJK ratio > 0.20）
  3. 執行 eval
  4. 讀取 result CSV，assert `score_cjk_ratio` 為 `1.0`
- **Expected**: scorer 正確計算並回傳 pass

#### S-scr-02: 無法解析的 scorer dotpath → 在任何 row 執行前報錯

- **Method**: script
- **Steps**:
  1. Config 設定 `function: scorers.nonexistent.my_scorer`
  2. 執行 `python -m evals.runner <scenario> --local-only 2>&1`
  3. Assert: exit code ≠ 0
  4. Assert: 錯誤在任何 task output 之前出現
  5. Assert: 錯誤訊息包含 "scorers.nonexistent"
- **Expected**: fail fast，不浪費計算

#### S-scr-03: Rubric template 正確插值 expected 欄位

- **Method**: script
- **Steps**:
  1. Config 設定 LLM-judge scorer，rubric: `"Does the output mention {expected.must_mention}?"`
  2. CSV row `must_mention="revenue growth"`
  3. `[POST-CODING: 在 LLM-judge scorer 內加 debug log 或 mock LLM call，捕捉實際送出的 rubric]`
  4. Assert: 送出的 rubric 為 `"Does the output mention revenue growth?"`
- **Expected**: 插值正確，非原始 template 文字

#### S-scr-04: Rubric 引用不存在的 expected 欄位 → 錯誤

- **Method**: script
- **Steps**:
  1. Rubric 含 `{expected.nonexistent_field}`
  2. 執行 eval
  3. Assert: 錯誤訊息指出 `nonexistent_field` 無法解析
- **Expected**: 插值變數驗證

#### S-scr-05: Score 超出 0~1 → 報錯

- **Method**: script
- **Steps**:
  1. 建立 test scorer 回傳 `{"name": "bad", "score": 1.5}`
  2. 執行 eval
  3. Assert: 錯誤訊息包含 "score" 和 "out of range" 或 "[0, 1]"
- **Expected**: validation error

#### S-scr-06: 一個 scorer 失敗，其他 scorer 仍然執行

- **Method**: script
- **Steps**:
  1. 建立 3 個 scorers：#1 正常、#2 拋出 RuntimeError、#3 正常
  2. 執行 eval
  3. 讀取 result CSV，assert #1 和 #3 有分數值，#2 標記為 error/null
  4. Assert: terminal 輸出指出 scorer #2 失敗
- **Expected**: failure isolation，partial results 保留

#### S-run-01: Task function 以 input 呼叫並取得 output

- **Method**: script
- **Steps**:
  1. 建立 mock task function：`def run(input): return f"received: {json.dumps(input)}"`
  2. 執行 eval
  3. 讀取 result CSV，assert output 欄位以 "received:" 開頭且包含 input 值
  4. `[POST-CODING: 確認 task function 沒有收到 expected 或 metadata 參數]`
- **Expected**: task function 只接收 input

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
  1. 在 config.yaml 中放入無效 YAML
  2. 執行 runner
  3. Assert: 錯誤訊息包含 scenario 名稱和 "YAML" 或 "parse"
- **Expected**: 不會是 raw Python traceback

#### S-res-01: 兩次執行產出不同的 result 檔案

- **Method**: script
- **Steps**:
  1. 執行 eval 一次，記錄 result CSV 檔名
  2. 等待至少 1 分鐘（timestamp 精度為分鐘）
  3. 再次執行 eval
  4. Assert: `results/` 下有 2 個不同的 `language_policy_*.csv` 檔案
- **Expected**: never-overwrite

#### S-res-02: Result CSV 結構正確

- **Method**: script
- **Steps**:
  1. Scenario 有 2 個 input 欄位（prompt, ideal_answer）和 2 個 scorers（factuality, completeness）
  2. 執行 eval
  3. 讀取 result CSV header
  4. Assert: 欄位為 `prompt, ideal_answer, output, score_factuality, score_completeness`
  5. Assert: score 值介於 0.0 和 1.0
- **Expected**: 欄位結構符合 design

#### S-res-03: Output 含逗號和換行時正確 CSV escape

- **Method**: script
- **Steps**:
  1. Mock task function 回傳 `"First, we note\nthat this is multi-line"`
  2. 執行 eval
  3. 用 Python `csv.reader` 讀取 result CSV
  4. Assert: output 欄位值完整等於原始文字（含逗號和換行）
- **Expected**: proper CSV escaping

#### S-res-04: `results/` 不存在時自動建立

- **Method**: script
- **Steps**:
  1. 確認 `results/` 目錄不存在（或暫時移走）
  2. 執行 eval
  3. Assert: `results/` 被自動建立且含 result CSV
- **Expected**: auto-create

#### S-bt-02: `--local-only` 不需要 API key 也能執行

- **Method**: script
- **Steps**:
  1. 確保 `BRAINTRUST_API_KEY` 環境變數未設定：`unset BRAINTRUST_API_KEY`
  2. 執行 `python -m evals.runner language_policy --local-only`
  3. Assert: exit code = 0
  4. Assert: result CSV 存在
- **Expected**: local mode 無 Braintrust 依賴

#### S-bt-03: 缺少 API key 時 fail fast

- **Method**: script
- **Steps**:
  1. `unset BRAINTRUST_API_KEY`
  2. 執行 `python -m evals.runner language_policy 2>&1`（無 `--local-only`）
  3. Assert: exit code ≠ 0
  4. Assert: 錯誤訊息包含 "BRAINTRUST_API_KEY" 和 "--local-only"
  5. Assert: 沒有 result CSV 產出（未執行任何 task）
- **Expected**: fail fast，不浪費計算

#### S-bt-04: 網路失敗不影響本地結果

- **Method**: script
- **Steps**:
  1. `[POST-CODING: 設定方式使 Braintrust API call 失敗（如設定無效的 API key 或 mock network failure）]`
  2. 執行 eval（非 local-only）
  3. Assert: result CSV 仍然存在於 `results/`
  4. Assert: 輸出含 Braintrust 上傳失敗的錯誤訊息
- **Expected**: local results 不受 Braintrust 失敗影響

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
  6. Assert: 輸出含 "config.yaml" missing
  7. 加入 `config.yaml`，但 `task.function` 指向不存在的 function
  8. 執行 runner
  9. Assert: 輸出含 task function resolution error
  10. 修正 dotpath 指向合法 function
  11. 執行 runner
  12. Assert: exit code = 0，result CSV 存在
- **Expected**: 每一步都有清楚的錯誤提示，最終成功執行

#### J-csv-01: 從 CSV 編輯到 eval 執行的完整流程

- **Method**: script
- **Steps**:
  1. 準備包含 CJK 內容的 CSV（模擬 Google Sheets 匯出）和對應 config
  2. 執行 `python -m evals.runner language_policy --local-only`
  3. Assert: exit code = 0
  4. 讀取 result CSV
  5. Assert: 所有 CJK 內容正確保留
  6. Assert: result CSV 含正確的 score 欄位
  7. `[POST-CODING: 驗證 result CSV 可在 Google Sheets 正確開啟]`
- **Expected**: CSV 作為 source of truth 的完整 pipeline 運作

#### J-scr-01: 混合 programmatic 和 LLM-judge scorers 的完整流程

- **Method**: script
- **Steps**:
  1. 準備 scenario：config 含 1 個 programmatic scorer + 1 個 LLM-judge scorer
  2. CSV 含 2 筆 test cases，包含 `must_mention` 欄位
  3. 執行 eval
  4. 讀取 result CSV
  5. Assert: 2 rows，每 row 有兩個 score 欄位
  6. Assert: programmatic score 和 LLM-judge score 都有值
- **Expected**: 兩種 scorer 類型共存

#### J-run-01: 單一 scenario 端到端執行

- **Method**: script
- **Steps**:
  1. 準備完整的 scenario（config + CSV + task function + scorer）
  2. 執行 `python -m evals.runner language_policy --local-only`
  3. Assert: result CSV 存在且結構正確
  4. Assert: 每一 row 都有 output 和 score 值
- **Expected**: 完整 data flow 驗證

#### J-res-01: Config 變更前後的 result CSV 共存

- **Method**: script
- **Steps**:
  1. 以 2 個 scorers 執行 eval，記錄 result CSV A 的檔名
  2. 修改 config 新增第 3 個 scorer
  3. 等待至少 1 分鐘後再次執行 eval
  4. Assert: result CSV A 仍存在且未被修改（checksum 不變）
  5. Assert: result CSV B 存在且有 3 個 score 欄位
- **Expected**: 歷史結果不受 config 變更影響

---

## Manual Verification

### Type 1: Technical Limitations

#### S-bt-01: 預設模式同時產出 local CSV 和 Braintrust experiment

- **Reason**: 需要 Braintrust 帳號和有效的 API key 才能驗證 experiment 建立
- **Steps**:
  1. 設定 `BRAINTRUST_API_KEY` 環境變數
  2. 執行 `python -m evals.runner language_policy`
  3. 確認 terminal 輸出 Braintrust experiment URL
  4. 確認 `results/` 有 result CSV
  5. 開啟 URL，確認 experiment 出現在 Braintrust UI
- **Expected**: dual output（local CSV + Braintrust experiment）

### Type 2: User Acceptance (UAT)

#### J-bt-01: Prompt 迭代工作流程

- **Acceptance Question**: Braintrust 的 experiment diff 是否能有效支援 prompt 迭代決策？
- **Steps**:
  1. 以目前的 prompt 執行 eval
  2. 修改 agent 的 system prompt
  3. 再次執行 eval
  4. 在 Braintrust UI 開啟兩個 experiments 的 Compare view
  5. 觀察：能否看到每個 test case 的分數變化？
  6. 點進一個退步的 test case，觀察 trace 是否清楚呈現 input → tool calls → output
  7. 判斷：這個 diff 資訊是否足以決定 prompt 修改是好是壞？
- **Expected**: 可以清楚看到 per-case regression/improvement，trace drill-down 提供足夠的 debugging context

#### J-bt-02: 新增 eval 維度並跨版本追蹤

- **Acceptance Question**: 新增 eval scenario 是否真的零 Python、零 registry？
- **Steps**:
  1. 建立新的 `scenarios/response_quality/` 目錄
  2. 編寫 `dataset.csv`（含 test cases）和 `config.yaml`（含 column mapping + scorers）
  3. 執行 `python -m evals.runner --all`
  4. 確認新的 scenario 被自動發現並執行
  5. 在 Braintrust UI 確認新的 experiment 出現
  6. 判斷：整個新增流程是否比原本的 Python dataclass 方式更快、更直覺？
- **Expected**: 新增 scenario 只需建立 CSV + YAML，不需修改任何 Python 程式碼
