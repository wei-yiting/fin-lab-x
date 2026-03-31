# Implementation Plan: CSV 驅動的 Evaluation 管理系統 + Braintrust 整合

> Design Reference: [`design.md`](./design.md)

**Goal:** 將 evaluation 系統從 Python dataclass 轉為 CSV 驅動的工作流程，整合 Braintrust 進行實驗追蹤與比較，並產出 result CSV 供本地標注。

**Architecture / Key Decisions:**
- 三層架構：CSV（dataset）/ YAML（config + mapping + scorers）/ Python（scorer 實作）
- Convention-based discovery：`scenarios/` 下每個子目錄 = 一個 scenario
- 所有 scorer 對齊 Braintrust `(input, output, expected) → {"name", "score"}` 簽名
- 現有 language policy eval 遷移為第一個 CSV scenario，作為 end-to-end 驗證

**Tech Stack:** Python 3.10+, Braintrust SDK, autoevals, PyYAML（已有）, csv（stdlib）

---

## Dependencies Verification

| Dependency | Version | Source | What Was Verified | Notes |
| ---------- | ------- | ------ | ----------------- | ----- |
| `braintrust` | latest | Context7 `/websites/braintrust_dev` | `Eval()` API：接受 `data` (list/lambda), `task` (callable), `scores` (list), `no_send_logs` (bool)。回傳 `.results` 和 `.summary`。Task function 可回傳任意型別（含 dict），scorer 的 `output` 參數型別即為 task 的回傳值，無 string 限制 | Python scorer 可回傳 `float` 或 `{"name": str, "score": float}` |
| `braintrust-langchain` | latest | Context7 `/websites/braintrust_dev` | 提供 `BraintrustCallbackHandler` 和 `set_global_handler`，設定後 LangGraph/LangChain 的所有 invoke 自動被 Braintrust trace 捕捉 | 用於 task function 中啟用 trace drill-down |
| `autoevals` | latest | Context7 | 提供 `Factuality`, `Levenshtein`, `EmbeddingSimilarity` 等內建 scorer | 可與自訂 scorer 混用於 `scores` list |
| `pyyaml` | >=6.0.2 | pyproject.toml | 已在 dependencies 中 | 無需額外安裝 |

## Constraints

- 現有 `backend/evals/test_language_policy.py` 的 pytest eval 必須保持可用，直到新系統完全驗證通過
- CSV 欄位值必須是 flat string/number（Google Sheets 相容）
- `backend/agent_engine/` 的程式碼不在此次修改範圍內，task function 透過 import 呼叫現有 `Orchestrator`
- `.artifacts/` 和 `results/` 目錄已在 `.gitignore` 中（`.artifacts/` 已有，`results/` 需新增）

---

## File Plan

| Operation | Path | Purpose |
| --------- | ---- | ------- |
| Create | `backend/evals/scenarios/language_policy/dataset.csv` | Language policy 的 8 個 test cases |
| Create | `backend/evals/scenarios/language_policy/eval_spec.yaml` | Column mapping + scorer 清單 |
| Create | `backend/evals/scenario_config.py` | 載入 scenario config 的 Pydantic models + YAML parser |
| Create | `backend/evals/dataset_loader.py` | CSV 讀取 + column mapping 轉換邏輯 |
| Create | `backend/evals/scorer_registry.py` | 從 dotpath 解析 scorer function + LLM-judge rubric builder |
| Create | `backend/evals/eval_runner.py` | Eval Runner：scenario discovery + 組裝 `Eval()` + result CSV 輸出 |
| Create | `backend/evals/scorers/language_policy_scorer.py` | Language policy scorers：`tool_arg_no_cjk`, `response_language` |
| Create | `backend/evals/eval_tasks.py` | Task functions：wrapping `Orchestrator.run()` for Braintrust `Eval()` |
| Create | `backend/evals/braintrust_config.yaml` | Braintrust 專案層級設定（project name, API key env var, local_mode） |
| Create | `backend/tests/evals/test_scenario_config.py` | config.py 的 unit tests |
| Create | `backend/tests/evals/test_dataset_loader.py` | loader.py 的 unit tests |
| Create | `backend/tests/evals/test_scorer_registry.py` | scorer_registry.py 的 unit tests |
| Create | `backend/tests/evals/test_eval_runner.py` | runner.py 的 integration tests |
| Create | `backend/tests/evals/__init__.py` | Package init |
| Update | `backend/evals/README.md` | 新增 Future Implementation 段落（LlamaIndex + Braintrust OTEL 整合） |
| Update | `pyproject.toml` | 新增 `braintrust`, `autoevals` 到 dev dependencies |
| Update | `.gitignore` | 新增 `backend/evals/results/` |
| Preserve | `backend/evals/test_language_policy.py` | 保留現有 pytest eval，待新系統驗證後再決定移除 |
| Preserve | `backend/evals/datasets/language_policy.py` | 保留，供現有 pytest eval 使用 |
| Preserve | `backend/evals/eval_helpers.py` | 保留，新 scorer 會 import 其中的 `contains_cjk`, `cjk_ratio` |

