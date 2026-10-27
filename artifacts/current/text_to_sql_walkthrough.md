# text_to_sql prototype walkthrough（DEV-224）

> 讀者：Dong（明天 10/28 16:00 面試要 demo、要能講清楚每一步）。預計閱讀 30 分鐘。
> 範圍：本機 prototype，**沒有做 eval**。設計決策來自 10/27 的 grilling（Q1–Q18），正式紀錄在 ADR-0022、ADR-0023、`CONTEXT.md`，以及 Linear DEV-224。

---

## 0. 怎麼跑 demo（3 個指令）

```bash
uv run python -m backend.scripts.ingest_yfinance_fundamentals
```

（只要第一次跑，或想更新資料時再跑。在 Mac 上大約 1 分鐘，23/23 檔成功，會產生 `data/fundamentals.db`。）

`backend/.env` 要有 `WORKFLOW_PROFILE=quant`。我已經幫 worktree 的 `.env` 加好了；沒有設的話，預設載入 `baseline`。

```bash
uv run uvicorn backend.api.main:app --port 8000
```

```bash
pnpm --dir frontend dev
```

打開 http://localhost:5173。RAG 那一半需要本機的 Qdrant 開著（`docker compose up qdrant`），而本機的 collection 已經有 universe 內大部分公司的 10-K。

> 今晚我驗證時，用的是 8001 / 5191 這兩個 port，因為 8000 / 5173 可能被其他 worktree 佔用。

---

## 1. 一張圖看完資料流

```
          ┌──────────── Ingest（本機、一次性）────────────┐
 yfinance ─► yfinance_fetcher ─► normalize_fiscal_period ─► upsert_rows ─► DuckDB 原始表
 (info + 季/年三表)  欄位對照、怪值處理   (含 52/53 週 snap)      (idempotent)   companies / market_valuations /
                                                                             quarterly_financials / annual_financials
          └────────────────────────────────────────────────┘
                                   │  schema.sql 每次連線都會套用
                                   ▼
          ┌──────────── 語意層（DB 內、確定性）── ADR-0023 ──┐
          │ quarterly_metrics VIEW   annual_metrics VIEW      │  ← 衍生比率、calendar quarter
          │ period_metrics(year, q_from, q_to) TABLE MACRO    │  ← 區間加總規則、coverage
          └────────────────────────────────────────────────┘
                                   ▲ 唯讀查詢
 使用者問題 ─► Orchestrator（quant profile：reader 的工具 + text_to_sql）
                │  依 system prompt 的分工選工具
                ├─ 10-K 文字 ─────► sec_filing_search（RAG，原本的）
                ├─ 即時股價 / 名單外公司 ─► Finnhub / Tavily
                └─ 結構化數字 ────► text_to_sql(question) ── ADR-0022
                                     ┌ attempt 1..3 ───────────────────────────┐
                                     │ LLM 寫 SQL（schema 由 DB 的 COMMENT 產生）│
                                     │ → 檢查：DuckDB parser 只允許 1 個 SELECT │
                                     │ → 執行：唯讀連線 + 禁止外部存取           │
                                     │ → 出錯：錯誤訊息餵回下一次 attempt        │
                                     └──────────────────────────────────────────┘
                                     回傳 {status, sql, rows≤50, attempts, coverage?}
                │
                ▼
 答案：本文的數字標 [N]，底部「資料來源」表格列出 yfinance、公司、期間、原始數值 → 結果
```

**一句話版本**：LLM 只負責「**解讀**問題、選對物件和期間」；公式、加總規則、時間對齊都由 **DB 層**決定；安全性由 **DB 引擎層**保證，不依賴 prompt。

---

## 2. 資料層：yfinance ingest

模組：`backend/ingestion/fundamentals_pipeline/yfinance_fetcher.py`。CLI：`backend/scripts/ingest_yfinance_fundamentals.py`。

