# V3 Quant Research — 討論紀錄與設計決策

## 核心目標

讓 agent 能夠用 SQL 精確回答任何需要跨公司、跨時間、多條件篩選或計算的財務問題。
將「計算」的責任從 LLM 轉移到 SQL engine，解決 LLM 算數不可靠的痛點。

## 價值鏈

```
資料收集（yfinance + 10-K/10-Q）
  → 結構化儲存（DuckDB）
    → 精確查詢（Text-to-SQL）
      → LLM 解讀結果並回答使用者
```

## 架構決策

### Hybrid 資料路徑

V3 是 hybrid 架構，兩條資料路徑並存：

- **DuckDB**：負責歷史資料、跨公司比較、排序/篩選/聚合等計算密集型查詢
- **yfinance API（即時）**：負責單家公司的即時數據查詢（如「AAPL 現在股價多少？」）

DuckDB 的價值不是持久化，而是**計算引擎**——一條 SQL 完成 10 家公司 × 8 季的比較，取代 LLM 在 context 裡對著數字硬算。

### Text-to-SQL 分兩步

決定將 Text-to-SQL 拆成兩個 tool：

1. `text_to_sql`：LLM 生成 SQL
2. `duckdb_query`：執行 SQL 並回傳結果

理由：Observability 優先。在 Langfuse trace 裡可以清楚看到 LLM 生成了什麼 SQL，方便 evaluation 和 improvement。Tool call 次數翻倍在研究階段不是問題。

## DuckDB Schema 設計

### 三張表

| 表名 | 資料來源 | 一行代表 | 典型查詢場景 |
|------|---------|---------|-------------|
| `current_metrics` | yfinance `ticker.info` | 一家公司的最新快照 | 「誰的 P/E 最低？」「誰的 ROE 最高？」 |
| `quarterly_financials` | yfinance `.quarterly_financials` / `.quarterly_balance_sheet` / `.quarterly_cashflow` | 一家公司的一季 | 「過去 8 季營收趨勢？」「CapEx/Revenue 排名？」 |
| `segment_financials` | 10-K / 10-Q segment disclosure（透過 edgartools 抓取） | 一家公司的一個 segment 的一期 | 「AWS 成長多快？」「Reality Labs 虧多少？」 |

### 表間關係

```
current_metrics.ticker ──── quarterly_financials.ticker
                       └─── segment_financials.ticker
                            segment_financials.period ─── quarterly_financials.period
```

### 更新策略

- `quarterly_financials` + `segment_financials`：每季 earnings season 後跑一次 ETL（約每年 1、4、7、10 月）
- `current_metrics`：每日或每週更新（估值比率隨股價變動）
- 舊資料不刪除，SQL 用 `ORDER BY period DESC LIMIT N` 取最新

### 欄位命名原則

為了讓 Text-to-SQL 的 LLM 能正確選擇欄位，命名需要消除歧義：

- 百分比加 `_pct`（如 `gross_profit_margin_pct`）
- 金額加 `_usd`（如 `free_cash_flow_usd`）
- 比率加 `_ratio`（如 `debt_to_equity_ratio`）
- 用全稱不用縮寫（`price_to_earnings` 而非 `pe`）
- 時間範圍明確（`_yoy` = year-over-year, `_ttm` = trailing twelve months）

### Schema 放在哪裡

Schema 描述（DDL + COMMENT）放在 `text_to_sql` tool 的 system prompt 裡，讓 LLM 在生成 SQL 時能看到所有可用的表和欄位。V3 初版使用 DDL + COMMENT 格式即可。

## 資料來源分析

### yfinance 能提供的

**`ticker.info`（~150 key-value pairs，即時快照）：**

| 類別 | 欄位 |
|------|------|
| Valuation | `forwardPE`, `trailingPE`, `priceToBook`, `enterpriseToEbitda`, `enterpriseToRevenue` |
| Profitability | `grossMargins`, `operatingMargins`, `profitMargins`, `returnOnEquity`, `returnOnAssets` |
| Growth | `revenueGrowth`, `earningsGrowth` |
| Financial Health | `debtToEquity`, `currentRatio`, `freeCashflow`, `operatingCashflow`, `totalDebt`, `totalCash` |
| Dividend | `dividendYield`, `payoutRatio` |

**`ticker.quarterly_financials`（Income Statement，33 line items × ~5 quarters）：**
- Total Revenue, Cost Of Revenue, Gross Profit
- Operating Income, Operating Expense, R&D, SGA
- Net Income, EBITDA, EBIT, EPS
- Tax Provision, Pretax Income

**`ticker.quarterly_balance_sheet`（65 line items × ~6 quarters）：**
- Total Assets, Total Liabilities, Stockholders Equity
- Cash And Cash Equivalents, Total Debt, Net Debt
- Current Assets, Current Liabilities, Working Capital
- Accounts Receivable, Inventory, Accounts Payable