**Structure sketch:**

```text
backend/evals/
  braintrust_config.yaml          # Braintrust 專案設定
  scenario_config.py              # Pydantic models（schema 定義 + YAML 驗證）
  dataset_loader.py               # CSV 讀取 + column mapping 轉換
  scorer_registry.py              # Scorer dotpath 解析 + LLM-judge builder
  eval_runner.py                  # CLI entry point + Eval() 組裝
  eval_tasks.py                   # Task functions (wrapping Orchestrator)
  eval_helpers.py                 # (existing) CJK helpers
  conftest.py                     # (existing) pytest fixtures
  test_language_policy.py         # (existing) pytest eval - preserved
  datasets/
    language_policy.py            # (existing) frozen dataclass - preserved
  scenarios/
    language_policy/
      dataset.csv                 # 8 test cases from dataclass
      eval_spec.yaml               # column mapping + scorer 定義
  scorers/
    __init__.py
    language_policy_scorer.py     # tool_arg_no_cjk, response_language
  results/                        # (gitignored) eval result CSVs
```

---

### Task 1: 新增 Dependencies + 基礎設定

**Files:**

- Update: `pyproject.toml`
- Update: `.gitignore`
- Create: `backend/evals/braintrust_config.yaml`

**What & Why:** 安裝 Braintrust SDK 和 autoevals，設定 gitignore 排除 result CSVs，建立 Braintrust 專案設定檔。這是所有後續 task 的前置條件。

**Implementation Notes:**

- `braintrust`、`braintrust-langchain` 和 `autoevals` 加到 `[project.optional-dependencies] dev` 區塊
- `backend/evals/results/` 加到 `.gitignore`
- `braintrust_config.yaml` 定義 project name 和 API key 環境變數名

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
| Dependency | `cd /Users/dong.wyt/Documents/dev-projects/fin-lab-x-wt-feat-csv-eval-management && pip install -e ".[dev]"` | 安裝成功，`import braintrust`、`import braintrust_langchain` 和 `import autoevals` 不報錯 | 確認 SDK 可用 |
| Lint | `ruff check backend/evals/` | 無 error | 確認 code style |

**Execution Checklist:**

- [ ] 更新 `pyproject.toml` 新增 `braintrust`、`braintrust-langchain` 和 `autoevals` 到 dev dependencies
- [ ] 更新 `.gitignore` 新增 `backend/evals/results/`
- [ ] 建立 `backend/evals/braintrust_config.yaml`
- [ ] 執行 `pip install -e ".[dev]"` 確認安裝成功
- [ ] 執行 `python -c "import braintrust; import braintrust_langchain; import autoevals; print('OK')"` 確認 import 正常
- [ ] 更新 `backend/evals/README.md`，新增 Future Implementation 段落：說明未來加入 LlamaIndex 時，需透過 `braintrust[otel]` + OpenTelemetry exporter 在 task function 中啟用 Braintrust trace 捕捉
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
from pydantic import BaseModel, Field

