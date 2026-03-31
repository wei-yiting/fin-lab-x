# Implementation Plan: CSV 驅動的 Evaluation 管理系統 + Braintrust 整合

> Design Reference: [`design.md`](./design.md)

**Goal:** 將 evaluation 系統從 Python dataclass 轉為 CSV 驅動的工作流程，整合 Braintrust 進行實驗追蹤與比較，並產出 result CSV 供本地標注。

**Architecture / Key Decisions:**

- 三層架構：CSV（dataset）/ YAML（config + mapping + scorers）/ Python（scorer 實作）
- Convention-based discovery：`scenarios/` 下每個包含 `eval_spec.yaml` 的子目錄 = 一個 scenario
- 所有 scorer 對齊 Braintrust `(input, output, expected) → {"name", "score"}` 簽名
- Task function 回傳完整 `OrchestratorResult` dict（含 `tool_outputs`），scorer 從中取所需欄位
- Braintrust tracing（`init_logger` + `set_global_handler`）在 eval runner entry point 設定，task function 不負責 tracing
- Runner 從一開始同時支援 `--local-only`（`no_send_logs=True`）和 platform 模式
- 現有 language policy pytest eval 保留不動，直到新系統完全驗證通過

**Tech Stack:** Python 3.10+, Braintrust SDK, braintrust-langchain, autoevals, PyYAML（已有）, csv（stdlib）, Pydantic（已有）

---

## Dependencies Verification

| Dependency | Version | Source | What Was Verified | Notes |
| --- | --- | --- | --- | --- |
| `braintrust` | latest | Context7 `/websites/braintrust_dev` | `Eval()` API：第一參數為 project name（str），`data`（list of dict），`task`（callable，接收 `input` 回傳 output），`scores`（list of scorer callable），`no_send_logs`（bool，`True` = 純本地不上傳），`experiment_name`（Optional[str]）。回傳 `result.results`（per-case，有 `.input`, `.output`, `.scores`）和 `result.summary` | Scorer 可回傳 `{"name": str, "score": float}` |
| `braintrust-langchain` | latest | Context7 `/websites/braintrust_dev` | `init_logger(project=..., api_key=...)` → `set_global_handler(BraintrustCallbackHandler())`。設定後 LangGraph/LangChain 的 `invoke()`/`ainvoke()` 自動被 Braintrust trace 捕捉（LLM calls, tool calls, node transitions）。只在 eval runner entry point 呼叫 | 安裝指令：`pip install braintrust-langchain` |
| `autoevals` | latest | Context7 `/braintrustdata/autoevals` | 提供 `Factuality`, `Levenshtein`, `EmbeddingSimilarity` 等內建 scorer | 本次只安裝，未來新 scenario 可混用自訂 + 內建 scorer |
| `pyyaml` | >=6.0.2 | pyproject.toml | 已在 dependencies 中 | 無需額外安裝 |

## Constraints

- 現有 `backend/evals/test_language_policy.py` pytest eval 不做任何修改，必須持續可執行
- CSV 欄位值為 flat string/number（Google Sheets 相容）
- `backend/agent_engine/` 不在修改範圍——task function 透過 import 呼叫現有 `Orchestrator`
- `backend/evals/results/` 需加入 `.gitignore`
- Eval runner process 中 Langfuse（per-request callback）和 Braintrust（global handler）共存，走不同 callback 路徑，互不衝突

---

## File Plan

| Operation | Path | Purpose |
| --- | --- | --- |
| Create | `backend/evals/scenario_config.py` | Scenario config Pydantic models + YAML / Braintrust config parser |
| Create | `backend/evals/dataset_loader.py` | CSV 讀取 + column mapping → `{input, expected, metadata}` 轉換 |
| Create | `backend/evals/scorer_registry.py` | Scorer dotpath 解析 + LLM-judge rubric builder |
| Create | `backend/evals/eval_runner.py` | CLI entry point + scenario discovery + `Eval()` 組裝 + result CSV 輸出 |
| Create | `backend/evals/eval_tasks.py` | Task functions：wrapping `Orchestrator.run()` |
| Create | `backend/evals/braintrust_config.yaml` | Braintrust 專案層級設定 |
| Create | `backend/evals/scenarios/language_policy/dataset.csv` | Language policy 8 筆 test cases（從 dataclass 遷移） |
| Create | `backend/evals/scenarios/language_policy/eval_spec.yaml` | Column mapping + scorer 清單 |
| Create | `backend/evals/scorers/__init__.py` | Package init |
| Create | `backend/evals/scorers/language_policy_scorer.py` | `tool_arg_no_cjk` + `response_language` scorers |
| Create | `backend/tests/evals/__init__.py` | Package init |
| Create | `backend/tests/evals/test_scenario_config.py` | Config parsing unit tests |
| Create | `backend/tests/evals/test_dataset_loader.py` | CSV loader unit tests |
| Create | `backend/tests/evals/test_scorer_registry.py` | Scorer registry unit tests |
| Create | `backend/tests/evals/test_eval_tasks.py` | Task function unit tests |
| Create | `backend/tests/evals/test_eval_runner.py` | Runner integration tests |
| Update | `pyproject.toml` | 新增 `braintrust`, `braintrust-langchain`, `autoevals` 到 dev dependencies |
| Update | `.gitignore` | 新增 `backend/evals/results/` |
| Update | `backend/evals/README.md` | 新增 Future Implementation 段落（LlamaIndex + Braintrust OTel） |
| Preserve | `backend/evals/test_language_policy.py` | 現有 pytest eval 不修改 |
| Preserve | `backend/evals/datasets/language_policy.py` | 現有 dataclass 不修改 |
| Preserve | `backend/evals/eval_helpers.py` | 新 scorer 會 import `contains_cjk`, `cjk_ratio` |

