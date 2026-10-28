# text_to_sql smoke results（DEV-224）

> 歷史紀錄：這份結果是在 tool 還叫 `text_to_sql`、引用還用「資料來源」表格的時候錄的。tool 已改名為 `company_fundamentals_query`，引用也改成 `[N]: sql://…`。

本機 quant profile，透過 `POST /api/v1/chat/invoke` 執行。每題使用新的 session。資料是 2026-10-27 的 yfinance ingest。**這不是 eval**：每題只跑一次，沒有 grader；標準答案見 `text_to_sql_eval_seed.yaml`。

| # | 問題 | 預期路由 | 實際 tool 呼叫 | text_to_sql status / 失敗次數 / rows | 秒 |
|---|---|---|---|---|---|
| Q1 | 上一季哪家公司毛利率最高？ | text_to_sql | text_to_sql | ok / 0 / 23 | 10.9 |
| Q2 | Compare NVDA and INTC revenue over the last 4 quarters. | text_to_sql | text_to_sql | ok / 0 / 8 | 17.6 |
| Q3 | KO 和 PEP 誰的 forward P/E 比較低？ | text_to_sql | text_to_sql | ok / 0 / 2 | 9.6 |
| Q4 | 2026 前三季營收最高的是哪家？ | text_to_sql | text_to_sql | ok / 0 / 23 | 13.2 |
| Q5 | Apple 10-K 怎麼描述供應鏈風險？ | sec_filing_search | sec_filing_search | — | 12.2 |
| Q6 | Apple 怎麼描述它的 AI 投資？它的研發佔營收比多少？ | sec_filing_search + text_to_sql | sec_filing_search → text_to_sql | ok / 0 / 2 | 17.7 |
| Q7 | Apple 2019 年營收多少？ | text_to_sql (no_rows) | text_to_sql → sec_filing_search | no_rows / 0 / 0 | 26.9 |
| Q8 | 台積電上一季營收多少？ | 名單外 → Finnhub / Tavily | tavily_financial_search → tavily_financial_search → finnhub_company_basic_financials → tavily_financial_search | — | 32.7 |

## Q1 — 上一季哪家公司毛利率最高？

**Tool** `text_to_sql` args: `{"question": "Gross margin of every covered company in its latest reported quarter, ranked highest first. Include each company's fiscal year, fiscal quarter, period end date, gross profit, total revenue, and gross margin percentage."}`

status `ok`, rows 23, failed attempts 0

```sql
WITH latest_quarters AS (
    SELECT
        ticker,
        period_end,
        fiscal_year,
        fiscal_quarter,
        calendar_year,
        calendar_quarter,
        gross_profit_usd,
        total_revenue_usd,
        gross_margin_pct
    FROM quarterly_metrics
    QUALIFY ROW_NUMBER() OVER (
        PARTITION BY ticker
        ORDER BY period_end DESC
    ) = 1
)
SELECT
    ticker,
    fiscal_year,
    fiscal_quarter,
    calendar_year,
    calendar_quarter,
    period_end,
    gross_profit_usd,
    total_revenue_usd,
    gross_margin_pct,
    ROW_NUMBER() OVER (
        ORDER BY gross_margin_pct DESC NULLS LAST
    ) AS gross_margin_rank
FROM latest_quarters
ORDER BY gross_margin_pct DESC NULLS LAST, ticker
LIMIT 50
```

**Answer**

<blockquote>

**Meta（META）在各公司最新公布季度的比較中毛利率最高，為 79.31%**，對應 FY2026 Q3（截至 2026-09-30）；毛利約 **$51.23B**、營收約 **$64.60B**。[1]

注意：各公司的「上一季」是各自最新報告季度，期間並不完全一致。BRK.B 與 JPM 未報告可比較的毛利，因此未納入排名。

**資料來源**

| # | 來源 | 資料 | 數值 → 結果 |
|---|---|---|---|
| [1] | yfinance via FinLab-X fundamentals database | META FY2026 Q3（截至 2026-09-30） | $51.23B 毛利 ÷ $64.60B 營收 → 毛利率 79.31% |

</blockquote>

## Q2 — Compare NVDA and INTC revenue over the last 4 quarters.

**Tool** `text_to_sql` args: `{"question": "Compare total revenue for NVDA and INTC in each company's last 4 reported quarters, showing ticker, fiscal year, fiscal quarter, period end date, and revenue in USD. Include the quarter-over-quarter revenue change percentage where available."}`

status `ok`, rows 8, failed attempts 0