| 做什麼 | 怎麼做 | 為什麼 |
|---|---|---|
| 寫哪幾張表 | `companies`、`market_valuations`（as_of = 當天）、`quarterly_financials`、`annual_financials` | yfinance 填得了的就這 4 張；SEC 專屬欄位保持 NULL |
| 欄位對照 | 每個 DDL 欄位對應一組 yfinance 欄位名稱，取第一個有值的（例：利息收入先找 `Interest Income`，再找 `Interest Income Non Operating`） | 不同產業的欄位名稱不同（銀行 vs 一般公司） |
| fiscal 季度標籤 | 一律用 foundation 的 `normalize_fiscal_period()`（照 design master §8 的契約） | 跨公司統一的 `(fiscal_year, fiscal_quarter)` |
| 52/53 週會計年度 | 期末日期是當月 1–7 日 → 視為上個月底（`snap_period_end`）。FYE 月份也用同一個規則推算 | 修掉 DEV-73 C6：原本 FYE 飄到 2/1 會直接 `ValueError` |
| **沒有營收的期間直接跳過** | 一季沒有 `total_revenue_usd`，就不算「已公布的季度」 | **實測才發現**：yfinance 會吐出尚未完整公布的季度（只有零星欄位，例如 AMZN 2026-06-30、JPM 2026-09-30）。如果不跳過，它會變成該公司的「最新一季」 |
| yfinance 怪值 | `dividendYield` 已經是百分比，直接存（design 寫 ×100，但新版 yfinance 已經改了）；機構持股是小數 → ×100；`Infinity` → NULL；BRK.B ↔ BRK-B | 用實測確認，不靠記憶 |
| 失敗處理 | 依序跑、單檔失敗不中斷、每檔寫一筆 `ingestion_runs`、**不做 retry**（upsert 是 idempotent，重跑即可） | 本機一次性 batch，加 retry 屬於超出規模需要（envelope） |

**為什麼還用 yfinance，而不是 DEV-69 的 Finnhub**：rate limit 只發生在**雲端 IP 或 JIT**。text_to_sql 的查詢路徑只讀 DuckDB，永遠不碰外部 API；ingest 在 Mac 上跑一次就好。這是有期限的過渡決定，等要做 on-demand ingestion（DEV-228，blocked by DEV-69）時再換 Finnhub。schema 不用改。

---

## 3. 語意層：view + table macro（ADR-0023）

**為什麼放在 DB，不放在 prompt**：prompt 只是建議，LLM 不一定照做；DB 裡的定義是確定性的、能寫單元測試，而且每次結果都一樣。這也回答了 design master §13.3 刻意留著的問題（「LLM 能不能自己寫除法」）：**比率在 DB 層定義一次，LLM 只負責選。**

### `quarterly_metrics` / `annual_metrics`（view）

- 內容：原始財報欄位（不含 SEC 專屬欄位）加上 7 個衍生指標：`gross_margin_pct`、`operating_margin_pct`、`net_margin_pct`、`fcf_margin_pct`、`rd_to_revenue_pct`（都已 ×100）、`debt_to_equity`、`current_ratio`。
- 分母是 0 或 NULL → 結果為 NULL。**NULL 代表「沒有揭露」，不是 0**（例如銀行沒有毛利）。
- view 存的是**公式**，不是結果。每次查詢都當場計算，原始資料一更新就跟著變。

### Calendar quarter（只在 quarterly view）

規則：**以 fiscal quarter 的中間月份**，決定它對應到哪個日曆季度。

| 公司 | Fiscal | 涵蓋月份 | → Calendar |
|---|---|---|---|
| AAPL（FYE 9 月） | FY2026 Q3 | 4–6 月 | 2026 Q2 |
| NVDA（FYE 1 月） | FY2027 Q1 | 2–4 月 | 2026 Q1（差 1 個月，要揭露） |
| MSFT（FYE 6 月） | FY2027 Q1 | 7–9 月 | 2026 Q3 |

**實作細節（面試好故事）**：本來是用 `period_end` 計算，結果觸發 **DuckDB 1.5.2 的 INTERNAL binder bug**：view 裡只要有「由 `period_end` 算出來的欄位」，再搭配 `ORDER BY period_end` 的 window function 就會出錯。最小重現（5 個變體）確認是 DuckDB 的問題後，我改成**用 `fiscal_year`、`fiscal_quarter` 加上公司的 FYE 月份來推算**，邏輯上反而更一致，因為它直接沿用 ingest 時已經正規化好的標籤。我也補了回歸測試。