**Structure sketch:**

```text
backend/evals/
  braintrust_config.yaml          # Braintrust 專案設定
  scenario_config.py              # Pydantic models + YAML parser
  dataset_loader.py               # CSV 讀取 + column mapping
  scorer_registry.py              # Scorer dotpath 解析 + LLM-judge builder
  eval_runner.py                  # CLI entry point + Eval() 組裝
  eval_tasks.py                   # Task functions (wrapping Orchestrator)
  eval_helpers.py                 # (existing) CJK helpers
  conftest.py                     # (existing) pytest fixtures
  test_language_policy.py         # (existing) pytest eval — preserved
  datasets/
    language_policy.py            # (existing) frozen dataclass — preserved
  scenarios/
    language_policy/
      dataset.csv                 # 8 test cases
      eval_spec.yaml              # column mapping + scorer 定義
  scorers/
    __init__.py
    language_policy_scorer.py     # tool_arg_no_cjk, response_language
  results/                        # (gitignored) eval result CSVs
```

---

### Task 1: Dependencies + Base Config

**Files:**

- Update: `pyproject.toml`
- Update: `.gitignore`
- Create: `backend/evals/braintrust_config.yaml`
- Update: `backend/evals/README.md`

**What & Why:** 安裝 Braintrust SDK 和相關 packages，設定 gitignore 排除 result CSVs，建立 Braintrust 專案設定檔。所有後續 task 的前置條件。

**Implementation Notes:**

- `braintrust`、`braintrust-langchain`、`autoevals` 加到 `[project.optional-dependencies] dev` 區塊
- `backend/evals/results/` 加到 `.gitignore`
- README 新增 Future Implementation 段落，說明未來 LlamaIndex 整合需透過 `braintrust[otel]` + OpenTelemetry exporter

**Critical Contract:**

```yaml
# backend/evals/braintrust_config.yaml
braintrust:
  project: "finlab-x"
  api_key_env: "BRAINTRUST_API_KEY"
  local_mode: false
```

**Verification:**

| Scope | Command | Expected Result | Why |
| ----- | ------- | --------------- | --- |
| Dependency | `cd /Users/dong.wyt/Documents/dev-projects/fin-lab-x-wt-feat-csv-eval-management && pip install -e ".[dev]"` | 安裝成功，無 error | 確認 packages 可解析安裝 |
| Import | `python -c "import braintrust; import braintrust_langchain; import autoevals; print('OK')"` | `OK` | 確認三個 package 都可 import |

**Execution Checklist:**

- [ ] 更新 `pyproject.toml` 新增 `braintrust`、`braintrust-langchain`、`autoevals` 到 `[project.optional-dependencies] dev`
- [ ] 更新 `.gitignore` 新增 `backend/evals/results/`
- [ ] 建立 `backend/evals/braintrust_config.yaml`
- [ ] 更新 `backend/evals/README.md` 新增 Future Implementation 段落
- [ ] 執行 `pip install -e ".[dev]"` 確認安裝成功
- [ ] 執行 import 驗證
- [ ] Commit: `git commit -m "chore(evals): add braintrust and autoevals dependencies"`

---

### Task 2: Scenario Config Models + YAML Parser

**Files:**

- Create: `backend/evals/scenario_config.py`
- Tests: `backend/tests/evals/__init__.py`, `backend/tests/evals/test_scenario_config.py`

**What & Why:** 定義 scenario config 的 Pydantic models 和 YAML 載入邏輯。這是整個系統的 schema 定義，所有後續元件都依賴它。

**Critical Contract:**

