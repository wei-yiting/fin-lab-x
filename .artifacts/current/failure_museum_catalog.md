# FinLabX 失敗博物館 — 素材目錄（Failure Museum Catalog）

> **這份文件是什麼**：為 FinLabX「失敗博物館」頁面收集的完整素材目錄。調查範圍涵蓋全部 15 個 PR（含每個 PR branch 上的中間 fix commits）、`fin-lab-x-wt/` 下 12 個 worktree、main repo 的 2026-07-06 全 repo 稽核報告（`.artifacts/current/repo_audit_report.md`）、eval 系統與診斷文件。
>
> 每個展品的欄位：**情境**（failure scenario）、**實例**（具體 example）、**Root cause**、**解法**（address 策略）、**狀態**、**量化**（目前有無 evaluation 覆蓋）、**證據**（commit / PR / 檔案路徑）。
>
> 標記說明：✅ 已修復｜🔧 修復中（in branch / uncommitted）｜⛔ 仍未修（open）｜❓ 待與你討論，我不臆測。

---

## 0. 你記憶中三個主題的驗證結果

| 記憶主題 | 驗證結果 | 對應展品 |
|---|---|---|
| Source citations format 不對 → 前端 render 失敗 | **證實** ✅ 已修（雙端夾擊），但修復本身留下 3 個殘留 bug 仍 open | A1 |
| News fetch 抓到 generic ticker page 而非具體文章 | **證實** ⛔ 未修。diagnostic run 的 CSV 有第一手證據：UNH 題引用 CNBC quotes 頁、TSLA 題引用 Reuters 公司頁 | C1 |
| 10-K 的 source 到現在還會錯 | **部分證實**，confidence: medium ❓ 找到 5 個有實碼佐證的候選機制，但沒有任何文件記錄「錯的樣態」——需要你補充 symptom | B7 |

---

## 展區 A — Citation 與 Source 呈現管線

### A1. Citation 格式漂移 → Sources 區塊 render 失敗　✅（殘留 3 bug ⛔）

- **情境**：LLM 輸出的 reference definitions 不符 CommonMark spec，前端 `markdown-sources` extractor 抓不到 → Sources UI 區塊空白、原始引用文字直接顯示在正文裡。
- **實例**：實際觀察到至少 5 種 malformed 格式（前端程式碼註解逐條標明 "one observed failure mode seen in real responses"）：
  1. bullet 前綴 `- [1]: URL`（CommonMark 要求 reference definition 在 column 0）
  2. 「來源：」/「References」標題行黏住第一條 definition，使它變成普通段落
  3. definition 前缺空行，被併進前一個段落
  4. 無冒號的 `[N] URL` 格式
  5. 全形括號 `【N】` inline citation（中文回應特別常見）
- **Root cause**：前端 parser 針對理想化格式打造；system prompt 沒有把 LLM 鎖死在單一格式，輸出自然漂移。
- **解法**：雙端夾擊（pincer）——(1) 前端 `normalizeRefDefs()` 三條 regex 修復管線 + `FALLBACK_RE` 容錯 + strip 雜訊；(2) system prompt LINK FORMAT 規則收緊（強制 `[N]: <url> "<title>"`、禁全形括號、禁 References heading、禁過場語），再用 MSW fixture + E2E test（`citation-sources.spec.ts`）鎖住。
- **狀態**：✅ 已修（PR #12）。但 audit 標出修復自身引入的殘留 bug 仍 ⛔：
  - #61：display-strip regex 的冒號是 optional，`[2024] Revenue grew 12%...` 這種正文行會被靜默刪除
  - #69：`#src-N` jump-link anchor 因 href 被覆寫成外部 URL，永遠不可達
  - #60：cursor sentinel `⌧CURSOR⌧` 在 code block / table 內會字面上屏
- **量化**：無 citation-format compliance scorer（缺口）。目前只有 E2E test 鎖住 happy path。
- **證據**：`frontend/src/lib/markdown-sources.ts:11-127`、`AssistantMessage.tsx:52-58`、commits `aec4152`、`5b558f2`、`239c0706f9`（RefSup 改 target=_blank + title）；audit #60/#61/#69。

### A2. 正文 inline [N] 與底部 reference list 脫鉤　✅（僅 prompt 防禦）

- **情境**：LLM 只在文末列 URL、正文沒有對應的 inline `[N]`，讀者無法對應 claim ↔ source。
- **解法**：prompt 強制規則："A response that lists [1]: url without an inline [1] in the body is INVALID — do not emit it"。
- **量化**：無 scorer 驗證此規則（缺口）。
- **證據**：`system_prompt.md:25`、commit `5b558f2`。

### A3. API 資料沒有可引用 URL → 曾強制引用 generic ticker page　✅（policy 演化）

- **情境**：純 yfinance 回答（報價、基本面）沒有任何外部 URL 可引用，與「所有 claim 都要有 source」的 zero-hallucination 政策直接衝突。
- **演化過程**（本身就是一個展品級的故事）：
  1. 早期 prompt 規定「yfinance-only 時省略 references」→ Sources 區塊缺位
  2. 反轉：**強制**每個 yfinance claim 附 `https://finance.yahoo.com/quote/TICKER` —— 用 generic ticker overview page 冒充 source（與 C1 的 failure 同型，只是這次是自己設計出來的）
  3. PR #15（Finnhub 抽換）：放棄 URL 硬性要求 —— "Finnhub free tier has no public per-ticker page — do NOT fabricate a per-ticker URL"，API 資料改為 cite by provider name（"According to Finnhub…"），URL 只要求「真的有 URL 的來源」（Tavily news、SEC filings），並加 DECISION-001 regression 斷言 prompt 不再殘留 yahoo/yfinance 字樣。
- **解法策略**：讓 citation policy 貼合資料來源的現實，而不是強迫捏造 URL。
- **證據**：commits `5b558f2`、`7af4cdd`（feat/finnhub-agent-tools branch）；PR #15 body。

---

## 展區 B — SEC 10-K 工具與 source 正確性

### B1. edgartools section 內容溢出 item 邊界　✅