### `period_metrics(cal_year, q_from, q_to)`（table macro = 帶參數的 view）

普通 view 沒有參數，做不了「使用者發問時才決定的區間」，所以改用 table macro：

| 類型 | 規則 | 例子 |
|---|---|---|
| 流量 | 加總；任一季缺值 → NULL | 營收、淨利、現金流 |
| 存量 | 取區間**最後一季** | 總資產、負債 |
| 比率 | 用**加總後的分子 ÷ 加總後的分母**重算，**絕不取平均** | 兩季毛利率 10%、30%，取平均是 20%；正確答案是 25% |
| **不完整區間** | `quarters_covered < quarters_expected` → **所有金額和比率一律 NULL**，只保留 coverage 欄位 | 見下面的故事 |

**為什麼不完整區間要強制 NULL（實測發現）**：第一次 live 測試問「2026 前三季 vs 2025 前三季，誰營收成長最多」，yfinance 只有大約 5 季資料，META 的 2025 區間只有 1 季，結果算出**假的 +254% 成長**還排第一名。光在 prompt 加排序規則救不了，因為所有公司的 2025 區間都不完整。所以改在 macro 裡強制處理，讓不完整的區間**連算都算不出來**。這正是「規則放在 DB 層」的價值。

### LLM 看得到什麼

`companies`、`market_valuations`、`quarterly_metrics`、`annual_metrics`、`period_metrics`。**藏起來的**：原始財報表（已被 view 包含）、SEC 的三張表（目前是空的，給 LLM 看只會讓它自信地回答「沒有資料」）、`ingestion_runs`。

---

## 4. `text_to_sql` tool（ADR-0022）

檔案：`backend/agent_engine/tools/text_to_sql.py` + `text_to_sql_prompt.md`。

### 為什麼是「tool 內的固定 loop」，而不是讓 orchestrator 自己寫 SQL，也不是 ReAct sub-agent

ADR-0018 的標準是：拆出去的門檻是 **context isolation**，不是「能力領域不同」。

- RAG 沒過門檻（一次檢索，chunk 本來就要給主 agent 讀）。
- text-to-SQL 過了：它有「寫 → 錯 → 改」的子流程，而 3k tokens 的 schema 主 agent 根本不需要看。
- 回傳的是**證據**（rows + SQL），不是 prose，所以 ADR-0018 拒絕「tool 內生成答案」的理由不適用。
- 附加價值：「問題 → SQL → 結果」變成**可以單獨評估的單元**，方便之後做 execution accuracy eval。
- 選 workflow 而不是 agent：步驟固定，好測試、好解釋、好 trace。等 eval 證明不夠用再升級。

### Loop

```
for attempt in 1..3:
    SQL = LLM(SQL prompt + schema + 前幾次失敗的 SQL 和錯誤)
    if 回 "UNANSWERABLE: 原因" → status=failed，停止（例：員工人數不在 schema 裡）
    檢查 + 執行
      出錯（parse / 非 SELECT / 欄位不存在 …）→ 記入 attempts，繼續
      成功：有資料 → ok；0 筆 → no_rows + coverage（不重試！）
3 次都失敗 → failed + coverage
```

**0 筆為什麼不重試**：0 筆通常是正確答案（資料真的不存在）。讓 LLM 重試，它會把條件越放越寬，最後「找到」不相干的資料。

### Schema prompt：從 DB 的 `COMMENT` 產生

延續你 design 的「**COMMENT 就是 LLM 看得到的 schema**」：tool 啟動時讀 `duckdb_columns()` / `duckdb_views()` / `duckdb_functions()`，產生 `CREATE TABLE ... -- comment` 格式的文字。view 的欄位如果沒有 comment，就沿用原始表同名欄位的 comment。**schema 只有一個來源**，改 DDL 的 comment，LLM 看到的就跟著變。

