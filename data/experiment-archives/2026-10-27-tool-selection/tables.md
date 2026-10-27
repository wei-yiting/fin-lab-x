30 of 30 rows labelled: 29 scored for routing (partial gap kept: 29; full gap excluded: 4), 0 partially labelled skipped (–).

Cells are means over rows of per-row means over repetitions; [95% CI] = row-level bootstrap.

## Routing (full coverage-gap rows excluded)

| Config | Rows | Runs | Recall | Recall (successful calls only) | Unnecessary-call rate | Unnecessary calls/run | Errored-only source uses | Median tool calls (all runs) |
|---|---|---|---|---|---|---|---|---|
| gemini_medium | 29 | 87 | 0.47 [0.30, 0.64] | 0.47 [0.30, 0.64] | 0.70 [0.54, 0.85] | 1.25 [0.86, 1.72] | 0 | 4 |
| gemini_minimal | 29 | 87 | 0.61 [0.44, 0.76] | 0.61 [0.44, 0.76] | 0.45 [0.30, 0.60] | 0.53 [0.33, 0.74] | 0 | 4 |
| luna_medium @ model-reasoning-benchmark | 29 | 87 | 0.85 [0.72, 0.97] | 0.85 [0.72, 0.97] | 0.31 [0.16, 0.47] | 0.40 [0.18, 0.64] | 0 | 7 |
| luna_none | 29 | 87 | 0.82 [0.70, 0.92] | 0.82 [0.70, 0.92] | 0.54 [0.37, 0.71] | 0.72 [0.48, 1.01] | 0 | 6 |
| luna_medium @ rag-bundle-ablation | 29 | 87 | 0.86 [0.75, 0.97] | 0.86 [0.75, 0.97] | 0.34 [0.20, 0.51] | 0.45 [0.23, 0.69] | 0 | 7 |
| reader_luna_medium | 29 | 87 | 0.93 [0.84, 1.00] | 0.93 [0.84, 1.00] | 0.25 [0.11, 0.40] | 0.30 [0.13, 0.49] | 1 | 4 |

## Unnecessary calls by source

Runs that called the source / runs on rows where it is labelled 不必要 (routing rows).

| Config | Finnhub quote | Finnhub financials | Tavily news | SEC 10-K |
|---|---|---|---|---|
| gemini_medium | 50/72 (69%) | 16/30 (53%) | 14/21 (67%) | 0/3 (0%) |
| gemini_minimal | 30/72 (42%) | 9/30 (30%) | 5/21 (24%) | 0/3 (0%) |
| luna_medium @ model-reasoning-benchmark | 22/72 (31%) | 10/30 (33%) | 0/21 (0%) | 0/3 (0%) |
| luna_none | 23/72 (32%) | 22/30 (73%) | 8/21 (38%) | 0/3 (0%) |
| luna_medium @ rag-bundle-ablation | 23/72 (32%) | 10/30 (33%) | 1/21 (5%) | 0/3 (0%) |
| reader_luna_medium | 17/72 (24%) | 9/30 (30%) | 0/21 (0%) | 0/3 (0%) |

## Ticker-argument accuracy (all labelled rows)

| Config | Rows | Accuracy |
|---|---|---|
| gemini_medium | 30 | 0.98 [0.94, 1.00] |
| gemini_minimal | 30 | 0.99 [0.96, 1.00] |
| luna_medium @ model-reasoning-benchmark | 30 | 0.99 [0.98, 1.00] |
| luna_none | 30 | 1.00 [1.00, 1.00] |
| luna_medium @ rag-bundle-ablation | 30 | 0.99 [0.97, 1.00] |
| reader_luna_medium | 30 | 0.98 [0.96, 1.00] |

## Entity coverage (multi-company rows; 必要 sources × servable tickers, successful calls)

| Config | Rows | All pairs covered | Share of pairs covered |
|---|---|---|---|
| gemini_medium | 12 | 0.39 [0.14, 0.64] | 0.59 [0.38, 0.78] |
| gemini_minimal | 12 | 0.53 [0.31, 0.75] | 0.70 [0.51, 0.87] |
| luna_medium @ model-reasoning-benchmark | 12 | 0.81 [0.56, 1.00] | 0.92 [0.82, 1.00] |
| luna_none | 12 | 0.72 [0.53, 0.92] | 0.84 [0.72, 0.95] |
| luna_medium @ rag-bundle-ablation | 12 | 0.83 [0.64, 1.00] | 0.93 [0.84, 1.00] |
| reader_luna_medium | 12 | 0.78 [0.58, 0.94] | 0.91 [0.84, 0.98] |

