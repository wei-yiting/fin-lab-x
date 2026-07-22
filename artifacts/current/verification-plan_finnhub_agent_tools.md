# Verification Plan：Finnhub Agent Tools 抽換

> 對應 `bdd-scenarios_finnhub_agent_tools.md`（scenario ID 一一對應）。
> 執行根目錄：`backend/`（所有 `uv run` 指令在 `backend/` 下執行，與既有 `README.md` 慣例一致）。
> 三類驗證：**Deterministic（mock pytest）**、**Live Smoke（真打 Finnhub free API）**、**Agent Integration（真跑 v1 agent）**。

---

## 約定與前置

- Mock 單元測試新檔：`backend/tests/tools/test_finnhub_tools.py`（design 已規劃）。tool 呼叫沿用既有 `_tool_call()` helper（須帶完整 ToolCall 以滿足 `InjectedToolCallId`）。
- patch seam：以 `patch("backend.agent_engine.tools.finnhub_client.get_finnhub_client")` 注入 mock client（design 指定此為 test-patching seam，call-time 解析）。
- Live / agent 測試需環境變數：`FINNHUB_API_KEY`（free tier）；agent integration 另需 LLM key（v1 用 `gpt-4o-mini`）。
- Live 測試使用 design 規劃的新 marker `finnhub_integration`，預設排除（沿用既有 `integration` marker 慣例：`addopts` 預設 `-m "not integration and not finnhub_integration"`，或顯式 `-m finnhub_integration` 才跑）。
  - `[POST-CODING: 確認 marker 名稱與註冊位置 — pyproject.toml [tool.pytest.ini_options] markers 或 conftest，與既有 integration marker 對齊]`

---

## A. Deterministic 驗證（mock pytest，無需任何 API key）

> 一律可重複、CI 預設執行。每條斷言到 tool 的可觀察輸出（回傳 dict / 拋出的 exception / stream 事件）。

### S-01　有效 ticker 完整即時報價
- **方法**：Deterministic（mock）
- **步驟**：
  1. mock `get_finnhub_client().quote("AAPL")` 回 `{"c":190.5,"o":188.0,"pc":187.2,"d":3.3,"dp":1.76,"h":191.2,"l":187.9,"t":1}`
  2. `_tool_call(finnhub_stock_quote, {"ticker":"AAPL"})`
- **預期**：dict == `{ticker:"AAPL", currentPrice:190.5, open:188.0, previousClose:187.2, change:3.3, percentChange:1.76, dayHigh:191.2, dayLow:187.9}`；斷言 `"forwardPE" not in result`、`"fiftyTwoWeekHigh" not in result`。
- **指令**：
  ```bash
  uv run pytest tests/tools/test_finnhub_tools.py -k "quote and fields" -q
  ```

### S-02　ticker 正規化
- **方法**：Deterministic（mock）
- **步驟**：以 `{"ticker":"  aapl  "}` 呼叫；mock client 記錄實際傳入的 symbol。
- **預期**：mock `.quote` 被以 `"AAPL"` 呼叫；回傳 `ticker == "AAPL"`。
- **指令**：`uv run pytest tests/tools/test_finnhub_tools.py -k "normalize" -q`

### S-03 / S-07 / S-08（stream 事件）
- **方法**：Deterministic（mock writer）
- **步驟**：patch `get_stream_writer` 回一個 recording mock，呼叫各工具。
- **預期**：
  - S-03：捕獲事件含 `status=="querying_stock"`、`toolName=="finnhub_stock_quote"`、`toolCallId` 存在、message 含 ticker。
  - S-07：`status=="querying_financials"`、`toolName=="finnhub_company_basic_financials"`。
  - S-08：`status=="querying_fields"`。
  - 另測「writer 不可用」：patch `get_stream_writer` 拋例外 → 工具仍正常回傳（不因缺 writer 失敗）。
- **指令**：`uv run pytest tests/tools/test_finnhub_tools.py -k "stream or writer" -q`

