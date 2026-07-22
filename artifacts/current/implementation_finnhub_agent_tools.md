# Implementation Plan: 以 Finnhub Free-Tier API 抽換 Agent 的 Yahoo Finance 工具

> Design Reference: [design_finnhub_agent_tools.md](./design_finnhub_agent_tools.md)

**Goal:** 把 agent 端的 2 個 yfinance `@tool` 整個抽換成 3 個基於官方 `finnhub-python` SDK（free tier）的工具，並把所有 config / system prompt / docstring / eval / 既有測試裡的 `yfinance` / `Yahoo Finance` 名稱與 mock 改為 Finnhub。

**Architecture / Key Decisions:** 新增 `finnhub_client.py`（domain core：`get_finnhub_client` seam + `fetch_quote` / `fetch_basic_financials` + `BASIC_FINANCIALS_CATALOG`）與 `finnhub_tools.py`（3 個 `@tool`）。`financial.py` 移除 yfinance、保留 `tavily_financial_search`。Finnhub 對無效 ticker 不 raise（quote 回全 0、metric 回空 `{}`），client 層需自行判定並 `raise ValueError`。Citation 規則套用 DECISION-001（去 Yahoo URL 強制、改 provider-name 標註）。

**Tech Stack:** Python 3.12、uv、pytest、LangChain `@tool`（sync）、`finnhub-python` SDK。

---

## Dependencies Verification

| Dependency | Version | Source | What Was Verified | Notes |
| ---------- | ------- | ------ | ----------------- | ----- |
| finnhub-python | latest（`>=2.4.0`，pin 由 `uv add` 解析） | Context7 `/finnhub-stock-api/finnhub-python` | `finnhub.Client(api_key=...)`；`client.quote(symbol)` 回 `{c,d,dp,h,l,o,pc,t}`；`client.company_basic_financials(symbol, 'all')` 回 `{metric:{...}, series, metricType, symbol}`；exceptions `FinnhubAPIException`（含 `.status_code` / `.message` / `.response`）、`FinnhubRequestException` 皆在 `finnhub.exceptions`；429 走 `FinnhubAPIException(status_code=429)` | 簽章與 design 一致；無效 ticker **不** raise（quote 全 0 / metric 空），須 client 層判定 |
| yfinance | `>=1.2.0`（**保留不動**） | repo grep | `pyproject.toml` 仍宣告；唯一 runtime `import yfinance` 在 `financial.py`（本 PR 移除）。`ingestion/quant_data_pipeline/` 目前只在 comment / docstring / `schema.sql` 提到 yfinance（fetcher 子系統尚未實作），是**文件化的 owner** | 見 Constraints：**不移除** pyproject 的 yfinance dep |

## Constraints

- **不可動** `backend/ingestion/quant_data_pipeline/`（離線 ETL，獨立子系統，out of scope）。
- **`pyproject.toml` 的 `yfinance>=1.2.0` 必須保留**。理由：grep 確認 ingestion 是 yfinance 的 documented owner（`row_models.py` docstring、`schema.sql` 欄位註解、`README.md` 範例都以 yfinance 為來源），其 fetcher 子系統為 upcoming。即使目前無 runtime `import`，移除 dep 會破壞該子系統的既定意圖且超出本 PR 範圍。本 PR 只移除 **agent tool** 對 yfinance 的 `import` 與使用。
- `tavily_financial_search` **完全不動**（新聞工具，非 Yahoo）。
- 不加 retry / 自建 rate-limit；429 / 網路錯誤一律 bubble up 給既有 `_HandleToolErrors` middleware。
- 不加 `@observe()`（與既有 yfinance tool 對齊；遵守 `tools/README.md` 與 `agent_engine/README.md` 的 guardrail——只有需要 nested span / custom metadata 才加）。
- Forward P/E **移除**；保留 trailing `peTTM`。
- 所有 tool 一律 `raise`（非 return error dict），與 SEC tool 一致。

---

## File Plan

| Operation | Path | Purpose |
| --------- | ---- | ------- |
| Create | `backend/agent_engine/tools/finnhub_client.py` | domain core：`get_finnhub_client` seam、`fetch_quote`、`fetch_basic_financials`、`BASIC_FINANCIALS_CATALOG` |
| Create | `backend/agent_engine/tools/finnhub_tools.py` | 3 個 `@tool`：`finnhub_stock_quote` / `finnhub_company_basic_financials` / `finnhub_get_available_fields` |
| Create | `backend/tests/tools/test_finnhub_tools.py` | 涵蓋 client validation + 3 tool 的 schema / stream event / exception / missing key / ticker 正規化 |
| Update | `backend/agent_engine/tools/financial.py` | 移除 2 個 yfinance tool + `import yfinance`；保留 tavily |
| Update | `backend/agent_engine/tools/__init__.py` | `setup_tools()` 改 import + register 3 finnhub tool |
| Update | `backend/agent_engine/tools/README.md` | 文件 yfinance → Finnhub（`financial.py` 描述） |
| Update | `backend/agent_engine/README.md` | yfinance → Finnhub（Components / config 範例） |
| Update | `backend/agent_engine/agents/base.py` | `_DEFAULT_SYSTEM_PROMPT` citation 範例 + budget 訊息：Yahoo Finance → Finnhub（純改名） |
| Update | `backend/agent_engine/agents/versions/v1_baseline/orchestrator_config.yaml` | tools list yfinance → finnhub（3 個） |
| Update | `backend/agent_engine/agents/versions/v2_reader/orchestrator_config.yaml` | 同上 |
| Update | `backend/agent_engine/agents/versions/v3_quant/orchestrator_config.yaml` | 同上（保留 duckdb/text_to_sql） |
| Update | `backend/agent_engine/agents/versions/v4_graph/orchestrator_config.yaml` | 同上（保留 neo4j/text_to_cypher） |
| Update | `backend/agent_engine/agents/versions/v5_analyst/orchestrator_config.yaml` | 同上（保留全部其他 tool） |
| Update | `backend/agent_engine/agents/versions/v1_baseline/system_prompt.md` | 套用 DECISION-001：去 Yahoo URL 強制、改 provider-name；移除 forwardPE；改 Finnhub 欄位範例 |
| Update | `backend/agent_engine/streaming/tool_error_sanitizer.py` | docstring 範例 `'yfinance API timeout'` → `'Finnhub API timeout'` |
| Update | `backend/evals/datasets/language_policy.py` | LP-05/LP-06 `expect_tool` yfinance → finnhub |
| Update | `backend/evals/scenarios/language_policy/dataset.csv` | LP-05/LP-06 `expect_tool` yfinance → finnhub |
| Update | `backend/tests/tools/test_financial.py` | 移除 yfinance 測試，保留 tavily |
| Update | `backend/tests/tools/test_observe_decorators.py` | tool / schema 名稱改 finnhub |
| Update | `backend/tests/agents/test_base.py` | tools 字串 yfinance → finnhub |
| Update | `backend/tests/agents/test_orchestrator_prompt_rendering.py` | `_V1_BASELINE_TOOLS` + 單例 config 字串改 finnhub |
| Update | `backend/tests/integration/test_v1_integration.py` | mock tool name + config 斷言改 finnhub |
| Update | `backend/tests/api/test_e2e.py` | mock tool_call name 改 finnhub |
| Update | `backend/tests/evals/test_scorer_registry.py` | tool 字串改 finnhub |
| Update | `backend/tests/streaming/test_tool_error_sanitizer.py` | traceback 範例字串改 Finnhub |
| Update | `backend/tests/streaming/test_sse_serializer.py` | （cosmetic）`tool_name="yfinance"` → `"finnhub_stock_quote"` |
| Update | `backend/tests/streaming/test_domain_events_schema.py` | （cosmetic）`tool_name="yfinance"` → `"finnhub_stock_quote"` |
| Update | `pyproject.toml` | **加** `finnhub-python`；**保留** `yfinance>=1.2.0`；加 pytest marker `finnhub_integration`（預設排除） |
| Update | `.env.example`（若存在）+ 提醒 user `.env` | 新增 `FINNHUB_API_KEY`（user 提供 key） |

