30 of 30 rows labelled: 29 scored for routing (partial gap kept: 29; full gap excluded: 4), 0 partially labelled skipped (–).

Cells are means over rows of per-row means over repetitions; [95% CI] = row-level bootstrap.

## Routing (full coverage-gap rows excluded)

| Config | Rows | Runs | Recall | Recall (successful calls only) | Unnecessary-call rate | Unnecessary calls/run | Errored-only source uses | Median tool calls (all runs) |
|---|---|---|---|---|---|---|---|---|
| luna_medium | 29 | 87 | 0.89 [0.77, 0.99] | 0.89 [0.77, 0.99] | 0.34 [0.20, 0.51] | 0.48 [0.26, 0.74] | 0 | 6 |
| luna_medium_plus_search | 29 | 87 | 0.87 [0.77, 0.97] | 0.86 [0.76, 0.95] | 0.28 [0.14, 0.41] | 0.36 [0.17, 0.55] | 1 | 6 |
| reader_luna_medium | 29 | 87 | 0.95 [0.89, 1.00] | 0.94 [0.87, 1.00] | 0.26 [0.11, 0.43] | 0.33 [0.14, 0.56] | 1 | 4 |
| reader_prompt_no_search | 29 | 87 | 0.97 [0.91, 1.00] | 0.94 [0.87, 1.00] | 0.23 [0.10, 0.38] | 0.29 [0.11, 0.49] | 2 | 6 |

## Unnecessary calls by source

Runs that called the source / runs on rows where it is labelled 不必要 (routing rows).

| Config | Finnhub quote | Finnhub financials | Tavily news | SEC 10-K |
|---|---|---|---|---|
| luna_medium | 20/72 (28%) | 13/30 (43%) | 1/21 (5%) | 0/3 (0%) |
| luna_medium_plus_search | 20/72 (28%) | 9/30 (30%) | 0/21 (0%) | 0/3 (0%) |
| reader_luna_medium | 16/72 (22%) | 9/30 (30%) | 0/21 (0%) | 0/3 (0%) |
| reader_prompt_no_search | 18/72 (25%) | 7/30 (23%) | 0/21 (0%) | 0/3 (0%) |

## Ticker-argument accuracy (all labelled rows)

| Config | Rows | Accuracy |
|---|---|---|
| luna_medium | 30 | 0.99 [0.97, 1.00] |
| luna_medium_plus_search | 30 | 0.98 [0.96, 1.00] |
| reader_luna_medium | 30 | 0.98 [0.94, 1.00] |
| reader_prompt_no_search | 30 | 0.99 [0.98, 1.00] |

## Entity coverage (multi-company rows; 必要 sources × servable tickers, successful calls)

| Config | Rows | All pairs covered | Share of pairs covered |
|---|---|---|---|
| luna_medium | 12 | 0.83 [0.64, 1.00] | 0.94 [0.87, 1.00] |
| luna_medium_plus_search | 12 | 0.81 [0.61, 0.97] | 0.91 [0.82, 0.98] |
| reader_luna_medium | 12 | 0.75 [0.58, 0.92] | 0.90 [0.81, 0.97] |
| reader_prompt_no_search | 12 | 0.86 [0.69, 1.00] | 0.94 [0.88, 1.00] |

## Coverage-gap checks (full and partial gap rows)

| Config | Rows | Runs | Insufficient evidence stated | Repeated failed calls/run | Runs with a repeated failed call | Retries after source failure/run |
|---|---|---|---|---|---|---|
| luna_medium | 2 | 6 | 0.67 [0.67, 0.67] | 0.00 [0.00, 0.00] | 0 | 0.00 [0.00, 0.00] |
| luna_medium_plus_search | 2 | 6 | 0.67 [0.33, 1.00] | 0.00 [0.00, 0.00] | 0 | 0.00 [0.00, 0.00] |
| reader_luna_medium | 2 | 6 | 0.83 [0.67, 1.00] | 0.00 [0.00, 0.00] | 0 | 0.33 [0.00, 0.67] |
| reader_prompt_no_search | 2 | 6 | 0.83 [0.67, 1.00] | 0.00 [0.00, 0.00] | 0 | 0.00 [0.00, 0.00] |