class ScorerConfig(BaseModel):
    name: str
    function: str | None = None       # Python dotpath for programmatic scorer
    type: str | None = None           # "llm_judge" for LLM-based scoring
    rubric: str | None = None         # Rubric template for llm_judge

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

def load_scenario_config(config_path: Path) -> ScenarioConfig: ...
def load_braintrust_config(config_path: Path) -> BraintrustConfig: ...
```

**Test Strategy:**

- 合法 YAML → 正確 parse 成 `ScenarioConfig`（happy path）
- 缺少必要欄位 → 拋出 `ValidationError`（failure path）
- `scorers` 同時包含 `function` 和 `llm_judge` type → 正確區分（edge case）
- `BraintrustConfig` 讀取與 default 值驗證

**Verification:**

| Scope | Command | Expected Result | Why |
| ----- | ------- | --------------- | --- |
| Targeted | `python -m pytest backend/tests/evals/test_scenario_config.py -v` | All tests pass | Config parsing 正確 |
| Type check | `pyright backend/evals/scenario_config.py` | 0 errors | Type safety |

**Execution Checklist:**

- [ ] 🔴 建立 `backend/tests/evals/__init__.py` 和 `backend/tests/evals/test_scenario_config.py`，撰寫測試
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
def load_dataset(csv_path: Path, column_mapping: dict[str, str]) -> list[dict]:
    """
    讀取 CSV，根據 column_mapping 轉換為 Braintrust 格式。

    column_mapping 範例:
      {"prompt": "input", "expect_cjk_min": "expected.cjk_min", "category": "metadata.category"}

    回傳:
      [{"input": "...", "expected": {"cjk_min": "0.8"}, "metadata": {"category": "..."}}, ...]
    """
```

**Implementation Notes:**

- 使用 `csv.DictReader` 讀取 CSV
- mapping target 格式：`"input"` = 整個值作為 input string；`"input.field"` = input 是 dict，值放在 `input["field"]`
- 數值欄位（如 `expect_cjk_min`）從 CSV 讀進來是 string，需要在 loader 中轉為 `float`（偵測是否為數值字串）

**Test Strategy:**

- 基本 mapping：3 columns → `{input, expected, metadata}` 正確組裝（happy path）
- 多欄位組裝 input object：`prompt → input`, `context → input.context` → input 變成 dict（edge case）
- 數值自動轉換：`"0.8"` → `0.8`（edge case）
- 空 CSV → 回傳空 list（edge case）
- 未 mapped 的 column → 被忽略（edge case）

**Verification:**

| Scope | Command | Expected Result | Why |
| ----- | ------- | --------------- | --- |
| Targeted | `python -m pytest backend/tests/evals/test_dataset_loader.py -v` | All tests pass | CSV 轉換正確 |

**Execution Checklist:**

- [ ] 🔴 撰寫 `backend/tests/evals/test_dataset_loader.py` 測試（含 fixture CSV 檔案或 `io.StringIO`）
- [ ] 🔴 執行測試確認 **fail**（RED）
- [ ] 🟢 實作 `backend/evals/dataset_loader.py`
- [ ] 🔵 Review + refactor，重跑測試確認 **pass**
- [ ] Commit: `git commit -m "feat(evals): add CSV loader with column mapping to braintrust format"`

---

### Task 4: Scorer Registry

**Files:**

- Create: `backend/evals/scorer_registry.py`
- Create: `backend/evals/scorers/__init__.py`
- Create: `backend/evals/scorers/language_policy_scorer.py`
- Tests: `backend/tests/evals/test_scorer_registry.py`

**What & Why:** 實作 scorer resolution（從 dotpath 載入 Python function）和 LLM-judge rubric builder。同時建立第一組 programmatic scorers（language policy），從現有 `eval_helpers.py` 重用 CJK 偵測邏輯。

**Critical Contract:**