**結構草圖**（新增檔案）：

```text
backend/agent_engine/tools/
  finnhub_client.py      # domain core (no @tool)
  finnhub_tools.py       # 3 @tool, depend on finnhub_client
backend/tests/tools/
  test_finnhub_tools.py  # client validation + 3 tool tests
```

---

### Checkpoint dependency ordering

```text
CP1 (core, sequential) ──► CP2 (financial.py + setup_tools)
        │                          │
        │                          ▼
        └──────────────► CP3 (parallelizable: configs / prompt / base.py / sanitizer / READMEs / evals)
                                   │
                                   ▼
                            CP4 (fix existing tests)
                                   │
                                   ▼
                            CP5 (full suite green + live marker)
```

- CP1 必須先完成（其餘都依賴新工具存在）。
- CP2 依賴 CP1（要 import 新工具來 register）。
- CP3 可在 CP2 完成後開始；CP3 內部多數 task 互為 disjoint files，可平行（見各 task 標註）。
- CP4 依賴 CP2 + CP3（測試斷言對應改名後的工具與 prompt）。
- CP5 是收尾驗證。

---

## Task 1 (Checkpoint 1): finnhub-python 依賴 + finnhub_client.py + finnhub_tools.py（core，sequential）

**Files:**

- Create: `backend/agent_engine/tools/finnhub_client.py`
- Create: `backend/agent_engine/tools/finnhub_tools.py`
- Create (Tests): `backend/tests/tools/test_finnhub_tools.py`
- Update: `pyproject.toml`（加 `finnhub-python`、加 marker；**不動 yfinance**）

**What & Why:** 這是整個 PR 的地基——新工具不存在前，後面所有改名都沒有目標。把 client（validation + catalog）與 tool（schema + stream event）拆兩個檔，client 是純 domain core 易 mock，tool 沿用既有 LangChain `@tool` 慣例。

**Approach Decision:**

| Option | Summary | Status | Why |
| ------ | ------- | -------- | -------- |
| A | client 與 tool 拆兩檔（`finnhub_client.py` + `finnhub_tools.py`） | Selected | client 無 LangChain 依賴、純函式好測；`get_finnhub_client` 是 patch seam；catalog 單一 source of truth 供 tool 2 / tool 3 共用 |
| B | 全部塞進 `financial.py` | Rejected | `financial.py` 已有 tavily；混在一起違反單一責任、且 mock 範圍變大 |

**Implementation Notes:**

- `get_finnhub_client()` 在 **call time** 讀 `FINNHUB_API_KEY`（不是 import time），讓測試能 patch、且 missing key 只在實際呼叫工具時才失敗。
- `fetch_quote`：無效 ticker → Finnhub 回全 0（`{c:0, pc:0, ...}`）→ 判定 `c in (0, None) and pc in (0, None)` 時 `raise ValueError`。
- `fetch_basic_financials`：回 `data['metric']`；空 `{}` → `raise ValueError`。
- 3 個 tool 都：`try/except` 取 `get_stream_writer()`（容錯成 `None`）、`ticker.strip().upper()` 正規化、回 `dict[str, Any]`、不加 `@observe()`。
- tool 2 / tool 3 共用 `BASIC_FINANCIALS_CATALOG`：tool 2 取值（present-only），tool 3 取描述 + availability。
- **mock 策略**：測試 patch `backend.agent_engine.tools.finnhub_client.get_finnhub_client` 這個 seam，回傳一個 `MagicMock`，其 `.quote(...)` / `.company_basic_financials(...)` 設好 `return_value`。**不要** patch `finnhub.Client`（SDK 內部建構不需驗證）。

**Critical Contract / Snippet:**

`finnhub_client.py` 的 catalog 型別與函式骨架（output key → (Finnhub metric key, 中性英文描述)）：

