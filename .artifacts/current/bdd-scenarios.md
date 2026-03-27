# BDD Scenarios

## Meta
- Design Reference: `.artifacts/current/design.md`
- Generated: 2026-03-27
- Discovery Method: Three Amigos (Agent Teams — PO, Dev, QA)
- User Decisions: D1(a) scorer failure isolation, D2(a) partial batch, D3(a) score range error, D4(a) task receives input only, D5(a) headers-only CSV is error

---

## Feature: Scenario Discovery

### Context
Runner 掃描 `scenarios/` 目錄，每個包含 `dataset.csv` + `config.yaml` 的子目錄即為一個可執行的 scenario。不需要 registry 檔案。

### Rule: 合法 scenario 必須包含 `dataset.csv` 和 `config.yaml`

#### S-disc-01: 完整目錄結構被正確發現
> 驗證 convention-based discovery 的 happy path

- **Given** `scenarios/language_policy/` 包含 `dataset.csv`（含 8 筆 test cases）和 `config.yaml`
- **When** 執行 `python -m evals.runner language_policy`
- **Then** scenario 被發現並執行，產出 result CSV

Category: Illustrative
Origin: Multiple

#### S-disc-02: 缺少檔案的目錄被跳過並警告
> 驗證不完整的 scenario 目錄不會中斷其他 scenario

- **Given** `scenarios/broken/` 只包含 `config.yaml`，缺少 `dataset.csv`
- **When** 執行 `python -m evals.runner --all`
- **Then** `broken` 被跳過並顯示警告，其他合法 scenario 正常執行

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

- **Given** `scenarios/` 目錄存在但為空
- **When** 執行 `python -m evals.runner --all`
- **Then** 顯示 "no scenarios found" 訊息

Category: Illustrative
Origin: QA

### Rule: `--all` 執行所有合法 scenario，跳過失敗的

#### S-disc-05: 混合合法與不合法時，合法的仍然執行
> 驗證一個壞 scenario 不會擋住整個 batch

- **Given** `scenarios/` 有 3 個子目錄：`alpha/`（合法）、`beta/`（合法）、`broken/`（缺 CSV）
- **When** 執行 `python -m evals.runner --all`
- **Then** `alpha` 和 `beta` 成功執行並產出 result CSV，`broken` 被跳過，最後顯示 summary：2 succeeded, 1 skipped

Category: Illustrative
Origin: Multiple

---

### Journey Scenarios

#### J-disc-01: 新手首次設定的錯誤恢復流程
> 驗證從零開始到成功執行的完整 progressive error recovery

- **Given** 一個新開發者，尚未建立 `scenarios/` 目錄
- **When** 她執行 `python -m evals.runner --all`，看到 "no scenarios found"
- **And** 建立 `scenarios/test1/` 只放了 `dataset.csv`，再跑一次，看到 "missing config.yaml"
- **And** 加入 `config.yaml` 但 `task.function` 打錯，再跑一次，看到 "cannot resolve task function"
- **And** 修正 dotpath 再跑一次
- **Then** eval 成功執行並產出 result CSV

Category: Journey
Origin: QA

---

## Feature: CSV Dataset 與 Column Mapping

### Context
CSV 是 test cases 的 source of truth，必須可在 Google Sheets 中編輯。YAML config 的 `column_mapping` 將人類友善的欄位名稱對應到 Braintrust 的 `{input, expected, metadata}` 結構。

### Rule: column_mapping 正確轉換 CSV rows 為 `{input, expected, metadata}`

#### S-csv-01: 單一欄位對應到 input string
> 驗證最簡單的 mapping 模式

- **Given** `column_mapping` 設定 `prompt: input`
- **And** CSV 有一筆 `prompt="What is AAPL's P/E ratio?"`
- **When** runner 轉換這一 row
- **Then** 產出 `{input: "What is AAPL's P/E ratio?", expected: {}, metadata: {}}`

Category: Illustrative
Origin: Dev

#### S-csv-02: 多欄位對應到巢狀結構
> 驗證 dotpath notation 正確組裝 nested objects

- **Given** `column_mapping` 設定 `prompt: input.question`, `category: input.category`, `ideal_answer: expected.answer`, `difficulty: metadata.difficulty`
- **And** CSV row: `prompt="Revenue trend?", category="financials", ideal_answer="Growing 15% YoY", difficulty="medium"`
- **When** runner 轉換這一 row
- **Then** 產出 `{input: {question: "Revenue trend?", category: "financials"}, expected: {answer: "Growing 15% YoY"}, metadata: {difficulty: "medium"}}`