### 唯讀防護三層（LLM 寫的 SQL 是不可信的輸入）

| 層 | 做法 | 擋什麼 |
|---|---|---|
| 1 語意層 | DuckDB 自己的 parser（`extract_statements`）：剛好 1 個 statement 且類型是 SELECT | INSERT / DROP / COPY / ATTACH / SET、`SELECT 1; DROP …` |
| 2 引擎層 | `read_only=True` 的連線 | 就算第 1 層有漏洞，也無法寫入 |
| 3 引擎層 | `enable_external_access=false` | `SELECT * FROM read_csv('/etc/passwd')`：這是合法的 SELECT，只有這層擋得住。**而且 SQL 沒辦法重新打開**（實測：`Cannot enable external access while database is running`） |

另外：每次查詢開新連線（ingest 寫入時不會被鎖住）、最多 50 列（`truncated` 標記）。**刻意不做**：限制只能查可見的表（讀到也沒有風險）、query timeout（23 檔 × 5 季，跑多久都是毫秒級）。

### 回傳契約

```
{status: ok | no_rows | failed, question, sql, columns, rows(≤50), truncated,
 attempts: [{sql, error}],   # 失敗的嘗試，demo 時可以展示 self-correction
 coverage?: {tickers, quarterly_period_end_range, annual_fiscal_year_range, valuations_as_of}}
```

只有**基礎設施錯誤**（DB 檔不存在、LLM API 失敗）會 raise，走既有的 `_HandleToolErrors`。所以 UI 出現紅色錯誤卡片，就代表「系統壞了」，而不是「查不到資料」。

### Trace（Langfuse 已驗證）

每次 attempt 都是一個具名的 LangChain runnable，callback 也會往下傳：

```
tools → text_to_sql → text_to_sql_attempt_1 → ChatOpenAI (GENERATION)
```

用同一套機制，Braintrust 在 eval 實驗時也會收到同一棵 trace 樹（`BraintrustCallbackHandler` 是 global handler）。這部分要在 DEV-227 實際驗證。

**一個踩到的坑（面試好故事）**：callback 往下傳之後，LangGraph 的 `messages` 串流模式會把 **tool 內部 LLM 的 token 也串流到答案裡**，UI 上整段答案前面多了一大段 SQL，而且 code fence 沒有關好，整個答案都被渲染成程式碼。API 的 invoke 模式不串流，所以一開始沒發現，是在 UI 驗證時才抓到。修法是給 inner model 加上 LangGraph 的 `nostream` tag：**trace 照樣有，但不會被串流出去**。也補了測試鎖住這個行為。

### 另一個坑：orchestrator 改寫問題時「越權」指定了作法

有一輪 smoke 的 Q4（2026 前三季營收最高）答錯，變成了 WMT。追查後發現，orchestrator 傳給 tool 的問題寫了「用 period_end 落在 1/1–9/30 的 fiscal 季度」。inner LLM 就照這個作法，用日期篩選再自己加總，完全繞過了 `period_metrics` 的 calendar 對應和完整性檢查。修法分兩層：

1. **quant prompt**：orchestrator 只說「要什麼」（公司、指標、使用者講的期間），不說「怎麼算」。
2. **SQL prompt**：問題裡的作法指示如果跟 TIME SEMANTICS 衝突，一律以 TIME SEMANTICS 為準。

修完後，tool 層連續 3 次、orchestrator 層連續 3 次都正確。**教訓**：兩個 LLM 之間的介面也是契約，要寫清楚誰負責什麼。這也是 eval 應該涵蓋的 failure mode（「上層 prompt 污染下層」）。

### Inner model

跟 quant orchestrator 用同一個 model（`gpt-5.6-luna`），reasoning effort 設 `low` 以降低延遲。現在是寫在模組裡的常數；搬進 profile config 是 DEV-226。

---

## 5. 接進 Orchestrator：quant profile