```python
import os
from typing import Any, NamedTuple

import finnhub


class FieldSpec(NamedTuple):
    metric_key: str
    description: str


# output key -> (Finnhub `metric` key, neutral English description)
BASIC_FINANCIALS_CATALOG: dict[str, FieldSpec] = {
    "fiftyTwoWeekHigh": FieldSpec("52WeekHigh", "52-week high price"),
    "fiftyTwoWeekLow": FieldSpec("52WeekLow", "52-week low price"),
    "peTTM": FieldSpec("peTTM", "Trailing twelve-month P/E ratio"),
    "psTTM": FieldSpec("psTTM", "Trailing twelve-month price-to-sales"),
    "pb": FieldSpec("pbQuarterly", "Price-to-book ratio"),
    "marketCap": FieldSpec("marketCapitalization", "Market capitalization (USD millions)"),
    "beta": FieldSpec("beta", "Beta coefficient"),
    "epsTTM": FieldSpec("epsTTM", "Earnings per share (TTM)"),
    "roeTTM": FieldSpec("roeTTM", "Return on equity (TTM)"),
    "roaTTM": FieldSpec("roaTTM", "Return on assets (TTM)"),
    "netProfitMarginTTM": FieldSpec("netProfitMarginTTM", "Net profit margin (TTM)"),
    "operatingMarginTTM": FieldSpec("operatingMarginTTM", "Operating margin (TTM)"),
    "currentRatio": FieldSpec("currentRatioQuarterly", "Current ratio"),
    "quickRatio": FieldSpec("quickRatioQuarterly", "Quick ratio"),
    "debtToEquity": FieldSpec("totalDebt/totalEquityQuarterly", "Debt-to-equity ratio"),
    "dividendYield": FieldSpec("dividendYieldIndicatedAnnual", "Indicated annual dividend yield"),
    "revenueGrowthTTMYoy": FieldSpec("revenueGrowthTTMYoy", "Revenue growth (TTM YoY)"),
    "epsGrowthTTMYoy": FieldSpec("epsGrowthTTMYoy", "EPS growth (TTM YoY)"),
    "tenDayAvgVolume": FieldSpec("10DayAverageTradingVolume", "10-day average trading volume"),
}


def get_finnhub_client() -> finnhub.Client:
    api_key = os.getenv("FINNHUB_API_KEY")
    if not api_key:
        raise ValueError("FINNHUB_API_KEY is not set.")
    return finnhub.Client(api_key=api_key)


def fetch_quote(symbol: str) -> dict[str, Any]:
    data = get_finnhub_client().quote(symbol)
    if not data or (data.get("c") in (0, None) and data.get("pc") in (0, None)):
        raise ValueError(
            f"No quote data for ticker '{symbol}'. The symbol may be invalid, "
            f"delisted, or not covered by Finnhub free tier."
        )
    return data


def fetch_basic_financials(symbol: str) -> dict[str, Any]:
    data = get_finnhub_client().company_basic_financials(symbol, "all")
    metric = (data or {}).get("metric") or {}
    if not metric:
        raise ValueError(
            f"No basic financials for ticker '{symbol}'. The symbol may be "
            f"invalid or not covered by Finnhub free tier."
        )
    return metric
```

`finnhub_tools.py` 的 3 個 tool 形狀（output schema 對應 design）：

```python
from typing import Annotated, Any

from langchain_core.tools import InjectedToolCallId
from langchain.tools import tool
from langgraph.config import get_stream_writer
from pydantic import BaseModel, Field

from backend.agent_engine.tools.finnhub_client import (
    BASIC_FINANCIALS_CATALOG,
    fetch_basic_financials,
    fetch_quote,
)


class FinnhubStockQuoteInput(BaseModel):
    ticker: str = Field(..., description="Stock ticker symbol (e.g., AAPL, TSLA)")


@tool("finnhub_stock_quote", args_schema=FinnhubStockQuoteInput)
def finnhub_stock_quote(
    ticker: str,
    tool_call_id: Annotated[str, InjectedToolCallId],
) -> dict[str, Any]:
    """Retrieve real-time stock quote (price, open, prev close, change, day high/low) via Finnhub."""
    try:
        writer = get_stream_writer()
    except Exception:
        writer = None
    t = ticker.strip().upper()
    if writer:
        writer({"status": "querying_stock", "message": f"Querying {t}...",
                "toolName": "finnhub_stock_quote", "toolCallId": tool_call_id})
    q = fetch_quote(t)
    return {
        "ticker": t,
        "currentPrice": q.get("c"),
        "open": q.get("o"),
        "previousClose": q.get("pc"),
        "change": q.get("d"),
        "percentChange": q.get("dp"),
        "dayHigh": q.get("h"),
        "dayLow": q.get("l"),
    }


class FinnhubCompanyBasicFinancialsInput(BaseModel):
    ticker: str = Field(..., description="Stock ticker symbol (e.g., AAPL, TSLA)")


@tool("finnhub_company_basic_financials", args_schema=FinnhubCompanyBasicFinancialsInput)
def finnhub_company_basic_financials(
    ticker: str,
    tool_call_id: Annotated[str, InjectedToolCallId],
) -> dict[str, Any]:
    """Retrieve curated company fundamentals (52wk H/L, peTTM, marketCap, beta, ROE, margins...) via Finnhub."""
    try:
        writer = get_stream_writer()
    except Exception:
        writer = None
    t = ticker.strip().upper()
    if writer:
        writer({"status": "querying_financials", "message": f"Querying financials for {t}...",
                "toolName": "finnhub_company_basic_financials", "toolCallId": tool_call_id})
    metric = fetch_basic_financials(t)
    out: dict[str, Any] = {"ticker": t}
    for out_key, spec in BASIC_FINANCIALS_CATALOG.items():
        if spec.metric_key in metric and metric[spec.metric_key] is not None:
            out[out_key] = metric[spec.metric_key]
    return out


class FinnhubGetAvailableFieldsInput(BaseModel):
    ticker: str = Field(..., description="Stock ticker symbol to query available fields")


@tool("finnhub_get_available_fields", args_schema=FinnhubGetAvailableFieldsInput)
def finnhub_get_available_fields(
    ticker: str,
    tool_call_id: Annotated[str, InjectedToolCallId],
) -> dict[str, Any]:
    """Discover which curated fundamental fields Finnhub actually has for this ticker."""
    try:
        writer = get_stream_writer()
    except Exception:
        writer = None
    t = ticker.strip().upper()
    if writer:
        writer({"status": "querying_fields", "message": f"Discovering fields for {t}...",
                "toolName": "finnhub_get_available_fields", "toolCallId": tool_call_id})
    metric = fetch_basic_financials(t)
    available: dict[str, Any] = {}
    for out_key, spec in BASIC_FINANCIALS_CATALOG.items():
        if spec.metric_key in metric and metric[spec.metric_key] is not None:
            available[out_key] = {"description": spec.description, "available": True}
    return {"ticker": t, "available_fields": available, "total_fields": len(available)}
```