```python
# backend/evals/scorer_registry.py
from backend.evals.scenario_config import ScorerConfig

def resolve_scorers(scorer_configs: list[ScorerConfig]) -> list[callable]:
    """
    將 config 中的 scorer 定義轉為 callable list。
    - function type: importlib 動態載入 Python dotpath
    - llm_judge type: 建立 LLM scorer closure，rubric 中的 {input}, {expected.field} 延遲插值
    """
```

```python
# backend/evals/scorers/language_policy_scorer.py
from backend.evals.eval_helpers import contains_cjk, cjk_ratio

def tool_arg_no_cjk(input, output, expected) -> dict:
    """檢查 tool arguments 是否全為英文（無 CJK 字元）。score: 1=pass, 0=fail"""

def response_language(input, output, expected) -> dict:
    """檢查 response 的 CJK ratio 是否在 expected 範圍內。score: 1=pass, 0=fail"""
```

**Implementation Notes:**

- `tool_arg_no_cjk` 需要從 `output` 中取得 `tool_outputs`，這意味著 task function 的回傳值需要包含結構化資訊，不能只是 string。**Approach Decision** 見下方。
- LLM-judge builder 建立一個 closure：接收 `ScorerConfig.rubric` template，在每次呼叫時用 `str.format_map()` 插入 `input` 和 `expected` 的值

**Approach Decision:**

| Option | Summary | Status | Why |
| ------ | ------- | ------ | --- |
| A: task function 回傳 `OrchestratorResult` dict，scorer 從中取所需欄位 | 保留完整結構化資訊 | Selected | Language policy scorer 需要 `tool_outputs`，未來 scorer 也可能需要中間結果 |
| B: task function 只回傳 response string | 簡單但丟失 tool call 資訊 | Rejected | 無法評估 tool argument 品質 |

**Test Strategy:**

- Dotpath resolve：合法路徑 → 回傳正確 function（happy path）
- Dotpath resolve：不存在的路徑 → 拋出明確錯誤（failure path）
- LLM-judge builder：rubric 插值正確（happy path，mock LLM call）
- `tool_arg_no_cjk`：tool args 全英文 → score 1；含 CJK → score 0（happy + failure）
- `response_language`：CJK ratio 在範圍內 → score 1；超出 → score 0（happy + failure）

**Verification:**

| Scope | Command | Expected Result | Why |
| ----- | ------- | --------------- | --- |
| Targeted | `python -m pytest backend/tests/evals/test_scorer_registry.py -v` | All tests pass | Scorer 解析和執行正確 |
| Type check | `pyright backend/evals/scorer_registry.py backend/evals/scorers/language_policy_scorer.py` | 0 errors | Type safety |

**Execution Checklist:**

- [ ] 🔴 撰寫 `backend/tests/evals/test_scorer_registry.py` 測試
- [ ] 🔴 執行測試確認 **fail**（RED）
- [ ] 🟢 實作 `backend/evals/scorer_registry.py`、`backend/evals/scorers/__init__.py`、`backend/evals/scorers/language_policy_scorer.py`
- [ ] 🔵 Review + refactor，重跑測試確認 **pass**
- [ ] Commit: `git commit -m "feat(evals): add scorer registry with dotpath resolution and language scorers"`

---

### Task 5: Task Function + Language Policy Scenario

**Files:**

- Create: `backend/evals/eval_tasks.py`
- Create: `backend/evals/scenarios/language_policy/dataset.csv`
- Create: `backend/evals/scenarios/language_policy/eval_spec.yaml`

**What & Why:** 建立 task function（wrapping Orchestrator）和第一個完整的 CSV scenario。Task function 是連接 eval 系統和 agent engine 的橋樑。Language policy scenario 是從現有 dataclass 遷移過來的 CSV 化版本。

**Critical Contract:**