## Coverage-gap checks (full and partial gap rows)

| Config | Rows | Runs | Insufficient evidence stated | Repeated failed calls/run | Runs with a repeated failed call | Retries after source failure/run |
|---|---|---|---|---|---|---|
| gemini_medium | 2 | 6 | 0.17 [0.00, 0.33] | 0.00 [0.00, 0.00] | 0 | 0.00 [0.00, 0.00] |
| gemini_minimal | 2 | 6 | 0.50 [0.00, 1.00] | 0.00 [0.00, 0.00] | 0 | 0.00 [0.00, 0.00] |
| luna_medium @ model-reasoning-benchmark | 2 | 6 | 0.83 [0.67, 1.00] | 0.00 [0.00, 0.00] | 0 | 0.17 [0.00, 0.33] |
| luna_none | 2 | 6 | 1.00 [1.00, 1.00] | 0.00 [0.00, 0.00] | 0 | 0.00 [0.00, 0.00] |
| luna_medium @ rag-bundle-ablation | 2 | 6 | 0.67 [0.33, 1.00] | 0.00 [0.00, 0.00] | 0 | 0.00 [0.00, 0.00] |
| reader_luna_medium | 2 | 6 | 0.83 [0.67, 1.00] | 0.00 [0.00, 0.00] | 0 | 0.00 [0.00, 0.00] |

## Per row × config

Labels: Q = Finnhub quote, F = Finnhub financials, N = Tavily news, S = SEC 10-K; R = 必要, E = 擇一必要, A = 可接受, U = 不必要.
Routing cells: recall / unnecessary-call rate / mean tool calls. Full-gap cells: insufficient evidence stated / repeated failed calls / mean tool calls.