**`ticker.quarterly_cashflow`（46 line items × ~6 quarters）：**
- Operating Cash Flow, Free Cash Flow, Capital Expenditure
- Repurchase Of Capital Stock（buyback 金額）
- Cash Dividends Paid
- Stock Based Compensation

**`ticker.dividends`：** 完整的歷史配息紀錄

### yfinance 無法提供的（需要 10-K/10-Q 補齊）

**Segment-level 財務數據：**

| 公司 | Segments | yfinance 只有合計數 |
|------|----------|-------------------|
| AMZN | North America / International / AWS | 總營收 $716.9B（看不到 AWS $128.7B） |
| META | Family of Apps / Reality Labs | 總營收（看不到 Reality Labs 虧損 $-17B） |
| AAPL | Products / Services | 總營收（看不到 Services margin 75%） |
| MSFT | Intelligent Cloud / Productivity / Personal Computing | 總營收（看不到 Azure 成長率） |

**其他缺口：**
- Interest expense 沒有獨立欄位（無法計算 interest coverage ratio）
- 非標準指標如 recurring revenue %、AI revenue exposure 無法從任何結構化資料源取得

### 10-K 補齊的可行性

透過 edgartools 已確認可從 10-K 全文中取得 segment 表格。技術挑戰是將文字表格 parse 為結構化資料。10-K 為年報（一年一次），若需季度 segment 數據需改抓 10-Q。

## Golden Dataset 覆蓋率分析

### 純 v3 題目（9 題）

| # | 問題摘要 | 需要的資料 | yfinance 覆蓋 |
|---|---------|-----------|-------------|
| 5 | AI 概念股估值合理 | P/E, PEG, revenue growth | ✅（但 AI revenue 佔比無法取得） |
| 7 | 現金流強 + 大量回購 | FCF, buyback, net income | ✅ |
| 10 | 經濟衰退誰最抗跌 | margin stability, debt ratio | ⚠️（recurring revenue % 無法取得） |
| 14 | 半導體 CapEx/Revenue 排名 | CapEx, revenue | ✅ |
| 16 | 誰的負債最擔心 | debt-to-equity, net debt | ⚠️（interest coverage ratio 無法計算） |
| 18 | 高成長 + 已獲利篩選 | revenue growth, net income, FCF | ✅ |
| 23 | 回購排名 | buyback, market cap, net income | ✅ |
| 24 | 穩定配息推薦 | dividend yield, payout ratio, 配息歷史 | ✅ |
| 29 | 降息受惠 | debt, P/E, growth | ✅ |

**結論：9 題中 7 題完全覆蓋，2 題部分缺失但不致命。**

### v2+v3 題目中 v3 負責的部分（12 題）

| # | 問題摘要 | v3 需要的資料 | yfinance 覆蓋 | 10-K 可補齊 |
|---|---------|-------------|-------------|-----------|
| 2 | TSLA 非汽車收入 | segment revenue | ❌ | ✅ |
| 3 | NVDA vs AMD 估值 | P/E, P/S, PEG | ✅ | — |
| 4 | META Reality Labs 虧損 | segment operating loss | ❌ | ✅ |
| 9 | AWS vs Azure 成長 | segment revenue | ❌ | ✅ |
| 12 | 10 家選組合 | P/E, growth, margin | ✅ | — |
| 13 | CRM AI 轉型驗證 | margin, RPO | ⚠️ | ⚠️（RPO 揭露程度不一） |
| 15 | AMZN 廣告業務 | segment revenue | ❌ | ✅ |
| 20 | AI 泡沫情境 | segment breakdown | ❌ | ✅（部分公司） |
| 21 | AAPL Services 佔比 | segment revenue + margin | ❌ | ✅ |
| 27 | AI CapEx 排名 | CapEx | ✅（總額） | — |
| 28 | AMD data center 成長 | segment revenue | ❌ | ✅ |
| 30 | 長期持有推薦 | growth + valuation | ✅ | — |

## 欄位參考手冊（Domain Knowledge）

### 表 1: `current_metrics` 欄位定義

#### Valuation（估值）— 股票「貴不貴」

