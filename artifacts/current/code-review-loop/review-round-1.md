# Code Review Round 1

> Reviewer: claude-opus-4-8 (3-lens panel, Codex unavailable) | Date: 2026-06-09

## Summary
| Metric | Count |
|--------|-------|
| Total issues | 7 |
| Blocking | 0 |
| Major | 0 |
| Minor | 4 |
| Suggestion | 3 |
| Library checks | 1 |

## Issues

### [Blocking]
None.

### [Major]
None.

### [Minor] m-1.1: `marketCap` description hard-codes "USD" but Finnhub returns reporting-currency millions
- **File:** `backend/agent_engine/tools/finnhub_client.py` L27-29
- **Problem:** The catalog labels `marketCapitalization` as `"Market capitalization (USD millions)"` (verified verbatim in source). Finnhub's `/stock/metric` returns this field in millions of the company's **reporting currency**, not unconditionally USD. The scale (millions) is right; the USD assertion is wrong for foreign-domiciled issuers / non-USD ADRs. This string is surfaced verbatim to the agent via `finnhub_get_available_fields` (`available[out_key] = {"description": spec.description, ...}`), and the PR's own `system_prompt` example uses TSM (Taiwan-domiciled) — a realistic non-USD mismatch. Under the ZERO HALLUCINATION / data-quality policy, a wrong currency claim can leak into a user-facing answer. This is the strongest finding of the round.
- **Fix:** Drop the currency qualifier: `"Market capitalization (millions of reporting currency)"` or `"Market capitalization (in millions)"`. Do not assert USD when Finnhub does not guarantee it.
- **Context7:** `/finnhub-stock-api/finnhub-python` confirms `company_basic_financials(symbol, 'all')` returns `data['metric']` as a key/value ratio map; `marketCapitalization` is documented as reporting-currency millions in Finnhub's `/stock/metric` schema, not unconditionally USD.

### [Minor] m-1.2: `tools/README.md` Map now mis-attributes Finnhub to `financial.py` and omits the two new files
- **File:** `backend/agent_engine/tools/README.md` L6
- **Problem:** Verified against the branch: this PR deleted the yfinance tools from `financial.py` and added Finnhub in two NEW files (`finnhub_client.py`, `finnhub_tools.py`); `financial.py` now contains only `tavily_financial_search`. Yet the README diff rewrote line 6 to read `financial.py: ... quantitative data retrieval via Finnhub and ... Tavily` — so the doc now (a) attributes Finnhub to the wrong file, and (b) has zero Map entries for the two new files, even though every other module (`registry`, `sec_filing_tools`, `sec_filing`, `__init__`) gets one. The README "Map" is this folder's canonical doc surface and the PR actively made it less accurate.
- **Fix:** Correct line 6 to describe `financial.py` as Tavily-only news search, and add two Map bullets: `finnhub_tools.py` (the 3 `@tool` wrappers: `finnhub_stock_quote`, `finnhub_company_basic_financials`, `finnhub_get_available_fields`) and `finnhub_client.py` (LangChain-free domain core: client seam, fetch functions, `BASIC_FINANCIALS_CATALOG`). A dedicated Finnhub README is overkill — the existing Map lines are the right place.

### [Minor] m-1.3: None-valued metric is indistinguishable from "field not covered" (symmetric, but genuine info loss)
- **File:** `backend/agent_engine/tools/finnhub_tools.py` L92-96, L127-131
- **Problem:** Both `finnhub_company_basic_financials` and `finnhub_get_available_fields` drop fields via `spec.metric_key in metric and metric[spec.metric_key] is not None`. A metric Finnhub returns explicitly as `null` is treated identically to one the API never returned. Real information loss. Severity is held at Minor (not Major) because the loss is **symmetric**: the discovery tool (tool 3) applies the exact same None-filter as the data tool (tool 2), so a None field is invisible in BOTH the catalog and the data — the agent never asks for something it was told exists, so its view is internally coherent. Verified the two predicates are byte-identical in source.
- **Fix:** Acceptable as-is for a token-efficient present-only contract. If you ever want the agent to distinguish "null" from "absent", keep None-valued keys in `get_available_fields` with `{"available": True, "value": None}` while still excluding them from the data tool. No change required for this PR.

