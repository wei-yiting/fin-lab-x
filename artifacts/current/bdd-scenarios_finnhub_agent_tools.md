# BDD Scenarios：以 Finnhub Free-Tier API 抽換 Agent 的 Yahoo Finance 工具

> Source of truth：`artifacts/current/design_finnhub_agent_tools.md`
> 範圍：只涵蓋 **agent-observable behavior**（tool input/output、error surface、agent 端到端、citation 行為），不涵蓋內部實作。
> 對應驗證方法見 `verification-plan_finnhub_agent_tools.md`（scenario ID 一一對應）。

---

## Three Amigos 探索摘要（收斂後）

| 角色 | 關鍵貢獻 | 影響的 scenario |
|---|---|---|
| PO | 種子範例：「問 AAPL 價格」「中文問特斯拉股價」「forward P/E 不該再出現」 | J-01、J-02、S-13 |
| Dev | 挑戰：Finnhub 對無效 ticker 不 raise（回全 0）→ client 層判定；429 走既有 middleware；missing key 在 call time 才爆 | S-04、S-05、S-06 |
| QA | 破壞性：`change`/`percentChange` 在 quote 全 0 時為 `None`（不是 0）；basic_financials present-only 不可有 `null`；sanitize 後仍可能殘留 ticker 字串（非機密，允許） | S-04、S-08、S-07 |

### 探索期間浮現、已由設計決策定案的假設（不再爭論）

1. **無效 ticker 的判定基準**：以 `c`（current）與 `pc`（previousClose）皆為 0/None 判定無效（design §關鍵研究結論-2）。不單看 `c`，因為盤前/停牌個股 `c` 可能暫為 0 但 `pc` 非 0。→ S-04 採此基準。
2. **429 是「外部」rate limit，與「內部 tool-call budget」語意不同**：system prompt 明文要求「budget 用罄」不可說成 rate limit；反向地，Finnhub 真正的 429 是外部 API 限流，經 `_HandleToolErrors` sanitize 後可如實呈現為 API 錯誤。兩者是不同來源、不可混為一談。→ S-06。
3. **Citation 去 Yahoo（DECISION-001）**：free tier 無 per-ticker 公開頁，硬編 URL 違反 zero-hallucination → 報價/基本面 claim 以 provider/tool 名稱標註、不強制 per-ticker URL。→ J-01、S-09、S-10。

---

# Feature 1：即時報價工具 `finnhub_stock_quote`

> **Rule 1.1**：對有效 ticker，工具回傳即時報價 dict，含 `ticker, currentPrice, open, previousClose, change, percentChange, dayHigh, dayLow` 八個 key，且只打 **1 次** Finnhub `/quote`。

### S-01　有效 ticker 回傳完整即時報價（happy path）
```gherkin
Given Finnhub /quote 對 "AAPL" 回傳 {c:190.5, o:188.0, pc:187.2, d:3.3, dp:1.76, h:191.2, l:187.9}
When agent 呼叫 finnhub_stock_quote(ticker="AAPL")
Then 回傳 dict 含 ticker="AAPL"、currentPrice=190.5、open=188.0、previousClose=187.2
And 含 change=3.3、percentChange=1.76、dayHigh=191.2、dayLow=187.9
And 不含 fiftyTwoWeekHigh / fiftyTwoWeekLow（那些屬於 basic_financials，不在 quote）
And 不含 forwardPE
```

### S-02　ticker 正規化為大寫並去空白
```gherkin
Given Finnhub /quote 對 "AAPL" 回傳有效報價
When agent 呼叫 finnhub_stock_quote(ticker="  aapl  ")
Then 工具以 "AAPL" 呼叫 Finnhub
And 回傳 dict 的 ticker 欄位為 "AAPL"
```

> **Rule 1.2**：呼叫工具時，若 stream writer 可用，發出 `querying_stock` 進度事件；不可用時靜默繼續（不得因缺 writer 而失敗）。

### S-03　報價工具發出 querying_stock stream 事件
```gherkin
Given stream writer 可用
When agent 呼叫 finnhub_stock_quote(ticker="MSFT")
Then 發出一筆 stream 事件 status="querying_stock"、toolName="finnhub_stock_quote"
And 事件含 toolCallId 與包含 "MSFT" 的 message
```

> **Rule 1.3**：Finnhub 對無效 ticker **不 raise**，而回傳全 0。client 層須判定「`c` 與 `pc` 皆為 0/None」為無效並 `raise ValueError`，錯誤訊息提及 symbol 可能 invalid/delisted。

### S-04　無效 ticker（Finnhub 全 0）→ 乾淨地 raise ValueError
```gherkin
Given Finnhub /quote 對 "ZZZZ" 回傳全 0：{c:0, h:0, l:0, o:0, pc:0, d:None, dp:None, t:0}
When agent 呼叫 finnhub_stock_quote(ticker="ZZZZ")
Then 工具 raise ValueError
And 錯誤訊息含 "ZZZZ" 且提及 invalid / delisted / not covered
And 不回傳任何全 0 的報價 dict（不得把 0 當成真實價格交給 agent）
```

---

