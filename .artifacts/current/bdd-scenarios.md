# BDD Scenarios

## Meta
- Design Reference: `.artifacts/current/design.md`
- Generated: 2026-03-31
- Discovery Method: Three Amigos (Agent Teams — PO, Dev, QA)
- User Decisions:
  - D1: Task function output 可以是 dict（scorer 自行處理）
  - D2: v1 input 永遠是 string（單一欄位 map 到 `input`）
  - D3: Result CSV 的 output dict 展開為 `output.*` 欄位
  - D4: Config `name` optional，預設用目錄名；必須唯一
  - D5: Result CSV 保留所有原始 CSV 欄位（mapped + unmapped）
  - D6: v1 支援 configurable per-case timeout（`task.timeout`）
  - D7: Config 支援 experiment metadata（model、prompt version 等）

---

## Feature: Scenario Discovery

### Context
Runner 掃描 `scenarios/` 目錄，每個包含 `dataset.csv` + `eval_spec.yaml` 的直接子目錄即為一個可執行的 scenario。不需要 registry 檔案。

### Rule: 合法 scenario 必須是 `scenarios/` 的直接子目錄，且包含 `dataset.csv` 和 `eval_spec.yaml`

#### S-disc-01: 完整目錄結構被正確發現
> 驗證 convention-based discovery 的 happy path

- **Given** `scenarios/language_policy/` 包含 `dataset.csv`（含 8 筆 test cases）和 `eval_spec.yaml`
- **When** 執行 `python -m evals.runner language_policy`
- **Then** scenario 被發現並執行，產出 result CSV

Category: Illustrative
Origin: PO

#### S-disc-02: 缺少檔案的目錄被跳過並警告
> 驗證不完整的 scenario 目錄在 --all 時不會中斷其他 scenario

- **Given** `scenarios/broken/` 只包含 `eval_spec.yaml`，缺少 `dataset.csv`
- **And** `scenarios/language_policy/` 是合法 scenario
- **When** 執行 `python -m evals.runner --all`
- **Then** `broken` 被跳過並顯示警告（指出缺少 `dataset.csv`），`language_policy` 正常執行

Category: Illustrative
Origin: Multiple

#### S-disc-03: 不存在的 scenario 名稱顯示可用清單
> 驗證使用者打錯名稱時能快速找到正確的 scenario

- **Given** 不存在 `scenarios/nonexistent/` 目錄
- **When** 執行 `python -m evals.runner nonexistent`
- **Then** 顯示錯誤 "Scenario 'nonexistent' not found" 並列出可用的 scenario 名稱

Category: Illustrative
Origin: PO

#### S-disc-04: `--all` 在沒有任何 scenario 時提示
> 驗證空的 scenarios 目錄不會靜默成功

- **Given** `scenarios/` 目錄存在但為空（或只含 `__pycache__/`）
- **When** 執行 `python -m evals.runner --all`
- **Then** 顯示 "no scenarios found" 訊息並以非零 exit code 結束

Category: Illustrative
Origin: QA

### Rule: 錯誤訊息區分「scenario 不存在」與「scenario 不完整」

#### S-disc-05: 目錄不存在 vs 缺少檔案產生不同錯誤
> 驗證使用者能區分名稱打錯和結構不完整

- **Given** `scenarios/` 中沒有 `phantom/` 目錄，但有 `broken/`（只含 `eval_spec.yaml`）
- **When** 執行 `python -m evals.runner phantom` 然後 `python -m evals.runner broken`
- **Then** 第一個顯示 "not found" 並列出可用 scenario；第二個顯示 "missing dataset.csv in scenario 'broken'"

Category: Illustrative
Origin: Dev

### Rule: Discovery 過濾隱藏和系統目錄

#### S-disc-06: `__pycache__/` 不被視為 scenario
> 驗證 Python 系統目錄不會汙染 scenario 列表

- **Given** `scenarios/` 包含 `language_policy/`（合法）和 `__pycache__/`（Python 自動產生）
- **When** 執行 `python -m evals.runner --all`
- **Then** 只有 `language_policy` 被發現和執行，`__pycache__` 被靜默過濾

Category: Illustrative
Origin: QA

### Rule: Scenario 目錄名稱必須符合命名規則（英數字、底線、連字號）

#### S-disc-07: 目錄名含空格 → 驗證錯誤
> 驗證非開發者從 Finder 建立目錄時的錯誤防護

