# Design: CSV 驅動的 Evaluation 管理系統 + Braintrust 整合

## 概述

將 evaluation 系統從寫死的 Python dataclass 轉換為 CSV 驅動、人類可編輯的工作流程，並整合 Braintrust 進行實驗追蹤與比較。

### 目標

1. CSV 檔案作為 evaluation dataset 的 source of truth
2. 可在 Google Sheets 或任何 CSV 編輯器中編輯
3. 編輯後的 CSV 可直接用於執行 evaluation
4. 整合 Braintrust 進行實驗追蹤、版本比較、trace 檢視
5. 產出 result CSV 供本地標注使用

### 平台分工

| 平台           | 角色                                                             |
| -------------- | ---------------------------------------------------------------- |
| **Langfuse**   | Production tracing 與 observability（已整合）                    |
| **Braintrust** | Offline evaluation 實驗：執行、評分、實驗 diff、trace drill-down |

---

## 1. 元件職責

| 元件                 | 職責                                                                            | 格式           |
| -------------------- | ------------------------------------------------------------------------------- | -------------- |
| **Scenario Dataset** | 儲存 test cases（input / expected / metadata）                                  | CSV            |
| **Scenario Config**  | 定義 column mapping、scorer 清單、rubric templates、task function               | YAML           |
| **Scorer Registry**  | 可重用的 scoring functions（programmatic + LLM-as-judge）                       | Python modules |
| **Eval Runner**      | 掃描 scenarios → 讀取 CSV + config → 組裝 Braintrust `Eval()` → 輸出 result CSV | Python         |

```mermaid
graph TB
    Runner["Eval Runner<br/>(orchestrator)"]

    subgraph Scenarios["scenarios/"]
        CSV["dataset.csv<br/>test case data"]
        Config["config.yaml<br/>mapping + scorer refs"]
    end

    subgraph Scorers["scorers/"]
        Lang["language.py<br/>cjk_ratio, tool_match"]
        Judge["llm_judge.py<br/>通用 LLM-as-judge"]
    end

    Runner -->|discovers| Scenarios
    Runner -->|resolves scorers| Scorers

    Runner -->|輸出| ResultCSV["Result CSV<br/>(本地標注用)"]
    Runner -->|輸出| BT["Braintrust<br/>(experiment + traces)"]
```

### 發現機制（Convention-Based）

Runner 掃描 `scenarios/` 目錄，每個包含 `dataset.csv` + `config.yaml` 的子目錄 = 一個 scenario。不需要額外的 registry 檔案。

---

## 2. 介面定義

### Scenario Config (YAML) schema

```yaml
name: string                    # scenario 名稱，同時作為 Braintrust experiment name
csv: string                     # dataset 檔名（預設 dataset.csv）

task:
  function: string              # task function 的 Python dotpath，如 "tasks.run_agent"

column_mapping:
  <csv_column>: input           # 單一欄位 → input（string 型）
  <csv_column>: input.<field>   # 多欄位 → input object
  <csv_column>: expected.<field>
  <csv_column>: metadata.<field>

scorers:
  - name: string
    function: string            # Python dotpath，如 "scorers.language.cjk_ratio"

  - name: string
    type: llm_judge
    rubric: string              # prompt template，可用 {input}, {expected.field} 插值
```

### Scorer function 簽名

所有 scorer 統一簽名，對齊 Braintrust convention：

```
(input, output, expected) → {"name": str, "score": float}
```

- `name`：scorer 的顯示名稱，用於 Braintrust UI 和 result CSV 的欄位名（如 `score_factuality`）
- `score`：0~1 之間的浮點數，1 = 完全通過，0 = 完全失敗

### Eval Runner CLI 介面

```bash
python -m evals.runner <scenario_name>      # 跑單一 scenario
python -m evals.runner --all                # 跑全部 scenario
python -m evals.runner <name> --local-only  # 不送 Braintrust，只輸出 local result CSV
python -m evals.runner <name> --output-dir ./results
```

### Result CSV 結構

包含原始 input 欄位 + model output + 每個 scorer 的分數：

```
prompt, ideal_answer, output, score_factuality, score_completeness, score_overall
```

---

## 3. 資料流