| Row | Labels | Gap | gemini_medium | gemini_minimal | luna_medium @ model-reasoning-benchmark | luna_none | luna_medium @ rag-bundle-ablation | reader_luna_medium |
|---|---|---|---|---|---|---|---|---|
| 1 | Q:A F:A N:R S:R |  | 0.00 / 0.00 / 4.0 | 0.00 / 0.00 / 3.3 | 1.00 / 0.00 / 7.3 | 1.00 / 0.00 / 7.0 | 1.00 / 0.00 / 7.3 | 1.00 / 0.00 / 4.0 |
| 2 | Q:U F:U N:R S:R |  | 0.00 / 1.00 / 4.0 | 0.33 / 1.00 / 4.0 | 1.00 / 1.00 / 8.0 | 1.00 / 1.00 / 6.0 | 0.67 / 1.00 / 7.0 | 1.00 / 1.00 / 5.3 |
| 3 | Q:U F:U N:R S:R |  | 0.00 / 1.00 / 3.7 | 0.00 / 1.00 / 3.0 | 0.00 / 0.00 / 5.7 | 0.33 / 0.67 / 3.3 | 0.33 / 0.00 / 5.7 | 1.00 / 0.00 / 3.7 |
| 4 | Q:U F:U N:R S:R | full | 0.33 / 0.0 / 5.7 | 1.00 / 0.0 / 6.0 | 1.00 / 0.0 / 8.7 | 1.00 / 0.0 / 5.3 | 1.00 / 0.0 / 8.0 | 1.00 / 0.0 / 7.7 |
| 5 | Q:U F:E N:R S:E |  | 1.00 / 1.00 / 3.7 | 1.00 / 1.00 / 3.0 | 1.00 / 1.00 / 7.0 | 1.00 / 1.00 / 6.3 | 1.00 / 1.00 / 7.3 | 1.00 / 1.00 / 5.0 |
| 6 | Q:U F:A N:R S:R |  | 0.67 / 1.00 / 5.7 | 0.67 / 0.33 / 3.7 | 1.00 / 0.00 / 7.3 | 1.00 / 0.00 / 6.0 | 1.00 / 0.33 / 8.0 | 1.00 / 0.00 / 3.0 |
| 7 | Q:U F:U N:R S:R |  | 0.00 / 0.67 / 4.3 | 0.00 / 0.33 / 2.7 | 1.00 / 0.00 / 7.7 | 1.00 / 0.67 / 7.3 | 1.00 / 0.00 / 7.0 | 1.00 / 0.00 / 3.3 |
| 8 | Q:U F:A N:U S:R |  | 1.00 / 1.00 / 4.3 | 1.00 / 0.67 / 3.7 | 1.00 / 0.00 / 4.3 | 1.00 / 1.00 / 6.0 | 1.00 / 0.33 / 4.7 | 1.00 / 0.00 / 4.7 |
| 9 | Q:U F:A N:R S:R |  | 0.00 / 0.00 / 5.3 | 1.00 / 0.00 / 5.3 | 1.00 / 0.00 / 10.0 | 1.00 / 0.00 / 10.0 | 1.00 / 0.33 / 10.7 | 1.00 / 0.00 / 7.3 |
| 10 | Q:U F:U N:R S:R |  | 0.00 / 1.00 / 6.0 | 0.67 / 0.00 / 2.3 | 1.00 / 0.00 / 9.3 | 0.33 / 1.00 / 9.0 | 1.00 / 0.00 / 9.0 | 1.00 / 0.00 / 5.3 |
| 11 | Q:U F:U N:A S:R |  | 1.00 / 1.00 / 6.0 | 1.00 / 0.33 / 4.7 | 1.00 / 0.00 / 3.0 | 1.00 / 0.00 / 4.3 | 1.00 / 0.00 / 3.0 | 1.00 / 0.00 / 2.0 |
| 12 | Q:U F:A N:A S:R |  | 1.00 / 1.00 / 5.0 | 1.00 / 0.33 / 5.0 | 1.00 / 0.00 / 4.7 | 1.00 / 0.00 / 5.7 | 1.00 / 0.00 / 4.7 | 1.00 / 0.00 / 2.0 |
| 13 | Q:U F:U N:U S:R |  | 1.00 / 0.00 / 3.3 | 1.00 / 0.00 / 4.0 | 1.00 / 0.00 / 6.7 | 1.00 / 0.33 / 6.7 | 1.00 / 0.00 / 6.0 | 1.00 / 0.00 / 2.0 |
| 14 | Q:U F:U N:R S:R |  | 0.00 / 1.00 / 3.0 | 0.00 / 0.33 / 1.7 | 0.00 / 0.00 / 4.7 | 0.33 / 1.00 / 2.3 | 0.00 / 0.00 / 6.0 | 1.00 / 0.00 / 4.0 |
| 15 | Q:U F:U N:U S:R |  | 1.00 / 1.00 / 3.7 | 1.00 / 0.00 / 2.7 | 1.00 / 0.33 / 4.0 | 1.00 / 1.00 / 5.3 | 1.00 / 0.33 / 4.3 | 1.00 / 0.67 / 2.7 |
| 16 | Q:U F:U N:A S:R |  | 0.33 / 1.00 / 2.7 | 1.00 / 1.00 / 3.3 | 1.00 / 1.00 / 5.3 | 1.00 / 1.00 / 5.0 | 1.00 / 1.00 / 5.3 | 1.00 / 0.33 / 2.7 |
| 17 | Q:U F:U N:A S:R |  | 1.00 / 1.00 / 6.7 | 1.00 / 0.33 / 3.3 | 1.00 / 1.00 / 6.3 | 1.00 / 1.00 / 6.0 | 1.00 / 1.00 / 5.3 | 1.00 / 1.00 / 4.7 |
| 18 | Q:U F:A N:U S:R |  | 0.33 / 0.67 / 4.3 | 1.00 / 0.67 / 5.7 | 1.00 / 0.00 / 8.0 | 1.00 / 0.00 / 8.0 | 1.00 / 0.00 / 8.0 | 1.00 / 0.00 / 2.0 |
| 19 | Q:U F:A N:U S:R |  | 0.00 / 1.00 / 3.3 | 0.67 / 1.00 / 3.7 | 1.00 / 1.00 / 5.3 | 1.00 / 1.00 / 5.0 | 1.00 / 1.00 / 5.3 | 1.00 / 0.67 / 2.7 |
| 20 | Q:U F:A N:A S:R |  | 0.00 / 1.00 / 3.3 | 0.00 / 1.00 / 3.0 | 0.67 / 1.00 / 4.0 | 0.33 / 1.00 / 3.7 | 1.00 / 1.00 / 5.3 | 1.00 / 0.33 / 2.7 |
| 21 | Q:U F:A N:U S:R |  | 1.00 / 1.00 / 9.7 | 1.00 / 0.00 / 4.0 | 1.00 / 0.00 / 8.0 | 1.00 / 0.00 / 8.0 | 1.00 / 0.00 / 8.0 | 1.00 / 0.00 / 5.3 |
| 22 | Q:U F:A N:A S:R |  | 0.00 / 0.00 / 5.3 | 0.67 / 0.00 / 5.0 | 1.00 / 0.00 / 9.0 | 0.67 / 0.00 / 8.0 | 1.00 / 0.00 / 9.3 | 1.00 / 0.00 / 6.0 |
| 23 | Q:A F:R N:R S:A |  | 1.00 / 0.00 / 4.0 | 1.00 / 0.00 / 3.3 | 1.00 / 0.00 / 4.3 | 1.00 / 0.00 / 6.3 | 1.00 / 0.00 / 5.7 | 1.00 / 0.00 / 4.0 |
| 24 | Q:A F:R N:R S:A |  | 1.00 / 0.00 / 6.0 | 0.67 / 0.00 / 5.3 | 1.00 / 0.00 / 8.0 | 1.00 / 0.00 / 6.0 | 1.00 / 0.00 / 6.0 | 0.67 / 0.00 / 7.7 |
| 25 | Q:A F:R N:R S:U |  | 1.00 / 0.00 / 5.3 | 1.00 / 0.00 / 5.7 | 0.00 / 0.00 / 4.0 | 1.00 / 0.00 / 6.0 | 0.33 / 0.00 / 4.7 | 0.33 / 0.00 / 4.0 |
| 26 | Q:A F:R N:R S:R |  | 0.00 / 0.00 / 8.0 | 0.00 / 0.00 / 7.3 | 0.00 / 0.00 / 9.0 | 0.00 / 0.00 / 9.0 | 0.00 / 0.00 / 9.0 | 0.00 / 0.00 / 9.0 |
| 27 | Q:U F:A N:A S:R |  | 0.33 / 1.00 / 4.7 | 0.00 / 1.00 / 3.0 | 1.00 / 0.67 / 7.3 | 1.00 / 1.00 / 7.0 | 1.00 / 0.67 / 7.7 | 1.00 / 1.00 / 6.0 |
| 28 | Q:U F:A N:R S:A |  | 1.00 / 1.00 / 3.7 | 1.00 / 1.00 / 3.0 | 1.00 / 1.00 / 4.0 | 1.00 / 1.00 / 3.0 | 1.00 / 1.00 / 4.0 | 1.00 / 1.00 / 3.7 |
| 29 | Q:U F:A N:R S:R | partial | 0.00 / 1.00 / 6.3 | 0.00 / 1.00 / 5.3 | 1.00 / 1.00 / 10.7 | 0.33 / 1.00 / 7.7 | 0.67 / 1.00 / 9.3 | 1.00 / 0.33 / 7.7 |
| 30 | Q:U F:A N:U S:R |  | 0.00 / 1.00 / 7.0 | 0.00 / 0.67 / 3.7 | 1.00 / 0.00 / 9.0 | 0.33 / 1.00 / 6.0 | 1.00 / 0.00 / 9.0 | 1.00 / 0.00 / 7.0 |