# Feature 2：基本面工具 `finnhub_company_basic_financials`

> **Rule 2.1**：對有效 ticker，回傳 catalog 內 **實際存在（present-only）** 的欄位 + `ticker`，只打 1 次 Finnhub `/stock/metric`。輸出 key 為 design catalog 的 output key（如 `fiftyTwoWeekHigh`、`peTTM`、`marketCap`、`beta`、`roeTTM`...），不含 `forwardPE`。

### S-05　有效 ticker 回傳 present-only 基本面（happy path）
```gherkin
Given Finnhub /stock/metric 對 "AAPL" 回傳 metric 含 52WeekHigh=260.1、52WeekLow=164.0、peTTM=28.4、marketCapitalization=2900000、beta=1.25、roeTTM=147.2、netProfitMarginTTM=24.3
And metric 缺 dividendYieldIndicatedAnnual（該欄不存在）
When agent 呼叫 finnhub_company_basic_financials(ticker="AAPL")
Then 回傳 dict 含 ticker="AAPL"、fiftyTwoWeekHigh=260.1、fiftyTwoWeekLow=164.0、peTTM=28.4、marketCap=2900000、beta=1.25、roeTTM=147.2、netProfitMarginTTM=24.3
And 不含 dividendYield（present-only：缺的欄位不輸出，不得是 null）
And 不含 forwardPE
And 沒有任何值為 null 的 catalog 欄位
```

> **Rule 2.2**：無效 ticker → Finnhub `metric` 為空 `{}` → client 層 `raise ValueError`。

### S-06　無效 ticker（空 metric）→ raise ValueError
```gherkin
Given Finnhub /stock/metric 對 "ZZZZ" 回傳 {metric:{}, series:{}, symbol:"ZZZZ"}
When agent 呼叫 finnhub_company_basic_financials(ticker="ZZZZ")
Then 工具 raise ValueError
And 錯誤訊息含 "ZZZZ" 且提及 invalid / not covered
```

### S-07　基本面工具發出 querying_financials stream 事件
```gherkin
Given stream writer 可用
When agent 呼叫 finnhub_company_basic_financials(ticker="AAPL")
Then 發出一筆 stream 事件 status="querying_financials"、toolName="finnhub_company_basic_financials"
```

---

# Feature 3：欄位探索工具 `finnhub_get_available_fields`

> **Rule 3.1**：回傳此 ticker 在 catalog 中「實際可用」的欄位描述 + 可用性 + 總數，只打 1 次 `/stock/metric`。語意同舊 `yfinance_get_available_fields`。

### S-08　欄位探索回傳 catalog 可用性
```gherkin
Given Finnhub /stock/metric 對 "AAPL" 的 metric 含 52WeekHigh、peTTM（但缺 dividendYieldIndicatedAnnual）
When agent 呼叫 finnhub_get_available_fields(ticker="AAPL")
Then 回傳 available_fields 含 fiftyTwoWeekHigh={description:"52-week high price", available:true}
And 含 peTTM={description:"Trailing twelve-month P/E ratio", available:true}
And available_fields 不含 dividendYield（catalog 該欄在此 ticker 不可用）
And total_fields 等於 available_fields 的數量
And available_fields 不含 forwardPE（catalog 已無此欄）
And 發出 stream 事件 status="querying_fields"
```

---

# Feature 4：環境 / 錯誤 surface（agent 可觀察的失敗行為）

> **Rule 4.1**：`FINNHUB_API_KEY` 未設時，在 **呼叫工具的當下**（非 import 時）raise `ValueError("FINNHUB_API_KEY is not set.")`。

### S-09　缺 FINNHUB_API_KEY → 呼叫工具時 raise
```gherkin
Given 環境變數 FINNHUB_API_KEY 未設定
And 模組已正常 import（import 階段不得失敗）
When agent 呼叫 finnhub_stock_quote(ticker="AAPL")
Then 工具 raise ValueError，訊息為 "FINNHUB_API_KEY is not set."
```

> **Rule 4.2**：Finnhub 429 rate limit → SDK 拋 `FinnhubAPIException`，bubble up 經 `_HandleToolErrors` middleware sanitize 後呈現。呈現內容須是「外部 API 錯誤」語意，**不得**被包裝成內部 budget 訊息，且不得洩漏 API key。

### S-10　429 rate limit → sanitized 外部 API 錯誤（非內部 budget）
```gherkin
Given Finnhub SDK 對 "AAPL" 拋 FinnhubAPIException(status_code=429)
When agent 透過串流路徑呼叫 finnhub_stock_quote(ticker="AAPL")
Then 該 tool 的錯誤經 sanitize 後 surface 給 agent
And sanitized 錯誤不含 "Per-run tool-call budget reached"（不得偽裝成內部 budget）
And sanitized 錯誤不含任何 API key / Bearer token / 連線字串 / 檔案路徑
And sanitized 錯誤保留足以理解的描述（如 status 429 / Finnhub API 字樣）
```

---

# Feature 5：System prompt / citation 去 Yahoo 化（DECISION-001）