> 注意：`finnhub_get_available_fields` 用 `fetch_basic_financials`（會在 metric 空時 raise ValueError），語意 = 「此 ticker 實際有哪些 curated 欄位」。

`pyproject.toml` marker 新增（保持既有 `addopts` 風格，預設排除 live marker）：

```toml
markers = [
    "eval: evaluation tests that hit real LLM APIs",
    "integration: integration tests requiring external services (Qdrant, etc.)",
    "sec_integration: SEC integration tests that hit real SEC EDGAR APIs",
    "finnhub_integration: Finnhub integration tests that hit the real Finnhub free API",
]
addopts = "-m 'not eval and not sec_integration and not integration and not finnhub_integration'"
```

**Test Strategy:** `test_finnhub_tools.py` 用 `_tool_call()` helper（複製自 `test_financial.py`：傳完整 `tool_call` dict 以滿足 `InjectedToolCallId`，回 `json.loads(msg.content)`），patch seam `backend.agent_engine.tools.finnhub_client.get_finnhub_client`。新增測試證明：

- `finnhub_stock_quote` happy path：mock `.quote()` 回 `{c,o,pc,d,dp,h,l,t}`，斷言 output 7 個欄位映射正確、`ticker` 已 upper。（happy）
- `finnhub_stock_quote` 無效 ticker：mock `.quote()` 回全 0 → `pytest.raises(ValueError, match="invalid")`。（failure path——design 核心風險）
- `finnhub_company_basic_financials` happy path + present-only：mock metric 只含部分 key（含一個值為 `None`），斷言只輸出 present 且非 None 的 catalog 欄位、缺的不出現。（happy + edge）
- `finnhub_company_basic_financials` 空 metric：mock 回 `{"metric": {}}` → `raise ValueError`。（failure）
- `finnhub_get_available_fields`：mock metric 含 2 個 key → `available_fields` 只列那 2 個且帶 description/available、`total_fields == 2`。（happy）
- missing API key：`patch.dict(os.environ, {}, clear=True)` 且**不**patch seam（讓真實 `get_finnhub_client` 跑）→ `pytest.raises(ValueError, match="FINNHUB_API_KEY")`。（failure）
- ticker 正規化：傳 `"aapl"` → `.quote("AAPL")`（用 mock 的 `assert_called_once_with("AAPL")`）。（edge）
- 無 stream writer：不 patch `get_stream_writer`（在非 streaming context 會丟 exception，工具須容錯）→ 仍正常回 dict。（regression：對齊既有 `test_tools_work_without_stream_writer`）

**Verification:**

| Scope | Command | Expected Result | Why |
| ----- | ------- | --------------- | --- |
| 依賴安裝 | `uv add finnhub-python` | `pyproject.toml` 新增 dep、`uv.lock` 更新、`uv pip list \| grep finnhub` 有輸出 | 工具可 import |
| Targeted | `uv run pytest backend/tests/tools/test_finnhub_tools.py -v` | 全部 pass（先確認 RED 再 GREEN） | 證明 3 tool + client validation 正確 |
| Import 健全性 | `uv run python -c "from backend.agent_engine.tools.finnhub_tools import finnhub_stock_quote, finnhub_company_basic_financials, finnhub_get_available_fields; print('ok')"` | 印出 `ok` | 無 import error |

**Execution Checklist:**

- [ ] `uv add finnhub-python`，並手動編輯 `pyproject.toml` 加 `finnhub_integration` marker + 更新 `addopts`（**保留 `yfinance>=1.2.0` 不動**）
- [ ] 🔴 撰寫 `test_finnhub_tools.py` 全部測試（含 client + 3 tool）
- [ ] 🔴 跑 `uv run pytest backend/tests/tools/test_finnhub_tools.py` 確認 **fail**（檔案尚未建立 → ImportError / 測試紅）
- [ ] 🟢 建立 `finnhub_client.py` + `finnhub_tools.py`，最小實作讓測試通過
- [ ] 🔵 檢視重複（catalog 迴圈邏輯 tool2/tool3 抽共用 helper 視情況）、跑測試確認仍 pass
- [ ] Commit：`git commit -m "feat(finnhub-tools): add finnhub_client + 3 agent tools on finnhub-python SDK"`

---

## Task 2 (Checkpoint 2): financial.py 移除 yfinance + setup_tools() register 3 finnhub tool

**Files:**

- Update: `backend/agent_engine/tools/financial.py`
- Update: `backend/agent_engine/tools/__init__.py`

**What & Why:** 把舊工具從 codebase 真正移除，並讓 registry 改 register 新工具。完成後 registry 只認得 finnhub 名稱，舊名稱查不到。

**Implementation Notes:**

- `financial.py`：刪除 `import yfinance as yf`、`YFinanceStockQuoteInput`、`yfinance_stock_quote`、`YFinanceGetAvailableFieldsInput`、`yfinance_get_available_fields`。保留 `TRUSTED_NEWS_DOMAINS`、`TavilyFinancialSearchInput`、`tavily_financial_search` 一字不動。
- `__init__.py` `setup_tools()`：
  - import 從 `financial` 只留 `tavily_financial_search`；新增 `from backend.agent_engine.tools.finnhub_tools import (finnhub_company_basic_financials, finnhub_get_available_fields, finnhub_stock_quote)`。
  - `register_tool` 改 3 行 finnhub：`register_tool("finnhub_stock_quote", finnhub_stock_quote)`、`register_tool("finnhub_company_basic_financials", finnhub_company_basic_financials)`、`register_tool("finnhub_get_available_fields", finnhub_get_available_fields)`，保留 tavily + 3 個 SEC register。