```python
# backend/evals/eval_tasks.py
import os
from braintrust import init_logger
from braintrust_langchain import BraintrustCallbackHandler, set_global_handler
from backend.agent_engine.agents.base import Orchestrator, OrchestratorResult
from backend.agent_engine.agents.config_loader import VersionConfigLoader

def _ensure_braintrust_tracing():
    """設定 Braintrust global callback handler，讓 LangGraph invoke 自動被 trace。"""
    init_logger(project="finlab-x", api_key=os.environ.get("BRAINTRUST_API_KEY"))
    set_global_handler(BraintrustCallbackHandler())

def run_v1(input) -> OrchestratorResult:
    """Braintrust task function：執行 v1_baseline agent，回傳完整 OrchestratorResult。"""
    _ensure_braintrust_tracing()
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
  expect_tool: expected.tool
  expect_search_query_no_cjk: expected.search_query_no_cjk
  expect_response_cjk_min: expected.cjk_min
  expect_response_cjk_max: expected.cjk_max

scorers:
  - name: tool_arg_no_cjk
    function: backend.evals.scorers.language_policy_scorer.tool_arg_no_cjk
  - name: response_language
    function: backend.evals.scorers.language_policy_scorer.response_language
```

```csv
id,description,prompt,prompt_language,expect_tool,expect_search_query_no_cjk,expect_response_cjk_min,expect_response_cjk_max
LP-01,Chinese news query,微軟最近有什麼新聞？,zh,tavily_financial_search,true,0.20,1.0
LP-02,Chinese earnings query,蘋果公司最新的財報表現如何？,zh,,true,0.20,1.0
LP-03,English news query,What is the latest news about MSFT?,en,tavily_financial_search,true,0.0,0.02
LP-04,English performance query,How is AAPL performing recently?,en,tavily_financial_search,true,0.0,0.02
LP-05,Chinese price query,特斯拉現在股價多少？,zh,yfinance_stock_quote,true,0.20,1.0
LP-06,English price query,What is TSLA's current price?,en,yfinance_stock_quote,true,0.0,0.02
LP-07,Mixed lang query,NVDA 最近表現如何？,zh,,true,0.20,1.0
LP-08,Ticker-only prompt,GOOGL,en,,true,0.0,0.02
```

**Implementation Notes:**

- Task function 呼叫前先設定 `BraintrustCallbackHandler` 為 global handler，使 `Orchestrator` 內部的 `agent.invoke()` 自動被 Braintrust trace 捕捉（LLM calls、tool calls 均會記錄）
- Task function 每次呼叫都建立新的 `Orchestrator` instance（eval 執行頻率低，不需 cache）
- CSV 中的 `expect_tool` 空值代表「不指定預期 tool」，loader 轉為 `None`
- `id` 和 `description` 欄位不在 `column_mapping` 中，會被 loader 忽略（但保留在 CSV 中供人類閱讀）

**Verification:**

| Scope | Command | Expected Result | Why |
| ----- | ------- | --------------- | --- |
| Targeted | `python -c "from backend.evals.eval_tasks import run_v1; print(type(run_v1))"` | `<class 'function'>` | Task function 可 import |
| Config parse | `python -c "from backend.evals.scenario_config import load_scenario_config; from pathlib import Path; c = load_scenario_config(Path('backend/evals/scenarios/language_policy/eval_spec.yaml')); print(c.name)"` | `language_policy` | Scenario config 可載入 |

**Execution Checklist:**

- [ ] 建立 `backend/evals/scenarios/language_policy/` 目錄
- [ ] 建立 `dataset.csv`，從現有 `LANGUAGE_POLICY_CASES` 轉換
- [ ] 建立 `eval_spec.yaml`，定義 column mapping 和 scorer refs
- [ ] 實作 `backend/evals/eval_tasks.py`
- [ ] 驗證 config 可載入、CSV 可讀取、task function 可 import
- [ ] Commit: `git commit -m "feat(evals): add language policy CSV scenario and task function"`

---

### Task 6: Eval Runner（核心 orchestrator）

**Files:**

- Create: `backend/evals/eval_runner.py`
- Tests: `backend/tests/evals/test_eval_runner.py`

**What & Why:** 這是整個系統的核心——掃描 scenarios、組裝 Braintrust `Eval()`、輸出 result CSV。它把前面所有 component 串在一起。

**Critical Contract:**