- **情境**：`get_section("11")` 回傳的內容實際包含 Items 12–14 —— 來源標註（「根據 Item 11」）對不上實際內容；char_count 與 stub 判定也因此失真。
- **實例**：human UAT（PR #14 review）抓到：AAPL FY2025 的 Item 11 有 2080 chars 且未被標為 stub，但 Items 10/12/13 都是 stub —— 因為 Item 11 的 body 挾帶了 12/13/14 的 "incorporated by reference" 文字；Item 9C 同病；key "14" 甚至從 TOC 整個消失。
- **Root cause**：upstream edgartools 的 `TenK.document.sections` 切分 bug。
- **解法**：`trim_text_to_item_boundary()`（`backend/common/sec_core.py`）在 list 與 get 兩側都用 regex 切到下一個 item 邊界 + 真實 EDGAR integration assertions（Item 11 必須是 stub；`get_section('11')` 不得包含 "Item 12."）。
- **量化**：sec_integration tests 覆蓋此 case；無 corpus-wide bleed 偵測。
- **證據**：PR #14 UAT review comment（完整 tool JSON）、commit `7d7f3e43ae`、`sec_core.py:110-132`。
- **備註**：這是 700+ 自動化測試沒抓到、**human UAT 才抓到**的兩個 bug 之一（另一個是 B6）。

### B2. 空殼 section（incorporated by reference）被當實質內容　✅

- **情境**：Part III Items 10–14 常只有一句「incorporated by reference to the Proxy Statement」；agent 取用後可能以 10-K 為 source 回答實際上在 DEF 14A 的資訊，或浪費 tool-call budget 抓空殼。
- **解法**：`is_stub_section()`（經驗校準的 100-char threshold）+ `is_stub`/`stub_reason` metadata + reading guide 向 LLM 解釋 stub 語意；ingestion 側同步清除（PR #9 "Part III stubs dilute retrieval relevance"）。
- **證據**：`sec_core.py:135-188`、`sec_filing_tools.py:246-250`（Item 1c pre-2023 專屬錯誤）、PR #9 commit `bfa8f75`。

### B3. Fiscal year 語意陷阱　✅（ingestion）/ 部分殘留

- **情境**：fiscal year 若從 `filing_date` 推導，一月申報的 10-K 會被歸到錯誤年度；非曆年制公司（NVDA FY2026 於 2026-01 結束）容易與使用者心中的「2025 年報」錯位。
- **實例**：eval dataset 自己就踩過 —— NVDA fiscal year off-by-one（commit `2c29bf3474` 修正）；`scenarios/sec_retrieval/README.md:23` 特別警告此語意。
- **解法**：fiscal_year 一律從 `period_of_report` 推導（PR #6 commits `3391039ee9`、`4683cb7b7c`）。
- **殘留**：使用者語意（「2025 年報」到底指 FY 還是曆年）仍靠 LLM 自行判斷，無 guardrail。

### B4. Latest fiscal year 永久 lru_cache　⛔

- **情境**：`fiscal_year=None`（拿最新一期）的解析結果被 `@lru_cache` 永久快取 → 公司發布新 10-K 後，長駐 process 在重啟前一直回舊年度 —— 年度標註靜默過期。
- **證據**：audit C2、`sec_core.py:293`。
- **狀態**：⛔ audit 排程中，未修。

### B5. DNS 失敗被轉譯成「這家公司不存在」　⛔

- **情境**：`_classify_edgar_error` 的 catch-all 把 DNS 失敗 / timeout / parsing bug 一律轉成 `TickerNotFoundError` → LLM 自信地告訴使用者「查無此公司」—— tool 層直接違反 zero-hallucination 政策。
- **證據**：audit B3、`sec_core.py`。
- **狀態**：⛔ 未修。

### B6. LangGraph 平行 tool 規劃 → 同一 filing 打 EDGAR 兩次　✅

- **情境**：human UAT 的 cache-reuse 步驟失敗：一個問題觸發兩次 `list_sections` + 兩次 `get_section`。兩個並發呼叫同時 miss `functools.lru_cache`（都還沒 populate），EDGAR 被打兩次。
- **Root cause**：`lru_cache` 沒有 in-flight de-duplication；LangGraph 會自由規劃重複的平行 tool calls。
- **解法**：defense in depth —— system prompt 規則抑制規劃端 + single-flight registry（輸家 block 在贏家的 Future 上）作為安全網。
- **證據**：PR #14 review、commit `ccb8ae85e2`。

### B7. 10-K source 至今仍會錯（你的記憶主題）　⛔ ❓

- **情境**：（你回報）回應引用的 10-K 來源到現在還是會錯。repo 內**沒有任何文件記錄具體錯的樣態**，以下是有實碼佐證的候選機制（事實陳述，非結論）：
  1. **SEC tools 的 output 完全不含 URL**（`sec_filing_get_section` 只回 ticker / fiscal_year / period_of_report / content），但 prompt LINK FORMAT 又要求「SEC filings 這類真的有 URL 的來源」要列 URL → LLM 引用 SEC 內容時，**任何它寫出來的 URL 都不是 grounded 的**，只能自己編（fabricated sec.gov link 的幻覺風險）。
  2. **B4 的 stale cache** → 年度標錯。
  3. **B3 的 fiscal year 語意錯位** → 使用者以為的年度 vs 實際 FY。
  4. **B5 的錯誤誤分類** → 「公司不存在」的錯誤陳述。
  5. **section resolution 靜默跳過**：`_iter_resolved_sections` 對解析不出 item key 的 section silently skip、重複 key 用 `setdefault` 取第一個。
- **量化**：`sec_retrieval` eval dataset 仍是 status: draft 的 10 列手寫 placeholder，且 scorer 有 P0 bug（H7）——**10-K 引用品質目前沒有任何可信的量測**。
- **❓ 待你補充**：(a) 你看到的「錯的 source」是 URL 錯、年度錯、還是 item/section 錯？有沒有印象中的實例或 Langfuse trace？(b) 是否應該讓 SEC tool 直接回傳 filing 的 accession-number URL，讓引用 grounded？

---

## 展區 C — News 工具

### C1. 新聞搜尋引用 generic ticker page 而非具體文章（你的記憶主題）　⛔

- **情境**：問「最近的利空新聞」，Tavily 回傳的 top result 是新聞網站的 ticker 報價/總覽頁，不是事件文章 —— citation 指向的頁面不支撐任何具體 claim。
- **實例**（第一手證據，diagnostic run CSV 的 `output.tool_outputs` 原文）：
  - UNH 題引用 `[1]: https://www.cnbc.com/quotes/UNH "UNH: UnitedHealth Group Inc - Stock Price, Quote and News - CNBC"`
  - TSLA 題引用 `[1]: https://www.reuters.com/markets/companies/TSLA.F/`
  - 同一批 run 還觀察到 tool routing 偏移：agent 先呼叫 `yfinance_stock_quote` 用估值數據「回答」新聞題。