**Critical Contract / Snippet:** `setup_tools()` register 區塊改後形狀：

```python
register_tool("finnhub_stock_quote", finnhub_stock_quote)
register_tool("finnhub_company_basic_financials", finnhub_company_basic_financials)
register_tool("finnhub_get_available_fields", finnhub_get_available_fields)
register_tool("tavily_financial_search", tavily_financial_search)
register_tool("sec_filing_list_sections", sec_filing_list_sections)
register_tool("sec_filing_get_section", sec_filing_get_section)
register_tool("sec_filing_downloader", sec_filing_downloader)
```

**Test Strategy:** 本 task 不新增測試（行為由 Task 1 的工具測試 + Task 4 改後的既有測試覆蓋）。用 runtime 驗證 registry 狀態。

**Verification:**

| Scope | Command | Expected Result | Why |
| ----- | ------- | --------------- | --- |
| Registry 內容 | `uv run python -c "from backend.agent_engine.tools import setup_tools; from backend.agent_engine.tools.registry import list_registered_tools; setup_tools(); n=list_registered_tools(); assert 'finnhub_stock_quote' in n and 'finnhub_company_basic_financials' in n and 'finnhub_get_available_fields' in n and 'yfinance_stock_quote' not in n, n; print('ok')"` | 印出 `ok` | 證明改名 register 生效、舊名稱已移除 |
| 殘留 import | `! grep -rn "yfinance" backend/agent_engine/tools/financial.py backend/agent_engine/tools/__init__.py` | 無輸出（grep 無命中） | 證明 agent tool 已無 yfinance |
| tavily 未壞 | `uv run pytest backend/tests/tools/test_financial.py::test_tavily_tool_exists -v`（此測試在 Task 4 仍保留） | pass | 確認 tavily 仍可 import |

> 注意：此時 `test_financial.py` 仍 import 舊 yfinance 名稱會 ImportError——預期，於 Task 4（CP4）修。CP2 結束時跑全測試會紅，這是計畫內順序。

**Execution Checklist:**

- [ ] 🟢 編輯 `financial.py` 移除 yfinance 區塊（保留 tavily）
- [ ] 🟢 編輯 `__init__.py` 改 import + register
- [ ] 執行上方 Registry 內容 + 殘留 import 驗證命令，皆通過
- [ ] Commit：`git commit -m "refactor(tools): drop yfinance agent tools, register finnhub tools in setup_tools"`

---

## Task 3 (Checkpoint 3): config / prompt / base.py / sanitizer / READMEs / evals 改名（可平行）

> CP3 內各 sub-task 多為 disjoint files，可平行執行。下方 **[P]** = 可與其他 [P] 並行；**[S-prompt]** 為唯一含產品語意（DECISION-001）的 task，建議單獨 review。

**Files & parallel grouping:**

- **3a [P]** Update: 5 個 `orchestrator_config.yaml`（v1–v5）
- **3b [S-prompt]** Update: `backend/agent_engine/agents/versions/v1_baseline/system_prompt.md`（DECISION-001）
- **3c [P]** Update: `backend/agent_engine/agents/base.py`（`_DEFAULT_SYSTEM_PROMPT` + budget 訊息）
- **3d [P]** Update: `backend/agent_engine/streaming/tool_error_sanitizer.py`（docstring only）
- **3e [P]** Update: `backend/agent_engine/tools/README.md` + `backend/agent_engine/README.md`
- **3f [P]** Update: `backend/evals/datasets/language_policy.py` + `backend/evals/scenarios/language_policy/dataset.csv`

**What & Why:** 把所有「指向舊工具名 / Yahoo」的非測試 production 文字改成 Finnhub。除 3b 外皆機械式改名（語意不變）。

### 3a — v1–v5 orchestrator_config.yaml [P]

每個 config 的 tools list 把：

```yaml
  - yfinance_stock_quote
  - yfinance_get_available_fields
```

改為：

```yaml
  - finnhub_stock_quote
  - finnhub_company_basic_financials
  - finnhub_get_available_fields
```

其餘 tool（tavily / sec / duckdb / neo4j / text_to_*）順序與內容**不動**。注意 v2–v5 檔頭有 placeholder NOTE 註解，保留。

### 3b — v1_baseline/system_prompt.md [S-prompt]（DECISION-001，唯一產品決策）

需改 4 處（其餘段落不動）：

1. **CITATION REQUIREMENTS** 區塊：
   - `Cite sources by tool name (e.g., "According to yfinance data...")` → `... (e.g., "According to Finnhub real-time quote data...")`
   - **刪除**整條「When a claim is based on yfinance tool output ... MUST also include the canonical Yahoo Finance quote page ... `https://finance.yahoo.com/quote/TICKER` ... yfinance-backed claims never ship without a Yahoo Finance reference.」（DECISION-001：free tier 無 per-ticker 公開頁，硬編 URL 違反 zero-hallucination）。
   - 新增一條（取代上條精神）：`- Real-time quote / fundamentals claims are cited by data provider name ("According to Finnhub..."). Finnhub free tier has no public per-ticker page — do NOT fabricate a per-ticker URL. URLs are only required for sources that genuinely have one (Tavily news, SEC filings).`
2. **LINK FORMAT** 區塊：**刪除**最後一條「When data comes only from yfinance, the references section MUST still contain the Yahoo Finance quote URL for each cited ticker」。其餘 `[N]` inline citation 規則（給 Tavily / SEC 用）保留。
3. **EXAMPLES → Example 1**：
   - 標題去 Yahoo：`Example 1 — English query, stock quote from Finnhub:`
   - 表格移除 `Forward P/E Ratio` 列（free tier 無）；可保留 `Trailing P/E Ratio`、52-week H/L。
   - **刪除** `[1]` inline marker 與底部 `[1]: https://finance.yahoo.com/quote/AAPL ...` reference（Finnhub quote 無 URL）。範例改成：以 provider-name 文字標註，不帶 `[1]`。
   - tool call 範例名稱：`yfinance_stock_quote` → `finnhub_stock_quote`。
4. **Example 2**：`yfinance_stock_quote(ticker="TSM")` → `finnhub_stock_quote(ticker="TSM")`（tavily 部分不動；此例的 `[1][2]` 是 tavily 新聞 URL，保留）。