- `quant/orchestrator_config.yaml`：tools = reader 的全部工具加上 `text_to_sql`；移除不存在的 `duckdb_query`（DEV-99）；預算 10 次。
- `quant/system_prompt.md`：以 reader 的 prompt 為基礎，新增三段：
  - **TOOL ROUTING**：名單內的財報、估值、比率、跨公司比較 → text_to_sql；10-K 文字 → RAG；即時股價、名單外公司 → Finnhub；需要兩種資料時就組合。
  - **STRUCTURED DATA**：怎麼讀 `status`、「上一季」的語意、日曆期間預設、不完整區間怎麼說明、NULL 不是 0、估值要寫 as_of、不要在答案裡貼 SQL。
  - **DATA SOURCES TABLE**：數字用 [N] 引用；底部的「資料來源」是 markdown 表格，不用 `[N]:` 語法。原因是前端的 Sources 區塊只接受 http(s) 網址，而且會刪掉所有 `[N]` 開頭的行（`markdown-sources.ts`）。這是過渡方案，之後由 citation-blocks session 的可展開 block 取代。
- `backend/api/main.py`：`WORKFLOW_PROFILE` 環境變數，預設 `baseline`，所以**正式站行為不變**。

---

## 6. 失敗處理一覽

| 狀況 | 系統行為 | 使用者看到 |
|---|---|---|
| SQL 欄位寫錯 | DuckDB 錯誤訊息（含 `Candidate bindings`）餵回，下一次 attempt 修正 | 正常答案；ToolCard 的 `attempts` 看得到修正過程 |
| LLM 寫出 DROP / 兩個 statement | 第 1 層擋下，當作錯誤重試 | 正常答案 |
| 0 筆（不在名單內、期間太早） | `no_rows` + coverage，不重試 | 「資料庫沒有這段資料，涵蓋範圍是 …」。實測中 agent 還會自己改用 RAG 讀舊的 10-K，並說明資料來源 |
| 問 schema 沒有的東西（員工數） | `UNANSWERABLE` → `failed` | 「無法用基本面資料庫回答」 |
| 不完整的日曆區間 | macro 回傳 NULL 金額 + coverage | 「X 公司只有 2/3 季，不能比較」 |
| 公司沒揭露（銀行毛利） | NULL，排名放最後 | 「JPM 不揭露毛利，未列入排名」 |
| DB 檔不存在、LLM API 掛掉 | raise → tool error middleware | 錯誤卡片 |

---

## 7. Smoke 結果（本機，2026-10-27）

完整的問題、tool 呼叫、SQL、答案在 `artifacts/current/text_to_sql_smoke_results.md`。

最終一輪（修完所有問題後，每題跑 1 次，不是 eval）：

| # | 問題 | 實際路由 | 結果重點 | 秒 |
|---|---|---|---|---|
| Q1 | 上一季哪家公司毛利率最高？ | text_to_sql（23 列，0 次重試） | META 79.31%（FY2026 Q3，2026-09-30），有說明各家期間不同；JPM、BRK.B 排除 | 10.9 |
| Q2 | Compare NVDA and INTC revenue over the last 4 quarters. | text_to_sql（8 列） | 逐季列表，有註明 NVDA 的季度晚 1 個月 | 17.6 |
| Q3 | KO 和 PEP 誰的 forward P/E 比較低？ | text_to_sql（**不是** Finnhub） | PEP 15.68 < KO 26.30，as of 2026-10-27 | 9.6 |
| Q4 | 2026 前三季營收最高的是哪家？ | text_to_sql → `period_metrics` | COST $235.8B，**實際涵蓋 2025/12–2026/08**；其他不完整的公司不列入比較 | 13.2 |
| Q5 | Apple 10-K 怎麼描述供應鏈風險？ | sec_filing_search | RAG 沒有退化，FY2025 10-K，有 [N] 引用 | 12.2 |
| Q6 | Apple 怎麼描述 AI 投資？研發佔營收比？ | sec_filing_search → text_to_sql | **組合**：10-K 沒有單獨揭露 AI 金額；R&D 8.30%（FY2025）、10.72%（FY2026 Q3） | 17.7 |
| Q7 | Apple 2019 年營收多少？ | text_to_sql（no_rows）→ sec_filing_search | 說明資料庫只涵蓋 FY2022 之後 → **改讀 FY2019 10-K** 回答 $260.17B | 26.9 |
| Q8 | 台積電上一季營收多少？（名單外） | Tavily ×3 + Finnhub | ⚠️ 抓到 1 月的新聞（2025 Q4），不是最新一季 → 已知限制 | 32.7 |