- **Given** `scenarios/response quality/` 包含 `dataset.csv` + `eval_spec.yaml`（目錄名含空格）
- **When** Runner 掃描 `scenarios/`
- **Then** 顯示清楚的驗證錯誤，指出 "response quality" 包含無效字元，建議使用 `response_quality`

Category: Illustrative
Origin: QA

### Rule: Config `name` 預設為目錄名，且在同一 project 中必須唯一

#### S-disc-08: 兩個 scenario 的 config 宣告相同 `name` → 警告
> 驗證重複的 experiment 名稱不會導致 Braintrust 資料合併

- **Given** `scenarios/v1_quality/eval_spec.yaml` 有 `name: response_quality`
- **And** `scenarios/v2_quality/eval_spec.yaml` 也有 `name: response_quality`
- **When** 執行 `python -m evals.runner --all`
- **Then** 顯示警告指出重複的 experiment name `response_quality`

Category: Illustrative
Origin: QA

---

### Journey Scenarios

#### J-disc-01: 新手首次設定的錯誤恢復流程
> 驗證從零開始到成功執行的完整 progressive error recovery

- **Given** 一個新開發者，尚未建立 `scenarios/` 目錄
- **When** 她執行 `python -m evals.runner --all`，看到 "no scenarios found"
- **And** 建立 `scenarios/test1/` 只放了 `dataset.csv`，再跑一次，看到 "missing eval_spec.yaml"
- **And** 加入 `eval_spec.yaml` 但 `task.function` 打錯，再跑一次，看到 "cannot resolve task function"
- **And** 修正 dotpath 再跑一次
- **Then** eval 成功執行並產出 result CSV

Category: Journey
Origin: QA

---

## Feature: CSV Dataset & Column Mapping

### Context
CSV 是 test cases 的 source of truth，必須可在 Google Sheets 中編輯。YAML config 的 `column_mapping` 將欄位名稱對應到 `{input, expected, metadata}` 結構。v1 的 `input` 永遠是 string。

### Rule: column_mapping 正確轉換 CSV rows 為 `{input, expected, metadata}`

#### S-csv-01: 單一欄位對應到 input string
> 驗證最簡單的 mapping 模式（v1 唯一的 input 模式）

- **Given** `column_mapping` 設定 `prompt: input`
- **And** CSV 有一筆 `prompt="What is AAPL's P/E ratio?"`
- **When** runner 轉換這一 row
- **Then** 產出 `{input: "What is AAPL's P/E ratio?", expected: {}, metadata: {}}`

Category: Illustrative
Origin: Dev

#### S-csv-02: 多欄位對應到 expected 和 metadata
> 驗證 dotpath notation 正確組裝 nested objects

- **Given** `column_mapping` 設定 `prompt: input`, `ideal_answer: expected.answer`, `difficulty: metadata.difficulty`
- **And** CSV row: `prompt="Revenue trend?", ideal_answer="Growing 15% YoY", difficulty="medium"`
- **When** runner 轉換這一 row
- **Then** 產出 `{input: "Revenue trend?", expected: {answer: "Growing 15% YoY"}, metadata: {difficulty: "medium"}}`

Category: Illustrative
Origin: Dev

### Rule: mapping 引用的欄位必須存在於 CSV 中，且在載入時立即驗證

#### S-csv-03: mapping 引用不存在的 CSV 欄位 → 立即報錯
> 驗證 fail-fast validation 防止浪費 task function 呼叫

- **Given** `column_mapping` 引用 `question: input`，但 CSV 只有 `prompt, ideal_answer`（沒有 `question`）
- **When** runner 載入此 scenario
- **Then** 在任何 task 執行前，顯示錯誤指出 `question` 欄位不存在於 CSV headers `[prompt, ideal_answer]`

Category: Illustrative
Origin: Multiple

### Rule: 空 CSV 或只有 header 的 CSV 是錯誤

#### S-csv-04: 只有 header 沒有 data rows 的 CSV → 錯誤
> 驗證使用者不會在不知情下跑了一個空的 eval

- **Given** `dataset.csv` 只包含 header row，沒有 data rows
- **When** runner 載入此 scenario
- **Then** 顯示錯誤 "no data rows found"

Category: Illustrative
Origin: QA