| DuckDB 欄位 | yfinance 來源 | 定義 | 怎麼解讀 |
|------------|--------------|------|---------|
| `trailing_price_to_earnings` | `trailingPE` | 股價 ÷ 過去 12 個月 EPS | 越低越「便宜」，但低也可能代表衰退。科技股 25-35 正常 |
| `forward_price_to_earnings` | `forwardPE` | 股價 ÷ 預估未來 12 個月 EPS | Forward < Trailing → 市場預期獲利成長 |
| `price_to_book_ratio` | `priceToBook` | 股價 ÷ 每股淨值 | 科技股通常很高（無形資產為主），參考價值較低 |
| `enterprise_value_to_ebitda_ratio` | `enterpriseToEbitda` | (市值+淨負債) ÷ EBITDA | 專業投資人偏好的估值指標，排除資本結構差異。15-25 正常 |
| `enterprise_value_to_revenue_ratio` | `enterpriseToRevenue` | (市值+淨負債) ÷ 年營收 | 用於尚未穩定獲利的高成長公司 |
| `market_cap_usd` | `marketCap` | 股價 × 流通股數 | 公司規模，也用於計算 buyback/market cap 比例 |

#### Profitability（獲利能力）— 賺錢效率

利潤的漏斗結構：營收 → 毛利（扣生產成本）→ 營業利益（扣研發+銷管）→ 淨利（扣稅+利息）

| DuckDB 欄位 | yfinance 來源 | 定義 | 怎麼解讀 |
|------------|--------------|------|---------|
| `gross_profit_margin_pct` | `grossMargins` | (營收-銷貨成本) ÷ 營收 | 軟體 >70%，硬體 30-50%。趨勢比絕對值重要 |
| `operating_margin_pct` | `operatingMargins` | 營業利益 ÷ 營收 | 反映核心業務經營效率，包含 R&D 和 SGA |
| `profit_margin_pct` | `profitMargins` | 淨利 ÷ 營收 | 最終底線，可能被一次性項目影響 |
| `return_on_equity_pct` | `returnOnEquity` | 淨利 ÷ 股東權益 | >20% 優秀，但高槓桿（大量回購）會虛高 |
| `return_on_assets_pct` | `returnOnAssets` | 淨利 ÷ 總資產 | 不受資本結構影響，ROE>>ROA 代表高槓桿 |

#### Growth（成長）

| DuckDB 欄位 | yfinance 來源 | 定義 | 怎麼解讀 |
|------------|--------------|------|---------|
| `revenue_growth_yoy_pct` | `revenueGrowth` | 營收同比成長率 | >20% 通常視為高速成長，注意基期效應 |
| `earnings_growth_yoy_pct` | `earningsGrowth` | 獲利同比成長率 | 獲利成長 > 營收成長 → operating leverage 改善 |

#### Financial Health（財務健康）— 會不會出問題

| DuckDB 欄位 | yfinance 來源 | 定義 | 怎麼解讀 |
|------------|--------------|------|---------|
| `debt_to_equity_ratio` | `debtToEquity` | 總負債 ÷ 股東權益 | <1 保守，1-2 適中，>2 高槓桿。科技股可能因回購而虛高 |
| `current_ratio` | `currentRatio` | 流動資產 ÷ 流動負債 | >1 = 短期償債安全。<1 不一定危險但需關注 |
| `free_cash_flow_usd` | `freeCashflow` | 營業現金流 - 資本支出 | 真正可自由運用的現金，比 net income 更真實 |
| `operating_cash_flow_usd` | `operatingCashflow` | 營運活動實際收到的現金 | 排除會計調整，反映真實現金進帳 |
| `total_debt_usd` | `totalDebt` | 公司總負債 | 搭配 total_cash 看 net debt |
| `total_cash_usd` | `totalCash` | 公司總現金 | net debt = total_debt - total_cash |

#### Dividend（股利）

| DuckDB 欄位 | yfinance 來源 | 定義 | 怎麼解讀 |
|------------|--------------|------|---------|
| `dividend_yield_pct` | `dividendYield` | 年配息 ÷ 股價 | 科技股通常 <1%，高殖利率可能是股價暴跌造成 |
| `payout_ratio_pct` | `payoutRatio` | 配息 ÷ 淨利 | >80% 配息可能不可持續，<30% 有提高空間 |

#### 其他

| DuckDB 欄位 | yfinance 來源 | 定義 | 怎麼解讀 |
|------------|--------------|------|---------|
| `beta` | `beta` | 個股相對大盤的波動幅度 | >1 波動大於大盤，<1 波動小於大盤。Q29（降息受惠）參考 |

### 表 2: `quarterly_financials` 欄位定義

#### Income Statement（損益表）— 一季賺了多少

結構為漏斗：營收 → 毛利 → 營業利益 → 淨利