## Ticker args outside the expected list (calls, all configs)

| Row | Expected | Off-list (calls) |
|---|---|---|
| 16 | V | JPM ×2 |
| 27 | JPM | BAC ×4, C ×4, WFC ×3 |
| 29 | AIR.PA, BA | AIR ×5, EADSY ×9 |

## Entity coverage per row × config (share of runs with all pairs covered)

Missed pairs are counted over all configs; Q/F/N/S as above.

| Row | Tickers | gemini_medium | gemini_minimal | luna_medium @ model-reasoning-benchmark | luna_none | luna_medium @ rag-bundle-ablation | reader_luna_medium | Missed pairs (runs) |
|---|---|---|---|---|---|---|---|---|
| 4 | ASML, TSM | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | none |
| 9 | AAPL, META | 0.00 | 0.33 | 1.00 | 1.00 | 1.00 | 1.00 | S:AAPL ×3, S:META ×3, N:META ×2 |
| 10 | AAPL, GOOGL, META | 0.00 | 0.00 | 1.00 | 0.33 | 1.00 | 0.67 | S:META ×8, S:AAPL ×7, S:GOOGL ×7, N:META ×4, N:GOOGL ×3 |
| 13 | MA, V | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | none |
| 18 | KO, PEP | 0.33 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | S:KO ×2, S:PEP ×2 |
| 21 | COST, WMT | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | none |
| 22 | AAPL, GOOGL, MSFT | 0.00 | 0.67 | 1.00 | 0.67 | 1.00 | 1.00 | S:AAPL ×5, S:GOOGL ×5, S:MSFT ×5 |
| 24 | NVDA, TSLA | 1.00 | 0.67 | 1.00 | 1.00 | 1.00 | 0.67 | N:NVDA ×2, N:TSLA ×2 |
| 25 | DIS, NFLX | 0.33 | 0.67 | 0.00 | 1.00 | 0.33 | 0.33 | N:NFLX ×9, N:DIS ×8 |
| 26 | COST, LLY, NVDA | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | S:COST ×15, S:LLY ×15, S:NVDA ×15, N:NVDA ×8, N:LLY ×5, N:COST ×4 |
| 29 | AIR.PA, BA | 0.00 | 0.00 | 0.67 | 0.33 | 0.67 | 0.67 | N:AIR.PA ×9, S:BA ×9 |
| 30 | COST, MCD, WMT | 0.00 | 0.00 | 1.00 | 0.33 | 1.00 | 1.00 | S:COST ×8, S:MCD ×8, S:WMT ×8 |