## Per row × config

Labels: Q = Finnhub quote, F = Finnhub financials, N = Tavily news, S = SEC 10-K; R = 必要, E = 擇一必要, A = 可接受, U = 不必要.
Routing cells: recall / unnecessary-call rate / mean tool calls. Full-gap cells: insufficient evidence stated / repeated failed calls / mean tool calls.

| Row | Labels | Gap | luna_medium | luna_medium_plus_search | reader_luna_medium | reader_prompt_no_search |
|---|---|---|---|---|---|---|
| 1 | Q:A F:A N:R S:R |  | 1.00 / 0.00 / 7.0 | 1.00 / 0.00 / 6.3 | 1.00 / 0.00 / 4.3 | 1.00 / 0.00 / 6.0 |
| 2 | Q:U F:U N:R S:R |  | 1.00 / 1.00 / 6.0 | 1.00 / 1.00 / 7.0 | 1.00 / 1.00 / 5.3 | 1.00 / 1.00 / 6.3 |
| 3 | Q:U F:U N:R S:R |  | 0.00 / 0.00 / 4.7 | 0.33 / 0.00 / 5.0 | 1.00 / 0.33 / 3.7 | 1.00 / 0.33 / 5.0 |
| 4 | Q:U F:U N:R S:R | full | 0.67 / 0.0 / 8.7 | 1.00 / 0.0 / 8.7 | 1.00 / 0.0 / 7.3 | 1.00 / 0.0 / 8.0 |
| 5 | Q:U F:E N:R S:E |  | 1.00 / 1.00 / 7.0 | 1.00 / 1.00 / 6.3 | 1.00 / 1.00 / 5.0 | 1.00 / 1.00 / 6.7 |
| 6 | Q:U F:A N:R S:R |  | 1.00 / 0.00 / 6.0 | 1.00 / 0.33 / 7.0 | 1.00 / 0.00 / 3.7 | 1.00 / 0.33 / 6.7 |
| 7 | Q:U F:U N:R S:R |  | 1.00 / 0.00 / 7.3 | 0.67 / 0.00 / 7.0 | 1.00 / 0.00 / 3.3 | 1.00 / 0.00 / 7.0 |
| 8 | Q:U F:A N:U S:R |  | 1.00 / 0.00 / 3.7 | 1.00 / 0.00 / 5.0 | 1.00 / 0.00 / 3.3 | 1.00 / 0.00 / 3.0 |
| 9 | Q:U F:A N:R S:R |  | 1.00 / 0.00 / 10.0 | 1.00 / 0.00 / 9.3 | 1.00 / 0.00 / 6.0 | 1.00 / 0.00 / 7.3 |
| 10 | Q:U F:U N:R S:R |  | 0.67 / 0.67 / 9.0 | 1.00 / 0.00 / 8.0 | 1.00 / 0.00 / 4.7 | 1.00 / 0.00 / 9.0 |
| 11 | Q:U F:U N:A S:R |  | 1.00 / 0.00 / 3.3 | 1.00 / 0.00 / 4.0 | 1.00 / 0.00 / 2.3 | 1.00 / 0.00 / 3.0 |
| 12 | Q:U F:A N:A S:R |  | 1.00 / 0.00 / 5.0 | 1.00 / 0.00 / 5.0 | 1.00 / 0.00 / 2.0 | 1.00 / 0.00 / 3.7 |
| 13 | Q:U F:U N:U S:R |  | 1.00 / 0.00 / 6.0 | 1.00 / 0.00 / 6.0 | 1.00 / 0.00 / 2.7 | 1.00 / 0.00 / 5.3 |
| 14 | Q:U F:U N:R S:R |  | 0.00 / 0.00 / 4.7 | 0.33 / 0.33 / 6.3 | 1.00 / 0.00 / 5.0 | 0.67 / 0.00 / 4.7 |
| 15 | Q:U F:U N:U S:R |  | 1.00 / 0.67 / 4.3 | 1.00 / 0.33 / 4.3 | 1.00 / 1.00 / 3.0 | 1.00 / 0.00 / 3.7 |
| 16 | Q:U F:U N:A S:R |  | 1.00 / 1.00 / 5.7 | 1.00 / 0.67 / 5.0 | 1.00 / 0.00 / 2.7 | 1.00 / 0.33 / 4.0 |
| 17 | Q:U F:U N:A S:R |  | 1.00 / 1.00 / 6.0 | 1.00 / 1.00 / 7.0 | 1.00 / 1.00 / 4.3 | 1.00 / 1.00 / 6.3 |
| 18 | Q:U F:A N:U S:R |  | 1.00 / 0.33 / 8.7 | 1.00 / 0.00 / 7.3 | 1.00 / 0.00 / 2.7 | 1.00 / 0.00 / 8.0 |
| 19 | Q:U F:A N:U S:R |  | 1.00 / 1.00 / 6.0 | 1.00 / 1.00 / 6.3 | 1.00 / 0.00 / 3.0 | 1.00 / 0.00 / 5.0 |
| 20 | Q:U F:A N:A S:R |  | 1.00 / 0.33 / 5.3 | 1.00 / 0.33 / 5.0 | 1.00 / 0.33 / 2.3 | 1.00 / 1.00 / 4.7 |
| 21 | Q:U F:A N:U S:R |  | 1.00 / 0.00 / 6.7 | 1.00 / 0.00 / 8.0 | 1.00 / 0.00 / 4.7 | 1.00 / 0.00 / 6.7 |
| 22 | Q:U F:A N:A S:R |  | 1.00 / 0.00 / 9.0 | 1.00 / 0.00 / 8.0 | 1.00 / 0.00 / 6.0 | 1.00 / 0.00 / 7.0 |
| 23 | Q:A F:R N:R S:A |  | 1.00 / 0.00 / 5.7 | 1.00 / 0.00 / 4.0 | 1.00 / 0.00 / 4.0 | 1.00 / 0.00 / 6.7 |
| 24 | Q:A F:R N:R S:A |  | 1.00 / 0.00 / 6.7 | 1.00 / 0.00 / 6.0 | 0.33 / 0.00 / 5.3 | 1.00 / 0.00 / 10.0 |
| 25 | Q:A F:R N:R S:U |  | 1.00 / 0.00 / 6.0 | 0.00 / 0.00 / 4.0 | 0.33 / 0.00 / 4.7 | 1.00 / 0.00 / 6.0 |
| 26 | Q:A F:R N:R S:R |  | 0.00 / 0.00 / 8.0 | 0.33 / 0.00 / 9.0 | 1.00 / 0.00 / 10.0 | 0.33 / 0.00 / 9.0 |
| 27 | Q:U F:A N:A S:R |  | 1.00 / 1.00 / 6.3 | 1.00 / 0.67 / 8.0 | 1.00 / 1.00 / 5.7 | 1.00 / 0.67 / 6.7 |
| 28 | Q:U F:A N:R S:A |  | 1.00 / 1.00 / 4.3 | 1.00 / 1.00 / 5.7 | 1.00 / 1.00 / 5.0 | 1.00 / 1.00 / 5.0 |
| 29 | Q:U F:A N:R S:R | partial | 1.00 / 1.00 / 10.0 | 0.67 / 0.33 / 8.3 | 1.00 / 1.00 / 10.3 | 1.00 / 0.00 / 8.7 |
| 30 | Q:U F:A N:U S:R |  | 1.00 / 0.00 / 9.0 | 1.00 / 0.00 / 8.0 | 1.00 / 0.00 / 8.3 | 1.00 / 0.00 / 6.0 |