### [Minor] m-1.4: All-zero invalid-ticker detection's WHY lives in the module docstring, not at the branch
- **File:** `backend/agent_engine/tools/finnhub_client.py` L65-72
- **Problem:** `fetch_quote` treats a quote as invalid only when BOTH `c` and `pc` are 0/None. The load-bearing rationale (Finnhub free tier returns an all-zero payload — not an error — for unknown tickers, and checking `c` alone would false-positive a legitimately-zero pre-market `c`) is explained in the module docstring (L4-6), but not at the conditional itself. A future reader editing `fetch_quote` in isolation sees a non-obvious two-field zero-check. Honest assessment: this is borderline — the docstring is only three lines up — but flagged because the logic is subtle and the edit risk is real.
- **Fix:** Optional one-line WHY comment above the guard, e.g. `# Finnhub free tier returns an all-zero payload (not an error) for unknown tickers; c==0 AND pc==0 is the invalid-ticker signal.`

### [Suggestion] S-1.1: Committed live tests under-assert the "all 19 catalog keys resolve" claim
- **File:** `backend/tests/tools/test_finnhub_tools.py` L159-163
- **Problem:** The PR states all 19 `BASIC_FINANCIALS_CATALOG` keys resolved for AAPL live, but `test_live_basic_financials_known_ticker` only asserts `"peTTM" in m or "52WeekHigh" in m`. The catalog keys are data-driven Finnhub strings (`totalDebt/totalEquityQuarterly` with a literal slash, `10DayAverageTradingVolume` with a leading digit, mixed `Quarterly`/`TTM` suffixes) that are NOT enumerated in the SDK or Context7 docs — only the one-time manual live run validates them. A silent typo in one catalog key would be silently dropped by the present-only filter (no error), and no committed test would catch the drift.
- **Fix:** Optional: strengthen the live integration test to assert a representative subset of the trickier keys resolve for a large-cap (e.g. assert at least N of the 19 output keys appear for AAPL/MSFT). Converts the one-time manual check into a regression guard. Not blocking — the live run validated it once.

### [Suggestion] S-1.2: `FinnhubAPIException` bubbles raw instead of mapping status codes
- **File:** `backend/agent_engine/tools/finnhub_client.py` L62, L74
- **Problem:** `fetch_quote`/`fetch_basic_financials` let `FinnhubAPIException` propagate raw into `_HandleToolErrors`, where it collapses to `sanitize_tool_error(str(e))`. The SDK exposes structured `e.status_code`/`e.message` (401 bad key, 403 premium/not-entitled, 429 rate limit). This is functionally correct — 429 does reach the existing middleware and is surfaced as `ToolMessage(status="error")`, matching the SEC tools' contract and the PR's stated design — so it is NOT a bug. A targeted `except FinnhubAPIException` distinguishing 403 ("not available on free tier") from 429 ("upstream rate limit") would give the agent better signal.
- **Fix:** Optional: catch `finnhub.exceptions.FinnhubAPIException` and re-raise as `ValueError` with a status-code-aware message. Leaving it to bubble is acceptable and consistent with the SEC tools.
- **Context7:** `/finnhub-stock-api/finnhub-python` documents `FinnhubAPIException` with `e.status_code` (401/403/429) and `e.message` and shows the recommended try/except pattern; the code does not use these structured fields.