```python
# backend/evals/eval_runner.py
"""Eval Runner: scenario discovery + Braintrust Eval() assembly + result CSV output.

Usage:
    python -m backend.evals.eval_runner language_policy
    python -m backend.evals.eval_runner --all
    python -m backend.evals.eval_runner language_policy --local-only
"""
import argparse
from pathlib import Path

SCENARIOS_DIR = Path(__file__).parent / "scenarios"
DEFAULT_RESULTS_DIR = Path(__file__).parent / "results"

def discover_scenarios(scenarios_dir: Path) -> list[str]:
    """掃描 scenarios/ 下有 eval_spec.yaml 的子目錄，回傳 scenario names。"""

def run_scenario(scenario_name: str, local_only: bool, output_dir: Path) -> None:
    """
    1. 載入 scenario config + CSV dataset
    2. 解析 scorers
    3. 呼叫 Braintrust Eval()
    4. 從 Eval() 結果寫 result CSV
    """

def write_result_csv(results, scenario_name: str, output_dir: Path) -> Path:
    """將 Eval() 結果寫入 {scenario}_{timestamp}.csv。"""

def main():
    """CLI entry point with argparse."""
```

**Implementation Notes:**

- `Eval()` 的 `data` 參數：傳入 `load_dataset()` 的結果
- `Eval()` 的 `task` 參數：動態 import config 中的 task function dotpath
- `Eval()` 的 `scores` 參數：`resolve_scorers()` 的結果
- `Eval()` 的 `no_send_logs` 參數：根據 `--local-only` flag 或 `braintrust_config.yaml` 的 `local_mode`
- Result CSV 從 `Eval()` 回傳的 `result.results` 取得每筆的 input/output/scores

**Test Strategy:**

- `discover_scenarios`：有效目錄結構 → 回傳 scenario names（happy path）
- `discover_scenarios`：空目錄 / 缺 eval_spec.yaml → 不回傳該目錄（edge case）
- `run_scenario` integration test：用 mock task + 小 CSV，`local_only=True`，驗證 result CSV 正確產出（happy path）
- `write_result_csv`：驗證 CSV 檔名格式和內容結構（happy path）

**Verification:**

| Scope | Command | Expected Result | Why |
| ----- | ------- | --------------- | --- |
| Targeted | `python -m pytest backend/tests/evals/test_eval_runner.py -v` | All tests pass | Runner 邏輯正確 |
| Discovery | `python -c "from backend.evals.eval_runner import discover_scenarios; from pathlib import Path; print(discover_scenarios(Path('backend/evals/scenarios')))"` | `['language_policy']` | Scenario discovery 正確 |

**Execution Checklist:**

- [ ] 🔴 撰寫 `backend/tests/evals/test_eval_runner.py` 測試（mock task function，`local_only=True`）
- [ ] 🔴 執行測試確認 **fail**（RED）
- [ ] 🟢 實作 `backend/evals/eval_runner.py`
- [ ] 🔵 Review + refactor，重跑測試確認 **pass**
- [ ] Commit: `git commit -m "feat(evals): add eval runner with scenario discovery and result CSV output"`

---

### Flow Verification: Local Eval 端對端流程

> Tasks 1-6 完成了本機 eval 的完整流程。以下驗證必須通過後才能繼續 Task 7。

| # | Method | Step | Expected Result |
| --- | --- | --- | --- |
| 1 | CLI | `python -m backend.evals.eval_runner language_policy --local-only` | 執行完成，terminal 顯示 eval summary（每個 scorer 的 pass/fail 統計） |
| 2 | File check | `ls backend/evals/results/language_policy_*.csv` | 存在一個 timestamped result CSV |
| 3 | File content | 打開 result CSV，檢查內容 | 包含 8 rows、原始 prompt + output + `score_tool_arg_no_cjk` + `score_response_language` 欄位 |
| 4 | Re-run | 再跑一次 `python -m backend.evals.eval_runner language_policy --local-only` | 產生第二個 result CSV（不覆蓋第一個） |

- [ ] All flow verifications pass

---

### Task 7: Braintrust Platform 整合

**Files:**