```python
# backend/evals/scenario_config.py
from pathlib import Path

from pydantic import BaseModel, Field

class ScorerConfig(BaseModel):
    name: str
    function: str | None = None       # Python dotpath for programmatic scorer
    type: str | None = None           # "llm_judge" for LLM-based scoring
    rubric: str | None = None         # Mustache prompt template for llm_judge, e.g. "{{expected.ticker}}"
    model: str | None = None          # (llm_judge) LLM model, e.g. "gpt-4o", default: Braintrust proxy default
    use_cot: bool = False             # (llm_judge) chain-of-thought reasoning before scoring
    choice_scores: dict[str, float] | None = None  # (llm_judge) choice→score mapping, default: {"Y": 1.0, "N": 0.0}

class TaskConfig(BaseModel):
    function: str                     # Python dotpath, e.g. "backend.evals.eval_tasks.run_v1"

class ScenarioConfig(BaseModel):
    name: str
    csv: str = "dataset.csv"
    task: TaskConfig
    column_mapping: dict[str, str]    # csv_column -> "input" | "input.field" | "expected.field" | "metadata.field"
    scorers: list[ScorerConfig]

class BraintrustConfig(BaseModel):
    project: str = "finlab-x"
    api_key_env: str = "BRAINTRUST_API_KEY"
    local_mode: bool = False

def load_scenario_config(config_path: Path) -> ScenarioConfig:
    """讀取 eval_spec.yaml，回傳 validated ScenarioConfig。"""

def load_braintrust_config(config_path: Path) -> BraintrustConfig:
    """讀取 braintrust_config.yaml，回傳 BraintrustConfig。"""
```

**Test Strategy:**

- 合法 YAML → 正確 parse 成 `ScenarioConfig`，所有欄位值正確（happy path）
- 缺少 `task.function` → `ValidationError`，指出缺失欄位（failure path）
- YAML 語法錯誤 → 拋出明確錯誤（failure path）
- `scorers` 同時包含 programmatic（`function`）和 `llm_judge`（`type` + `rubric` + `model` + `use_cot` + `choice_scores`）→ 正確區分，optional fields 有正確 default（edge case）
- `BraintrustConfig` default 值：未指定 `project` → 預設 `"finlab-x"`（edge case）

**Verification:**

| Scope | Command | Expected Result | Why |
| ----- | ------- | --------------- | --- |
| Targeted | `python -m pytest backend/tests/evals/test_scenario_config.py -v` | All tests pass | Config parsing 正確 |
| Type check | `pyright backend/evals/scenario_config.py` | 0 errors | Type safety |

**Execution Checklist:**

- [ ] 🔴 建立 `backend/tests/evals/__init__.py` 和 `backend/tests/evals/test_scenario_config.py`，涵蓋上述 test strategy
- [ ] 🔴 執行測試確認 **fail**（RED）
- [ ] 🟢 實作 `backend/evals/scenario_config.py`
- [ ] 🔵 Review + refactor，重跑測試確認 **pass**
- [ ] Commit: `git commit -m "feat(evals): add scenario config pydantic models and YAML parser"`

---

### Task 3: CSV Loader + Column Mapping

**Files:**

- Create: `backend/evals/dataset_loader.py`
- Tests: `backend/tests/evals/test_dataset_loader.py`

**What & Why:** 讀取 CSV 並根據 `column_mapping` 將每一 row 轉為 `{input, expected, metadata}` 結構。這是 CSV → Braintrust data format 的核心轉換邏輯。

**Critical Contract:**

```python
# backend/evals/dataset_loader.py
from pathlib import Path

def load_dataset(csv_path: Path, column_mapping: dict[str, str]) -> list[dict]:
    """讀取 CSV，根據 column_mapping 轉換為 Braintrust Eval() data 格式。

    column_mapping 範例:
      {"prompt": "input", "expect_cjk_min": "expected.cjk_min", "category": "metadata.category"}

    回傳:
      [{"input": "...", "expected": {"cjk_min": 0.8}, "metadata": {"category": "..."}}, ...]

    型別轉換規則（CSV 值皆為 string，需自動轉換）:
      - 空字串 → None
      - "true" / "false"（case-insensitive）→ bool
      - 可解析為 float 的數值字串 → float
      - 其餘 → str

    Raises:
      ValueError: column_mapping 引用了 CSV 中不存在的欄位
      ValueError: CSV 只有 header 沒有 data rows
    """
```

**Implementation Notes:**

- 使用 `csv.DictReader` 讀取 CSV（自動處理 RFC 4180 quoting：含逗號、換行、引號的欄位）
- Mapping target 格式：`"input"` = 整個值作為 input string；`"input.field"` = input 是 dict，值放在 `input["field"]`
- 如果同一個 bucket 同時有 `"input"`（string）和 `"input.field"`（object），object 優先
- 在載入後立即驗證 column_mapping 中的所有 CSV 欄位名都存在於 header 中，不存在時拋出 `ValueError` 指出具體欄位名

**Test Strategy:**

- 基本 mapping：`prompt → input` → `{"input": "What is AAPL's P/E ratio?", "expected": {}, "metadata": {}}`（happy path）
- 多欄位 dotpath mapping：`prompt → input.question, category → input.category, ideal_answer → expected.answer` → 正確組裝 nested dict（happy path）
- 數值自動轉換：`"0.8"` → `0.8`，`"true"` → `True`，`""` → `None`（edge case）
- 未 mapped 的 column → 被忽略，不出現在 output 中（edge case）
- Column mapping 引用不存在的 CSV 欄位 → `ValueError`，訊息指出欄位名（failure path）
- 只有 header 沒有 data rows → `ValueError`，訊息含 "no data rows"（failure path）
- CJK 內容（中文 prompt）→ 正確保留，無 mojibake（edge case）
- RFC 4180 特殊字元（cell 含逗號、換行、escaped 引號）→ 正確 parse（edge case）