> 改完後**人工確認**：(a) prompt 內不再出現 `yahoo` / `forwardPE` / `forward P/E`；(b) `[N]` 規則只服務真正有 URL 的來源；(c) 無孤兒 `[1]:` reference 沒有對應 inline。

### 3c — base.py [P]

- `_DEFAULT_SYSTEM_PROMPT`：
  - CITATION：`(e.g., "According to yfinance data...")` → `(e.g., "According to Finnhub data...")`
  - TOOL CALL BUDGET：`it is NOT an external rate limit from SEC, Yahoo Finance, Tavily, or any other external API.` → `... from SEC, Finnhub, Tavily, or any other external API.`
- `RunBudgetMiddleware._budget_message`：docstring 內 `real SEC / Yahoo / Tavily 429` → `real SEC / Finnhub / Tavily 429`；回傳字串中 `external rate limit from SEC EDGAR, Yahoo Finance, Tavily,` → `... from SEC EDGAR, Finnhub, Tavily,`。

### 3d — tool_error_sanitizer.py [P]

docstring 範例 `(e.g., 'yfinance API timeout')` → `(e.g., 'Finnhub API timeout')`。**程式邏輯不動**。

### 3e — READMEs [P]

- `tools/README.md` Map 區塊：`financial.py: Implements tools for quantitative data retrieval via yfinance and ...` → `... via Finnhub and event-driven news search via Tavily.`
- `agent_engine/README.md`：
  - Components：`Tools: Atomic, stateless functions (yfinance, Tavily, SEC)` → `(Finnhub, Tavily, SEC)`。
  - 兩處 `print(config.tools)` 範例註解 `['yfinance_stock_quote', 'yfinance_get_available_fields', ...]` → `['finnhub_stock_quote', 'finnhub_company_basic_financials', ...]`。

### 3f — eval dataset [P]

- `language_policy.py`：LP-05 與 LP-06 的 `expect_tool="yfinance_stock_quote"` → `expect_tool="finnhub_stock_quote"`（其餘欄位不動）。
- `dataset.csv`：第 6、7 行（LP-05 / LP-06）`expect_tool` 欄 `yfinance_stock_quote` → `finnhub_stock_quote`。

**Test Strategy:** 本 task 無新測試。3b 的 prompt 正確性由 CP4 的 `test_orchestrator_prompt_rendering.py`（已有「advertises SEC tools」「無 yfinance 殘留」類斷言）+ 人工 review 把關；CP5 加一條斷言確保 prompt 無 `yahoo` / `forwardPE`（見 Task 4 注記）。

**Verification:**

| Scope | Command | Expected Result | Why |
| ----- | ------- | --------------- | --- |
| config 改名完整 | `! grep -rn "yfinance" backend/agent_engine/agents/versions/` | 無輸出 | 5 個 yaml 都改完 |
| prompt 去 Yahoo | `! grep -rniE "yahoo\|forwardpe\|forward p/e\|yfinance" backend/agent_engine/agents/versions/v1_baseline/system_prompt.md` | 無輸出 | DECISION-001 落實、forwardPE 移除 |
| production 文字無 yfinance | `! grep -rn "yfinance\|Yahoo Finance" backend/agent_engine/agents/base.py backend/agent_engine/streaming/tool_error_sanitizer.py backend/agent_engine/README.md backend/agent_engine/tools/README.md` | 無輸出 | base/sanitizer/READMEs 改完 |
| eval 改名 | `! grep -rn "yfinance" backend/evals/` | 無輸出 | LP-05/06 改完 |
| config 仍可載入 | `uv run python -c "from backend.agent_engine.agents.config_loader import VersionConfigLoader; c=VersionConfigLoader('v1_baseline').load(); assert 'finnhub_stock_quote' in c.tools and 'yfinance_stock_quote' not in c.tools; print('ok')"` | 印出 `ok` | YAML 結構未壞 |

**Execution Checklist:**

- [ ] 3a 改 5 個 yaml（[P]）
- [ ] 3b 改 v1 system_prompt 套 DECISION-001（[S-prompt]，單獨小心 review）
- [ ] 3c 改 base.py（[P]）
- [ ] 3d 改 sanitizer docstring（[P]）
- [ ] 3e 改兩個 README（[P]）
- [ ] 3f 改 eval .py + .csv（[P]）
- [ ] 跑上方 5 條 grep / load 驗證，全綠
- [ ] Commit：`git commit -m "refactor(agent): rename yfinance->finnhub in configs, prompt, docs, evals (DECISION-001 citations)"`

---

## Task 4 (Checkpoint 4): 修既有測試的 yfinance 名稱 / mock

**Files:**

- Update: `backend/tests/tools/test_financial.py`
- Update: `backend/tests/tools/test_observe_decorators.py`
- Update: `backend/tests/agents/test_base.py`
- Update: `backend/tests/agents/test_orchestrator_prompt_rendering.py`
- Update: `backend/tests/integration/test_v1_integration.py`
- Update: `backend/tests/api/test_e2e.py`
- Update: `backend/tests/evals/test_scorer_registry.py`
- Update: `backend/tests/streaming/test_tool_error_sanitizer.py`
- Update (cosmetic): `backend/tests/streaming/test_sse_serializer.py`、`backend/tests/streaming/test_domain_events_schema.py`

**What & Why:** CP2 之後既有測試會因 import 不到舊工具 / 斷言舊名稱而紅。逐檔對齊到 finnhub。

**Implementation Notes:**