- **Root cause**：未有正式 root-cause 分析（INFERRED：query 組法是 `f"{ticker} {query}"`，ticker 前綴推高 ticker-page 的排序；`include_domains=[reuters.com, bloomberg.com, cnbc.com]` 限域內 aggregator 頁面本來就多）。
- **狀態**：⛔ **未修**。Finnhub 抽換明文「keep tavily」不動它。目前的對策是把它做成診斷軌的量測對象：near_v1_diagnostic dataset 30 題中 `source_coverage_gap` 是 primary failure mechanism ×4、secondary ×4，4 題的 `likely_tuning_lever = tavily_sources`。
- **量化**：診斷軌（execution_health + Langfuse 人工標註）已建好但**人工標註尚未執行** —— 還沒有 measured 分數。
- **❓ 待你確認**：(a) 你記憶中的 Reuters 案例就是這批 diagnostic run，還是更早的手動測試？(b) 修法候選（Tavily `topic="news"` 參數、published_date 過濾、URL pattern 排除 `/markets/companies/`、去掉 query 的 ticker 前綴）有沒有評估過？
- **證據**：`fin-lab-x-wt/v1-eval-experiment-pipeline/backend/evals/results/near_v1_diagnostic_20260424_*.csv`、`financial.py:132-136`、`EVAL-V1-DIAGNOSTIC-WALKTHROUGH.md`。

---

## 展區 D — Market Data 工具（yfinance → Finnhub 全史）

### D1. yfinance 常態性 rate limit → 整組工具汰換　🔧（PR #15 open）

- **情境**：yfinance 是非官方 Yahoo scraping、無 SLA，即時行情 tool calls 間歇性失敗（IP throttling）。
- **解法**：換 Finnhub 官方 free-tier REST API（60 calls/min），三個 tool 拆開讓「問一個價格 = 恰好一次 call」以貼合 rate budget；quant ingestion 子系統保留 yfinance（各自為 documented owner）。
- **策略**：用官方、有文件的 API 換掉非官方 scraper，且 tool 顆粒度圍繞 rate budget 設計。
- **證據**：PR #15 body、commits `283f3676af`、`7af4cdd387`。

### D2. 無效 ticker 的靜默失敗家族（三代同題）

同一個「external API 對 invalid input 不報錯」的 failure，在三個資料來源各發生一次：

| 世代 | API 行為 | 風險 | 解法 | 證據 |
|---|---|---|---|---|
| yfinance `.info`（PR #7） | 回 `{"currentPrice": null}` 不 raise | LLM 分不清「無效 ticker」vs「休市」→ 幻覺 | 雙欄位 guard → `ValueError` → sanitized SSE error（human reviewer 抓到，266 tests 沒抓到） | commit `0ed8965f1e` |
| yfinance 1.x 404（quant worktree） | HTTP 404 只 log，回近空 dict | 被誤分類成 retryable 的 `EmptyResponseError` → 誤觸 retry + 錯誤語意誤導 | 檢查 `symbol`/`quoteType` 皆缺 → `YFinanceTickerNotFoundError` + live drift canary test | quant-yfinance-ingestion uncommitted diff 🔧 |
| Finnhub（PR #15） | 回全零 quote `{c:0, h:0, ...}` 不 raise | agent 把 $0.00 當真實價格回報 | 全零/空 map 偵測 → `ValueError` + opt-in live tests 鎖住假設 | commit `b9fa6757a8` |

**策展價值**：換掉一個 API 不會消滅這類 failure —— 每個新 API 都有自己的「靜默垃圾」形狀，教訓是**每接一個資料來源就要先探明它的 invalid-input 行為並寫 live contract test**。

---

## 展區 E — Prompt / Policy Compliance

### E1. Language policy 違規：CJK 漏進 tool arguments　✅（本館鎮館之寶：催生了整個 eval framework）

- **情境**：使用者用中文問，agent 把「微軟最近新聞」原文丟給 Tavily search（而非 "MSFT recent news"）；回應語言也會與使用者語言不符。失敗只能靠人工發現。
- **量化（第一個有 baseline 的 failure）**：baseline eval **5/8 失敗** → prompt 修復後 **8/8 通過**（3-run stability 95.8%）。
- **Root cause**："Always think and search in English" 太模糊 —— 無明確規則、無範例、tool schema 欄位層級無 guardrail。
- **解法**：三層 —— (1) system prompt 明確規則 + before/after 範例；(2) tool schema 的 query 欄位描述加 `(MUST be in English)`；(3) 建立 8-case eval suite（CJK-ratio 程式化斷言）防 regression。**這是 repo 的第一個 eval，整個 eval framework 因這個 failure 而生。**
- **證據**：PR #3、commits `65ba25b5a9`、`8a29d9c`；`backend/evals/scorers/language_policy_scorer.py`。

### E2. 讀完英文 10-K 後回應語言漂移　✅（防禦碼存在；incident 為 INFERRED）

- **情境**：agent 讀入大量英文 SEC filing 內容後，in-context 英文壓過 system prompt 的 language policy，改用英文回覆。
- **解法**：language-directive sandwich —— tool output 用 `_LANGUAGE_DIRECTIVE_PRE/_POST` 前後包夾 section content，並利用 dict insertion order 確保 pre-directive 先於 content 出現（程式碼自述 "anchoring the language policy at the boundary where in-context English would otherwise dominate"）。
- **證據**：`sec_filing_tools.py:58-68, 275-289`、commit `0de9d04`（PR #14）。

### E3. 內部 tool-call budget 被說成「我被 rate limit 了」——同一誤判在兩層各發生一次　✅

- **情境**：
  - **Layer 1（LLM 層）**：`ToolCallLimitMiddleware` 的 block 訊息被 LLM 轉述成「我遇到 rate limit」，把內部預算限制與 SEC/Yahoo/Tavily 的真實 429 混為一談。
  - **Layer 2（前端層）**：backend 把訊息改寫成明文「this is NOT a rate limit from SEC EDGAR…」之後，前端的 friendly-error regex `/rate limit/i` **匹配到澄清句自己**，render 出「Too many requests. Please wait a moment.」—— 與本意完全相反。
- **Root cause**：tool 錯誤以 free-form 字串跨 FE/BE wire，沒有結構化的 `errorClass` 欄位，只能對 prose 做 regex 分類（commit 自承是 architectural gap 的 workaround）。
- **解法**：sentinel pattern 排在 `/rate limit/i` 之前 + backend 措辭改為 "NOT an *external* rate limit" 讓子字串消失；typed errorClass 列為獨立 refactor（❓ 尚未見落地）。
- **證據**：PR #14 commits `37addf7690`、`066a80f148`；`system_prompt.md:8-9`。