### S-04　無效 ticker（quote 全 0）→ ValueError
- **方法**：Deterministic（mock）
- **步驟**：mock `.quote("ZZZZ")` 回 `{"c":0,"h":0,"l":0,"o":0,"pc":0,"d":None,"dp":None,"t":0}`；以 `pytest.raises(ValueError)` 包住 `_tool_call`。
- **預期**：raise `ValueError`；`"ZZZZ" in str(exc)` 且訊息含 invalid/delisted/not covered 之一。
  - 邊界補測（QA）：`{"c":0, "pc":187.2,...}`（c 為 0 但 pc 非 0，盤前情境）**不應** raise — 驗證判定基準是 `c` 與 `pc` 皆 0/None。
- **指令**：`uv run pytest tests/tools/test_finnhub_tools.py -k "invalid_quote or allzero or premarket" -q`

### S-05　基本面 present-only happy path
- **方法**：Deterministic（mock）
- **步驟**：mock `.company_basic_financials("AAPL","all")` 回 `{"metric":{"52WeekHigh":260.1,"52WeekLow":164.0,"peTTM":28.4,"marketCapitalization":2900000,"beta":1.25,"roeTTM":147.2,"netProfitMarginTTM":24.3},"series":{},"symbol":"AAPL"}`（**刻意不含** `dividendYieldIndicatedAnnual`）。
- **預期**：回傳含 `fiftyTwoWeekHigh/Low, peTTM, marketCap, beta, roeTTM, netProfitMarginTTM` + `ticker`；斷言 `"dividendYield" not in result`、`"forwardPE" not in result`、`all(v is not None for v in result.values())`（無 null 欄位）。
- **指令**：`uv run pytest tests/tools/test_finnhub_tools.py -k "basic_financials and present" -q`

### S-06　基本面無效 ticker（空 metric）→ ValueError
- **方法**：Deterministic（mock）
- **步驟**：mock 回 `{"metric":{}, "series":{}, "symbol":"ZZZZ"}`；`pytest.raises(ValueError)`。
- **預期**：raise；`"ZZZZ" in str(exc)`，訊息含 invalid/not covered。
- **指令**：`uv run pytest tests/tools/test_finnhub_tools.py -k "basic_financials and invalid" -q`

### S-09　缺 FINNHUB_API_KEY → call-time raise
- **方法**：Deterministic（mock env）
- **步驟**：
  1. `monkeypatch.delenv("FINNHUB_API_KEY", raising=False)`
  2. 確認 **import 階段不爆**：`import backend.agent_engine.tools.finnhub_tools` 成功（已在 collection 期完成 → 此處只斷言模組已載入）。
  3. **不** patch `get_finnhub_client`（要走真實 key 檢查）；`pytest.raises(ValueError)` 包住 `_tool_call(finnhub_stock_quote, {"ticker":"AAPL"})`。
- **預期**：`str(exc) == "FINNHUB_API_KEY is not set."`。
- **指令**：`uv run pytest tests/tools/test_finnhub_tools.py -k "missing_key" -q`

### S-10　429 → sanitized 外部錯誤（非內部 budget、不洩 key）
- **方法**：Deterministic（mock SDK exception + sanitizer 單測）
- **步驟（兩段）**：
  1. **工具 bubble-up**：mock `.quote` 拋 `finnhub.exceptions.FinnhubAPIException`（status_code=429）；驗證工具讓例外向上拋（不吞、不轉成 error dict）。
  2. **sanitizer 行為**：直接餵 `sanitize_tool_error("FinnhubAPIException: status 429, api_key=SECRETKEY123 at /Users/x/y/z/finnhub_client.py")`。
- **預期**：
  - 工具確實 raise（`pytest.raises(FinnhubAPIException)`）。
  - sanitized 字串：含 "429"（保留可理解描述）；`"SECRETKEY123" not in out`、`"api_key=SECRET" not in out`（key 被 `[REDACTED]`）；`"Per-run tool-call budget reached" not in out`（不可偽裝成內部 budget）；不含原始檔案路徑（被 `[path]`）。