- **`test_financial.py`**：移除所有 `yfinance_*` import 與全部 yfinance 測試函式（`test_yfinance_*`、`test_ticker_normalization_uppercase`、`test_tools_work_without_stream_writer` 中 yfinance 版本——後者的等價 case 已搬到 `test_finnhub_tools.py`）。**保留** `_tool_call` helper、`test_tavily_tool_exists`、`test_tavily_financial_search_missing_api_key`、`test_tavily_financial_search_results`、`TRUSTED_NEWS_DOMAINS` import。改後此檔只剩 tavily 測試。
- **`test_observe_decorators.py`**：
  - import 改 `from backend.agent_engine.tools.finnhub_tools import (finnhub_company_basic_financials, finnhub_get_available_fields, finnhub_stock_quote)`，`financial` 只留 `tavily_financial_search`。
  - `TOOLS_WITHOUT_OBSERVE` 改放 3 個 finnhub tool + tavily。
  - `test_all_tools_have_valid_schema` 的 `expected_schemas`：移除兩個 `YFinance*`，加 `"finnhub_stock_quote": "FinnhubStockQuoteInput"`、`"finnhub_company_basic_financials": "FinnhubCompanyBasicFinancialsInput"`、`"finnhub_get_available_fields": "FinnhubGetAvailableFieldsInput"`、`"tavily_financial_search": "TavilyFinancialSearchInput"`（SEC 維持）。
- **`test_base.py`**：`tools=["yfinance_stock_quote"]`（2 處）+ `mock_tool.name = "yfinance_stock_quote"` → `finnhub_stock_quote`。
- **`test_orchestrator_prompt_rendering.py`**：
  - `_V1_BASELINE_TOOLS` 改為 `["finnhub_stock_quote", "finnhub_company_basic_financials", "finnhub_get_available_fields", "tavily_financial_search", "sec_filing_list_sections", "sec_filing_get_section"]`（注意：原本 2 個 yfinance → 3 個 finnhub，list 長度 +1；`EXPECTED_TOOLS_BY_VERSION` 自動沿用）。
  - `test_validate_edgar_identity_skipped_when_no_sec_tool` 內 `SimpleNamespace(tools=["yfinance_stock_quote"])` → `finnhub_stock_quote`。
  - **新增**一條斷言（落實 3b review）：讀 `V1_BASELINE_PROMPT_PATH.read_text()` 斷言 `"yahoo" not in text.lower()` 且 `"forwardpe" not in text.lower()` 且 `"yfinance" not in text.lower()`。
- **`test_v1_integration.py`**：所有 `yfinance_stock_quote` / `yfinance_get_available_fields` mock name / tool_call name / `config.tools` 斷言 → finnhub 對應名。`test_yfinance_tool_integration` 函式名改 `test_finnhub_tool_integration`、內部用 `finnhub_get_available_fields`。`assert "yfinance_stock_quote" in config.tools` → `finnhub_stock_quote`。
- **`test_e2e.py`**：mock tool_call 的 `"name": "yfinance_stock_quote"`（2 處）→ `finnhub_stock_quote`。
- **`test_scorer_registry.py`**：`"tool": "yfinance_stock_quote"`（2 處）→ `finnhub_stock_quote`。
- **`test_tool_error_sanitizer.py`**：traceback 範例字串 `tools/yfinance.py` 與 `yfinance API timeout`（3 處 assert）→ `Finnhub API timeout`（path 改 `tools/finnhub_client.py`）。邏輯斷言不變。
- **`test_sse_serializer.py` / `test_domain_events_schema.py`**（cosmetic）：`tool_name="yfinance"` 是泛用佔位字串、與真實工具名無耦合；為一致性改 `"finnhub_stock_quote"`（含 `toolName` 斷言）。非功能必需，但避免 reviewer 誤會殘留。

**Test Strategy:** 本 task 不新增「行為」測試，是把既有測試的「期望值」對齊改名後的真相；唯一新增的實質斷言是 prompt 去 Yahoo/forwardPE（保護 DECISION-001 不被回退）。

**Verification:**

| Scope | Command | Expected Result | Why |
| ----- | ------- | --------------- | --- |
| 各改動檔 | `uv run pytest backend/tests/tools/test_financial.py backend/tests/tools/test_observe_decorators.py backend/tests/agents/test_base.py backend/tests/agents/test_orchestrator_prompt_rendering.py -v` | 全 pass | tool / schema / prompt 斷言對齊 |
| 整合 + e2e + eval + streaming | `uv run pytest backend/tests/integration/test_v1_integration.py backend/tests/api/test_e2e.py backend/tests/evals/test_scorer_registry.py backend/tests/streaming/ -v` | 全 pass | mock name / sanitizer / event 對齊 |
| 全 repo 無 yfinance 殘留（測試層） | `grep -rn "yfinance" backend/tests/` | 無輸出 | 測試已全面改名 |

**Execution Checklist:**

- [ ] 🔴 先跑 `uv run pytest backend/tests/ -q` 確認目前因 CP2 紅（ImportError / 名稱不符）——記錄哪些紅
- [ ] 🟢 逐檔改名 / 改 mock（依 Implementation Notes 順序）
- [ ] 🟢 在 `test_orchestrator_prompt_rendering.py` 新增 prompt 去 Yahoo/forwardPE 斷言
- [ ] 🔵 跑上方兩組 pytest，全綠
- [ ] `grep -rn "yfinance" backend/tests/` 確認無殘留（cosmetic 兩檔也改完）
- [ ] Commit：`git commit -m "test(finnhub): align existing tests to finnhub tool names and prompt"`

---

## Task 5 (Checkpoint 5): 全套件綠 + live integration（finnhub_integration marker）

**Files:**

- Update (Tests): `backend/tests/tools/test_finnhub_tools.py`（加 live integration 區段，`@pytest.mark.finnhub_integration`）

**What & Why:** 收尾——確認預設套件全綠、無任何 yfinance 殘留於 agent 子系統，並補一個 opt-in live 測試真打 Finnhub free API（CI 預設跳過，需 `FINNHUB_API_KEY` 才跑）。

**Implementation Notes:**

- live 測試（marker `finnhub_integration`，預設被 `addopts` 排除）：
  - `test_live_quote_known_ticker`：真實 `fetch_quote("AAPL")` → 斷言 `currentPrice`(`c`) 為非 0 數值。
  - `test_live_basic_financials_known_ticker`：真實 `fetch_basic_financials("MSFT")` → 斷言含至少一個 catalog metric key（如 `peTTM` 或 `52WeekHigh`）。
  - `test_live_invalid_ticker_raises`：`fetch_quote("ZZZZINVALID")` → `pytest.raises(ValueError)`（驗證「全 0 偵測」對真 API 成立）。
  - 用 `pytest.importorskip` 不需要；用 `os.getenv("FINNHUB_API_KEY")` guard：`@pytest.mark.skipif(not os.getenv("FINNHUB_API_KEY"), reason="needs FINNHUB_API_KEY")` 疊加 marker，避免本機誤跑。