---

## 展區 F — Streaming / 前後端 Contract

### F1. AI SDK v6 wire format mismatch：backend 拒收所有真實前端請求　✅

- **情境**：前端（AI SDK v6 `DefaultChatTransport`）送 `{messages: [...], trigger}`，backend `StreamChatRequest` 期望 flat `{message: str}` → 合法 payload 全數被拒。**對所有 MSW-mocked 前端測試不可見**——mock fixtures 編碼了同一個錯誤假設；只有 BDD browser-use 對真實 backend 驗證時才爆出來。
- **解法**：兩步 —— 先在前端用 `prepareSendMessagesRequest` 墊 shim 解鎖，然後 backend 對齊 SDK wire format（PR #10）、刪掉 shim。策略：**在 source of truth（SDK 格式）修 contract，然後刪除臨時墊片**。
- **證據**：PR #10、commits `993c7c03af`、`91d4dd3009`、`1943857875`。

### F2. Contract 修復的第一版自己又有兩個洞　✅

- **情境**：PR #10 第一版用 `list[dict]` 收 nested messages —— malformed payload 噴 500 `AttributeError`（而非 422）；SDK 把 user message 拆成多個 text parts 時**只讀 `parts[0]`，其餘靜默截斷**。
- **解法**：typed nested Pydantic models（`MessagePart`/`ChatMessage`）讓驗證發生在欄位層級；join 全部 text parts。由 code review 抓到，非測試。
- **證據**：commit `bf234cb973`。

### F3. AI SDK v6 未文件化行為集（contract findings）　✅（文件化）

實測發現、寫進 `docs/ai_sdk_v6_contract_findings.md` 的地雷：

| 行為 | 後果 |
|---|---|
| SSE `error` chunk **不會**進 `message.parts[]` | 等 parts 出現 error 的整條 UI 分支是 dead code（原設計的 inline ErrorBlock 因此砍掉） |
| fixture 寫 `textDelta` 而非 `delta` 會被 SDK **靜默丟棄** | 「stream 看起來 valid 其實是空的」→ 造成 H11 的 false-positive 測試 |
| `HttpChatTransport` 丟出的 Error **不帶 HTTP status** | 500/409/422 全部分類成 unknown → 通用錯誤文案（解法：`statusAwareFetch` 搶先丟 `ChatHttpError`） |
| 部分 turn regenerate 有 race window | 客戶端在 LangGraph commit 前斷線 → 404（附可執行 probe script） |
| tool part 的名稱在 `part.type='tool-{name}'` 而非 `part.toolName` | tool 卡片標題全部顯示 "undefined"（解法：`resolveToolName()` fallback chain） |

### F4. Regenerate / Retry 狀態機連環 bug（同一主題 regress 兩次）　✅

- **情境**：(a) regenerate 一律 422 —— 為 submit path 寫的 `model_validator` 拒收帶 message history 的 regenerate payload；(b) pre-stream error 後 retry 把 user message 重複 append 一次；(c) round-1 code review 的「修復」把同一 bug 重新引入 mid-stream retry path；(d) `regenerate()` 在失敗後重試會 4xx-loop，因為 AI SDK 在發請求前就**不可逆地移除** assistant message。
- **解法**：驗證邏輯按 trigger path 分家；shape-aware smart retry（依最後一則訊息的形狀分派：user → slice + `sendMessage`；partial assistant → `regenerate({messageId})` + 4xx fallback）。regression 先用 dedicated integration test 證明再修。
- **證據**：commits `63630e9b36`、`a8b18b867f`、`96c4098b`、`daad71e5f6`。

### F5. Mid-stream 錯誤被 pre-stream classifier 吃掉　✅

- **情境**：context-length-exceeded、rate limit 等 mid-stream SSE 錯誤被 render 成通用 "Something went wrong"，`error-messages.ts` 裡已定義好的 friendly 訊息從未被顯示。
- **解法**：以「最後一則訊息是 partial assistant turn 且錯誤非 HTTP/network 層」判定 mid-stream，路由到 mid-stream-sse classifier。
- **證據**：commit `cacc8d7cb4`。

### F6. Backend 例外時 SSE 不送 error/finish frame → 前端永久掛住　⛔

- **情境**：`chat.py` 只 catch `ValueError`（且幾乎是 dead code）；`sse_serializer.py` 的 `json.dumps` 無 `default=str`，tool args 帶不可序列化值即 mid-stream `TypeError` —— 前端永遠停在未完成的訊息上。失敗路徑零測試。
- **狀態**：⛔ audit B1，未修。
- **證據**：`chat.py:117-119`、audit B1/#41。

### F7. Multi-provider streaming reasoning：BDD 抓出的 6 個生命週期 bug　🔧（branch 未 push）

- **情境**（worktree `multi-provider-streaming-reasoning`，36 commits）：
  1. reasoning chunks 在 tool call 之後的 gap 中丟失
  2. 使用者按 Stop 被播報成「正常完成」（`onFinish` 未分 isAbort）
  3. abort 時 Langfuse 缺 `reasoning_tail_aborted` 標記、reasoning metadata 落庫不可靠
  4. AI SDK v6 `onData` 只對 `data-*` chunks 觸發 → 多個 handler 分支是 dead code、`onFinish` 未接線
  5. STOPPED 指示器 render 位置跳動
  6. 依賴 Langfuse SDK **私有屬性 `CallbackHandler._runs`** → 用 contract tests 鎖型別防升級靜默破壞
- **狀態**：🔧 fixed on branch（BDD 第二輪 14 PASS / 0 FAIL），但 **branch 未 push、無 PR、本機唯一副本**；且 uncommitted 變更中混入意外的 `backend/Dockerfile` 刪除，照樣 commit 會弄壞 CI。
- **證據**：commits `48798a3`、`4da26d1`、`3d422d2`、`e8cedea`、`c89c33b`、`3439c78`、`508eb37`；WORKTREES-BRIEF。

### F8. Tool 錯誤原文直達 LLM/使用者　✅（有殘留不一致 ⛔）

- **情境**：tool exception 的路徑、API key、stack trace 原文流向 LLM 與使用者。
- **解法**：`tool_error_sanitizer.py`（strip keys/connection strings/paths/tracebacks）+ `_HandleToolErrors` middleware。
- **殘留**：audit B4 —— 舊 dead stack `tools/sec_filing.py:61-62` 吞例外回傳未 sanitize 的 error dict，繞過整個機制；audit #44 —— sanitizer 的 `_UNIX_PATH` regex 反而把合法 sec.gov URL path 打成 `[path]`，降級使用者該看到的錯誤。