- **指令**：
  ```bash
  uv run pytest tests/tools/test_finnhub_tools.py -k "rate_limit or 429" tests/streaming/ -k "sanitize" -q
  ```

### S-11　system prompt 去 Yahoo / 去 forwardPE
- **方法**：Deterministic（檔案 grep 斷言，可寫成 pytest）
- **步驟**：讀 `agent_engine/agents/versions/v1_baseline/system_prompt.md`。
- **預期**：`"finance.yahoo.com" not in text`、`"yfinance" not in text`、`"forwardPE" not in text`、`"Forward P/E" not in text`；且出現 "Finnhub" 字樣。
- **指令**：
  ```bash
  uv run python -c "
  t=open('backend/agent_engine/agents/versions/v1_baseline/system_prompt.md').read()
  for bad in ('finance.yahoo.com','yfinance','forwardPE','Forward P/E'):
      assert bad not in t, bad
  assert 'Finnhub' in t
  print('S-11 OK')"
  ```
  （在 worktree root 執行；或併入既有 `tests/agents/test_orchestrator_prompt_rendering.py`）

### S-12　v1 config 只 register finnhub 工具
- **方法**：Deterministic（YAML 斷言）
- **步驟**：解析 `v1_baseline/orchestrator_config.yaml` 的 tools list。
- **預期**：含 `finnhub_stock_quote / finnhub_company_basic_financials / finnhub_get_available_fields`；`not any("yfinance" in t for t in tools)`；仍含 `tavily_financial_search`、`sec_filing_list_sections`、`sec_filing_get_section`。
- **指令**：
  ```bash
  uv run python -c "
  import yaml
  c=yaml.safe_load(open('backend/agent_engine/agents/versions/v1_baseline/orchestrator_config.yaml'))
  t=c['tools']
  assert {'finnhub_stock_quote','finnhub_company_basic_financials','finnhub_get_available_fields'} <= set(t)
  assert not any('yfinance' in x for x in t)
  assert 'tavily_financial_search' in t
  print('S-12 OK', t)"
  ```

### S-13　LP-05 / LP-06 expect_tool 改 finnhub
- **方法**：Deterministic（dataset 斷言）
- **步驟**：import `LANGUAGE_POLICY_CASES`，取 LP-05/LP-06。
- **預期**：兩者 `expect_tool == "finnhub_stock_quote"`；LP-05 `prompt=="特斯拉現在股價多少？"`、`prompt_language=="zh"`、`expect_response_cjk_min==0.20`；整檔無 "yfinance"。
- **指令**：
  ```bash
  uv run python -c "
  from backend.evals.datasets.language_policy import LANGUAGE_POLICY_CASES as C
  m={c.id:c for c in C}
  assert m['LP-05'].expect_tool=='finnhub_stock_quote'
  assert m['LP-06'].expect_tool=='finnhub_stock_quote'
  assert m['LP-05'].prompt=='特斯拉現在股價多少？' and m['LP-05'].prompt_language=='zh'
  assert m['LP-05'].expect_response_cjk_min==0.20
  src=open('backend/evals/datasets/language_policy.py').read()
  assert 'yfinance' not in src
  print('S-13 OK')"
  ```

**A 段一鍵跑（mock 全集，CI 預設）**：
```bash
cd backend && uv run pytest tests/tools/test_finnhub_tools.py -q
```

---

## B. Live Smoke 驗證（真打 Finnhub free API — 需 FINNHUB_API_KEY）

> 用 `finnhub_integration` marker；free tier 60 calls/min，下列總呼叫數 ≤ 6，安全。
> 斷言「關鍵欄位存在且型別/非空合理」，**不**斷言精確即時數值（即時資料會變）。

