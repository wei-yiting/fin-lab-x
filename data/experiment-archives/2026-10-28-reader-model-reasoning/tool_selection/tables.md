30 of 30 rows labelled: 29 scored for routing (partial gap kept: 29; full gap excluded: 4), 0 partially labelled skipped (–).

Cells are means over rows of per-row means over repetitions; [95% CI] = row-level bootstrap.

## Routing (full coverage-gap rows excluded)

| Config | Rows | Runs | Recall | Recall (successful calls only) | Unnecessary-call rate | Unnecessary calls/run | Errored-only source uses | Median tool calls (all runs) |
|---|---|---|---|---|---|---|---|---|
| reader_gemini_medium | 29 | 87 | 0.89 [0.78, 0.97] | 0.89 [0.78, 0.97] | 0.45 [0.30, 0.60] | 0.62 [0.40, 0.86] | 0 | 4 |
| reader_gemini_minimal | 29 | 87 | 0.79 [0.66, 0.92] | 0.79 [0.66, 0.92] | 0.34 [0.20, 0.52] | 0.41 [0.22, 0.63] | 0 | 3 |
| reader_luna_medium | 29 | 87 | 0.94 [0.87, 1.00] | 0.94 [0.87, 1.00] | 0.31 [0.17, 0.47] | 0.39 [0.21, 0.61] | 0 | 5 |
| reader_luna_none | 29 | 87 | 0.99 [0.97, 1.00] | 0.99 [0.97, 1.00] | 0.39 [0.23, 0.56] | 0.47 [0.29, 0.68] | 0 | 4 |

## Unnecessary calls by source

Runs that called the source / runs on rows where it is labelled 不必要 (routing rows).

| Config | Finnhub quote | Finnhub financials | Tavily news | SEC 10-K |
|---|---|---|---|---|
| reader_gemini_medium | 34/72 (47%) | 7/30 (23%) | 5/21 (24%) | 0/3 (0%) |
| reader_gemini_minimal | 27/72 (38%) | 8/30 (27%) | 0/21 (0%) | 0/3 (0%) |
| reader_luna_medium | 20/72 (28%) | 11/30 (37%) | 0/21 (0%) | 0/3 (0%) |
| reader_luna_none | 19/72 (26%) | 13/30 (43%) | 7/21 (33%) | 0/3 (0%) |

## Ticker-argument accuracy (all labelled rows)

| Config | Rows | Accuracy |
|---|---|---|
| reader_gemini_medium | 30 | 0.98 [0.94, 1.00] |
| reader_gemini_minimal | 30 | 0.99 [0.96, 1.00] |
| reader_luna_medium | 30 | 0.98 [0.94, 1.00] |
| reader_luna_none | 30 | 0.98 [0.95, 1.00] |

## Entity coverage (multi-company rows; 必要 sources × servable tickers, successful calls)

| Config | Rows | All pairs covered | Share of pairs covered |
|---|---|---|---|
| reader_gemini_medium | 12 | 0.67 [0.42, 0.89] | 0.87 [0.76, 0.95] |
| reader_gemini_minimal | 12 | 0.56 [0.31, 0.81] | 0.80 [0.67, 0.92] |
| reader_luna_medium | 12 | 0.78 [0.56, 0.94] | 0.92 [0.84, 0.98] |
| reader_luna_none | 12 | 0.72 [0.50, 0.92] | 0.89 [0.80, 0.98] |

## Coverage-gap checks (full and partial gap rows)

| Config | Rows | Runs | Insufficient evidence stated | Repeated failed calls/run | Runs with a repeated failed call | Retries after source failure/run |
|---|---|---|---|---|---|---|
| reader_gemini_medium | 2 | 6 | 0.50 [0.00, 1.00] | 0.00 [0.00, 0.00] | 0 | 0.33 [0.00, 0.67] |
| reader_gemini_minimal | 2 | 6 | 0.17 [0.00, 0.33] | 0.00 [0.00, 0.00] | 0 | 0.00 [0.00, 0.00] |
| reader_luna_medium | 2 | 6 | 0.83 [0.67, 1.00] | 0.00 [0.00, 0.00] | 0 | 0.67 [0.00, 1.33] |
| reader_luna_none | 2 | 6 | 0.67 [0.33, 1.00] | 0.00 [0.00, 0.00] | 0 | 0.00 [0.00, 0.00] |