- Update: `backend/evals/eval_runner.py`（移除 `local_only` hardcode，接入 Braintrust config）

**What & Why:** 接通 Braintrust platform，讓 eval 結果上傳到 Braintrust 進行 experiment tracking。這是從「local-only」升級到「完整 Braintrust 整合」的最後一步。

**Implementation Notes:**

- Runner 讀取 `braintrust_config.yaml` 的 `project` 名稱作為 `Eval()` 的第一個參數
- 當 `local_only=False` 且 `BRAINTRUST_API_KEY` 環境變數存在時，`Eval()` 自動上傳到 Braintrust
- 執行成功後，terminal 會印出 Braintrust experiment URL

**Verification:**

| Scope | Command | Expected Result | Why |
| ----- | ------- | --------------- | --- |
| Targeted | `python -m backend.evals.eval_runner language_policy` | Terminal 輸出 Braintrust experiment URL | 確認上傳成功 |
| Braintrust UI | 打開 URL | Experiment 出現，可看到 8 個 test cases + scores | 確認資料完整 |

**Execution Checklist:**

- [ ] 確認 `BRAINTRUST_API_KEY` 環境變數已設定
- [ ] 更新 `runner.py`：讀取 `braintrust_config.yaml`，將 `project` 傳入 `Eval()`
- [ ] 執行 `python -m backend.evals.eval_runner language_policy`
- [ ] 確認 terminal 輸出 experiment URL
- [ ] 在 Braintrust UI 確認 experiment 資料完整
- [ ] Commit: `git commit -m "feat(evals): integrate braintrust platform for experiment tracking"`

---

### Task 8: Manual Braintrust Platform 全流程驗證

**What & Why:** 驗證完整的 prompt 迭代工作流程——修改參數後再跑一次 eval，在 Braintrust UI 上做 experiment diff，確認 per-case regression/improvement 可見。

**Prerequisites:**

- Braintrust 帳號已建立，project "finlab-x" 已存在
- `BRAINTRUST_API_KEY` 環境變數已設定
- Task 7 的 Braintrust 整合已完成

**Verification:**

| # | Method | Step | Expected Result |
| --- | --- | --- | --- |
| 1 | CLI | `python -m backend.evals.eval_runner language_policy` | Terminal 輸出 experiment URL (run 1) |
| 2 | Braintrust UI | 打開 URL → 點進任一 test case | 能看到完整 trace（input / output / tool calls） |
| 3 | Braintrust UI | 確認 scorer 分數 | 每個 scorer（`tool_arg_no_cjk`, `response_language`）分數獨立顯示 |
| 4 | CLI | 再跑一次 `python -m backend.evals.eval_runner language_policy` | Terminal 輸出新的 experiment URL (run 2) |
| 5 | Braintrust UI | 選 run 1 和 run 2 → 點 "Compare" | 能看到 experiment diff，顯示 per-case regression/improvement |
| 6 | File check | `ls backend/evals/results/` | 存在兩個 timestamped result CSVs |

- [ ] All manual verifications pass

**Execution Checklist:**

- [ ] 執行 run 1，記錄 experiment URL
- [ ] 在 Braintrust UI 驗證 trace drill-down 和 scorer breakdown
- [ ] 執行 run 2
- [ ] 在 Braintrust UI 驗證 experiment diff 功能
- [ ] 確認 result CSVs 正確產出
- [ ] 記錄驗證結果

---

## Pre-delivery Checklist

### Code Level (TDD)

- [ ] `python -m pytest backend/tests/evals/ -v` — all tests pass
- [ ] `python -m pytest backend/evals/test_language_policy.py -v -m eval` — 現有 pytest eval 仍然通過（未被破壞）
- [ ] `ruff check backend/evals/` — lint pass
- [ ] `pyright backend/evals/` — type check pass

### Flow Level (Behavioral)

- [ ] Flow: Local Eval 端對端 — PASS / FAIL
- [ ] Flow: Braintrust Platform 全流程 — PASS / FAIL

### Summary

- [ ] Both levels pass → ready for delivery
- [ ] Any failure is documented with cause and next action