| DuckDB 欄位 | yfinance 來源 | 定義 | Golden Dataset 用途 |
|------------|--------------|------|-------------------|
| `total_revenue_usd` | `Total Revenue` | 總營收 | 成長趨勢、CapEx/Revenue 計算 |
| `cost_of_revenue_usd` | `Cost Of Revenue` | 銷貨成本（直接生產成本） | 計算毛利率趨勢 |
| `gross_profit_usd` | `Gross Profit` | 營收 - 銷貨成本 | 毛利率 = gross_profit / revenue |
| `research_and_development_usd` | `Research And Development` | 研發費用 | 判斷公司投資力度 |
| `selling_general_admin_usd` | `Selling General And Administration` | 銷管費用 | 判斷營運效率 |
| `operating_income_usd` | `Operating Income` | 毛利 - 營運費用 | 核心業務獲利 |
| `net_income_usd` | `Net Income` | 最終利潤（扣完所有成本） | Q18（已獲利篩選） |
| `ebitda_usd` | `EBITDA` | 稅前息前折舊前利潤 | 排除非現金費用的獲利指標 |
| `diluted_eps` | `Diluted EPS` | 每股盈餘（考慮稀釋） | P/E 的分母 |

#### Balance Sheet（資產負債表）— 某時點的財務狀況

| DuckDB 欄位 | yfinance 來源 | 定義 | Golden Dataset 用途 |
|------------|--------------|------|-------------------|
| `total_assets_usd` | `Total Assets` | 全部資產 | ROA 的分母 |
| `total_debt_usd` | `Total Debt` | 全部負債 | Q16（負債排名） |
| `net_debt_usd` | `Net Debt` | 負債 - 現金 | 負值 = 現金 > 負債 |
| `cash_and_equivalents_usd` | `Cash And Cash Equivalents` | 現金部位 | 財務安全墊 |
| `stockholders_equity_usd` | `Stockholders Equity` | 總資產 - 總負債 | D/E ratio 的分母 |
| `current_assets_usd` | `Current Assets` | 1 年內可變現的資產 | current ratio 分子 |
| `current_liabilities_usd` | `Current Liabilities` | 1 年內要還的債 | current ratio 分母 |
| `accounts_receivable_usd` | `Accounts Receivable` | 客戶欠款 | 應收帳款異常增加 = 可能有收款問題 |
| `inventory_usd` | `Inventory` | 存貨 | 存貨異常增加 = 可能有滯銷問題 |

#### Cash Flow Statement（現金流量表）— 現金怎麼流動

| DuckDB 欄位 | yfinance 來源 | 定義 | Golden Dataset 用途 |
|------------|--------------|------|-------------------|
| `operating_cash_flow_usd` | `Operating Cash Flow` | 營業活動產生的現金 | 比 net income 更真實的獲利指標 |
| `capital_expenditure_usd` | `Capital Expenditure` | 購買設備/廠房支出 | Q14（CapEx/Revenue）、Q27（AI CapEx） |
| `free_cash_flow_usd` | `Free Cash Flow` | 營業現金流 - CapEx | Q7（現金流強的公司） |
| `stock_buyback_usd` | `Repurchase Of Capital Stock` | 回購股票金額（負數=流出） | Q23（回購排名） |
| `dividends_paid_usd` | `Cash Dividends Paid` | 發放股利金額（負數=流出） | Q24（配息穩定性） |
| `stock_based_compensation_usd` | `Stock Based Compensation` | 員工股票獎酬（非現金費用） | 科技公司的隱性成本，稀釋股東 |

### 表 3: `segment_financials` 欄位定義

| DuckDB 欄位 | 來源 | 定義 | Golden Dataset 用途 |
|------------|------|------|-------------------|
| `ticker` | — | 公司代碼 | JOIN key |
| `period` | 10-K/10-Q filing period | 報告期間 | JOIN key |
| `segment_name` | SEC filing segment disclosure | 業務部門名稱 | 如 AWS, Reality Labs, Services |
| `segment_revenue_usd` | SEC filing | 該部門營收 | Q9（AWS vs Azure）、Q21（AAPL Services） |
| `segment_operating_income_usd` | SEC filing | 該部門營業利益（可為負） | Q4（Reality Labs 虧損）、利潤集中度分析 |

Segment operating margin = segment_operating_income / segment_revenue，可用於判斷各部門的獲利效率。

## 待決定事項

- [ ] 具體收錄哪些公司（Golden Dataset 涵蓋：AAPL, MSFT, GOOGL, AMZN, META, NVDA, TSLA, AVGO, AMD, CRM）
- [ ] 各表的具體欄位清單與 yfinance field → DuckDB column 的完整 mapping
- [ ] 10-K/10-Q segment data 的 parsing 策略（LLM extraction vs rule-based parsing）
- [ ] ETL pipeline 的技術實作（script 架構、排程方式、error handling）
- [ ] Text-to-SQL prompt 設計（schema description 格式、few-shot examples 選擇）
- [ ] 實作順序：先做 yfinance 路線（表 1 + 表 2）跑通 Text-to-SQL，再加 10-K 路線（表 3）