Category: Illustrative
Origin: Dev

#### S-csv-03: 未映射的額外欄位被忽略
> 驗證 column_mapping 是 whitelist，不是 exact match

- **Given** CSV 有欄位 `prompt, ideal_answer, notes`，但 mapping 只定義 `prompt` 和 `ideal_answer`
- **When** runner 轉換 rows
- **Then** `notes` 欄位不出現在 input、expected 或 metadata 中，eval 正常執行

Category: Illustrative
Origin: Multiple

### Rule: mapping 引用的欄位必須存在於 CSV 中

#### S-csv-04: mapping 引用不存在的 CSV 欄位 → 錯誤
> 驗證 upfront validation 防止跑到一半才 crash

- **Given** `column_mapping` 引用 `question: input`，但 CSV 只有 `prompt, ideal_answer`（沒有 `question`）
- **When** runner 載入此 scenario
- **Then** 在任何 task 執行前，顯示錯誤指出 `question` 欄位不存在於 CSV

Category: Illustrative
Origin: Multiple

### Rule: CSV 必須正確處理 UTF-8 和特殊字元

#### S-csv-05: CJK 內容端到端保持正確
> 驗證中日韓文字在整個 pipeline 中不會損壞

- **Given** CSV 包含 prompt `"請問台灣的首都在哪裡？"` 和 expected answer 含中文字元
- **When** runner 執行 eval
- **Then** CJK 內容正確傳入 task function、正確寫入 result CSV，無 mojibake

Category: Illustrative
Origin: QA

#### S-csv-06: CSV 內含逗號、換行、引號的欄位值正確解析
> 驗證 RFC 4180 合規的 CSV parsing

- **Given** CSV 有一個 cell 值為 `"He said, ""hello""\nand left"`
- **When** runner 解析此 CSV
- **Then** 該值被正確解析為單一欄位，並在 result CSV 中正確輸出

Category: Illustrative
Origin: QA

### Rule: 空 CSV 或只有 header 的 CSV 是錯誤

#### S-csv-07: 只有 header 沒有 data rows 的 CSV → 錯誤
> 驗證使用者不會在不知情下跑了一個空的 eval

- **Given** `dataset.csv` 只包含 header row，沒有 data rows
- **When** runner 載入此 scenario
- **Then** 顯示錯誤 "no data rows found"

Category: Illustrative
Origin: QA

---

### Journey Scenarios

#### J-csv-01: 從 Google Sheets 編輯到執行 eval 的完整流程
> 驗證 CSV 作為 source of truth 的核心 value proposition

- **Given** 開發者將 8 筆 language policy test cases 從舊的 Python dataclass 遷移到 CSV：
  `prompt, ideal_answer, prompt_language, expect_tool, expect_cjk_min`（含中英文混合內容）
- **And** 建立對應的 `config.yaml` 定義 column mapping 和 2 個 scorers
- **When** 執行 `python -m evals.runner language_policy --local-only`
- **Then** 8 筆 test cases 全部執行，result CSV 產出於 `results/` 目錄
- **And** result CSV 可在 Google Sheets 中開啟，CJK 內容正確顯示

Category: Journey
Origin: PO

---

## Feature: Scorer System

### Context
兩種 scorer：programmatic（Python function）和 LLM-as-judge（rubric template）。統一簽名 `(input, output, expected) → {"name", "score"}`，score 範圍 0~1。

### Rule: Programmatic scorer 透過 Python dotpath 解析並執行

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
> 驗證 `{expected.field}` 變數被正確替換

- **Given** rubric template: `"Does the output mention {expected.must_mention}? Input was: {input}"`
- **And** test case 的 `expected.must_mention = "revenue growth"`，`input = "Tell me about AAPL"`
- **When** LLM-judge scorer 執行
- **Then** 送給 LLM 的 rubric 是 `"Does the output mention revenue growth? Input was: Tell me about AAPL"`

Category: Illustrative
Origin: Multiple

#### S-scr-04: Rubric 引用不存在的 expected 欄位 → 錯誤
> 驗證 template 變數驗證

- **Given** rubric 包含 `{expected.nonexistent_field}`，但 test case 的 expected 沒有此欄位
- **When** scorer 嘗試插值
- **Then** 顯示錯誤指出插值變數無法解析

Category: Illustrative
Origin: Multiple

### Rule: Score 必須在 [0, 1] 範圍內，否則報錯

#### S-scr-05: Score 超出 0~1 → 報錯
> 驗證 scorer 的 bug 會被抓出來