---

## 展區 G — RAG Ingestion 與 Retrieval

### G1. 跨公司污染：問 AMD 拿到 Intel + NVIDIA　✅（機制層）——量化最完整的展品

- **情境**：naive dense retrieval 下，中文 query 問 AMD 供應鏈風險，top-10 chunks = **7×INTC + 3×NVDA + 0×AMD**。實驗報告原文：「系統完美地誤導下游 LLM 用 Intel 和 NVIDIA 的供應鏈描述回答 AMD 的問題」。
- **量化**：18 題 A/B 實驗 —— naive collection mean **p@10 = 0.622**（std 0.312，range 0.00–1.00；AMD 三題平均 0.13）；three-layer + filter 後 **p@10 = 1.00**（報告自注：filter 之下這是 tautology，非賣點——重點是 baseline 有多不可靠）。
- **Root cause**：語意相似度在「同產業競爭對手」之間最強（正是最不能搞混的公司）；小語料 ticker（AMD 僅 83 chunks / 4.5%）被語意鄰居淹沒；中文 query → 英文 chunks 的跨語言條件放大 entity mismatch。
- **解法**：three-layer contract —— payload metadata + Qdrant KeywordIndex + tenant-aware HNSW（`is_tenant=True`）+ query 時 `must=[ticker=X]` filter。已進 main 的 v2 pipeline（PR #11）。
- **殘留 caveat**：實驗假設 oracle ticker（router 從 query 抽 ticker 的準確率被隔離，是獨立議題）；且 audit #18 —— `retriever.py:281` 在呼叫者傳 `"year": None` 時 year filter 被丟掉 → **跨年份污染這條同型 failure 在 main 上仍 ⛔**。
- **證據**：`fin-lab-x-wt/rag-filter-eval/artifacts/experiment_results.md`、`retrieval_diff_20260513_082123.md`、6 份 result CSVs。

### G2. SEC HTML heading 偵測長征（28 家 ticker 的 markup 地獄）　✅

- **情境**：heading promotion heuristics 是照一種 document generator（bold Workiva）調的，套到異質 corpus 上全面翻車。28-ticker discovery sweep 有 **24 家被標 needs_review**。
- **實例**：
  - TOC 的 PART/Item 條目與正文一起被 promote → JPM h1=22（應為 4）、CRM h2=48、BAC h2=45、BRK.A/B 的 Items 10–14 出現在 Item 1 **之前**（非單調）
  - JPM/INTC 用非粗體 heading（font-weight:400 + font-size jump）→ 只認 `<b>/<strong>` 的邏輯**整批靜默丟棄**（JPM h2=0）
  - Donnelley/Workiva 把 "Item 7." 拆到多個 `<span>` → `get_text(strip=True)` 黏成 "Item7.MD&A" → regex 靜默不匹配
- **修復又引發 regression（展品中的展品）**：第一版 pure last-occurrence-wins dedup 修好了目標 ticker，卻弄壞了原本健康的 JNJ/MSFT/BAC（它們 TOC 是粗體但正文 PART divider 非粗體）→ 改 bold-aware dedup，並建立 **23-ticker hard-gate baseline regression harness**（把已健康的 ticker 鎖住當 regression 網）。
- **成果**：24 → 2 needs_review（PG/INTC 接受 graceful degradation）。
- **證據**：PR #8、commits `66fec6c8df`、`54c8dd1c66`、`5eec055f66`。

### G3. HTML→Markdown 轉換的三個地雷（PR #6）　✅

| 地雷 | 症狀 | 解法 |
|---|---|---|
| Rust html-to-markdown 從 `<title>` 自動生成 frontmatter | 存檔的 10-K 有**兩個** YAML frontmatter 疊在一起，弄壞下游 metadata contract | adapter 先 strip 轉換器的 title block |
| 老 filing（GE 2008）的 text node 內嵌硬換行 | Markdown 變成一行一句碎片（`Item\n1A. Risk Factors.`），**RAG chunking 全毀** | `_normalize_text_whitespace` 模擬瀏覽器 whitespace collapse（`<pre>/<code>` 等除外） |
| MSFT 2025 inline-XBRL 把 heading 拆 span | `get_text(strip=True)` 產出 "PARTI"、"LEGALPROCEEDINGS" → section 偵測失敗；PART II/III/IV **純屬運氣**才通過 | `" ".join(get_text().split())` —— join 後再 normalize，不是逐字串 strip |

### G4. 手刻 HTML parser 的長期不可維護 → edgartools 重寫設計　🔧（設計完成，零實作）

- **情境**：~1000 行手刻 parsing（`html_preprocessor` ~300 行 + `sec_heading_promoter` ~365 行 regex/font-size heuristics），每加一家公司就冒新 quirk（JNJ/MSFT/BAC/BRK 各有專屬 workaround）。配套 research 證實 ALL-CAPS heading 規則不可靠（多數公司用 Title-Case）、`filing.markdown()` 品質跨 sector 不一（12 家中 8 家良好）。
- **解法（設計）**：Path 2 —— 用 edgartools native API（`tenk[item_key]`、`filing.markdown()`）取代整個手刻 pipeline，舊版凍結為 `_html` suffix 做 A/B sunset。
- **狀態**：🔧 990 行 design.md + 6 份 research memos + 9 個 probe scripts 已 rescue 進 branch（`0242332`），實作未開始。
- **證據**：`improve-rag-ingestion/artifacts/current/design.md`。

### G5. Retrieval 其他已修/未修條目（速覽）

| 條目 | 症狀 | 狀態 |
|---|---|---|
| `parse_item()` 只看 header_path 第一層 | 有 Part 層級的 filing 全部標 `_unknown` → item-filtered retrieval 壞掉 | ✅ PR #11（BDD 對真實 filing 驗證才抓到） |
| 單次 upsert 超過 Qdrant 32MB payload 上限 | BAC ~1100 chunks（73MB）ingest 失敗 | ✅ BATCH_SIZE=100 |
| JIT ingestion 在 embeddings 已完成時仍打 EDGAR | 浪費 API calls + 弄壞 integration tests | ✅ PR #11 |
| ingest 先刪舊 points 再呼叫 embedding API | OpenAI 失敗時舊資料已消失 → 該 ticker/year 檢索**靜默回空**（point ID 是 deterministic uuid5，本可直接 upsert 覆蓋） | ⛔ audit C4 |
| EDGAR retry 只 catch `ConnectionError/OSError`，edgartools 走 httpx | **retry 機制實質是死的**；已有正確的 `_classify_edgar_error()` 卻沒被用 | ⛔ audit C3 |
| MarkdownCleaner 過度熱心的規則 | 句子切分器丟掉以數字/引號/括號開頭的真實內容；fixtures 與 production 形狀不符 | ✅ PR #9（"conservative by design: 寧留噪音不誤刪"） |