### Rule: CSV 必須正確處理 UTF-8 BOM 和特殊字元

#### S-csv-05: BOM 開頭的 CSV 正確解析
> 驗證 Excel/Google Sheets 匯出的 BOM 不會破壞第一個欄位名

- **Given** `dataset.csv` 由 Excel 匯出，開頭含 UTF-8 BOM（`\xEF\xBB\xBF`）
- **And** `column_mapping` 引用第一個欄位 `prompt: input`
- **When** runner 解析 CSV
- **Then** 第一個 header 正確讀為 `prompt`（非 `\ufeffprompt`），mapping 正常運作

Category: Illustrative
Origin: QA

#### S-csv-06: CJK 內容端到端保持正確
> 驗證中日韓文字在整個 pipeline 中不會損壞

- **Given** CSV 包含 prompt `"請問台灣的首都在哪裡？"` 和 expected answer 含中文字元
- **When** runner 執行 eval
- **Then** CJK 內容正確傳入 task function、正確寫入 result CSV，無 mojibake

Category: Illustrative
Origin: QA

### Rule: 空白 CSV cell 可被 scorer 區分為「無值」

#### S-csv-07: 空白 cell 與有值 cell 的行為不同
> 驗證使用者不會因為空白 cell 得到假的 score

- **Given** CSV 有欄位 `expect_tool` mapped to `expected.tool`
- **And** Row 1 的 `expect_tool` = `"tavily_search"`，Row 2 的 `expect_tool` 為空白
- **When** runner 轉換 rows 並傳給 scorer
- **Then** Row 1 的 `expected.tool` = `"tavily_search"`；Row 2 的 `expected.tool` = `None`（非空字串 `""`）

Category: Illustrative
Origin: Dev

### Rule: 數值字串自動轉換必須安全

#### S-csv-08: 數值閾值轉為 float，非數值 ID 保持 string
> 驗證 auto-conversion 不會損壞非數值欄位

- **Given** CSV 有 `expect_cjk_min="0.8"` 和 `version="3.10"` 和 `case_id="001"`
- **When** runner 執行 auto-conversion
- **Then** `expect_cjk_min` = `0.8`（float），`version` = `"3.10"`（string，因為會損失精度），`case_id` = `"001"`（string，因為有前導零）

Category: Illustrative
Origin: Dev

### Rule: 未包含在 column_mapping 的 CSV 欄位不影響 mapping，且保留在 result CSV 中

#### S-csv-09: 未 mapped 的欄位不報錯且在 result CSV 中原封不動保留
> 驗證 memo 或人工標注用的額外欄位不會干擾 pipeline，並在結果中完整保留

- **Given** CSV 有欄位 `prompt, ideal_answer, notes, reviewer`，其中 `notes` 和 `reviewer` 不在 `column_mapping` 中
- **And** `column_mapping` 只定義 `prompt: input, ideal_answer: expected.answer`
- **When** runner 載入並執行此 scenario
- **Then** mapping 階段不報錯
- **And** result CSV 包含 `prompt, ideal_answer, notes, reviewer, output.*, score_*`，`notes` 和 `reviewer` 的值與原始 CSV 完全相同

Category: Illustrative
Origin: PO

---

### Journey Scenarios

#### J-csv-01: 從 Google Sheets 編輯到執行 eval 的完整流程
> 驗證 CSV 作為 source of truth 的核心 value proposition，包含未 mapped 的 memo 欄位

- **Given** 開發者將 8 筆 language policy test cases 從舊的 Python dataclass 遷移到 CSV：
  `id, description, prompt, prompt_language, expect_tool, expect_cjk_min`（含中英文混合內容）
- **And** `id` 和 `description` 不在 `column_mapping` 中（供人工備註用）
- **And** 建立對應的 `eval_spec.yaml` 定義 column mapping 和 2 個 scorers
- **When** 執行 `python -m evals.runner language_policy --local-only`
- **Then** 8 筆 test cases 全部執行，result CSV 產出於 `results/` 目錄
- **And** result CSV 包含所有原始欄位（含未 mapped 的 `id`, `description`）+ output + score 欄位，CJK 內容正確

Category: Journey
Origin: PO

---

## Feature: Scorer System

### Context
兩種 scorer：programmatic（Python function）和 LLM-as-judge（`autoevals.LLMClassifier` + Mustache rubric template）。統一簽名 `(output, expected, *, input) → Score(name, score)`，對齊 autoevals convention，score 範圍 0~1。