### LIVE-1（覆蓋 S-01 真實面）　AAPL / MSFT 即時報價非空
- **步驟**：對 `["AAPL","MSFT"]` 各呼叫一次 `finnhub_stock_quote`（走真實 client，不 mock）。
- **預期**：每筆回傳 `currentPrice` 為 `float` 且 `> 0`；含全部 8 個 key；`"forwardPE" not in result`。

### LIVE-2（覆蓋 S-05 真實面）　AAPL / MSFT 基本面非空 + catalog 拼寫校正
- **步驟**：對 `["AAPL","MSFT"]` 各呼叫一次 `finnhub_company_basic_financials`。
- **預期**：回傳含 `peTTM`（float）與至少一個 52 週欄位；所有值非 None（present-only）；`"forwardPE" not in result`。此測同時校正 design catalog 中各 Finnhub `metric` key 的實際拼寫（free tier 回傳為準）。
- **`[POST-CODING: 若某 catalog key 在 AAPL/MSFT 上實際拼寫與 design 表不符，回頭修正 BASIC_FINANCIALS_CATALOG]`**

### LIVE-3（覆蓋 S-04 真實面）　無效 ticker 真打 → ValueError
- **步驟**：對 `"ZZZZ"`（或保證無效的 symbol）呼叫 `finnhub_stock_quote`。
- **預期**：Finnhub 真實回全 0 → 工具 raise `ValueError`，訊息含 `"ZZZZ"`。

**B 段執行**：
```bash
cd backend && FINNHUB_API_KEY=<your_free_key> uv run pytest -m finnhub_integration -q
```
若 marker 尚未配置，過渡用一次性 smoke script：
```bash
cd backend && FINNHUB_API_KEY=<key> uv run python -c "
from backend.agent_engine.tools.finnhub_client import fetch_quote, fetch_basic_financials
for t in ('AAPL','MSFT'):
    q=fetch_quote(t); assert q['c']>0, (t,q); print(t,'quote c=',q['c'])
    m=fetch_basic_financials(t); assert 'peTTM' in m, (t, list(m)[:10]); print(t,'peTTM=',m.get('peTTM'))
try:
    fetch_quote('ZZZZ'); raise SystemExit('FAIL: ZZZZ did not raise')
except ValueError as e:
    assert 'ZZZZ' in str(e); print('invalid ticker OK')
print('LIVE smoke OK')"
```

---

## C. Agent Integration 驗證（真跑 v1 agent — 需 FINNHUB_API_KEY + LLM key）

> 走真實 `Orchestrator.astream_run`，收斂為 `OrchestratorResult{response, tool_outputs}`（與 `evals/eval_tasks.py::_astream_collect` 同路徑）。
> 斷言「選對工具 / 回應語言 / citation 行為 / 無 forwardPE / 無 Yahoo URL」，不斷言精確價格。

### J-01　英文問 AAPL 價格 → finnhub_stock_quote + 引用 Finnhub、無 Yahoo URL
- **方法**：Agent Integration（live LLM）
- **步驟**：對 v1 跑 prompt `"What is AAPL's current stock price?"`，收集 `OrchestratorResult`。
- **預期**：
  - `any(o["tool"]=="finnhub_stock_quote" and o["args"].get("ticker")=="AAPL" for o in tool_outputs)`。
  - 對應 tool result 含 `currentPrice`，非 None 且 `!= 0`。
  - `"finance.yahoo.com" not in response`、`"forwardPE" not in response and "Forward P/E" not in response`。
  - response 無 CJK（英文）。

### J-02（= LP-05 真實面）　中文問特斯拉 → 英文 ticker、中文回應
- **方法**：Agent Integration（live LLM）
- **步驟**：prompt `"特斯拉現在股價多少？"`。
- **預期**：
  - 呼叫 `finnhub_stock_quote`，`args["ticker"]` 無 CJK 且 == `"TSLA"`。
  - response CJK 比例 ≥ 0.20（沿用 `language_policy_scorer` 的 CJK 比例量測）。
  - `"finance.yahoo.com" not in response`、`"forwardPE" not in response`。