**Verification:**

| Scope | Command | Expected Result | Why |
| ----- | ------- | --------------- | --- |
| Targeted | `python -m pytest backend/tests/evals/test_dataset_loader.py -v` | All tests pass | CSV 轉換正確 |

**Execution Checklist:**

- [ ] 🔴 撰寫 `backend/tests/evals/test_dataset_loader.py`（使用 `io.StringIO` 或 `tmp_path` fixture 建立 test CSV）
- [ ] 🔴 執行測試確認 **fail**（RED）
- [ ] 🟢 實作 `backend/evals/dataset_loader.py`
- [ ] 🔵 Review + refactor，重跑測試確認 **pass**
- [ ] Commit: `git commit -m "feat(evals): add CSV loader with column mapping to braintrust format"`

---

### Task 4: Scorer Registry + Language Policy Scorers

**Files:**

- Create: `backend/evals/scorer_registry.py`
- Create: `backend/evals/scorers/__init__.py`
- Create: `backend/evals/scorers/language_policy_scorer.py`
- Tests: `backend/tests/evals/test_scorer_registry.py`

**What & Why:** 實作 scorer resolution（從 dotpath 載入 Python function）和 LLM-judge rubric builder。同時建立第一組 programmatic scorers（language policy），從現有 `eval_helpers.py` 重用 CJK 偵測邏輯。

**Approach Decision:**

| Option | Summary | Status | Why |
| ------ | ------- | ------ | --- |
| A: task function 回傳 `OrchestratorResult` dict，scorer 從中取所需欄位 | 保留完整結構化資訊 | Selected | `tool_arg_no_cjk` scorer 需要 `tool_outputs`，未來 scorer 也可能需要中間結果 |
| B: task function 只回傳 response string | 簡單但丟失 tool call 資訊 | Rejected | 無法評估 tool argument 品質 |

**Critical Contract:**

```python
# backend/evals/scorer_registry.py
from autoevals import LLMClassifier
from backend.evals.scenario_config import ScorerConfig

def resolve_scorers(scorer_configs: list[ScorerConfig]) -> list[callable]:
    """將 config 中的 scorer 定義轉為 callable list。

    所有回傳的 callable 符合 autoevals convention：(output, expected, *, input) → Score

    - function type: importlib 動態載入 Python dotpath
    - llm_judge type: 建立 autoevals.LLMClassifier instance
      - rubric → prompt_template（Mustache 語法，{{input}}, {{expected.field}}）
      - model, use_cot, choice_scores 從 ScorerConfig 取值（有 default）

    Raises:
        ImportError: dotpath 指向不存在的 module 或 function
    """
```

```python
# backend/evals/scorers/language_policy_scorer.py
from backend.evals.eval_helpers import contains_cjk, cjk_ratio

def tool_arg_no_cjk(output, expected, *, input) -> Score:
    """檢查 tool arguments 是否全為英文（無 CJK 字元）。

    簽名對齊 autoevals convention：(output, expected, *, input) → Score

    - output: OrchestratorResult dict（keys: response, tool_outputs, model, version），取 output["tool_outputs"]
    - expected: 可含 expected["search_query_no_cjk"]（bool）和 expected["tool"]（Optional[str]）
    - 若 expected["search_query_no_cjk"] 為 False 或 None → 直接 score 1.0（skip）
    - ticker 格式 arg 用 ^[A-Z][A-Z0-9.\-]*$ regex 驗證，非一般 CJK 檢查
    - score: 1.0 = 全部 pass, 0.0 = 任一 fail
    """

def response_language(output, expected, *, input) -> Score:
    """檢查 response 的 CJK ratio 是否在 expected 範圍內。

    簽名對齊 autoevals convention：(output, expected, *, input) → Score

    - output: OrchestratorResult dict（keys: response, tool_outputs, model, version），取 output["response"]
    - expected: 需含 expected["cjk_min"]（float）和 expected["cjk_max"]（float）
    - score: 1.0 = ratio 在 [cjk_min, cjk_max] 範圍內, 0.0 = 超出範圍
    """
```

**Implementation Notes:**

- `resolve_scorers()` 在 eval 執行前一次性解析所有 scorer，確保 dotpath 不存在時在 task 開始前就報錯
- `llm_judge` 類型：建立 `autoevals.LLMClassifier` instance，`rubric` → `prompt_template`（Mustache 語法），`choice_scores` 預設 `{"Y": 1.0, "N": 0.0}`，`use_cot` 和 `model` 從 config 取值
- Programmatic scorer 簽名為 `(output, expected, *, input) → Score`，與 `LLMClassifier` 一致
- `tool_arg_no_cjk` 的邏輯對齊現有 `test_language_policy.py` 中的 Rule A 檢查邏輯