### Rule: Programmatic scorer 透過 Python dotpath 解析，且在 task 執行前完成驗證

#### S-scr-01: Programmatic scorer 正確評分
> 驗證 dotpath 解析和 scorer 執行的 happy path

- **Given** config 設定 scorer `function: scorers.language.cjk_ratio`
- **And** agent 回覆 "微軟（MSFT）最新消息如下：..."（CJK ratio 0.45），expected CJK min 0.20
- **When** scorer 執行
- **Then** 回傳 `{"name": "cjk_ratio", "score": 1.0}`（pass — 0.45 >= 0.20）

Category: Illustrative
Origin: PO

#### S-scr-02: 無法解析的 scorer dotpath → 在任何 row 執行前報錯
> 驗證 fail-fast：不浪費計算資源

- **Given** config 設定 `function: scorers.nonexistent.my_scorer`，該 module 不存在
- **When** runner 解析 scorers
- **Then** 在任何 task function 呼叫前，顯示錯誤指出 module 找不到

Category: Illustrative
Origin: Dev

### Rule: LLM-judge scorer 使用 rubric template 並插值 per-case 變數

#### S-scr-03: Rubric template 正確插值 expected 欄位
> 驗證 Mustache `{{expected.field}}` 變數被正確替換

- **Given** rubric template: `"Does the output mention {{expected.must_mention}}? Input was: {{input}}"`
- **And** test case 的 `expected.must_mention = "revenue growth"`，`input = "Tell me about AAPL"`
- **When** LLM-judge scorer（`autoevals.LLMClassifier`）執行
- **Then** 送給 LLM 的 rubric 是 `"Does the output mention revenue growth? Input was: Tell me about AAPL"`

Category: Illustrative
Origin: Multiple

#### S-scr-04: Rubric 引用不存在的 expected 欄位 → 錯誤
> 驗證 template 變數驗證

- **Given** rubric 包含 `{{expected.nonexistent_field}}`，但 test case 的 expected 沒有此欄位
- **When** scorer 嘗試插值
- **Then** 顯示錯誤指出插值變數無法解析

Category: Illustrative
Origin: Multiple

#### S-scr-05: 空白的 expected 欄位在 rubric 中被清楚處理
> 驗證空白值不會產生無意義的 rubric

- **Given** rubric 是 `"Response must mention {{expected.must_mention}}"`
- **And** 該 row 的 `must_mention` cell 為空白（`None`）
- **When** scorer 嘗試插值
- **Then** 顯示警告或錯誤指出 `expected.must_mention` 為空，而非產出 `"Response must mention None"`

Category: Illustrative
Origin: QA

### Rule: Scorer 拋例外時，標記 error 並繼續其他 scorer

#### S-scr-06: 一個 scorer 失敗，其他 scorer 仍然執行
> 驗證 scorer failure isolation

- **Given** 一個 scenario 有 3 個 scorers，其中 scorer #2 拋出 `RuntimeError`
- **When** runner 處理某一 row
- **Then** scorer #1 和 #3 正常產出分數，scorer #2 在 result CSV 標記為 `ERROR`
- **And** terminal 輸出清楚指出哪個 scorer 在哪一 row 失敗

Category: Illustrative
Origin: QA

#### S-scr-07: Error 狀態與 score 0.0 可區分
> 驗證使用者不會把 scorer crash 誤判為 output 完全失敗

- **Given** Row A 的 scorer 正常回傳 `score: 0.0`（output 完全不符）
- **And** Row B 的 scorer 拋出 exception
- **When** 使用者檢視 result CSV
- **Then** Row A 顯示 `score_factuality: 0.0`，Row B 顯示 `score_factuality: ERROR`

Category: Illustrative
Origin: Multiple

### Rule: Scorer 名稱必須唯一

#### S-scr-08: 重複的 scorer name → config 載入時報錯
> 驗證 result CSV 和 Braintrust 不會因欄位名衝突而損失資料

- **Given** config 定義兩個 scorers 都命名為 `"accuracy"`
- **When** runner 載入 config
- **Then** 顯示 validation error 指出重複的 scorer name

Category: Illustrative
Origin: QA

---

### Journey Scenarios