- **Given** 一個 scorer 回傳 `{"name": "test", "score": 1.5}`
- **When** runner 收到此結果
- **Then** 顯示 validation error：score 1.5 超出 [0, 1] 範圍

Category: Illustrative
Origin: QA

### Rule: Scorer 拋例外時，標記 error 並繼續其他 scorer

#### S-scr-06: 一個 scorer 失敗，其他 scorer 仍然執行
> 驗證 scorer failure isolation（使用者決策 D1）

- **Given** 一個 scenario 有 3 個 scorers，其中 scorer #2 拋出 `RuntimeError`
- **When** runner 處理某一 row
- **Then** scorer #1 和 #3 正常產出分數，scorer #2 在 result CSV 標記為 error
- **And** terminal 輸出清楚指出哪個 scorer 在哪一 row 失敗

Category: Illustrative
Origin: QA

---

### Journey Scenarios

#### J-scr-01: 混合 programmatic 和 LLM-judge scorers 的完整流程
> 驗證兩種 scorer 類型在同一 scenario 中共存

- **Given** config 設定 2 個 scorers：programmatic `cjk_ratio` + LLM-judge `completeness`（rubric: "Does the output mention {expected.must_mention}?"）
- **And** CSV 有 2 筆 test cases，含 `prompt, must_mention, category` 欄位
- **When** 執行 `python -m evals.runner response_quality --local-only`
- **Then** 每一 row 都被兩個 scorers 評分
- **And** result CSV 有欄位 `prompt, must_mention, category, output, score_cjk_ratio, score_completeness`

Category: Journey
Origin: Dev

---

## Feature: Eval Runner CLI

### Context
CLI 是使用者與 eval 系統的主要互動介面，支援單一 scenario、全部執行、local-only 模式、自訂輸出目錄。

### Rule: Task function 只接收 `input` 參數

#### S-run-01: Task function 以 input 呼叫並取得 output
> 驗證 task function 簽名（使用者決策 D4）

- **Given** config 設定 `task.function: tasks.run_agent`，CSV mapping 產出 `input: "What is AAPL's revenue?"`
- **When** runner 執行此 test case
- **Then** `tasks.run_agent` 被呼叫並只接收 `input` 值，回傳 output string

Category: Illustrative
Origin: Dev

### Rule: YAML config 必須通過 schema 驗證

#### S-run-02: config 缺少 `task.function` → 在執行前報錯
> 驗證 required field 驗證

- **Given** `config.yaml` 有 `name` 和 `column_mapping` 但缺少 `task.function`
- **When** runner 載入此 scenario
- **Then** 顯示 validation error 指出 `task.function` 是必填欄位

Category: Illustrative
Origin: Dev

#### S-run-03: config YAML 語法錯誤 → 清楚報錯
> 驗證 YAML parse 失敗不會產生 raw traceback

- **Given** `config.yaml` 包含無效的 YAML（如未關閉的引號）
- **When** runner 載入此 scenario
- **Then** 顯示 YAML parse error 並指出 scenario 名稱和檔案路徑

Category: Illustrative
Origin: Multiple

---

### Journey Scenarios

#### J-run-01: 單一 scenario 端到端執行（happy path）
> 驗證從 discovery 到 result CSV 的完整 data flow

- **Given** `scenarios/language_policy/config.yaml` 設定 task function、column mapping、1 個 scorer
- **And** `dataset.csv` 含 1 筆 test case：`prompt="What is AAPL's revenue?", ideal_answer="Apple's revenue is..."`
- **When** 執行 `python -m evals.runner language_policy --local-only`
- **Then** runner 發現 scenario → 載入 config → 解析 CSV → 轉換 mapping → 呼叫 task function → 執行 scorer → 寫入 result CSV
- **And** result CSV 含欄位 `prompt, ideal_answer, output, score_cjk_ratio`

Category: Journey
Origin: Dev

---

## Feature: Result CSV Output

### Context
每次 eval 產出一個 result CSV，包含原始 input 欄位 + model output + per-scorer 分數。檔案使用 timestamp 命名，永遠不覆蓋。

### Rule: Result CSV 使用 `{scenario}_{timestamp}.csv` 命名，永不覆蓋

#### S-res-01: 兩次執行產出不同的 result 檔案
> 驗證 never-overwrite 保證

- **Given** 已執行 `language_policy` 一次，產出 `results/language_policy_20260327_1400.csv`
- **When** 在 14:30 再次執行
- **Then** 產出新檔案 `results/language_policy_20260327_1430.csv`
- **And** 原本的 `results/language_policy_20260327_1400.csv` 不變

Category: Illustrative
Origin: Multiple