**修正過程中抓到、也已修好的問題**（都有對應的 commit；前 4 個有回歸測試）：DuckDB binder bug、yfinance 半成品季度、不完整區間算出的假 +254% 成長、SQL token 串流進答案、`WHERE metric IS NOT NULL` 放錯位置、orchestrator 越權指定作法。

**建議 demo 順序**：Q1 → Q6（組合工具，主軸）→ Q4（時間語意）→ Q7（誠實面對缺資料）。每題約 10–27 秒。

---

## 8. 跟 design（design_master.md）比較：簡化了什麼

| Design 的內容 | Prototype 的做法 | 原因 |
|---|---|---|
| 8 張表 | 只填 4 張 yfinance 表；SEC 三張和 SEC 專屬欄位留空，而且不讓 LLM 看到 | SEC XBRL subsystem 是 DEV-225；normalization（§13.2）還沒決定 |
| 每個子系統都要用 `with_retry`（§8） | 不做 retry | 本機一次性 batch，失敗重跑即可 |
| 子系統的 `traced_span` 和 `yf_*` span 命名（§7.8） | ingest 不開 trace；text_to_sql 用 LangChain run tree | ingest 是 CLI，§7.8 本來就說 CLI 不開 trace；query 端用 LangChain run 才能 Langfuse / Braintrust 共用 |
| 衍生指標延後決定（§13.3） | **已決定**：放在 DB 層（view + macro），ADR-0023 | text-to-SQL 設計需要這個答案 |
| `dividendYield` ×100（§3.2） | 不乘 | 新版 yfinance 已經是百分比（實測） |
| Hybrid batch + JIT | 只有 batch | JIT 要在雲端跑，必須先完成 Finnhub 遷移（DEV-228 / DEV-69） |
| Universe 10 檔 | 23 檔（原本的 10 檔 + demo 需要的公司） | 跟 RAG 的 10-K 涵蓋範圍對齊，才能在同一家公司上組合兩種工具 |

---

## 9. 已知限制（誠實清單）

1. **沒有 eval**：目前只有 8 題 smoke，不能宣稱準確率。
2. **資料很淺**：每家約 5 季、4 個會計年度；多數 YoY 和跨年區間答不出來（這時會誠實回答「不完整」）。
3. **名單外的公司會走 Tavily 新聞**：台積電那題抓到的是 **4 月的舊新聞（Q1）**，不是最新一季。新聞來源的數字沒有驗證機制。
4. **ToolCard 的 output 是跳脫過的 JSON 字串**，SQL 不好讀。demo 時可以講 SQL，或打開 Langfuse trace 展示。這屬於前端通用元件，不在這次範圍。
5. **快照有日期**：估值是 ingest 當天的快照；財報要重跑 ingest 才會更新。
6. **SQL 的時間語意靠 prompt**：例如「上一季要先取最新一季，再看指標」是寫在 prompt 裡的，LLM 偶爾會用不同但等價的寫法。這正是 eval 要量的東西。
7. **Language Policy 偶爾出錯**：tool argument 有時混入中文（例如「上一季」）；繁體中文的問題也出現過**用簡體中文回答**一次（既有的 language policy 問題，不是 text_to_sql 造成的）。
7b. **非決定性**：同一題在不同次執行中，SQL 寫法可能不同（Q4 曾經出現過一次錯誤寫法，修完 prompt 後連續 6 次都正確）。沒有 eval，就沒辦法量化穩定度。
8. **DuckDB 1.5.2 binder bug** 是用設計避開的，沒有升級版本；之後如果有人在 view 裡用 `period_end` 計算欄位，會再踩到（回歸測試會擋下）。
9. 已知的 DuckDB 單一 writer 限制：ingest 期間如果剛好有查詢，查詢會失敗（錯誤訊息會說明）。