#### J-scr-01: 混合 programmatic 和 LLM-judge scorers 的完整流程
> 驗證 language_policy scenario 中 programmatic 和 LLM-judge scorer 共存並各自正確評分

- **Given** `language_policy` config 設定 3 個 scorers：programmatic `tool_arg_no_cjk` + programmatic `response_language` + LLM-judge `response_relevance`（rubric 檢查回覆是否只討論 `{{expected.ticker}}` 相關資訊）
- **And** CSV 有 8 筆 test cases，含 `ticker` 欄位（如 MSFT, AAPL）
- **When** 執行 `python -m evals.runner language_policy --local-only`
- **Then** 每一 row 都被 3 個 scorers 評分
- **And** result CSV 有欄位 `score_tool_arg_no_cjk, score_response_language, score_response_relevance`
- **And** `response_relevance` 的分數來自真實 LLM 呼叫（非 mock）

Category: Journey
Origin: Dev

---

## Feature: Eval Runner CLI

### Context
CLI 是使用者與 eval 系統的主要互動介面，支援單一 scenario、全部執行、local-only 模式、自訂輸出目錄、per-case timeout。

### Rule: Task function 只接收 `input` 參數（v1 為 string）

#### S-run-01: Task function 以 input string 呼叫並取得 output
> 驗證 task function 簽名

- **Given** config 設定 `task.function: tasks.run_agent`，CSV mapping 產出 `input: "What is AAPL's revenue?"`
- **When** runner 執行此 test case
- **Then** `tasks.run_agent` 被呼叫並接收 string `"What is AAPL's revenue?"`，回傳 output

Category: Illustrative
Origin: Dev

### Rule: YAML config 必須通過 schema 驗證

#### S-run-02: config 缺少 `task.function` → 在執行前報錯
> 驗證 required field 驗證

- **Given** `eval_spec.yaml` 有 `name` 和 `column_mapping` 但缺少 `task.function`
- **When** runner 載入此 scenario
- **Then** 顯示 validation error 指出 `task.function` 是必填欄位

Category: Illustrative
Origin: Dev

#### S-run-03: config YAML 語法錯誤 → 清楚報錯
> 驗證 YAML parse 失敗不會產生 raw traceback

- **Given** `eval_spec.yaml` 包含無效的 YAML（如 tab/space 混用）
- **When** runner 載入此 scenario
- **Then** 顯示 YAML parse error 並指出 scenario 名稱和檔案路徑

Category: Illustrative
Origin: Multiple

### Rule: `--all` 執行所有合法 scenario，失敗的 scenario 不阻擋後續執行

#### S-run-04: 混合成功與失敗時，成功的仍然執行
> 驗證 batch 模式的韌性

- **Given** `scenarios/` 有 3 個子目錄：`alpha/`（合法）、`beta/`（scorer dotpath 錯誤）、`gamma/`（合法）
- **When** 執行 `python -m evals.runner --all`
- **Then** `alpha` 和 `gamma` 成功執行並產出 result CSV
- **And** `beta` 的錯誤被記錄，最後顯示 summary：2 succeeded, 1 failed

Category: Illustrative
Origin: Multiple

### Rule: `--local-only` 代表零 Braintrust 依賴

#### S-run-05: `--local-only` 不需要 API key 也能執行
> 驗證 local 開發不依賴 Braintrust

- **Given** `BRAINTRUST_API_KEY` 未設定
- **When** 執行 `python -m evals.runner language_policy --local-only`
- **Then** eval 成功完成並產出 result CSV，無任何 Braintrust 相關錯誤

Category: Illustrative
Origin: QA

### Rule: `--output-dir` 自動建立不存在的目錄

#### S-run-06: 指定不存在的 output 目錄 → 自動建立
> 驗證首次使用者不會遇到 FileNotFoundError

- **Given** `./custom_results/` 目錄尚未存在
- **When** 執行 `python -m evals.runner language_policy --output-dir ./custom_results`
- **Then** 自動建立 `./custom_results/` 並寫入 result CSV

Category: Illustrative
Origin: QA

### Rule: Task function 回傳 None → 清楚報錯

#### S-run-07: Task function 缺少 return → 不產出假 score
> 驗證 Python 常見的遺漏 return 問題不會產生垃圾分數

- **Given** `task.function` 指向一個忘記寫 `return` 的 function（回傳 `None`）
- **When** runner 執行此 test case
- **Then** 顯示錯誤指出 task function 回傳了 `None`，而非將 `None` 傳給 scorer