---

## 展區 H — Eval 系統自身的失敗（Meta 展區：量測工具本身壞掉）

### H1. Vacuous pass 家族：綠燈但什麼都沒測

| 案例 | 機制 | 解法 |
|---|---|---|
| language-policy eval 假通過（PR #3） | assertion loop 迭代「實際被呼叫的 tool」——期望的 tool 沒被呼叫 = 零斷言 = PASS；ticker args 被 `continue` 跳過驗證 | `matched_expected_tool` flag + 強制斷言 + ticker regex |
| CI type-check 檢查了零個檔案（PR #5） | `tsc --noEmit` 不跟 project references → root tsconfig 沒檔案 → 永遠綠 | `tsc -b --noEmit` |
| self-fulfilling integration tests | 測試自己重新實作一份 `_preflight_check`（副本已 drift）、banner test 自己 print 自己 assert | 改為驅動真正的 production 函式 🔧（worktree 未 commit） |

### H2. 兩個 defect 互相抵銷的 false-positive 測試　✅

- **情境**：`useChat.stop()` abort 測試 round-1 PASS 是假的：fixture 用 `textDelta`（AI SDK v6 實為 `delta`）→ SDK 靜默丟掉所有 text chunk → `stop()` 執行時沒有 in-flight text → 測試「通過」但從未行使 abort path。修正欄位名後測試又「失敗」——那是 MSW handler 不支援 `request.signal.abort` 的**第二個 fixture defect 偽裝成 product bug**。
- **教訓**：test plan 照假設的 wire format 寫、mock 基礎設施不 abort-aware —— 兩層假設疊加，PASS 與 FAIL 都不可信。
- **證據**：commit `913fdeafb3`（commit body 有完整 post-mortem）、`90fa11476d`。

### H3. MagicMock 滿足任何屬性 → 「簡化」通過全部單元測試、對真實 EDGAR 直接 crash　✅

- **情境**：review-driven 簡化移除了 `getattr(tenk.company, "name", ...)` 的防禦 fallback。單元測試全綠（MagicMock 自動提供 `.name`），對真實 edgartools 直接 `AttributeError`——`tenk.company` 是 plain `str`。
- **解法**：還原 fallback + 用「bare string」regression test 把真實形狀編碼進單元測試。
- **證據**：commit `eaa80fa314`（PR #14）。

### H4. Scorer 拿到 JSON 字串逐字元迭代 → IR metrics 全是雜訊　🔧（P0）

- **情境**：`dataset_loader._convert_cell` 從不 `json.loads` → `expected_header_paths` 以字串進 scorer → `for p in expected` **逐字元迭代**、`startswith(p)` 用單一字元比對 → recall@5/10、MRR、MAP 產出「接近零但非零」的分數，**看起來像真實的爛成績**，靜默污染 retrieval 品質追蹤。既有 unit tests 全部餵 Python list，永遠測不到這條路。
- **狀態**：🔧 fix 完整（`column_types` typed conversion + loader→scorer 整合測試）但在 worktree `eval-pipeline-fixes` **未 commit**。注意：`v1-eval-experiment-pipeline` 複製了 loader 私有邏輯，此修復**不會自動生效**到 diagnostic 軌。
- **證據**：audit P0-1、`eval-pipeline-fixes` uncommitted diff。

### H5. 指標實作錯誤：「MAP」根本不是 MAP　✅

- **情境**：scorer 實作的是「每個 expected entry 第一次命中的 reciprocal rank 取平均」，掛名 MAP。命中 rank 1 和 3 時回報 0.667，正典 MAP 是 0.833 —— **系統性低估** retrieval 品質，cross-company 案例（3+ expected entries）失真最大。
- **解法**：改為正典 `AP = (1/R)·Σ P@k`（引 Manning/Raghavan/Schütze Ch.8）+ greedy one-to-one binding + 5 個正典 AP 單元案例。
- **證據**：commit `a1353f8489`（PR #11）。

### H6. Eval dataset 本身就是錯的（ground truth 汙染）

| 案例 | 錯誤 | 發現方式 |
|---|---|---|
| sec_retrieval：NVDA fiscal year off-by-one；expected_header_paths 缺 Part 前綴 | scorer 對著錯誤期望打分 | BDD E2E 對真實資料驗證（`2c29bf3474`） |
| language_policy LP-02：scenario 要 GOOGL、dataset 寫 AAPL | 測試案例與 scenario 不符 | BDD loop（`2c8d6e1335`） |
| LP-02 的 AAPL/GOOGL 在兩套平行 eval stack 中**各自漂移** | 兩個 source of truth 量測不同的東西 | audit E3 ⛔ |
| `item 1a` vs `Item 1A` 大小寫差異靜默失分 | near-miss 靜默 0 分 | 建了 `validate_sec_eval_dataset.py` 做 case-insensitive near-miss 偵測 ✅ |

### H7. 外部平台整合的失敗（Braintrust / Langfuse）

| 案例 | 症狀 | 解法 | 狀態 |
|---|---|---|---|
| Braintrust API 憑記憶寫（hallucinated import path / types） | `set_global_handler` import 錯位置、`Eval()` data 型別錯 | 對照真實 SDK 修正（→ 後來的 Context7 驗證規則的起源案例） | ✅ |
| `result.scores` 假設是 Score objects，實為 raw floats | result CSV 寫入失敗 | 兩種格式都支援 | ✅ |
| scorer 的 `"SKIPPED"` 字串 sentinel 洩漏到 Braintrust | 刻意 skip 的 row 在 UI 顯示為 scorer error | 平台邊界把 sentinel 轉回 `None` | 🔧 未 commit |
| 非 local 模式同一 task **跑兩次**（dual-run） | 雙倍 LLM 花費、CSV 與 Braintrust 記錄互相矛盾 | 方向已列入 audit 決策點 6 | ⛔ |
| Braintrust process 級 singleton handler | eval scenario 只能循序跑（max_concurrency=1） | 擴規模前需解 | ⛔ |
| Langfuse free plan 限制（35 字元 score-config 名稱、單一 annotation queue） | 命名被迫縮寫 + profile 收斂 | alias 映射 + 單一 profile | ✅ |
| eval run 結束時 "Event loop is closed" 洗版 | async client 在 loop teardown 後被 GC；nested `asyncio.run` | 在 owning loop 內 `finally` close + 單一 event loop + `braintrust.flush()` | ✅ |