### J-03　無效 ticker 端到端 → 不捏造價格
- **方法**：Agent Integration（live LLM）
- **步驟**：prompt `"What is the current price of ZZZZ?"`。
- **預期**：`finnhub_stock_quote` 對 ZZZZ 觸發 ValueError（在 tool_outputs/errors 可見）；response 不含具體價格數字（regex 無 `$\d` 形式報價）；response 表達資料不可得（含 "don't have enough information" 或等義說明）；無 Yahoo URL。

**C 段執行（沿用 eval 路徑，最省事）**：
```bash
cd backend && FINNHUB_API_KEY=<key> OPENAI_API_KEY=<key> uv run python -c "
import asyncio
from backend.agent_engine.agents.config_loader import VersionConfigLoader
from backend.agent_engine.agents.base import Orchestrator
from backend.agent_engine.streaming.domain_events_schema import TextDelta, ToolCall, ToolResult

async def run(prompt):
    orch=Orchestrator(VersionConfigLoader('v1_baseline').load(), checkpointer=None)
    text=[]; calls=[]
    async for e in orch.astream_run(message=prompt, session_id='verif'):
        if isinstance(e,TextDelta): text.append(e.delta)
        elif isinstance(e,ToolCall): calls.append((e.tool_name,e.args))
    return ''.join(text), calls

resp,calls=asyncio.run(run('What is AAPL\\'s current stock price?'))
assert any(n=='finnhub_stock_quote' and a.get('ticker')=='AAPL' for n,a in calls), calls
assert 'finance.yahoo.com' not in resp and 'forwardPE' not in resp
print('J-01 OK'); print(resp[:300])

resp2,calls2=asyncio.run(run('特斯拉現在股價多少？'))
tkr=[a.get('ticker') for n,a in calls2 if n=='finnhub_stock_quote']
assert tkr and tkr[0]=='TSLA' and all(ord(ch)<0x2E80 for ch in tkr[0]), tkr
cjk=sum(1 for c in resp2 if 0x4E00<=ord(c)<=0x9FFF)/max(len(resp2),1)
assert cjk>=0.20, cjk
assert 'finance.yahoo.com' not in resp2 and 'forwardPE' not in resp2
print('J-02 OK cjk=',round(cjk,2)); print(resp2[:300])
"
```
- **`[POST-CODING: 確認 domain_events_schema 內 ToolResult 帶 result 與 tool_call_id 的實際欄位名；若與 eval_tasks 對齊，直接套 _astream_collect 較穩]`**

---

## D. 回歸 / 全套 gate（pre-push）

依專案 pre-push 慣例，抽換後需跑（mock 全集，不含 live）：
```bash
cd backend && uv run pytest tests/tools/ tests/agents/ tests/integration/ tests/streaming/ tests/evals/ tests/api/ -q
```
- 預期：原 `test_financial.py` 的 yfinance 測試已移除（保留 tavily）；新 `test_finnhub_tools.py` 全綠；所有舊測試的 yfinance 字串/mock 已改 finnhub（design 受影響測試清單）；無 collection error（`import yfinance` 不再出現在 agent tool 路徑）。

---

## 驗證方法總覽

| Scenario | 方法 | 需 API key | 主指令位置 |
|---|---|---|---|
| S-01~S-09, S-10(part), S-11~S-13 | Deterministic（mock / grep / yaml） | 無 | A 段 |
| S-10 sanitizer | Deterministic（mock + sanitizer 單測） | 無 | A 段 |
| LIVE-1/2/3（S-01/S-04/S-05 真實面） | Live Smoke | FINNHUB_API_KEY | B 段 |
| J-01, J-02, J-03 | Agent Integration | FINNHUB_API_KEY + LLM | C 段 |
| 全回歸 | Deterministic | 無 | D 段 |

> 無 browser/UI scenario：本變更只動 tool dict 回傳與 system prompt，無前端 contract 變更（design Scope「不包含」明列前端 UI 不調整），故不需 Browser-Use CLI。