```sql
WITH last_four AS (
    SELECT
        ticker,
        fiscal_year,
        fiscal_quarter,
        period_end,
        total_revenue_usd,
        LAG(total_revenue_usd) OVER (
            PARTITION BY ticker
            ORDER BY period_end
        ) AS prior_quarter_revenue_usd
    FROM quarterly_metrics
    WHERE ticker IN ('NVDA', 'INTC')
    QUALIFY ROW_NUMBER() OVER (
        PARTITION BY ticker
        ORDER BY period_end DESC
    ) <= 4
)
SELECT
    ticker,
    fiscal_year,
    fiscal_quarter,
    period_end,
    total_revenue_usd,
    prior_quarter_revenue_usd,
    CASE
        WHEN prior_quarter_revenue_usd IS NOT NULL
             AND prior_quarter_revenue_usd <> 0
        THEN (total_revenue_usd - prior_quarter_revenue_usd)
             / prior_quarter_revenue_usd * 100.0
        ELSE NULL
    END AS revenue_qoq_change_pct
FROM last_four
ORDER BY ticker, period_end
```

**Answer**

<blockquote>

## Conclusion

NVDA generated substantially more revenue than INTC in each of their latest four reported quarters. NVDA’s quarterly revenue rose from **$57.0B to $96.2B**, while INTC’s increased from **$13.7B to $16.1B**. Across these four quarters, NVDA generated approximately **$313.0B** of revenue versus **$55.0B** for INTC—about **5.7× more**.

| Company | Fiscal quarter ended | Revenue | QoQ change |
|---|---:|---:|---:|
| NVDA | FY2026 Q3 — 2025-10-31 | $57.0B [1] | +22.0% |
| NVDA | FY2026 Q4 — 2026-01-31 | $68.1B [2] | +19.5% |
| NVDA | FY2027 Q1 — 2026-04-30 | $81.6B [3] | +19.8% |
| NVDA | FY2027 Q2 — 2026-07-31 | $96.2B [4] | +17.9% |
| INTC | FY2025 Q3 — 2025-09-30 | $13.7B [5] | +6.2% |
| INTC | FY2025 Q4 — 2025-12-31 | $13.7B [6] | +0.2% |
| INTC | FY2026 Q1 — 2026-03-31 | $13.6B [7] | −0.7% |
| INTC | FY2026 Q2 — 2026-06-30 | $16.1B [8] | +18.8% |

NVDA’s revenue expanded every quarter in the retrieved period, although its sequential growth rate moderated from **22.0%** to **17.9%**. INTC was broadly flat through FY2026 Q1 before a stronger increase in FY2026 Q2. The companies’ fiscal quarter dates do not align exactly, so this is a comparison of each company’s latest four reported quarters rather than identical calendar periods.

**Data sources**

| # | Source | Data | Values → result |
|---|---|---|---|
| [1] | yfinance via FinLab-X fundamentals database | NVDA FY2026 Q3, ended 2025-10-31 | Revenue $57.0B; QoQ change +22.0% |
| [2] | yfinance via FinLab-X fundamentals database | NVDA FY2026 Q4, ended 2026-01-31 | Revenue $68.1B; QoQ change +19.5% |
| [3] | yfinance via FinLab-X fundamentals database | NVDA FY2027 Q1, ended 2026-04-30 | Revenue $81.6B; QoQ change +19.8% |
| [4] | yfinance via FinLab-X fundamentals database | NVDA FY2027 Q2, ended 2026-07-31 | Revenue $96.2B; QoQ change +17.9% |
| [5] | yfinance via FinLab-X fundamentals database | INTC FY2025 Q3, ended 2025-09-30 | Revenue $13.7B; QoQ change +6.2% |
| [6] | yfinance via FinLab-X fundamentals database | INTC FY2025 Q4, ended 2025-12-31 | Revenue $13.7B; QoQ change +0.2% |
| [7] | yfinance via FinLab-X fundamentals database | INTC FY2026 Q1, ended 2026-03-31 | Revenue $13.6B; QoQ change −0.7% |
| [8] | yfinance via FinLab-X fundamentals database | INTC FY2026 Q2, ended 2026-06-30 | Revenue $16.1B; QoQ change +18.8% |

</blockquote>

## Q3 — KO 和 PEP 誰的 forward P/E 比較低？

**Tool** `text_to_sql` args: `{"question": "Compare the forward P/E valuation ratio of KO and PEP using the latest available valuation snapshot in the FinLab-X fundamentals database. Return forward P/E, as_of_date, and identify which company is lower."}`