---

## 10. 下一步：怎麼加上 execution-accuracy eval（DEV-227）

1. **Dataset**：從 `artifacts/current/text_to_sql_eval_seed.yaml` 的 7 題開始。每題都有人工檢查過的 gold SQL、key facts，以及**要抓的 failure mode**（例：fiscal 標籤跨公司對齊、margin 取平均、`WHERE metric IS NOT NULL` 放錯位置）。依 failure taxonomy 擴充到 30–50 題：時間語意、NULL、不完整區間、名單外、schema 外。
2. **Grader（不用 LLM judge）**：分別執行 gold SQL 和生成的 SQL，**比較結果集**，不比 SQL 字串。比較時忽略欄位順序、浮點數設容差、多出來的欄位允許。因為 text_to_sql 是可以單獨評估的單元，可以不經 orchestrator，直接呼叫 `answer_question()`，又快又便宜。
3. **第二個指標：tool routing accuracy**：在 quant profile 下，數字題選中 text_to_sql、10-K 題選中 RAG 的比率。這要經過 orchestrator 跑。
4. **答案層**（之後才做）：引用完整性，也就是每個 [N] 都有對應的資料來源列、數值跟 rows 一致。可以用 deterministic scorer 檢查。
5. **固定資料快照**：eval 要對一份**凍結**的 DuckDB 跑，不然重新 ingest 後 gold 答案就變了。
6. **第一個驗收項**：Braintrust 實驗裡看得到完整的巢狀 trace。

---

## 11. 面試可能被問的問題（答案要點）

- **為什麼不讓 LLM 直接查原始表？** 公式和時間對齊是確定性的領域知識，放 DB 才能測試；LLM 只做語意對應（ADR-0023）。用 +254% 的故事舉例。
- **為什麼 text-to-SQL 拆成 tool 內的 loop，RAG 卻不拆？** ADR-0018 的 context isolation 門檻：有沒有要隔離的子流程（ADR-0022）。
- **怎麼防 SQL injection 和資料外洩？** 三層防護，其中兩層在引擎層。舉 `read_csv('/etc/passwd')` 的例子：它是合法的 SELECT，parser 擋不住，只有引擎層的設定擋得住。
- **表變多了怎麼辦？** schema 會塞不下 → 先做 table selection，或用 schema 檢索挑相關的表，再生成 SQL。那時候 loop 也可能需要升級成 agent。現在 3k tokens，還不需要。
- **怎麼知道它是對的？** 現在不知道，只有 smoke。下一步是 execution accuracy（比較結果集）加上 routing accuracy，種子資料已經準備好了。
- **最難的部分？** 不是 SQL 語法，是**時間語意**：fiscal vs calendar、latest reported quarter、不完整區間、52/53 週會計年度。

---

## 附：這次新增和修改的檔案

- Ingest：`fundamentals_pipeline/yfinance_fetcher.py`、`scripts/ingest_yfinance_fundamentals.py`、`calendar_to_fiscal_period.py`（snap）、`config/ticker_universe.yaml`（23 檔）
- 語意層：`fundamentals_pipeline/duck_db/schema.sql`（檔案最後的 Semantic layer 段落）
- Tool：`agent_engine/tools/text_to_sql.py`、`text_to_sql_prompt.md`、`tools/__init__.py`（註冊）
- Profile：`profiles/quant/orchestrator_config.yaml`、`profiles/quant/system_prompt.md`、`api/main.py`（`WORKFLOW_PROFILE`）
- 測試：`tests/tools/test_text_to_sql.py`（22）、`tests/ingestion/fundamentals_pipeline/test_semantic_layer.py`、`test_yfinance_fetcher.py`、`test_calendar_to_fiscal_period.py`（新增案例）、profile 和 env 的測試。全部 backend 測試 1436 passed。
- 文件：ADR-0022、ADR-0023、`CONTEXT.md`（Ticker universe、Derived metric、Fiscal / Calendar / Latest reported quarter）、各模組 README、`docs/file_structure.md`