Category: Illustrative
Origin: QA

### Rule: Row-level task 失敗 → 錯誤標記，繼續處理後續 rows

#### S-run-08: 部分 row 失敗時，result CSV 標記失敗行
> 驗證 partial failure 不會產生看似完整但實際缺少 row 的 result

- **Given** scenario 有 8 rows，task function 在 row 6 拋出 `TimeoutError`
- **When** runner 執行此 scenario
- **Then** result CSV 包含全部 8 rows：rows 1-5, 7-8 有正常 output 和 scores，row 6 的 output 和 score 欄位標記為 `ERROR`
- **And** terminal 顯示 "7/8 cases succeeded, 1 failed"

Category: Illustrative
Origin: Multiple

### Rule: 可設定的 per-case timeout 防止無限掛起

#### S-run-09: Task function 超時 → 該 case 標記 error，繼續後續
> 驗證 hung agent 不會阻擋整個 eval run

- **Given** config 設定 `task.timeout: 120`（秒）
- **And** task function 在某一 row 呼叫的 agent 進入無限推理迴圈
- **When** 120 秒後 timeout 觸發
- **Then** 該 row 標記為 `TIMEOUT` error，runner 繼續處理下一個 row

Category: Illustrative
Origin: Multiple

---

### Journey Scenarios

#### J-run-01: 單一 scenario 端到端執行（happy path）
> 驗證從 discovery 到 result CSV 的完整 data flow

- **Given** `scenarios/language_policy/eval_spec.yaml` 設定 task function、column mapping、1 個 scorer
- **And** `dataset.csv` 含 3 筆 test cases：`prompt="What is AAPL's revenue?", ideal_answer="Apple's revenue is..."`
- **When** 執行 `python -m evals.runner language_policy --local-only`
- **Then** runner 發現 scenario → 載入 config → 驗證 scorers → 解析 CSV → 驗證 mapping → 呼叫 task function → 執行 scorer → 寫入 result CSV
- **And** result CSV 含所有原始欄位 + `output.*` 欄位 + `score_*` 欄位

Category: Journey
Origin: Dev

---

## Feature: Result CSV Output

### Context
每次 eval 產出一個 result CSV，包含所有原始 CSV 欄位 + output 欄位 + per-scorer 分數。檔案使用 timestamp 命名，永遠不覆蓋。

### Rule: Result CSV 包含所有原始欄位 + `output.*` + `score_*`

#### S-res-01: Result CSV 結構正確
> 驗證 output 的欄位組成

- **Given** scenario CSV 有欄位 `prompt, ideal_answer, notes`（`notes` 未 mapped），scorers 為 `factuality, completeness`
- **And** task function 回傳 `{"response": "...", "model": "gpt-4"}`
- **When** eval 完成
- **Then** result CSV 有欄位：`prompt, ideal_answer, notes, output.response, output.model, score_factuality, score_completeness`

Category: Illustrative
Origin: Multiple

### Rule: Result CSV 使用 `{scenario}_{timestamp}.csv` 命名，永不覆蓋

#### S-res-02: 兩次執行產出不同的 result 檔案
> 驗證 never-overwrite 保證

- **Given** 已執行 `language_policy` 一次，`results/` 中有一個 result CSV
- **When** 再次執行
- **Then** 產出新的 result CSV，原本的檔案不變

Category: Illustrative
Origin: Multiple

### Rule: Result CSV 使用原始 CSV 欄位名稱

#### S-res-03: 欄位名是原始 CSV header，非 dotpath
> 驗證 result 可與 input CSV side-by-side 比對

- **Given** input CSV 有欄位 `prompt, ideal_answer`，mapping 為 `prompt: input, ideal_answer: expected.answer`
- **When** eval 完成
- **Then** result CSV 欄位名為 `prompt, ideal_answer`（非 `input, expected.answer`）

Category: Illustrative
Origin: Dev

### Rule: Output 正確 CSV escape

#### S-res-04: Output 含逗號和換行時正確 escape
> 驗證 LLM output 不會損壞 result CSV

- **Given** task function 回傳含逗號和換行的文字：`"First, we note\nthat revenue is $25.5B"`
- **When** result CSV 被寫入
- **Then** 該欄位被正確 CSV escape，標準 CSV parser 和 Google Sheets 可正確讀取