## Per row × config

Labels: Q = Finnhub quote, F = Finnhub financials, N = Tavily news, S = SEC 10-K; R = 必要, E = 擇一必要, A = 可接受, U = 不必要.
Routing cells: recall / unnecessary-call rate / mean tool calls. Full-gap cells: insufficient evidence stated / repeated failed calls / mean tool calls.

| Row | Labels | Gap | reader_gemini_medium | reader_gemini_minimal | reader_luna_medium | reader_luna_none |
|---|---|---|---|---|---|---|
| 1 | Q:A F:A N:R S:R |  | 1.00 / 0.00 / 4.3 | 1.00 / 0.00 / 4.0 | 1.00 / 0.00 / 4.7 | 1.00 / 0.00 / 4.0 |
| 2 | Q:U F:U N:R S:R |  | 1.00 / 1.00 / 4.0 | 1.00 / 1.00 / 3.7 | 1.00 / 1.00 / 6.0 | 1.00 / 1.00 / 3.7 |
| 3 | Q:U F:U N:R S:R |  | 1.00 / 1.00 / 3.3 | 1.00 / 1.00 / 3.0 | 1.00 / 1.00 / 5.3 | 1.00 / 1.00 / 3.3 |
| 4 | Q:U F:U N:R S:R | full | 1.00 / 0.0 / 8.0 | 0.33 / 0.0 / 7.3 | 1.00 / 0.0 / 9.0 | 1.00 / 0.0 / 5.0 |
| 5 | Q:U F:E N:R S:E |  | 1.00 / 1.00 / 4.7 | 1.00 / 1.00 / 4.0 | 1.00 / 1.00 / 5.3 | 1.00 / 1.00 / 4.0 |
| 6 | Q:U F:A N:R S:R |  | 0.67 / 0.67 / 2.3 | 0.00 / 0.00 / 1.0 | 1.00 / 0.00 / 3.3 | 1.00 / 0.00 / 3.3 |
| 7 | Q:U F:U N:R S:R |  | 1.00 / 0.00 / 2.0 | 0.00 / 0.00 / 1.0 | 1.00 / 0.00 / 3.3 | 1.00 / 1.00 / 3.0 |
| 8 | Q:U F:A N:U S:R |  | 1.00 / 1.00 / 4.7 | 1.00 / 0.00 / 2.3 | 1.00 / 0.00 / 3.7 | 1.00 / 1.00 / 4.0 |
| 9 | Q:U F:A N:R S:R |  | 0.67 / 0.33 / 4.0 | 0.33 / 0.00 / 2.3 | 1.00 / 0.00 / 6.7 | 1.00 / 0.00 / 5.7 |
| 10 | Q:U F:U N:R S:R |  | 0.00 / 0.00 / 3.0 | 0.00 / 0.00 / 3.0 | 1.00 / 0.00 / 6.0 | 0.67 / 0.00 / 4.3 |
| 11 | Q:U F:U N:A S:R |  | 1.00 / 0.00 / 2.3 | 1.00 / 0.00 / 1.7 | 1.00 / 0.00 / 2.0 | 1.00 / 0.00 / 1.3 |
| 12 | Q:U F:A N:A S:R |  | 1.00 / 0.33 / 2.7 | 1.00 / 0.33 / 2.7 | 1.00 / 0.00 / 2.0 | 1.00 / 0.00 / 3.0 |
| 13 | Q:U F:U N:U S:R |  | 1.00 / 0.00 / 2.0 | 1.00 / 0.00 / 2.0 | 1.00 / 0.00 / 2.0 | 1.00 / 0.00 / 2.7 |
| 14 | Q:U F:U N:R S:R |  | 0.67 / 0.00 / 2.0 | 0.67 / 0.67 / 2.3 | 1.00 / 0.00 / 5.0 | 1.00 / 0.00 / 2.0 |
| 15 | Q:U F:U N:U S:R |  | 1.00 / 0.33 / 1.3 | 1.00 / 1.00 / 2.7 | 1.00 / 0.67 / 2.3 | 1.00 / 1.00 / 2.3 |
| 16 | Q:U F:U N:A S:R |  | 1.00 / 1.00 / 2.3 | 1.00 / 0.33 / 1.3 | 1.00 / 0.67 / 2.7 | 1.00 / 1.00 / 3.7 |
| 17 | Q:U F:U N:A S:R |  | 1.00 / 0.67 / 3.7 | 1.00 / 0.67 / 3.0 | 1.00 / 1.00 / 5.7 | 1.00 / 1.00 / 3.7 |
| 18 | Q:U F:A N:U S:R |  | 1.00 / 0.00 / 4.0 | 1.00 / 0.00 / 2.7 | 1.00 / 0.00 / 2.7 | 1.00 / 0.00 / 4.0 |
| 19 | Q:U F:A N:U S:R |  | 1.00 / 1.00 / 3.7 | 1.00 / 0.00 / 2.0 | 1.00 / 0.67 / 3.3 | 1.00 / 1.00 / 3.0 |
| 20 | Q:U F:A N:A S:R |  | 1.00 / 1.00 / 4.0 | 1.00 / 1.00 / 3.0 | 1.00 / 0.33 / 2.7 | 1.00 / 0.33 / 3.3 |
| 21 | Q:U F:A N:U S:R |  | 1.00 / 0.33 / 4.7 | 1.00 / 0.00 / 3.3 | 1.00 / 0.00 / 6.0 | 1.00 / 0.33 / 4.7 |
| 22 | Q:U F:A N:A S:R |  | 1.00 / 0.00 / 6.0 | 1.00 / 0.00 / 6.0 | 1.00 / 0.00 / 6.7 | 1.00 / 0.00 / 6.0 |
| 23 | Q:A F:R N:R S:A |  | 1.00 / 0.00 / 4.0 | 1.00 / 0.00 / 4.0 | 1.00 / 0.00 / 4.0 | 1.00 / 0.00 / 4.0 |
| 24 | Q:A F:R N:R S:A |  | 0.67 / 0.00 / 6.0 | 0.33 / 0.00 / 6.0 | 0.67 / 0.00 / 7.3 | 1.00 / 0.00 / 8.0 |
| 25 | Q:A F:R N:R S:U |  | 1.00 / 0.00 / 5.7 | 0.67 / 0.00 / 5.0 | 0.33 / 0.00 / 4.7 | 1.00 / 0.00 / 6.0 |
| 26 | Q:A F:R N:R S:R |  | 0.00 / 0.00 / 9.0 | 0.00 / 0.00 / 7.0 | 0.33 / 0.00 / 10.0 | 1.00 / 0.00 / 8.3 |
| 27 | Q:U F:A N:A S:R |  | 1.00 / 1.00 / 4.7 | 1.00 / 1.00 / 4.0 | 1.00 / 1.00 / 6.7 | 1.00 / 0.33 / 3.3 |
| 28 | Q:U F:A N:R S:A |  | 1.00 / 1.00 / 4.0 | 1.00 / 1.00 / 4.0 | 1.00 / 1.00 / 4.0 | 1.00 / 1.00 / 4.0 |
| 29 | Q:U F:A N:R S:R | partial | 1.00 / 1.00 / 7.3 | 1.00 / 1.00 / 5.3 | 1.00 / 0.67 / 10.0 | 1.00 / 0.33 / 6.0 |
| 30 | Q:U F:A N:U S:R |  | 1.00 / 0.33 / 8.7 | 1.00 / 0.00 / 6.3 | 1.00 / 0.00 / 8.3 | 1.00 / 0.00 / 6.0 |