**Test Strategy:**

- Dotpath resolve：合法路徑 → 回傳正確 function reference（happy path）
- Dotpath resolve：不存在的 module → `ImportError`，訊息指出 module 名（failure path）
- Dotpath resolve：module 存在但 function 不存在 → `ImportError`，訊息指出 function 名（failure path）
- LLM-judge resolve：`llm_judge` type + rubric → 回傳 `LLMClassifier` instance，`prompt_template` 為 rubric 值（happy path）
- LLM-judge resolve：`llm_judge` type + `model="gpt-4o"` + `use_cot=True` + custom `choice_scores` → instance 正確設定（happy path）
- LLM-judge resolve：缺少 `rubric` 的 `llm_judge` type → 拋出 `ValueError`（failure path）
- `tool_arg_no_cjk`：tool args 全英文 → `{"name": "tool_arg_no_cjk", "score": 1.0}`（happy path）
- `tool_arg_no_cjk`：tool arg 含 CJK → `{"name": "tool_arg_no_cjk", "score": 0.0}`（failure path）
- `tool_arg_no_cjk`：ticker arg 用 regex 驗證而非 CJK 檢查（edge case）
- `tool_arg_no_cjk`：`expected["search_query_no_cjk"]` 為 `None` → skip，score 1.0（edge case）
- `response_language`：CJK ratio 在範圍 [0.2, 1.0] 內 → score 1.0（happy path）
- `response_language`：CJK ratio 低於 min → score 0.0（failure path）

**Verification:**

| Scope | Command | Expected Result | Why |
| ----- | ------- | --------------- | --- |
| Targeted | `python -m pytest backend/tests/evals/test_scorer_registry.py -v` | All tests pass | Scorer 解析和執行正確 |
| Type check | `pyright backend/evals/scorer_registry.py backend/evals/scorers/language_policy_scorer.py` | 0 errors | Type safety |

**Execution Checklist:**

- [ ] 🔴 撰寫 `backend/tests/evals/test_scorer_registry.py`，涵蓋上述 test strategy
- [ ] 🔴 執行測試確認 **fail**（RED）
- [ ] 🟢 實作 `backend/evals/scorer_registry.py`、`backend/evals/scorers/__init__.py`、`backend/evals/scorers/language_policy_scorer.py`
- [ ] 🔵 Review + refactor，重跑測試確認 **pass**
- [ ] Commit: `git commit -m "feat(evals): add scorer registry with dotpath resolution and language scorers"`

---

### Task 5: Task Function + Language Policy Scenario Data

**Files:**

- Create: `backend/evals/eval_tasks.py`
- Create: `backend/evals/scenarios/language_policy/dataset.csv`
- Create: `backend/evals/scenarios/language_policy/eval_spec.yaml`
- Tests: `backend/tests/evals/test_eval_tasks.py`

**What & Why:** 建立 task function（wrapping Orchestrator）和第一個完整 CSV scenario。Task function 連接 eval 系統與 agent engine。Language policy scenario 從現有 dataclass 遷移為 CSV 格式。

**Critical Contract:**

```python
# backend/evals/eval_tasks.py
from backend.agent_engine.agents.base import Orchestrator, OrchestratorResult
from backend.agent_engine.agents.config_loader import VersionConfigLoader

def run_v1(input) -> OrchestratorResult:
    """Braintrust task function：執行 v1_baseline agent，回傳完整 OrchestratorResult。

    Braintrust Eval() 只傳入 input（不含 expected / metadata）。
    Braintrust tracing 已由 runner 在 Eval() 呼叫前設定 global handler。
    """
    config = VersionConfigLoader("v1_baseline").load()
    orchestrator = Orchestrator(config)
    prompt = input if isinstance(input, str) else input.get("prompt", str(input))
    return orchestrator.run(prompt)
```

```yaml
# backend/evals/scenarios/language_policy/eval_spec.yaml
name: language_policy
csv: dataset.csv

task:
  function: backend.evals.eval_tasks.run_v1

column_mapping:
  prompt: input
  prompt_language: metadata.prompt_language
  ticker: expected.ticker
  expect_tool: expected.tool
  expect_search_query_no_cjk: expected.search_query_no_cjk
  expect_response_cjk_min: expected.cjk_min
  expect_response_cjk_max: expected.cjk_max

scorers:
  - name: tool_arg_no_cjk
    function: backend.evals.scorers.language_policy_scorer.tool_arg_no_cjk
  - name: response_language
    function: backend.evals.scorers.language_policy_scorer.response_language
  - name: response_relevance
    type: llm_judge
    model: gpt-4o
    use_cot: true
    rubric: |
      The user asked about the company with ticker {{expected.ticker}}.

      User's question:
      {{input}}

      Agent's response:
      {{output}}

      Does the response stay focused ONLY on {{expected.ticker}} and directly relevant information?
      Score Y if the response only discusses {{expected.ticker}} and topics the user asked about.
      Score N if the response includes substantial information about other companies or topics not asked about.
    choice_scores:
      Y: 1.0
      N: 0.0
```