Category: Illustrative
Origin: QA

### Rule: 原始 CSV 欄位名與生成欄位名衝突時有處理

#### S-res-05: Input CSV 有欄位名 `output` → 衝突處理
> 驗證使用者自定義欄位不會被覆蓋

- **Given** `dataset.csv` 有欄位 `prompt, output, ideal_answer`（使用者用 `output` 存預期輸出格式）
- **When** eval 完成，runner 產出 result CSV
- **Then** result CSV 能區分原始 `output` 欄位和生成的 `output.*` 欄位（如加前綴或重新命名原始欄位）

Category: Illustrative
Origin: QA

### Rule: `results/` 目錄路徑是確定的（相對於 evals 模組）

#### S-res-06: 從不同 working directory 執行，results 位置一致
> 驗證使用者不會找不到 result CSV

- **Given** 使用者從 repo root 執行 `python -m evals.runner language_policy`
- **And** 另一次從 `backend/` 目錄執行相同指令
- **When** 兩次 eval 都完成
- **Then** 兩次的 result CSV 都出現在相同的目錄（如 `backend/evals/results/`）

Category: Illustrative
Origin: QA

---

### Journey Scenarios

#### J-res-01: Config 變更前後的 result CSV 共存
> 驗證 schema 演化不會破壞歷史結果

- **Given** 先以 2 個 scorers 執行 eval，產出 result CSV A（2 個 score 欄位）
- **When** 修改 config 新增第 3 個 scorer 後再次執行
- **Then** 產出 result CSV B（3 個 score 欄位）
- **And** result CSV A 保持不變，兩個檔案都可在 Google Sheets 中開啟

Category: Journey
Origin: QA

---

## Feature: Braintrust Integration

### Context
Eval 結果預設上傳至 Braintrust 進行實驗追蹤與比較。`--local-only` 可停用。Langfuse 在 eval 時同時作為 tracing 工具存在，但其失敗不應阻擋 eval 執行。

### Rule: 預設上傳 Braintrust，`--local-only` 停用

#### S-bt-01: 預設模式同時產出 local CSV 和 Braintrust experiment
> 驗證 dual output

- **Given** `BRAINTRUST_API_KEY` 已設定，project "finlab-x" 存在
- **When** 執行 `python -m evals.runner language_policy`
- **Then** terminal 輸出 Braintrust experiment URL
- **And** 同時在 `results/` 產出 result CSV

Category: Illustrative
Origin: Dev

### Rule: 缺少 API key 且非 local-only → 在執行前報錯

#### S-bt-02: 缺少 API key 時 fail fast
> 驗證不浪費計算資源

- **Given** `BRAINTRUST_API_KEY` 未設定，且未指定 `--local-only`
- **When** 執行 `python -m evals.runner language_policy`
- **Then** 在任何 task 執行前，顯示錯誤要求設定 API key 或使用 `--local-only`

Category: Illustrative
Origin: Multiple

### Rule: `--local-only` 不 import braintrust 模組

#### S-bt-03: `--local-only` 不觸發任何 Braintrust SDK 行為
> 驗證 local-only 模式的完全隔離

- **Given** `BRAINTRUST_API_KEY` 未設定
- **When** 執行 `python -m evals.runner language_policy --local-only`
- **Then** eval 成功；不呼叫 `set_global_handler()`；braintrust module 未被 import

Category: Illustrative
Origin: Dev

### Rule: Langfuse 失敗不阻擋 eval 執行

#### S-bt-04: Langfuse 不可用時 eval 仍然完成
> 驗證 tracing 是 nice-to-have，不是 eval 的前提

- **Given** `LANGFUSE_SECRET_KEY` 未設定或已過期
- **When** 執行 `python -m evals.runner language_policy`
- **Then** eval 正常執行並產出 result CSV 和 Braintrust experiment
- **And** 顯示警告指出 Langfuse tracing 不可用

Category: Illustrative
Origin: Multiple

### Rule: Result CSV 在 Braintrust upload 之前寫入

#### S-bt-05: Braintrust upload 失敗不影響本地結果
> 驗證 local results 的韌性

- **Given** Braintrust API 無法連線（網路錯誤）
- **When** eval 完成所有 scoring
- **Then** result CSV 仍然正常寫入 `results/`
- **And** 錯誤訊息指出 Braintrust 上傳失敗