### Rule: Result CSV 包含原始欄位 + output + per-scorer 分數

#### S-res-02: Result CSV 結構正確
> 驗證 output 的欄位組成

- **Given** scenario CSV 有欄位 `prompt, ideal_answer`，scorers 為 `factuality, completeness`
- **When** eval 完成
- **Then** result CSV 有欄位：`prompt, ideal_answer, output, score_factuality, score_completeness`
- **And** score 值介於 0.0 和 1.0

Category: Illustrative
Origin: PO

#### S-res-03: Output 含逗號和換行時正確 CSV escape
> 驗證 result CSV 不會因為特殊字元而損壞

- **Given** task function 回傳含逗號和換行的文字：`"First, we note\nthat this is multi-line"`
- **When** result CSV 被寫入
- **Then** 該欄位被正確 CSV escape（加引號），標準 CSV parser 可正確讀取

Category: Illustrative
Origin: QA

### Rule: 輸出目錄自動建立

#### S-res-04: `results/` 不存在時自動建立
> 驗證首次使用者不會遇到 FileNotFoundError

- **Given** `results/` 目錄尚未存在
- **When** runner 執行完 eval
- **Then** 自動建立 `results/` 並寫入 result CSV

Category: Illustrative
Origin: Multiple

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
Eval 結果預設上傳至 Braintrust 進行實驗追蹤與比較。`--local-only` 可停用上傳。所有計算在本機完成，Braintrust 只做儲存與視覺化。

### Rule: 預設上傳 Braintrust，`--local-only` 停用

#### S-bt-01: 預設模式同時產出 local CSV 和 Braintrust experiment
> 驗證 dual output

- **Given** `BRAINTRUST_API_KEY` 已設定，project "finlab-x" 存在
- **When** 執行 `python -m evals.runner language_policy`
- **Then** terminal 輸出 Braintrust experiment URL
- **And** 同時在 `results/` 產出 result CSV

Category: Illustrative
Origin: Dev

#### S-bt-02: `--local-only` 不需要 API key 也能執行
> 驗證 local 開發不依賴 Braintrust

- **Given** `BRAINTRUST_API_KEY` 未設定
- **When** 執行 `python -m evals.runner language_policy --local-only`
- **Then** eval 成功完成並產出 result CSV

Category: Illustrative
Origin: QA

### Rule: 缺少 API key 且非 local-only → 在執行前報錯

#### S-bt-03: 缺少 API key 時 fail fast
> 驗證不浪費計算資源

- **Given** `BRAINTRUST_API_KEY` 未設定，且未指定 `--local-only`
- **When** 執行 `python -m evals.runner language_policy`
- **Then** 在任何 task 執行前，顯示錯誤要求設定 API key 或使用 `--local-only`

Category: Illustrative
Origin: Multiple

### Rule: Braintrust 上傳失敗時，local result CSV 仍然保留

#### S-bt-04: 網路失敗不影響本地結果
> 驗證 local results 的韌性

- **Given** Braintrust API 無法連線（網路錯誤）
- **When** eval 完成所有 scoring
- **Then** result CSV 仍然正常寫入 `results/`
- **And** 錯誤訊息指出 Braintrust 上傳失敗

Category: Illustrative
Origin: QA

---

### Journey Scenarios

#### J-bt-01: Prompt 迭代工作流程（修改 → 執行 → 比較 → 重複）
> 驗證 Braintrust 實驗比較的核心使用情境

- **Given** 已執行 `language_policy` eval 一次，Braintrust experiment 顯示平均分數 0.65
- **When** 修改 agent 的 system prompt 以改善中文回覆品質
- **And** 再次執行 `python -m evals.runner language_policy`
- **Then** 新的 Braintrust experiment 顯示平均分數 0.78
- **And** 在 Braintrust UI 比較兩個 experiments 時，可以看到 per-case 的 regression 和 improvement
- **And** 可以 drill-down 到退步的 test case，查看完整 trace（input → tool calls → output）

Category: Journey
Origin: PO

#### J-bt-02: 新增 eval 維度並跨版本追蹤
> 驗證系統可擴展到多個 eval scenario

- **Given** 專案從 v1 演進到 v2，需要新增 "response_quality" eval
- **When** 建立 `scenarios/response_quality/` 含 15 筆 test cases 和對應 config
- **And** 執行 `python -m evals.runner --all`
- **Then** `language_policy`（8 cases）和 `response_quality`（15 cases）都成功執行
- **And** Braintrust 上出現兩個 experiments，各自可獨立追蹤和比較

Category: Journey
Origin: PO