## Coverage-gap audit: matched insufficiency phrase per run

| Row | Config | Rep | Matched phrase |
|---|---|---|---|
| 4 | gemini_medium | 1 | (none) |
| 4 | gemini_medium | 2 | (none) |
| 4 | gemini_medium | 3 | 數據說明與潛在限制 |
| 4 | gemini_minimal | 1 | 數據/資訊限制 |
| 4 | gemini_minimal | 2 | 資料品質與限制 |
| 4 | gemini_minimal | 3 | 數據品質與資訊限制 |
| 4 | luna_medium @ model-reasoning-benchmark | 1 | 資料不足 |
| 4 | luna_medium @ model-reasoning-benchmark | 2 | 證據不足 |
| 4 | luna_medium @ model-reasoning-benchmark | 3 | 證據不足 |
| 4 | luna_none | 1 | 資料不足 |
| 4 | luna_none | 2 | 證據不足 |
| 4 | luna_none | 3 | 資料不足 |
| 4 | luna_medium @ rag-bundle-ablation | 1 | 證據不足 |
| 4 | luna_medium @ rag-bundle-ablation | 2 | 資料不足 |
| 4 | luna_medium @ rag-bundle-ablation | 3 | 資料不足 |
| 4 | reader_luna_medium | 1 | 證據，**不足 |
| 4 | reader_luna_medium | 2 | 證據不足 |
| 4 | reader_luna_medium | 3 | 無法取得 |
| 29 | gemini_medium | 1 | (none) |
| 29 | gemini_medium | 2 | (none) |
| 29 | gemini_medium | 3 | (none) |
| 29 | gemini_minimal | 1 | (none) |
| 29 | gemini_minimal | 2 | (none) |
| 29 | gemini_minimal | 3 | (none) |
| 29 | luna_medium @ model-reasoning-benchmark | 1 | (none) |
| 29 | luna_medium @ model-reasoning-benchmark | 2 | 沒有找到 |
| 29 | luna_medium @ model-reasoning-benchmark | 3 | 無法取得 |
| 29 | luna_none | 1 | 資料不足 |
| 29 | luna_none | 2 | 未能取得 |
| 29 | luna_none | 3 | 未能取得 |
| 29 | luna_medium @ rag-bundle-ablation | 1 | (none) |
| 29 | luna_medium @ rag-bundle-ablation | 2 | 資料不足 |
| 29 | luna_medium @ rag-bundle-ablation | 3 | (none) |
| 29 | reader_luna_medium | 1 | 資料限制 |
| 29 | reader_luna_medium | 2 | 沒有取得 |
| 29 | reader_luna_medium | 3 | (none) |