## Ticker args outside the expected list (calls, all configs)

| Row | Expected | Off-list (calls) |
|---|---|---|
| 8 | JPM | BAC ×1 |
| 16 | V | JPM ×2 |
| 27 | JPM | BAC ×2, C ×2, WFC ×2 |
| 29 | AIR.PA, BA | AIR ×5, EADSY ×7 |

## Entity coverage per row × config (share of runs with all pairs covered)

Missed pairs are counted over all configs; Q/F/N/S as above.

| Row | Tickers | reader_gemini_medium | reader_gemini_minimal | reader_luna_medium | reader_luna_none | Missed pairs (runs) |
|---|---|---|---|---|---|---|
| 4 | ASML, TSM | 1.00 | 1.00 | 1.00 | 0.00 | N:ASML ×3 |
| 9 | AAPL, META | 0.67 | 0.00 | 1.00 | 0.67 | N:META ×5, N:AAPL ×3 |
| 10 | AAPL, GOOGL, META | 0.00 | 0.00 | 1.00 | 0.33 | N:GOOGL ×8, N:META ×8, N:AAPL ×7 |
| 13 | MA, V | 1.00 | 1.00 | 1.00 | 1.00 | none |
| 18 | KO, PEP | 1.00 | 1.00 | 1.00 | 1.00 | none |
| 21 | COST, WMT | 1.00 | 1.00 | 1.00 | 1.00 | none |
| 22 | AAPL, GOOGL, MSFT | 1.00 | 1.00 | 1.00 | 1.00 | none |
| 24 | NVDA, TSLA | 0.67 | 0.33 | 0.67 | 1.00 | N:NVDA ×4, N:TSLA ×4 |
| 25 | DIS, NFLX | 0.67 | 0.33 | 0.33 | 1.00 | N:NFLX ×4, N:DIS ×4 |
| 26 | COST, LLY, NVDA | 0.00 | 0.00 | 0.00 | 0.67 | S:COST ×6, S:LLY ×6, S:NVDA ×5, N:COST ×4, N:LLY ×4, N:NVDA ×3 |
| 29 | AIR.PA, BA | 0.00 | 0.00 | 0.33 | 0.00 | N:AIR.PA ×11, N:BA ×2 |
| 30 | COST, MCD, WMT | 1.00 | 1.00 | 1.00 | 1.00 | none |