> **Rule 5.1**：v1 system prompt 不得再要求每個報價 claim 附 `https://finance.yahoo.com/quote/TICKER`；報價/基本面 claim 以 provider/tool 名稱標註。真正有 URL 的來源（Tavily/SEC）維持 `[N]` inline + 底部 reference。

### S-11　system prompt 已移除 Yahoo URL 強制規則
```gherkin
Given v1_baseline/system_prompt.md
When 檢視 CITATION / LINK FORMAT 段落與 Example 1
Then 不含 "finance.yahoo.com"
And 不含 "yfinance"
And 不含 "forwardPE" / "Forward P/E"
And 報價 citation 改以 provider/tool 名稱描述（如 "According to Finnhub..."）
```

> **Rule 5.2**：v1 config 的 tools list 已換成 3 個 finnhub tool，不再有 yfinance tool。

### S-12　v1 orchestrator config 只 register finnhub 工具
```gherkin
Given v1_baseline/orchestrator_config.yaml
When 檢視 tools list
Then 含 finnhub_stock_quote、finnhub_company_basic_financials、finnhub_get_available_fields
And 不含任何 yfinance_* 工具名稱
And 仍保留 tavily_financial_search 與 sec_filing_* 工具（未更動）
```

> **Rule 5.3**：eval dataset LP-05 / LP-06 的 `expect_tool` 由 `yfinance_stock_quote` 改為 `finnhub_stock_quote`，其餘語言政策斷言不變。

### S-13　語言政策 dataset 期望工具改為 finnhub
```gherkin
Given evals/datasets/language_policy.py
When 檢視 LP-05 與 LP-06
Then 兩者 expect_tool 皆為 "finnhub_stock_quote"
And LP-05 prompt 仍為 "特斯拉現在股價多少？"、prompt_language="zh"、expect_response_cjk_min=0.20
And 不含任何 "yfinance" 字串
```

---

# Journey Scenarios（端到端，跑真實 v1 agent）

> **J-** 走真實 `Orchestrator.astream_run`，收斂為 `OrchestratorResult{response, tool_outputs}`。需真實 LLM + `FINNHUB_API_KEY`。
> 斷言聚焦「agent 選了正確工具 / 回應語言 / citation 行為」，價格數值本身屬即時資料、不做精確值斷言。

### J-01　英文問 AAPL 股價 → 呼叫 finnhub_stock_quote → 以 Finnhub 標註、無 Yahoo URL
```gherkin
Given v1 agent 已載入 finnhub 工具，FINNHUB_API_KEY 已設定
When 使用者問 "What is AAPL's current stock price?"
Then agent 的 tool_outputs 含一次 finnhub_stock_quote(ticker="AAPL") 的呼叫
And 該 tool 結果含 currentPrice（非 None、非 0）
And 最終 response 引用 Finnhub（provider/tool 名稱），陳述目前價格
And response 不含 "finance.yahoo.com" 任何 URL
And response 不含 "forwardPE" / "Forward P/E"
And response 為英文（無 CJK）
```

### J-02　中文問特斯拉股價（LP-05）→ 英文 ticker 參數、中文回應、finnhub_stock_quote
```gherkin
Given v1 agent 已載入 finnhub 工具，FINNHUB_API_KEY 已設定
When 使用者問 "特斯拉現在股價多少？"
Then agent 呼叫 finnhub_stock_quote，ticker 參數為英文 "TSLA"（無 CJK）
And tool 結果含 currentPrice
And 最終 response 為繁體中文（CJK 比例 ≥ 0.20）
And response 以 Finnhub 標註資料來源，不含 "finance.yahoo.com"
And response 不含 "forwardPE"
```

### J-03　無效 ticker 端到端 → agent 收到乾淨錯誤、不捏造價格
```gherkin
Given v1 agent 已載入 finnhub 工具
When 使用者問 "What is the current price of ZZZZ?"（無效 ticker）
Then finnhub_stock_quote 對 "ZZZZ" raise ValueError（全 0 偵測）
And agent 不在 response 編造任何具體價格數字
And response 表達資料不可得（符合 ZERO HALLUCINATION：說明 symbol 無效 / 無足夠資料）
And response 不含 "finance.yahoo.com"
```

---

## 覆蓋對照

| 設計要求（design） | Scenario |
|---|---|
| 即時報價 happy path（8 欄位、1 call） | S-01, S-02, S-03 |
| 基本面 happy path（present-only、無 forwardPE） | S-05, S-07 |
| 欄位探索 catalog + 可用性 | S-08 |
| 無效 ticker（全 0 / 空 metric）→ ValueError | S-04, S-06, J-03 |
| 缺 FINNHUB_API_KEY → call-time raise | S-09 |
| 429 → sanitized 外部錯誤、非內部 budget、不洩 key | S-10 |
| DECISION-001 citation 去 Yahoo、provider-name | S-11, J-01, J-02 |
| forwardPE 全面消失 | S-01, S-05, S-08, S-11, J-01, J-02 |
| config / dataset 改名 | S-12, S-13 |
| 端到端「問 AAPL 價格」→ finnhub_stock_quote + 引用 Finnhub | J-01 |
| 中文 LP-05 → 英文 ticker、中文回應 | J-02 |