status `ok`, rows 2, failed attempts 0

```sql
WITH latest_valuations AS (
    SELECT
        mv.ticker,
        c.company_name,
        mv.as_of_date,
        mv.forward_price_to_earnings,
        ROW_NUMBER() OVER (
            PARTITION BY mv.ticker
            ORDER BY mv.as_of_date DESC
        ) AS rn
    FROM market_valuations AS mv
    JOIN companies AS c
        ON c.ticker = mv.ticker
    WHERE mv.ticker IN ('KO', 'PEP')
)
SELECT
    ticker,
    company_name,
    as_of_date,
    forward_price_to_earnings,
    CASE
        WHEN forward_price_to_earnings = MIN(forward_price_to_earnings) OVER ()
            THEN 'Lower forward P/E'
        ELSE 'Higher forward P/E'
    END AS comparison
FROM latest_valuations
WHERE rn = 1
ORDER BY forward_price_to_earnings ASC NULLS LAST
```

**Answer**

<blockquote>

**PEP 的 forward P/E 較低。**

- **PEP：15.68 倍**（估值快照截至 2026-10-27）[1]
- **KO：26.30 倍**（估值快照截至 2026-10-27）[2]

因此，PEP 比 KO 低約 **10.62 倍**。

**資料來源**

| # | Source | Data | Values → result |
|---|---|---|---|
| [1] | yfinance via FinLab-X fundamentals database（as of 2026-10-27） | PEP valuation snapshot | forward P/E = 15.68 倍 |
| [2] | yfinance via FinLab-X fundamentals database（as of 2026-10-27） | KO valuation snapshot | forward P/E = 26.30 倍 |

</blockquote>

## Q4 — 2026 前三季營收最高的是哪家？

**Tool** `text_to_sql` args: `{"question": "Among all covered companies, which company had the highest total revenue in calendar 2026 Q1-Q3 (the first three calendar quarters of 2026)? Return each comparable company's total revenue for that calendar window, the fiscal periods and end dates covered, quarters covered versus expected, and identify the highest."}`

status `ok`, rows 23, failed attempts 0

```sql
WITH window_metrics AS (
    SELECT
        pm.*,
        c.company_name,
        (pm.quarters_covered = pm.quarters_expected) AS is_comparable
    FROM period_metrics(2026, 1, 3) AS pm
    LEFT JOIN companies AS c
        ON c.ticker = pm.ticker
),
ranked AS (
    SELECT
        *,
        CASE
            WHEN is_comparable THEN
                RANK() OVER (
                    PARTITION BY is_comparable
                    ORDER BY total_revenue_usd DESC NULLS LAST
                )
        END AS comparable_revenue_rank
    FROM window_metrics
)
SELECT
    ticker,
    company_name,
    calendar_year,
    calendar_quarter_from,
    calendar_quarter_to,
    first_period_end,
    last_period_end,
    quarters_covered,
    quarters_expected,
    is_comparable,
    total_revenue_usd,
    comparable_revenue_rank,
    (is_comparable AND comparable_revenue_rank = 1) AS is_highest
FROM ranked
ORDER BY
    is_comparable DESC,
    comparable_revenue_rank ASC NULLS LAST,
    total_revenue_usd DESC NULLS LAST,
    ticker
LIMIT 50
```

**Answer**

<blockquote>

在目前資料庫中，**Costco（COST）**是 **2026 年前三個曆季**營收最高的公司，合計約 **2,358.5 億美元**。[1]

- 覆蓋期間：2025 年 12 月至 2026 年 8 月  
- 期間結束日：2026-02-28 至 2026-08-31  
- 已涵蓋完整 3 個季度，因此可納入比較。  
- Meta 排名第二，營收約 1,817.1 億美元；但多數公司尚未涵蓋完整三季，資料庫未將其列入可比排名。

**資料來源**

| # | Source | Data | Values → result |
|---|---|---|---|
| [1] | yfinance via FinLab-X fundamentals database | COST，2026 年曆年前三季；期間結束日 2026-02-28 至 2026-08-31 | 營收合計 **$235.847B** → 可比公司中排名第 1 |

</blockquote>

## Q5 — Apple 10-K 怎麼描述供應鏈風險？

**Tool** `sec_filing_search` args: `{"query": "supply chain risk concentration suppliers manufacturing in Asia single-source components logistics disruptions tariffs and geopolitical events", "ticker": "AAPL", "fiscal_year": null}`