```csv
id,description,prompt,prompt_language,ticker,expect_tool,expect_search_query_no_cjk,expect_response_cjk_min,expect_response_cjk_max
LP-01,Chinese news query,微軟最近有什麼新聞？,zh,MSFT,tavily_financial_search,true,0.20,1.0
LP-02,Chinese earnings query,蘋果公司最新的財報表現如何？,zh,AAPL,,true,0.20,1.0
LP-03,English news query,What is the latest news about MSFT?,en,MSFT,tavily_financial_search,true,0.0,0.02
LP-04,English performance query,How is AAPL performing recently?,en,AAPL,tavily_financial_search,true,0.0,0.02
LP-05,Chinese price query,特斯拉現在股價多少？,zh,TSLA,yfinance_stock_quote,true,0.20,1.0
LP-06,English price query,What is TSLA's current price?,en,TSLA,yfinance_stock_quote,true,0.0,0.02
LP-07,Mixed lang query,NVDA 最近表現如何？,zh,NVDA,,true,0.20,1.0
LP-08,Ticker-only prompt,GOOGL,en,GOOGL,,true,0.0,0.02
```

**Implementation Notes:**

- Task function 不含 Braintrust tracing 設定——runner 負責在 `Eval()` 前設定 `set_global_handler()`
- `id` 和 `description` 欄位不在 `column_mapping` 中，被 loader 忽略但保留在 result CSV（供人類閱讀）
- `ticker` 欄位 mapped 到 `expected.ticker`，供 `response_relevance` LLM-judge 的 rubric 插值使用
- CSV 中空值（如 LP-02 的 `expect_tool`）經 loader 轉為 `None`
- Task function 每次呼叫建立新 `Orchestrator` instance（eval 執行頻率低，不需 cache）

**Test Strategy:**

- `run_v1`：string input → `orchestrator.run()` 收到同一 string（happy path，mock `Orchestrator`）
- `run_v1`：dict input `{"prompt": "test"}` → `orchestrator.run("test")`（edge case，mock `Orchestrator`）
- `run_v1`：回傳值為 `OrchestratorResult` 結構（happy path）

**Verification:**

| Scope | Command | Expected Result | Why |
| ----- | ------- | --------------- | --- |
| Targeted | `python -m pytest backend/tests/evals/test_eval_tasks.py -v` | All tests pass | Task function input dispatch 正確 |
| Config | `python -c "from backend.evals.scenario_config import load_scenario_config; from pathlib import Path; c = load_scenario_config(Path('backend/evals/scenarios/language_policy/eval_spec.yaml')); print(c.name, len(c.scorers))"` | `language_policy 3` | Config 正確載入（2 programmatic + 1 llm_judge） |
| Dataset | `python -c "from backend.evals.dataset_loader import load_dataset; from backend.evals.scenario_config import load_scenario_config; from pathlib import Path; c = load_scenario_config(Path('backend/evals/scenarios/language_policy/eval_spec.yaml')); d = load_dataset(Path('backend/evals/scenarios/language_policy/dataset.csv'), c.column_mapping); print(len(d), type(d[0]['input']))"` | `8 <class 'str'>` | 8 筆 data 正確載入，input 為 string |

**Execution Checklist:**

- [ ] 🔴 撰寫 `backend/tests/evals/test_eval_tasks.py`（mock `VersionConfigLoader` 和 `Orchestrator`，驗證 input dispatch 邏輯）
- [ ] 🔴 執行測試確認 **fail**（RED）
- [ ] 🟢 實作 `backend/evals/eval_tasks.py`
- [ ] 建立 `backend/evals/scenarios/language_policy/` 目錄
- [ ] 建立 `dataset.csv`（從 `LANGUAGE_POLICY_CASES` dataclass 轉換，確保 CJK 編碼 UTF-8）
- [ ] 建立 `eval_spec.yaml`
- [ ] 🔵 Review + refactor，重跑測試確認 **pass**，執行 verification 指令確認元件整合正確
- [ ] Commit: `git commit -m "feat(evals): add language policy CSV scenario and task function"`

---

### Task 6: Eval Runner

**Files:**

- Create: `backend/evals/eval_runner.py`
- Tests: `backend/tests/evals/test_eval_runner.py`

**What & Why:** 核心 orchestrator——掃描 scenarios、設定 Braintrust tracing、組裝 `Eval()`、輸出 result CSV。從一開始同時支援 `--local-only` 和 platform 模式。

**Critical Contract:**