## Ticker args outside the expected list (calls, all configs)

| Row | Expected | Off-list (calls) |
|---|---|---|
| 16 | V | JPM ×1 |
| 27 | JPM | BAC ×3, C ×3, GS ×1, MS ×1, WFC ×3 |
| 29 | AIR.PA, BA | AIR ×7, EADSY ×5 |

## Entity coverage per row × config (share of runs with all pairs covered)

Missed pairs are counted over all configs; Q/F/N/S as above.

| Row | Tickers | luna_medium | luna_medium_plus_search | reader_luna_medium | reader_prompt_no_search | Missed pairs (runs) |
|---|---|---|---|---|---|---|
| 4 | ASML, TSM | 1.00 | 1.00 | 1.00 | 1.00 | none |
| 9 | AAPL, META | 1.00 | 1.00 | 1.00 | 1.00 | none |
| 10 | AAPL, GOOGL, META | 0.67 | 0.67 | 0.33 | 0.33 | N:GOOGL ×5, N:META ×5, N:AAPL ×4, S:AAPL ×1, S:GOOGL ×1, S:META ×1 |
| 13 | MA, V | 1.00 | 1.00 | 1.00 | 1.00 | none |
| 18 | KO, PEP | 1.00 | 1.00 | 1.00 | 1.00 | none |
| 21 | COST, WMT | 1.00 | 1.00 | 1.00 | 1.00 | none |
| 22 | AAPL, GOOGL, MSFT | 1.00 | 1.00 | 1.00 | 1.00 | none |
| 24 | NVDA, TSLA | 1.00 | 1.00 | 0.33 | 1.00 | N:NVDA ×2, N:TSLA ×2 |
| 25 | DIS, NFLX | 1.00 | 0.00 | 0.33 | 1.00 | N:DIS ×5, N:NFLX ×5 |
| 26 | COST, LLY, NVDA | 0.00 | 0.33 | 0.67 | 0.33 | S:COST ×7, S:LLY ×7, S:NVDA ×6, N:COST ×1, N:LLY ×1, N:NVDA ×1 |
| 29 | AIR.PA, BA | 0.33 | 0.67 | 0.33 | 0.67 | N:AIR.PA ×6, S:BA ×1 |
| 30 | COST, MCD, WMT | 1.00 | 1.00 | 1.00 | 1.00 | none |