### H8. BDD loop 一輪抓出 6 個 eval-runner defect（PR #4）　✅

task 無 timeout 可掛死、scorer 回 `None` 直接 crash runner、生成的 `output.*` keys 撞爆 CSV 原欄位、Braintrust 上傳先於 local CSV 寫入（上傳失敗 = 全部結果消失）、LP-02 dataset 錯、judge wrapper 對空 rubric 變數列誤動作。單一 commit `2c8d6e1335` 一次列出 —— **執行完整 pipeline 對真實行為驗證（BDD loop）才找得到，unit tests 全部沒抓到**。

### H9. 自動 code-review loop 產生 false-positive findings、fixer 照單全收　✅（revert）

- **情境**：reviewer agent 標了不是問題的問題，fixer agent 沒驗證外部 library 的真實 contract 就「修」了正確的程式碼：(1) 把 cache-first 邏輯改成先查本地 cache —— 但本地 cache **不可能知道** SEC 有沒有更新的 filing，會回 stale data；(2) 為 html-to-markdown **不可能出現**的回傳形狀加防禦碼和測試。
- **解法**：revert + 把真實 invariants 寫進 README。這是 multi-agent review loop 自身的 meta-failure。
- **證據**：commit `5334e9eec8`（PR #6）。

### H10. 開放式問答無法自動打分 → 診斷軌設計決策

- **情境**：near-v1 開放式財經問答**沒有 golden answer**，LLM judge 自動打分容易失真。
- **解法（設計層決策）**：機器只量 `execution_health`（跑得順不順），答案品質交人工在 Langfuse 標註；30 題 dataset 用 `primary_failure_mechanism` 分類學把「預期會怎麼失敗」正式編碼（tool_routing_error ×11、evidence_synthesis_limit ×6、multi_entity_overload ×5、source_coverage_gap ×4、overreach_vs_abstain ×4）。
- **狀態**：pipeline 建好、**人工標註尚未執行**——這是 news/10-K 引用品質量化的前置條件。
- **證據**：`EVAL-V1-DIAGNOSTIC-WALKTHROUGH.md`、near_v1_diagnostic dataset.csv。

---

## 展區 I — Infra / Process 失敗

### I1. `backend/.env`（真實 API keys）被烤進 Docker image　🔧（P0）

- **情境**：docker-compose 與 CI 都用 `context: .`（repo root），但 Docker **只讀 context 根目錄的 `.dockerignore`** —— 既有的 `backend/.dockerignore` 從未被讀取，`COPY backend/ ./backend/` 把 `.env` 複製進 builder 與 runtime 兩層 layer。`docker history` / `docker save` 可還原憑證；image 一旦 push 即外洩。附帶 build context 上傳 `node_modules`/`.venv`/`.git`。
- **解法**：root `.dockerignore`（含 `**/.env.*`）+ multi-stage Dockerfile + non-root user。
- **狀態**：🔧 worktree `dockerignore-env-leak` 的 diff 完整但**全部未 commit**。
- **證據**：audit P0-3、worktree uncommitted diff。

### I2. 六週設計工作曾只存在單一機器的 gitignored 目錄（process failure）　✅

- **情境**：`improve-rag-ingestion` 從 git 看是空 branch，實際藏 53KB design.md + 6 研究 memos；`rag-filter-eval` 的實驗報告 + 6 個 result CSVs（文章要引用的數據）全被 `.gitignore` 排除；3 個 branch 完全未 push —— 單一磁碟故障即全滅。
- **解法**：4 個 rescue commits（force-add 進 branch history）+ CLAUDE.md 新增規則「Commit `artifacts/current/` to the feature branch as it evolves」，規則本文明寫教訓來源。
- **策展價值**：failure → 直接改寫工作協定的範例。

### I3. 其他 infra 展品（速覽）

| 條目 | 一句話 | 狀態 |
|---|---|---|
| LangSmith → Langfuse 遷移 | 觀測層 vendor 選型未考慮規劃中的 LlamaIndex RAG（LangSmith 不支援）→ 整包自製 tracing 一個 sprint 後全刪重來 | ✅（教訓：選型要對照 roadmap） |
| Langfuse session id 兩連發 | 硬編碼 `"new_session"` 把所有對話 lump 成一個 session；修好後 UUID 又只回給 client、沒傳給 Langfuse（生成時機在 `arun()` 之後） | ✅ PR #2 |
| OTel detach error 噪音 | `propagate_attributes()` 跨 async generator 邊界 → 無害但洗版；refcounted logging filter workaround → Langfuse 升級修掉 root cause 後 filter 反而該刪（audit #46：會遮住未來真 detach 錯誤） | filter 清理 ⛔ |
| `.env` 載入依賴 CWD | `load_dotenv()` 相對 CWD 解析 → 換目錄啟動就 silently 缺 keys；**PR #1 和 PR #4 各踩一次** | ✅（`__file__` 錨定） |
| DuckDB `ON CONFLICT SET` 拒收 bare `CURRENT_TIMESTAMP` | binder 當成 column identifier（DDL DEFAULT 卻可以）→ 改 `now()` + WHY comment 防止未來被「修」回去 | ✅ PR #13 |
| SQL 三值邏輯繞過 CHECK | `NULL BETWEEN 1 AND 4` 是 NULL 不是 FALSE → 無效列靜默通過（design review 抓到，preventive） | ✅ PR #13 |
| Vitest 吃掉 Playwright specs | 兩套 runner 打架 | ✅ exclude glob |
| Docs 重大漂移 | AGENTS.md / file_structure.md 描述不存在的 Next.js / BaseAgent / LangSmith —— 「錯的手冊比沒有更糟，agent 會照著下錯指令」 | ⛔ audit G1 |
| 兩套錯誤 hierarchy 同名 class | `TickerNotFoundError` ×2 → import 錯一個，`except` 靜默永不匹配（audit C3 正是實例） | ⛔ audit D4 |
| Session guard 失效 | in-process lock 在 multi-worker 下無效；`/chat/invoke` 完全繞過 busy guard → 交錯寫壞 SQLite checkpoint | ⛔ audit A1/A2 |
| `__pycache__` 被 commit | PR #1 的 repo hygiene | ✅ |