```python
# backend/evals/eval_runner.py
"""Eval Runner: scenario discovery + Braintrust Eval() assembly + result CSV output.

Usage:
    python -m backend.evals.eval_runner language_policy
    python -m backend.evals.eval_runner --all
    python -m backend.evals.eval_runner language_policy --local-only
    python -m backend.evals.eval_runner language_policy --output-dir ./results
"""
from pathlib import Path

SCENARIOS_DIR = Path(__file__).parent / "scenarios"
DEFAULT_RESULTS_DIR = Path(__file__).parent / "results"
BRAINTRUST_CONFIG_PATH = Path(__file__).parent / "braintrust_config.yaml"

def discover_scenarios(scenarios_dir: Path) -> list[str]:
    """掃描 scenarios/ 下含 eval_spec.yaml 的子目錄，回傳 scenario names。"""

def run_scenario(scenario_name: str, *, local_only: bool, output_dir: Path) -> Path:
    """執行單一 scenario。

    流程：
    1. 載入 eval_spec.yaml → ScenarioConfig
    2. 驗證 CSV 檔案存在
    3. load_dataset() → data list
    4. resolve_scorers() → scorer callables
    5. 動態 import task function
    6. 如非 local_only：驗證 API key、init_logger + set_global_handler
    7. Eval(project, data=..., task=..., scores=..., experiment_name=..., no_send_logs=...)
    8. write_result_csv() → 回傳 result CSV path
    """

def write_result_csv(eval_result, scenario_name: str, scorer_names: list[str], output_dir: Path) -> Path:
    """從 Eval() 結果寫入 {scenario}_{YYYYMMDD_HHMM}.csv。

    CSV 欄位組成：
    - 原始 input 欄位（如 prompt）
    - output：task function 的 response string（取 output["response"] 如果 output 是 dict）
    - score_{name}：每個 scorer 的分數，name 來自 ScorerConfig.name
      例：scorer_names=["tool_arg_no_cjk", "response_language"]
      → CSV 欄位 score_tool_arg_no_cjk, score_response_language

    每筆資料取自 eval_result.results[i]：
    - .input → 原始 input
    - .output → task function 回傳值
    - .scores → dict，key 為 scorer name，value 含 .score（float）
    """

def main():
    """CLI entry point with argparse。

    Behavior:
    - 單一 scenario：失敗時 exit code ≠ 0
    - --all：跳過無效 scenario（warning），其餘執行，印出 summary（N succeeded, M skipped）
    - 不存在的 scenario name → 列出可用 scenario 清單
    - 空 scenarios 目錄 + --all → "no scenarios found"
    - 非 local_only 且無 API key → fail fast，提示設定 key 或用 --local-only
    """
```

**Implementation Notes:**

- `discover_scenarios()` 掃描子目錄中含 `eval_spec.yaml` 的資料夾
- 驗證階段在 `Eval()` 之前完成：config parse、CSV 存在、scorer dotpath resolve、task function import。任何失敗都在 task 執行前報錯
- Platform 模式下，`init_logger(project=..., api_key=...)` + `set_global_handler(BraintrustCallbackHandler())` 在第一個 `Eval()` 呼叫前設定一次
- `Eval()` 的 `data` 參數傳入 `load_dataset()` 結果；`task` 傳入動態 import 的 function；`scores` 傳入 `resolve_scorers()` 結果
- Result CSV 從 `eval_result.results` 取得每筆的 `input`、`output`、`scores`，寫入 timestamped CSV
- `results/` 目錄不存在時自動建立
- 動態 import task function 使用與 `scorer_registry.py` 相同的 importlib 邏輯（可抽共用 helper）

**Test Strategy:**

- `discover_scenarios`：有效目錄（含 `eval_spec.yaml`）→ 回傳 scenario name（happy path）
- `discover_scenarios`：空目錄 → 回傳空 list（edge case）
- `discover_scenarios`：子目錄缺 `eval_spec.yaml` → 不納入結果（edge case）
- `run_scenario` integration test：mock task function + 2-row CSV + `local_only=True` → result CSV 正確產出，包含 input + output + score 欄位（happy path）
- `run_scenario`：CSV 不存在 → 報錯，訊息指出缺失檔案（failure path）
- `run_scenario`：task function dotpath 錯誤 → 報錯，訊息指出 import 失敗（failure path）
- `write_result_csv`：驗證檔名為 `{scenario}_{timestamp}.csv` 格式（happy path）
- `write_result_csv`：兩次寫入 → 產生不同 timestamp 的檔案，不覆蓋（edge case）
- `write_result_csv`：output 含逗號和換行 → result CSV 正確 escape（edge case）
- `main` CLI：不存在的 scenario → exit code ≠ 0 + 列出可用清單（failure path）

**Verification:**

| Scope | Command | Expected Result | Why |
| ----- | ------- | --------------- | --- |
| Targeted | `python -m pytest backend/tests/evals/test_eval_runner.py -v` | All tests pass | Runner 邏輯正確 |
| Discovery | `python -c "from backend.evals.eval_runner import discover_scenarios; from pathlib import Path; print(discover_scenarios(Path('backend/evals/scenarios')))"` | `['language_policy']` | Scenario discovery 正確 |
| Lint | `ruff check backend/evals/` | 無 error | Code style |