**Answer**

<blockquote>

Apple 在 **FY2025 10-K（財政年度截至 2025-09-27）** 中，將供應鏈風險描述為多層次且相互交織的風險，核心包括：

- **製造與供應高度集中於海外及特定地區**：Apple 表示，其絕大多數製造由外包夥伴完成，主要位於中國大陸、印度、日本、南韓、台灣及越南；全球供應鏈的集中性可能放大地緣政治衝突或其他中斷的影響。[1]
- **依賴單一或少數供應商**：部分關鍵零組件來自單一或有限來源；新產品尤其可能採用只能由單一供應商提供的客製化零組件。因此，供應商故障、產能不足、產業整併或無法續約，都可能造成短缺及價格上升。[2][3]
- **外包降低直接控制力**：Apple 依賴外包夥伴進行零組件製造、硬體組裝及部分物流管理。這雖然有助於降低營運成本，但也減少 Apple 對生產與配送的直接控制，可能影響產品成本、品質、數量及應變彈性。[2]
- **供應短缺與價格波動**：即使某些零組件有多個供應來源，也可能受到整個產業的短缺及商品價格大幅波動影響；半導體供應不足就是 Apple 明確提到的歷史風險。[2]
- **關稅、出口管制與地緣政治**：貿易限制可能提高產品、零組件、稀土及其他原材料的成本，或限制其供應；Apple 也可能因此被迫更換供應商、重組業務關係或調整產品銷售。FY2025 10-K 特別提到 2025 年新增及可能持續變化的美國關稅措施。[1][4]
- **自然災害、疫情及營運事故**：供應商和代工廠所在地可能面臨地震、極端天氣、火災、停電、工業事故、勞資爭議、公共衛生事件及網路攻擊。這些事件可能導致生產與交付延遲、成本上升，並需要大量時間及支出才能恢復。[5]
- **供應商行為與品質風險**：Apple 依賴供應商遵守其供應商行為準則，但違規事件仍可能發生，並損害 Apple 的業務、聲譽及財務表現。[2]

**總結而言，Apple 的 10-K 並非只把供應鏈風險視為「零組件短缺」問題，而是強調其海外製造集中、單一來源依賴、外包控制力有限，以及貿易、地緣政治和自然災害等因素可能同時衝擊供應、成本、產品上市及毛利率。**

[1]: sec://0000320193-25-000079/1a#15  
[2]: sec://0000320193-25-000079/1a#21  
[3]: sec://0000320193-25-000079/1a#22  
[4]: sec://0000320193-25-000079/7#65  
[5]: sec://0000320193-25-000079/1a#17

</blockquote>

## Q6 — Apple 怎麼描述它的 AI 投資？它的研發佔營收比多少？

**Tool** `sec_filing_search` args: `{"query": "artificial intelligence investment strategy research and development AI capabilities infrastructure and products", "ticker": "AAPL", "fiscal_year": null}`

**Tool** `text_to_sql` args: `{"question": "R&D to revenue ratio of AAPL in its latest reported quarter and latest fiscal year; return R&D expense, total revenue, ratio, fiscal label, and period end date for both periods"}`

status `ok`, rows 2, failed attempts 0

```sql
WITH latest_quarter AS (
    SELECT
        ticker,
        'Latest reported quarter' AS period_type,
        fiscal_year,
        fiscal_quarter,
        period_end,
        research_and_development_usd,
        total_revenue_usd,
        rd_to_revenue_pct
    FROM quarterly_metrics
    WHERE ticker = 'AAPL'
    QUALIFY ROW_NUMBER() OVER (
        PARTITION BY ticker
        ORDER BY period_end DESC
    ) = 1
),
latest_fiscal_year AS (
    SELECT
        ticker,
        'Latest fiscal year' AS period_type,
        fiscal_year,
        CAST(NULL AS INTEGER) AS fiscal_quarter,
        period_end,
        research_and_development_usd,
        total_revenue_usd,
        rd_to_revenue_pct
    FROM annual_metrics
    WHERE ticker = 'AAPL'
    QUALIFY ROW_NUMBER() OVER (
        PARTITION BY ticker
        ORDER BY period_end DESC
    ) = 1
)
SELECT
    ticker,
    period_type,
    fiscal_year,
    fiscal_quarter,
    period_end,
    research_and_development_usd,
    total_revenue_usd,
    rd_to_revenue_pct
FROM latest_quarter
UNION ALL
SELECT
    ticker,
    period_type,
    fiscal_year,
    fiscal_quarter,
    period_end,
    research_and_development_usd,
    total_revenue_usd,
    rd_to_revenue_pct
FROM latest_fiscal_year
ORDER BY period_type
```