---

## 橫向 Patterns（策展敘事層）

1. **Mock 編碼了與程式碼相同的錯誤假設** —— 最高頻 pattern：wire format mismatch（F1）、tool name undefined（F3）、false-positive abort test（H2）、MagicMock `.name`（H3）全部「mocked tests 全綠、真實系統翻車」。標準修法：BDD browser-use / 真實 integration 驗證找出真形狀 → 把真形狀回填成 unit-level regression test。
2. **Vacuous pass（綠燈但什麼都沒測）** —— eval 假通過、CI 檢查零檔案、self-fulfilling tests、dead retry。教訓：每個 gate 都要能回答「它曾經 fail 過嗎？」。
3. **修復的標準模式是「prompt 硬化 + eval 固定」** —— E1 直接催生 eval framework；此後幾乎每類 failure 都留下 scorer、regression 斷言（DECISION-001）、contract test 或 probe script。
4. **雙端夾擊（two-sided pincer）** —— citation 格式同時在 backend prompt 與 frontend normalize 管線佈防；budget-vs-rate-limit 同時改 backend 措辭與 frontend regex。
5. **外部 API 的靜默垃圾形狀** —— yfinance null、yfinance 404 空殼、Finnhub 全零、edgartools section bleed、AI SDK 未文件化行為：每接一個依賴就要探明 invalid-input 行為並用 live contract test 鎖住。
6. **修復自己引發 regression** —— PART dedup 弄壞健康 ticker（G2）、review-loop false-positive「修好」正確程式碼（H9）、citation strip regex 誤刪正文（A1 殘留）、round-1 review fix 重新引入 retry bug（F4）。對策：hard-gate baseline（已健康樣本鎖住）+ 對修復本身 review。
7. **Human 在迴路中抓到自動化抓不到的** —— PR #7 invalid ticker（human reviewer）、PR #14 section bleed 與 double-EDGAR（human UAT）：concurrency 行為與真實資料內容缺陷對 unit/integration suites 都不可見。

---

## 量化現況與 Evaluation 缺口

| Failure 主題 | 現有量測 | 缺口 |
|---|---|---|
| Language policy（E1） | ✅ 8-case eval + CJK-ratio scorer（5/8→8/8 有 baseline） | 兩套平行 stack 已 drift（H6）待收斂 |
| RAG cross-ticker（G1） | ✅ 18 題 p@10 A/B 實驗（0.622→1.00） | router ticker 抽取準確率未隔離測試 |
| SEC retrieval 品質 | ⚠️ IR metrics 存在但 scorer 有 P0 bug（H4）+ dataset 是 draft placeholder | **目前分數不可信**；修復在 worktree 未 commit |
| Citation format compliance（A1/A2） | ❌ 只有 E2E happy path | 無 scorer 驗證 inline [N]、格式合規率 |
| News 具體性（C1） | ⚠️ 診斷軌已建（failure taxonomy + execution_health） | 人工標註未執行；無 URL-pattern 自動 scorer |
| 10-K source 正確性（B7） | ❌ 無 | 無任何量測；tool 不回 URL 使 grounding 無從驗證 |
| 開放式回答品質（H10） | ⚠️ execution_health only（by design） | Langfuse 人工標註 loop 未跑第一輪 |

---

## ❓ 待與你討論的問題（我不臆測的部分）

1. **B7（10-K source 錯誤）的具體樣態**：你看到的錯是 (a) URL 錯/捏造的 sec.gov 連結、(b) 年度錯、(c) item/section 錯、還是 (d) 內容對不上出處？有沒有印象中的實例或可撈的 Langfuse trace？這決定 B7 在博物館怎麼寫、以及對應 evaluation 怎麼設計。
2. **C1（news generic page）**：你記憶中的 Reuters 案例就是 2026-04-24 那批 diagnostic run（TSLA→`reuters.com/markets/companies/TSLA.F/`），還是更早的手動測試？有沒有嘗試過任何 Tavily query rewriting / URL-pattern filter？（repo 內找不到嘗試痕跡）
3. **博物館收錄範圍**：只收 agent-behavior failures（展區 A–E + G1），還是 eval-meta（H）與 infra/process（I）也要上牆？H 和 I 的故事性很強（vacuous pass、review-loop false positives、六週工作差點消失），但和「建立 Agent 的 failure」主題略有距離。
4. **「現行展品」專區**：audit 中仍 open 的 P0/high（H4 scorer 雜訊、F6 SSE 掛死、B4/B5、G5 的 delete-before-embed 與 dead retry、I1 env leak）要不要在博物館標成「還活著的 bug」專區？這會讓博物館兼具 roadmap 功能。
5. **順帶的風險提醒**（非問題）：`multi-provider-streaming-reasoning`（36 commits）未 push、本機唯一副本，且 uncommitted 變更混入 `backend/Dockerfile` 刪除；`dockerignore-env-leak` 與 `eval-pipeline-fixes` 的 P0 修復都完整但未 commit。

---

## 附錄：證據索引

- **主稽核**：`.artifacts/current/repo_audit_report.md`（2026-07-06）
- **實驗數據**：`fin-lab-x-wt/rag-filter-eval/artifacts/experiment_results.md`
- **診斷軌**：`fin-lab-x-wt/EVAL-V1-DIAGNOSTIC-WALKTHROUGH.md`、`EVAL-STATUS-BRIEF.md`、`v1-eval-experiment-pipeline/backend/evals/results/near_v1_diagnostic_20260424_*.csv`
- **Parsing 研究**：`fin-lab-x-wt/improve-rag-ingestion/artifacts/current/design.md` + `research_*.md`
- **關鍵程式碼**：`frontend/src/lib/markdown-sources.ts`、`backend/common/sec_core.py`、`backend/agent_engine/tools/sec_filing_tools.py`、`backend/agent_engine/tools/financial.py`、`backend/agent_engine/streaming/tool_error_sanitizer.py`、`backend/agent_engine/agents/versions/v1_baseline/system_prompt.md`、`docs/ai_sdk_v6_contract_findings.md`
- **關鍵 commits**：`8a29d9c`（language policy）、`aec4152`/`5b558f2`（citation）、`3783ce8`（wire format）、`66a3295`（heading saga）、`e1d9d98`（SEC tool refactor）、`7af4cdd`（citation policy 轉向）、`2c8d6e1335`（BDD 六連修）、`913fdeafb3`（false-positive test post-mortem）、`5334e9eec8`（review-loop revert）