## Coverage-gap audit: matched insufficiency phrase per run

| Row | Config | Rep | Matched phrase |
|---|---|---|---|
| 4 | luna_medium | 1 | 資料不足 |
| 4 | luna_medium | 2 | (none) |
| 4 | luna_medium | 3 | 證據不足 |
| 4 | luna_medium_plus_search | 1 | 證據不足 |
| 4 | luna_medium_plus_search | 2 | 沒有拿到 |
| 4 | luna_medium_plus_search | 3 | 資料限制 |
| 4 | reader_luna_medium | 1 | 工具只支援 |
| 4 | reader_luna_medium | 2 | 工具只支援 |
| 4 | reader_luna_medium | 3 | 工具只支援 |
| 4 | reader_prompt_no_search | 1 | 工具只支援 |
| 4 | reader_prompt_no_search | 2 | 沒有取得 |
| 4 | reader_prompt_no_search | 3 | 工具只支援 |
| 29 | luna_medium | 1 | (none) |
| 29 | luna_medium | 2 | 資料品質限制 |
| 29 | luna_medium | 3 | 資料不足 |
| 29 | luna_medium_plus_search | 1 | 資料不足 |
| 29 | luna_medium_plus_search | 2 | (none) |
| 29 | luna_medium_plus_search | 3 | (none) |
| 29 | reader_luna_medium | 1 | (none) |
| 29 | reader_luna_medium | 2 | 資料不足 |
| 29 | reader_luna_medium | 3 | 沒有取得 |
| 29 | reader_prompt_no_search | 1 | 未能取得 |
| 29 | reader_prompt_no_search | 2 | 沒有取得 |
| 29 | reader_prompt_no_search | 3 | (none) |