```mermaid
graph TD
    subgraph Setup["1. SETUP"]
        Name["收到 scenario name"]
        ReadConfig["讀取 config.yaml"]
        ReadCSV["讀取 dataset.csv"]
        Transform["套用 column_mapping<br/>每一 row → {input, expected, metadata}"]
        Name --> ReadConfig --> ReadCSV --> Transform
    end

    subgraph Execution["2. EXECUTION（透過 Braintrust Eval()）"]
        Task["呼叫 task function（run agent）<br/>→ 取得 output"]
        Score["對每個 scorer 執行<br/>scorer(input, output, expected) → score"]
        Trace["Braintrust 自動捕捉<br/>執行過程中的 traces"]
        Task --> Score
        Task --> Trace
    end

    subgraph Output["3. OUTPUT"]
        CSV2["寫入 result CSV<br/>results/{name}_{timestamp}.csv"]
        BT["送至 Braintrust<br/>experiment + traces + scores"]
    end

    Transform --> Task
    Score --> CSV2
    Score --> BT
```

### 關鍵決策

| 決策                  | 選擇                                                        | 理由                                         |
| --------------------- | ----------------------------------------------------------- | -------------------------------------------- |
| Task function 來源    | config.yaml 指定 Python dotpath                             | 不同 scenario 可能測試不同的 agent 或 prompt |
| LLM-judge 的 LLM 呼叫 | 在 scorer 內部處理，runner 不管                             | 保持 scorer 介面統一                         |
| Result CSV 命名       | `{scenario}_{timestamp}.csv`                                | 每次執行都保留，不覆蓋，方便回溯標注         |
| Braintrust 開關       | `--local-only` flag                                         | 開發時可純 local，正式比較時送 Braintrust    |
| Trace 目的地          | Eval 的 trace 進 Braintrust；production trace 留在 Langfuse | 清楚區分 eval 與 production 情境             |
| Result CSV 預設路徑   | `results/`（相對於 evals 目錄），可用 `--output-dir` 覆寫    | 不指定時有合理預設，減少必填參數             |

---

## 4. Braintrust 整合

### Trace 捕捉設定

Braintrust 對 LangGraph 和 LlamaIndex 的 trace 捕捉並非零設定，需要少量整合程式碼（類似 Langfuse）：

| Framework | 整合方式 | 設定量 |
|-----------|---------|--------|
| **LangGraph** | `BraintrustCallbackHandler` 傳入 LangChain callback system | 約 2-3 行 |
| **LlamaIndex** | OpenTelemetry exporter 指向 Braintrust endpoint | 約 3-4 行 |

此整合程式碼寫在 task function 內部，由 implementation plan 階段具體定義。

### 整合範圍

| 項目           | 做法                                                        |
| -------------- | ----------------------------------------------------------- |
| **Eval 執行**  | 透過 Braintrust `Eval()` 執行，自動獲得 experiment tracking |
| **Trace 捕捉** | `Eval()` 執行 task 時自動記錄，可在 UI drill-down 檢視      |
| **實驗比較**   | 每次 eval run 產生一個 experiment，在 Braintrust UI 做 diff |
| **Scorers**    | 自訂 scorer + `autoevals` 內建 scorer 混合使用              |

### Runner 組裝 `Eval()` 的流程

所有計算都在本機完成。`python -m evals.runner` 會在本機執行 dataset 遍歷、task function 呼叫、scorer 計算，然後將結果**上傳**至 Braintrust platform 做儲存與視覺化。Braintrust 不會重新執行任何東西，它只是結果的呈現平台。

```mermaid
graph LR
    Config["讀取 scenario config"]
    Data["CSV → column_mapping<br/>→ [{input, expected, metadata}]"]
    TaskFn["config 指定的 task function<br/>（呼叫 agent）"]
    ScorerList["config 列出的 scorer list"]
    Prog["programmatic<br/>→ resolve Python dotpath"]
    LLM["llm_judge<br/>→ 從 rubric template 建立"]

    Config --> Data
    Config --> TaskFn
    Config --> ScorerList
    ScorerList --> Prog
    ScorerList --> LLM

    Data --> Eval["Eval(scenario_name,<br/>data, task, scores)"]
    TaskFn --> Eval
    Prog --> Eval
    LLM --> Eval

    Eval --> BT["Braintrust<br/>(experiment + traces)"]
    Eval --> ResultCSV["Result CSV<br/>(本地標注用)"]
```

### Braintrust 專案設定