## Coverage-gap audit: matched insufficiency phrase per run

| Row | Config | Rep | Matched phrase |
|---|---|---|---|
| 4 | reader_gemini_medium | 1 | 工具無法 |
| 4 | reader_gemini_medium | 2 | 工具無法 |
| 4 | reader_gemini_medium | 3 | 資料限制 |
| 4 | reader_gemini_minimal | 1 | (none) |
| 4 | reader_gemini_minimal | 2 | 數據限制 |
| 4 | reader_gemini_minimal | 3 | (none) |
| 4 | reader_luna_medium | 1 | 工具只支援 |
| 4 | reader_luna_medium | 2 | 工具只支援 |
| 4 | reader_luna_medium | 3 | 工具只支援 |
| 4 | reader_luna_none | 1 | 證據不足 |
| 4 | reader_luna_none | 2 | 工具無法 |
| 4 | reader_luna_none | 3 | 證據不足 |
| 29 | reader_gemini_medium | 1 | (none) |
| 29 | reader_gemini_medium | 2 | (none) |
| 29 | reader_gemini_medium | 3 | (none) |
| 29 | reader_gemini_minimal | 1 | (none) |
| 29 | reader_gemini_minimal | 2 | (none) |
| 29 | reader_gemini_minimal | 3 | (none) |
| 29 | reader_luna_medium | 1 | 沒有取得 |
| 29 | reader_luna_medium | 2 | (none) |
| 29 | reader_luna_medium | 3 | 沒有取得 |
| 29 | reader_luna_none | 1 | 無法取得 |
| 29 | reader_luna_none | 2 | (none) |
| 29 | reader_luna_none | 3 | (none) |