### [Suggestion] S-1.3: Stream "querying" event fires before fetch + stream-writer-PRESENT path is untested
- **File:** `backend/agent_engine/tools/finnhub_tools.py` L35-48 (all 3 tools); `backend/tests/tools/test_finnhub_tools.py` L142-149
- **Problem:** Two small, related observations, both downgraded from the lenses' Minor framing because each is cosmetic/low-value. (a) In all three tools the `writer({...status...})` call runs before `fetch_*`, so on a missing key / invalid ticker the stream shows a "Querying AAPL..." start with no completion before the sanitized error. Verified — but this exactly matches the prior yfinance tools' writer-before-fetch ordering, so it is not a regression. (b) The `get_stream_writer()`-PRESENT branch has no positive test: `test_finnhub_tools_work_without_stream_writer` covers the `except -> writer=None` path, but no test asserts the status-event dict is written when a writer exists.
- **Fix:** (a) No change needed unless you want the start event to imply success — documented as a conscious choice. (b) Optional: one test patching `get_stream_writer` to a `MagicMock` and asserting the status dict (`status`/`toolName`/`toolCallId`) is written. Low priority — the writer block is simple and identical across all 3 tools and the SEC tools.

## Documentation Gaps
| Folder | Missing |
|--------|---------|
| `backend/agent_engine/tools/` | `tools/README.md` Map section: no entries for `finnhub_client.py` / `finnhub_tools.py`, and line 6 mis-attributes Finnhub to `financial.py` (see m-1.2). |

## Official Standards Check
| Library | Version | API Used | Status | Notes |
|---------|---------|----------|--------|-------|
| finnhub-python | 2.4.28 (installed; pyproject pins >=2.4.28) | `finnhub.Client(api_key=...)`, `client.quote(symbol)`, `client.company_basic_financials(symbol, 'all')`, `finnhub.exceptions.FinnhubAPIException` | Correct / current / non-deprecated; FREE-TIER SAFE | Signatures inspected on the installed SDK match Context7 (`/finnhub-stock-api/finnhub-python`) exactly: `__init__(self, api_key, proxies=None)`, `quote(self, symbol)`, `company_basic_financials(self, symbol, metric)`; `'all'` is a documented `_type` value; calls use positional args correctly. `quote()` GETs `/quote`, `company_basic_financials()` GETs `/stock/metric` — both return raw JSON with no client-side validation, consistent with the code's invalid-ticker assumption (all-zero quote / empty metric map rather than raising). `_handle_response` raises `FinnhubAPIException` on any non-2xx (429 included) with no internal retry — confirms the 429-bubble design. No premium leak: `price_metrics` (`/stock/price-metric`) exists but is correctly unused; no v2 profile/estimates/recommendations; `forwardPE` correctly dropped (grep over `backend/agent_engine/tools` confirms zero premium-field refs). All 19 `BASIC_FINANCIALS_CATALOG` keys (incl. slash-containing `totalDebt/totalEquityQuarterly`, leading-digit `10DayAverageTradingVolume`, mixed `Quarterly`/`TTM` suffixes) are real `/stock/metric` keys, empirically resolved for AAPL — but the exact key namespace is NOT enumerated in the SDK or Context7 docs, so it relies on the PR's live run (see S-1.1). Only semantic caveat: `marketCapitalization` description hard-codes USD (it is reporting-currency millions) — see m-1.1. |

## Notes on reconciliation
- **No false positives carried forward.** The intentional yfinance regression-guard assertion and retained yfinance dependency (owned by `ingestion/quant_data_pipeline`) are confirmed legitimate by all three lenses — explicitly NOT residue.
- **Dropped non-findings:** the three PRAGMATISM "design-question" entries (client/tools split is justified — keep it; tool-2/tool-3 catalog-loop duplication should NOT be extracted; output-key naming is clear) are the lens answering with "no change" and are excluded rather than inflating the count.
- **Honest downgrade:** CORRECTNESS rated the "querying event fires before fetch" observation Minor, but its own fix is "No change needed" and it matches prior tooling — merged into S-1.3 at Suggestion.
- The invalid-ticker `c AND pc` logic, field mapping (`c->currentPrice` … `l->dayLow`), call-time key read, 429 bubbling, empty-metric guard, ticker normalization-before-call, and config/`__init__` consistency were all independently verified PASS.