**Answer**

<blockquote>

**結論：Apple 並未在 FY2025 10-K 中單獨揭露「AI 投資金額」或一項獨立的 AI 預算。**它是以更廣義的研發與技術創新來描述相關投入：Apple 表示，競爭力高度依賴持續推出創新產品、服務與技術，因此持續透過研發、智慧財產授權及收購第三方企業與技術來擴大產品範圍。[1] 同時，Apple 將機器學習與人工智慧列為新興技術，並指出其可能帶來訓練資料著作權、輸出內容及第三方智慧財產權等風險。[2]

在研發費用方面：

- **最新年度：FY2025**：研發費用 **345.5 億美元**，營收 **4,161.61 億美元**，研發佔營收 **8.30%**。[3]  
  SEC FY2025 10-K 顯示的會計年度截止日為 **2025-09-27**；資料庫該年度的 period end 顯示為 **2025-09-30**，兩者存在日期差異，比例仍採資料庫計算值。
- **最新已報告季度：FY2026 Q3，截至 2026-06-30**：研發費用 **117.29 億美元**，營收 **1,094.17 億美元**，研發佔營收 **10.72%**。[4]

此外，Apple 的 10-K 表示，FY2025 研發費用增加主要來自**人事相關支出與基礎設施相關成本上升**；但該摘錄沒有把這些成本進一步拆分為 AI 投資。[5]

**資料來源**

| # | Source | Data | Values → result |
|---|---|---|---|
| [3] | yfinance via FinLab-X fundamentals database | AAPL FY2025（資料庫 period end：2025-09-30） | 研發費用 $34.55B ÷ 營收 $416.161B → 研發佔營收 8.30% |
| [4] | yfinance via FinLab-X fundamentals database | AAPL FY2026 Q3（截至 2026-06-30） | 研發費用 $11.729B ÷ 營收 $109.417B → 研發佔營收 10.72% |

[1]: sec://0000320193-25-000079/1#8  
[2]: sec://0000320193-25-000079/1a#25  
[5]: sec://0000320193-25-000079/7#78

</blockquote>

## Q7 — Apple 2019 年營收多少？

**Tool** `text_to_sql` args: `{"question": "What was Apple's (AAPL) total revenue in fiscal year 2019, meaning the fiscal year ended in 2019? Return the revenue in USD and the fiscal year-end date."}`

status `no_rows`, rows 0, failed attempts 0

```sql
SELECT
    ticker,
    fiscal_year,
    period_end,
    total_revenue_usd
FROM annual_metrics
WHERE ticker = 'AAPL'
  AND fiscal_year = 2019
```

**Tool** `sec_filing_search` args: `{"query": "total net sales revenue for fiscal year 2019 and fiscal year ended date", "ticker": "AAPL", "fiscal_year": 2019}`

**Answer**

<blockquote>

Apple 2019 財政年度（截至 **2019 年 9 月 28 日**）營收為 **2,601.74 億美元**（即 **260,174 百萬美元**）。[1]

補充：FinLab-X 基本面資料庫目前僅涵蓋 2022–2026 財政年度，因此無法直接提供 2019 年的數據。

[1]: sec://0000320193-19-000119/unknown#43

</blockquote>

## Q8 — 台積電上一季營收多少？

**Tool** `tavily_financial_search` args: `{"query": "TSM TSMC latest reported quarter revenue previous quarter revenue", "ticker": "TSM"}`

**Tool** `tavily_financial_search` args: `{"query": "TSMC December 2025 quarter exact revenue NT dollars Q4 2025", "ticker": "TSM"}`

**Tool** `finnhub_company_basic_financials` args: `{"ticker": "TSM"}`

**Tool** `tavily_financial_search` args: `{"query": "TSMC fourth quarter 2025 revenue NT$ exact 2025 December quarter earnings revenue", "ticker": "TSM"}`

**Answer**

<blockquote>

若你指台積電最新已公布的 **2025 年第四季（10–12月）**，營收為 **超過新台幣 1 兆元**，年增 **20.5%**；目前檢索到的報導未列出更精確的金額。[1]

[1]: https://www.cnbc.com/2026/01/15/tsmc-q4-profit-record-ai-chip-demand-nt1-trillion.html "TSMC extends record quarter, profit jumps 35% on robust AI chip demand"

</blockquote>
