# Code Review Improvement Report：Finnhub Agent Tools 抽換

> 日期：2026-06-09 ｜ Branch：`feat/finnhub-agent-tools` ｜ Base：`f0936a5` → Head：`b9fa675`
> Reviewer：claude-opus-4-8（3-lens panel；Codex 不可用——本機 Codex CLI 0.123.0 不支援設定的 `gpt-5.5` model，ChatGPT 帳號亦拒絕替代 model，故 fallback 為同 model 但跨 session/lens 隔離）

## 架構影響摘要

本 PR 把 agent 端的即時市場資料來源從 **Yahoo Finance（`yfinance` scraping，常踩 rate limit）** 換成 **Finnhub 官方 REST API（`finnhub-python` SDK，free tier）**。對 contributor 而言要知道的變更：

1. **工具從 2 個變 3 個**：舊 `yfinance_stock_quote` / `yfinance_get_available_fields` → 新 `finnhub_stock_quote`（即時報價，`/quote`，1 call）、`finnhub_company_basic_financials`（基本面，`/stock/metric`）、`finnhub_get_available_fields`（per-ticker 欄位探索）。拆「報價 vs 基本面」讓「只問股價」時只花 1 個 API call，貼合 free-tier 60 calls/min 的限制。
2. **新增 domain core 層**：`finnhub_client.py`（無 LangChain 依賴，純 fetch + 驗證 + catalog），與 `finnhub_tools.py`（3 個 `@tool`）分離；`get_finnhub_client()` 是 test patch seam。
3. **無效 ticker 處理**：Finnhub free tier 對未知 symbol **不丟 error**（quote 回全 0、basic financials 回空 metric），client 層自行判定並 `raise ValueError`。
4. **Forward P/E 移除**：free tier 無 forward estimate；保留 trailing `peTTM`。
5. **Citation 規則去 Yahoo（DECISION-001）**：報價/基本面改以 provider name（"According to Finnhub..."）標註，不再強制 `finance.yahoo.com/quote/TICKER` URL（free tier 無 per-ticker 公開頁，硬編 URL 違反 zero-hallucination）。
6. **`yfinance` dependency 保留不動**：`quant_data_pipeline` ingestion 子系統是其 documented owner；本 PR 只移除 agent tool 對 yfinance 的使用，**未動** `pyproject.toml` 的 yfinance dep 與 ingestion 程式碼。

## Round 摘要

| Round | Blocking | Major | Minor | Suggestion | 結果 |
|-------|----------|-------|-------|------------|------|
| 1 | 0 | 0 | 4 | 3 | APPROVE WITH NITS |

## 修正項目（fix round 1）

| Issue | Severity | 修正 |
|-------|----------|------|
| m-1.1 | Minor | `marketCap` 描述移除錯誤的 "USD"（Finnhub 回 reporting-currency millions，對非美股如 TSM 會誤導） |
| m-1.2 | Minor | `tools/README.md` Map 修正：`financial.py` 改標為 Tavily-only，新增 `finnhub_tools.py` / `finnhub_client.py` 兩筆 |
| m-1.4 | Minor | `fetch_quote` 全 0 偵測加 WHY 註解 |
| S-1.1 | Suggestion | 新增 opt-in live test，斷言 ≥17/19 catalog metric key 對 AAPL 真實 resolve（防 catalog key 拼錯被 present-only filter 靜默吃掉） |

**Deferred（accepted as-is）**：m-1.3（None vs absent，對稱無害）、S-1.2（`FinnhubAPIException` raw bubble，與 SEC tool 一致）、S-1.3（stream event 順序，cosmetic）。

## Official Standards Check（Context7）

| Library | Version | API Used | Status | Notes |
|---------|---------|----------|--------|-------|
| finnhub-python | 2.4.28 | `Client(api_key=...)`, `client.quote(symbol)`, `client.company_basic_financials(symbol,'all')`, `finnhub.exceptions.FinnhubAPIException` | ✅ Current | 皆為非 deprecated 官方 API；僅用 free-tier endpoint（`/quote`、`/stock/metric`），無 premium leak（未用 `/stock/price-metric`、v1 `/stock/profile`、forward estimates）；19 個 catalog metric key 經真實 free-tier 回傳驗證 resolve。 |

## Final Verification

| 項目 | 命令 | 結果 |
|------|------|------|
| 預設全套件 | `uv run --extra dev pytest backend/tests/ -q` | ✅ 820 passed, 0 failed |
| Live Finnhub（free API） | `... -m finnhub_integration` | ✅ 4 passed（AAPL quote、MSFT financials、invalid → ValueError、catalog 19-key guard） |
| Lint | `uv run --extra dev ruff check` | ✅ All checks passed |
| yfinance 殘留（agent 端） | `grep -rn yfinance backend/agent_engine backend/evals` | ✅ 無（僅測試端的 DECISION-001 regression guard 斷言中保留字面 "yfinance"） |
| ingestion 未波及 | `grep -rln yfinance backend/ingestion` | ✅ 仍在（documented owner，符合預期） |

> **待辦（非本 PR code 問題）**：Agent end-to-end 行為 journey（J-01/02/03，真跑 v1 agent）因 `.env` 的 `OPENAI_API_KEY` 目前回 401（invalid）而未能執行。Finnhub 工具層已由 820 unit + 4 live test 充分驗證；agent 的工具選用/config/prompt 行為由 unit test（S-11/S-12/S-13 + prompt regression guard）涵蓋。換上有效 LLM key 後可補跑 journey。

## Changed Files Manifest

新增：`finnhub_client.py`、`finnhub_tools.py`、`tests/tools/test_finnhub_tools.py`
修改：`financial.py`、`tools/__init__.py`、`tools/README.md`、`agent_engine/README.md`、`agents/base.py`、`v1-v5 orchestrator_config.yaml`、`v1_baseline/system_prompt.md`、`streaming/tool_error_sanitizer.py`、`evals/datasets/language_policy.py`、`evals/scenarios/language_policy/dataset.csv`、`pyproject.toml`、`uv.lock`、以及對齊的既有測試（test_base / test_orchestrator_prompt_rendering / test_e2e / test_scorer_registry / test_v1_integration / streaming/* / test_observe_decorators / test_financial）