**Execution Checklist:**

- [ ] 🔴 撰寫 `backend/tests/evals/test_eval_runner.py`（mock task function 回傳固定 `OrchestratorResult`，使用 `tmp_path` 作為 output dir，`local_only=True`）
- [ ] 🔴 執行測試確認 **fail**（RED）
- [ ] 🟢 實作 `backend/evals/eval_runner.py`
- [ ] 🔵 Review + refactor，重跑測試確認 **pass**
- [ ] Commit: `git commit -m "feat(evals): add eval runner with scenario discovery and result CSV output"`

---

### Flow Verification: Local Eval 端對端流程

> Tasks 1–6 完成了本機 eval 的完整流程。以下驗證必須全部通過後才能進行 Task 7。

| # | Method | Step | Expected Result |
| --- | --- | --- | --- |
| 1 | CLI | `python -m backend.evals.eval_runner language_policy --local-only` | 執行完成，exit code = 0，terminal 顯示 per-scorer 統計 |
| 2 | File check | `ls backend/evals/results/language_policy_*.csv` | 存在一個 timestamped result CSV |
| 3 | File content | `python -c "import csv, glob; f=glob.glob('backend/evals/results/language_policy_*.csv')[0]; r=list(csv.DictReader(open(f))); print(len(r), sorted(r[0].keys()))"` | 8 rows，欄位包含 `output`、`score_tool_arg_no_cjk`、`score_response_language`、`score_response_relevance` |
| 4 | Re-run | 再跑一次 `python -m backend.evals.eval_runner language_policy --local-only` | 產生第二個 result CSV（不覆蓋第一個） |
| 5 | Guardrail | `python -m pytest backend/evals/test_language_policy.py -v -m eval` | 現有 pytest eval 仍通過（未被破壞） |

- [ ] All flow verifications pass

---

### Task 7: Manual Braintrust Platform 全流程驗證

**What & Why:** 驗證完整的 prompt 迭代工作流程——執行 eval 上傳到 Braintrust，在 UI 上做 experiment diff，確認 per-case regression/improvement 和 trace drill-down 可見。

**Prerequisites:**

- Braintrust 帳號已建立，project "finlab-x" 已存在
- `BRAINTRUST_API_KEY` 環境變數已設定
- Flow Verification: Local Eval 已通過

**Verification:**

| # | Method | Step | Expected Result |
| --- | --- | --- | --- |
| 1 | CLI | `python -m backend.evals.eval_runner language_policy` | Terminal 輸出 Braintrust experiment URL (run 1)，result CSV 產出 |
| 2 | Braintrust UI | 打開 URL → 確認 experiment 存在 | 8 個 test cases 都在，每個有 `tool_arg_no_cjk`、`response_language`、`response_relevance` 分數 |
| 3 | Braintrust UI | 點進任一 test case | 能看到完整 trace（LLM call、tool calls、node transitions）；確認 `response_relevance` scorer 的 LLM call 不在 task trace 中 |
| 4 | CLI | 再跑一次 `python -m backend.evals.eval_runner language_policy` | Terminal 輸出新的 experiment URL (run 2) |
| 5 | Braintrust UI | 選 run 1 和 run 2 → 點 "Compare" | 能看到 experiment diff，顯示 per-case 變化 |
| 6 | File check | `ls backend/evals/results/` | 存在兩個不同 timestamp 的 result CSVs |
| 7 | Fail fast | 移除 `BRAINTRUST_API_KEY`，執行 `python -m backend.evals.eval_runner language_policy`（不加 `--local-only`） | 在 task 執行前報錯，提示設定 API key 或使用 `--local-only` |

- [ ] All manual verifications pass

**Execution Checklist:**

- [ ] 確認 `BRAINTRUST_API_KEY` 環境變數已設定
- [ ] 執行 run 1，記錄 experiment URL
- [ ] 在 Braintrust UI 驗證 test cases、scores、trace drill-down
- [ ] 執行 run 2
- [ ] 在 Braintrust UI 驗證 experiment diff
- [ ] 測試 fail fast 行為
- [ ] 記錄驗證結果

---

## Pre-delivery Checklist

### Code Level (TDD)

- [ ] `python -m pytest backend/tests/evals/ -v` — all new tests pass
- [ ] `python -m pytest backend/evals/test_language_policy.py -v -m eval` — 現有 pytest eval 仍通過
- [ ] `ruff check backend/evals/` — lint pass
- [ ] `pyright backend/evals/` — type check pass

### Flow Level (Behavioral)

- [ ] Flow: Local Eval 端對端 — PASS / FAIL
- [ ] Flow: Braintrust Platform 全流程 — PASS / FAIL

### Summary

- [ ] Both levels pass → ready for delivery
- [ ] Any failure is documented with cause and next action