```yaml
# 專案層級的 Braintrust 設定（一個檔案）
braintrust:
  project: "finlab-x"
  api_key_env: "BRAINTRUST_API_KEY"
  local_mode: false
```

### Prompt 迭代工作流程

```mermaid
graph TD
    A["1. 修改 prompt"] --> B["2. python -m evals.runner v1_response_quality"]
    B --> C["3. 打開 Braintrust UI<br/>看到新 experiment"]
    C --> D["4. 點 Compare<br/>跟上次 experiment diff"]
    D --> E["5. 檢視 per-case<br/>regression / improvement"]
    E --> F{"6. 改得好嗎？"}
    F -->|需要調整| A
    F -->|滿意| G["7. 確定此版本 prompt"]
```

---

## 5. 約束、取捨與範圍外

### 約束

| 約束                                                     | 影響                                              |
| -------------------------------------------------------- | ------------------------------------------------- |
| CSV 必須可在 Google Sheets 中編輯                        | 欄位值為 flat string / number，不能有 nested JSON |
| Braintrust `Eval()` 預期 `{input, expected, metadata}`   | column_mapping 必須能將 CSV 組裝成這三個 bucket   |
| Scorer 簽名固定為 `(input, output, expected) → score`    | 所有 scoring 邏輯（含 LLM-judge）都必須符合此介面 |
| Eval trace 進 Braintrust；production trace 留在 Langfuse | 依情境清楚分離平台                                |

### 取捨

| 取捨                            | 選擇                                      | 放棄                                                      |
| ------------------------------- | ----------------------------------------- | --------------------------------------------------------- |
| Convention over configuration   | 檔案結構即 registry，零註冊               | 明確的 registry 檔案                                      |
| YAML config 而非 Python wrapper | 新增 scenario 不需寫 Python               | 每個 scenario 的完全 Python 彈性（未來可加 escape hatch） |
| 使用 Braintrust 做 eval         | 強大的 experiment diff + trace drill-down | 需維護第二個平台帳號                                      |
| Result CSV 不覆蓋               | 每次執行都保留，方便標注回溯              | 磁碟空間（可定期清理）                                    |

### 範圍外（這次不做）

- Dataset 自動生成 pipeline
- CI 自動觸發 eval（先手動執行）
- Langfuse ↔ Braintrust 雙向同步
- Production online evaluation（先做 offline evaluation）

---

## 6. 測試策略

| 驗證目標                       | 方法                                                        | 類型             |
| ------------------------------ | ----------------------------------------------------------- | ---------------- |
| CSV 讀取 + column mapping 正確 | 給定 CSV + config → 驗證 `{input, expected, metadata}` 結構 | Unit test        |
| Scorer registry 解析           | config 裡的 dotpath 正確 resolve 到 Python function         | Unit test        |
| LLM-judge rubric 插值          | `{expected.must_mention}` 正確帶入 per-case 值              | Unit test        |
| Scenario discovery             | 正確結構的資料夾被找到，缺檔的會報錯                        | Unit test        |
| 端對端 eval 執行               | Mock task + 小 CSV，跑完整流程驗證 result CSV 輸出格式      | Integration test |
| Braintrust local 整合          | `local_mode=true` 跑 `Eval()`，驗證 scores 結構正確         | Integration test |
| **Braintrust platform 全流程** | **見下方 manual test checklist**                            | **Manual test**  |

### Manual Test: Braintrust Platform 全流程

**初始設定（一次性）：**

1. 前往 [braintrust.dev](https://www.braintrust.dev) 註冊帳號
2. 建立 project "finlab-x"
3. Settings → API Keys → 建立 API key
4. 設定環境變數 `export BRAINTRUST_API_KEY="sk-..."`（加到 `.env`）
5. `pip install braintrust autoevals`（加到 `pyproject.toml`）

**驗證流程：**

1. 執行 `python -m evals.runner language_policy` → terminal 輸出 Braintrust experiment URL
2. 打開 URL → 確認 experiment 出現在 Braintrust UI
3. 點進任一 test case → 確認能看到完整 trace（input / output / tool calls）
4. 確認每個 scorer 的分數獨立顯示
5. 修改 prompt 或參數，再跑一次 eval
6. 在 Braintrust UI 做 experiment diff → 看到 per-case regression / improvement
7. 確認 `results/` 目錄有產出 result CSV，內容正確