Category: Illustrative
Origin: Multiple

### Rule: `--all` 模式下每個 scenario 產生獨立的 Braintrust experiment

#### S-bt-06: --all 不會造成 experiment 之間的 trace 汙染
> 驗證 global handler 在 scenario 之間正確重設

- **Given** `--all` 發現 `language_policy` 和 `response_quality` 兩個 scenario
- **When** 依序執行兩個 scenario
- **Then** Braintrust 上出現兩個獨立的 experiments，各自只包含自己 scenario 的 test cases

Category: Illustrative
Origin: QA

### Rule: Scorer 的 LLM 呼叫不應汙染 experiment trace

#### S-bt-07: LLM-judge 的 LLM 呼叫不出現在 task trace 中
> 驗證 Braintrust trace drill-down 只顯示 agent 行為

- **Given** scenario 使用 LLM-judge scorer，scorer 內部呼叫 LLM 進行評分
- **When** eval 完成，使用者在 Braintrust UI drill-down 某個 test case 的 trace
- **Then** trace 只顯示 task function（agent）的 LLM calls 和 tool calls，不包含 scorer 的 LLM call

Category: Illustrative
Origin: Dev

### Rule: Config 支援 experiment metadata

#### S-bt-08: Experiment metadata 附加到 Braintrust experiment
> 驗證使用者可以搜尋和篩選 experiments

- **Given** config 包含 metadata：`experiment: { model: "gpt-4o", prompt_version: "v3-cot" }`
- **When** 執行 eval
- **Then** Braintrust experiment 附帶此 metadata，可在 UI 中用於搜尋和篩選

Category: Illustrative
Origin: Multiple

---

### Journey Scenarios

#### J-bt-01: Prompt 迭代工作流程（修改 → 執行 → 比較 → 重複）
> 驗證 Braintrust 實驗比較的核心使用情境，含 programmatic + LLM-judge 混合 scores

- **Given** 已執行 `language_policy` eval 一次，Braintrust experiment 顯示 3 個 scorer 的平均分數（`tool_arg_no_cjk`, `response_language`, `response_relevance`）
- **When** 修改 agent 的 system prompt 以改善中文回覆品質
- **And** 再次執行 `python -m evals.runner language_policy`
- **Then** 新的 Braintrust experiment 顯示更新的分數（含 LLM-judge `response_relevance`）
- **And** 在 Braintrust UI 比較兩個 experiments 時，可以看到 per-case 的 regression 和 improvement（包含 LLM-judge score 的變化）
- **And** 可以 drill-down 到退步的 test case，查看完整 trace（input → tool calls → output）

Category: Journey
Origin: PO

#### J-bt-02: 多 scenario batch evaluation
> 驗證系統可擴展到多個 eval scenario

- **Given** 專案有 `language_policy`（8 cases）和 `response_quality`（15 cases）兩個 scenario
- **When** 執行 `python -m evals.runner --all`
- **Then** 兩個 scenario 都成功執行
- **And** 各自產出 result CSV 和 Braintrust experiment
- **And** 最後顯示 summary：2 scenarios succeeded

Category: Journey
Origin: PO

---

## Feature: Cross-Feature Behavior

### Context
跨功能的行為保證，確保系統在非正常情境下的韌性和資料完整性。

### Rule: Ctrl+C 中斷不損壞資料

#### S-xf-01: 中途中斷保留已完成的 partial results
> 驗證使用者中斷不會導致資料遺失

- **Given** eval 正在處理 row 25 of 100
- **When** 使用者按下 Ctrl+C
- **Then** 已完成的 rows（1-24）的 result CSV 被安全寫入（或明確告知未保存）
- **And** 不會留下損壞的半寫 CSV 檔案

Category: Illustrative
Origin: QA

### Rule: End-to-end 資料完整性

#### S-xf-02: 含特殊字元的值通過完整 pipeline 不變
> 驗證從 CSV 到 result CSV 的 round-trip 資料完整性

- **Given** CSV 有一個 cell 值為 `"Tesla's revenue was $25.5B, up 15%\nKey highlights:\n- EPS: $1.85"`
- **When** 此值通過 CSV parsing → column mapping → task function input → result CSV output
- **Then** result CSV 中的原始欄位值完整保留（含逗號、換行、引號）

Category: Illustrative
Origin: QA