**Critical Contract / Snippet:** live 測試骨架：

```python
import os
import pytest
from backend.agent_engine.tools.finnhub_client import fetch_quote, fetch_basic_financials


@pytest.mark.finnhub_integration
@pytest.mark.skipif(not os.getenv("FINNHUB_API_KEY"), reason="needs FINNHUB_API_KEY")
def test_live_quote_known_ticker():
    q = fetch_quote("AAPL")
    assert q["c"] and q["c"] > 0


@pytest.mark.finnhub_integration
@pytest.mark.skipif(not os.getenv("FINNHUB_API_KEY"), reason="needs FINNHUB_API_KEY")
def test_live_basic_financials_known_ticker():
    m = fetch_basic_financials("MSFT")
    assert "peTTM" in m or "52WeekHigh" in m


@pytest.mark.finnhub_integration
@pytest.mark.skipif(not os.getenv("FINNHUB_API_KEY"), reason="needs FINNHUB_API_KEY")
def test_live_invalid_ticker_raises():
    with pytest.raises(ValueError):
        fetch_quote("ZZZZINVALID")
```

**Test Strategy:** live 測試證明「catalog metric key 拼寫對真 free-tier 回傳成立」（design 第 156 行要求 smoke 校正）+「全 0 偵測對真 API 有效」。預設不跑，避免 CI 依賴外部 API。

**Verification:**

| Scope | Command | Expected Result | Why |
| ----- | ------- | --------------- | --- |
| 預設全套件 | `uv run pytest backend/tests/ -q` | 全 pass、0 failed（live / eval / sec_integration / integration / finnhub_integration 依 `addopts` 自動排除） | 整體無回歸 |
| 無 yfinance 殘留（agent 子系統） | `grep -rn "yfinance" backend/agent_engine backend/evals backend/tests \| grep -v ingestion` | 無輸出 | agent 端完全去 yfinance（ingestion 不算） |
| ingestion 未被波及 | `grep -rln "yfinance" backend/ingestion \| wc -l` | 數字 > 0（comment/schema 仍在，**符合預期**） | 確認沒誤改 ingestion |
| Live（opt-in，本機備妥 key 時） | `FINNHUB_API_KEY=<key> uv run pytest backend/tests/tools/test_finnhub_tools.py -m finnhub_integration -v` | 3 個 live 測試 pass（catalog key 拼寫經真 API 校正） | free-tier 真實行為驗證 |
| Lint | `uv run ruff check backend/agent_engine/tools/finnhub_client.py backend/agent_engine/tools/finnhub_tools.py backend/tests/tools/test_finnhub_tools.py` | 無 error | 風格一致 |

**Execution Checklist:**

- [ ] 🟢 在 `test_finnhub_tools.py` 加 3 個 `finnhub_integration` live 測試
- [ ] 跑 `uv run pytest backend/tests/ -q` 全綠
- [ ] 跑 3 條 grep 驗證（agent 去 yfinance、ingestion 保留、無誤改）
- [ ] （本機有 key 時）跑 live marker 校正 catalog metric key 拼寫；若某 key 在 free tier 拼法不同，回頭修 `BASIC_FINANCIALS_CATALOG` 並重跑 Task 1 單元測試
- [ ] `uv run ruff check ...` 無 error
- [ ] 提醒 user：在 `.env` 設定真實 `FINNHUB_API_KEY` 才能跑 live 與實際 agent 查詢
- [ ] Commit：`git commit -m "test(finnhub): add opt-in finnhub_integration live API smoke tests"`

---

### Flow Verification: Agent 端 Finnhub 工具替換完成

> Task 1–5 完成「agent 兩個 yfinance tool → 3 個 finnhub tool」的端到端替換。下列須全過才算交付完成。

| #   | Method | Step | Expected Result |
| --- | ------ | ---- | --------------- |
| 1 | Runtime / function invocation | `uv run python -c "from backend.agent_engine.tools.finnhub_tools import finnhub_stock_quote; print(finnhub_stock_quote.name, finnhub_stock_quote.args_schema.__name__)"` | 印 `finnhub_stock_quote FinnhubStockQuoteInput` |
| 2 | Runtime（registry） | CP2 的 registry 驗證命令 | finnhub 3 名稱在、yfinance 不在 |
| 3 | Database/State check（config 載入） | CP3 的 config load 命令（v1） | `finnhub_stock_quote in tools` 且 `yfinance_stock_quote not in tools` |
| 4 | Log grep（去 Yahoo） | CP3 的 prompt 去 Yahoo grep | 無 `yahoo` / `forwardpe` / `yfinance` |
| 5 | 單元測試 | `uv run pytest backend/tests/tools/test_finnhub_tools.py backend/tests/tools/test_observe_decorators.py -q` | 全 pass |
| 6 | 全套件 | `uv run pytest backend/tests/ -q` | 全 pass，0 failed |
| 7 | Live（opt-in） | CP5 live marker 命令（需 key） | 3 live 測試 pass，catalog key 拼寫經真 API 校正 |

- [ ] 上述 #1–#6 全過（#7 在備妥 `FINNHUB_API_KEY` 後執行）

---

## Pre-delivery Checklist

### Code Level (TDD)

- [ ] 每個 task 的 Targeted 驗證命令通過
- [ ] `uv run pytest backend/tests/ -q` 全 pass（預設排除 live/eval/sec/integration）
- [ ] `uv run ruff check backend/agent_engine/tools/ backend/tests/tools/test_finnhub_tools.py` 無 error
- [ ] 無 build step（純 Python lib），故不適用 bundle 驗證

### Flow Level (Behavioral)

- [ ] Flow: Agent 端 Finnhub 工具替換完成 — PASS / FAIL（#1–#6 必過，#7 視 key）

### Summary

- [ ] Code + Flow 皆過 → 可交付
- [ ] 任何失敗已記錄原因與下一步
