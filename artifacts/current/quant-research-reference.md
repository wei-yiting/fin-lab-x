# V3 Quant Research — Financial Metrics Reference

本文件是 `quant-research.md`（設計決策文件）的補充教材，說明各財務指標的意義、解讀方式、產業基準和應用情境。

## 美國上市公司的財報制度

- **10-Q**（季報）：每季出一份，一年出三份（Q1, Q2, Q3）
- **10-K**（年報）：每年出一份，涵蓋完整會計年度（Q4 不出 10-Q，而是出整年的 10-K）
- 美國沒有月報制度

## Fiscal Year（會計年度）

各公司的會計年度不同，「Q1」代表的實際月份因公司而異：

| 公司 | 會計年度結束日 | Q1 | Q2 | Q3 | Q4 |
|------|-------------|-----|-----|-----|-----|
| AMZN | 12/31（日曆年） | Jan-Mar | Apr-Jun | Jul-Sep | Oct-Dec |
| MSFT | 6/30 | Jul-Sep | Oct-Dec | Jan-Mar | Apr-Jun |
| AAPL | 9/27（不是月底） | Oct-Dec | Jan-Mar | Apr-Jun | Jul-Sep |
| NVDA | 1/25（不是月底） | Feb-Apr | May-Jul | Aug-Oct | Nov-Jan |
| CRM | 1/31 | Feb-Apr | May-Jul | Aug-Oct | Nov-Jan |

## 利潤漏斗結構

```
Revenue（營收）
 - Cost of Revenue（銷貨成本）
 = Gross Profit（毛利）        → Gross Margin = Gross Profit / Revenue
   - R&D（研發）
   - SGA（銷管）
   = Operating Income（營業利益）→ Operating Margin = Op Income / Revenue
     - Tax + Interest
     = Net Income（淨利）       → Net Margin = Net Income / Revenue
```

## 指標解讀指南

### Profitability（獲利能力）

| 指標 | 怎麼解讀 |
|------|---------|
| Gross Profit Margin | 軟體 >70%，硬體 30-50%。趨勢比絕對值重要 |
| Operating Margin | 反映核心業務獲利能力 |
| Net Profit Margin | 可能被一次性項目影響 |
| Effective Tax Rate | 用於解釋「為什麼某公司 net margin 高」——海外收入多的公司稅率低（15%），國內為主的公司稅率高（25%），導致 operating margin 相近但 net margin 差異大 |
| ROE | >20% 優秀，但大量回購會讓分母變小而虛高 |
| ROA | 不受資本結構影響。ROE >> ROA → 高槓桿 |

### Financial Health（財務健康）

| 指標 | 怎麼解讀 |
|------|---------|
| Debt-to-Equity Ratio | <1 保守，1-2 適中，>2 高槓桿。科技股可能因回購虛高 |
| Long-term Debt Ratio | 接近 1 = 大部分是長期債（穩定），接近 0 = 大量短期債（近期有再融資壓力） |
| Interest Coverage Ratio | >5 安全，<1.5 有違約風險 |
| Current Ratio | >1 安全，<1 需關注但不一定危險 |
| Net Debt | 負值 = 現金多於負債，非常健康 |
| Lease / Assets | 零售/航空/餐飲可能 >20%，輕資產公司 <5% |
| Goodwill / Assets | >30% 代表大量成長來自併購，需關注 impairment 風險 |
| FCF | 比 Net Income 更真實 |

### Growth（成長）

| 指標 | 怎麼解讀 |
|------|---------|
| Revenue Growth YoY | >20% 通常視為高速成長，注意基期效應 |
| Earnings Growth YoY | 獲利成長 > 營收成長 → operating leverage 改善 |
| CapEx / Revenue | 用於半導體 CapEx 排名等分析 |
| D&A / Revenue | SaaS ~5%、硬體 ~10%、半導體/雲端 ~15-20%。高 D&A 代表過去投入大量 CapEx，壓低帳面利潤但不是真的花錢 |
| Product Revenue % | 高佔比 → 受供應鏈風險（戰爭、關稅、油價）影響大。低佔比 → 偏服務型，受人力成本影響 |

### Per-Share Metrics（每股指標）

| 指標 | 怎麼解讀 |
|------|---------|
| Diluted EPS | 最常用的每股獲利指標 |
| FCF per Share | 比 EPS 更真實，排除非現金項目 |
| Revenue per Share | 追蹤公司規模與稀釋效果 |
| Share Count Change YoY | 負值 = 回購在消滅股份，正值 = 增資或 SBC 稀釋 |

### Revenue Quality（營收品質）

| 指標 | 怎麼解讀 |
|------|---------|
| RPO / Revenue | >2 代表有超過兩年的營收已鎖定，管道健康 |
| Current RPO % | 接近 1 = 多為短約；低 = 長期大合約多 |
| Deferred Revenue / Revenue | 成長中 = 客戶預付增加（正面）；下降 = 可能交付加速或新約減少 |
| Net Interest Income | 金融業核心：正值 = 賺利差，非金融業：負值正常（借錢有利息成本） |

### Capital Return（資本回報）

| 指標 | 怎麼解讀 |
|------|---------|
| Payout Ratio | >80% 可能不可持續，<30% 有提高空間 |
| Buyback / Net Income | 用於回購排名分析 |
| Buyback / Market Cap | 需要 JOIN market_valuations |

### Segment（部門）

| 指標 | 怎麼解讀 |
|------|---------|
| Segment Operating Margin | 比較各部門的獲利能力。例：AAPL Services ~75%，Products ~35% |
| Segment Revenue Share | 需要 JOIN quarterly_financials 或 annual_financials |
| Segment CapEx Intensity | 看各部門的資本投入比例，如 AWS vs AMZN 零售 |
| Segment Asset Efficiency | 每 $1 資產產生多少營收 |

### Geographic（地區）

| 指標 | 怎麼解讀 |
|------|---------|
| Region Revenue Share | 需要 JOIN quarterly_financials 或 annual_financials。看公司對特定市場的依賴程度 |
| Region Revenue Growth YoY | 看哪個市場在加速成長或衰退 |

## DDL 是什麼

DDL = **Data Definition Language**，是 SQL 裡用來定義資料庫結構的語法子集。最常見的 DDL statement 是 `CREATE TABLE`：

```sql
CREATE TABLE companies (
    ticker VARCHAR PRIMARY KEY,        -- 股票代碼
    company_name VARCHAR NOT NULL,     -- 公司名稱
    sector VARCHAR                     -- 產業大類
);
```

在 Text-to-SQL 的脈絡中，「DDL + COMMENT」指把 `CREATE TABLE` statements 加上每個欄位的註解放進 system prompt，讓 LLM 看到所有可用的表和欄位。
